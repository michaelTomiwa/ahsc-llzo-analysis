# Seed literature and mineral knowledge base

## Dataset scope
The project compares AHSC and LLZO battery records. Its locally supplied CSVs contain performance fields including potential midpoint, capacitance/capacity, specific energy, specific power, cycling stability, and ionic conductivity. Missingness is substantial for some fields, particularly AHSC ionic conductivity. Any predictive result must be interpreted as exploratory because the available training subset is small.

## AHSC and LLZO analysis method
The Python workflow combines the supplied AHSC and LLZO files, computes descriptive summaries, uses two-sided Mann–Whitney U tests for independent group comparisons, and generates boxplots and histograms. The random-forest regression predicts AHSC specific power only from predictors that are sufficiently observed among rows with a specific-power value. This is a pragmatic missing-data safeguard, not causal evidence.

## Democratic Republic of the Congo
USGS reports that the Democratic Republic of the Congo was the world's leading cobalt producer in 2024, with estimated mine production of 226,000 metric tons of cobalt content. The USGS country profile also discusses the Manono lithium and tin project; project activity is not the same thing as national production and legal or project status can change.
Source: USGS, Congo (Kinshasa) country profile, https://www.usgs.gov/centers/national-minerals-information-center/congo-kinshasa

## Zimbabwe
USGS reports Zimbabwe as a major lithium producer. Its 2024 country table lists estimated lithium ore production of one million metric tons, mostly spodumene including petalite and lepidolite, and lists cobalt mine production of 344 metric tons of cobalt content. Production data should be read together with grade, processing, environmental, community, transport, and governance constraints.
Source: USGS, Zimbabwe country profile, https://www.usgs.gov/centers/national-minerals-information-center/zimbabwe

## Mozambique and graphite
The USGS Mozambique country profile refers to graphite asset activity. This prototype treats Mozambique's graphite record as a qualitative country/project signal rather than a quantified national production claim. A user should add validated project data before comparing it directly with national mine-production figures.
Source: USGS, Mozambique country profile, https://www.usgs.gov/centers/national-minerals-information-center/mozambique

## Responsible use
This prototype is for research exploration. It does not provide investment, procurement, or technical-design advice. Verify source recency, project status, unit definitions, and data provenance before making decisions.
