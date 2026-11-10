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

## 3. Optimise Ni/Co oxide-hydroxide built from African-supplied elements
- **Proposed material:** electrode material (Co3O4@Mn-Ni(OH)2/CC)
- **Change:** Use electrode material (Co3O4@Mn-Ni(OH)2/CC) as the baseline and tune morphology/loading
- **Expected effect:** Family median 39.2 Wh/kg (max 65.5, n=8); 2/8 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.933
- **Mechanism:** Ni/Co oxide-hydroxide ranks among the best families for specific energy in the curated literature, and electrode material (Co3O4@Mn-Ni(OH)2/CC) uses elements with African supply (Co, Mn, Ni).
- **Evidence (fact ids):** AHSC-0008-specific_energy, AHSC-0043-specific_energy, AHSC-0044-specific_energy, AHSC-0045-specific_energy, AHSC-0046-specific_energy, AHSC-0050-specific_energy
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.758 | relevance 0.95 | novelty 0.35 | feasibility 0.6 | evidence 0.847 | Africa 0.843
- **Notes:** already reported for electrode material (Co3O4@Mn-Ni(OH)2/CC) (1x); Africa supply ['Co', 'Mn', 'Ni']; flags ['Co: responsible-sourcing due diligence required']

## 4. Optimise Manganese oxide built from African-supplied elements
- **Proposed material:** C@Mn3O4( +)
- **Change:** Use C@Mn3O4( +) as the baseline and tune morphology/loading
- **Expected effect:** Family median 32.8 Wh/kg (max 110, n=20); 5/20 reported values already meet the goal target; aim to exceed the median at Africa supply score 1.0
- **Mechanism:** Manganese oxide ranks among the best families for specific energy in the curated literature, and C@Mn3O4( +) uses elements with African supply (Mn).
- **Evidence (fact ids):** AHSC-0003-specific_energy, AHSC-0004-specific_energy, AHSC-0143-specific_energy, AHSC-0144-specific_energy, AHSC-0145-specific_energy, AHSC-0146-specific_energy
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.74 | relevance 0.9 | novelty 0.35 | feasibility 0.6 | evidence 0.777 | Africa 0.88
- **Notes:** already reported for C@Mn3O4( +) (1x); Africa supply ['Mn']; flags none

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

## 3. Optimise Ni/Co oxide-hydroxide built from African-supplied elements
- **Proposed material:** Mn-Ni-Co-P
- **Change:** Use Mn-Ni-Co-P as the baseline and tune morphology/loading
- **Expected effect:** Family median 83.3 % (max 96, n=14); 1/14 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.933
- **Mechanism:** Ni/Co oxide-hydroxide ranks among the best families for cycling stability in the curated literature, and Mn-Ni-Co-P uses elements with African supply (Co, Mn, Ni).
- **Evidence (fact ids):** AHSC-0008-cycling_stability, AHSC-0043-cycling_stability, AHSC-0044-cycling_stability, AHSC-0050-cycling_stability, AHSC-0057-cycling_stability, AHSC-0063-cycling_stability
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.758 | relevance 0.861 | novelty 0.35 | feasibility 0.6 | evidence 0.936 | Africa 0.843
- **Notes:** already reported for Mn-Ni-Co-P (1x); Africa supply ['Co', 'Mn', 'Ni']; flags ['Co: responsible-sourcing due diligence required']

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

## 5. Optimise Manganese oxide built from African-supplied elements
- **Proposed material:** MnO2@Zn/Ni-MOF
- **Change:** Use MnO2@Zn/Ni-MOF as the baseline and tune morphology/loading
- **Expected effect:** Family median 87.2 % (max 97.3, n=6); 1/6 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.867
- **Mechanism:** Manganese oxide ranks among the best families for cycling stability in the curated literature, and MnO2@Zn/Ni-MOF uses elements with African supply (Mn, Ni, Zn).
- **Evidence (fact ids):** AHSC-0003-cycling_stability, AHSC-0004-cycling_stability, AHSC-0042-cycling_stability, AHSC-0080-cycling_stability, AHSC-0088-cycling_stability, AHSC-0366-cycling_stability
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.734 | relevance 0.861 | novelty 0.35 | feasibility 0.6 | evidence 0.873 | Africa 0.807
- **Notes:** already reported for MnO2@Zn/Ni-MOF (1x); Africa supply ['Mn', 'Ni', 'Zn']; flags none


