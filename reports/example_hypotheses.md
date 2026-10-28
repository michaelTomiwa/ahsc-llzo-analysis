# Hypothesis report

**Goal:** Increase LLZO ionic conductivity above 10⁻³ S/cm at room temperature  
**Generator:** offline (graph templates + domain priors)  
**Africa focus:** on

## 1. PEO-LLZTO composite with percolating garnet filler
- **Proposed material:** PEO/LiTFSI with 40-60 wt% LLZTO nanofibres
- **Change:** Raise garnet loading above the percolation threshold in a polymer matrix
- **Expected effect:** Increase ionic conductivity towards the goal
- **Mechanism:** Continuous ceramic/polymer interfaces provide fast Li+ pathways and suppress PEO crystallinity; the composite is processed below 100 °C, avoiding sintering energy costs. (Mechanism from established literature; knowledge-graph facts cited are same-family context, not direct proof.)
- **Evidence (fact ids):** LLZO-0001-ionic_conductivity, LLZO-0041-ionic_conductivity, LLZO-0043-ionic_conductivity, LLZO-0044-ionic_conductivity, 10.1002/inf2.70012-000-ionic_conductivity
- **Max processing temperature:** 80 °C
- **Validation experiment:** Solution-cast films at 0-60 wt% filler; EIS 25-80 °C; DSC crystallinity; success = >1e-4 S/cm at RT.
- **Scores:** final 0.941 | relevance 0.964 | novelty 0.9 | feasibility 1.0 | evidence 0.918 | Africa 0.929
- **Notes:** no matching material-property evidence in the corpus; Africa supply ['C', 'F', 'La', 'Li', 'S', 'Ta', 'Zr']; flags ['Ta: responsible-sourcing due diligence required']

## 2. Aluminium co-doping of Ta-LLZO
- **Proposed material:** Li6.25Al0.15La3Zr1.75Ta0.25O12 (Al,Ta co-doped garnet)
- **Change:** Partial Li-site Al substitution on Ta-stabilised cubic LLZO
- **Expected effect:** Increase ionic conductivity towards the goal
- **Mechanism:** Supervalent dopants stabilise the cubic garnet phase and create Li vacancies that raise Li+ mobility; Al is supplied from Guinean/Ghanaian bauxite and is cheaper than Ta. (Mechanism from established literature; knowledge-graph facts cited are same-family context, not direct proof.)
- **Evidence (fact ids):** LLZO-0002-ionic_conductivity, LLZO-0144-ionic_conductivity, LLZO-0145-ionic_conductivity
- **Max processing temperature:** 1100 °C
- **Validation experiment:** Solid-state synthesis of x=0-0.25 Al series; XRD for cubic phase; EIS at 25 °C on dense pellets (>92% density); success = >5e-4 S/cm with lower Ta content.
- **Scores:** final 0.834 | relevance 1.0 | novelty 0.55 | feasibility 0.875 | evidence 0.777 | Africa 0.881
- **Notes:** very similar fact exists (LLZO-0002-ionic_conductivity); Africa supply ['Al', 'La', 'Li', 'Ta', 'Zr']; flags ['Ta: responsible-sourcing due diligence required']

## 3. Optimise Garnet LLZO built from African-supplied elements
- **Proposed material:** Ceramic SSE: LLZTO pellets (pristine or coated with Li3PO4)
- **Change:** Use Ceramic SSE: LLZTO pellets (pristine or coated with Li3PO4) as the baseline and tune morphology/loading
- **Expected effect:** Family median 0.000423 S/cm (max 0.000584, n=3); 0/3 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.92
- **Mechanism:** Garnet LLZO ranks among the best families for ionic conductivity in the curated literature, and Ceramic SSE: LLZTO pellets (pristine or coated with Li3PO4) uses elements with African supply (La, Li, P, Ta, Zr).
- **Evidence (fact ids):** LLZO-0002-ionic_conductivity, LLZO-0144-ionic_conductivity, LLZO-0145-ionic_conductivity
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.763 | relevance 0.964 | novelty 0.35 | feasibility 0.6 | evidence 0.865 | Africa 0.836
- **Notes:** already reported for Ceramic SSE: LLZTO pellets (pristine or coated with Li3PO4) (1x); Africa supply ['La', 'Li', 'P', 'Ta', 'Zr']; flags ['Ta: responsible-sourcing due diligence required']

