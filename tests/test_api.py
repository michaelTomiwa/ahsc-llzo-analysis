from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_health_and_schema():
    health = client.get("/health").json()
    assert health["status"] == "ok" and health["facts"] > 1000
    assert "relationships" in client.get("/schema").json()


def test_facts_and_search():
    facts = client.get("/facts", params={"system": "LLZO", "property": "ionic_conductivity", "limit": 5}).json()
    assert len(facts) == 5 and all(f["property"] == "ionic_conductivity" for f in facts)
    assert client.get("/search", params={"q": "MXene capacitance", "k": 3}).json()


def test_extract_endpoint():
    body = client.post("/extract", json={"text": "The PEO electrolyte reached 1.2 × 10−4 S cm−1 at 60 °C.",
                                         "use_llm": False}).json()
    assert body["facts"][0]["property"] == "ionic_conductivity" and body["grounding_rate"] == 1.0


def test_ask_hypotheses_graph():
    assert client.post("/ask", json={"question": "Which AHSC families have the best cycling stability?"}).json()["citations"]
    report = client.post("/hypotheses", json={"goal": "Improve AHSC cycling stability above 95% retention", "n": 3}).json()
    assert len(report["hypotheses"]) == 3 and report["track2_design_candidates"] and report["track4_experiment_plan"]
    graph = client.get("/graph/LLZO-0.5Ta").json()
    assert graph["nodes"] and graph["edges"]
    assert client.get("/graph/notamaterialxyz").status_code == 404
    assert client.get("/research-map").json()["gaps"]
    assert client.get("/africa/constraints").json()["element_supply"]
