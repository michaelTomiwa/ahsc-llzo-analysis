"""Phase 4.1: goal-driven hypothesis generation over the knowledge graph.

Adapted from goal-driven scientific hypothesis generation (NAACL 2025 style): a research goal
plus constraints -> retrieve graph context (best families, gaps, dopant effects, African
supply) -> LLM proposes testable hypotheses with evidence fact ids -> hypotheses are scored
and re-ranked (see hypothesis_evaluator).

Offline, a transparent generator builds hypotheses from the same context: (1) transfer the
best-performing Africa-compatible material families, (2) fill knowledge-graph gaps, and
(3) apply well-established mechanisms from a small, labelled domain-prior library whose
support is then counted in the graph.
"""
from __future__ import annotations

import json
import re

from . import llm
from .africa import AFRICAN_CONSTRAINTS, africa_profile, supply_table
from .chem import normalize_text
from .facts import is_reliable
from .graph_rag import Engine, get_engine
from .knowledge_graph import dopant_effects, family_property_stats, gap_analysis

EXAMPLE_GOALS = [
    "Increase LLZO ionic conductivity above 10⁻³ S/cm at room temperature",
    "Improve AHSC cycling stability above 95% retention after 10,000 cycles",
    "Reduce LLZO sintering temperature below 1000°C for African manufacturing",
    "Raise AHSC specific energy above 60 Wh/kg using Africa-sourced electrode materials",
]

HYPOTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "hypotheses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "proposed_material": {"type": "string"},
                    "composition_change": {"type": "string"},
                    "target_property": {"type": "string"},
                    "expected_change": {"type": "string"},
                    "mechanistic_reasoning": {"type": "string"},
                    "supporting_fact_ids": {"type": "array", "items": {"type": "string"}},
                    "elements": {"type": "array", "items": {"type": "string"}},
                    "synthesis_route": {"type": "string"},
                    "estimated_synthesis_temp_c": {"type": "number"},
                    "applications": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number"},
                    "validation_experiment": {"type": "string"},
                },
                "required": ["title", "proposed_material", "composition_change", "target_property", "expected_change",
                             "mechanistic_reasoning", "supporting_fact_ids", "elements", "synthesis_route",
                             "estimated_synthesis_temp_c", "applications", "confidence", "validation_experiment"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["hypotheses"],
    "additionalProperties": False,
}

HYPOTHESIS_PROMPT = """You are a materials scientist. Given the knowledge-graph context and a goal, generate {n} testable hypotheses.

Goal: {goal}
Constraints: {constraints}

Knowledge Graph Context:
{context}

For each hypothesis provide: the proposed material/composition/dopant, the expected property change (quantitative
where the context supports it), mechanistic reasoning, supporting evidence as fact ids that appear in the context
(use [] if the idea rests on general knowledge, and say so in the reasoning), elements involved, a synthesis route
with an estimated maximum processing temperature in °C (use -1 if unknown), target applications, a confidence
score 0-1, and one concrete validation experiment (technique, sample matrix, success threshold).
Prefer earth-abundant, Africa-supplied elements and processing below the temperature limit; avoid {avoid}.
Make the hypotheses diverse (different mechanisms), and do not repeat what the context already shows is reported."""