## 4. Optimise PVDF-based polymer built from African-supplied elements
- **Proposed material:** PVDF-HFP (with DMF and LATTP)
- **Change:** Use PVDF-HFP (with DMF and LATTP) as the baseline and tune morphology/loading
- **Expected effect:** Family median 0.00051 S/cm (max 0.0019, n=16); 2/16 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.833
- **Mechanism:** PVDF-based polymer ranks among the best families for ionic conductivity in the curated literature, and PVDF-HFP (with DMF and LATTP) uses elements with African supply (C, F, P).
- **Evidence (fact ids):** LLZO-0005-ionic_conductivity, LLZO-0012-ionic_conductivity, LLZO-0014-ionic_conductivity, LLZO-0022-ionic_conductivity, LLZO-0026-ionic_conductivity, LLZO-0035-ionic_conductivity
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.751 | relevance 0.893 | novelty 0.35 | feasibility 0.6 | evidence 0.936 | Africa 0.788
- **Notes:** already reported for PVDF-HFP (with DMF and LATTP) (1x); Africa supply ['C', 'F', 'P']; flags none

## 5. Optimise PMMA polymer built from African-supplied elements
- **Proposed material:** PMMA-based matrices (with PF55, AlCl3)
- **Change:** Use PMMA-based matrices (with PF55, AlCl3) as the baseline and tune morphology/loading
- **Expected effect:** Family median 0.001 S/cm (max 0.0062, n=3); 2/3 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.9
- **Mechanism:** PMMA polymer ranks among the best families for ionic conductivity in the curated literature, and PMMA-based matrices (with PF55, AlCl3) uses elements with African supply (Al, C, Cl, F, P).
- **Evidence (fact ids):** LLZO-0034-ionic_conductivity, LLZO-0048-ionic_conductivity, LLZO-0065-ionic_conductivity
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.744 | relevance 0.893 | novelty 0.35 | feasibility 0.6 | evidence 0.865 | Africa 0.825
- **Notes:** already reported for PMMA-based matrices (with PF55, AlCl3) (1x); Africa supply ['Al', 'C', 'Cl', 'F', 'P']; flags none


---

# Hypothesis report

**Goal:** Improve AHSC cycling stability above 95% retention after 10,000 cycles  
**Generator:** offline (graph templates + domain priors)  
**Africa focus:** on

## 1. N-doped biomass carbon negative electrode
- **Proposed material:** N,S-doped porous carbon from agro-waste // NiCo-LDH
- **Change:** Heteroatom doping of a biomass carbon negative electrode
- **Expected effect:** Increase cycling stability towards the goal
- **Mechanism:** Heteroatom doping improves wettability and adds stable pseudocapacitive sites without the phase changes that degrade metal-oxide electrodes. (Mechanism from established literature; knowledge-graph facts cited are same-family context, not direct proof.)
- **Evidence (fact ids):** AHSC-0002-cycling_stability, AHSC-0007-cycling_stability, AHSC-0009-cycling_stability, AHSC-0010-cycling_stability, AHSC-0013-cycling_stability, AHSC-0014-cycling_stability
- **Max processing temperature:** 800 °C
- **Validation experiment:** Pyrolyse urea/thiourea-treated biomass at 700-900 °C; three-electrode CV/GCD; full cell 10,000 cycles; success = >95% retention.
- **Scores:** final 0.843 | relevance 0.861 | novelty 0.3 | feasibility 1.0 | evidence 0.936 | Africa 0.973
- **Notes:** already reported for NiCo-LDH (2x); Africa supply ['C', 'Co', 'Ni', 'S']; flags ['Co: responsible-sourcing due diligence required']

