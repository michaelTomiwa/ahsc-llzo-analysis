"""Link every curated thesis record to its literature source (paper DOI and/or source review).

Two provenance logs drive data/record_sources.csv:
- data/provenance/doi_search_log.jsonl: one entry per searched record. A DOI is accepted only if
  the paper's own text shows the record's material and values ("verified_values"), or its
  title names the exact material ("title"). Entries keep the verbatim sentence used as evidence.
- data/provenance/review_sources.jsonl: review tables that the curated rows were compiled from,
  with the verified row range and (separately) the probable extension of the block.

    python -m knowledge_engine.record_sources build          # regenerate data/record_sources.csv
    python -m knowledge_engine.record_sources resolve        # Crossref lookup for unmatched records
                                                             # (needs api.crossref.org network access)
"""
from __future__ import annotations

import argparse
import json
import re
import time

import pandas as pd

from .chem import canonical_material, is_missing, normalize_text
from .config import AHSC_CSV, DATA_DIR, LLZO_CSV, RECORD_SOURCES_CSV

PROVENANCE_DIR = DATA_DIR / "provenance"
SEARCH_LOG = PROVENANCE_DIR / "doi_search_log.jsonl"
REVIEW_LOG = PROVENANCE_DIR / "review_sources.jsonl"
COLUMNS = ["record_id", "doi", "title", "year", "url", "match_type", "matched_values", "evidence",
           "source_review_doi", "source_review_title", "source_review_url", "review_link",
           "cathode_material", "anode_material", "electrolyte"]


