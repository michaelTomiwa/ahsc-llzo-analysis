"""Streamlit research prototype for AHSC, LLZO, literature RAG, and minerals data."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ahsc_llzo_analysis import read_dataset
from rag import answer

ROOT = Path(__file__).resolve().parent


@st.cache_data
def load_data():
    ahsc = read_dataset(ROOT / "ahsc_cleaned (1).csv", "AHSC")
    llzo = read_dataset(ROOT / "llzo_cleaned (1).csv", "LLZO")
    minerals = pd.read_csv(ROOT / "data" / "mineral_resources.csv")
    return ahsc, llzo, pd.concat([ahsc, llzo], ignore_index=True), minerals


@st.cache_resource
def model_bundle():
    from ahsc_llzo_analysis import random_forest
    # Fit an in-memory model using the same reproducible selection logic as the analysis.
    from sklearn.ensemble import RandomForestRegressor
    ahsc, _, _, _ = load_data()
    target = "specific_power_w_kg"
    candidates = ["potential_mid_v", "capacitance_capacity_value", "cycling_stability_pct", "ionic_conductivity_s_cm"]
    target_rows = ahsc[ahsc[target].notna()]
    threshold = max(10, int(len(target_rows) * 0.5 + 0.999))
    features = [c for c in candidates if target_rows[c].notna().sum() >= threshold]
    data = ahsc[[target, *features]].dropna()
    model = RandomForestRegressor(n_estimators=500, random_state=123, n_jobs=-1).fit(data[features], data[target])
    return model, features, data


st.set_page_config(page_title="African Battery Materials Lab", page_icon="🔋", layout="wide")
st.title("African Battery Materials Lab")
st.caption("AHSC vs LLZO analytics · live exploratory prediction · local-first literature RAG · critical-minerals explorer")
ahsc, llzo, combined, minerals = load_data()

tab_overview, tab_predict, tab_chat, tab_minerals, tab_data = st.tabs([
    "Overview", "Live prediction", "Literature chat", "African minerals", "Data & limits"
])

with tab_overview:
    c1, c2, c3 = st.columns(3)
    c1.metric("AHSC records", len(ahsc))
    c2.metric("LLZO records", len(llzo))
    c3.metric("Combined records", len(combined))
    st.subheader("Available performance variables")
    st.dataframe(combined.groupby("dataset")[["potential_mid_v", "capacitance_capacity_value", "specific_energy_wh_kg", "specific_power_w_kg", "cycling_stability_pct", "ionic_conductivity_s_cm"]].count(), use_container_width=True)
    st.info("Use this as a research exploration tool. The datasets are observational, incomplete, and not a basis for causal or commercial conclusions.")

with tab_predict:
    model, features, training = model_bundle()
    st.subheader("Predict AHSC specific power")
    st.caption(f"Model: Random Forest (500 trees), trained on {len(training)} complete AHSC observations using: {', '.join(features)}.")
    values = {}
    cols = st.columns(len(features))
    for col, feature in zip(cols, features):
        values[feature] = col.number_input(feature.replace("_", " ").title(), value=float(training[feature].median()), format="%.4f")
    if st.button("Run prediction", type="primary"):
        prediction = float(model.predict(pd.DataFrame([values]))[0])
        st.metric("Estimated specific power", f"{prediction:,.1f} W/kg")
        st.warning("Exploratory estimate only: do not use this output for experimental design, investment, or procurement without validation.")

with tab_chat:
    st.subheader("Chat with the literature knowledge base")
    question = st.text_area("Ask about the supplied analysis or the seeded African-minerals literature", placeholder="What does the prototype say about DRC cobalt and Zimbabwe lithium?")
    if st.button("Ask the knowledge base") and question.strip():
        response, sources, mode = answer(question)
        st.caption(f"Mode: {mode}")
        st.write(response)
        with st.expander("Retrieved source passages"):
            for source in sources:
                st.markdown(source)

with tab_minerals:
    st.subheader("Critical-minerals explorer")
    countries = st.multiselect("Countries", sorted(minerals.country.unique()), default=["Democratic Republic of the Congo", "Zimbabwe", "Mozambique"])
    commodities = st.multiselect("Commodities", sorted(minerals.commodity.unique()), default=["Cobalt", "Lithium", "Graphite"])
    view = minerals[minerals.country.isin(countries) & minerals.commodity.isin(commodities)]
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.caption("Blank production/capacity values are intentionally left blank: they indicate qualitative/source-backed context, not zero production.")
    for _, row in view.drop_duplicates("source_url").iterrows():
        st.markdown(f"- [{row.source_name}]({row.source_url})")

with tab_data:
    st.subheader("Coverage and limitations")
    coverage = combined.groupby("dataset")[["potential_mid_v", "capacitance_capacity_value", "cycling_stability_pct", "ionic_conductivity_s_cm", "specific_power_w_kg"]].count()
    st.dataframe(coverage, use_container_width=True)
    st.markdown("- RAG starts with a local, versioned seed knowledge base. Add vetted papers or project reports to `knowledge_base/` before treating it as a literature review.\n- Add an `.env` file from `.env.example` to activate LangChain/OpenAI answers. Keep API keys out of Git.\n- Mineral entries are source-linked discovery context, not a financial, ESG, geological-reserve, or supply-chain due-diligence system.")