## 2. MnO2 on biomass-derived activated carbon
- **Proposed material:** MnO2 / agro-waste activated carbon composite // activated carbon (aqueous Na2SO4)
- **Change:** Anchor nanostructured MnO2 on hierarchical porous carbon from local biomass
- **Expected effect:** Increase cycling stability towards the goal
- **Mechanism:** The conductive carbon scaffold buffers MnO2 volume change and dissolution, and neutral Na2SO4 electrolyte limits Mn dissolution; Mn (South Africa, Gabon) and biomass carbon are local. (Mechanism from established literature; knowledge-graph facts cited are same-family context, not direct proof.)
- **Evidence (fact ids):** AHSC-0003-cycling_stability, AHSC-0004-cycling_stability, AHSC-0042-cycling_stability, AHSC-0080-cycling_stability, AHSC-0088-cycling_stability, AHSC-0366-cycling_stability
- **Max processing temperature:** 800 °C
- **Validation experiment:** Hydrothermal MnO2 on KOH-activated carbon from e.g. coconut shell; GCD at 5 A/g for 10,000 cycles; success = >95% retention.
- **Scores:** final 0.794 | relevance 0.861 | novelty 0.15 | feasibility 1.0 | evidence 0.79 | Africa 1.0
- **Notes:** already reported for Activated carbon (18x); Africa supply ['C', 'Mn', 'Na', 'S']; flags none

## 3. Measure cycling stability for Other polymer electrolyte
- **Proposed material:** Solid-state gelor polymer electrolyte (e.g.,PVA/ZnSO4)
- **Change:** No change: characterise an under-reported property
- **Expected effect:** First data point for this family-property pair in the corpus
- **Mechanism:** Other polymer electrolyte appears in 3 AHSC records but none report cycling stability, although 71% of AHSC records do. This is a gap in reporting, so the measurement is novel by construction.
- **Evidence (fact ids):** AHSC-0033-specific_capacity, AHSC-0034-specific_capacity, AHSC-0040-specific_capacity
- **Max processing temperature:** unknown °C
- **Validation experiment:** Standard cycling stability measurement (EIS/GCD/CV as appropriate) on 3 replicate cells.
- **Scores:** final 0.749 | relevance 0.917 | novelty 0.65 | feasibility 0.8 | evidence 0.528 | Africa 0.825
- **Notes:** material is in the corpus but not for this property; Africa supply ['S', 'Zn']; flags none

## 4. Optimise Metal phosphide built from African-supplied elements
- **Proposed material:** C-doped Co-Mn-Fe-P
- **Change:** Use C-doped Co-Mn-Fe-P as the baseline and tune morphology/loading
- **Expected effect:** Family median 90.5 % (max 100, n=12); 4/12 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.933
- **Mechanism:** Metal phosphide ranks among the best families for cycling stability in the curated literature, and C-doped Co-Mn-Fe-P uses elements with African supply (Co, Fe, Mn).
- **Evidence (fact ids):** AHSC-0258-cycling_stability, AHSC-0259-cycling_stability, AHSC-0261-cycling_stability, AHSC-0262-cycling_stability, AHSC-0263-cycling_stability, AHSC-0264-cycling_stability
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.748 | relevance 0.861 | novelty 0.35 | feasibility 0.6 | evidence 0.895 | Africa 0.843
- **Notes:** already reported for C-doped Co-Mn-Fe-P (1x); Africa supply ['Co', 'Fe', 'Mn']; flags ['Co: responsible-sourcing due diligence required']

