# AHSC vs LLZO analysis

Python implementation of the supplied R workflow for comparing AHSC and LLZO battery datasets.

## What it produces

- descriptive statistics by dataset;
- two-sided Mann–Whitney U tests (the Python equivalent of R's unpaired `wilcox.test`);
- boxplots and overlaid histograms for the four comparison variables;
- an AHSC random-forest regression model for specific power. Predictors that are too sparse
  among rows with a specific-power value are excluded and recorded in the run manifest.

## Run

```powershell
python -m pip install -r requirements.txt
python ahsc_llzo_analysis.py
```

Outputs are created in `results/` and `plots/`. The input files may retain their current names, `ahsc_cleaned (1).csv` and `llzo_cleaned (1).csv`.

## Reproducibility

The model uses a fixed random seed (`123`). Input fields are parsed as numeric where applicable and malformed/missing values are excluded only for the calculation requiring them.

## Interactive software prototype

The Streamlit app adds live AHSC specific-power prediction, literature chat, and an African critical-minerals explorer.

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

The chat works immediately in transparent local-retrieval mode. To enable LangChain/OpenAI synthesis, copy `.env.example` to `.env` and add your `OPENAI_API_KEY`; never commit `.env`.