---

# Hypothesis report

**Goal:** Increase AHSC specific power above 5,000 W/kg without cobalt  
**Generator:** offline (graph templates + domain priors)  
**Africa focus:** on

## 1. Optimise Carbon built from African-supplied elements
- **Proposed material:** P-CNT/rGO
- **Change:** Use P-CNT/rGO as the baseline and tune morphology/loading
- **Expected effect:** Family median 136 W/kg (max 8e+04, n=20); 3/20 reported values already meet the goal target; aim to exceed the median at Africa supply score 1.0
- **Mechanism:** Carbon ranks among the best families for specific power in the curated literature, and P-CNT/rGO uses elements with African supply (C).
- **Evidence (fact ids):** AHSC-0002-specific_power, AHSC-0007-specific_power, AHSC-0009-specific_power, AHSC-0010-specific_power, AHSC-0012-specific_power, AHSC-0013-specific_power
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.734 | relevance 0.875 | novelty 0.35 | feasibility 0.6 | evidence 0.777 | Africa 0.88
- **Notes:** already reported for P-CNT/rGO (1x); Africa supply ['C']; flags none

## 2. Optimise Transition-metal oxide built from African-supplied elements
- **Proposed material:** Cu-Mn-Zn Oxide
- **Change:** Use Cu-Mn-Zn Oxide as the baseline and tune morphology/loading
- **Expected effect:** Family median 801 W/kg (max 9.43e+03, n=5); 1/5 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.933
- **Mechanism:** Transition-metal oxide ranks among the best families for specific power in the curated literature, and Cu-Mn-Zn Oxide uses elements with African supply (Cu, Mn, Zn).
- **Evidence (fact ids):** AHSC-0052-specific_power, AHSC-0060-specific_power, AHSC-0061-specific_power, AHSC-0072-specific_power, AHSC-0075-specific_power
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.722 | relevance 0.875 | novelty 0.35 | feasibility 0.6 | evidence 0.762 | Africa 0.843
- **Notes:** already reported for Cu-Mn-Zn Oxide (1x); Africa supply ['Cu', 'Mn', 'Zn']; flags none

## 3. Optimise MXene built from African-supplied elements
- **Proposed material:** Ti3C2-ZrO2 NC
- **Change:** Use Ti3C2-ZrO2 NC as the baseline and tune morphology/loading
- **Expected effect:** Family median 14 W/kg (max 1.44e+03, n=5); 0/5 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.867
- **Mechanism:** MXene ranks among the best families for specific power in the curated literature, and Ti3C2-ZrO2 NC uses elements with African supply (C, Ti, Zr).
- **Evidence (fact ids):** AHSC-0011-specific_power, AHSC-0121-specific_power, AHSC-0126-specific_power, AHSC-0127-specific_power, AHSC-0131-specific_power
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.706 | relevance 0.875 | novelty 0.35 | feasibility 0.6 | evidence 0.731 | Africa 0.807
- **Notes:** already reported for Ti3C2-ZrO2 NC (1x); Africa supply ['C', 'Ti', 'Zr']; flags none

## 4. Optimise Manganese oxide built from African-supplied elements
- **Proposed material:** ZnxMnO2/Ppy (ZMOP)
- **Change:** Use ZnxMnO2/Ppy (ZMOP) as the baseline and tune morphology/loading
- **Expected effect:** Family median 834 W/kg (max 867, n=4); 0/4 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.933
- **Mechanism:** Manganese oxide ranks among the best families for specific power in the curated literature, and ZnxMnO2/Ppy (ZMOP) uses elements with African supply (C, Mn, Zn).
- **Evidence (fact ids):** AHSC-0003-specific_power, AHSC-0004-specific_power, 10.1016/j.electacta.2020.137169-001-specific_power, 10.1002/bte2.20240035-002-specific_power
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.699 | relevance 0.875 | novelty 0.3 | feasibility 0.6 | evidence 0.695 | Africa 0.843
- **Notes:** already reported for ZnxMnO2/Ppy (ZMOP) (2x); Africa supply ['C', 'Mn', 'Zn']; flags none

