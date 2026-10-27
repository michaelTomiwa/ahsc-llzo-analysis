"""Phase 1: digitise the curated thesis dataset into evidence-grounded JSONL facts.

Each CSV row is one curated literature record (a device/cell reported in a paper). Each
reported property becomes one fact. The `evidence_span` is the verbatim raw cell text and
`evidence_text` is the full serialized record, so `verify_evidence()` can audit every value.

Run:  python -m knowledge_engine.facts
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd

from .africa import africa_profile
from .chem import (additives_in, canonical_material, detect_unit, dopants_in, elements_in, is_missing,
                   material_family, normalize_text, parse_conductivity, parse_rate, parse_temperature)
from .config import AHSC_CSV, FACTS_JSONL, LLZO_CSV, RECORD_SOURCES_CSV, ROOT

RAW_FIELDS = ["cathode_material", "anode_material", "electrolyte", "potential_window", "capacitance_capacity",
              "specific_energy", "specific_power", "cycling_stability", "ionic_conductivity", "capacity_retention"]

PROPERTY_INFO = {
    "potential_window": {"label": "Potential window (upper limit)", "unit": "V", "category": "electrochemical"},
    "specific_capacitance": {"label": "Specific capacitance", "unit": "F/g", "category": "charge storage"},
    "specific_capacity": {"label": "Specific capacity", "unit": "mAh/g", "category": "charge storage"},
    "specific_energy": {"label": "Specific energy", "unit": "Wh/kg", "category": "device performance"},
    "specific_power": {"label": "Specific power", "unit": "W/kg", "category": "device performance"},
    "cycling_stability": {"label": "Cycling stability (retention)", "unit": "%", "category": "durability"},
    "capacity_retention": {"label": "Capacity retention", "unit": "%", "category": "durability"},
    "ionic_conductivity": {"label": "Ionic conductivity", "unit": "S/cm", "category": "transport"},
    "rate_capability": {"label": "Rate capability (capacitance at current density)", "unit": "F/g",
                        "category": "charge storage"},
}
CAPACITY_UNITS = {"mAh/g", "mAh/cm2"}
# Flags that make a value unsuitable for statistics (an implied-but-standard unit is not one of them).
SEVERE_FLAGS = {"implausible_value_check_source", "unusually_high_check_source", "theoretical_value",
                "non_standard_retention_metric", "evidence_not_found_in_source", "raw_text_disagrees_with_curated_value"}


def is_reliable(fact: dict) -> bool:
    return not SEVERE_FLAGS.intersection(fact.get("quality_flags", []))


def _num(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) else number


def _load_record_sources() -> dict[str, dict]:
    """Optional mapping record_id -> DOI/title/year, filled in from the thesis reference list."""
    if not RECORD_SOURCES_CSV.exists():
        return {}
    table = pd.read_csv(RECORD_SOURCES_CSV, dtype=str).fillna("")
    return {row["record_id"]: row for row in table.to_dict("records") if row.get("doi") or row.get("title")}


def _window_bounds(raw: str) -> tuple[float | None, float | None]:
    numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", normalize_text(raw).replace("–", "-"))]
    numbers = [abs(n) if i else n for i, n in enumerate(numbers)]  # '0-2.6' splits as 0, -2.6
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    if len(numbers) == 1:
        return None, numbers[0]
    return None, None


def _evidence_text(row: pd.Series) -> str:
    return " | ".join(f"{field}: {str(row.get(field)).strip()}" for field in RAW_FIELDS
                      if not is_missing(row.get(field)))


def _primary(system: str, row: pd.Series) -> tuple[str, str]:
    """The study's subject material: AHSC papers report electrodes, LLZO papers report electrolytes."""
    if system == "LLZO" and not is_missing(row.get("electrolyte")):
        return canonical_material(row["electrolyte"]), "electrolyte"
    if not is_missing(row.get("cathode_material")):
        return canonical_material(row["cathode_material"]), "electrode"
    return canonical_material(row.get("electrolyte")), "electrolyte"


