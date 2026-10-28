# Ontology

The machine-readable definition is [`schema.json`](../schema.json). This page explains the design choices.

## Entities

| Entity | Identity | Key attributes | Notes |
|---|---|---|---|
| **Material** | canonical name | system, role, family, elements, Africa score | The *study subject*: the electrode for AHSC records and the electrolyte for LLZO records. Cell components (anode, separator electrolyte, interlayers) are also Materials, linked through `usesComponent`. |
| **MaterialFamily** | family name | – | 26 coarse classes (MXene, LDH, Garnet LLZO, PEO/PEG polymer, Polymer-garnet composite, …) assigned by ordered regex rules in `knowledge_engine/chem.py`. Electrolyte-only families never apply to electrodes. |
| **Property** | snake_case name | unit, category | Controlled vocabulary in `schema.json → properties_vocabulary`. |
| **Value** | fact id | number, unit, condition, method, confidence, quality flags | One reported measurement = one fact in the JSONL. In the graph, values are aggregated on the `hasProperty` edge (values, units, fact ids, sources, n, median). |
| **Paper** | DOI, or curated record id | title, year, source type | A curated row becomes a DOI-identified paper when `data/record_sources.csv` links it (value-verified or exact-title match). Each fact's `source` also carries `review_doi` for the review table the row was compiled from (`review_link` = `verified_row` or `block_inferred`). |
| **Element** | symbol | African supply status | Parsed from formulas and known abbreviations (LFP, LLZTO, AC, MXene …). |
| **Dopant** | element symbol | – | Garnet dopants detected from `LLZO-0.5Ta`, `LLZTO`, `Li6.5La3Zr1.5Ta0.5O12`, `Al-doped` … |
| **System** | AHSC / LLZO | – | |
| **Country** | name | – | African countries with production of an element (`data/africa_element_supply.csv`). |

## Relationships

```
Material  -hasProperty->     Property      (edge holds Values: numbers, units, fact ids, sources)
Property  -hasValue->        Value         (materialised as JSONL facts)
Material  -studiedIn->       Paper
Paper     -usesComponent->   Material      (role = cathode | anode | electrolyte)
Material  -memberOf->        MaterialFamily
Material  -containsElement-> Element
Material  -dopedWith->       Dopant
Material  -inSystem->        System
Element   -suppliedBy->      Country
```

## Fact record

Each line of `data/thesis_facts.jsonl` is one fact. Abridged example:

```json
{"id": "LLZO-0002-ionic_conductivity", "system": "LLZO",
 "material": "Garnet-type Li6.5La3Zr1.5Ta0.5O12 (LLZO)", "material_family": "Garnet LLZO",
 "dopants": ["Ta"], "elements": ["La", "Li", "O", "Ta", "Zr"],
 "property": "ionic_conductivity", "value": 0.000316, "unit": "S/cm", "condition": null,
 "source": {"type": "thesis_curated_record", "file": "llzo_cleaned (1).csv", "csv_line": 3, "doi": null},
 "evidence_span": "10⁻⁴ to 10⁻³ S cm⁻¹.",
 "confidence": 0.8, "quality_flags": ["corrected_from_raw_text", "range_reported"],
 "africa": {"score": 0.825, "african_supply": ["La", "Li", "Ta", "Zr"], "flags": ["Ta: responsible-sourcing due diligence required"]}}
```

## Evidence grounding

`evidence_span` must occur verbatim in the source text. For curated records the source text is the
serialised raw CSV row (`evidence_text`). For mined papers it is the abstract or PDF text.
`verify_evidence()` (in `knowledge_engine/evidence.py`) normalises only whitespace, case, unicode
sub/superscripts and dash variants, and never accepts paraphrase. Mined facts that fail the check are
dropped from the knowledge base.

## Quality flags

| Flag | Meaning | Used in statistics? |
|---|---|---|
| `unit_assumed` | Raw text had no unit; the column's thesis unit was assumed | yes |
| `reinterpreted_column` | AHSC "capacity retention" cells holding `capacitance/current` were mapped to `rate_capability` | yes |
| `corrected_from_raw_text` | Curated number was non-physical; value re-parsed from the raw text | yes |
| `range_reported` | Source gave a range; geometric mean stored | yes |
| `non_gravimetric_unit` | Areal/volumetric unit (e.g. mWh/cm³) in a gravimetric column | yes (separate unit) |
| `implausible_value_check_source` | e.g. retention > 100 % or window > 6.5 V | **no** |
| `unusually_high_check_source` | ionic conductivity > 0.05 S/cm | **no** |
| `raw_text_disagrees_with_curated_value` | Curated and re-parsed values differ by > 5 % | **no** |
| `theoretical_value` | Theoretical rather than measured | **no** |
| `non_standard_retention_metric` | Mechanical/OCV retention, not cycling | **no** |

## Africa layer

`africa.score` is the mean over a material's non-trivial elements (H, O and N excluded) of the supply
weight: major producer or ubiquitous = 1.0, producer = 0.8, project stage = 0.5, none = 0. Hypotheses get
an extra composite score that combines supply (55 %), processing temperature against the 1000 °C limit
(30 %) and application fit (15 %), with a penalty for scarce elements.
