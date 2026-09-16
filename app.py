"""Interactive Streamlit research dashboard."""
from pathlib import Path
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from ahsc_llzo_analysis import read_dataset
from rag import answer

ROOT = Path(__file__).resolve().parent
METRICS = {"Potential midpoint": "potential_mid_v", "Capacitance / capacity": "capacitance_capacity_value", "Specific energy": "specific_energy_wh_kg", "Specific power": "specific_power_w_kg", "Cycling stability": "cycling_stability_pct", "Ionic conductivity": "ionic_conductivity_s_cm"}
UNITS = {"potential_mid_v":"V", "capacitance_capacity_value":"reported value", "specific_energy_wh_kg":"Wh/kg", "specific_power_w_kg":"W/kg", "cycling_stability_pct":"%", "ionic_conductivity_s_cm":"S/cm"}

@st.cache_data
def load_data():
    ahsc = read_dataset(ROOT / "ahsc_cleaned (1).csv", "AHSC")
    llzo = read_dataset(ROOT / "llzo_cleaned (1).csv", "LLZO")
    return ahsc, llzo, pd.concat([ahsc, llzo], ignore_index=True), pd.read_csv(ROOT / "data" / "mineral_resources.csv")

@st.cache_resource
def model_bundle():
    from sklearn.ensemble import RandomForestRegressor
    ahsc, _, _, _ = load_data(); target = "specific_power_w_kg"
    candidates = ["potential_mid_v", "capacitance_capacity_value", "cycling_stability_pct", "ionic_conductivity_s_cm"]
    target_rows = ahsc[ahsc[target].notna()]; threshold = max(10, int(np.ceil(len(target_rows) * .5)))
    features = [c for c in candidates if target_rows[c].notna().sum() >= threshold]
    training = ahsc[[target, *features]].dropna()
    return RandomForestRegressor(n_estimators=500, random_state=123, n_jobs=-1).fit(training[features], training[target]), features, training

def label(column): return next(name for name, value in METRICS.items() if value == column)

