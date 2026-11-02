"""Held-out evaluation of AHSC energy- and power-density models against simple baselines.

Follows the thesis protocol (Chapter 5, Table 5.2): log10 targets, median-imputed numeric inputs, the ten most
frequent cathode, anode and electrolyte names one-hot encoded (the rest grouped as "Other"), Ridge (alpha = 1)
and Random Forest (200 trees, depth 5, 3 samples per leaf), scored by 5-fold cross-validation. Here the 5-fold
split is repeated 10 times so the spread of R² is visible, and a mean baseline is scored on the same folds.

    python -m knowledge_engine.model_evaluation        # writes reports/model_evaluation.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import AHSC_CSV, REPORTS_DIR

REPORT_PATH = REPORTS_DIR / "model_evaluation.json"
N_SPLITS, N_REPEATS, TOP_N = 5, 10, 10

TARGETS = {
    "specific_energy_wh_kg": ("Wh/kg", "Energy density (Wh/kg)"),
    "specific_power_w_kg": ("W/kg", "Power density (W/kg)"),
}
CATEGORICAL = ["cathode_material", "anode_material", "electrolyte"]
NUMERIC = ["potential_mid_v", "potential_width_v", "capacitance_capacity_value", "specific_energy_wh_kg",
           "specific_power_w_kg", "cycling_stability_pct", "cycling_stability_cycles"]
LOG_COLUMNS = ["capacitance_capacity_value", "specific_energy_wh_kg", "specific_power_w_kg", "cycling_stability_cycles"]
# Energy and power are physically linked (E = P × t), so each target is also scored without the other one.
LINKED = {"specific_energy_wh_kg": "specific_power_w_kg", "specific_power_w_kg": "specific_energy_wh_kg"}
LABELS = {"potential_mid_v": "Potential midpoint (V)", "potential_width_v": "Potential window width (V)",
          "capacitance_capacity_value": "Capacitance / capacity", "specific_energy_wh_kg": "Energy density (Wh/kg)",
          "specific_power_w_kg": "Power density (W/kg)", "cycling_stability_pct": "Cycling stability (%)",
          "cycling_stability_cycles": "Cycles tested"}
# Thesis Table 5.2 (5-fold CV R²), for side-by-side comparison.
THESIS_TABLE_5_2 = {
    "specific_energy_wh_kg": {"Ridge regression": 0.352, "Random forest": 0.204},
    "specific_power_w_kg": {"Ridge regression": 0.263, "Random forest": 0.277},
}


def ahsc_table() -> pd.DataFrame:
    """The 369 curated AHSC records, cleaned as in thesis section 3.4 (log10 values, top-10 categories)."""
    from ahsc_llzo_analysis import read_dataset

    table = read_dataset(AHSC_CSV, "AHSC")
    table.loc[table.cycling_stability_pct > 110, "cycling_stability_pct"] = np.nan
    for column in LOG_COLUMNS:
        table[column] = np.log10(table[column].where(table[column] > 0))
    for column in CATEGORICAL:
        top = table[column].value_counts().index[:TOP_N]
        table[column] = table[column].where(table[column].isin(top), "Other").fillna("Other")
    return table


def _inputs(target: str, without_linked: bool = False) -> list[str]:
    return [c for c in NUMERIC if c != target and not (without_linked and c == LINKED[target])]


def _pipeline(model, numeric: list[str]):
    prepare = ColumnTransformer([
        ("numeric", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric),
        ("material", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])
    return make_pipeline(prepare, model)


def _models() -> dict:
    return {
        "Mean baseline": DummyRegressor(),
        "Ridge regression": Ridge(alpha=1.0),
        "Random forest": RandomForestRegressor(n_estimators=200, max_depth=5, min_samples_leaf=3, random_state=0,
                                               n_jobs=-1),
    }


def _cross_validate(pipeline, X: pd.DataFrame, y: pd.Series) -> dict:
    r2, mae = [], []
    for seed in range(N_REPEATS):
        predicted = cross_val_predict(pipeline, X, y, cv=KFold(N_SPLITS, shuffle=True, random_state=seed))
        r2.append(r2_score(y, predicted))
        mae.append(mean_absolute_error(y, predicted))
    return {"r2_mean": round(float(np.mean(r2)), 3), "r2_std": round(float(np.std(r2)), 3),
            "r2_min": round(float(np.min(r2)), 3), "r2_max": round(float(np.max(r2)), 3),
            "mae_log10": round(float(np.mean(mae)), 3)}


def evaluate() -> dict:
    table = ahsc_table()
    results = []
    for target, (unit, label) in TARGETS.items():
        rows = table[table[target].notna()]
        linked = LABELS[LINKED[target]].split(" (")[0].lower()
        for feature_set, numeric in [("All inputs", _inputs(target)), (f"Without {linked}", _inputs(target, True))]:
            for name, model in _models().items():
                results.append({"target": target, "target_label": label, "unit": unit, "feature_set": feature_set,
                                "model": name, "records": len(rows), "inputs": numeric + CATEGORICAL,
                                "thesis_r2": THESIS_TABLE_5_2[target].get(name) if feature_set == "All inputs" else None,
                                **_cross_validate(_pipeline(model, numeric), rows[numeric + CATEGORICAL], rows[target])})
    return {"protocol": f"{N_REPEATS} × repeated {N_SPLITS}-fold cross-validation on log10(target); R² and MAE are "
                        "computed on pooled out-of-fold predictions and averaged over repeats",
            "data": f"{len(table)} curated AHSC records; cycling stability above 110% removed; capacitance, energy, "
                    "power and cycle count log10-transformed",
            "model_inputs": f"median-imputed numeric properties + the top {TOP_N} cathode, anode and electrolyte names "
                            "(one-hot, the rest grouped as Other), as in thesis section 3.4",
            "thesis_reference": "Thesis Table 5.2, 5-fold cross-validation",
            "results": results}


def fit_predictor(target: str = "specific_energy_wh_kg", model_name: str | None = None):
    """Fit the target's best model on every record; returns (pipeline, model name, numeric inputs, table)."""
    table = ahsc_table()
    rows = table[table[target].notna()]
    if model_name is None:
        report = json.loads(REPORT_PATH.read_text()) if REPORT_PATH.exists() else evaluate()
        scored = [r for r in report["results"] if r["target"] == target and r["feature_set"] == "All inputs"]
        model_name = max(scored, key=lambda r: r["r2_mean"])["model"]
    numeric = _inputs(target)
    pipeline = _pipeline(_models()[model_name], numeric).fit(rows[numeric + CATEGORICAL], rows[target])
    return pipeline, model_name, numeric, table


def predict(pipeline, numeric: list[str], values: dict, materials: dict) -> float:
    """values: raw (unlogged) numeric inputs, 0 or None = not reported; materials: cathode/anode/electrolyte names."""
    row = {}
    for name in numeric:
        value = values.get(name)
        row[name] = np.nan if not value else (np.log10(value) if name in LOG_COLUMNS else value)
    row.update({c: materials.get(c, "Other") for c in CATEGORICAL})
    return float(10 ** pipeline.predict(pd.DataFrame([row]))[0])


def write_report() -> dict:
    report = evaluate()
    REPORTS_DIR.mkdir(exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    frame = pd.DataFrame(write_report()["results"])
    print(frame[["target", "feature_set", "model", "records", "r2_mean", "r2_std", "thesis_r2"]].to_string(index=False))