## 5. Optimise Metal sulfide built from African-supplied elements
- **Proposed material:** Ni3S2/ Ni2O3@N-CAN
- **Change:** Use Ni3S2/ Ni2O3@N-CAN as the baseline and tune morphology/loading
- **Expected effect:** Family median 700 W/kg (max 700, n=1); 0/1 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.9
- **Mechanism:** Metal sulfide ranks among the best families for specific power in the curated literature, and Ni3S2/ Ni2O3@N-CAN uses elements with African supply (Ni, S).
- **Evidence (fact ids):** AHSC-0001-specific_power
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.606 | relevance 0.875 | novelty 0.35 | feasibility 0.6 | evidence 0.268 | Africa 0.825
- **Notes:** already reported for Ni3S2/ Ni2O3@N-CAN (1x); Africa supply ['Ni', 'S']; flags none


---

# Hypothesis report

**Goal:** Increase the specific capacitance of manganese-based AHSC electrodes for off-grid solar storage  
**Generator:** offline (graph templates + domain priors)  
**Africa focus:** on

## 1. Optimise Manganese oxide (manganese) built from African-supplied elements
- **Proposed material:** MnO2@Zn/Ni-MOF
- **Change:** Use MnO2@Zn/Ni-MOF as the baseline and tune morphology/loading
- **Expected effect:** Family median 109 F/g (max 1.54e+03, n=15); aim to exceed the median at Africa supply score 0.867
- **Mechanism:** Manganese oxide ranks among the best families for specific capacitance in the curated literature among manganese materials, and MnO2@Zn/Ni-MOF uses elements with African supply (Mn, Ni, Zn).
- **Evidence (fact ids):** AHSC-0003-specific_capacitance, AHSC-0004-specific_capacitance, AHSC-0080-specific_capacitance, AHSC-0088-specific_capacitance, AHSC-0143-specific_capacitance, AHSC-0145-specific_capacitance
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.753 | relevance 0.942 | novelty 0.35 | feasibility 0.6 | evidence 0.873 | Africa 0.807
- **Notes:** already reported for MnO2@Zn/Ni-MOF (1x); Africa supply ['Mn', 'Ni', 'Zn']; flags none

## 2. Optimise Layered double hydroxide (manganese) built from African-supplied elements
- **Proposed material:** ZnCo2O4@NiMn-LDH (2:1)
- **Change:** Use ZnCo2O4@NiMn-LDH (2:1) as the baseline and tune morphology/loading
- **Expected effect:** Family median 484 F/g (max 639, n=2); aim to exceed the median at Africa supply score 0.9
- **Mechanism:** Layered double hydroxide ranks among the best families for specific capacitance in the curated literature among manganese materials, and ZnCo2O4@NiMn-LDH (2:1) uses elements with African supply (Co, Mn, Ni, Zn).
- **Evidence (fact ids):** AHSC-0155-specific_capacitance, AHSC-0175-specific_capacitance
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.747 | relevance 0.942 | novelty 0.35 | feasibility 0.6 | evidence 0.826 | Africa 0.825
- **Notes:** already reported for ZnCo2O4@NiMn-LDH (2:1) (1x); Africa supply ['Co', 'Mn', 'Ni', 'Zn']; flags ['Co: responsible-sourcing due diligence required']

## 3. Optimise Ni/Co oxide-hydroxide (manganese) built from African-supplied elements
- **Proposed material:** Mn-Ni-Co-P
- **Change:** Use Mn-Ni-Co-P as the baseline and tune morphology/loading
- **Expected effect:** Family median 177 F/g (max 177, n=1); aim to exceed the median at Africa supply score 0.933
- **Mechanism:** Ni/Co oxide-hydroxide ranks among the best families for specific capacitance in the curated literature among manganese materials, and Mn-Ni-Co-P uses elements with African supply (Co, Mn, Ni).
- **Evidence (fact ids):** AHSC-0274-specific_capacitance
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.74 | relevance 0.942 | novelty 0.35 | feasibility 0.6 | evidence 0.777 | Africa 0.843
- **Notes:** already reported for Mn-Ni-Co-P (1x); Africa supply ['Co', 'Mn', 'Ni']; flags ['Co: responsible-sourcing due diligence required']

