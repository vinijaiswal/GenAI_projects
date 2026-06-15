"""Actionbook: healthcare access planner for the Databricks workspace dataset.

This Streamlit demo reads cleaned healthcare specialty and health-indicator CSVs from
Unity Catalog Volume files, then turns them into an interactive action plan for
non-diagnostic healthcare planning. It is designed for Databricks Apps, but includes
sample-data fallbacks so the UI can be smoke-tested locally.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

CATALOG = "workspace"
SCHEMA = "virtue_foundation_project"
VOLUME = "cleaned_data"
VOLUME_ROOT = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
HEALTH_INDICATORS_CSV = f"{VOLUME_ROOT}/health_indicators.csv"
SPECIALTIES_CSV = f"{VOLUME_ROOT}/op_100_specialties.csv"

EMERGENCY_TERMS = {
    "chest pain",
    "difficulty breathing",
    "shortness of breath",
    "stroke",
    "severe bleeding",
    "unconscious",
    "seizure",
    "suicidal",
    "poison",
}

SAMPLE_INDICATORS = pd.DataFrame(
    [
        {"location": "Bihar", "indicator": "Diabetes", "value": 8.4, "unit": "% adults", "need": "endocrinology follow-up"},
        {"location": "Karnataka", "indicator": "Hypertension", "value": 23.6, "unit": "% adults", "need": "cardiology and primary care"},
        {"location": "Maharashtra", "indicator": "Maternal health", "value": 71.2, "unit": "coverage score", "need": "obstetrics and gynecology"},
        {"location": "Tamil Nadu", "indicator": "Child nutrition", "value": 68.5, "unit": "coverage score", "need": "pediatrics and nutrition"},
    ]
)

SAMPLE_SPECIALTIES = pd.DataFrame(
    [
        {"specialty": "General Medicine", "potential_healthcare_need": "Primary triage, chronic disease review", "priority": "High"},
        {"specialty": "Cardiology", "potential_healthcare_need": "Hypertension and cardiac risk management", "priority": "High"},
        {"specialty": "Endocrinology", "potential_healthcare_need": "Diabetes screening and medication review", "priority": "Medium"},
        {"specialty": "Obstetrics and Gynecology", "potential_healthcare_need": "Pregnancy, maternal health, reproductive care", "priority": "High"},
        {"specialty": "Pediatrics", "potential_healthcare_need": "Child health and nutrition", "priority": "High"},
    ]
)


@dataclass(frozen=True)
class ActionPlan:
    urgency: str
    specialty: str
    rationale: str
    next_steps: list[str]


def _find_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    normalized = {column.lower().strip().replace(" ", "_"): column for column in columns}
    for candidate in candidates:
        key = candidate.lower().strip().replace(" ", "_")
        if key in normalized:
            return normalized[key]
    return None


@st.cache_data(show_spinner=False)
def load_csv(path: str, fallback: pd.DataFrame) -> pd.DataFrame:
    """Load a CSV from a Databricks Volume path, falling back for local previews."""
    if Path(path).exists():
        return pd.read_csv(path)
    return fallback.copy()


def normalize_specialties(df: pd.DataFrame) -> pd.DataFrame:
    specialty_col = _find_column(df.columns, ["specialty", "speciality", "provider_specialty", "name"])
    need_col = _find_column(df.columns, ["potential_healthcare_need", "healthcare_need", "need", "description"])
    priority_col = _find_column(df.columns, ["priority", "rank", "score", "volume", "count"])

    normalized = pd.DataFrame()
    normalized["specialty"] = df[specialty_col].astype(str) if specialty_col else df.iloc[:, 0].astype(str)
    normalized["potential_healthcare_need"] = (
        df[need_col].astype(str) if need_col else "Specialty care capacity planning"
    )
    normalized["priority"] = df[priority_col].astype(str) if priority_col else "Review"
    return normalized.dropna(subset=["specialty"]).drop_duplicates().head(100)


def normalize_indicators(df: pd.DataFrame) -> pd.DataFrame:
    location_col = _find_column(df.columns, ["location", "state", "district", "region"])
    indicator_col = _find_column(df.columns, ["indicator", "measure", "metric", "health_indicator"])
    value_col = _find_column(df.columns, ["value", "rate", "prevalence", "score", "percent"])
    unit_col = _find_column(df.columns, ["unit", "units"])
    need_col = _find_column(df.columns, ["need", "potential_healthcare_need", "healthcare_need"])

    normalized = pd.DataFrame()
    normalized["location"] = df[location_col].astype(str) if location_col else "All locations"
    normalized["indicator"] = df[indicator_col].astype(str) if indicator_col else df.iloc[:, 0].astype(str)
    normalized["value"] = pd.to_numeric(df[value_col], errors="coerce") if value_col else pd.NA
    normalized["unit"] = df[unit_col].astype(str) if unit_col else ""
    normalized["need"] = df[need_col].astype(str) if need_col else normalized["indicator"]
    return normalized.dropna(subset=["indicator"]).head(500)


def infer_specialty(need: str, specialties: pd.DataFrame) -> str:
    text = need.lower()
    keyword_map = {
        "diabetes": "Endocrinology",
        "hypertension": "Cardiology",
        "heart": "Cardiology",
        "pregnan": "Obstetrics and Gynecology",
        "maternal": "Obstetrics and Gynecology",
        "child": "Pediatrics",
        "nutrition": "Pediatrics",
        "skin": "Dermatology",
        "mental": "Psychiatry",
    }
    for keyword, specialty in keyword_map.items():
        if keyword in text and specialties["specialty"].str.contains(specialty, case=False, na=False).any():
            return specialty
    return specialties.iloc[0]["specialty"] if not specialties.empty else "General Medicine"


def build_action_plan(concern: str, location: str, specialties: pd.DataFrame) -> ActionPlan:
    text = concern.lower()
    if any(term in text for term in EMERGENCY_TERMS):
        return ActionPlan(
            urgency="Emergency — seek care now",
            specialty="Emergency Medicine",
            rationale="Your description includes possible red-flag symptoms that should not wait for routine planning.",
            next_steps=[
                "Call local emergency services or go to the nearest emergency department now.",
                "Bring medicines, allergies, recent reports, and an ID if available.",
                "Use this app later for follow-up and specialty-capacity planning, not for urgent triage.",
            ],
        )

    specialty = infer_specialty(concern, specialties)
    location_phrase = f" for {location}" if location else " for the selected community"
    return ActionPlan(
        urgency="Planned-care action",
        specialty=specialty,
        rationale=f"The cleaned specialty list and selected health need suggest {specialty}{location_phrase}.",
        next_steps=[
            f"Review the top related indicators and confirm whether {specialty} capacity matches local demand.",
            "Create outreach: screening camp, referral slots, pharmacy/generic options, and follow-up reminders.",
            "Track owner, deadline, and metric in the action board below.",
        ],
    )


def app() -> None:
    st.set_page_config(page_title="Actionbook: Healthcare Needs", page_icon="🩺", layout="wide")
    st.title("🩺 Actionbook: Healthcare Needs Command Center")
    st.caption("Databricks Apps demo using Unity Catalog Volume CSVs from workspace.virtue_foundation_project.cleaned_data")

    raw_indicators = load_csv(HEALTH_INDICATORS_CSV, SAMPLE_INDICATORS)
    raw_specialties = load_csv(SPECIALTIES_CSV, SAMPLE_SPECIALTIES)
    indicators = normalize_indicators(raw_indicators)
    specialties = normalize_specialties(raw_specialties)

    with st.sidebar:
        st.header("Data source")
        st.code(HEALTH_INDICATORS_CSV)
        st.code(SPECIALTIES_CSV)
        st.metric("Indicators", f"{len(indicators):,}")
        st.metric("Specialties", f"{len(specialties):,}")

    locations = ["All locations"] + sorted(indicators["location"].dropna().astype(str).unique().tolist())
    selected_location = st.selectbox("Focus geography", locations)
    focus = indicators if selected_location == "All locations" else indicators[indicators["location"] == selected_location]

    c1, c2, c3 = st.columns(3)
    c1.metric("Rows in focus", f"{len(focus):,}")
    c2.metric("Unique indicators", f"{focus['indicator'].nunique():,}")
    c3.metric("Top specialties", f"{specialties['specialty'].nunique():,}")

    left, right = st.columns([1.1, 0.9])
    with left:
        st.subheader("Health indicators")
        st.dataframe(focus.sort_values("value", ascending=False, na_position="last"), use_container_width=True)
    with right:
        st.subheader("Specialty action map")
        st.dataframe(specialties, use_container_width=True)

    st.subheader("Generate an action plan")
    default_need = focus.iloc[0]["need"] if not focus.empty else "diabetes screening"
    concern = st.text_area("Describe the community need or patient-navigation question", value=str(default_need))
    plan = build_action_plan(concern, selected_location, specialties)

    st.info(f"**{plan.urgency}** · Suggested specialty: **{plan.specialty}**")
    st.write(plan.rationale)
    for step in plan.next_steps:
        st.checkbox(step, value=False)

    st.subheader("30-day action board")
    action_board = pd.DataFrame(
        [
            {"Action": "Validate demand hotspot", "Owner": "Analytics", "Metric": "Indicator rows reviewed", "Status": "Ready"},
            {"Action": f"Reserve {plan.specialty} referral slots", "Owner": "Operations", "Metric": "Slots opened", "Status": "Planned"},
            {"Action": "Launch community outreach", "Owner": "Care team", "Metric": "People reached", "Status": "Planned"},
        ]
    )
    st.data_editor(action_board, use_container_width=True, num_rows="dynamic")
    st.warning("This demo supports planning and navigation only. It does not diagnose, prescribe, or replace licensed clinical care.")


if __name__ == "__main__":
    app()
