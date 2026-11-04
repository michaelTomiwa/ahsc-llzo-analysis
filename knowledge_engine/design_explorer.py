"""AHSC design space: measured energy–power Pareto front, thesis-predicted designs and SHAP feature importance.

- Measured devices: every AHSC record reporting both energy density (Wh/kg) and power density (W/kg), taken from
  the unit-cleaned knowledge-engine facts (kW/kg converted, flagged values excluded).
- Pareto fronts: NSGA-II style non-dominated sorting (maximise energy and power); front 1 is the Pareto front.
- Thesis designs: the top-10 RSM desirability designs (thesis Table 4.1), model predictions rather than measurements.
- NSGA-II results: if the thesis NSGA-II front is exported to data/nsga2_pareto.csv, it is shown alongside.
- SHAP: mean |SHAP| per input for the best energy and power models (thesis protocol, model_evaluation.py),
  one-hot material columns summed back to cathode, anode and electrolyte.

    python -m knowledge_engine.design_explorer        # writes reports/shap_importance.json (needs `shap`)
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .config import DATA_DIR, REPORTS_DIR
from .facts import is_reliable, load_facts

RSM_DESIGNS_CSV = DATA_DIR / "rsm_top_designs.csv"
NSGA2_CSV = DATA_DIR / "nsga2_pareto.csv"
SHAP_PATH = REPORTS_DIR / "shap_importance.json"
UNITS = {"specific_energy": "Wh/kg", "specific_power": "W/kg"}


def measured_devices() -> pd.DataFrame:
    """One row per AHSC record with both energy (Wh/kg) and power (W/kg) reported and unflagged."""
    rows: dict[str, dict] = {}
    for fact in load_facts(include_literature=False):
        if (fact["system"] != "AHSC" or fact["property"] not in UNITS or fact["unit"] != UNITS[fact["property"]]
                or not is_reliable(fact)):
            continue
        row = rows.setdefault(fact["record_id"], {
            "record_id": fact["record_id"], "cathode": fact["components"].get("cathode") or "",
            "anode": fact["components"].get("anode") or "", "electrolyte": fact["components"].get("electrolyte") or "",
            "family": fact["material_family"], "elements": fact.get("cell_elements") or fact["elements"],
            "africa_score": fact["africa"]["score"], "doi": fact["source"].get("doi") or "",
            "review_doi": fact["source"].get("review_doi") or ""})
        row["energy_wh_kg" if fact["property"] == "specific_energy" else "power_w_kg"] = fact["value"]
    frame = pd.DataFrame(rows.values())
    frame = frame.dropna(subset=["energy_wh_kg", "power_w_kg"])
    frame = frame[(frame.energy_wh_kg > 0) & (frame.power_w_kg > 0)].reset_index(drop=True)
    frame["source"] = "Measured (literature)"
    frame["front"] = pareto_ranks(frame.energy_wh_kg.to_numpy(), frame.power_w_kg.to_numpy())
    return frame


def pareto_ranks(energy: np.ndarray, power: np.ndarray) -> np.ndarray:
    """NSGA-II fast non-dominated sorting for two objectives to maximise; 1 = Pareto front."""
    n = len(energy)
    dominated_by = [[] for _ in range(n)]
    counts = np.zeros(n, dtype=int)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if energy[i] >= energy[j] and power[i] >= power[j] and (energy[i] > energy[j] or power[i] > power[j]):
                dominated_by[i].append(j)
            elif energy[j] >= energy[i] and power[j] >= power[i] and (energy[j] > energy[i] or power[j] > power[i]):
                counts[i] += 1
    ranks = np.zeros(n, dtype=int)
    current = [i for i in range(n) if counts[i] == 0]
    level = 1
    while current:
        following = []
        for i in current:
            ranks[i] = level
            for j in dominated_by[i]:
                counts[j] -= 1
                if counts[j] == 0:
                    following.append(j)
        current, level = following, level + 1
    return ranks


def thesis_designs() -> pd.DataFrame:
    """Thesis Table 4.1: top-10 RSM desirability designs (predicted, not measured)."""
    from .africa import africa_profile
    from .chem import elements_in

    frame = pd.read_csv(RSM_DESIGNS_CSV)
    frame["elements"] = [sorted(set(elements_in(a, "AHSC")) | set(elements_in(c, "AHSC")))
                         for a, c in zip(frame.anode, frame.cathode)]
    frame["africa_score"] = [africa_profile(e)["score"] for e in frame.elements]
    frame["record_id"] = "RSM-" + frame["rank"].astype(str)
    frame["source"] = "Thesis RSM prediction (Table 4.1)"
    frame["electrolyte"] = frame.electrolyte_conc_m.map(lambda m: f"{m:g} M aqueous electrolyte")
    frame["front"] = pareto_ranks(frame.energy_wh_kg.to_numpy(), frame.power_w_kg.to_numpy())
    return frame


def nsga2_results() -> pd.DataFrame | None:
    """Optional: the thesis NSGA-II Pareto front exported from the R project (energy_wh_kg, power_w_kg, ...)."""
    if not NSGA2_CSV.exists():
        return None
    frame = pd.read_csv(NSGA2_CSV)
    return frame if {"energy_wh_kg", "power_w_kg"} <= set(frame.columns) else None


def trade_off_score(frame: pd.DataFrame, energy_weight: float) -> pd.Series:
    """Blend of log-scaled energy and power, each scaled 0-1 over the frame; energy_weight in [0, 1]."""
    def scaled(column: str) -> pd.Series:
        values = np.log10(frame[column])
        span = values.max() - values.min()
        return (values - values.min()) / span if span else values * 0
    return energy_weight * scaled("energy_wh_kg") + (1 - energy_weight) * scaled("power_w_kg")


# ------------------------------------------------------------------ SHAP

def shap_importance() -> dict:
    """Mean |SHAP| per original input for each target's best model (needs the `shap` package)."""
    import shap

    from .model_evaluation import CATEGORICAL, LABELS, TARGETS, fit_predictor

    out = {}
    for target, (_, label) in TARGETS.items():
        pipeline, model_name, numeric, table = fit_predictor(target)
        rows = table[table[target].notna()]
        prepare, model = pipeline[0], pipeline[-1]
        X = prepare.transform(rows[numeric + CATEGORICAL])
        X = X.toarray() if hasattr(X, "toarray") else np.asarray(X)
        names = list(prepare.get_feature_names_out())
        if model_name == "Random forest":
            values = shap.TreeExplainer(model).shap_values(X)
        else:
            values = shap.LinearExplainer(model, X).shap_values(X)
        per_column = np.abs(values).mean(axis=0)
        grouped: dict[str, float] = {}
        for name, value in zip(names, per_column):
            kind, column = name.split("__", 1)
            if kind == "material":
                column = next(c for c in CATEGORICAL if column.startswith(c))
            grouped[column] = grouped.get(column, 0.0) + float(value)
        total = sum(grouped.values()) or 1.0
        out[target] = {"label": label, "model": model_name, "records": len(rows),
                       "importance": [{"feature": c, "label": LABELS.get(c, c.replace("_", " ").capitalize()),
                                       "mean_abs_shap": round(v, 4), "share": round(v / total, 3)}
                                      for c, v in sorted(grouped.items(), key=lambda kv: -kv[1])]}
    return out


def load_shap() -> dict | None:
    return json.loads(SHAP_PATH.read_text()) if SHAP_PATH.exists() else None


def write_shap() -> dict:
    report = shap_importance()
    REPORTS_DIR.mkdir(exist_ok=True)
    SHAP_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    for target, entry in write_shap().items():
        print(entry["label"], entry["model"])
        for item in entry["importance"]:
            print(f"  {item['label']:<32} {item['share']:.0%}")
    devices = measured_devices()
    print(f"{len(devices)} measured devices, {int((devices.front == 1).sum())} on the Pareto front")