## 5. Optimise Transition-metal oxide built from African-supplied elements
- **Proposed material:** ZnCo2O4 NSs
- **Change:** Use ZnCo2O4 NSs as the baseline and tune morphology/loading
- **Expected effect:** Family median 89.7 % (max 100, n=25); 7/25 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.9
- **Mechanism:** Transition-metal oxide ranks among the best families for cycling stability in the curated literature, and ZnCo2O4 NSs uses elements with African supply (Co, Zn).
- **Evidence (fact ids):** AHSC-0017-cycling_stability, AHSC-0018-cycling_stability, AHSC-0030-cycling_stability, AHSC-0032-cycling_stability, AHSC-0047-cycling_stability, AHSC-0049-cycling_stability
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.728 | relevance 0.861 | novelty 0.35 | feasibility 0.6 | evidence 0.826 | Africa 0.825
- **Notes:** already reported for ZnCo2O4 NSs (1x); Africa supply ['Co', 'Zn']; flags ['Co: responsible-sourcing due diligence required']


---

# Hypothesis report

**Goal:** Reduce LLZO sintering temperature below 1000°C for African manufacturing  
**Generator:** offline (graph templates + domain priors)  
**Africa focus:** on

## 1. Polymer-garnet route that eliminates high-temperature sintering
- **Proposed material:** PVDF-HFP / LLZTO / LiTFSI composite membrane
- **Change:** Replace a dense sintered pellet with a garnet-filled polymer membrane
- **Expected effect:** Decrease sintering temperature towards the goal
- **Mechanism:** Garnet powder is calcined once and then processed in a polymer at <120 °C, avoiding the >1000 °C densification step that is costly on weak grids. (Mechanism from established literature; knowledge-graph facts cited are same-family context, not direct proof.)
- **Evidence (fact ids):** LLZO-0001-ionic_conductivity, LLZO-0041-ionic_conductivity, LLZO-0043-ionic_conductivity, LLZO-0044-ionic_conductivity, 10.1002/inf2.70012-000-ionic_conductivity
- **Max processing temperature:** 120 °C
- **Validation experiment:** Cast membranes with 10-50 wt% LLZTO; EIS; Li|Li symmetric cycling at 0.1 mA/cm2; success = >300 h stable plating with >1e-4 S/cm.
- **Scores:** final 0.884 | relevance 0.917 | novelty 0.9 | feasibility 1.0 | evidence 0.713 | Africa 0.929
- **Notes:** no matching material-property evidence in the corpus; Africa supply ['C', 'F', 'La', 'Li', 'S', 'Ta', 'Zr']; flags ['Ta: responsible-sourcing due diligence required']

## 2. Li3BO3 sintering aid for low-temperature garnet densification
- **Proposed material:** Ta-LLZO + 1-5 wt% Li3BO3 (liquid-phase sintering aid)
- **Change:** Add a low-melting lithium borate grain-boundary phase
- **Expected effect:** Decrease sintering temperature towards the goal
- **Mechanism:** A Li3BO3 liquid phase (melting near 700 °C) promotes densification well below conventional garnet sintering temperatures, cutting furnace energy demand. (Mechanism from established literature; knowledge-graph facts cited are same-family context, not direct proof.)
- **Evidence (fact ids):** LLZO-0002-ionic_conductivity, LLZO-0144-ionic_conductivity, LLZO-0145-ionic_conductivity
- **Max processing temperature:** 950 °C
- **Validation experiment:** Sinter pellets at 850-1000 °C with 0-5 wt% Li3BO3; Archimedes density; EIS; success = >90% density and >2e-4 S/cm at <1000 °C.
- **Scores:** final 0.803 | relevance 1.0 | novelty 0.65 | feasibility 1.0 | evidence 0.528 | Africa 0.846
- **Notes:** material is in the corpus but not for this property; Africa supply ['La', 'Li', 'Ta', 'Zr']; flags ['Ta: responsible-sourcing due diligence required']

