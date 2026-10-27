# Contributing

Contributions of data, extraction rules, ontology terms and code are welcome.

## Setup

```bash
python -m pip install -r requirements.txt
python -m knowledge_engine.pipeline      # rebuild facts, graph and reports
pytest -q                                # offline, no API key needed
```

## Ways to contribute

**Add DOIs to curated records.** Fill the `doi`, `title` and `year` columns of `data/record_sources.csv`
(one row per thesis record, e.g. `AHSC-0001`) and rerun the pipeline. Every fact, citation and hypothesis
then links to `https://doi.org/<doi>`.

**Add papers.** Run `python -m knowledge_engine.literature dois my_dois.txt` or `... harvest`, then
`... mine`. Only facts whose evidence span is found verbatim in the abstract are stored.

**Correct a value.** Fix the source CSV, not `data/thesis_facts.jsonl` (it is generated). If a value is
suspect but cannot be fixed, the digitiser's quality flags (`reports/data_quality.json`) should catch it.
Add a rule in `knowledge_engine/facts.py` if they do not.

**Improve chemistry rules.** Material families, element parsing and dopant detection live in
`knowledge_engine/chem.py`. Add a test in `tests/test_chem_and_facts.py` for every new rule.

**Africa supply data.** `data/africa_element_supply.csv` holds qualitative statuses from USGS sources.
Changes need a source URL, and statuses must reflect production rather than resource or exploration claims.

## Pull requests

- Keep evidence grounding at 100% for curated facts and at least 95% for extracted facts.
- Run `pytest -q` before opening a PR. CI runs the same tests in offline mode.
- Never commit `.env` or API keys.
- Describe any change to `schema.json` in `docs/ONTOLOGY.md`.
