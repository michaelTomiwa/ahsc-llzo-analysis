"""REST API for the knowledge engine (Track 1 -> Tracks 2, 4, 5).

    uvicorn api:app --reload        # OpenAPI docs at http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from knowledge_engine import __version__, llm
from knowledge_engine.africa import AFRICAN_CONSTRAINTS, supply_table
from knowledge_engine.config import SCHEMA_PATH
from knowledge_engine.extraction import extract
from knowledge_engine.graph_rag import get_engine, graph_rag
from knowledge_engine.hypothesis_engine import EXAMPLE_GOALS, generate_hypotheses
from knowledge_engine.hypothesis_evaluator import to_design_candidates, to_experiment_plan
from knowledge_engine.knowledge_graph import (centrality, find_nodes, gap_analysis, get_neighborhood,
                                              graph_summary, property_cooccurrence, serialize_subgraph)

app = FastAPI(
    title="AHSC-LLZO Materials Knowledge Engine",
    version=__version__,
    description="Evidence-grounded facts, knowledge graph, GraphRAG and Africa-aware hypothesis generation for "
                "asymmetric hybrid supercapacitors (AHSC) and garnet LLZO solid electrolytes.",
)


class ExtractRequest(BaseModel):
    text: str = Field(..., description="Abstract, paragraph or full text of a paper")
    doi: str | None = None
    title: str | None = None
    use_llm: bool | None = Field(None, description="Force LLM (true) or rule-based (false); default auto")


class AskRequest(BaseModel):
    question: str = Field(..., examples=["What dopants improve LLZO ionic conductivity?"])


class HypothesisRequest(BaseModel):
    goal: str = Field(..., examples=EXAMPLE_GOALS[:1])
    constraints: dict = Field(default_factory=dict, description="Overrides merged into AFRICAN_CONSTRAINTS")
    n: int = Field(5, ge=1, le=10)
    africa_focus: bool = True


@app.get("/health")
def health() -> dict:
    engine = get_engine()
    return {"status": "ok", "version": __version__, "llm_provider": llm.provider(), "facts": len(engine.facts),
            "search_backend": engine.index.backend_name, "graph": graph_summary(engine.graph)}


@app.get("/schema")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@app.get("/facts")
def facts(system: str | None = None, prop: str | None = Query(None, alias="property"), material: str | None = None,
          min_confidence: float = 0.0, limit: int = Query(100, le=2000)) -> list[dict]:
    rows = [f for f in get_engine().facts
            if (system is None or f["system"] == system) and (prop is None or f["property"] == prop)
            and (material is None or material.lower() in f["material"].lower()) and f["confidence"] >= min_confidence]
    return [{k: v for k, v in f.items() if k != "evidence_text"} for f in rows[:limit]]


@app.get("/search")
def search(q: str, k: int = Query(10, le=50), system: str | None = None) -> list[dict]:
    return get_engine().index.search(q, k=k, system=system)


@app.post("/extract")
def extract_endpoint(request: ExtractRequest) -> dict:
    source = {"id": request.doi or "api", "type": "api_text", "doi": request.doi, "title": request.title}
    return extract(request.text, source, use_llm=request.use_llm)


@app.post("/ask")
def ask(request: AskRequest) -> dict:
    return graph_rag(request.question)


@app.post("/hypotheses")
def hypotheses(request: HypothesisRequest) -> dict:
    report = generate_hypotheses(request.goal, request.constraints, request.n, request.africa_focus)
    report["track2_design_candidates"] = to_design_candidates(report)
    report["track4_experiment_plan"] = to_experiment_plan(report)
    return report


@app.get("/graph/{material}")
def graph_neighborhood(material: str, depth: int = Query(1, ge=0, le=2)) -> dict:
    engine = get_engine()
    nodes = find_nodes(engine.graph, material) or [n for n in engine.graph if material.lower() in n.lower()][:5]
    if not nodes:
        raise HTTPException(404, f"No graph node matches '{material}'")
    sub = get_neighborhood(engine.graph, nodes[:3], depth=depth)
    return {"matched": nodes[:3], "summary": serialize_subgraph(sub),
            "nodes": [{"id": n, "type": d["type"], "name": d["name"]} for n, d in sub.nodes(data=True)],
            "edges": [{"source": u, "target": v, "relation": d.get("relation"), "median": d.get("median"),
                       "unit": d.get("unit"), "n": d.get("n")} for u, v, d in sub.edges(data=True)]}


@app.get("/research-map")
def research_map(level: str = "material_family") -> dict:
    engine = get_engine()
    return {"top_materials": centrality(engine.graph, "Material").to_dict("records"),
            "top_families": centrality(engine.graph, "MaterialFamily").to_dict("records"),
            "property_cooccurrence": property_cooccurrence(engine.facts).head(20).to_dict("records"),
            "gaps": gap_analysis(engine.facts, level=level).head(50).to_dict("records")}


@app.get("/africa/constraints")
def africa_constraints() -> dict:
    return {"constraints": AFRICAN_CONSTRAINTS, "element_supply": supply_table().to_dict("records")}
