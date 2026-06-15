# CarePath India

CarePath India is a Gradio healthcare-navigation app intended for Databricks Apps or local demos. It improves on a generic LLM-generated prototype by making the safest behavior deterministic: emergency red flags are escalated before any general guidance is shown, and all responses frame the tool as navigation rather than diagnosis.

## What was wrong with the generated app

- The deployed URL could not be inspected from this environment because the Databricks app endpoint returned an access/proxy error, so this repo now contains a reproducible local app implementation.
- Healthcare advice is high-risk; a general chatbot should not present itself as a doctor, diagnose, or prescribe.
- The app needs clear emergency escalation for India and clear limits on what it can safely do.
- A Databricks-generated prototype should be separated into deployable app code plus pinned runtime dependencies instead of living only as notebook cells.

## Run locally

```bash
pip install -r DatabricksApps/carepath_india/requirements.txt
python DatabricksApps/carepath_india/app.py
```

## Safety model

The app uses deterministic keyword checks for emergency red flags such as chest pain, difficulty breathing, stroke-like symptoms, severe bleeding, poisoning, seizure, unconsciousness, and self-harm. Non-emergency requests are routed to a likely specialty and include preparation steps and India-specific resources such as 108/112 emergency calling and public-facility options.


## Repository placement

This app lives under `DatabricksApps/carepath_india` so it stays isolated from the general GenAI examples and notebook collection in the repository root.
