import os
import json

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()  # reads variables from a local .env file

_api_key = os.getenv("GEMINI_API_KEY")
_client = genai.Client(api_key=_api_key) if _api_key else None

SYSTEM_PROMPT = (
    "You are a plant biotechnology research assistant embedded in a lab "
    "platform called PlantBio AI. Answer questions about tissue culture, "
    "plant pathology, micropropagation, and related plant science topics "
    "clearly and concisely, in a way useful to students and researchers. "
    "If a question is outside plant science, say so briefly."
)

IMAGE_SYSTEM_PROMPT = (
    "You are a plant biotechnology lab assistant analyzing a photo of a "
    "tissue culture or plant sample. Describe what you observe (color, "
    "growth, any visible browning/contamination/necrosis), give a plausible "
    "assessment of culture health, and suggest what to check next. Be clear "
    "this is a visual estimate, not a lab-confirmed diagnosis, and keep the "
    "answer concise (short paragraphs or a short list)."
)

DIAGNOSIS_SYSTEM_PROMPT = (
    "You are a plant pathology assistant embedded in a lab platform called "
    "PlantBio AI. The user will describe symptoms they're observing on a "
    "plant, along with any matching entries found in their own disease "
    "database (which may be empty). Using both the described symptoms and "
    "any provided reference entries, suggest the most likely disease(s) or "
    "cause(s), ranked by likelihood, with brief reasoning for each. Use "
    "Markdown formatting (headings, bold, bullet points) for readability. "
    "Always end with a clear note that this is an AI estimate, not a "
    "lab-confirmed diagnosis, and that visual/lab confirmation is recommended."
)

PLANT_PROFILE_SYSTEM_PROMPT = (
    "You are a plant biology reference assistant. Given a plant name (common "
    "or scientific), return a detailed reference profile as JSON ONLY — no "
    "markdown fences, no extra text before or after. Use exactly these keys: "
    "taxonomy, morphology, anatomy, biochemistry, molecular_biology, "
    "physiology, economic_importance. Each value must be a single string "
    "containing 4-8 concise bullet points in Markdown format (each point on "
    "its own line, starting with \"- \"). Be factually accurate and specific "
    "to this species where possible; if certain about the species intended, "
    "use its correct scientific name in the taxonomy section. If a category "
    "genuinely has little established information for this plant, still "
    "provide what general information applies at genus/family level and "
    "note that it's a general estimate. Return valid JSON only."
)

AUTOFILL_SYSTEM_PROMPT = (
    "You are a plant pathology reference assistant. Given only a disease "
    "name, return factual reference information as JSON ONLY — no markdown "
    "fences, no extra text before or after. Use exactly these keys: "
    "pathogen (scientific name of the causal organism, or null if unknown), "
    "pathogen_type (one of \"Fungus\", \"Bacteria\", \"Virus\", \"Nematode\", "
    "\"Other\", or null), host_species (typical host plants, or null), "
    "symptoms (a concise description of typical symptoms), "
    "management (typical control/management strategies, or null), "
    "notes (any other useful info, or null). Return valid JSON only."
)

# gemini-2.5-flash was retired; Google's API now points to gemini-3.6-flash
MODEL_NAME = "gemini-3.6-flash"


def _ensure_client():
    if _client is None:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to a .env file in the "
            "backend folder before calling this endpoint."
        )


def ask_plant_ai(question: str) -> str:
    """Send a question to Gemini and return the plain-text answer."""
    _ensure_client()

    response = _client.models.generate_content(
        model=MODEL_NAME,
        contents=question,
        config={"system_instruction": SYSTEM_PROMPT},
    )

    return response.text


def analyze_culture_image(image_bytes: bytes, mime_type: str) -> str:
    """Send an uploaded image to Gemini's vision-capable model and return an analysis."""
    _ensure_client()

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    response = _client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            "Analyze this plant tissue culture / sample image.",
            image_part,
        ],
        config={"system_instruction": IMAGE_SYSTEM_PROMPT},
    )

    return response.text


def diagnose_symptoms(symptom_text: str, matched_records: list[dict]) -> str:
    """Ask Gemini to suggest likely diseases given symptoms + any DB matches."""
    _ensure_client()

    if matched_records:
        records_text = "\n\n".join(
            f"- {r['name']} (pathogen: {r.get('pathogen') or 'unknown'}, "
            f"type: {r.get('pathogen_type') or 'unknown'}): "
            f"known symptoms — {r.get('symptoms', '')}. "
            f"Management — {r.get('management') or 'not recorded'}."
            for r in matched_records
        )
        context = f"Matching entries found in the user's own disease database:\n{records_text}"
    else:
        context = "No matching entries were found in the user's disease database."

    prompt = (
        f"Observed symptoms: {symptom_text}\n\n"
        f"{context}\n\n"
        "Suggest the most likely disease(s) or cause(s)."
    )

    response = _client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={"system_instruction": DIAGNOSIS_SYSTEM_PROMPT},
    )

    return response.text


def autofill_disease(name: str) -> dict:
    """Ask Gemini for reference fields about a named disease, returned as a dict."""
    _ensure_client()

    response = _client.models.generate_content(
        model=MODEL_NAME,
        contents=f"Disease name: {name}",
        config={
            "system_instruction": AUTOFILL_SYSTEM_PROMPT,
            "response_mime_type": "application/json",
        },
    )

    raw = response.text.strip()
    # Defensive cleanup in case the model wraps the JSON in a code fence anyway
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"AI did not return valid JSON: {e}")


def generate_plant_profile(name: str) -> dict:
    """Ask Gemini for a structured, categorized reference profile for a plant."""
    _ensure_client()

    response = _client.models.generate_content(
        model=MODEL_NAME,
        contents=f"Plant name: {name}",
        config={
            "system_instruction": PLANT_PROFILE_SYSTEM_PROMPT,
            "response_mime_type": "application/json",
        },
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"AI did not return valid JSON: {e}")