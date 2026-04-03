"""
LangGraph Diagnostic Agent for MediConnect-AI

Five-node graph:
  SymptomParser → TriageEngine → SpecialistMatcher → HospitalRouter → ResponseGenerator → END
                                  ↑                    ↑
                 (if urgency ≥ 8) └── skip ────────────┘

All data files are loaded once at module level.
"""

import json
import math
import logging
import os
from pathlib import Path
from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level data loading (executed once on import)
# ---------------------------------------------------------------------------
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def _load_json(filename: str) -> Any:
    """Load a JSON file from the data directory."""
    filepath = _DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as fh:
        return json.load(fh)

_SYMPTOMS_DB: List[Dict] = _load_json("symptoms.json")["symptoms"]
_SPECIALTIES_DB: List[Dict] = _load_json("specialties.json")["specialties"]
_HOSPITALS_DB: List[Dict] = _load_json("hospitals.json")["hospitals"]

# Pre-build keyword → symptom lookup for O(1) matching
_KEYWORD_INDEX: Dict[str, Dict] = {}
for _symp in _SYMPTOMS_DB:
    for _kw in _symp.get("keywords", []):
        _KEYWORD_INDEX[_kw.lower()] = _symp

logger.info(
    "Diagnostic agent data loaded: %d symptoms, %d specialties, %d hospitals, %d keywords",
    len(_SYMPTOMS_DB),
    len(_SPECIALTIES_DB),
    len(_HOSPITALS_DB),
    len(_KEYWORD_INDEX),
)

# ---------------------------------------------------------------------------
# TypedDict State
# ---------------------------------------------------------------------------

class DiagnosticState(TypedDict):
    raw_input: str
    language: str
    symptoms_extracted: List[str]
    urgency_score: int
    urgency_level: str          # HIGH | MEDIUM | LOW
    matched_specialists: List[str]
    nearest_hospitals: List[Dict]
    final_response: str
    user_lat: float
    user_lon: float


