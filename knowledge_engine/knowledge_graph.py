"""Phase 3: knowledge graph construction, analytics (centrality, co-occurrence, gaps), export.

Node types: Material, MaterialFamily, Property, Element, Dopant, Paper (curated record or
DOI), System, Country. Edge types follow schema.json:
    Material -hasProperty-> Property     (values, units, fact ids, sources)
    Material -memberOf-> MaterialFamily  Material -containsElement-> Element
    Material -dopedWith-> Dopant         Material -studiedIn-> Paper
    Paper -usesComponent-> Material      Material -inSystem-> System
    Element -suppliedBy-> Country        (African supply, from data/africa_element_supply.csv)

    python -m knowledge_engine.knowledge_graph   # -> data/knowledge_graph.graphml + reports/research_map.json
"""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from itertools import combinations

import networkx as nx
import pandas as pd

from .africa import africa_profile, countries_for, element_supply
from .config import GRAPHML_PATH, REPORTS_DIR
from .facts import is_reliable, load_facts


def nid(kind: str, name: str) -> str:
    return f"{kind}:{name}"


def build_graph(facts: list[dict] | None = None) -> nx.DiGraph:
    facts = facts if facts is not None else load_facts()
    G = nx.DiGraph()

    def node(kind: str, name: str, **attrs) -> str:
        key = nid(kind, name)
        if key not in G:
            G.add_node(key, type=kind, name=name, **attrs)
        return key

    for fact in facts:
        material = node("Material", fact["material"], system=fact["system"], role=fact["material_role"],
                        family=fact["material_family"], elements=fact["elements"],
                        africa_score=fact["africa"]["score"])
        prop = node("Property", fact["property"], label=fact.get("property_label", fact["property"]),
                    category=fact.get("property_category", ""))
        source = fact["source"]
        paper = node("Paper", source.get("doi") or fact["record_id"], doi=source.get("doi") or "",
                     title=source.get("title") or "", source_type=source["type"], system=fact["system"])
        family = node("MaterialFamily", fact["material_family"])
        system = node("System", fact["system"])

        edge = G.get_edge_data(material, prop) or {"relation": "hasProperty", "values": [], "units": [],
                                                    "fact_ids": [], "sources": [], "conditions": []}
        edge["values"].append(fact["value"])
        edge["units"].append(fact["unit"])
        edge["fact_ids"].append(fact["id"])
        edge["sources"].append(source.get("doi") or fact["record_id"])
        edge["conditions"].append(fact.get("condition") or "")
        G.add_edge(material, prop, **edge)

        G.add_edge(material, family, relation="memberOf")
        G.add_edge(material, system, relation="inSystem")
        G.add_edge(material, paper, relation="studiedIn")
        for role, component in (fact.get("components") or {}).items():
            if component and component != fact["material"]:
                comp = node("Material", component, system=fact["system"], role=role, family="", elements=[],
                            africa_score=None)
                G.add_edge(paper, comp, relation="usesComponent", role=role)
        for element in fact["elements"]:
            el = node("Element", element, african_supply=(element_supply(element) or {}).get("status", "none"))
            G.add_edge(material, el, relation="containsElement")
            for country in countries_for(element):
                G.add_edge(el, node("Country", country), relation="suppliedBy")
        for dopant in fact.get("dopants", []):
            G.add_edge(material, node("Dopant", dopant), relation="dopedWith")

    for u, v, data in G.edges(data=True):
        if data.get("relation") == "hasProperty":
            data["n"] = len(data["values"])
            data["median"] = statistics.median(data["values"])
            data["unit"] = Counter(data["units"]).most_common(1)[0][0]
    return G


def nodes_of(G: nx.DiGraph, kind: str) -> list[str]:
    return [n for n, d in G.nodes(data=True) if d["type"] == kind]


# ---------------------------------------------------------------- analytics
def centrality(G: nx.DiGraph, kind: str = "Material", top: int = 15) -> pd.DataFrame:
    """Degree centrality (undirected) of one node type, plus how many papers study each node."""
    degree = nx.degree_centrality(G.to_undirected(as_view=True))
    rows = []
    for n in nodes_of(G, kind):
        materials = [n] if kind == "Material" else [m for m, _ in G.in_edges(n)]
        papers = len({p for m in materials for _, p, d in G.out_edges(m, data=True) if d.get("relation") == "studiedIn"}
                     | {p for m in materials for p, _, d in G.in_edges(m, data=True) if d.get("relation") == "usesComponent"})
        rows.append({"node": G.nodes[n]["name"], "degree_centrality": round(degree[n], 5),
                     "degree": G.degree(n), "papers": papers})
    return pd.DataFrame(rows).sort_values(["papers", "degree"], ascending=False).head(top).reset_index(drop=True)


