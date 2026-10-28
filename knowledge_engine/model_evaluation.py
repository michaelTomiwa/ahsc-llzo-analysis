"""Held-out evaluation of AHSC property models against simple baselines.

The thesis random forest reported R² = 0.277 on a single 80/20 split (7 test records). This module re-tests it
with repeated k-fold cross-validation and compares it with models trained on the cleaned knowledge-engine facts.

    python -m knowledge_engine.model_evaluation        # writes reports/model_evaluation.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .config import AHSC_CSV, REPORTS_DIR
from .facts import is_reliable, load_facts

REPORT_PATH = REPORTS_DIR / "model_evaluation.json"
N_SPLITS, N_REPEATS = 5, 10
MISSING = -9.0  # log10 placeholder for an unreported input; far below any real value

# Targets: (curated property, unit, label). Energy density is the sprint target.
TARGETS = {
    "specific_energy": ("Wh/kg", "Energy density (Wh/kg)"),
    "specific_power": ("W/kg", "Power density (W/kg)"),
}
INPUTS = ["specific_energy", "specific_power", "potential_window", "specific_capacitance", "cycling_stability"]
# Energy and power are physically linked (E = P × t), so every target is also scored without the other one.
LINKED = {"specific_energy": "specific_power", "specific_power": "specific_energy"}


def ahsc_table() -> pd.DataFrame:
    """One row per AHSC record: log-free property values, material family and element one-hots."""
    rows = []
    for fact in load_facts(include_literature=False):
        if fact["system"] != "AHSC" or not is_reliable(fact):
            continue
        unit = TARGETS.get(fact["property"], ("F/g" if fact["property"] == "specific_capacitance" else None,))[0]
        if unit and fact["unit"] != unit:
            continue  # keep one unit per property (e.g. gravimetric F/g, not mF/cm2)
        rows.append({"record": fact["record_id"], "property": fact["property"], "value": fact["value"],
                     "family": fact.get("material_family") or "Other", "elements": fact.get("elements") or []})
    facts = pd.DataFrame(rows)
    table = facts.pivot_table(index="record", columns="property", values="value", aggfunc="first")
    meta = facts.groupby("record").agg(family=("family", "first"), elements=("elements", "first"))
    return table.join(meta)


def _features(table: pd.DataFrame, numeric: list[str]) -> pd.DataFrame:
    values = table.reindex(columns=numeric).where(lambda v: v > 0)
    numeric_part = np.log10(values).fillna(MISSING)
    elements = pd.get_dummies(table.elements.explode()).groupby(level=0).max().reindex(table.index, fill_value=False)
    families = pd.get_dummies(table.family, prefix="family")
    return pd.concat([numeric_part, elements.add_prefix("el_"), families], axis=1).astype(float)


class FamilyMedian(RegressorMixin, BaseEstimator):
    """Baseline: predict the training median of the record's material family (overall median if unseen)."""

    def fit(self, X, y):
        family = X.filter(like="family_").idxmax(axis=1)
        self.global_ = float(np.median(y))
        self.medians_ = pd.Series(np.asarray(y), index=X.index).groupby(family).median().to_dict()
        return self

    def predict(self, X):
        family = X.filter(like="family_").idxmax(axis=1)
        return np.array([self.medians_.get(f, self.global_) for f in family])


def _models() -> dict:
    return {
        "Mean baseline": DummyRegressor(),
        "Family-median baseline": FamilyMedian(),
        "Ridge regression": make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 3, 20))),
        "Random forest": RandomForestRegressor(n_estimators=200, min_samples_leaf=2, random_state=0, n_jobs=-1),
    }


def _cross_validate(model, X: pd.DataFrame, y: pd.Series) -> dict:
    r2, mae = [], []
    for seed in range(N_REPEATS):
        predicted = cross_val_predict(model, X, y, cv=KFold(N_SPLITS, shuffle=True, random_state=seed))
        r2.append(r2_score(y, predicted))
        mae.append(mean_absolute_error(y, predicted))
    return {"r2_mean": round(float(np.mean(r2)), 3), "r2_std": round(float(np.std(r2)), 3),
            "r2_min": round(float(np.min(r2)), 3), "r2_max": round(float(np.max(r2)), 3),
            "mae_log10": round(float(np.mean(mae)), 3)}


