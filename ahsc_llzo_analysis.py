"""Reproducible AHSC vs LLZO analysis.

Run from the repository root:
    python ahsc_llzo_analysis.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import mannwhitneyu
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent
NUMERIC_COLUMNS = [
    "potential_mid_v", "capacitance_capacity_value", "cycling_stability_pct",
    "ionic_conductivity_s_cm", "specific_energy_wh_kg", "specific_power_w_kg",
]
COMPARISON_COLUMNS = [
    "potential_mid_v", "capacitance_capacity_value", "cycling_stability_pct", "ionic_conductivity_s_cm",
]


def read_dataset(path: Path, label: str) -> pd.DataFrame:
    """Read a source CSV and coerce the numeric analysis fields."""
    frame = pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
    frame.columns = [column.strip().lower() for column in frame.columns]
    for column in NUMERIC_COLUMNS:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["dataset"] = label
    return frame


def safe_filename(column: str) -> str:
    return column.replace("_", "-")


def summary_statistics(combined: pd.DataFrame) -> pd.DataFrame:
    return (
        combined.groupby("dataset", dropna=False)[COMPARISON_COLUMNS]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .stack(level=0, future_stack=True)
        .reset_index()
        .rename(columns={"level_1": "variable"})
    )


def wilcoxon_comparisons(combined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in COMPARISON_COLUMNS:
        ahsc = combined.loc[combined.dataset.eq("AHSC"), column].dropna()
        llzo = combined.loc[combined.dataset.eq("LLZO"), column].dropna()
        if len(ahsc) and len(llzo):
            statistic, p_value = mannwhitneyu(ahsc, llzo, alternative="two-sided")
            rows.append({"variable": column, "ahsc_n": len(ahsc), "llzo_n": len(llzo),
                         "statistic": statistic, "p_value": p_value,
                         "significant_at_0_05": p_value < 0.05})
        else:
            rows.append({"variable": column, "ahsc_n": len(ahsc), "llzo_n": len(llzo),
                         "statistic": np.nan, "p_value": np.nan, "significant_at_0_05": False})
    return pd.DataFrame(rows)


def make_distribution_plots(combined: pd.DataFrame, plots_dir: Path) -> None:
    sns.set_theme(style="whitegrid")
    for column in COMPARISON_COLUMNS:
        values = combined[["dataset", column]].dropna()
        if values.empty:
            continue
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.boxplot(data=values, x="dataset", y=column, hue="dataset", legend=False, ax=ax)
        ax.set_title(f"{column.replace('_', ' ').title()} comparison")
        fig.tight_layout()
        fig.savefig(plots_dir / f"{safe_filename(column)}_boxplot.png", dpi=180)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.histplot(data=values, x=column, hue="dataset", bins=30, element="step", stat="count",
                     common_norm=False, ax=ax)
        ax.set_title(f"{column.replace('_', ' ').title()} distribution")
        fig.tight_layout()
        fig.savefig(plots_dir / f"{safe_filename(column)}_histogram.png", dpi=180)
        plt.close(fig)


def random_forest(ahsc: pd.DataFrame, results_dir: Path, plots_dir: Path) -> dict | None:
    target = "specific_power_w_kg"
    candidate_features = ["potential_mid_v", "capacitance_capacity_value", "cycling_stability_pct", "ionic_conductivity_s_cm"]
    target_rows = ahsc.loc[ahsc[target].notna()]
    # Preserve only predictors observed for at least half of the target rows.  This avoids
    # discarding every row solely because a sparsely reported measurement is missing.
    minimum_available = max(10, int(np.ceil(len(target_rows) * 0.5)))
    features = [column for column in candidate_features if target_rows[column].notna().sum() >= minimum_available]
    if not features:
        return None
    data = ahsc[[target, *features]].dropna()
    if len(data) < 10:
        return None
    train, test = train_test_split(data, test_size=0.2, random_state=123)
    model = RandomForestRegressor(n_estimators=500, random_state=123, n_jobs=-1)
    model.fit(train[features], train[target])
    predicted = model.predict(test[features])
    metrics = {"n_observations": len(data), "features": features, "train_rows": len(train), "test_rows": len(test),
               "rmse": float(np.sqrt(mean_squared_error(test[target], predicted))),
               "r2": float(r2_score(test[target], predicted))}
    pd.DataFrame([metrics]).to_csv(results_dir / "random_forest_metrics.csv", index=False)
    pd.DataFrame({"observed": test[target].to_numpy(), "predicted": predicted}).to_csv(
        results_dir / "random_forest_predictions.csv", index=False)

    importance = pd.DataFrame({"feature": features, "importance": model.feature_importances_}).sort_values("importance")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(importance.feature, importance.importance, color="#2a6fbb")
    ax.set_title("Random forest feature importance")
    fig.tight_layout()
    fig.savefig(plots_dir / "random_forest_importance.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(test[target], predicted, alpha=0.8)
    bounds = [min(test[target].min(), predicted.min()), max(test[target].max(), predicted.max())]
    ax.plot(bounds, bounds, "k--", linewidth=1)
    ax.set(xlabel="Observed specific power (W/kg)", ylabel="Predicted specific power (W/kg)", title="Random forest: observed vs predicted")
    fig.tight_layout()
    fig.savefig(plots_dir / "random_forest_observed_vs_predicted.png", dpi=180)
    plt.close(fig)
    return metrics


def run(ahsc_path: Path, llzo_path: Path, output_dir: Path) -> dict:
    results_dir, plots_dir = output_dir / "results", output_dir / "plots"
    results_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    ahsc, llzo = read_dataset(ahsc_path, "AHSC"), read_dataset(llzo_path, "LLZO")
    combined = pd.concat([ahsc, llzo], ignore_index=True, sort=False)
    combined.to_csv(results_dir / "combined_data.csv", index=False)
    summary_statistics(combined).to_csv(results_dir / "summary_statistics.csv", index=False)
    wilcoxon_comparisons(combined).to_csv(results_dir / "mann_whitney_u_tests.csv", index=False)
    make_distribution_plots(combined, plots_dir)
    rf_metrics = random_forest(ahsc, results_dir, plots_dir)
    manifest = {"ahsc_rows": len(ahsc), "llzo_rows": len(llzo), "combined_rows": len(combined),
                "random_forest": rf_metrics}
    (results_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ahsc", type=Path, default=ROOT / "ahsc_cleaned (1).csv")
    parser.add_argument("--llzo", type=Path, default=ROOT / "llzo_cleaned (1).csv")
    parser.add_argument("--output", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(run(args.ahsc, args.llzo, args.output), indent=2))
