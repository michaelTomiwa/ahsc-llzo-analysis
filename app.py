"""African Battery Materials Knowledge Engine - Streamlit app (Track 1).

Tabs: Literature Explorer · Knowledge Graph · Hypothesis Generator · Research Map · Africa Focus ·
Data Quality · Thesis Analytics (the original performance explorer and RF model, kept as a Track 3 bridge).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from ahsc_llzo_analysis import read_dataset
from knowledge_engine import llm
from knowledge_engine.africa import AFRICAN_CONSTRAINTS, africa_profile, supply_table
from knowledge_engine.config import AHSC_CSV, LLZO_CSV, MINERALS_CSV, REPORTS_DIR, SCHEMA_PATH
from knowledge_engine.extraction import extract, pdf_to_text, validate
from knowledge_engine.facts import facts_frame
from knowledge_engine.graph_rag import Engine, graph_rag
from knowledge_engine.hypothesis_engine import EXAMPLE_GOALS, generate_hypotheses
from knowledge_engine.hypothesis_evaluator import to_design_candidates, to_experiment_plan, to_markdown
from knowledge_engine.knowledge_graph import (centrality, coverage_matrix, dopant_effects, find_nodes, gap_analysis,
                                              get_neighborhood, property_cooccurrence, sparse_cells)
from knowledge_engine.pipeline import data_quality_report

COLORS = {"AHSC": "#167cbe", "LLZO": "#18a692"}
NODE_COLORS = {"Material": "#1264C4", "MaterialFamily": "#7B4FD0", "Property": "#D89217", "Element": "#18A692",
               "Dopant": "#D14D72", "Paper": "#8A94A6", "System": "#172038", "Country": "#2E9E4F"}


@st.cache_resource(show_spinner="Loading knowledge base, graph and semantic index...")
def engine() -> Engine:
    return Engine()


@st.cache_data
def thesis_data():
    ahsc, llzo = read_dataset(AHSC_CSV, "AHSC"), read_dataset(LLZO_CSV, "LLZO")
    return ahsc, llzo, pd.concat([ahsc, llzo], ignore_index=True), pd.read_csv(MINERALS_CSV)


@st.cache_data(show_spinner="Benchmarking extractor against curated thesis facts...")
def extraction_benchmark() -> dict:
    path = REPORTS_DIR / "extraction_validation.json"
    return json.loads(path.read_text()) if path.exists() else validate(use_llm=False)


def doi_link(citation: dict) -> str:
    if citation.get("doi"):
        link = f"[{citation['doi']}](https://doi.org/{citation['doi']})"
    elif citation.get("url"):
        link = f"[paper]({citation['url']})"
    else:
        link = citation["source"]
    if citation.get("review_doi"):
        qualifier = "" if citation.get("review_link") == "verified_row" else ", probable"
        link += f" · curated from review [{citation['review_doi']}](https://doi.org/{citation['review_doi']}){qualifier}"
    return link


def show_citations(citations: list[dict], limit: int = 10) -> None:
    for c in citations[:limit]:
        flags = f" · ⚠ {', '.join(c['quality_flags'])}" if c.get("quality_flags") else ""
        st.markdown(f"- **{c['material']}** — {c['property'].replace('_', ' ')} = {c['value']:.4g} {c['unit']}"
                    f"{' (' + c['condition'] + ')' if c.get('condition') else ''}  \n"
                    f"  *Evidence:* “{c['evidence_span']}” · *Source:* {doi_link(c)} · `{c['fact_id']}` · "
                    f"confidence {c['confidence']}{flags}")


def pyvis_html(sub, height: int = 620) -> str:
    from pyvis.network import Network

    net = Network(height=f"{height}px", width="100%", directed=True, bgcolor="#ffffff", font_color="#172038",
                  cdn_resources="in_line")
    net.barnes_hut(gravity=-2500, central_gravity=0.5, spring_length=110)
    for node, data in sub.nodes(data=True):
        label = str(data["name"])
        net.add_node(node, label=label[:28] + ("…" if len(label) > 28 else ""), title=f"{data['type']}: {label}",
                     color=NODE_COLORS.get(data["type"], "#999"), size=22 if data["type"] in ("Material", "Property") else 14)
    for u, v, data in sub.edges(data=True):
        title = data.get("relation", "")
        if data.get("relation") == "hasProperty":
            title += f": median {data['median']:.4g} {data['unit']} (n={data['n']})"
        net.add_edge(u, v, title=title, color="#c5cde0", arrows="to")
    return net.generate_html()


st.set_page_config(page_title="African Battery Materials Knowledge Engine", page_icon="⚡", layout="wide")
st.markdown("""<style>
.stApp{background:#f7f8fc;color:#172038}[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1635,#13285c)}
[data-testid="stSidebar"] *{color:#f4f7ff!important}.hero{background:linear-gradient(120deg,#081a3c,#1a4d9a 63%,#18a6a6);
border-radius:22px;padding:1.8rem 2.2rem;color:#fff;margin-bottom:1.1rem;box-shadow:0 18px 50px rgba(12,38,88,.2)}
.hero h1{font-size:2.3rem;line-height:1.05;margin:0 0 .5rem;color:#fff;letter-spacing:-.04em}.hero p{margin:0;color:#dceaff}
[data-testid="stMetric"]{background:#fff;border:1px solid #e5e9f3;border-radius:16px;padding:1rem}
.kicker{color:#168d94;font-size:.78rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}
.stTabs [data-baseweb="tab-list"]{gap:1rem;border-bottom:1px solid #e4e9f2}.stTabs [data-baseweb="tab"]{height:46px;font-weight:600}
</style>""", unsafe_allow_html=True)

E = engine()
facts_df = facts_frame(E.facts)

with st.sidebar:
    st.markdown("## Knowledge engine")
    mode = llm.provider()
    st.markdown(f"**LLM:** {'🟢 ' + mode if mode != 'offline' else '⚪ offline (rule-based fallbacks)'}")
    st.markdown(f"**Search:** {E.index.backend_name}")
    st.markdown(f"**Facts:** {len(E.facts):,} · **records:** {facts_df.record_id.nunique():,}")
    st.markdown(f"**Graph:** {E.graph.number_of_nodes():,} nodes · {E.graph.number_of_edges():,} edges")
    st.markdown("---")
    africa_focus = st.toggle("Africa-first mode", value=True,
                             help="Re-ranks retrieval and hypotheses by African element supply, <1000 °C processing "
                                  "and off-grid/EV/grid applications.")
    system_filter = st.multiselect("Systems", ["AHSC", "LLZO"], default=["AHSC", "LLZO"])
    st.markdown("---\nSet ANTHROPIC_API_KEY in .env to enable LLM extraction, GraphRAG synthesis and hypothesis agents.")

st.markdown("""<div class="hero"><div class="kicker" style="color:#82f0df">Track 1 · Literature → Knowledge → Hypotheses</div>
<h1>African Battery Materials Knowledge Engine</h1><p>An LLM-powered engine that extracts evidence-grounded facts from
AHSC and LLZO literature, builds a knowledge graph, and generates testable hypotheses under African constraints —
validated on 533 manually curated records.</p></div>""", unsafe_allow_html=True)

tabs = st.tabs(["Literature Explorer", "Knowledge Graph", "Hypothesis Generator", "Research Map", "Africa Focus",
                "Data Quality", "Thesis Analytics"])

# ------------------------------------------------------------------ Literature Explorer
with tabs[0]:
    st.markdown("<div class='kicker'>Semantic search · GraphRAG · extraction</div>", unsafe_allow_html=True)
    ask_col, search_col = st.columns([1.2, 1])
    with ask_col:
        st.subheader("Ask the knowledge graph")
        question = st.text_input("Research question", "What dopants improve LLZO ionic conductivity?")
        examples = st.columns(3)
        for col, q in zip(examples, ["Which AHSC electrode families give the highest specific capacitance?",
                                     "How stable are MnO2-based supercapacitors over long cycling?",
                                     "Which polymer electrolytes exceed 1 mS/cm?"]):
            if col.button(q[:42] + "…", help=q, width="stretch"):
                question = q
        if question:
            with st.spinner("Linking entities, traversing graph, synthesising..."):
                result = graph_rag(question, E)
            st.markdown(result["answer"])
            st.caption(f"Mode: {result['mode']} · entities: {result['entities']['mode']} · "
                       f"{len(result['subgraph']['nodes'])} graph nodes in context")
            with st.expander(f"Evidence ({len(result['citations'])} cited facts)", expanded=True):
                show_citations(result["citations"])
    with search_col:
        st.subheader("Semantic fact search")
        query = st.text_input("Search facts, abstracts and mineral notes", "biomass activated carbon high retention")
        min_africa = st.slider("Minimum Africa supply score", 0.0, 1.0, 0.0 if not africa_focus else 0.5, 0.1)
        if query:
            hits = E.index.search(query, k=12, system=system_filter[0] if len(system_filter) == 1 else None,
                                  min_africa=min_africa)
            for hit in hits:
                fact = E.by_id.get(hit["id"])
                if fact:
                    st.markdown(f"**{fact['material']}** · {fact['property_label']} = **{fact['value']:.4g} {fact['unit']}** "
                                f"· {fact['system']} · Africa {fact['africa']['score']}  \n"
                                f"<small>“{fact['evidence_span']}” — `{fact['id']}` · score {hit['score']}</small>",
                                unsafe_allow_html=True)
                else:
                    st.markdown(f"**{hit['metadata']['material'] or hit['kind']}** — {hit['text'][:220]}…")
    st.markdown("---")
    st.subheader("Extract facts from a new paper")
    st.caption("LLM extraction with schema-enforced JSON when an API key is set; transparent regex extractor otherwise. "
               "Every fact is checked against a verbatim span of the source text.")
    up_col, text_col = st.columns([1, 2])
    upload = up_col.file_uploader("PDF or text", type=["pdf", "txt"])
    sample = ("Ta-doped Li6.4La3Zr1.4Ta0.6O12 sintered at 1150 °C showed an ionic conductivity of 6.1 × 10−4 S cm−1 "
              "at 25 °C. The NiCo-LDH electrode delivered 1520 F g−1 at 1 A g−1 and retained 92% after 10,000 cycles.")
    text = text_col.text_area("…or paste an abstract", sample, height=110)
    if st.button("Extract structured facts", type="primary"):
        if upload is not None and upload.name.lower().endswith(".pdf"):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
                handle.write(upload.getvalue())
            text = pdf_to_text(Path(handle.name))
        elif upload is not None:
            text = upload.getvalue().decode("utf-8", errors="replace")
        result = extract(text, {"id": upload.name if upload else "pasted", "type": "user_text"})
        st.success(f"{result['n_facts']} facts · grounding {result['grounding_rate']} · mode {result['mode']}")
        if result["facts"]:
            table = pd.DataFrame([{k: f[k] for k in ("material", "property", "value", "unit", "condition", "evidence_span",
                                                     "grounded", "confidence")} | {"africa": f["africa"]["score"]}
                                  for f in result["facts"]])
            st.dataframe(table, width="stretch", hide_index=True)
            st.download_button("Download facts (JSONL)", "\n".join(json.dumps(f) for f in result["facts"]),
                               "extracted_facts.jsonl", "application/json")

# ------------------------------------------------------------------ Knowledge Graph
with tabs[1]:
    st.markdown("<div class='kicker'>Interactive knowledge graph</div>", unsafe_allow_html=True)
    left, right = st.columns([1, 2.2])
    with left:
        families = sorted({f["material_family"] for f in E.facts if f["system"] in system_filter})
        focus_kind = st.radio("Focus on", ["Material family", "Material", "Element / dopant"], horizontal=True)
        if focus_kind == "Material family":
            choice = st.selectbox("Family", families, index=families.index("Garnet LLZO") if "Garnet LLZO" in families else 0)
            seeds = [f"MaterialFamily:{choice}"]
        elif focus_kind == "Material":
            materials = facts_df[facts_df.system.isin(system_filter)].material.value_counts().index.tolist()
            choice = st.selectbox("Material", materials)
            seeds = [f"Material:{choice}"]
        else:
            elements = sorted(n.split(":", 1)[1] for n in E.graph if n.startswith(("Element:", "Dopant:")))
            choice = st.selectbox("Element or dopant", elements, index=elements.index("Ta") if "Ta" in elements else 0)
            seeds = [n for n in (f"Element:{choice}", f"Dopant:{choice}") if n in E.graph]
        depth = st.slider("Traversal depth", 1, 3, 2)
        max_nodes = st.slider("Max nodes", 30, 250, 90, 10)
        sub = get_neighborhood(E.graph, seeds, depth=depth, max_nodes=max_nodes)
        st.metric("Nodes / edges", f"{sub.number_of_nodes()} / {sub.number_of_edges()}")
        st.markdown(" ".join(f"<span style='color:{c}'>●</span> {k}" for k, c in NODE_COLORS.items()), unsafe_allow_html=True)
        prop_edges = [(E.graph.nodes[u]["name"], E.graph.nodes[v]["name"], d) for u, v, d in sub.edges(data=True)
                      if d.get("relation") == "hasProperty"]
        if prop_edges:
            st.dataframe(pd.DataFrame([{"material": u, "property": v, "n": d["n"], "median": d["median"], "unit": d["unit"]}
                                       for u, v, d in prop_edges]).sort_values("n", ascending=False),
                         hide_index=True, width="stretch", height=240)
    with right:
        try:
            components.html(pyvis_html(sub), height=640, scrolling=False)
        except ImportError:
            st.info("Install `pyvis` for the interactive network view.")
    st.download_button("Download full graph (GraphML)", (Path("data") / "knowledge_graph.graphml").read_bytes()
                       if (Path("data") / "knowledge_graph.graphml").exists() else b"", "knowledge_graph.graphml")

# ------------------------------------------------------------------ Hypothesis Generator
with tabs[2]:
    st.markdown("<div class='kicker'>Goal + constraints → ranked, testable hypotheses</div>", unsafe_allow_html=True)
    goal_col, constraint_col = st.columns([1.4, 1])
    with goal_col:
        preset = st.selectbox("Example goals", EXAMPLE_GOALS)
        goal = st.text_area("Research goal", preset, height=80)
        n = st.slider("Number of hypotheses", 3, 8, 5)
    with constraint_col:
        max_temp = st.number_input("Max synthesis temperature (°C)", 100, 1500, AFRICAN_CONSTRAINTS["max_synthesis_temp_c"], 50)
        preferred = st.multiselect("Preferred elements", sorted(supply_table().element), AFRICAN_CONSTRAINTS["elements"])
        apps = st.multiselect("Applications", AFRICAN_CONSTRAINTS["applications"], AFRICAN_CONSTRAINTS["applications"][:3])
    if st.button("Generate hypotheses", type="primary"):
        with st.spinner("Retrieving graph context, generating and scoring hypotheses..."):
            st.session_state.report = generate_hypotheses(goal, {"max_synthesis_temp_c": max_temp, "elements": preferred,
                                                                 "applications": apps}, n, africa_focus, E)
    report = st.session_state.get("report")
    if report:
        st.caption(f"Generator: {report['mode']} · parsed goal: {report['goal_parsed']} · Africa focus "
                   f"{'on' if report['africa_focus'] else 'off'}")
        score_table = pd.DataFrame([{"rank": h["rank"], "hypothesis": h["title"], **{k: h["scores"][k] for k in
                                     ("final", "relevance", "novelty", "feasibility", "evidence", "africa")}}
                                    for h in report["hypotheses"]])
        st.dataframe(score_table.style.background_gradient(cmap="Blues", subset=["final"]).format(precision=2),
                     hide_index=True, width="stretch")
        for h in report["hypotheses"]:
            s = h["scores"]
            with st.expander(f"#{h['rank']} · {h['title']} — final {s['final']:.2f}", expanded=h["rank"] == 1):
                st.markdown(f"**Proposed material:** {h['proposed_material']}  \n**Change:** {h['composition_change']}  \n"
                            f"**Expected effect:** {h['expected_change']}  \n**Mechanism:** {h['mechanistic_reasoning']}  \n"
                            f"**Validation experiment:** {h['validation_experiment']}  \n"
                            f"**Max processing temperature:** {h.get('estimated_synthesis_temp_c') or 'unknown'} °C · "
                            f"**Origin:** {h.get('origin', 'llm')}")
                st.caption(f"Novelty: {s['notes']['novelty']} · valid cited facts: {s['notes']['valid_cited_facts']} · "
                           f"related graph facts: {s['notes']['related_graph_facts']} · Africa supply "
                           f"{s['notes']['africa_detail']['african_supply']} · flags {s['notes']['africa_detail']['flags'] or 'none'}")
                support = [E.by_id[i] for i in h.get("supporting_fact_ids", []) if i in E.by_id]
                for fact in support[:5]:
                    st.markdown(f"- `{fact['id']}` {fact['material']}: {fact['value']:.4g} {fact['unit']} — "
                                f"“{fact['evidence_span']}” ({fact['source'].get('doi') or fact['source'].get('review_doi') or fact['source']['file']})")
        export = {k: v for k, v in report.items() if k != "context"}
        d1, d2, d3, d4 = st.columns(4)
        d1.download_button("Hypotheses (JSON)", json.dumps(export, indent=2, default=str), "hypotheses.json", "application/json")
        d2.download_button("Report (Markdown)", to_markdown(report), "hypothesis_report.md", "text/markdown")
        d3.download_button("Track 2 design candidates", json.dumps(to_design_candidates(report), indent=2),
                           "track2_design_candidates.json", "application/json")
        d4.download_button("Track 4 experiment plan", json.dumps(to_experiment_plan(report), indent=2, default=str),
                           "track4_experiment_plan.json", "application/json")
        with st.expander("Knowledge-graph context sent to the generator"):
            st.text(report["context"])

# ------------------------------------------------------------------ Research Map
with tabs[3]:
    st.markdown("<div class='kicker'>Centrality · co-occurrence · gaps</div>", unsafe_allow_html=True)
    scoped = [f for f in E.facts if f["system"] in system_filter]
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Most-studied material families")
        fam = centrality(E.graph, "MaterialFamily", 15)
        st.altair_chart(alt.Chart(fam).mark_bar(color="#7B4FD0", cornerRadiusEnd=4).encode(
            y=alt.Y("node:N", sort="-x", title=None), x=alt.X("papers:Q", title="Records"),
            tooltip=["node", "papers", "degree_centrality"]).properties(height=380), width="stretch")
    with c2:
        st.subheader("Most central materials & components")
        mats = centrality(E.graph, "Material", 15)
        st.altair_chart(alt.Chart(mats).mark_bar(color="#1264C4", cornerRadiusEnd=4).encode(
            y=alt.Y("node:N", sort="-x", title=None), x=alt.X("papers:Q", title="Records"),
            tooltip=["node", "papers", "degree_centrality"]).properties(height=380), width="stretch")
    st.subheader("Coverage map: material family × property (records)")
    cover = coverage_matrix(scoped).reset_index().melt(["system", "entity"], var_name="property", value_name="records")
    st.altair_chart(alt.Chart(cover).mark_rect().encode(
        x=alt.X("property:N", title=None), y=alt.Y("entity:N", title=None),
        color=alt.Color("records:Q", scale=alt.Scale(scheme="blues")), tooltip=["system", "entity", "property", "records"]
    ).properties(height=26 * cover.entity.nunique() + 40), width="stretch")
    g1, g2 = st.columns([1.3, 1])
    with g1:
        st.subheader("Research gaps (no data yet)")
        gaps = gap_analysis(scoped)
        st.dataframe(gaps.head(30), hide_index=True, width="stretch")
        st.download_button("Download gaps (CSV)", gaps.to_csv(index=False), "research_gaps.csv", "text/csv")
    with g2:
        st.subheader("Property co-occurrence")
        st.dataframe(property_cooccurrence(scoped).head(15), hide_index=True, width="stretch")
        st.subheader("Thinly evidenced cells (1-2 records)")
        st.dataframe(sparse_cells(scoped).head(15), hide_index=True, width="stretch")
    if "LLZO" in system_filter:
        st.subheader("LLZO dopant summary")
        st.dataframe(dopant_effects(E.facts), hide_index=True, width="stretch")

# ------------------------------------------------------------------ Africa Focus
with tabs[4]:
    st.markdown("<div class='kicker'>Africa as a design principle</div>", unsafe_allow_html=True)
    st.markdown("Every fact, graph node and hypothesis carries an **Africa supply score** (share of its non-trivial "
                "elements with established African supply, weighted by producer status). Hypotheses are re-ranked by "
                f"supply, processing temperature (≤ {AFRICAN_CONSTRAINTS['max_synthesis_temp_c']} °C) and application fit.")
    a1, a2 = st.columns([1, 1.2])
    with a1:
        st.subheader("Element supply table")
        st.dataframe(supply_table()[["element", "status", "african_countries", "usgs_2024_african_production",
                                    "verification", "source_url"]], hide_index=True,
                     width="stretch", height=420)
    with a2:
        st.subheader("Best-performing Africa-compatible materials")
        prop = st.selectbox("Property", sorted(facts_df[facts_df.system.isin(system_filter)].property.unique()),
                            index=0)
        threshold = st.slider("Minimum Africa score", 0.0, 1.0, 0.8, 0.05)
        sub = facts_df[(facts_df.property == prop) & facts_df.system.isin(system_filter) & (facts_df.africa_score >= threshold)]
        unit = sub.unit.mode()[0] if not sub.empty else ""
        sub = sub[sub.unit == unit].sort_values("value", ascending=False)
        st.dataframe(sub[["material", "material_family", "value", "unit", "condition", "africa_score", "id"]].head(25),
                     hide_index=True, width="stretch", height=380)
    st.subheader("Africa supply score vs performance")
    scatter = facts_df[(facts_df.property == prop) & facts_df.system.isin(system_filter) & facts_df.africa_score.notna()]
    scatter = scatter[scatter.unit == (scatter.unit.mode()[0] if not scatter.empty else "")]
    st.altair_chart(alt.Chart(scatter).mark_circle(size=60, opacity=.7).encode(
        x=alt.X("africa_score:Q", title="Africa supply score"), y=alt.Y("value:Q", title=f"{prop} ({unit})", scale=alt.Scale(type="log")),
        color=alt.Color("system:N", scale=alt.Scale(domain=list(COLORS), range=list(COLORS.values()))),
        tooltip=["material", "material_family", "value", "africa_score", "id"]).properties(height=320).interactive(),
        width="stretch")
    _, _, _, minerals = thesis_data()
    st.subheader("Critical-minerals context (USGS)")
    st.dataframe(minerals[["country", "commodity", "role_or_status", "year", "production_or_capacity", "unit", "notes"]],
                 hide_index=True, width="stretch")
    with st.expander("Check a composition"):
        formula = st.text_input("Formula or material name", "Li6.4La3Zr1.4Ta0.6O12")
        from knowledge_engine.chem import elements_in
        st.json(africa_profile(elements_in(formula)))

# ------------------------------------------------------------------ Data Quality
with tabs[5]:
    st.markdown("<div class='kicker'>Scientific rigour</div>", unsafe_allow_html=True)
    quality = data_quality_report([f for f in E.facts if f["source"]["type"] == "thesis_curated_record"])
    bench = extraction_benchmark()
    m = st.columns(5)
    m[0].metric("Facts", f"{quality['facts']:,}", help=f"from {quality['records']} curated records with numeric data")
    m[1].metric("Evidence grounding", f"{quality['grounding']['grounding_rate']:.0%}")
    m[2].metric("Extractor precision", f"{bench['precision']:.2f}")
    m[3].metric("Extractor recall", f"{bench['recall']:.2f}")
    m[4].metric("Mean confidence", f"{quality['mean_confidence']:.2f}")
    st.caption(f"Extractor: {bench['extractor']} · {bench['records']} records · {bench['note']}")
    q1, q2 = st.columns(2)
    with q1:
        st.subheader("Extraction precision / recall by property")
        per = pd.DataFrame(bench["per_property"]).T.reset_index(names="property").dropna(subset=["recall"])
        st.altair_chart(alt.Chart(per.melt("property", ["precision", "recall"])).mark_bar().encode(
            x=alt.X("value:Q", scale=alt.Scale(domain=[0, 1])), y=alt.Y("property:N", title=None), color="variable:N",
            yOffset="variable:N", tooltip=["property", "variable", "value"]).properties(height=300), width="stretch")
    with q2:
        st.subheader("Quality flags raised during digitisation")
        flags = pd.DataFrame(list(quality["quality_flags"].items()), columns=["flag", "facts"])
        st.altair_chart(alt.Chart(flags).mark_bar(color="#D89217").encode(y=alt.Y("flag:N", sort="-x", title=None),
                        x="facts:Q", tooltip=["flag", "facts"]).properties(height=300), width="stretch")
    st.subheader("Flagged facts to review")
    flagged = facts_df[facts_df.quality_flags.map(lambda f: bool(set(f) - {"unit_assumed"}))]
    st.dataframe(flagged[["id", "material", "property", "value", "unit", "evidence_span", "quality_flags", "confidence"]],
                 hide_index=True, width="stretch")
    links = quality["record_links"]
    st.markdown(f"**Source links:** {links['paper_doi']} records with a paper DOI ({links['paper_doi_value_verified']} "
                f"verified against the paper's own values, {links['paper_doi_title_match']} by exact title), "
                f"{links['paper_verified_url_only']} verified papers without a DOI, {links['source_review_verified_row']} "
                f"records traced to a verified source-review table and {links['source_review_block_inferred']} more by "
                f"block inference. Provenance: `data/provenance/`; resolver: `python -m knowledge_engine.record_sources resolve`.")
    with st.expander("Ontology (schema.json)"):
        st.json(json.loads(SCHEMA_PATH.read_text()))
    st.download_button("Download all facts (JSONL)", "\n".join(json.dumps(f, ensure_ascii=False) for f in E.facts),
                       "thesis_facts.jsonl", "application/json")

# ------------------------------------------------------------------ Thesis Analytics (Track 3 bridge)
with tabs[6]:
    ahsc, llzo, combined, _ = thesis_data()
    st.markdown("<div class='kicker'>Original thesis analytics · bridge to Track 3 (prediction)</div>", unsafe_allow_html=True)
    metrics = {"Potential midpoint": "potential_mid_v", "Capacitance / capacity": "capacitance_capacity_value",
               "Specific energy": "specific_energy_wh_kg", "Specific power": "specific_power_w_kg",
               "Cycling stability": "cycling_stability_pct", "Ionic conductivity": "ionic_conductivity_s_cm"}
    view = combined[combined.dataset.isin(system_filter)]
    c1, c2 = st.columns(2)
    x_name = c1.selectbox("X axis", list(metrics), index=1)
    y_name = c2.selectbox("Y axis", list(metrics), index=4)
    dots = view.dropna(subset=[metrics[x_name], metrics[y_name]])
    st.altair_chart(alt.Chart(dots).mark_circle(size=70, opacity=.68).encode(
        x=alt.X(f"{metrics[x_name]}:Q", title=x_name), y=alt.Y(f"{metrics[y_name]}:Q", title=y_name),
        color=alt.Color("dataset:N", scale=alt.Scale(domain=list(COLORS), range=list(COLORS.values()))),
        tooltip=["dataset", "cathode_material", "anode_material", "electrolyte"]).properties(height=360).interactive(),
        width="stretch")

    @st.cache_resource
    def rf_model():
        from sklearn.ensemble import RandomForestRegressor
        target = "specific_power_w_kg"
        candidates = ["potential_mid_v", "capacitance_capacity_value", "cycling_stability_pct", "ionic_conductivity_s_cm"]
        rows = ahsc[ahsc[target].notna()]
        threshold = max(10, int(np.ceil(len(rows) * .5)))
        features = [c for c in candidates if rows[c].notna().sum() >= threshold]
        training = ahsc[[target, *features]].dropna()
        return RandomForestRegressor(n_estimators=500, random_state=123, n_jobs=-1).fit(training[features], training[target]), features, training

    model, features, training = rf_model()
    st.subheader("Exploratory AHSC specific-power model (Random Forest)")
    cols, values = st.columns(len(features)), {}
    for col, feature in zip(cols, features):
        lo, hi, med = map(float, [training[feature].min(), training[feature].max(), training[feature].median()])
        values[feature] = col.slider(feature, lo, hi, med)
    prediction = float(model.predict(pd.DataFrame([values]))[0])
    st.metric("Estimated specific power", f"{prediction:,.0f} W/kg")
    st.caption(f"{len(training)} complete training records. Exploratory only: this model belongs to Track 3; the "
               "knowledge engine (Track 1) supplies its curated, evidence-linked training facts.")
