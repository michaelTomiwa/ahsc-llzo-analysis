import json

from knowledge_engine import llm
from knowledge_engine.extraction import extract, rule_extract, validate
from knowledge_engine.graph_rag import graph_rag
from knowledge_engine.hypothesis_engine import EXAMPLE_GOALS, generate_hypotheses, parse_goal
from knowledge_engine.hypothesis_evaluator import to_design_candidates, to_experiment_plan, to_markdown
from knowledge_engine.knowledge_graph import (centrality, gap_analysis, get_neighborhood, property_cooccurrence,
                                              to_graphml)

ABSTRACT = ("Ta-doped Li6.4La3Zr1.4Ta0.6O12 sintered at 1150 °C showed an ionic conductivity of 6.1 × 10−4 S cm−1 at "
            "25 °C. The NiCo-LDH electrode delivered 1520 F g−1 at 1 A g−1 and retained 92% after 10,000 cycles; the "
            "device reached 45 Wh kg−1 at 800 W kg−1 within 0–1.6 V.")


def test_rule_extract_values():
    facts = {(f["property"], round(f["value"], 8)) for f in rule_extract(ABSTRACT)}
    assert ("ionic_conductivity", 6.1e-4) in facts
    assert ("specific_capacitance", 1520.0) in facts
    assert ("cycling_stability", 92.0) in facts
    assert ("sintering_temperature", 1150.0) in facts
    assert ("potential_window", 1.6) in facts


def test_extract_is_grounded():
    result = extract(ABSTRACT, use_llm=False)
    assert result["n_facts"] >= 6
    assert result["grounding_rate"] == 1.0
    garnet = next(f for f in result["facts"] if f["property"] == "ionic_conductivity")
    assert garnet["dopants"] == ["Ta"] and garnet["system"] == "LLZO"


def test_extraction_benchmark_quality():
    report = validate(use_llm=False, limit=150)
    assert report["precision"] > 0.8
    assert report["recall"] > 0.7
    assert report["evidence_grounding_rate"] >= 0.95


def test_graph_structure(engine, tmp_path):
    G = engine.graph
    types = {d["type"] for _, d in G.nodes(data=True)}
    assert {"Material", "Property", "Paper", "Element", "MaterialFamily", "Country"} <= types
    assert G.has_edge("Material:Garnet-type Li6.5La3Zr1.5Ta0.5O12 (LLZO)", "Dopant:Ta")
    assert not centrality(G, "MaterialFamily").empty
    assert not property_cooccurrence(engine.facts).empty
    gaps = gap_analysis(engine.facts)
    assert {"entity", "missing_property", "priority"} <= set(gaps.columns)
    sub = get_neighborhood(G, ["MaterialFamily:Garnet LLZO"], depth=1)
    assert sub.number_of_nodes() > 5
    path = to_graphml(G, tmp_path / "kg.graphml")
    assert path.stat().st_size > 10_000


def test_semantic_search(engine):
    hits = engine.index.search("Ta doped garnet ionic conductivity", k=10, system="LLZO")
    assert any("Ta" in hit["text"] or "LLZTO" in hit["text"] for hit in hits)


def test_graph_rag_offline(engine):
    result = graph_rag("What dopants improve LLZO ionic conductivity?", engine)
    assert result["mode"].startswith("offline")
    assert "ionic_conductivity" in result["entities"]["properties"]
    assert result["citations"] and all(c["evidence_span"] for c in result["citations"])
    assert "Ta" in result["answer"]


def test_parse_goal():
    parsed = parse_goal(EXAMPLE_GOALS[0])
    assert parsed["system"] == "LLZO" and parsed["property"] == "ionic_conductivity"
    assert abs(parsed["target"] - 1e-3) < 1e-12
    assert parse_goal(EXAMPLE_GOALS[2])["direction"] == "decrease"


def test_hypotheses_ranked_and_exportable(engine):
    report = generate_hypotheses(EXAMPLE_GOALS[1], n=5, engine=engine)
    hyps = report["hypotheses"]
    assert 3 <= len(hyps) <= 5
    finals = [h["scores"]["final"] for h in hyps]
    assert finals == sorted(finals, reverse=True)
    for h in hyps:
        assert set(h["scores"]) >= {"relevance", "novelty", "feasibility", "evidence", "africa", "final"}
        assert all(i in engine.by_id for i in h["supporting_fact_ids"])
    assert "# Hypothesis report" in to_markdown(report)
    assert to_design_candidates(report)[0]["candidate_id"] == "H01"
    assert to_experiment_plan(report)[0]["step"] == 1
    json.dumps({k: v for k, v in report.items()}, default=str)


def test_africa_focus_changes_ranking(engine):
    on = generate_hypotheses(EXAMPLE_GOALS[0], n=6, africa_focus=True, engine=engine)
    off = generate_hypotheses(EXAMPLE_GOALS[0], n=6, africa_focus=False, engine=engine)
    assert all(h["scores"]["final"] != h["scores"]["base"] for h in on["hypotheses"])
    assert all(h["scores"]["final"] == h["scores"]["base"] for h in off["hypotheses"])


def test_llm_layer_parses_structured_output(monkeypatch):
    """The Anthropic path returns parsed JSON; mocked so the test needs no key or network."""

    class Block:
        type = "text"
        text = '{"facts": []}'

    class Response:
        stop_reason = "end_turn"
        model = "claude-test"
        content = [Block()]

    class Messages:
        def create(self, **kwargs):
            assert kwargs["output_config"]["format"]["type"] == "json_schema"
            assert kwargs["fallbacks"] == "default"
            return Response()

    class FakeClient:
        def __init__(self):
            self.beta = type("Beta", (), {"messages": Messages()})()

    import anthropic

    monkeypatch.setattr(anthropic, "Anthropic", FakeClient)
    monkeypatch.setenv("KE_LLM_PROVIDER", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    result = llm.complete("hi", schema={"type": "object"})
    assert result.data == {"facts": []} and result.mode == "anthropic:claude-test"