def _read_jsonl(path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _record_ids() -> list[tuple[str, pd.Series]]:
    out = []
    for system, path in (("AHSC", AHSC_CSV), ("LLZO", LLZO_CSV)):
        frame = pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
        frame.columns = [c.strip().lower() for c in frame.columns]
        out += [(f"{system}-{i + 1:04d}", row) for i, row in frame.iterrows()]
    return out


def _in_range(record_id: str, start: str, end: str) -> bool:
    system, number = record_id.split("-")
    s_system, s_number = start.split("-")
    e_system, e_number = end.split("-")
    return system == s_system == e_system and int(s_number) <= int(number) <= int(e_number)


def build() -> pd.DataFrame:
    searches = {entry["record_id"]: entry for entry in _read_jsonl(SEARCH_LOG)}
    reviews = _read_jsonl(REVIEW_LOG)
    rows = []
    for record_id, raw in _record_ids():
        entry = searches.get(record_id, {})
        row = {column: "" for column in COLUMNS}
        row["record_id"] = record_id
        row["cathode_material"] = "" if is_missing(raw.get("cathode_material")) else canonical_material(raw["cathode_material"])
        row["anode_material"] = "" if is_missing(raw.get("anode_material")) else canonical_material(raw["anode_material"])
        row["electrolyte"] = "" if is_missing(raw.get("electrolyte")) else canonical_material(raw["electrolyte"])
        if entry.get("doi") or entry.get("url"):
            row.update({"doi": entry.get("doi") or "", "title": entry.get("title") or "",
                        "year": entry.get("year") or "", "url": entry.get("url") or "",
                        "match_type": entry.get("match") or "verified_values",
                        "matched_values": "; ".join(entry.get("matched_values", [])),
                        "evidence": entry.get("evidence", "")})
        for review in reviews:
            verified = _in_range(record_id, *review["range"])
            probable = False
            extension = review.get("extends_probably_to")
            if not verified and extension:
                ids = re.findall(r"[A-Z]+-\d{4}", extension)
                start, end = (ids[0], ids[1]) if len(ids) > 1 else (review["range"][0], ids[0])
                probable = _in_range(record_id, start, end)
            if verified or probable:
                row.update({"source_review_doi": review["review_doi"], "source_review_title": review["review_title"],
                            "source_review_url": review.get("review_url", ""),
                            "review_link": "verified_row" if verified else "block_inferred"})
                break
        rows.append(row)
    table = pd.DataFrame(rows, columns=COLUMNS)
    table.to_csv(RECORD_SOURCES_CSV, index=False)
    return table


def coverage(table: pd.DataFrame | None = None) -> dict:
    table = table if table is not None else pd.read_csv(RECORD_SOURCES_CSV, dtype=str).fillna("")
    table = table.fillna("")
    has_doi = table.doi.ne("")
    return {
        "records": len(table),
        "paper_doi": int(has_doi.sum()),
        "paper_doi_value_verified": int((has_doi & table.match_type.eq("verified_values")).sum()),
        "paper_doi_title_match": int((has_doi & table.match_type.eq("title")).sum()),
        "paper_verified_url_only": int((~has_doi & table.url.ne("")).sum()),
        "source_review_verified_row": int(table.review_link.eq("verified_row").sum()),
        "source_review_block_inferred": int(table.review_link.eq("block_inferred").sum()),
        "any_citation": int((has_doi | table.url.ne("") | table.source_review_doi.ne("")).sum()),
        "records_searched": len(_read_jsonl(SEARCH_LOG)),
    }


# ---------------------------------------------------------------- automated resolver
def _record_query(raw: pd.Series, system: str) -> tuple[str, list[str]]:
    """Crossref bibliographic query plus the numeric strings a matching abstract must contain."""
    fields = ["cathode_material", "anode_material", "electrolyte"] if system == "AHSC" else \
        ["electrolyte", "cathode_material"]
    words = " ".join(normalize_text(raw.get(f)) for f in fields if not is_missing(raw.get(f)))
    numbers = []
    for field in ("capacitance_capacity", "specific_energy", "ionic_conductivity", "cycling_stability"):
        if not is_missing(raw.get(field)):
            numbers += re.findall(r"\d+\.\d+|\d{3,}", normalize_text(raw.get(field)))
    topic = "supercapacitor" if system == "AHSC" else "solid electrolyte lithium"
    return f"{words} {topic} {' '.join(numbers[:3])}".strip(), numbers


def resolve(limit: int | None = None, pause: float = 1.0) -> list[dict]:
    """Search Crossref for records without a paper DOI and accept only value-verified matches.

    A candidate is accepted when its abstract (as deposited with Crossref) contains at least one
    of the record's numeric values AND one material token. Accepted matches are appended to the
    search log with match type "verified_values" and the evidence sentence.
    """
    from .literature import _session

    session = _session()
    done = {e["record_id"] for e in _read_jsonl(SEARCH_LOG) if e.get("doi")}
    accepted = []
    for record_id, raw in _record_ids():
        if record_id in done:
            continue
        if limit is not None and len(accepted) >= limit:
            break
        system = record_id.split("-")[0]
        query, numbers = _record_query(raw, system)
        if not numbers:
            continue
        response = session.get("https://api.crossref.org/works",
                                params={"query.bibliographic": query, "rows": 5,
                                        "select": "DOI,title,abstract,issued"}, timeout=30)
        response.raise_for_status()
        material = canonical_material(raw.get("cathode_material") if system == "AHSC" else raw.get("electrolyte"))
        tokens = [t for t in re.findall(r"[A-Za-z0-9@/.\-]{3,}", material)][:3]
        for item in response.json()["message"]["items"]:
            abstract = re.sub(r"<[^>]+>", " ", item.get("abstract", "") or "")
            if not abstract:
                continue
            value_hit = next((n for n in numbers if n in abstract), None)
            token_hit = next((t for t in tokens if t.lower() in abstract.lower()), None)
            if value_hit and token_hit:
                sentence = next((s for s in re.split(r"(?<=[.;])\s+", abstract) if value_hit in s), abstract[:300])
                entry = {"record_id": record_id, "doi": item["DOI"], "title": " ".join(item.get("title", [])),
                         "year": (item.get("issued", {}).get("date-parts") or [[None]])[0][0],
                         "matched_values": [token_hit, value_hit], "evidence": sentence.strip(),
                         "match": "verified_values", "method": "crossref resolver"}
                accepted.append(entry)
                with SEARCH_LOG.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
                break
        time.sleep(pause)
    return accepted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["build", "resolve", "coverage"])
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.command == "resolve":
        print(f"{len(resolve(args.limit))} new value-verified DOIs")
        build()
    elif args.command == "build":
        build()
    print(json.dumps(coverage(), indent=2))


if __name__ == "__main__":
    main()
