"""CarePath India: a safer, deterministic Gradio healthcare navigation app.

This app is intentionally not a diagnostic system. It gives plain-language next-step
navigation, emergency red-flag escalation, and India-specific care resources while
encouraging users to consult licensed clinicians.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

EMERGENCY_RED_FLAGS = {
    "chest pain": "Chest pain can be urgent, especially with sweating, breathlessness, nausea, or pain spreading to the arm/jaw.",
    "difficulty breathing": "Breathing difficulty needs urgent assessment.",
    "shortness of breath": "Shortness of breath can worsen quickly and needs urgent assessment.",
    "severe bleeding": "Severe or uncontrolled bleeding needs emergency care.",
    "unconscious": "Loss of consciousness is an emergency.",
    "stroke": "Possible stroke symptoms need immediate emergency care.",
    "face drooping": "Face drooping can be a stroke warning sign.",
    "suicidal": "Thoughts of self-harm require immediate support.",
    "poison": "Poisoning or overdose needs urgent care.",
    "seizure": "A first seizure, prolonged seizure, or repeated seizures need urgent care.",
}

SPECIALTY_KEYWORDS = {
    "fever": "General physician / family medicine",
    "cough": "General physician / pulmonology if persistent",
    "diabetes": "Endocrinology or general physician",
    "pregnancy": "Obstetrics and gynecology",
    "child": "Pediatrics",
    "rash": "Dermatology",
    "skin": "Dermatology",
    "heart": "Cardiology",
    "bp": "General physician / cardiology",
    "blood pressure": "General physician / cardiology",
    "mental": "Psychiatry / clinical psychology",
    "anxiety": "Psychiatry / clinical psychology",
    "depression": "Psychiatry / clinical psychology",
    "tooth": "Dentistry",
    "eye": "Ophthalmology",
    "vision": "Ophthalmology",
    "bone": "Orthopedics",
    "joint": "Orthopedics / rheumatology",
    "kidney": "Nephrology / urology",
    "urine": "Urology / general physician",
}

PUBLIC_RESOURCES = [
    "Call 108 or 112 for emergencies in India where available.",
    "For government facilities, ask for the nearest PHC, CHC, district hospital, or medical college hospital.",
    "Ask the clinician or pharmacist about Jan Aushadhi generic alternatives when cost is a concern.",
    "Keep prescriptions, investigation reports, allergies, current medicines, age, pregnancy status, and major conditions ready.",
]


@dataclass(frozen=True)
class CarePlan:
    urgency: str
    summary: str
    next_steps: list[str]
    specialty: str


def _contains_any(text: str, phrases: Iterable[str]) -> list[str]:
    lowered = text.lower()
    return [phrase for phrase in phrases if phrase in lowered]


def build_care_plan(user_message: str, city_or_state: str = "") -> CarePlan:
    """Build a conservative navigation plan from user-described symptoms or needs."""
    message = user_message.strip()
    location = city_or_state.strip()
    red_flags = _contains_any(message, EMERGENCY_RED_FLAGS)

    if not message:
        return CarePlan(
            urgency="Need more information",
            summary="Please describe the symptom, duration, age, and any known conditions or medicines.",
            next_steps=[
                "Share the main concern in one or two sentences.",
                "Mention duration, severity, age, pregnancy status if relevant, and current medicines.",
            ],
            specialty="General physician / family medicine",
        )

    if red_flags:
        reasons = "; ".join(EMERGENCY_RED_FLAGS[item] for item in red_flags[:3])
        return CarePlan(
            urgency="Emergency — seek care now",
            summary=f"I noticed potential emergency warning signs: {reasons}",
            next_steps=[
                "Call 108 or 112, or go to the nearest emergency department immediately.",
                "Do not drive yourself if you may faint, have severe pain, severe bleeding, stroke-like symptoms, or breathing trouble.",
                "Carry ID, current medicines, allergies, and recent reports if available.",
            ],
            specialty="Emergency medicine",
        )

    matched_specialties = [label for key, label in SPECIALTY_KEYWORDS.items() if key in message.lower()]
    specialty = matched_specialties[0] if matched_specialties else "General physician / family medicine"
    location_phrase = f" in {location}" if location else " near you"

    return CarePlan(
        urgency="Non-emergency navigation",
        summary="This looks suitable for planned care unless symptoms are rapidly worsening or severe.",
        next_steps=[
            f"Book a visit with {specialty}{location_phrase}.",
            "If symptoms become severe, sudden, or involve red flags, use emergency services instead of waiting.",
            "Prepare a short timeline of symptoms and bring prescriptions, test reports, allergies, and medicine list.",
            "Ask about lower-cost options, generic medicines, and whether public facilities can provide the needed care.",
        ],
        specialty=specialty,
    )


def respond(message: str, history: list[dict[str, str]] | None, city_or_state: str) -> str:
    """Return a chat response formatted for Gradio ChatInterface."""
    plan = build_care_plan(message, city_or_state)
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(plan.next_steps, start=1))
    resources = "\n".join(f"- {resource}" for resource in PUBLIC_RESOURCES)

    return f"""### {plan.urgency}

{plan.summary}

**Suggested care path:** {plan.specialty}

**Next steps**
{steps}

**India care resources**
{resources}

_Important: I can help with navigation and preparation, but I cannot diagnose, prescribe, or replace a licensed clinician._"""


def create_demo():
    """Create the Gradio UI."""
    import gradio as gr

    with gr.Blocks(theme=gr.themes.Soft(), title="CarePath India") as demo:
        gr.Markdown(
            """
            # 🏥 CarePath India
            A healthcare navigation assistant for India that helps users decide **where to seek care**, what to bring,
            and when to escalate to emergency services. It is not a diagnostic or prescribing tool.
            """
        )
        city_or_state = gr.Textbox(
            label="City or state (optional)",
            placeholder="e.g., Bengaluru, Karnataka",
        )
        gr.ChatInterface(
            fn=respond,
            type="messages",
            additional_inputs=[city_or_state],
            examples=[
                "My father has chest pain and sweating",
                "I have had fever and cough for three days",
                "My child has a rash and itching",
                "I need affordable diabetes medicine options",
            ],
        )
    return demo


if __name__ == "__main__":
    create_demo().launch()