# Well-established mechanisms (textbook-level, not mined). Each is labelled as a prior; its
# knowledge-graph support is counted separately so the evaluator can tell grounded from prior.
DOMAIN_PRIORS: list[dict] = [
    {"systems": ["LLZO"], "property": "ionic_conductivity", "title": "Aluminium co-doping of Ta-LLZO",
     "proposed_material": "Li6.25Al0.15La3Zr1.75Ta0.25O12 (Al,Ta co-doped garnet)",
     "composition_change": "Partial Li-site Al substitution on Ta-stabilised cubic LLZO",
     "mechanism": "Supervalent dopants stabilise the cubic garnet phase and create Li vacancies that raise Li+ "
                  "mobility; Al is supplied from Guinean/Ghanaian bauxite and is cheaper than Ta.",
     "elements": ["Li", "Al", "La", "Zr", "Ta", "O"], "temp": 1100, "family": "Garnet LLZO",
     "experiment": "Solid-state synthesis of x=0-0.25 Al series; XRD for cubic phase; EIS at 25 °C on dense pellets "
                   "(>92% density); success = >5e-4 S/cm with lower Ta content."},
    {"systems": ["LLZO"], "property": "ionic_conductivity", "title": "PEO-LLZTO composite with percolating garnet filler",
     "proposed_material": "PEO/LiTFSI with 40-60 wt% LLZTO nanofibres",
     "composition_change": "Raise garnet loading above the percolation threshold in a polymer matrix",
     "mechanism": "Continuous ceramic/polymer interfaces provide fast Li+ pathways and suppress PEO crystallinity; "
                  "the composite is processed below 100 °C, avoiding sintering energy costs.",
     "elements": ["Li", "La", "Zr", "Ta", "C", "O", "F", "S", "N"], "temp": 80, "family": "Polymer-garnet composite",
     "experiment": "Solution-cast films at 0-60 wt% filler; EIS 25-80 °C; DSC crystallinity; success = >1e-4 S/cm at RT."},
    {"systems": ["LLZO"], "property": "sintering_temperature", "title": "Li3BO3 sintering aid for low-temperature garnet densification",
     "proposed_material": "Ta-LLZO + 1-5 wt% Li3BO3 (liquid-phase sintering aid)",
     "composition_change": "Add a low-melting lithium borate grain-boundary phase",
     "mechanism": "A Li3BO3 liquid phase (melting near 700 °C) promotes densification well below conventional "
                  "garnet sintering temperatures, cutting furnace energy demand.",
     "elements": ["Li", "B", "La", "Zr", "Ta", "O"], "temp": 950, "family": "Garnet LLZO",
     "experiment": "Sinter pellets at 850-1000 °C with 0-5 wt% Li3BO3; Archimedes density; EIS; success = >90% "
                   "density and >2e-4 S/cm at <1000 °C."},
    {"systems": ["LLZO"], "property": "sintering_temperature", "title": "Polymer-garnet route that eliminates high-temperature sintering",
     "proposed_material": "PVDF-HFP / LLZTO / LiTFSI composite membrane",
     "composition_change": "Replace a dense sintered pellet with a garnet-filled polymer membrane",
     "mechanism": "Garnet powder is calcined once and then processed in a polymer at <120 °C, avoiding the "
                  ">1000 °C densification step that is costly on weak grids.",
     "elements": ["Li", "La", "Zr", "Ta", "C", "F", "O", "S", "N"], "temp": 120, "family": "Polymer-garnet composite",
     "experiment": "Cast membranes with 10-50 wt% LLZTO; EIS; Li|Li symmetric cycling at 0.1 mA/cm2; success = "
                   ">300 h stable plating with >1e-4 S/cm."},
    {"systems": ["AHSC"], "property": "cycling_stability", "title": "MnO2 on biomass-derived activated carbon",
     "proposed_material": "MnO2 / agro-waste activated carbon composite // activated carbon (aqueous Na2SO4)",
     "composition_change": "Anchor nanostructured MnO2 on hierarchical porous carbon from local biomass",
     "mechanism": "The conductive carbon scaffold buffers MnO2 volume change and dissolution, and neutral Na2SO4 "
                  "electrolyte limits Mn dissolution; Mn (South Africa, Gabon) and biomass carbon are local.",
     "elements": ["Mn", "O", "C", "Na", "S"], "temp": 800, "family": "Manganese oxide",
     "experiment": "Hydrothermal MnO2 on KOH-activated carbon from e.g. coconut shell; GCD at 5 A/g for 10,000 "
                   "cycles; success = >95% retention."},
    {"systems": ["AHSC"], "property": "cycling_stability", "title": "N-doped biomass carbon negative electrode",
     "proposed_material": "N,S-doped porous carbon from agro-waste // NiCo-LDH",
     "composition_change": "Heteroatom doping of a biomass carbon negative electrode",
     "mechanism": "Heteroatom doping improves wettability and adds stable pseudocapacitive sites without the "
                  "phase changes that degrade metal-oxide electrodes.",
     "elements": ["C", "N", "S", "Ni", "Co", "O"], "temp": 800, "family": "Carbon",
     "experiment": "Pyrolyse urea/thiourea-treated biomass at 700-900 °C; three-electrode CV/GCD; full cell "
                   "10,000 cycles; success = >95% retention."},
    {"systems": ["AHSC"], "property": "specific_energy", "title": "Widen the aqueous voltage window with a water-in-salt electrolyte",
     "proposed_material": "MnO2 // Fe2O3 asymmetric cell in concentrated NaClO4 or KOAc",
     "composition_change": "Pair Mn and Fe oxide electrodes with a high-concentration aqueous electrolyte",
     "mechanism": "Energy scales with V^2; suppressing water activity widens the stable window beyond 2 V while "
                  "keeping cheap, non-flammable aqueous chemistry built from abundant Mn and Fe.",
     "elements": ["Mn", "Fe", "O", "Na", "Cl", "K", "C"], "temp": 200, "family": "Manganese oxide",
     "experiment": "Floating test at 2.0-2.4 V; GCD energy/power; success = >60 Wh/kg (active mass) with >90% "
                   "retention after 5,000 cycles."},
    {"systems": ["AHSC"], "property": "specific_capacitance", "title": "MXene/LDH heterostructure using local Ti and Ni",
     "proposed_material": "Ti3C2Tx MXene / NiFe-LDH heterostructure",
     "composition_change": "Grow LDH nanosheets on conductive MXene to prevent restacking",
     "mechanism": "MXene supplies electronic conductivity and the LDH supplies faradaic capacity; electrostatic "
                  "self-assembly prevents restacking of both. Ti (mineral sands) and Ni/Fe have African supply.",
     "elements": ["Ti", "C", "Ni", "Fe", "O", "H"], "temp": 150, "family": "MXene",
     "experiment": "Co-precipitate LDH on delaminated MXene; CV/GCD 1-20 A/g; success = >1500 F/g at 1 A/g."},
]

