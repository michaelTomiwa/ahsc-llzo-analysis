"""Phase 3.3: GraphRAG - entity linking -> graph traversal + semantic retrieval -> LLM synthesis.

Answers carry fact-level citations (fact id, value, verbatim evidence span, source record/DOI).
Without an API key the synthesis step is a deterministic, statistics-based summary of the
same retrieved context, so answers stay grounded and reproducible.
"""
from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

import networkx as nx

from . import llm
from .facts import is_reliable, load_facts
from .knowledge_graph import (build_graph, dopant_effects, family_property_stats, find_nodes, get_neighborhood,
                              serialize_subgraph)
from .search import SemanticIndex

PROPERTY_KEYWORDS = {
    "ionic_conductivity": r"conductiv|ion transport|li\+ transport",
    "specific_capacitance": r"capacitan",
    "specific_capacity": r"capacity(?! retention)|mah",
    "specific_energy": r"energy density|specific energy|wh/kg",
    "specific_power": r"power density|specific power|w/kg",
    "cycling_stability": r"cycl|stabilit|retention|durab|lifetime",
    "potential_window": r"window|voltage|potential",
    "rate_capability": r"rate capab",
}
SYSTEM_KEYWORDS = {"LLZO": r"llzo|garnet|solid.state|electrolyte", "AHSC": r"ahsc|supercap|hybrid|capacitor"}

ENTITY_SCHEMA = {
    "type": "object",
    "properties": {
        "materials": {"type": "array", "items": {"type": "string"}},
        "properties": {"type": "array", "items": {"type": "string", "enum": list(PROPERTY_KEYWORDS)}},
        "elements_or_dopants": {"type": "array", "items": {"type": "string"}},
        "systems": {"type": "array", "items": {"type": "string", "enum": ["AHSC", "LLZO"]}},
    },
    "required": ["materials", "properties", "elements_or_dopants", "systems"],
    "additionalProperties": False,
}

ANSWER_PROMPT = """Answer the research question using ONLY the knowledge-graph context and facts below.

Question: {question}

Knowledge-graph context (edges with medians and fact ids):
{graph}

Analytics:
{analytics}

Retrieved facts (id | material | value | evidence span | source):
{facts}

Write 1-3 short paragraphs. Cite fact ids in square brackets after each claim, e.g. [LLZO-0002-ionic_conductivity].
Say explicitly when the data are thin (few records), conflicting, or do not answer the question, and suggest
what evidence would be needed. Do not invent values, DOIs or mechanisms that the context does not support;
you may add clearly-labelled general domain knowledge in one final sentence starting with "Background:"."""


@dataclass
class Engine:
    """Loads facts, graph and index once; reused by the app, API and hypothesis engine."""
    facts: list[dict] = field(default_factory=load_facts)
    graph: nx.DiGraph | None = None
    index: SemanticIndex | None = None

    def __post_init__(self):
        self.graph = self.graph or build_graph(self.facts)
        self.index = self.index or SemanticIndex()
        self.by_id = {fact["id"]: fact for fact in self.facts}


_ENGINE: Engine | None = None


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = Engine()
    return _ENGINE


def extract_entities(question: str, engine: Engine) -> dict:
    """LLM entity extraction when available, lexicon matching always (union of both)."""
    lowered = question.lower()
    entities = {
        "properties": [p for p, pattern in PROPERTY_KEYWORDS.items() if re.search(pattern, lowered)],
        "systems": [s for s, pattern in SYSTEM_KEYWORDS.items() if re.search(pattern, lowered)],
        "nodes": find_nodes(engine.graph, question)[:25],
        "mode": "lexicon",
    }
    if llm.available():
        result = llm.complete(f"Extract the entities in this materials-science question:\n{question}",
                              schema=ENTITY_SCHEMA, effort="low")
        if result.data:
            entities["mode"] = f"lexicon + {result.mode}"
            entities["properties"] = sorted(set(entities["properties"]) | set(result.data["properties"]))
            entities["systems"] = sorted(set(entities["systems"]) | set(result.data["systems"]))
            for name in result.data["materials"] + result.data["elements_or_dopants"]:
                entities["nodes"] += [n for n in find_nodes(engine.graph, name) if n not in entities["nodes"]][:5]
    for prop in entities["properties"]:
        entities["nodes"].append(f"Property:{prop}")
    return entities


