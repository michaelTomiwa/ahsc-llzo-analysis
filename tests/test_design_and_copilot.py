import numpy as np

from knowledge_engine.copilot import parse_request, recommend
from knowledge_engine.design_explorer import load_shap, measured_devices, pareto_ranks, thesis_designs, trade_off_score


def test_pareto_ranks_are_non_dominated_sorting():
    energy = np.array([10, 5, 8, 4, 10])
    power = np.array([1, 9, 8, 2, 1])
    ranks = pareto_ranks(energy, power)
    assert list(ranks) == [1, 1, 1, 2, 1]  # equal points do not dominate each other


def test_measured_devices_and_front():
    devices = measured_devices()
    assert len(devices) >= 40
    assert (devices.energy_wh_kg > 0).all() and (devices.power_w_kg > 0).all()
    front = devices[devices.front == 1]
    for _, row in front.iterrows():  # nothing measured beats a front point on both objectives
        assert not ((devices.energy_wh_kg > row.energy_wh_kg) & (devices.power_w_kg > row.power_w_kg)).any()


def test_thesis_designs_match_table_4_1():
    designs = thesis_designs()
    top = designs[designs["rank"] == 1].iloc[0]
    assert (top.anode, top.cathode) == ("Graphene", "PANI@NiCu")
    assert (top.energy_wh_kg, top.power_w_kg) == (81.67, 1342.82)


def test_trade_off_slider_extremes():
    devices = measured_devices()
    assert devices.loc[trade_off_score(devices, 1.0).idxmax()].energy_wh_kg == devices.energy_wh_kg.max()
    assert devices.loc[trade_off_score(devices, 0.0).idxmax()].power_w_kg == devices.power_w_kg.max()


def test_shap_report_is_committed():
    shap = load_shap()
    assert set(shap) == {"specific_energy_wh_kg", "specific_power_w_kg"}
    for entry in shap.values():
        assert abs(sum(i["share"] for i in entry["importance"]) - 1) < 0.01


def test_copilot_parses_and_respects_constraints():
    request = parse_request("High energy above 100 Wh/kg, cobalt-free, African materials, aqueous electrolyte")
    assert request["energy_weight"] == 0.8 and request["min_energy"] == 100 and request["africa"]
    assert request["avoid"] == ["Co"] and request["aqueous"]
    assert parse_request("I need high power density")["energy_weight"] == 0.2
    result = recommend("above 100 Wh/kg cobalt-free", use_llm=False)
    assert result["recommendations"] and result["mode"] == "offline"
    for pick in result["recommendations"]:
        assert pick["energy_wh_kg"] >= 100
    balanced = recommend("balanced energy and power", use_llm=False)
    assert balanced["thesis_pick"]["cathode"] == "PANI@NiCu"
    assert "Graphene // PANI@NiCu" in balanced["answer"]


def test_paper_checked_value_is_flagged():
    from knowledge_engine.facts import build_facts, is_reliable

    fact = next(f for f in build_facts() if f["id"] == "LLZO-0024-ionic_conductivity")
    assert "source_paper_disagrees" in fact["quality_flags"] and not is_reliable(fact)
    assert fact["value_details"]["paper_value"] == 3.53e-4
