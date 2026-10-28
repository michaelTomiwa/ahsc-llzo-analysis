"""Build every knowledge-engine artefact in one command.

    python -m knowledge_engine.pipeline            # facts, graph, research map, reports
    python -m knowledge_engine.pipeline --harvest  # also pull new abstracts (network) and mine them
"""
from __future__ import annotations

import argparse
import json

from .config import FACTS_JSONL, GRAPHML_PATH, REPORTS_DIR, ROOT
from .evidence import grounding_report
from .facts import build_facts, facts_frame, load_facts, write_jsonl
from .record_sources import build as build_record_sources, coverage as record_coverage


def data_quality_report(facts: list[dict]) -> dict:
    frame = facts_frame(facts)
    flags: dict[str, int] = {}
    for fact in facts:
        for flag in fact["quality_flags"]:
            flags[flag] = flags.get(flag, 0) + 1
    return {
        "facts": len(facts),
        "records": int(frame.record_id.nunique()),
        "facts_by_system_property": {f"{s}/{p}": int(n) for (s, p), n in frame.groupby(["system", "property"]).size().items()},
        "mean_confidence": round(float(frame.confidence.mean()), 3),
        "quality_flags": dict(sorted(flags.items(), key=lambda kv: -kv[1])),
        "facts_with_doi": int(frame.doi.notna().sum()),
        "facts_with_review_doi": int(sum(1 for f in facts if f["source"].get("review_doi"))),
        "record_links": record_coverage(),
        "grounding": {k: v for k, v in grounding_report(facts).items() if k != "failures"},
    }


def write_example_hypotheses() -> None:
    """Showcase report: ranked hypotheses for each example goal (offline unless an LLM key is set)."""
    from .hypothesis_engine import EXAMPLE_GOALS, generate_hypotheses
    from .hypothesis_evaluator import to_markdown

    sections = [to_markdown(generate_hypotheses(goal, n=5)) for goal in EXAMPLE_GOALS]
    (REPORTS_DIR / "example_hypotheses.md").write_text("\n\n---\n\n".join(sections), encoding="utf-8")


def run(harvest: bool = False, llm: bool = False) -> dict:
    from .extraction import validate
    from .knowledge_graph import build_graph, research_map, to_graphml

    REPORTS_DIR.mkdir(exist_ok=True)
    build_record_sources()
    thesis = build_facts()
    write_jsonl(thesis, FACTS_JSONL)
    if harvest:
        from .literature import harvest as harvest_papers, mine
        harvest_papers()
        mine(use_llm=llm or None)
    facts = load_facts()
    to_graphml(build_graph(facts), GRAPHML_PATH)
    outputs = {
        "data_quality.json": data_quality_report(thesis),
        "extraction_validation.json": validate(use_llm=False),
        "research_map.json": research_map(facts),
    }
    for name, payload in outputs.items():
        (REPORTS_DIR / name).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_example_hypotheses()
    return {"facts": len(facts), "thesis_facts": len(thesis), "graph": outputs["research_map.json"]["graph"],
            "extraction": {k: outputs["extraction_validation.json"][k] for k in ("precision", "recall", "f1",
                                                                                 "evidence_grounding_rate")},
            "artefacts": [str(p.relative_to(ROOT)) for p in (FACTS_JSONL, GRAPHML_PATH)]
            + [f"reports/{name}" for name in outputs] + ["reports/example_hypotheses.md"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--harvest", action="store_true", help="harvest + mine OpenAlex abstracts (needs network)")
    parser.add_argument("--llm", action="store_true", help="use the LLM extractor when mining")
    args = parser.parse_args()
    print(json.dumps(run(args.harvest, args.llm), indent=2))
