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

**Goal:** Increase AHSC specific power above 5,000 W/kg without cobalt  
**Generator:** offline (graph templates + domain priors)  
**Africa focus:** on

## 1. Optimise Ni/Co oxide-hydroxide built from African-supplied elements
- **Proposed material:** Co3O4/Ni
- **Change:** Use Co3O4/Ni as the baseline and tune morphology/loading
- **Expected effect:** Family median 775 W/kg (max 4e+03, n=8); 0/8 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.9
- **Mechanism:** Ni/Co oxide-hydroxide ranks among the best families for specific power in the curated literature, and Co3O4/Ni uses elements with African supply (Co, Ni).
- **Evidence (fact ids):** AHSC-0008-specific_power, AHSC-0043-specific_power, AHSC-0044-specific_power, AHSC-0045-specific_power, AHSC-0046-specific_power, AHSC-0050-specific_power
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.734 | relevance 0.875 | novelty 0.35 | feasibility 0.6 | evidence 0.837 | Africa 0.825
- **Notes:** already reported for Co3O4/Ni (1x); Africa supply ['Co', 'Ni']; flags ['Co: responsible-sourcing due diligence required']

## 2. Optimise Transition-metal oxide built from African-supplied elements
- **Proposed material:** Cu-Mn-Zn Oxide
- **Change:** Use Cu-Mn-Zn Oxide as the baseline and tune morphology/loading
- **Expected effect:** Family median 1.08e+03 W/kg (max 9.43e+03, n=12); 1/12 reported values already meet the goal target; aim to exceed the median at Africa supply score 0.933
- **Mechanism:** Transition-metal oxide ranks among the best families for specific power in the curated literature, and Cu-Mn-Zn Oxide uses elements with African supply (Cu, Mn, Zn).
- **Evidence (fact ids):** AHSC-0047-specific_power, AHSC-0049-specific_power, AHSC-0051-specific_power, AHSC-0052-specific_power, AHSC-0058-specific_power, AHSC-0059-specific_power
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.733 | relevance 0.875 | novelty 0.35 | feasibility 0.6 | evidence 0.815 | Africa 0.843
- **Notes:** already reported for Cu-Mn-Zn Oxide (1x); Africa supply ['Cu', 'Mn', 'Zn']; flags none

## 3. Measure specific energy for Conducting polymer
- **Proposed material:** CoVO- PANI@CC
- **Change:** No change: characterise an under-reported property
- **Expected effect:** First data point for this family-property pair in the corpus
- **Mechanism:** Conducting polymer appears in 12 AHSC records but none report specific energy, although 20% of AHSC records do. This is a gap in reporting, so the measurement is novel by construction.
- **Evidence (fact ids):** AHSC-0005-potential_window, AHSC-0005-specific_capacitance, AHSC-0005-cycling_stability, AHSC-0090-specific_capacitance, AHSC-0090-cycling_stability
- **Max processing temperature:** unknown °C
- **Validation experiment:** Standard specific energy measurement (EIS/GCD/CV as appropriate) on 3 replicate cells.
- **Scores:** final 0.7 | relevance 0.475 | novelty 0.65 | feasibility 0.8 | evidence 0.731 | Africa 0.843
- **Notes:** material is in the corpus but not for this property; Africa supply ['C', 'Co', 'V']; flags ['Co: responsible-sourcing due diligence required']

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

## 5. Measure potential window for Metal phosphide
- **Proposed material:** Ni12P5
- **Change:** No change: characterise an under-reported property
- **Expected effect:** First data point for this family-property pair in the corpus
- **Mechanism:** Metal phosphide appears in 12 AHSC records but none report potential window, although 31% of AHSC records do. This is a gap in reporting, so the measurement is novel by construction.
- **Evidence (fact ids):** AHSC-0258-specific_capacitance, AHSC-0258-cycling_stability, AHSC-0259-specific_capacitance, AHSC-0259-cycling_stability, AHSC-0261-specific_capacitance
- **Max processing temperature:** unknown °C
- **Validation experiment:** Standard potential window measurement (EIS/GCD/CV as appropriate) on 3 replicate cells.
- **Scores:** final 0.685 | relevance 0.412 | novelty 0.65 | feasibility 0.8 | evidence 0.731 | Africa 0.843
- **Notes:** material is in the corpus but not for this property; Africa supply ['Co', 'Ni', 'P']; flags ['Co: responsible-sourcing due diligence required']


---

# Hypothesis report

**Goal:** Increase the specific capacitance of manganese-based AHSC electrodes for off-grid solar storage  
**Generator:** offline (graph templates + domain priors)  
**Africa focus:** on