st.set_page_config(page_title="African Battery Materials Lab", page_icon="AB", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.stApp{background:#f7f8fc;color:#172038}[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1635,#13285c)}[data-testid="stSidebar"] *{color:#f4f7ff!important}.hero{background:linear-gradient(120deg,#081a3c,#1a4d9a 63%,#18a6a6);border-radius:22px;padding:2rem 2.2rem;color:#fff;margin-bottom:1.2rem;box-shadow:0 18px 50px rgba(12,38,88,.2)}.hero h1{font-size:2.45rem;line-height:1.05;margin:0 0 .55rem;color:#fff;letter-spacing:-.04em}.hero p{margin:0;color:#dceaff;font-size:1.05rem}[data-testid="stMetric"]{background:#fff;border:1px solid #e5e9f3;border-radius:16px;padding:1rem;box-shadow:0 4px 14px rgba(27,43,77,.05)}.section-kicker{color:#168d94;font-size:.78rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}.stTabs [data-baseweb="tab-list"]{gap:1.4rem;border-bottom:1px solid #e4e9f2}.stTabs [data-baseweb="tab"]{height:48px;font-weight:600}.stButton>button{background:#1264c4;color:white;border:0;border-radius:10px;font-weight:700}</style>""", unsafe_allow_html=True)
ahsc, llzo, combined, minerals = load_data()
with st.sidebar:
    st.markdown("## Research controls")
    selected = st.multiselect("Dataset", ["AHSC", "LLZO"], default=["AHSC", "LLZO"])
    metric_name = st.selectbox("Focus metric", list(METRICS), index=3); metric = METRICS[metric_name]
    st.markdown("---\n**Evidence status**\n\nLocal research data · source-linked minerals · exploratory model")
filtered = combined[combined.dataset.isin(selected)].copy()
st.markdown("""<div class="hero"><div class="section-kicker" style="color:#82f0df">Research intelligence workspace</div><h1>African Battery Materials Lab</h1><p>Explore AHSC and LLZO performance, test a live predictive scenario, and connect material research with critical-mineral context.</p></div>""", unsafe_allow_html=True)
overview, predict, chat, minerals_tab, methods = st.tabs(["Performance explorer", "Live prediction", "Literature intelligence", "African minerals", "Methods & data"])

with overview:
    cards = st.columns(4)
    for card, title, value in zip(cards, ["Records in view", f"{metric_name} coverage", "AHSC records", "LLZO records"], [len(filtered), filtered[metric].notna().sum(), len(filtered[filtered.dataset.eq("AHSC")]), len(filtered[filtered.dataset.eq("LLZO")])]): card.metric(title, f"{value:,}")
    left, right = st.columns([1.35,1])
    with left:
        st.subheader(f"{metric_name} distribution")
        chart = alt.Chart(filtered.dropna(subset=[metric])).mark_bar(opacity=.78, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(alt.X(f"{metric}:Q", bin=alt.Bin(maxbins=28), title=f"{metric_name} ({UNITS[metric]})"), alt.Y("count():Q", title="Records"), alt.Color("dataset:N", scale=alt.Scale(domain=["AHSC","LLZO"],range=["#167cbe","#18a692"])), tooltip=["dataset:N","count():Q"]).properties(height=320).interactive()
        st.altair_chart(chart, use_container_width=True)
    with right:
        st.subheader("Data coverage")
        cover = filtered.groupby("dataset")[list(METRICS.values())].count().T.reset_index(names="metric"); cover["metric"] = cover.metric.map(label)
        long = cover.melt("metric", var_name="dataset", value_name="records")
        st.altair_chart(alt.Chart(long).mark_bar(cornerRadiusEnd=4).encode(y=alt.Y("metric:N",sort="-x",title=None),x=alt.X("records:Q",title="Non-missing records"),color=alt.Color("dataset:N",scale=alt.Scale(domain=["AHSC","LLZO"],range=["#167cbe","#18a692"])),tooltip=["metric:N","dataset:N","records:Q"]).properties(height=320), use_container_width=True)
    st.subheader("Performance relationship explorer")
    c1,c2=st.columns(2); x_name=c1.selectbox("X axis",list(METRICS),index=1); y_name=c2.selectbox("Y axis",list(METRICS),index=3)
    x,y=METRICS[x_name],METRICS[y_name]; dots=filtered.dropna(subset=[x,y])
    st.altair_chart(alt.Chart(dots).mark_circle(size=70,opacity=.68).encode(x=alt.X(f"{x}:Q",title=f"{x_name} ({UNITS[x]})"),y=alt.Y(f"{y}:Q",title=f"{y_name} ({UNITS[y]})"),color=alt.Color("dataset:N",scale=alt.Scale(domain=["AHSC","LLZO"],range=["#167cbe","#18a692"])),tooltip=["dataset:N",f"{x}:Q",f"{y}:Q","cathode_material:N","anode_material:N"]).properties(height=390).interactive(),use_container_width=True)

with predict:
    model, features, training = model_bundle(); st.markdown("<div class='section-kicker'>Scenario studio</div>",unsafe_allow_html=True); st.subheader("Estimate AHSC specific power")
    st.caption(f"Random Forest · 500 trees · {len(training)} complete AHSC training records · predictors: {', '.join(label(f) for f in features)}")
    values={}; cols=st.columns(len(features))
    for col, feature in zip(cols,features):
        lo,hi,med=map(float,[training[feature].min(),training[feature].max(),training[feature].median()]); values[feature]=col.slider(label(feature),lo,hi,med); col.caption(f"Observed range {lo:,.3g}–{hi:,.3g} {UNITS[feature]}")
    prediction=float(model.predict(pd.DataFrame([values]))[0]); percentile=(training.specific_power_w_kg<=prediction).mean()*100
    a,b,c=st.columns([1,1,2]); a.metric("Estimated specific power",f"{prediction:,.0f} W/kg"); b.metric("Training-set percentile",f"{percentile:.0f}th"); c.info("Updates as controls change. This is exploratory and must be experimentally validated.")
    with st.expander("Model transparency"): st.dataframe(training.describe().T, use_container_width=True)

with chat:
    st.markdown("<div class='section-kicker'>Evidence-grounded Q&A</div>",unsafe_allow_html=True); st.subheader("Literature intelligence"); st.caption("Answers use a local, versioned knowledge base. Add vetted papers and reports to expand it.")
    if "messages" not in st.session_state: st.session_state.messages=[]
    for role,content,mode in st.session_state.messages:
        with st.chat_message(role): st.write(content); st.caption(mode) if mode else None
    prompt=st.chat_input("Ask about AHSC, LLZO, DRC cobalt, Zimbabwe lithium, or graphite…")
    if prompt:
        st.session_state.messages.append(("user",prompt,""));
        with st.chat_message("assistant"):
            response,sources,mode=answer(prompt); st.write(response); st.caption(mode)
            with st.expander("Retrieved passages"):
                for source in sources: st.markdown(source)
        st.session_state.messages.append(("assistant",response,mode))
    if st.button("Clear conversation"): st.session_state.messages=[]; st.rerun()

with minerals_tab:
    st.markdown("<div class='section-kicker'>Critical-minerals context</div>",unsafe_allow_html=True); st.subheader("African minerals explorer")
    a,b=st.columns(2); countries=a.multiselect("Countries",sorted(minerals.country.unique()),default=["Democratic Republic of the Congo","Zimbabwe","Mozambique"]); commodities=b.multiselect("Commodities",sorted(minerals.commodity.unique()),default=["Cobalt","Lithium","Graphite"])
    view=minerals[minerals.country.isin(countries)&minerals.commodity.isin(commodities)].copy(); numeric=view.dropna(subset=["production_or_capacity"])
    if not numeric.empty: st.altair_chart(alt.Chart(numeric).mark_circle(size=210,opacity=.85).encode(x=alt.X("country:N",title=None),y=alt.Y("production_or_capacity:Q",title="Reported production / capacity"),color=alt.Color("commodity:N",scale=alt.Scale(range=["#1d67b3","#d89217","#1ba98d"])),tooltip=["country:N","commodity:N","production_or_capacity:Q","unit:N","role_or_status:N"]).properties(height=280).interactive(),use_container_width=True)
    st.dataframe(view[["country","commodity","role_or_status","year","production_or_capacity","unit","notes"]],use_container_width=True,hide_index=True); st.download_button("Download filtered minerals data",view.to_csv(index=False).encode(),"african_minerals_filtered.csv","text/csv")
    with st.expander("Primary sources"):
        for _,row in view.drop_duplicates("source_url").iterrows(): st.markdown(f"- [{row.source_name}]({row.source_url})")

with methods:
    st.markdown("<div class='section-kicker'>Provenance & guardrails</div>",unsafe_allow_html=True); st.subheader("Data coverage")
    coverage=combined.groupby("dataset")[list(METRICS.values())].count().T; coverage.index=[label(c) for c in coverage.index]; st.dataframe(coverage,use_container_width=True)
    st.markdown("- **Performance analytics:** descriptive and exploratory; association is not causality.\n- **Live prediction:** compare scenarios inside observed ranges, then validate experimentally.\n- **Literature chat:** local retrieval by default; add `.env` for LangChain LLM synthesis.\n- **Minerals explorer:** discovery context, not reserve estimation, due diligence, or investment advice.")
