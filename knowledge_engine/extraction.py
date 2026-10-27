"""Phase 2: extract material-property-value facts from new literature (text or PDF).

Two extractors share one output schema:
- `llm_extract`: schema-enforced LLM extraction (primary when an API key is configured);
- `rule_extract`: transparent regex extractor (offline fallback and sanity baseline).
Every extracted fact is evidence-checked with `verify_evidence()`; ungrounded facts are
kept only with `grounded: false` so they can be reviewed, never silently trusted.

Validate against the manually curated thesis facts:
    python -m knowledge_engine.extraction --validate [--llm --limit 40]
Extract from a paper:
    python -m knowledge_engine.extraction paper.pdf
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from . import llm
from .africa import africa_profile
from .chem import (canonical_material, dopants_in, elements_in, material_family, normalize_text, parse_conductivity,
                   parse_temperature)
from .config import REPORTS_DIR
from .evidence import verify_evidence

PROPERTIES = ["ionic_conductivity", "specific_capacitance", "specific_capacity", "specific_energy",
              "specific_power", "cycling_stability", "capacity_retention", "potential_window", "rate_capability",
              "sintering_temperature", "activation_energy", "other"]

FACT_SCHEMA = {
    "type": "object",
    "properties": {
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "material": {"type": "string"},
                    "property": {"type": "string", "enum": PROPERTIES},
                    "value": {"type": "number"},
                    "unit": {"type": "string"},
                    "condition": {"type": "string"},
                    "method": {"type": "string"},
                    "evidence_span": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["material", "property", "value", "unit", "condition", "method", "evidence_span",
                             "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["facts"],
    "additionalProperties": False,
}

EXTRACTION_PROMPT = """Extract every material-property-value triple reported in the text below.

Rules:
- `evidence_span` must be copied VERBATIM from the text (a contiguous clause containing the value).
- Use units as written; ionic conductivity in S/cm (convert mS/cm), capacitance in F/g where possible.
- `property` must be one of: {properties}.
- `condition`: temperature, current density, C-rate, cycle count (empty string if none).
- `method`: measurement technique if stated (e.g. EIS, GCD, CV), else empty string.
- `confidence`: 0-1, lower when the value is approximate, a range, or the material is ambiguous.
- Do not infer values that are not stated.

