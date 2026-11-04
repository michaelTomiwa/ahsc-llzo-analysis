"""Materials Copilot: a plain-language AHSC design request -> ranked, evidence-linked recommendations.

The request is parsed into an energy/power weighting and constraints (thresholds, Africa supply, elements to
avoid, aqueous electrolyte). Candidates are the measured devices and the thesis RSM designs; each is scored on
the same log-scaled energy/power trade-off used by the Pareto slider and explained with the SHAP drivers.
With an LLM key the answer is written by the LLM from these candidates only; offline it is a template.

    python -m knowledge_engine.copilot "I need high power density with African materials"
"""
from __future__ import annotations

import json
import re
import sys

import pandas as pd

from . import llm
from .design_explorer import load_shap, measured_devices, thesis_designs, trade_off_score

ELEMENT_WORDS = {"cobalt": "Co", "nickel": "Ni", "lithium": "Li", "vanadium": "V", "tungsten": "W", "copper": "Cu",
                 "manganese": "Mn", "zinc": "Zn", "iron": "Fe", "titanium": "Ti", "tantalum": "Ta", "tin": "Sn"}
AQUEOUS = re.compile(r"koh|naoh|lioh|h2so4|na2so4|k2so4|li2so4|znso4|zn\(|kcl|licl|nano3|aqueous|pva", re.I)


def parse_request(text: str) -> dict:
    """Energy weight, thresholds and constraints from a plain-language request."""
    lowered = text.lower()
    wants_power = bool(re.search(r"power|fast charg|high rate|rate capab", lowered))
    wants_energy = bool(re.search(r"energy|long run|storage capacity|wh", lowered))
    energy_weight = 0.5 if wants_power == wants_energy else (0.8 if wants_energy else 0.2)
    request = {"energy_weight": energy_weight, "min_energy": None, "min_power": None, "africa": False,
               "avoid": [], "aqueous": False}
    for value, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(wh/kg|w/kg|kw/kg)", lowered):
        if unit == "wh/kg":
            request["min_energy"] = float(value)
        else:
            request["min_power"] = float(value) * (1000 if unit == "kw/kg" else 1)
    request["africa"] = bool(re.search(r"africa|local supply|locally sourced", lowered))
    request["aqueous"] = bool(re.search(r"aqueous|water|safe electrolyte", lowered))
    for word, symbol in ELEMENT_WORDS.items():
        if re.search(rf"(no|without|avoid|free of)\s+{word}|{word}[- ]free", lowered):
            request["avoid"].append(symbol)
    return request


def candidates() -> pd.DataFrame:
    measured = measured_devices().assign(kind="measured")
    designs = thesis_designs().assign(kind="predicted")
    columns = ["record_id", "kind", "source", "cathode", "anode", "electrolyte", "energy_wh_kg", "power_w_kg",
               "elements", "africa_score", "front", "doi"]
    return pd.concat([measured, designs.assign(doi="")], ignore_index=True)[columns]