PROPERTY_PATTERNS = {
    "ionic_conductivity": r"conductiv",
    "cycling_stability": r"cycl|retention|stabilit",
    "sintering_temperature": r"sinter|processing temperature|densif",
    "specific_energy": r"energy",
    "specific_power": r"power",
    "specific_capacitance": r"capacitan",
    "specific_capacity": r"capacity",
    "potential_window": r"window|voltage",
}


def parse_goal(goal: str) -> dict:
    """Pull system, target property, numeric target and direction out of a free-text goal."""
    text = normalize_text(goal).replace(",", "")
    lowered = text.lower()
    system = "LLZO" if re.search(r"llzo|garnet|solid.state|electrolyte", lowered) else \
        "AHSC" if re.search(r"ahsc|supercap|capacitor", lowered) else None
    prop = next((p for p, pattern in PROPERTY_PATTERNS.items() if re.search(pattern, lowered)), None)
    target = None
    scientific = re.search(r"(?:(\d+(?:\.\d+)?)\s*[x×*]\s*)?10\s*\^?\s*(-\d+)", text)
    if scientific:
        target = float(scientific.group(1) or 1.0) * 10.0 ** int(scientific.group(2))
    else:
        number = re.search(r"(\d+(?:\.\d+)?)\s*(%|°c|s/cm|wh/kg|w/kg|f/g|mah/g|v\b)", lowered)
        target = float(number.group(1)) if number else None
    direction = "decrease" if re.search(r"reduce|lower|below|decrease|minimi", lowered) else "increase"
    return {"system": system, "property": prop, "target": target, "direction": direction}


def build_context(goal_info: dict, engine: Engine, africa_focus: bool = True, max_facts: int = 25) -> tuple[str, list[str]]:
    """Text context for the LLM plus the list of fact ids it may cite."""
    system, prop = goal_info["system"], goal_info["property"]
    lines, cited = [], []
    stats_prop = prop if prop not in (None, "sintering_temperature") else ("ionic_conductivity" if system == "LLZO" else None)
    if stats_prop:
        stats = family_property_stats(engine.facts, stats_prop, system)
        lines.append(f"## {stats_prop} by material family ({system or 'all systems'})")
        lines += [f"- {r.material_family}: median {r.median:.4g} {r.unit}, max {r.max:.4g}, n={r.count}"
                  for r in stats.head(10).itertuples()]
        pool = [f for f in engine.facts if f["property"] == stats_prop and is_reliable(f)
                and (system is None or f["system"] == system)]
        unit = max({f["unit"] for f in pool}, key=lambda u: sum(f["unit"] == u for f in pool)) if pool else ""
        pool = [f for f in pool if f["unit"] == unit]
        if africa_focus:
            top = max((f["value"] for f in pool), default=1.0) or 1.0
            pool.sort(key=lambda f: -(f["africa"]["score"] or 0) * 0.3 - f["value"] / top)
        else:
            pool.sort(key=lambda f: -f["value"])
        lines.append("## Top reported facts" + (" (Africa-supply weighted)" if africa_focus else ""))
        for fact in pool[:max_facts]:
            cited.append(fact["id"])
            lines.append(f"- [{fact['id']}] {fact['material']} ({fact['material_family']}): {fact['value']:.4g} "
                         f"{fact['unit']} {fact.get('condition') or ''}; elements {','.join(fact['elements'])}; "
                         f"Africa score {fact['africa']['score']}; evidence \"{fact['evidence_span']}\"")
    if system == "LLZO":
        table = dopant_effects(engine.facts)
        if not table.empty:
            lines.append("## Dopant effects (LLZO)")
            lines += [f"- {r.dopant}: {r.property} median {r.median:.4g} {r.unit} (n={r.count})" for r in table.itertuples()]
    gaps = gap_analysis(engine.facts)
    if not gaps.empty:
        sub = gaps[gaps.system == system] if system else gaps
        lines.append("## Knowledge gaps (family x property never reported)")
        lines += [f"- {r.entity} lacks {r.missing_property} ({r.entity_records} records, Africa {r.africa_score})"
                  for r in sub.head(8).itertuples()]
    if africa_focus:
        table = supply_table()
        lines.append("## African element supply (qualitative)")
        lines += [f"- {r.element}: {r.status} ({r.african_countries})" for r in table.itertuples()
                  if r.status != "ubiquitous"]
    return "\n".join(lines), cited


