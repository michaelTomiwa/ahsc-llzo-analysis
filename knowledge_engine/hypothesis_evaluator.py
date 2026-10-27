"""Phase 4.2-4.3: score hypotheses (relevance, novelty, feasibility, evidence) and re-rank by Africa.

    final = 0.75 * base + 0.25 * africa       (africa_focus=True)
    base  = 0.30 relevance + 0.20 novelty + 0.20 feasibility + 0.30 evidence

Relevance and feasibility use an LLM judge when configured, otherwise transparent
heuristics. Novelty and evidence are always computed from the knowledge graph, so they are
reproducible and auditable.
"""
from __future__ import annotations

import math
import re

from . import llm
from .africa import AFRICAN_CONSTRAINTS, africa_rerank_score, feasibility_from_temperature
from .chem import elements_in
from .facts import is_reliable
from .knowledge_graph import find_nodes

WEIGHTS = {"relevance": 0.30, "novelty": 0.20, "feasibility": 0.20, "evidence": 0.30}
AFRICA_WEIGHT = 0.25

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "relevance": {"type": "number"},
        "feasibility": {"type": "number"},
        "rationale": {"type": "string"},
    },
    "required": ["relevance", "feasibility", "rationale"],
    "additionalProperties": False,
}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]{3,}", text.lower())}


def heuristic_relevance(hypothesis: dict, goal: str, goal_info: dict) -> float:
    text = " ".join(str(hypothesis.get(k, "")) for k in ("title", "target_property", "expected_change",
                                                         "mechanistic_reasoning", "proposed_material"))
    goal_tokens = _tokens(goal)
    overlap = len(goal_tokens & _tokens(text)) / max(len(goal_tokens), 1)
    property_match = 1.0 if goal_info.get("property") and goal_info["property"] == hypothesis.get("target_property") else 0.0
    if goal_info.get("property") == "sintering_temperature" and "sinter" in text.lower():
        property_match = 1.0
    return round(min(1.0, 0.35 + 0.4 * property_match + 0.5 * overlap), 3)


def heuristic_feasibility(hypothesis: dict) -> float:
    temperature = feasibility_from_temperature(hypothesis.get("estimated_synthesis_temp_c"))
    standard = 1.0 if re.search(r"EIS|GCD|CV|XRD|cycl|impedance|charge", hypothesis.get("validation_experiment", ""), re.I) else 0.6
    avoid = sum(e in AFRICAN_CONSTRAINTS["avoid"] for e in hypothesis.get("elements", []))
    return round(max(0.0, 0.5 * temperature + 0.5 * standard - 0.2 * avoid), 3)


def check_literature_novelty(hypothesis: dict, engine) -> tuple[float, str]:
    """1.0 = nothing like it in the graph; low = the exact material-property pair is already reported."""
    target = hypothesis.get("target_property", "")
    material_nodes = [n for n in find_nodes(engine.graph, hypothesis.get("proposed_material", ""))
                      if n.startswith("Material:")]
    exact = [n for n in material_nodes if engine.graph.has_edge(n, f"Property:{target}")]
    if exact:
        reports = engine.graph.edges[exact[0], f"Property:{target}"]["n"]
        return round(max(0.15, 0.4 - 0.05 * reports), 3), f"already reported for {engine.graph.nodes[exact[0]]['name']} ({reports}x)"
    if material_nodes:
        return 0.65, "material is in the corpus but not for this property"
    hits = engine.index.search(f"{hypothesis.get('proposed_material', '')} {target.replace('_', ' ')}", k=1,
                               kinds=("fact",))
    if hits and hits[0]["score"] > 0.85:
        return 0.55, f"very similar fact exists ({hits[0]['id']})"
    return 0.9, "no matching material-property evidence in the corpus"


def count_supporting_edges(hypothesis: dict, engine) -> tuple[float, int, int]:
    """Evidence score from valid cited facts plus graph edges for the same family/elements and property."""
    cited = [i for i in hypothesis.get("supporting_fact_ids", []) if i in engine.by_id and is_reliable(engine.by_id[i])]
    target = hypothesis.get("target_property", "")
    elements = set(hypothesis.get("elements") or elements_in(hypothesis.get("proposed_material", "")))
    related = 0
    for fact in engine.facts:
        if fact["property"] == target and is_reliable(fact) and elements and \
                len(elements & set(fact["elements"]) - {"O", "H", "C", "N"}) >= 2:
            related += 1
    score = 1.0 - math.exp(-(len(cited) + 0.25 * min(related, 20)) / 4.0)
    return round(score, 3), len(cited), related


def llm_judge(hypothesis: dict, goal: str) -> dict | None:
    if not llm.available():
        return None
    prompt = (f"Goal: {goal}\nHypothesis: {hypothesis}\n\nScore 0-1: relevance (does it directly address the goal?) "
              f"and feasibility (can a typical African university or national lab test it within 6 months with "
              f"standard synthesis and EIS/GCD/XRD?). Give a one-sentence rationale.")
    result = llm.complete(prompt, schema=JUDGE_SCHEMA, effort="low")
    return result.data