Text:
<<<
{text}
>>>"""

_NUM = r"(\d+(?:\.\d+)?)"
_SENTENCE_SPLIT = re.compile(r"(?<=[.;])\s+(?=[A-Z(])|\n+")
RULES: list[tuple[str, str, re.Pattern]] = [
    ("ionic_conductivity", "S/cm", re.compile(
        r"((?:\d+(?:\.\d+)?\s*(?:[x×]\s*)?)?10\s*\^?\s*-\s*\d+(?:\s*(?:to|-)\s*(?:\d+(?:\.\d+)?\s*[x×]\s*)?10\s*\^?\s*-\s*\d+)?"
        r"\s*(?:S\s*/?\s*cm\s*-?1?|S\s*cm)?(?:\s*(?:at|@)\s*(?:\d+\s*°?\s*C|RT|room temperature))?)", re.I)),
    ("ionic_conductivity_ms", "mS/cm", re.compile(_NUM + r"\s*mS\s*/?\s*cm", re.I)),
    ("specific_capacitance", "F/g", re.compile(_NUM + r"\s*F\s*/?\s*g(?:\s*-?1)?(?:\s*(?:at|@)\s*" + _NUM + r"\s*A\s*/?\s*g(?:\s*-?1)?)?", re.I)),
    ("specific_capacitance", "mF/cm2", re.compile(_NUM + r"\s*mF\s*/?\s*cm\s*-?2", re.I)),
    ("specific_capacity", "mAh/g", re.compile(_NUM + r"\s*mAh\s*/?\s*g(?:\s*-?1)?(?:\s*(?:at|@)\s*" + _NUM + r"\s*C)?", re.I)),
    ("specific_energy", "Wh/kg", re.compile(_NUM + r"\s*Wh\s*/?\s*kg(?:\s*-?1)?", re.I)),
    ("specific_power", "W/kg", re.compile(r"(?<![h\d.])" + _NUM + r"\s*(k?)W\s*/?\s*kg(?:\s*-?1)?", re.I)),
    ("cycling_stability", "%", re.compile(_NUM + r"\s*%[^.;]{0,40}?(?:after|over|for)\s*(\d[\d,]*)\s*cycles", re.I)),
    ("potential_window", "V", re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*V\b", re.I)),
    ("sintering_temperature", "°C", re.compile(r"sinter\w*[^.;]{0,40}?(\d{3,4})\s*°\s*C", re.I)),
    # Context-cued patterns for values written without units, as is common in tables and abstracts.
    ("potential_window", "V", re.compile(r"(?:potential|voltage) window (?:of|was|is)\s*\(?(-?\d+(?:\.\d+)?)\s*(?:-|to)\s*"
                                         r"(\d+(?:\.\d+)?)(?![\d.]*\s*V)", re.I)),
    ("cycling_stability", "%", re.compile(r"(?:retention|stability)[^.;]{0,20}?(?:of|was|is)\s*~?(\d+(?:\.\d+)?)\s*%?\s*"
                                          r"(?:,|@|\(|/|after|over)\s*(\d[\d,]*)", re.I)),
    ("specific_energy", "Wh/kg", re.compile(r"specific energy (?:of|was|is)\s*(\d+(?:\.\d+)?)(?!\s*(?:m|µ|μ|u)?Wh)", re.I)),
    ("specific_power", "W/kg", re.compile(r"specific power (?:of|was|is)\s*(\d+(?:\.\d+)?)()(?!\s*k?W)", re.I)),
]
_MATERIAL_HINT = re.compile(
    r"(LLZ[TAG]?O(?:-[0-9.]*[A-Z][a-z]?)?|Li\d[\w.]*O12|[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*(?:\.\d+)?)+(?:Tx)?(?:-[A-Za-z0-9]+)*|"
    r"PEO|PVDF(?:-HFP)?|PAN|MXene|activated carbon|rGO|graphene|CNTs?|LDH|LiFePO4|NCM\d*)")


def _guess_material(sentence: str, default: str = "") -> str:
    candidates = [m for m in _MATERIAL_HINT.findall(sentence) if not re.fullmatch(r"[A-Z]", m)
                  and m.upper() not in {"EIS", "CV", "GCD", "XRD", "SEM", "RT"}]
    return canonical_material(candidates[0]) if candidates else default


def rule_extract(text: str, default_material: str = "") -> list[dict]:
    """Regex extractor: high precision for the unit patterns above, no inference."""
    facts = []
    clean = normalize_text(text)
    for sentence in _SENTENCE_SPLIT.split(clean):
        material = _guess_material(sentence, default_material)
        for prop, unit, pattern in RULES:
            for match in pattern.finditer(sentence):
                span = match.group(0).strip()
                condition = None
                if prop.startswith("ionic_conductivity"):
                    if prop == "ionic_conductivity_ms":
                        value, prop_name = float(match.group(1)) / 1000.0, "ionic_conductivity"
                    else:
                        value, _ = parse_conductivity(span)
                        prop_name = "ionic_conductivity"
                        if value is None or value > 1:
                            continue
                    unit_name, condition = "S/cm", parse_temperature(span)
                elif prop == "potential_window":
                    value, prop_name, unit_name = float(match.group(2)), prop, unit
                elif prop == "specific_power":
                    value = float(match.group(1)) * (1000.0 if match.group(2) else 1.0)
                    prop_name, unit_name = prop, unit
                elif prop == "cycling_stability":
                    value, prop_name, unit_name = float(match.group(1)), prop, unit
                    condition = f"after {match.group(2).replace(',', '')} cycles"
                else:
                    value, prop_name, unit_name = float(match.group(1)), prop, unit
                    if match.lastindex and match.lastindex >= 2 and match.group(2):
                        condition = f"at {match.group(2)} {'A/g' if unit == 'F/g' else 'C'}"
                facts.append({"material": material, "property": prop_name, "value": value, "unit": unit_name,
                              "condition": condition or "", "method": "", "evidence_span": span,
                              "confidence": 0.7 if material else 0.5})
    # De-duplicate overlapping matches (e.g. a range matched twice).
    unique = {(f["property"], round(f["value"], 12), f["evidence_span"]): f for f in facts}
    return list(unique.values())


def llm_extract(text: str) -> tuple[list[dict], str]:
    result = llm.complete(EXTRACTION_PROMPT.format(properties=", ".join(PROPERTIES), text=text), schema=FACT_SCHEMA)
    if not result.data:
        return [], result.mode
    return list(result.data.get("facts", [])), result.mode


def finalize(raw_facts: list[dict], source_text: str, source: dict, extraction_method: str,
             system: str | None = None) -> list[dict]:
    """Attach grounding, chemistry and Africa annotations to raw extracted facts."""
    out = []
    for index, fact in enumerate(raw_facts):
        material = canonical_material(fact.get("material")) or "unspecified"
        inferred_system = system or ("LLZO" if fact["property"] == "ionic_conductivity" or "LLZ" in material.upper()
                                     else "AHSC")
        role = "electrolyte" if fact["property"] == "ionic_conductivity" else "electrode"
        elements = elements_in(material, inferred_system)
        grounded = verify_evidence(fact.get("evidence_span", ""), source_text)
        flags = [] if grounded else ["evidence_not_found_in_source"]
        out.append({
            "id": f"{source.get('id', 'doc')}-{index:03d}-{fact['property']}",
            "record_id": source.get("id", "doc"),
            "system": inferred_system,
            "material": material,
            "material_role": role,
            "material_family": material_family(material, role),
            "components": {},
            "elements": elements,
            "cell_elements": elements,
            "dopants": dopants_in(material),
            "additives": [],
            "property": fact["property"],
            "property_label": fact["property"].replace("_", " ").capitalize(),
            "property_category": "extracted",
            "value": float(fact["value"]),
            "unit": fact.get("unit", ""),
            "value_details": {},
            "condition": fact.get("condition") or None,
            "method": fact.get("method") or "not stated",
            "source": {"type": source.get("type", "literature"), "record_id": source.get("id", "doc"),
                       "doi": source.get("doi"), "title": source.get("title"), "year": source.get("year"),
                       "file": source.get("file")},
            "evidence_span": fact.get("evidence_span", ""),
            "evidence_text": "",  # full text lives in data/literature; kept out of the JSONL for size
            "confidence": round(float(fact.get("confidence", 0.5)) * (1.0 if grounded else 0.3), 3),
            "quality_flags": flags,
            "grounded": grounded,
            "extraction_method": extraction_method,
            "africa": africa_profile(elements),
            "text": f"{material} has {fact['property'].replace('_', ' ')} of {float(fact['value']):.4g} "
                    f"{fact.get('unit', '')} {fact.get('condition') or ''}. Source: "
                    f"{source.get('doi') or source.get('title') or source.get('id')}.",
        })
    return out


def extract(text: str, source: dict | None = None, use_llm: bool | None = None, system: str | None = None) -> dict:
    """Extract grounded facts from text. LLM first (if configured), rule-based otherwise."""
    source = source or {"id": "adhoc", "type": "user_text"}
    use_llm = llm.available() if use_llm is None else use_llm
    mode = "rule-based"
    raw: list[dict] = []
    if use_llm:
        raw, mode = llm_extract(text)
    if not raw:
        raw = rule_extract(text)
        mode = f"rule-based ({mode})" if use_llm else "rule-based"
    facts = finalize(raw, text, source, mode, system)
    grounded = sum(f["grounded"] for f in facts)
    return {"mode": mode, "facts": facts, "n_facts": len(facts),
            "grounding_rate": round(grounded / len(facts), 4) if facts else None}


def pdf_to_text(path: Path) -> str:
    from pypdf import PdfReader

    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def extract_pdf(path: Path, source: dict | None = None, use_llm: bool | None = None) -> dict:
    text = pdf_to_text(path)
    return extract(text, source or {"id": path.stem, "type": "pdf", "file": str(path)}, use_llm)


# ---------------------------------------------------------------- validation vs. thesis
def record_sentences(fact_group: list[dict]) -> str:
    """Render one curated record as abstract-style prose built only from its raw cell text."""
    first = fact_group[0]
    parts = [f"In this work, {first['material']} was studied"]
    comps = first["components"]
    if comps:
        parts[0] += " in a cell with " + ", ".join(f"{v} as {k}" for k, v in comps.items())
    lines = [parts[0] + "."]
    phrasing = {"potential_window": "The device operated over a potential window of {raw}.",
                "specific_capacitance": "It delivered a specific capacitance of {raw}.",
                "specific_capacity": "It delivered a specific capacity of {raw}.",
                "specific_energy": "The specific energy was {raw}.",
                "specific_power": "The specific power was {raw}.",
                "cycling_stability": "Cycling stability was {raw}.",
                "capacity_retention": "Capacity retention was {raw}.",
                "rate_capability": "Rate capability was {raw}.",
                "ionic_conductivity": "The ionic conductivity was {raw}."}
    for fact in fact_group:
        lines.append(phrasing[fact["property"]].format(raw=fact["evidence_span"]))
    return " ".join(lines)


def _matches(predicted: dict, gold: dict) -> bool:
    if predicted["property"] != gold["property"]:
        return False
    value, target = predicted["value"], gold["value"]
    if gold["property"] == "ionic_conductivity":
        return abs(value - target) <= 0.05 * abs(target)
    return abs(value - target) <= max(0.02 * abs(target), 0.011)


def validate(use_llm: bool = False, limit: int | None = None, facts: list[dict] | None = None) -> dict:
    """Precision / recall / grounding of the extractor against manually curated thesis facts.

    The benchmark text for each record is generated from that record's verbatim raw cells, so
    it measures value/unit/property extraction, not full-paper reading. Gold facts with units
    the extractor is not designed for (e.g. mF/cm or C/g) still count against recall.
    """
    from .facts import load_facts
    facts = facts or [f for f in load_facts(include_literature=False) if not f["quality_flags"]]
    groups: dict[str, list[dict]] = {}
    for fact in facts:
        groups.setdefault(fact["record_id"], []).append(fact)
    record_ids = sorted(groups)[:limit] if limit else sorted(groups)
    tp = fp = fn = grounded = predicted_total = 0
    per_property: dict[str, dict] = {}
    mode = "rule-based"
    for record_id in record_ids:
        gold = groups[record_id]
        text = record_sentences(gold)
        result = extract(text, {"id": record_id, "type": "benchmark"}, use_llm=use_llm, system=gold[0]["system"])
        mode = result["mode"]
        predicted = [p for p in result["facts"] if p["property"] in {g["property"] for g in gold} | set(PROPERTIES)]
        predicted_total += len(predicted)
        grounded += sum(p["grounded"] for p in predicted)
        unmatched = list(predicted)
        for item in gold:
            stats = per_property.setdefault(item["property"], {"tp": 0, "fn": 0, "fp": 0})
            hit = next((p for p in unmatched if _matches(p, item)), None)
            if hit:
                tp += 1
                stats["tp"] += 1
                unmatched.remove(hit)
            else:
                fn += 1
                stats["fn"] += 1
        for extra in unmatched:
            fp += 1
            per_property.setdefault(extra["property"], {"tp": 0, "fn": 0, "fp": 0})["fp"] += 1
    for stats in per_property.values():
        stats["precision"] = round(stats["tp"] / (stats["tp"] + stats["fp"]), 3) if stats["tp"] + stats["fp"] else None
        stats["recall"] = round(stats["tp"] / (stats["tp"] + stats["fn"]), 3) if stats["tp"] + stats["fn"] else None
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"extractor": mode, "records": len(record_ids), "gold_facts": tp + fn, "predicted_facts": predicted_total,
            "true_positives": tp, "false_positives": fp, "false_negatives": fn,
            "precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
            "evidence_grounding_rate": round(grounded / predicted_total, 4) if predicted_total else None,
            "per_property": dict(sorted(per_property.items())),
            "note": "Benchmark sentences are generated from each record's verbatim raw cells; gold = curated "
                    "thesis values without quality flags."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", type=Path, help="PDF or .txt file to extract from")
    parser.add_argument("--validate", action="store_true", help="benchmark against curated thesis facts")
    parser.add_argument("--llm", action="store_true", help="use the configured LLM provider")
    parser.add_argument("--limit", type=int, help="limit benchmark records (LLM cost control)")
    args = parser.parse_args()
    if args.validate:
        report = validate(use_llm=args.llm, limit=args.limit)
        REPORTS_DIR.mkdir(exist_ok=True)
        name = "extraction_validation_llm.json" if args.llm else "extraction_validation.json"
        (REPORTS_DIR / name).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in report.items() if k != "per_property"}, indent=2))
        return
    if not args.path:
        parser.error("give a PDF/text path or --validate")
    if args.path.suffix.lower() == ".pdf":
        result = extract_pdf(args.path, use_llm=args.llm or None)
    else:
        result = extract(args.path.read_text(encoding="utf-8"), {"id": args.path.stem, "type": "text",
                                                                   "file": str(args.path)}, args.llm or None)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