def _analytics(question: str, entities: dict, engine: Engine) -> str:
    lines = []
    lowered = question.lower()
    if re.search(r"dopant|doping|doped|substitut", lowered) or any(n.startswith("Dopant:") for n in entities["nodes"]):
        table = dopant_effects(engine.facts)
        if not table.empty and entities["properties"]:
            table = table[table.property.isin(entities["properties"])]
        if not table.empty:
            for row in table.itertuples():
                lines.append(f"dopant {row.dopant}: {row.property} median {row.median:.4g} {row.unit} "
                             f"(n={row.count}, range {row.min:.4g}-{row.max:.4g})")
    for prop in entities["properties"][:2]:
        for system in entities["systems"] or [None]:
            stats = family_property_stats(engine.facts, prop, system)
            for row in stats.head(6).itertuples():
                lines.append(f"{prop}{' in ' + system if system else ''}: family {row.material_family} median "
                             f"{row.median:.4g} {row.unit} (n={row.count}, max {row.max:.4g})")
    return "\n".join(lines) or "No aggregate statistics matched this question."


def _retrieve_facts(question: str, entities: dict, engine: Engine, sub: nx.DiGraph, k: int) -> list[dict]:
    system = entities["systems"][0] if len(entities["systems"]) == 1 else None
    hits = engine.index.search(question, k=k, system=system, kinds=("fact",))
    ids = [hit["id"] for hit in hits]
    if re.search(r"dopant|doping|doped", question, re.I):
        wanted_props = set(entities["properties"]) or None
        ids = [f["id"] for f in engine.facts if f.get("dopants")
               and (wanted_props is None or f["property"] in wanted_props)] + ids
    # Add the best-supported facts from graph edges that match the asked-for properties.
    wanted = {f"Property:{p}" for p in entities["properties"]}
    for u, v, data in sub.edges(data=True):
        if data.get("relation") == "hasProperty" and (not wanted or v in wanted):
            ids += data["fact_ids"][:2]
    unique = list(dict.fromkeys(i for i in ids if i in engine.by_id))
    return [engine.by_id[i] for i in unique[: k + 10]]


def _citation(fact: dict) -> dict:
    source = fact["source"]
    return {"fact_id": fact["id"], "material": fact["material"], "property": fact["property"],
            "value": fact["value"], "unit": fact["unit"], "condition": fact.get("condition"),
            "evidence_span": fact["evidence_span"], "doi": source.get("doi"), "url": source.get("url"),
            "review_doi": source.get("review_doi"), "review_link": source.get("review_link"),
            "source": source.get("doi") or source.get("url")
            or f"{source.get('file', '')} line {source.get('csv_line', '')}".strip(),
            "confidence": fact["confidence"], "quality_flags": fact["quality_flags"]}