def score_hypothesis(hypothesis: dict, goal: str, goal_info: dict, engine, constraints: dict | None = None,
                     africa_focus: bool = True, use_llm_judge: bool = True) -> dict:
    judged = llm_judge(hypothesis, goal) if use_llm_judge else None
    relevance = float(judged["relevance"]) if judged else heuristic_relevance(hypothesis, goal, goal_info)
    feasibility = float(judged["feasibility"]) if judged else heuristic_feasibility(hypothesis)
    novelty, novelty_note = check_literature_novelty(hypothesis, engine)
    evidence, cited, related = count_supporting_edges(hypothesis, engine)
    base = (WEIGHTS["relevance"] * relevance + WEIGHTS["novelty"] * novelty + WEIGHTS["feasibility"] * feasibility
            + WEIGHTS["evidence"] * evidence)
    africa = africa_rerank_score(hypothesis.get("elements") or elements_in(hypothesis.get("proposed_material", "")),
                                 hypothesis.get("estimated_synthesis_temp_c"), hypothesis.get("applications"))
    final = (1 - AFRICA_WEIGHT) * base + AFRICA_WEIGHT * africa["africa_score"] if africa_focus else base
    return {"relevance": round(relevance, 3), "novelty": novelty, "feasibility": round(feasibility, 3),
            "evidence": evidence, "base": round(base, 3), "africa": africa["africa_score"], "final": round(final, 3),
            "notes": {"novelty": novelty_note, "valid_cited_facts": cited, "related_graph_facts": related,
                      "judge": (judged or {}).get("rationale", "heuristic"), "africa_detail": africa}}


def rank_hypotheses(hypotheses: list[dict], goal: str, goal_info: dict, engine, constraints: dict | None = None,
                    africa_focus: bool = True) -> list[dict]:
    scored = [{**h, "scores": score_hypothesis(h, goal, goal_info, engine, constraints, africa_focus)} for h in hypotheses]
    # Drop duplicate proposals, keeping the best-scoring one.
    unique: dict[str, dict] = {}
    for h in sorted(scored, key=lambda h: -h["scores"]["final"]):
        unique.setdefault(h["proposed_material"].lower() + h.get("target_property", ""), h)
    ranked = list(unique.values())
    for rank, h in enumerate(ranked, start=1):
        h["rank"] = rank
    return ranked


# ---------------------------------------------------------------- exports
def to_markdown(report: dict) -> str:
    lines = [f"# Hypothesis report\n", f"**Goal:** {report['goal']}  ", f"**Generator:** {report['mode']}  ",
             f"**Africa focus:** {'on' if report['africa_focus'] else 'off'}\n"]
    for h in report["hypotheses"]:
        s = h["scores"]
        lines += [f"## {h['rank']}. {h['title']}", f"- **Proposed material:** {h['proposed_material']}",
                  f"- **Change:** {h['composition_change']}", f"- **Expected effect:** {h['expected_change']}",
                  f"- **Mechanism:** {h['mechanistic_reasoning']}",
                  f"- **Evidence (fact ids):** {', '.join(h.get('supporting_fact_ids') or []) or 'none (prior knowledge)'}",
                  f"- **Max processing temperature:** {h.get('estimated_synthesis_temp_c') or 'unknown'} °C",
                  f"- **Validation experiment:** {h['validation_experiment']}",
                  f"- **Scores:** final {s['final']} | relevance {s['relevance']} | novelty {s['novelty']} | "
                  f"feasibility {s['feasibility']} | evidence {s['evidence']} | Africa {s['africa']}",
                  f"- **Notes:** {s['notes']['novelty']}; Africa supply {s['notes']['africa_detail']['african_supply']}; "
                  f"flags {s['notes']['africa_detail']['flags'] or 'none'}\n"]
    return "\n".join(lines)


def to_design_candidates(report: dict) -> list[dict]:
    """Track 2 (Design) hand-off: candidate compositions with target and priority."""
    return [{"candidate_id": f"H{h['rank']:02d}", "composition": h["proposed_material"],
             "elements": h.get("elements", []), "target_property": h.get("target_property"),
             "goal": report["goal"], "priority": h["scores"]["final"], "africa_score": h["scores"]["africa"],
             "evidence_fact_ids": h.get("supporting_fact_ids", [])} for h in report["hypotheses"]]


def to_experiment_plan(report: dict) -> list[dict]:
    """Track 4 (Plan) hand-off: one validation experiment per hypothesis, ordered by priority."""
    return [{"step": h["rank"], "hypothesis": h["title"], "material": h["proposed_material"],
             "experiment": h["validation_experiment"], "max_temperature_c": h.get("estimated_synthesis_temp_c"),
             "success_metric": h["expected_change"], "priority": h["scores"]["final"]} for h in report["hypotheses"]]