## 3. Measure specific capacity for Bio-derived polymer
- **Proposed material:** Pectin with LiClO4
- **Change:** No change: characterise an under-reported property
- **Expected effect:** First data point for this family-property pair in the corpus
- **Mechanism:** Bio-derived polymer appears in 4 LLZO records but none report specific capacity, although 59% of LLZO records do. This is a gap in reporting, so the measurement is novel by construction.
- **Evidence (fact ids):** LLZO-0054-ionic_conductivity, LLZO-0055-ionic_conductivity, LLZO-0057-ionic_conductivity, LLZO-0103-ionic_conductivity
- **Max processing temperature:** unknown °C
- **Validation experiment:** Standard specific capacity measurement (EIS/GCD/CV as appropriate) on 3 replicate cells.
- **Scores:** final 0.729 | relevance 0.461 | novelty 0.65 | feasibility 0.8 | evidence 0.895 | Africa 0.825
- **Notes:** material is in the corpus but not for this property; Africa supply ['C', 'Cl', 'F', 'Li', 'S']; flags none

## 4. Measure potential window for Bio-derived polymer
- **Proposed material:** Pectin with LiClO4
- **Change:** No change: characterise an under-reported property
- **Expected effect:** First data point for this family-property pair in the corpus
- **Mechanism:** Bio-derived polymer appears in 4 LLZO records but none report potential window, although 58% of LLZO records do. This is a gap in reporting, so the measurement is novel by construction.
- **Evidence (fact ids):** LLZO-0054-ionic_conductivity, LLZO-0055-ionic_conductivity, LLZO-0057-ionic_conductivity, LLZO-0103-ionic_conductivity
- **Max processing temperature:** unknown °C
- **Validation experiment:** Standard potential window measurement (EIS/GCD/CV as appropriate) on 3 replicate cells.
- **Scores:** final 0.729 | relevance 0.461 | novelty 0.65 | feasibility 0.8 | evidence 0.895 | Africa 0.825
- **Notes:** material is in the corpus but not for this property; Africa supply ['C', 'Cl', 'F', 'Li', 'S']; flags none


---

# Hypothesis report

**Goal:** Raise AHSC specific energy above 60 Wh/kg using Africa-sourced electrode materials  
**Generator:** offline (graph templates + domain priors)  
**Africa focus:** on

## 1. Widen the aqueous voltage window with a water-in-salt electrolyte
- **Proposed material:** MnO2 // Fe2O3 asymmetric cell in concentrated NaClO4 or KOAc
- **Change:** Pair Mn and Fe oxide electrodes with a high-concentration aqueous electrolyte
- **Expected effect:** Increase specific energy towards the goal
- **Mechanism:** Energy scales with V^2; suppressing water activity widens the stable window beyond 2 V while keeping cheap, non-flammable aqueous chemistry built from abundant Mn and Fe. (Mechanism from established literature; knowledge-graph facts cited are same-family context, not direct proof.)
- **Evidence (fact ids):** AHSC-0003-specific_energy, AHSC-0004-specific_energy, AHSC-0143-specific_energy, AHSC-0144-specific_energy, AHSC-0145-specific_energy, AHSC-0146-specific_energy
- **Max processing temperature:** 200 °C
- **Validation experiment:** Floating test at 2.0-2.4 V; GCD energy/power; success = >60 Wh/kg (active mass) with >90% retention after 5,000 cycles.
- **Scores:** final 0.825 | relevance 0.85 | novelty 0.35 | feasibility 1.0 | evidence 0.826 | Africa 0.982
- **Notes:** already reported for MnO2 (1x); Africa supply ['C', 'Cl', 'Fe', 'K', 'Mn', 'Na']; flags none

