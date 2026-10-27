# Pipeline Position

**Stage:** Knowledge (Track 1)

**Upstream inputs:** PDFs, abstracts (OpenAlex / Crossref), patents and lab notes as text, curated datasets
(the 533-record AHSC/LLZO thesis dataset).

**Downstream outputs:** structured evidence-grounded facts (JSONL), a knowledge graph (GraphML), research maps
(centrality, co-occurrence, gaps), and ranked hypotheses with validation experiments (JSON / Markdown).

```mermaid
flowchart LR
  subgraph Upstream
    P[PDFs / abstracts / lab notes]
    T[533 curated thesis records]
  end
  subgraph Track1[Track 1: Knowledge engine]
    X[LLM extraction + evidence grounding]
    F[(Facts JSONL\nschema.json)]
    S[Semantic index]
    G[(Knowledge graph)]
    R[GraphRAG]
    H[Hypothesis engine\n+ evaluator + Africa re-rank]
  end
  P --> X --> F
  T --> F
  F --> S & G
  S & G --> R
  G --> H
  H -->|design candidates| T2[Track 2: Design]
  F -->|curated training facts| T3[Track 3: Predict]
  H -->|experiment plan| T4[Track 4: Plan]
  F & G -->|schema + REST API| T5[Track 5: Data]
```

## Integration

| Track | What it receives | Format | Where |
|---|---|---|---|
| Track 2 (Design) | Ranked candidate compositions with target property, priority, Africa score and evidence fact ids | `track2_design_candidates.json` | App → Hypothesis Generator download, `POST /hypotheses` → `track2_design_candidates` |
| Track 3 (Predict) | Curated, unit-checked, quality-flagged training facts (the thesis RF/GB models consume these) | `data/thesis_facts.jsonl` | `GET /facts?property=...&min_confidence=0.9` |
| Track 4 (Plan) | One validation experiment per hypothesis: technique, max processing temperature, success metric, priority | `track4_experiment_plan.json` | App download, `POST /hypotheses` → `track4_experiment_plan` |
| Track 5 (Data) | Ontology, fact schema, graph export, REST API with OpenAPI docs | `schema.json`, `knowledge_graph.graphml`, `/docs` | `GET /schema`, `GET /graph/{material}` |

## Contracts

- Every fact carries `evidence_span` (verbatim), `source` (record id / DOI), `confidence` and `quality_flags`.
- Every hypothesis carries `supporting_fact_ids`, which resolve to facts, and per-criterion scores.
- Units follow `schema.json → properties_vocabulary`. Non-standard units are kept as reported, never silently converted.