def _property_facts(system: str, row: pd.Series) -> list[dict]:
    """Return partial fact dicts: property, value, unit, raw, condition, flags, confidence."""
    out = []

    def add(prop, value, unit, raw, condition=None, flags=(), confidence=1.0, details=None):
        out.append({"property": prop, "value": value, "unit": unit, "raw": str(raw).strip(),
                    "condition": condition, "quality_flags": list(flags),
                    "confidence": round(confidence, 2), "value_details": details or {}})

    raw = row.get("potential_window")
    if not is_missing(raw):
        lower, upper = _window_bounds(raw)
        if upper is not None:
            flags = ["implausible_value_check_source"] if upper > 6.5 else []
            add("potential_window", upper, "V", raw, flags=flags, confidence=0.5 if flags else 1.0,
                details={"lower_v": lower, "upper_v": upper, "width_v": _num(row.get("potential_width_v")),
                         "midpoint_v": _num(row.get("potential_mid_v"))})

    raw, value = row.get("capacitance_capacity"), _num(row.get("capacitance_capacity_value"))
    if not is_missing(raw) and value is not None:
        default = "F/g" if system == "AHSC" else "mAh/g"
        unit, explicit = detect_unit(raw, default)
        prop = "specific_capacity" if unit in CAPACITY_UNITS else "specific_capacitance"
        add(prop, value, unit, raw, condition=parse_rate(raw), flags=[] if explicit else ["unit_assumed"],
            confidence=1.0 if explicit else 0.85)

    for prop, raw_col, value_col, default in (("specific_energy", "specific_energy", "specific_energy_wh_kg", "Wh/kg"),
                                               ("specific_power", "specific_power", "specific_power_w_kg", "W/kg")):
        raw, value = row.get(raw_col), _num(row.get(value_col))
        if is_missing(raw) or value is None:
            continue
        unit, explicit = detect_unit(raw, default)
        if unit == "kW/kg":  # curated column is already converted to W/kg
            unit = "W/kg"
        flags = [] if explicit else ["unit_assumed"]
        if explicit and unit != default:
            flags.append("non_gravimetric_unit")
        if "theoretical" in normalize_text(raw).lower():
            flags.append("theoretical_value")
        add(prop, value, unit, raw, condition=parse_rate(raw), flags=flags,
            confidence=1.0 - 0.15 * (not explicit) - 0.25 * ("theoretical_value" in flags))

    raw, value = row.get("cycling_stability"), _num(row.get("cycling_stability_pct"))
    if not is_missing(raw) and value is not None:
        cycles = _num(row.get("cycling_stability_cycles"))
        flags = ["implausible_value_check_source"] if value > 100.5 else []
        add("cycling_stability", value, "%", raw, condition=f"after {int(cycles)} cycles" if cycles else None,
            flags=flags, confidence=0.5 if flags else 1.0, details={"cycles": cycles})

    raw, value = row.get("capacity_retention"), _num(row.get("capacity_retention_pct"))
    if not is_missing(raw) and value is not None:
        text = normalize_text(raw)
        if re.fullmatch(r"\d+(?:\.\d+)?/\d+(?:\.\d+)?(;.*)?", text):
            # AHSC curation stored rate capability here as "capacitance/current density".
            rate = text.split(";")[0].split("/")[1]
            add("rate_capability", value, "F/g", raw, condition=f"at {rate} A/g (unit implied)",
                flags=["unit_assumed", "reinterpreted_column"], confidence=0.7)
        else:
            flags = [] if value <= 100.5 and not re.search(r"stretch|bend|twist|ocv|heal", text, re.I) \
                else ["non_standard_retention_metric"]
            add("capacity_retention", value, "%", raw, flags=flags, confidence=0.5 if flags else 1.0)

    raw, curated = row.get("ionic_conductivity"), _num(row.get("ionic_conductivity_s_cm"))
    if not is_missing(raw):
        reparsed, note = parse_conductivity(raw)
        value, flags, confidence = curated, [], 1.0
        if curated is None or curated > 1.0:  # S/cm > 1 is not physical for these electrolytes
            if reparsed is not None:
                value, flags, confidence = reparsed, ["corrected_from_raw_text"], 0.8
            else:
                value = None
        elif reparsed is not None and abs(reparsed - curated) / max(curated, 1e-12) > 0.05:
            flags.append("raw_text_disagrees_with_curated_value")
            confidence = 0.7
        if note.startswith("range"):
            flags.append("range_reported")
            confidence = min(confidence, 0.9)
        if value is not None and value > 0.05:
            flags.append("unusually_high_check_source")
            confidence = min(confidence, 0.6)
        if value is not None:
            add("ionic_conductivity", value, "S/cm", raw, condition=parse_temperature(raw), flags=flags,
                confidence=confidence, details={"curated_value": curated, "reparsed_value": reparsed})
    return out