## 1. MXene/LDH heterostructure using local Ti and Ni
- **Proposed material:** Ti3C2Tx MXene / NiFe-LDH heterostructure
- **Change:** Grow LDH nanosheets on conductive MXene to prevent restacking
- **Expected effect:** Increase specific capacitance towards the goal
- **Mechanism:** MXene supplies electronic conductivity and the LDH supplies faradaic capacity; electrostatic self-assembly prevents restacking of both. Ti (mineral sands) and Ni/Fe have African supply. (Mechanism from established literature; knowledge-graph facts cited are same-family context, not direct proof.)
- **Evidence (fact ids):** AHSC-0011-specific_capacitance, AHSC-0119-specific_capacitance, AHSC-0120-specific_capacitance, AHSC-0121-specific_capacitance, AHSC-0122-specific_capacitance, AHSC-0123-specific_capacitance
- **Max processing temperature:** 150 °C
- **Validation experiment:** Co-precipitate LDH on delaminated MXene; CV/GCD 1-20 A/g; success = >1500 F/g at 1 A/g.
- **Scores:** final 0.839 | relevance 0.904 | novelty 0.3 | feasibility 1.0 | evidence 0.936 | Africa 0.918
- **Notes:** already reported for Ti3C2Tx MXene (2x); Africa supply ['C', 'Fe', 'Ni', 'Ti']; flags none

## 2. Measure specific capacitance for Lithium metal
- **Proposed material:** Lithium foil
- **Change:** No change: characterise an under-reported property
- **Expected effect:** First data point for this family-property pair in the corpus
- **Mechanism:** Lithium metal appears in 4 AHSC records but none report specific capacitance, although 67% of AHSC records do. This is a gap in reporting, so the measurement is novel by construction.
- **Evidence (fact ids):** AHSC-0019-specific_capacity, AHSC-0020-specific_capacity, AHSC-0020-cycling_stability, AHSC-0022-specific_capacity, AHSC-0023-specific_capacity
- **Max processing temperature:** unknown °C
- **Validation experiment:** Standard specific capacitance measurement (EIS/GCD/CV as appropriate) on 3 replicate cells.
- **Scores:** final 0.81 | relevance 0.942 | novelty 0.65 | feasibility 0.8 | evidence 0.713 | Africa 0.88
- **Notes:** material is in the corpus but not for this property; Africa supply ['Li']; flags none

## 3. Optimise MXene built from African-supplied elements
- **Proposed material:** MXene/NiCo2S4
- **Change:** Use MXene/NiCo2S4 as the baseline and tune morphology/loading
- **Expected effect:** Family median 473 F/g (max 2.68e+03, n=70); aim to exceed the median at Africa supply score 0.92
- **Mechanism:** MXene ranks among the best families for specific capacitance in the curated literature, and MXene/NiCo2S4 uses elements with African supply (C, Co, Ni, S, Ti).
- **Evidence (fact ids):** AHSC-0011-specific_capacitance, AHSC-0119-specific_capacitance, AHSC-0120-specific_capacitance, AHSC-0121-specific_capacitance, AHSC-0122-specific_capacitance, AHSC-0123-specific_capacitance
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.765 | relevance 0.904 | novelty 0.35 | feasibility 0.6 | evidence 0.936 | Africa 0.836
- **Notes:** already reported for MXene/NiCo2S4 (1x); Africa supply ['C', 'Co', 'Ni', 'S', 'Ti']; flags ['Co: responsible-sourcing due diligence required']

## 4. Measure specific capacitance for Other polymer electrolyte
- **Proposed material:** Solid-state gelor polymer electrolyte (e.g.,PVA/ZnSO4)
- **Change:** No change: characterise an under-reported property
- **Expected effect:** First data point for this family-property pair in the corpus
- **Mechanism:** Other polymer electrolyte appears in 3 AHSC records but none report specific capacitance, although 67% of AHSC records do. This is a gap in reporting, so the measurement is novel by construction.
- **Evidence (fact ids):** AHSC-0033-specific_capacity, AHSC-0034-specific_capacity, AHSC-0040-specific_capacity
- **Max processing temperature:** unknown °C
- **Validation experiment:** Standard specific capacitance measurement (EIS/GCD/CV as appropriate) on 3 replicate cells.
- **Scores:** final 0.754 | relevance 0.942 | novelty 0.65 | feasibility 0.8 | evidence 0.528 | Africa 0.825
- **Notes:** material is in the corpus but not for this property; Africa supply ['S', 'Zn']; flags none

## 5. Optimise Layered double hydroxide built from African-supplied elements
- **Proposed material:** NiAl LDH
- **Change:** Use NiAl LDH as the baseline and tune morphology/loading
- **Expected effect:** Family median 646 F/g (max 2.59e+03, n=44); aim to exceed the median at Africa supply score 0.9
- **Mechanism:** Layered double hydroxide ranks among the best families for specific capacitance in the curated literature, and NiAl LDH uses elements with African supply (Al, Ni).
- **Evidence (fact ids):** AHSC-0129-specific_capacitance, AHSC-0155-specific_capacitance, AHSC-0156-specific_capacitance, AHSC-0158-specific_capacitance, AHSC-0159-specific_capacitance, AHSC-0160-specific_capacitance
- **Max processing temperature:** unknown °C
- **Validation experiment:** Reproduce the best cited record, then vary one parameter (loading, dopant level or annealing temperature) in a 3-level design; report the target property with error bars from 3 cells.
- **Scores:** final 0.74 | relevance 0.904 | novelty 0.35 | feasibility 0.6 | evidence 0.837 | Africa 0.825
- **Notes:** already reported for NiAl LDH (1x); Africa supply ['Al', 'Ni']; flags none