## 2. Measure specific energy for Metal phosphide
- **Proposed material:** Ni12P5
- **Change:** No change: characterise an under-reported property
- **Expected effect:** First data point for this family-property pair in the corpus
- **Mechanism:** Metal phosphide appears in 12 AHSC records but none report specific energy, although 20% of AHSC records do. This is a gap in reporting, so the measurement is novel by construction.
- **Evidence (fact ids):** AHSC-0258-specific_capacitance, AHSC-0258-cycling_stability, AHSC-0259-specific_capacitance, AHSC-0259-cycling_stability, AHSC-0261-specific_capacitance
- **Max processing temperature:** unknown °C
- **Validation experiment:** Standard specific energy measurement (EIS/GCD/CV as appropriate) on 3 replicate cells.
- **Scores:** final 0.811 | relevance 0.9 | novelty 0.65 | feasibility 0.8 | evidence 0.803 | Africa 0.843
- **Notes:** material is in the corpus but not for this property; Africa supply ['Co', 'Ni', 'P']; flags ['Co: responsible-sourcing due diligence required']

## 3. Measure specific energy for Conducting polymer
- **Proposed material:** CoVO- PANI@CC
- **Change:** No change: characterise an under-reported property
- **Expected effect:** First data point for this family-property pair in the corpus
- **Mechanism:** Conducting polymer appears in 12 AHSC records but none report specific energy, although 20% of AHSC records do. This is a gap in reporting, so the measurement is novel by construction.
- **Evidence (fact ids):** AHSC-0005-potential_window, AHSC-0005-specific_capacitance, AHSC-0005-cycling_stability, AHSC-0090-specific_capacitance, AHSC-0090-cycling_stability
- **Max processing temperature:** unknown °C
- **Validation experiment:** Standard specific energy measurement (EIS/GCD/CV as appropriate) on 3 replicate cells.
- **Scores:** final 0.795 | relevance 0.9 | novelty 0.65 | feasibility 0.8 | evidence 0.731 | Africa 0.843
- **Notes:** material is in the corpus but not for this property; Africa supply ['C', 'Co', 'V']; flags ['Co: responsible-sourcing due diligence required']

## 4. Optimise MXene built from African-supplied elements
- **Proposed material:** CoFe2O4/Cr2CTx
- **Change:** Use CoFe2O4/Cr2CTx as the baseline and tune morphology/loading
- **Expected effect:** Family median 75.6 Wh/kg (max 125, n=3); 2/6 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.95
- **Mechanism:** MXene ranks among the best families for specific energy in the curated literature, and CoFe2O4/Cr2CTx uses elements with African supply (C, Co, Cr, Fe).
- **Evidence (fact ids):** AHSC-0011-specific_energy, AHSC-0048-specific_energy, AHSC-0119-specific_energy, AHSC-0132-specific_energy, AHSC-0133-specific_energy, AHSC-0139-specific_energy
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.741 | relevance 0.9 | novelty 0.35 | feasibility 0.6 | evidence 0.815 | Africa 0.852
- **Notes:** already reported for CoFe2O4/Cr2CTx (1x); Africa supply ['C', 'Co', 'Cr', 'Fe']; flags ['Co: responsible-sourcing due diligence required']

## 5. Optimise Transition-metal oxide built from African-supplied elements
- **Proposed material:** Na2Fe2(SO4)3
- **Change:** Use Na2Fe2(SO4)3 as the baseline and tune morphology/loading
- **Expected effect:** Family median 44.1 Wh/kg (max 240, n=12); 3/12 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.933
- **Mechanism:** Transition-metal oxide ranks among the best families for specific energy in the curated literature, and Na2Fe2(SO4)3 uses elements with African supply (Fe, Na, S).
- **Evidence (fact ids):** AHSC-0047-specific_energy, AHSC-0049-specific_energy, AHSC-0051-specific_energy, AHSC-0052-specific_energy, AHSC-0058-specific_energy, AHSC-0059-specific_energy
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.734 | relevance 0.9 | novelty 0.35 | feasibility 0.6 | evidence 0.79 | Africa 0.843
- **Notes:** already reported for Na2Fe2(SO4)3 (1x); Africa supply ['Fe', 'Na', 'S']; flags none