def recommend(text: str, k: int = 3, use_llm: bool | None = None) -> dict:
    request = parse_request(text)
    pool = candidates()
    notes = []
    mask = pd.Series(True, index=pool.index)
    if request["min_energy"]:
        mask &= pool.energy_wh_kg >= request["min_energy"]
    if request["min_power"]:
        mask &= pool.power_w_kg >= request["min_power"]
    if request["avoid"]:
        mask &= ~pool.elements.map(lambda els: bool(set(els) & set(request["avoid"])))
    if request["aqueous"]:
        mask &= pool.electrolyte.map(lambda e: bool(AQUEOUS.search(str(e))))
    if request["africa"]:
        mask &= pool.africa_score.fillna(0) >= 0.8
    if not mask.any():
        notes.append("No candidate meets every constraint, so the closest overall matches are shown instead.")
        mask[:] = True
    pool = pool[mask].copy()
    pool["score"] = trade_off_score(pool, request["energy_weight"])
    top = pool.sort_values(["score", "front"], ascending=[False, True]).head(k)

    shap = load_shap() or {}
    focus = "specific_power_w_kg" if request["energy_weight"] < 0.5 else "specific_energy_wh_kg"
    drivers = [item["label"] for item in shap.get(focus, {}).get("importance", [])[:3]]
    picks = [{"rank": i + 1, "id": row.record_id, "kind": row.kind, "source": row.source, "cathode": row.cathode,
              "anode": row.anode, "electrolyte": row.electrolyte, "energy_wh_kg": round(float(row.energy_wh_kg), 1),
              "power_w_kg": round(float(row.power_w_kg), 1), "africa_score": None if pd.isna(row.africa_score) else round(float(row.africa_score), 2),
              "pareto_front": int(row.front), "doi": row.doi or ""}
             for i, row in enumerate(top.itertuples())]
    designs = pool[pool.kind == "predicted"]
    thesis_pick = None
    if len(designs):
        # Balanced goal: the thesis's own desirability ranking (Table 4.1); otherwise the trade-off within designs.
        within = trade_off_score(designs, request["energy_weight"])
        best = designs.loc[designs.record_id.eq("RSM-1").idxmax()] if request["energy_weight"] == 0.5 and (
            designs.record_id == "RSM-1").any() else designs.loc[within.idxmax()]
        thesis_pick = {"id": best.record_id, "cathode": best.cathode, "anode": best.anode,
                       "energy_wh_kg": round(float(best.energy_wh_kg), 1), "power_w_kg": round(float(best.power_w_kg), 1),
                       "africa_score": round(float(best.africa_score or 0), 2)}
    result = {"request": request, "recommendations": picks, "thesis_pick": thesis_pick, "drivers": drivers,
              "notes": notes, "mode": "offline"}
    if use_llm is not False and llm.available():
        answer = llm.complete(
            "You are a materials copilot for aqueous/asymmetric hybrid supercapacitors. Using ONLY the candidates "
            f"and SHAP drivers below, answer the request in under 150 words. Say whether each pick is measured or a "
            f"model prediction, and never invent numbers.\n\nRequest: {text}\nCandidates: {json.dumps(picks)}\n"
            f"Best thesis RSM design (predicted): {json.dumps(thesis_pick)}\nSHAP drivers ({focus}): {drivers}\n"
            f"Notes: {notes}")
        if answer.text:
            result.update(answer=answer.text.strip(), mode=answer.mode)
            return result
    result["answer"] = _template(request, picks, thesis_pick, drivers, notes)
    return result


def _template(request: dict, picks: list[dict], thesis_pick: dict | None, drivers: list[str], notes: list[str]) -> str:
    goal = {0.2: "power density", 0.8: "energy density"}.get(request["energy_weight"], "a balance of energy and power")
    lines = [f"Prioritising {goal}" + (" with African-supplied elements" if request["africa"] else "") + ":", ""]
    for p in picks:
        status = "measured device" if p["kind"] == "measured" else "thesis RSM prediction, not yet measured"
        lines.append(f"{p['rank']}. {_cell(p)} ({status}): {p['energy_wh_kg']:g} Wh/kg, "
                     f"{p['power_w_kg']:,.0f} W/kg, Africa supply score {'n/a' if p['africa_score'] is None else format(p['africa_score'], '.2f')}"
                     + (f", Pareto front {p['pareto_front']}" if p["kind"] == "measured" else "") + ".")
    lines.append("")
    if thesis_pick and all(p["id"] != thesis_pick["id"] for p in picks):
        lines.append(f"Best thesis design for this goal (RSM prediction, to validate): {_cell(thesis_pick)}, {thesis_pick['energy_wh_kg']:g} Wh/kg and "
                     f"{thesis_pick['power_w_kg']:,.0f} W/kg.")
    if drivers:
        lines.append(f"What drives this target most (SHAP): {', '.join(drivers)}.")
    lines.extend(notes)
    head = lines.index("", 1)
    return "\n".join(lines[:head + 1] + [""]) + "\n\n".join(line for line in lines[head + 1:] if line)


def _cell(item: dict) -> str:
    """Anode // cathode, the order the thesis uses (e.g. Graphene // PANI@NiCu)."""
    return f"{item['anode'] or 'anode not reported'} // {item['cathode'] or 'cathode not reported'}"


if __name__ == "__main__":
    print(recommend(" ".join(sys.argv[1:]) or "I need high power density")["answer"])