def _offline_answer(question: str, entities: dict, facts: list[dict], analytics: str, engine: Engine) -> str:
    if not facts:
        return "No facts in the knowledge base match this question. Try naming a material, property or system."
    parts = []
    if re.search(r"dopant|doping|doped", question, re.I):
        doped = [f for f in facts if f.get("dopants")]
        parts.append(
            "**Dopant evidence.** " + (
                "Doped compositions in the knowledge base: " + ", ".join(sorted({
                    f"{f['material']} ({'/'.join(f['dopants'])})" for f in doped})[:8]) + ". "
                if doped else "No retrieved fact names a dopant explicitly. ")
            + "The per-dopant aggregates below compare doped garnets with records where no dopant is stated "
              "(mostly polymer electrolytes), so they are not a like-for-like dopant ranking; the curated "
              "LLZO-xTa/Ga interface records report capacity and voltage but not conductivity.")
    props = entities["properties"] or sorted({f["property"] for f in facts})[:2]
    systems = set(entities["systems"]) or {f["system"] for f in facts}
    for prop in props[:3]:
        # Rank across the whole knowledge base (not only retrieved facts) for "best/highest" questions.
        pool = engine.facts if entities["properties"] else facts
        relevant = [f for f in pool if f["property"] == prop and f["system"] in systems and is_reliable(f)]
        if not relevant:
            continue
        unit = statistics.mode(f["unit"] for f in relevant)
        relevant = sorted((f for f in relevant if f["unit"] == unit), key=lambda f: -f["value"])
        values = [f["value"] for f in relevant]
        best = relevant[:3]
        parts.append(f"**{prop.replace('_', ' ').capitalize()}** - {len(values)} values, median "
                     f"{statistics.median(values):.4g} {unit}. Highest: " + "; ".join(
                         f"{f['material']} {f['value']:.4g} {unit} [{f['id']}]" for f in best) + ".")
    if analytics and not analytics.startswith("No aggregate"):
        parts.append("**Aggregates from the knowledge graph:**\n" + "\n".join(f"- {line}" for line in analytics.splitlines()[:8]))
    if len(facts) < 5:
        parts.append("Evidence is thin (fewer than 5 matching facts); treat this as preliminary.")
    parts.append("_Offline mode: deterministic summary of retrieved graph context. Configure ANTHROPIC_API_KEY "
                 "for LLM synthesis._")
    return "\n\n".join(parts)


def graph_rag(question: str, engine: Engine | None = None, k: int = 12) -> dict:
    engine = engine or get_engine()
    entities = extract_entities(question, engine)
    sub = get_neighborhood(engine.graph, entities["nodes"], depth=1)
    facts = _retrieve_facts(question, entities, engine, sub, k)
    analytics = _analytics(question, entities, engine)
    mode = "offline (graph + statistics)"
    answer = ""
    if llm.available():
        fact_lines = "\n".join(f"{f['id']} | {f['material']} | {f['value']:.4g} {f['unit']} {f.get('condition') or ''} | "
                               f"\"{f['evidence_span']}\" | {f['source'].get('doi') or f['record_id']}" for f in facts)
        result = llm.complete(ANSWER_PROMPT.format(question=question, graph=serialize_subgraph(sub) or "(none)",
                                                   analytics=analytics, facts=fact_lines))
        if result.text:
            answer, mode = result.text, result.mode
        else:
            mode = f"offline fallback ({result.mode})"
    if not answer:
        answer = _offline_answer(question, entities, facts, analytics, engine)
    cited = list(dict.fromkeys(re.findall(r"\[([A-Z]+-\d{4}-[a-z_]+)\]", answer)))
    cited_facts = [engine.by_id[i] for i in cited if i in engine.by_id]
    citations = [_citation(f) for f in cited_facts + [f for f in facts if f["id"] not in cited]][: k + 10]
    return {"question": question, "answer": answer, "mode": mode, "entities": entities, "analytics": analytics,
            "citations": citations,
            "subgraph": {"nodes": [{"id": n, **{k: v for k, v in d.items() if k in ("type", "name")}}
                                   for n, d in sub.nodes(data=True)],
                         "edges": [{"source": u, "target": v, "relation": d.get("relation")}
                                   for u, v, d in sub.edges(data=True)]}}


if __name__ == "__main__":
    import sys

    response = graph_rag(" ".join(sys.argv[1:]) or "What dopants improve LLZO ionic conductivity?")
    print(response["mode"])
    print(response["answer"])
    for citation in response["citations"][:8]:
        print("-", citation["fact_id"], citation["evidence_span"], citation["source"])