## 4. Optimise MXene (manganese) built from African-supplied elements
- **Proposed material:** MnFe2O4/MXene
- **Change:** Use MnFe2O4/MXene as the baseline and tune morphology/loading
- **Expected effect:** Family median 390 F/g (max 1.26e+03, n=3); aim to exceed the median at Africa supply score 0.9
- **Mechanism:** MXene ranks among the best families for specific capacitance in the curated literature among manganese materials, and MnFe2O4/MXene uses elements with African supply (C, Fe, Mn, Ti).
- **Evidence (fact ids):** AHSC-0239-specific_capacitance, AHSC-0240-specific_capacitance, AHSC-0290-specific_capacitance
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.732 | relevance 0.942 | novelty 0.35 | feasibility 0.6 | evidence 0.762 | Africa 0.825
- **Notes:** already reported for MnFe2O4/MXene (1x); Africa supply ['C', 'Fe', 'Mn', 'Ti']; flags none

## 5. Optimise Transition-metal oxide (manganese) built from African-supplied elements
- **Proposed material:** Mn-Co Oxide
- **Change:** Use Mn-Co Oxide as the baseline and tune morphology/loading
- **Expected effect:** Family median 4.48 F/g (max 4.48, n=1); aim to exceed the median at Africa supply score 1.0
- **Mechanism:** Transition-metal oxide ranks among the best families for specific capacitance in the curated literature among manganese materials, and Mn-Co Oxide uses elements with African supply (Co, Mn).
- **Evidence (fact ids):** AHSC-0087-specific_capacitance
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.663 | relevance 0.942 | novelty 0.35 | feasibility 0.6 | evidence 0.393 | Africa 0.88
- **Notes:** already reported for Mn-Co Oxide (1x); Africa supply ['Co', 'Mn']; flags ['Co: responsible-sourcing due diligence required']


---

# Hypothesis report

**Goal:** Improve both the specific capacitance and cycling stability of AHSC electrodes  
**Generator:** offline (graph templates + domain priors)  
**Africa focus:** on

## 1. N-doped biomass carbon negative electrode
- **Proposed material:** N,S-doped porous carbon from agro-waste // NiCo-LDH
- **Change:** Heteroatom doping of a biomass carbon negative electrode
- **Expected effect:** Increase cycling stability towards the goal
- **Mechanism:** Heteroatom doping improves wettability and adds stable pseudocapacitive sites without the phase changes that degrade metal-oxide electrodes. (Mechanism from established literature; knowledge-graph facts cited are same-family context, not direct proof.)
- **Evidence (fact ids):** AHSC-0002-specific_capacitance, AHSC-0002-cycling_stability, AHSC-0007-specific_capacitance, AHSC-0007-cycling_stability, AHSC-0009-specific_capacitance, AHSC-0009-cycling_stability
- **Max processing temperature:** 800 °C
- **Validation experiment:** Pyrolyse urea/thiourea-treated biomass at 700-900 °C; three-electrode CV/GCD; full cell 10,000 cycles; success = >95% retention.
- **Scores:** final 0.829 | relevance 0.8 | novelty 0.3 | feasibility 1.0 | evidence 0.936 | Africa 0.973
- **Notes:** already reported for NiCo-LDH (2x); Africa supply ['C', 'Co', 'Ni', 'S']; flags ['Co: responsible-sourcing due diligence required']

## 2. MXene/LDH heterostructure using local Ti and Ni
- **Proposed material:** Ti3C2Tx MXene / NiFe-LDH heterostructure
- **Change:** Grow LDH nanosheets on conductive MXene to prevent restacking
- **Expected effect:** Increase specific capacitance towards the goal
- **Mechanism:** MXene supplies electronic conductivity and the LDH supplies faradaic capacity; electrostatic self-assembly prevents restacking of both. Ti (mineral sands) and Ni/Fe have African supply. (Mechanism from established literature; knowledge-graph facts cited are same-family context, not direct proof.)
- **Evidence (fact ids):** AHSC-0011-specific_capacitance, AHSC-0011-cycling_stability, AHSC-0048-cycling_stability, AHSC-0119-specific_capacitance, AHSC-0119-cycling_stability, AHSC-0120-specific_capacitance
- **Max processing temperature:** 150 °C
- **Validation experiment:** Co-precipitate LDH on delaminated MXene; CV/GCD 1-20 A/g; success = >1500 F/g at 1 A/g.
- **Scores:** final 0.815 | relevance 0.8 | novelty 0.3 | feasibility 1.0 | evidence 0.936 | Africa 0.918
- **Notes:** already reported for Ti3C2Tx MXene (2x); Africa supply ['C', 'Fe', 'Ni', 'Ti']; flags none

