"""Phase 2.1: grow the corpus with real papers (metadata + abstracts) and mine them.

Sources: OpenAlex (search + reconstructed abstracts, no key needed) and Crossref (DOI
metadata). Queries are Africa-structural: besides core AHSC/LLZO topics they target
chemistries built from African-supplied elements (Mn, Fe, Ti, Zr, graphite, biomass carbon).

    python -m knowledge_engine.literature harvest --per-query 40     # -> data/literature/metadata.json
    python -m knowledge_engine.literature dois dois.txt               # Crossref lookup for thesis DOIs
    python -m knowledge_engine.literature provenance                  # verified papers found per record
    python -m knowledge_engine.literature mine [--llm]                # -> data/literature_facts.jsonl

Set KE_CONTACT_EMAIL to join the OpenAlex/Crossref "polite pool".
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

import requests

from .config import LITERATURE_FACTS_JSONL, LITERATURE_METADATA
from .facts import write_jsonl

QUERIES: dict[str, list[str]] = {
    "LLZO": [
        "Ta-doped LLZO garnet ionic conductivity",
        "Al-doped Li7La3Zr2O12 sintering temperature",
        "Ga-doped LLZO cubic phase conductivity",
        "low temperature sintering garnet solid electrolyte",
        "LLZO PEO composite polymer electrolyte",
        "garnet lithium metal interface interlayer",
        "LiFePO4 solid-state battery garnet electrolyte",
    ],
    "AHSC": [
        "asymmetric hybrid supercapacitor specific capacitance",
        "biomass derived activated carbon supercapacitor",
        "MnO2 asymmetric supercapacitor cycling stability",
        "NiCo layered double hydroxide hybrid supercapacitor",
        "Ti3C2 MXene supercapacitor electrode",
        "zinc ion hybrid supercapacitor",
        "natural graphite derived graphene supercapacitor Africa",
        "Fe2O3 negative electrode asymmetric supercapacitor",
    ],
}


def _session() -> requests.Session:
    session = requests.Session()
    contact = os.getenv("KE_CONTACT_EMAIL", "")
    session.headers["User-Agent"] = f"ahsc-llzo-knowledge-engine/1.0 (mailto:{contact})" if contact else \
        "ahsc-llzo-knowledge-engine/1.0"
    return session


def _abstract_from_inverted_index(index: dict | None) -> str:
    if not index:
        return ""
    positions = [(position, word) for word, places in index.items() for position in places]
    return " ".join(word for _, word in sorted(positions))


def openalex_search(query: str, per_page: int = 25, session: requests.Session | None = None) -> list[dict]:
    session = session or _session()
    params = {"search": query, "per-page": min(per_page, 200), "filter": "has_abstract:true,type:article",
              "select": "id,doi,title,publication_year,authorships,abstract_inverted_index,open_access,primary_location"}
    contact = os.getenv("KE_CONTACT_EMAIL")
    if contact:
        params["mailto"] = contact
    response = session.get("https://api.openalex.org/works", params=params, timeout=30)
    response.raise_for_status()
    papers = []
    for work in response.json().get("results", []):
        papers.append({
            "id": work["id"].rsplit("/", 1)[-1],
            "doi": (work.get("doi") or "").replace("https://doi.org/", "") or None,
            "title": work.get("title") or "",
            "year": work.get("publication_year"),
            "authors": [a["author"]["display_name"] for a in work.get("authorships", [])[:8]],
            "abstract": _abstract_from_inverted_index(work.get("abstract_inverted_index")),
            "open_access_url": (work.get("open_access") or {}).get("oa_url"),
            "query": query,
        })
    return papers


def fetch_paper_metadata(doi: str, session: requests.Session | None = None) -> dict:
    """Crossref metadata for one DOI (title, authors, year, abstract when deposited)."""
    session = session or _session()
    response = session.get(f"https://api.crossref.org/works/{doi}", timeout=30)
    response.raise_for_status()
    message = response.json()["message"]
    abstract = re.sub(r"<[^>]+>", " ", message.get("abstract", "") or "")
    return {"id": doi, "doi": doi, "title": " ".join(message.get("title", [])),
            "year": (message.get("issued", {}).get("date-parts") or [[None]])[0][0],
            "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in message.get("author", [])[:8]],
            "abstract": re.sub(r"\s+", " ", abstract).strip(), "query": "thesis reference"}


def _merge_save(papers: list[dict], path: Path = LITERATURE_METADATA) -> list[dict]:
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    by_key = {p.get("doi") or p["id"]: p for p in existing}
    for paper in papers:
        by_key.setdefault(paper.get("doi") or paper["id"], paper)
    merged = list(by_key.values())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(merged, indent=1, ensure_ascii=False), encoding="utf-8")
    return merged


def harvest(per_query: int = 40, pause: float = 1.0) -> list[dict]:
    session, papers = _session(), []
    for system, queries in QUERIES.items():
        for query in queries:
            for paper in openalex_search(query, per_query, session):
                papers.append({**paper, "system": system})
            time.sleep(pause)
    return _merge_save(papers)


def lookup_dois(dois: list[str], pause: float = 1.0) -> list[dict]:
    session, papers = _session(), []
    for doi in dois:
        try:
            papers.append(fetch_paper_metadata(doi.strip(), session))
        except requests.RequestException as exc:
            print(f"skip {doi}: {exc}")
        time.sleep(pause)
    return _merge_save(papers)


def corpus_from_provenance() -> list[dict]:
    """Add every verified paper from data/provenance/doi_search_log.jsonl to the corpus.

    The stored text is the verbatim evidence sentence returned by the web search (not a full
    abstract), so facts mined from it remain grounded in text that was actually retrieved.
    """
    from .record_sources import REVIEW_LOG, SEARCH_LOG, _read_jsonl

    papers = []
    for entry in _read_jsonl(SEARCH_LOG):
        if not entry.get("evidence") or not (entry.get("doi") or entry.get("url")):
            continue
        papers.append({"id": entry.get("doi") or entry["url"], "doi": entry.get("doi"), "url": entry.get("url"),
                       "title": entry.get("title") or "", "year": entry.get("year"),
                       "abstract": entry["evidence"], "text_type": "verbatim evidence excerpt",
                       "system": entry["record_id"].split("-")[0], "linked_record": entry["record_id"],
                       "query": "per-record source search (Exa web search)"})
    for review in _read_jsonl(REVIEW_LOG):
        papers.append({"id": review["review_doi"], "doi": review["review_doi"], "url": review.get("review_url"),
                       "title": review["review_title"], "year": review.get("review_year"), "abstract": "",
                       "text_type": "source review (table compiled into the thesis dataset)",
                       "system": review["range"][0].split("-")[0], "query": "source review identification"})
    return _merge_save(papers)


def mine(use_llm: bool | None = None) -> list[dict]:
    """Extract grounded facts from every harvested abstract into data/literature_facts.jsonl."""
    from .extraction import extract

    from .config import RECORD_SOURCES_CSV

    papers = json.loads(LITERATURE_METADATA.read_text(encoding="utf-8")) if LITERATURE_METADATA.exists() else []
    records = {}
    if RECORD_SOURCES_CSV.exists():
        import pandas as pd
        records = {r["record_id"]: r for r in pd.read_csv(RECORD_SOURCES_CSV, dtype=str).fillna("").to_dict("records")}
    facts = []
    for paper in papers:
        if not paper.get("abstract"):
            continue
        source = {"id": paper.get("doi") or paper["id"], "type": "literature_abstract", "doi": paper.get("doi"),
                  "title": paper.get("title"), "year": paper.get("year"), "file": paper.get("url")}
        record = records.get(paper.get("linked_record", ""))
        if record:  # the paper was matched to a curated record, so its cell components are known
            source["system"] = paper.get("system")
            source["components"] = {"cathode": record["cathode_material"], "anode": record.get("anode_material", ""),
                                    "electrolyte": record["electrolyte"]}
        result = extract(paper["abstract"], source, use_llm=use_llm, system=paper.get("system"))
        facts += [fact for fact in result["facts"] if fact["grounded"]]
    write_jsonl(facts, LITERATURE_FACTS_JSONL)
    return facts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    h = sub.add_parser("harvest")
    h.add_argument("--per-query", type=int, default=40)
    d = sub.add_parser("dois")
    d.add_argument("file", type=Path, help="text file with one DOI per line")
    sub.add_parser("provenance", help="add verified papers from data/provenance to the corpus")
    m = sub.add_parser("mine")
    m.add_argument("--llm", action="store_true")
    args = parser.parse_args()
    if args.command == "harvest":
        print(f"{len(harvest(args.per_query))} papers in {LITERATURE_METADATA}")
    elif args.command == "provenance":
        print(f"{len(corpus_from_provenance())} papers in {LITERATURE_METADATA}")
    elif args.command == "dois":
        print(f"{len(lookup_dois(args.file.read_text().split()))} papers in {LITERATURE_METADATA}")
    else:
        print(f"{len(mine(args.llm or None))} grounded literature facts in {LITERATURE_FACTS_JSONL}")


if __name__ == "__main__":
    main()
