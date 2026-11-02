"""Africa-first constraints: element supply, synthesis energy and application fit.

Africa is a structural design principle of the engine, not a separate tab:
- every fact and graph node carries an `africa` score derived from its elements;
- literature ingestion queries are biased towards Africa-relevant chemistries;
- hypothesis generation receives these constraints and hypotheses are re-ranked by them.

Supply statuses and 2024 production figures come from USGS Mineral Commodity Summaries 2025
(https://doi.org/10.3133/mcs2025); each row of data/africa_element_supply.csv records how far it
was verified. They are not reserve estimates or investment advice.
"""
from __future__ import annotations

import re
from functools import lru_cache

import pandas as pd

from .config import AFRICA_SUPPLY_CSV

AFRICAN_CONSTRAINTS: dict = {
    # Elements with established African supply that the feedback explicitly prioritises.
    "elements": ["Li", "Fe", "Mn", "Na", "Mg", "Al", "C", "Co", "Ni", "Cu", "Ti", "Zr", "P", "Zn"],
    "max_synthesis_temp_c": 1000,  # energy-cost / grid-reliability constraint
    "precursors": ["local minerals", "agro-waste biomass carbon", "phosphate rock", "mineral sands"],
    "applications": ["off-grid solar", "electric two/three-wheelers (EV)", "grid storage", "telecom tower backup"],
    "avoid": ["Ga", "Ge", "In", "Te", "Ir", "Ru"],  # scarce, no African supply, or very expensive
}

STATUS_WEIGHT = {"major_producer": 1.0, "ubiquitous": 1.0, "producer": 0.8, "project_stage": 0.5}
NEUTRAL_ELEMENTS = {"H", "O", "N"}  # present in almost every material; excluded from the score


@lru_cache(maxsize=1)
def supply_table() -> pd.DataFrame:
    return pd.read_csv(AFRICA_SUPPLY_CSV).fillna("")


@lru_cache(maxsize=1)
def _supply_lookup() -> dict[str, dict]:
    return {row["element"]: row for row in supply_table().to_dict("records")}


def element_supply(element: str) -> dict | None:
    return _supply_lookup().get(element)


def africa_profile(elements: list[str] | set[str]) -> dict:
    """Score 0-1: how much of a material's (non-neutral) element set has African supply."""
    scored = sorted(set(elements) - NEUTRAL_ELEMENTS)
    lookup = _supply_lookup()
    if not scored:
        return {"score": None, "african_supply": [], "no_african_supply": [], "flags": []}
    weights, african, missing, flags = [], [], [], []
    for element in scored:
        row = lookup.get(element)
        weight = STATUS_WEIGHT.get(row["status"], 0.0) if row else 0.0
        weights.append(weight)
        (african if weight > 0 else missing).append(element)
        if row and re.search(r"due diligence|3TG|responsible", row["note"], re.I):
            flags.append(f"{element}: responsible-sourcing due diligence required")
        if element in AFRICAN_CONSTRAINTS["avoid"]:
            flags.append(f"{element}: scarce / no African supply")
    return {"score": round(sum(weights) / len(weights), 3), "african_supply": african,
            "no_african_supply": missing, "flags": flags}


def countries_for(element: str) -> list[str]:
    row = element_supply(element)
    if not row or row["status"] == "ubiquitous":
        return []
    return [country.strip() for country in re.split(r";", row["african_countries"]) if country.strip()
            and "continent" not in country]


def feasibility_from_temperature(temperature_c: float | None) -> float:
    """1.0 at/below the constraint, decaying linearly to 0 at +400 °C above it."""
    if temperature_c is None:
        return 0.6  # unknown: neutral-to-cautious
    limit = AFRICAN_CONSTRAINTS["max_synthesis_temp_c"]
    if temperature_c <= limit:
        return 1.0
    return max(0.0, 1.0 - (temperature_c - limit) / 400.0)


def africa_rerank_score(elements: list[str], synthesis_temp_c: float | None, applications: list[str] | None = None) -> dict:
    """Composite African-feasibility score used to re-rank hypotheses."""
    profile = africa_profile(elements)
    supply = profile["score"] if profile["score"] is not None else 0.5
    temperature = feasibility_from_temperature(synthesis_temp_c)
    application_fit = 1.0 if applications and any(
        any(word in app.lower() for word in ("solar", "grid", "ev", "wheel", "off-grid", "telecom", "storage"))
        for app in applications) else 0.6
    penalty = 0.15 * sum("scarce" in flag for flag in profile["flags"])
    score = max(0.0, 0.55 * supply + 0.3 * temperature + 0.15 * application_fit - penalty)
    return {"africa_score": round(score, 3), "supply_score": supply, "temperature_score": temperature,
            "application_fit": application_fit, **{k: profile[k] for k in ("african_supply", "no_african_supply", "flags")}}