def _offline_hypotheses(goal: str, goal_info: dict, engine: Engine, n: int) -> list[dict]:
    system, prop = goal_info["system"], goal_info["property"]
    hypotheses = []
    # (1) Domain priors that match the goal.
    for prior in DOMAIN_PRIORS:
        if (system is None or system in prior["systems"]) and (prop is None or prior["property"] == prop):
            support = [f["id"] for f in engine.facts if f["material_family"] == prior["family"] and is_reliable(f)
                       and f["property"] == (prop if prop != "sintering_temperature" else "ionic_conductivity")][:6]
            hypotheses.append({
                "title": prior["title"], "proposed_material": prior["proposed_material"],
                "composition_change": prior["composition_change"], "target_property": prior["property"],
                "expected_change": f"{goal_info['direction'].capitalize()} {prior['property'].replace('_', ' ')} towards the goal",
                "mechanistic_reasoning": prior["mechanism"] + " (Mechanism from established literature; knowledge-"
                                         "graph facts cited are same-family context, not direct proof.)",
                "supporting_fact_ids": support, "elements": prior["elements"],
                "synthesis_route": "see validation experiment", "estimated_synthesis_temp_c": prior["temp"],
                "applications": AFRICAN_CONSTRAINTS["applications"][:2], "confidence": 0.55,
                "validation_experiment": prior["experiment"], "origin": "domain prior"})
    # (2) Transfer the best Africa-compatible family for the target property.
    stats_prop = prop if prop not in (None, "sintering_temperature") else None
    if stats_prop:
        stats = family_property_stats(engine.facts, stats_prop, system)
        for row in stats.head(6).itertuples():
            members = [f for f in engine.facts if f["material_family"] == row.material_family and f["property"] == stats_prop
                       and is_reliable(f) and (system is None or f["system"] == system)]
            if not members or row.material_family in ("Other", "Unspecified", "Liquid electrolyte"):
                continue
            compatible = [f for f in members if (f["africa"]["score"] or 0) >= 0.6] or members
            compatible.sort(key=lambda f: -f["value"])
            lead = compatible[0]
            beat = sum(f["value"] >= goal_info["target"] for f in members) if goal_info["target"] else None
            profile = africa_profile(lead["elements"])
            if profile["score"] is not None and profile["score"] < 0.6:
                continue
            hypotheses.append({
                "title": f"Optimise {row.material_family} built from African-supplied elements",
                "proposed_material": lead["material"],
                "composition_change": f"Use {lead['material']} as the baseline and tune morphology/loading",
                "target_property": stats_prop,
                "expected_change": f"Family median {row.median:.3g} {row.unit} (max {row.max:.3g}, n={row.count})"
                                   + (f"; {beat}/{len(members)} reported values already meet the goal target"
                                      if beat is not None else "")
                                   + f"; aim to exceed the median at Africa supply score {profile['score']}",
                "mechanistic_reasoning": f"{row.material_family} ranks among the best families for {stats_prop.replace('_', ' ')} "
                                         f"in the curated literature, and {lead['material']} uses elements with African "
                                         f"supply ({', '.join(profile['african_supply']) or 'n/a'}).",
                "supporting_fact_ids": [m["id"] for m in members[:6]], "elements": lead["elements"],
                "synthesis_route": "follow the cited record's route; replace precursors with locally sourced equivalents",
                "estimated_synthesis_temp_c": -1, "applications": AFRICAN_CONSTRAINTS["applications"][:3],
                "confidence": round(min(0.85, 0.4 + 0.05 * len(members)), 2),
                "validation_experiment": "Reproduce the best cited record, then vary one parameter (loading, dopant level "
                                         "or annealing temperature) in a 3-level design; report the target property with "
                                         "error bars from 3 cells.", "origin": "graph: best family"})
    # (3) Fill a knowledge-graph gap.
    gaps = gap_analysis(engine.facts)
    if not gaps.empty:
        sub = gaps[(gaps.system == system) if system else gaps.system.notna()]
        if stats_prop:
            sub = sub[sub.missing_property == stats_prop] if (sub.missing_property == stats_prop).any() else sub
        for gap in sub.head(2).itertuples():
            members = [f for f in engine.facts if f["material_family"] == gap.entity and f["system"] == gap.system]
            hypotheses.append({
                "title": f"Measure {gap.missing_property.replace('_', ' ')} for {gap.entity}",
                "proposed_material": members[0]["material"] if members else gap.entity,
                "composition_change": "No change: characterise an under-reported property",
                "target_property": gap.missing_property,
                "expected_change": "First data point for this family-property pair in the corpus",
                "mechanistic_reasoning": f"{gap.entity} appears in {gap.entity_records} {gap.system} records but none "
                                         f"report {gap.missing_property.replace('_', ' ')}, although "
                                         f"{gap.property_share_in_system:.0%} of {gap.system} records do. This is a "
                                         f"gap in reporting, so the measurement is novel by construction.",
                "supporting_fact_ids": [m["id"] for m in members[:5]],
                "elements": sorted({e for m in members[:5] for e in m["elements"]}),
                "synthesis_route": "re-make the cited material", "estimated_synthesis_temp_c": -1,
                "applications": AFRICAN_CONSTRAINTS["applications"][:2], "confidence": 0.5,
                "validation_experiment": f"Standard {gap.missing_property.replace('_', ' ')} measurement (EIS/GCD/CV as "
                                         f"appropriate) on 3 replicate cells.", "origin": "graph: gap"})
    return hypotheses[: max(n, 1) + 3]