def thesis_model_check() -> dict:
    """Re-test the original thesis random forest (raw CSV, specific power) with repeated cross-validation."""
    from ahsc_llzo_analysis import read_dataset
    from sklearn.model_selection import train_test_split

    ahsc = read_dataset(AHSC_CSV, "AHSC")
    target = "specific_power_w_kg"
    candidates = ["potential_mid_v", "capacitance_capacity_value", "cycling_stability_pct", "ionic_conductivity_s_cm"]
    rows = ahsc[ahsc[target].notna()]
    features = [c for c in candidates if rows[c].notna().sum() >= max(10, int(np.ceil(len(rows) * .5)))]
    data = ahsc[[target, *features]].dropna()
    rf = RandomForestRegressor(n_estimators=500, random_state=123, n_jobs=-1)
    train, test = train_test_split(data, test_size=.2, random_state=123)
    single = r2_score(test[target], rf.fit(train[features], train[target]).predict(test[features]))
    y = np.log10(data[target])
    return {"records": len(data), "features": features, "single_split_r2": round(float(single), 3),
            "single_split_test_records": len(test),
            "cross_validated": {"Mean baseline": _cross_validate(DummyRegressor(), data[features], y),
                                "Random forest": _cross_validate(rf, data[features], y)}}


def evaluate() -> dict:
    table = ahsc_table()
    results = []
    for target, (unit, label) in TARGETS.items():
        rows = table[table[target].gt(0)]
        y = np.log10(rows[target])
        others = [c for c in INPUTS if c != target]
        for feature_set, numeric in [("All inputs", others),
                                     (f"Without {LINKED[target].replace('_', ' ')}",
                                      [c for c in others if c != LINKED[target]])]:
            X = _features(rows, numeric)
            for name, model in _models().items():
                results.append({"target": target, "target_label": label, "unit": unit, "feature_set": feature_set,
                                "model": name, "records": len(rows), "inputs": numeric,
                                **_cross_validate(model, X, y)})
    return {"protocol": f"{N_REPEATS} × repeated {N_SPLITS}-fold cross-validation on log10(target); R² and MAE are "
                        "computed on pooled out-of-fold predictions and averaged over repeats",
            "data": "AHSC facts from data/thesis_facts.jsonl; flagged facts excluded; one unit per property",
            "model_inputs": "log10 of reported properties (missing = -9) + element one-hots + material-family one-hots",
            "results": results, "thesis_model": thesis_model_check()}


def fit_predictor(target: str = "specific_energy"):
    """Fit ridge on all records for interactive prediction; returns (model, feature columns, training table)."""
    table = ahsc_table()
    rows = table[table[target].gt(0)]
    numeric = [c for c in INPUTS if c != target]
    X = _features(rows, numeric)
    model = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 3, 20))).fit(X, np.log10(rows[target]))
    return model, list(X.columns), rows, numeric


def predict(model, columns: list[str], numeric_values: dict, family: str, elements: list[str]) -> float:
    row = {c: 0.0 for c in columns}
    for name, value in numeric_values.items():
        row[name] = float(np.log10(value)) if value and value > 0 else MISSING
    for element in elements:
        if f"el_{element}" in row:
            row[f"el_{element}"] = 1.0
    if f"family_{family}" in row:
        row[f"family_{family}"] = 1.0
    return float(10 ** model.predict(pd.DataFrame([row], columns=columns))[0])


def write_report() -> dict:
    report = evaluate()
    REPORTS_DIR.mkdir(exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    report = write_report()
    frame = pd.DataFrame(report["results"])
    print(frame[["target", "feature_set", "model", "records", "r2_mean", "r2_std", "mae_log10"]].to_string(index=False))
    print(json.dumps(report["thesis_model"], indent=2))