## 3. Optimise Metal phosphide for both specific capacitance and cycling stability
- **Proposed material:** CoP
- **Change:** Start from CoP; tune loading and morphology while tracking both properties
- **Expected effect:** specific capacitance median 448 F/g (n=5); cycling stability median 90.5 % (n=12); 5 records report both properties
- **Mechanism:** Metal phosphide ranks in the top part of the corpus on both specific capacitance and cycling stability, so it is a candidate for improving both without a trade-off.
- **Evidence (fact ids):** AHSC-0259-specific_capacitance, AHSC-0261-specific_capacitance, AHSC-0262-specific_capacitance, AHSC-0267-specific_capacitance, AHSC-0258-cycling_stability, AHSC-0259-cycling_stability, AHSC-0261-cycling_stability, AHSC-0262-cycling_stability
- **Max processing temperature:** unknown °C
- **Validation experiment:** Make 3 cells of CoP; measure specific capacitance by GCD at 1 A/g and cycling retention over 10,000 cycles on the same cells.
- **Scores:** final 0.814 | relevance 1.0 | novelty 0.3 | feasibility 0.8 | evidence 0.907 | Africa 0.88
- **Notes:** already reported for CoP (2x); Africa supply ['Co', 'P']; flags ['Co: responsible-sourcing due diligence required']

## 4. Optimise MXene for both specific capacitance and cycling stability
- **Proposed material:** Transparent Ti3C2 MXene film
- **Change:** Start from Transparent Ti3C2 MXene film; tune loading and morphology while tracking both properties
- **Expected effect:** specific capacitance median 473 F/g (n=70); cycling stability median 90 % (n=95); 58 records report both properties
- **Mechanism:** MXene ranks in the top part of the corpus on both specific capacitance and cycling stability, so it is a candidate for improving both without a trade-off.
- **Evidence (fact ids):** AHSC-0123-specific_capacitance, AHSC-0167-specific_capacitance, AHSC-0183-specific_capacitance, AHSC-0194-specific_capacitance, AHSC-0011-cycling_stability, AHSC-0048-cycling_stability, AHSC-0119-cycling_stability, AHSC-0121-cycling_stability
- **Max processing temperature:** unknown °C
- **Validation experiment:** Make 3 cells of Transparent Ti3C2 MXene film; measure specific capacitance by GCD at 1 A/g and cycling retention over 10,000 cycles on the same cells.
- **Scores:** final 0.798 | relevance 1.0 | novelty 0.35 | feasibility 0.8 | evidence 0.865 | Africa 0.825
- **Notes:** already reported for Transparent Ti3C2 MXene film (1x); Africa supply ['C', 'Ti']; flags none

## 5. MnO2 on biomass-derived activated carbon
- **Proposed material:** MnO2 / agro-waste activated carbon composite // activated carbon (aqueous Na2SO4)
- **Change:** Anchor nanostructured MnO2 on hierarchical porous carbon from local biomass
- **Expected effect:** Increase cycling stability towards the goal
- **Mechanism:** The conductive carbon scaffold buffers MnO2 volume change and dissolution, and neutral Na2SO4 electrolyte limits Mn dissolution; Mn (South Africa, Gabon) and biomass carbon are local. (Mechanism from established literature; knowledge-graph facts cited are same-family context, not direct proof.)
- **Evidence (fact ids):** AHSC-0003-specific_capacitance, AHSC-0003-cycling_stability, AHSC-0004-specific_capacitance, AHSC-0004-cycling_stability, AHSC-0042-cycling_stability, AHSC-0080-specific_capacitance
- **Max processing temperature:** 800 °C
- **Validation experiment:** Hydrothermal MnO2 on KOH-activated carbon from e.g. coconut shell; GCD at 5 A/g for 10,000 cycles; success = >95% retention.
- **Scores:** final 0.769 | relevance 0.75 | novelty 0.15 | feasibility 1.0 | evidence 0.79 | Africa 1.0
- **Notes:** already reported for Activated carbon (18x); Africa supply ['C', 'Mn', 'Na', 'S']; flags none