# ---------------------------------------------------------------------------
# Haversine helper
# ---------------------------------------------------------------------------
_EARTH_RADIUS_KM = 6371.0

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two lat/lon points."""
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Node 1 — SymptomParser
# ---------------------------------------------------------------------------

def symptom_parser(state: DiagnosticState) -> Dict[str, Any]:
    """Extract symptom keywords from raw user text and normalise to
    canonical symptom names from symptoms.json."""
    raw = state["raw_input"].lower().strip()
    matched_names: List[str] = []
    seen_ids: set = set()

    # Longest-keyword-first matching to avoid substring collisions
    sorted_keywords = sorted(_KEYWORD_INDEX.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword in raw:
            symp = _KEYWORD_INDEX[keyword]
            sid = symp["id"]
            if sid not in seen_ids:
                matched_names.append(symp["name"])
                seen_ids.add(sid)

    # Fallback: if nothing matched, keep raw text as-is
    if not matched_names:
        matched_names = [raw[:80]]
        logger.info("SymptomParser: no keyword match, using raw input")

    logger.info("SymptomParser: extracted %s", matched_names)
    return {"symptoms_extracted": matched_names}


# ---------------------------------------------------------------------------
# Node 2 — TriageEngine
# ---------------------------------------------------------------------------

def triage_engine(state: DiagnosticState) -> Dict[str, Any]:
    """Score urgency 1-10 using rule-based rules from symptoms.json.
    Picks the **highest** urgency_score among matched symptoms."""
    max_score = 1
    for name in state["symptoms_extracted"]:
        for symp in _SYMPTOMS_DB:
            if symp["name"].lower() == name.lower():
                score = symp.get("urgency_score", 1)
                if score > max_score:
                    max_score = score
                break

    if max_score >= 8:
        level = "HIGH"
    elif max_score >= 5:
        level = "MEDIUM"
    else:
        level = "LOW"

    logger.info("TriageEngine: score=%d  level=%s", max_score, level)
    return {"urgency_score": max_score, "urgency_level": level}


# ---------------------------------------------------------------------------
# Node 3 — SpecialistMatcher
# ---------------------------------------------------------------------------

def specialist_matcher(state: DiagnosticState) -> Dict[str, Any]:
    """Map extracted symptoms to medical specialties from specialties.json.
    Uses the symptom-level ``specialties`` list first, then falls back to
    the specialties.json cross-reference."""
    specialists: List[str] = []
    seen: set = set()

    # Primary: direct from symptoms.json
    for name in state["symptoms_extracted"]:
        for symp in _SYMPTOMS_DB:
            if symp["name"].lower() == name.lower():
                for spec in symp.get("specialties", []):
                    if spec not in seen:
                        specialists.append(spec)
                        seen.add(spec)
                break

    # Secondary: from specialties.json symptoms list
    if not specialists:
        for spec_entry in _SPECIALTIES_DB:
            spec_symptoms_lower = [s.lower() for s in spec_entry.get("symptoms", [])]
            for name in state["symptoms_extracted"]:
                if name.lower() in spec_symptoms_lower and spec_entry["name"] not in seen:
                    specialists.append(spec_entry["name"])
                    seen.add(spec_entry["name"])

    if not specialists:
        specialists = ["General Medicine"]

    logger.info("SpecialistMatcher: %s", specialists)
    return {"matched_specialists": specialists}


# ---------------------------------------------------------------------------
# Node 4 — HospitalRouter
# ---------------------------------------------------------------------------

def hospital_router(state: DiagnosticState) -> Dict[str, Any]:
    """Find the 5 nearest hospitals from hospitals.json that offer at least
    one of the required specialties, sorted by Haversine distance."""
    user_lat = state.get("user_lat", 12.9716)   # default: Bangalore centre
    user_lon = state.get("user_lon", 77.5946)
    required_specs = set(state.get("matched_specialists", []))

    # For HIGH urgency without specialist match, include Emergency Medicine
    if state.get("urgency_level") == "HIGH":
        required_specs.add("Emergency Medicine")

    candidates: List[Dict] = []
    for hosp in _HOSPITALS_DB:
        hosp_specs = set(hosp.get("specialties", []))
        if hosp_specs & required_specs:
            loc = hosp.get("location", {})
            dist = _haversine(user_lat, user_lon, loc.get("lat", 0), loc.get("lng", 0))
            candidates.append({
                "id": hosp["id"],
                "name": hosp["name"],
                "address": hosp.get("address", ""),
                "phone": hosp.get("phone", ""),
                "emergency_phone": hosp.get("emergency_phone", ""),
                "distance_km": round(dist, 2),
                "specialties_matched": sorted(hosp_specs & required_specs),
                "emergency_available": hosp.get("emergency_available", False),
                "rating": hosp.get("rating", 0),
            })

    candidates.sort(key=lambda h: h["distance_km"])
    top5 = candidates[:5]
    logger.info("HospitalRouter: found %d candidates, returning top %d", len(candidates), len(top5))
    return {"nearest_hospitals": top5}


# ---------------------------------------------------------------------------
# Node 5 — ResponseGenerator (uses Groq LLaMA via groq_provider)
# ---------------------------------------------------------------------------

def response_generator(state: DiagnosticState) -> Dict[str, Any]:
    """Compose final patient-facing response.
    Tries Groq LLaMA first; falls back to a deterministic template."""

    hospitals_summary = "\n".join(
        f"  {i+1}. {h['name']} — {h['distance_km']} km — ☎ {h.get('emergency_phone', h.get('phone', 'N/A'))}"
        for i, h in enumerate(state.get("nearest_hospitals", []))
    )

    prompt = (
        f"Patient symptoms: {', '.join(state['symptoms_extracted'])}\n"
        f"Urgency: {state['urgency_level']} (score {state['urgency_score']}/10)\n"
        f"Recommended specialists: {', '.join(state.get('matched_specialists', ['General Medicine']))}\n"
        f"Nearest hospitals:\n{hospitals_summary}\n\n"
        "Give a short, reassuring response to the patient. "
        "Include urgency guidance and recommend the nearest hospital. "
        "If urgency is HIGH, tell them to call 108 immediately."
    )

    try:
        from utils.groq_provider import get_health_response
        result = get_health_response(prompt, state.get("language", "en"))
        final = result.get("response", "")
        if final:
            logger.info("ResponseGenerator: used Groq LLaMA")
            return {"final_response": final}
    except Exception as exc:
        logger.error("ResponseGenerator: Groq call failed: %s", exc)

    # Deterministic fallback
    if state["urgency_level"] == "HIGH":
        advice = (
            f"🚨 **URGENT — Call 108 immediately!**\n\n"
            f"Your symptoms ({', '.join(state['symptoms_extracted'])}) indicate a "
            f"**{state['urgency_level']}** urgency situation (score {state['urgency_score']}/10).\n\n"
            f"**Recommended specialist(s):** {', '.join(state.get('matched_specialists', []))}\n\n"
            f"**Nearest hospitals:**\n{hospitals_summary}\n\n"
            f"⚠️ Do not delay — seek emergency care now."
        )
    else:
        advice = (
            f"Based on your symptoms ({', '.join(state['symptoms_extracted'])}), "
            f"this appears to be a **{state['urgency_level']}** priority issue "
            f"(score {state['urgency_score']}/10).\n\n"
            f"**Recommended specialist(s):** {', '.join(state.get('matched_specialists', []))}\n\n"
            f"**Nearest hospitals:**\n{hospitals_summary}\n\n"
            f"Please consult a healthcare professional for proper evaluation."
        )

    logger.info("ResponseGenerator: used deterministic fallback")
    return {"final_response": advice}


# ---------------------------------------------------------------------------
# Conditional edge — skip SpecialistMatcher when urgency ≥ 8
# ---------------------------------------------------------------------------

def _after_triage(state: DiagnosticState) -> str:
    """Return the next node name based on urgency score."""
    if state.get("urgency_score", 0) >= 8:
        # HIGH urgency → skip specialist, go straight to hospital routing
        # We still set a default specialist list so HospitalRouter works
        logger.info("Conditional: urgency %d ≥ 8 → skipping SpecialistMatcher", state["urgency_score"])
        return "hospital_router"
    return "specialist_matcher"


def _prepare_emergency_specialists(state: DiagnosticState) -> Dict[str, Any]:
    """Inject Emergency Medicine as default specialist for HIGH urgency
    bypasses, so HospitalRouter has something to match on."""
    specialists = ["Emergency Medicine"]
    # Also pull specialties from matched symptoms
    for name in state.get("symptoms_extracted", []):
        for symp in _SYMPTOMS_DB:
            if symp["name"].lower() == name.lower():
                for spec in symp.get("specialties", []):
                    if spec not in specialists:
                        specialists.append(spec)
                break
    return {"matched_specialists": specialists}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def _build_graph() -> StateGraph:
    """Build and compile the LangGraph diagnostic agent."""
    graph = StateGraph(DiagnosticState)

    # Add nodes
    graph.add_node("symptom_parser", symptom_parser)
    graph.add_node("triage_engine", triage_engine)
    graph.add_node("specialist_matcher", specialist_matcher)
    graph.add_node("emergency_specialist_inject", _prepare_emergency_specialists)
    graph.add_node("hospital_router", hospital_router)
    graph.add_node("response_generator", response_generator)

    # Entry point
    graph.set_entry_point("symptom_parser")

    # Edges
    graph.add_edge("symptom_parser", "triage_engine")

    # Conditional edge after triage
    graph.add_conditional_edges(
        "triage_engine",
        _after_triage,
        {
            "specialist_matcher": "specialist_matcher",
            "hospital_router": "emergency_specialist_inject",
        },
    )

    # Normal path
    graph.add_edge("specialist_matcher", "hospital_router")

    # Emergency bypass path
    graph.add_edge("emergency_specialist_inject", "hospital_router")

    # Common continuation
    graph.add_edge("hospital_router", "response_generator")
    graph.add_edge("response_generator", END)

    return graph.compile()


# Compile once at module level
diagnostic_agent = _build_graph()


# ---------------------------------------------------------------------------
# Public API — ready to import in Flask routes
# ---------------------------------------------------------------------------

def run_diagnostic(
    raw_input: str,
    language: str = "en",
    user_lat: float = 12.9716,
    user_lon: float = 77.5946,
) -> Dict[str, Any]:
    """Run the full diagnostic pipeline and return the completed state.

    Args:
        raw_input:  Free-text symptom description from the patient.
        language:   ``"en"`` for English, ``"kn"`` for Kannada.
        user_lat:   Patient's latitude  (default: Bangalore centre).
        user_lon:   Patient's longitude (default: Bangalore centre).

    Returns:
        A dict with keys: ``symptoms_extracted``, ``urgency_score``,
        ``urgency_level``, ``matched_specialists``, ``nearest_hospitals``,
        ``final_response``.
    """
    initial_state: DiagnosticState = {
        "raw_input": raw_input,
        "language": language,
        "symptoms_extracted": [],
        "urgency_score": 0,
        "urgency_level": "LOW",
        "matched_specialists": [],
        "nearest_hospitals": [],
        "final_response": "",
        "user_lat": user_lat,
        "user_lon": user_lon,
    }

    result = diagnostic_agent.invoke(initial_state)
    logger.info(
        "Diagnostic complete: urgency=%s score=%d specialists=%s hospitals=%d",
        result.get("urgency_level"),
        result.get("urgency_score", 0),
        result.get("matched_specialists"),
        len(result.get("nearest_hospitals", [])),
    )
    return dict(result)
