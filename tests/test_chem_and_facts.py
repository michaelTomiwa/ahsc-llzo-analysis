import pytest

from knowledge_engine.africa import africa_profile, africa_rerank_score
from knowledge_engine.chem import (canonical_material, detect_unit, dopants_in, elements_in, material_family,
                                   parse_conductivity, parse_temperature)
from knowledge_engine.evidence import grounding_report, verify_evidence
from knowledge_engine.facts import build_facts


@pytest.mark.parametrize("raw,expected", [
    ("2.9 × 10⁻⁴ S cm⁻¹.", 2.9e-4),
    ("0.52 × 10⁻⁴ at RT", 5.2e-5),
    ("10−4 at 60", 1e-4),
    ("3 x 10⁻³ S cm⁻¹", 3e-3),
])
def test_parse_conductivity(raw, expected):
    value, _ = parse_conductivity(raw)
    assert value == pytest.approx(expected)


def test_conductivity_range_uses_geometric_mean():
    value, note = parse_conductivity("10⁻⁴ to 10⁻³ S cm⁻¹.")
    assert value == pytest.approx(10 ** -3.5)
    assert note.startswith("range")


def test_temperature_and_units():
    assert parse_temperature("9 × 10⁻⁵ S cm⁻¹ at 80 °C") == "80 °C"
    assert parse_temperature("1.24 × 10⁻⁴ at RT") == "room temperature"
    assert detect_unit("236 F/g @1 A/g", "?") == ("F/g", True)
    assert detect_unit("7.8 mF cm–2", "?") == ("mF/cm2", True)
    assert detect_unit("257.8", "F/g") == ("F/g", False)


def test_elements_dopants_families():
    assert elements_in("LLZO-0.25Ga") == ["Ga", "La", "Li", "O", "Zr"]
    assert dopants_in("Garnet-type Li₆.₅La₃Zr₁.₅Ta₀.₅O₁₂ (LLZO)") == ["Ta"]
    assert dopants_in("PEO-LLZTO (with LiTFSI)") == ["Ta"]
    assert material_family("Ti3C2Tx/rGO(electrode material)") == "MXene"
    assert material_family("PVDF-HFP (with DMF and LiTFSI)", "electrolyte") == "PVDF-based polymer"
    assert material_family("PEO (with LLZTO)", "electrolyte") == "Polymer-garnet composite"
    assert canonical_material("AC") == "Activated carbon"
    # In supercapacitor papers 'NCM' is usually a carbon, not a lithium cathode.
    assert "Li" not in elements_in("NiCo-LDH/NCM@NF", "AHSC")


def test_africa_scores():
    assert africa_profile(["Mn", "O"])["score"] == 1.0
    assert africa_profile(["Ga", "In"])["score"] == 0.0
    cobalt = africa_profile(["Co", "O"])
    assert any("due diligence" in flag for flag in cobalt["flags"])
    hot = africa_rerank_score(["Mn", "O"], 1300)["africa_score"]
    cool = africa_rerank_score(["Mn", "O"], 600)["africa_score"]
    assert cool > hot


def test_verify_evidence():
    source = "The ionic conductivity was 6.1 × 10−4 S cm−1 at 25 °C."
    assert verify_evidence("6.1 × 10−4 S cm−1", source)
    assert verify_evidence("6.1 × 10-4 S cm-1", source)  # unicode-normalised match
    assert not verify_evidence("6.1 × 10-3 S cm-1", source)
    assert not verify_evidence("", source)


@pytest.fixture(scope="module")
def facts():
    return build_facts()


def test_facts_cover_curated_records(facts):
    records = {f["record_id"] for f in facts}
    assert len(records) >= 500  # 533 curated rows; a few report no numeric property
    assert {f["system"] for f in facts} == {"AHSC", "LLZO"}
    assert len({f["id"] for f in facts}) == len(facts)


def test_facts_are_grounded_and_well_formed(facts):
    report = grounding_report(facts)
    assert report["grounding_rate"] == 1.0
    for fact in facts[:200]:
        assert 0 < fact["confidence"] <= 1
        assert fact["evidence_span"] and fact["unit"]
        assert fact["source"]["type"] == "thesis_curated_record"


def test_implausible_conductivity_is_corrected(facts):
    # LLZO row 2 stores 7.0 S/cm for '10⁻⁴ to 10⁻³ S cm⁻¹'; the digitiser must repair and flag it.
    fact = next(f for f in facts if f["id"] == "LLZO-0002-ionic_conductivity")
    assert fact["value"] < 1e-2
    assert "corrected_from_raw_text" in fact["quality_flags"]


def test_thesis_medians_match(facts):
    import statistics

    llzo_sigma = [f["value"] for f in facts if f["system"] == "LLZO" and f["property"] == "ionic_conductivity"]
    assert 1e-4 < statistics.median(llzo_sigma) < 1e-3


def test_record_sources_provenance():
    from knowledge_engine.record_sources import build, coverage

    table = build()
    stats = coverage(table)
    assert stats["records"] == 533
    assert stats["paper_doi"] >= 20 and stats["source_review_verified_row"] >= 50
    linked = table[table.doi.ne("")]
    assert linked.doi.str.startswith("10.").all()
    # Every value-verified DOI keeps the verbatim sentence it was accepted on.
    assert linked[linked.match_type.eq("verified_values")].evidence.str.len().gt(20).all()


def test_facts_carry_paper_and_review_dois(facts):
    first = next(f for f in facts if f["record_id"] == "AHSC-0001")
    assert first["source"]["doi"] == "10.1016/j.jcis.2023.10.067"
    assert first["source"]["review_doi"] == "10.3390/inorganics13020049"
    assert first["source"]["review_link"] == "verified_row"


def test_africa_supply_table_is_verified():
    from knowledge_engine.africa import supply_table

    table = supply_table()
    assert {"verification", "usgs_2024_african_production", "source_url"} <= set(table.columns)
    cobalt = table[table.element == "Co"].iloc[0]
    assert "76%" in cobalt.usgs_2024_african_production and cobalt.verification.startswith("verified")
    assert not table.source_url.str.contains("mcs2026").any()