def build_facts(ahsc_path: Path = AHSC_CSV, llzo_path: Path = LLZO_CSV) -> list[dict]:
    sources = _load_record_sources()
    facts: list[dict] = []
    for system, path in (("AHSC", ahsc_path), ("LLZO", llzo_path)):
        frame = pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
        frame.columns = [column.strip().lower() for column in frame.columns]
        for index, row in frame.iterrows():
            record_id = f"{system}-{index + 1:04d}"
            material, role = _primary(system, row)
            components = {part: canonical_material(row.get(col)) for part, col in
                          (("cathode", "cathode_material"), ("anode", "anode_material"), ("electrolyte", "electrolyte"))
                          if not is_missing(row.get(col))}
            elements = elements_in(material, system)
            cell_elements = sorted({e for name in components.values() for e in elements_in(name, system)})
            source_meta = sources.get(record_id, {})
            source = {"type": "thesis_curated_record", "record_id": record_id,
                      "file": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name,
                      "csv_line": index + 2, "doi": source_meta.get("doi") or None,
                      "title": source_meta.get("title") or None, "year": source_meta.get("year") or None}
            evidence_text = _evidence_text(row)
            family = material_family(material, role)
            dopants = dopants_in(material) if role == "electrolyte" else []
            for item in _property_facts(system, row):
                info = PROPERTY_INFO[item["property"]]
                condition = f" ({item['condition']})" if item["condition"] else ""
                text = (f"{system} record {record_id}: {material} [{family}] has {info['label'].lower()} of "
                        f"{item['value']:.4g} {item['unit']}{condition}. Cell: "
                        + "; ".join(f"{k} = {v}" for k, v in components.items()) + "."
                        + (f" Dopants: {', '.join(dopants)}-doped." if dopants else ""))
                facts.append({
                    "id": f"{record_id}-{item['property']}",
                    "record_id": record_id,
                    "system": system,
                    "material": material,
                    "material_role": role,
                    "material_family": family,
                    "components": components,
                    "elements": elements,
                    "cell_elements": cell_elements,
                    "dopants": dopants,
                    "additives": additives_in(material) if role == "electrolyte" else [],
                    "property": item["property"],
                    "property_label": info["label"],
                    "property_category": info["category"],
                    "value": item["value"],
                    "unit": item["unit"],
                    "value_details": item["value_details"],
                    "condition": item["condition"],
                    "method": "literature-reported (manually curated for thesis)",
                    "source": source,
                    "evidence_span": item["raw"],
                    "evidence_text": evidence_text,
                    "confidence": item["confidence"],
                    "quality_flags": item["quality_flags"],
                    "extraction_method": "manual_curation",
                    "africa": africa_profile(elements),
                    "text": text,
                })
    return facts


def write_jsonl(records: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_facts(include_literature: bool = True) -> list[dict]:
    """Thesis facts (built on the fly if the JSONL is missing) plus any mined literature facts."""
    from .config import LITERATURE_FACTS_JSONL
    facts = load_jsonl(FACTS_JSONL) or build_facts()
    if include_literature:
        facts += load_jsonl(LITERATURE_FACTS_JSONL)
    return facts


def facts_frame(facts: list[dict]) -> pd.DataFrame:
    rows = [{k: v for k, v in fact.items() if k not in ("components", "value_details", "source", "africa")}
            | {"africa_score": fact["africa"]["score"], "doi": fact["source"].get("doi"),
               "source_type": fact["source"]["type"]} for fact in facts]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    built = build_facts()
    write_jsonl(built, FACTS_JSONL)
    records = len({fact["record_id"] for fact in built})
    print(f"Wrote {len(built)} facts from {records} curated records to {FACTS_JSONL.relative_to(ROOT)}")