def property_cooccurrence(facts: list[dict]) -> pd.DataFrame:
    """Which properties are reported together in the same paper/record (count and Jaccard)."""
    per_record: dict[str, set] = defaultdict(set)
    for fact in facts:
        per_record[fact["record_id"]].add(fact["property"])
    counts = Counter(p for props in per_record.values() for p in props)
    pairs = Counter(pair for props in per_record.values() for pair in combinations(sorted(props), 2))
    rows = [{"property_a": a, "property_b": b, "records_with_both": n,
             "jaccard": round(n / (counts[a] + counts[b] - n), 3)} for (a, b), n in pairs.items()]
    return pd.DataFrame(rows).sort_values("records_with_both", ascending=False).reset_index(drop=True)


def coverage_matrix(facts: list[dict], level: str = "material_family") -> pd.DataFrame:
    frame = pd.DataFrame([{"system": f["system"], "entity": f[level], "property": f["property"],
                           "record_id": f["record_id"]} for f in facts])
    return frame.pivot_table(index=["system", "entity"], columns="property", values="record_id",
                             aggfunc="nunique", fill_value=0)


def gap_analysis(facts: list[dict], level: str = "material_family", min_records: int = 3,
                 min_property_share: float = 0.15) -> pd.DataFrame:
    """Material(-family) x property pairs with no data, restricted to meaningful gaps.

    A pair is a gap when the entity has >= `min_records` records in a system and the property
    is reported for >= `min_property_share` of that system's records, yet never for the entity.
    Gaps are ranked by how much is known about the entity (research leverage) and its African
    supply score.
    """
    frame = pd.DataFrame([{"system": f["system"], "entity": f[level], "property": f["property"],
                           "record_id": f["record_id"], "africa": f["africa"]["score"]} for f in facts])
    rows = []
    for system, sub in frame.groupby("system"):
        total_records = sub.record_id.nunique()
        share = sub.groupby("property").record_id.nunique() / total_records
        relevant = share[share >= min_property_share].index
        for entity, group in sub.groupby("entity"):
            records = group.record_id.nunique()
            if records < min_records or entity in ("Unspecified", "Other"):
                continue
            have = set(group.property)
            africa = group.africa.dropna().mean() if group.africa.notna().any() else None
            for prop in relevant:
                if prop not in have:
                    rows.append({"system": system, "entity": entity, "missing_property": prop,
                                 "entity_records": records, "property_share_in_system": round(float(share[prop]), 2),
                                 "africa_score": round(africa, 2) if africa is not None else None})
    gaps = pd.DataFrame(rows)
    if gaps.empty:
        return gaps
    gaps["priority"] = (gaps.entity_records.rank(pct=True) * 0.5 + gaps.property_share_in_system * 0.3
                        + gaps.africa_score.fillna(0.5) * 0.2).round(3)
    return gaps.sort_values("priority", ascending=False).reset_index(drop=True)


def sparse_cells(facts: list[dict], level: str = "material_family", max_records: int = 2) -> pd.DataFrame:
    """Thinly evidenced (1-2 records) entity-property cells: candidates for targeted literature mining."""
    matrix = coverage_matrix(facts, level)
    stacked = matrix.stack()
    thin = stacked[(stacked > 0) & (stacked <= max_records)].reset_index()
    thin.columns = ["system", "entity", "property", "records"]
    return thin.sort_values("records").reset_index(drop=True)


def family_property_stats(facts: list[dict], prop: str, system: str | None = None) -> pd.DataFrame:
    frame = pd.DataFrame([f for f in facts if f["property"] == prop and (system is None or f["system"] == system)
                          and is_reliable(f)])
    if frame.empty:
        return frame
    unit = frame.unit.mode()[0]
    frame = frame[frame.unit == unit]
    return (frame.groupby("material_family").value.agg(["count", "median", "max"]).reset_index()
            .assign(unit=unit).sort_values("median", ascending=False).reset_index(drop=True))


