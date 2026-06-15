# Actionbook: Healthcare Needs Command Center

A Streamlit Databricks Apps demo that turns cleaned healthcare CSV files into an interactive **Actionbook** for community health planning, specialty-capacity review, and safe patient-navigation next steps.

## Dataset

The app expects the cleaned files in this Unity Catalog Volume:

- `/Volumes/workspace/virtue_foundation_project/cleaned_data/health_indicators.csv`
- `/Volumes/workspace/virtue_foundation_project/cleaned_data/op_100_specialties.csv`

The code includes a small sample fallback so contributors can smoke-test the UI locally without Databricks Volume mounts.

## Run locally

```bash
pip install -r DatabricksApps/actionbook_healthcare/requirements.txt
streamlit run DatabricksApps/actionbook_healthcare/app.py
```

## Deploy as a Databricks App

Create a Databricks App from this directory and use the command:

```bash
streamlit run app.py --server.port 8000 --server.address 0.0.0.0
```

## What the demo does

- Loads cleaned health indicators and top specialty/need mappings from the `cleaned_data` Volume.
- Normalizes common column-name variations so the app remains resilient if the CSV schema changes slightly.
- Lets users focus on a geography, review indicators, and map healthcare needs to relevant specialties.
- Generates a conservative action plan and 30-day editable action board.
- Escalates obvious emergency red flags and clearly states that the demo is not a diagnostic tool.