def generate_hypotheses(goal: str, constraints: dict | None = None, n: int = 5, africa_focus: bool = True,
                        engine: Engine | None = None) -> dict:
    """Generate, score and rank hypotheses for a research goal."""
    from .hypothesis_evaluator import rank_hypotheses

    engine = engine or get_engine()
    constraints = {**AFRICAN_CONSTRAINTS, **(constraints or {})} if africa_focus else (constraints or {})
    goal_info = parse_goal(goal)
    context, citable = build_context(goal_info, engine, africa_focus)
    mode, hypotheses = "offline (graph templates + domain priors)", []
    if llm.available():
        result = llm.complete(HYPOTHESIS_PROMPT.format(n=n, goal=goal, constraints=json.dumps(constraints),
                                                       context=context,
                                                       avoid=", ".join(constraints.get("avoid", []))),
                              schema=HYPOTHESIS_SCHEMA, effort="high")
        if result.data and result.data.get("hypotheses"):
            mode = result.mode
            hypotheses = [{**h, "origin": "llm"} for h in result.data["hypotheses"]]
        else:
            mode = f"offline fallback ({result.mode})"
    if not hypotheses:
        hypotheses = _offline_hypotheses(goal, goal_info, engine, n)
    for h in hypotheses:
        if h.get("estimated_synthesis_temp_c") is not None and h["estimated_synthesis_temp_c"] < 0:
            h["estimated_synthesis_temp_c"] = None
    ranked = rank_hypotheses(hypotheses, goal, goal_info, engine, constraints, africa_focus)
    return {"goal": goal, "goal_parsed": goal_info, "constraints": constraints, "africa_focus": africa_focus,
            "mode": mode, "hypotheses": ranked[:n], "context": context}


if __name__ == "__main__":
    import sys

    report = generate_hypotheses(" ".join(sys.argv[1:]) or EXAMPLE_GOALS[0])
    print(report["mode"])
    for h in report["hypotheses"]:
        print(f"{h['rank']}. [{h['scores']['final']:.2f}] {h['title']} -- {h['proposed_material']}")