def dopant_effects(facts: list[dict]) -> pd.DataFrame:
    """Per-dopant summary for LLZO materials across every reported property."""
    rows = []
    for fact in facts:
        if fact["system"] != "LLZO" or not is_reliable(fact):
            continue
        for dopant in fact.get("dopants") or ["undoped / not stated"]:
            rows.append({"dopant": dopant, "property": fact["property"], "value": fact["value"], "unit": fact["unit"],
                         "family": fact["material_family"]})
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return (frame.groupby(["dopant", "property", "unit"]).value.agg(["count", "median", "min", "max"])
            .reset_index().sort_values(["property", "median"], ascending=[True, False]))


# ---------------------------------------------------------------- traversal
def find_nodes(G: nx.DiGraph, text: str) -> list[str]:
    """Nodes whose name appears in `text` (longest names first; short names need word boundaries)."""
    import re

    lowered = text.lower()
    hits = []
    for n, data in G.nodes(data=True):
        name = str(data["name"]).lower()
        if len(name) < 2 or data["type"] in ("Paper",):
            continue
        pattern = rf"(?<![a-z0-9]){re.escape(name)}(?![a-z0-9])"
        if re.search(pattern, lowered):
            hits.append(n)
    return sorted(hits, key=lambda n: -len(G.nodes[n]["name"]))


def get_neighborhood(G: nx.DiGraph, entities: list[str], depth: int = 1, max_nodes: int = 120) -> nx.DiGraph:
    keep: set[str] = set()
    frontier = [e for e in entities if e in G]
    undirected = G.to_undirected(as_view=True)
    for _ in range(depth + 1):
        next_frontier = []
        for n in frontier:
            if n in keep:
                continue
            keep.add(n)
            if len(keep) >= max_nodes:
                break
            # Expand through hub nodes (systems, properties) only one hop to avoid pulling in everything.
            if G.nodes[n]["type"] in ("System",) and n not in entities:
                continue
            next_frontier.extend(undirected.neighbors(n))
        frontier = next_frontier
        if len(keep) >= max_nodes:
            break
    return G.subgraph(keep).copy()


def serialize_subgraph(sub: nx.DiGraph, max_edges: int = 80) -> str:
    """Compact, citation-bearing text rendering of a subgraph for LLM context."""
    lines = []
    edges = sorted(sub.edges(data=True), key=lambda e: -(e[2].get("n") or 0))
    for u, v, data in edges[:max_edges]:
        un, vn = sub.nodes[u]["name"], sub.nodes[v]["name"]
        if data.get("relation") == "hasProperty":
            facts = ", ".join(data["fact_ids"][:4])
            lines.append(f"({un}) -hasProperty-> ({vn}): n={data['n']}, median={data['median']:.4g} {data['unit']}, "
                         f"range={min(data['values']):.4g}-{max(data['values']):.4g} [facts: {facts}]")
        else:
            lines.append(f"({un}) -{data.get('relation')}-> ({vn})")
    return "\n".join(lines)


# ---------------------------------------------------------------- export
def to_graphml(G: nx.DiGraph, path=GRAPHML_PATH):
    export = nx.DiGraph()
    for n, data in G.nodes(data=True):
        export.add_node(n, **{k: json.dumps(v) if isinstance(v, (list, dict)) else ("" if v is None else v)
                              for k, v in data.items()})
    for u, v, data in G.edges(data=True):
        export.add_edge(u, v, **{k: json.dumps(val) if isinstance(val, (list, dict)) else val
                                 for k, val in data.items()})
    path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(export, path)
    return path


def graph_summary(G: nx.DiGraph) -> dict:
    return {"nodes": G.number_of_nodes(), "edges": G.number_of_edges(),
            "node_types": dict(Counter(d["type"] for _, d in G.nodes(data=True))),
            "edge_types": dict(Counter(d.get("relation") for _, _, d in G.edges(data=True)))}


def research_map(facts: list[dict] | None = None) -> dict:
    facts = facts if facts is not None else load_facts()
    G = build_graph(facts)
    return {
        "graph": graph_summary(G),
        "top_materials": centrality(G, "Material").to_dict("records"),
        "top_families": centrality(G, "MaterialFamily").to_dict("records"),
        "top_elements": centrality(G, "Element").to_dict("records"),
        "property_cooccurrence": property_cooccurrence(facts).head(15).to_dict("records"),
        "gaps": gap_analysis(facts).head(40).to_dict("records"),
        "dopant_effects": dopant_effects(facts).to_dict("records"),
    }


if __name__ == "__main__":
    all_facts = load_facts()
    graph = build_graph(all_facts)
    to_graphml(graph)
    REPORTS_DIR.mkdir(exist_ok=True)
    report = research_map(all_facts)
    (REPORTS_DIR / "research_map.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report["graph"], indent=2))
