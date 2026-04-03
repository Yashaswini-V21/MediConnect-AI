"""
Groq AI Provider for HealthBridge AI
Uses Groq's llama3-8b-8192 model for health guidance.
Falls back to local RuleBasedProvider when API is unavailable.
"""

import os
import time
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MODEL = "llama3-8b-8192"
_MAX_RETRIES = 2
_RETRY_DELAY_SECONDS = 1

_SYSTEM_PROMPT = (
    "You are a medical triage assistant for Indian patients. "
    "Give concise, clear health guidance. Always recommend calling 108 for emergencies. "
    "Never replace professional medical advice.\n\n"
    "Respond ONLY with valid JSON in this exact format:\n"
    '{"response": "<your advice>", "urgency": "HIGH|MEDIUM|LOW", "specialist": "<recommended specialist>"}\n'
    "Do not include any text outside the JSON object."
)


def _get_client():
    """Lazily import and build the Groq client so the module can load
    even when the ``groq`` package is not installed (offline fallback)."""
    try:
        from groq import Groq  # noqa: WPS433 – intentional lazy import
    except ImportError:
        logger.error("groq package is not installed – run: pip install groq")
        return None

    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY environment variable is not set")
        return None

    return Groq(api_key=api_key)


def _parse_groq_response(raw_text: str) -> Dict[str, str]:
    """Parse the JSON response from Groq, with defensive handling."""
    try:
        parsed = json.loads(raw_text.strip())
        return {
            "response": str(parsed.get("response", raw_text)),
            "urgency": str(parsed.get("urgency", "MEDIUM")).upper(),
            "specialist": str(parsed.get("specialist", "General Physician")),
        }
    except (json.JSONDecodeError, AttributeError):
        # Model returned free text instead of JSON – wrap it
        return {
            "response": raw_text.strip(),
            "urgency": "MEDIUM",
            "specialist": "General Physician",
        }


def _call_groq(symptom_text: str, language: str) -> Dict[str, str] | None:
    """Call Groq API with retry logic.  Returns ``None`` on failure."""
    client = _get_client()
    if client is None:
        return None

    lang_hint = "Respond in Kannada." if language.lower() in ("kn", "kannada") else ""

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": f"{lang_hint}Patient says: {symptom_text}"},
    ]

    last_error: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 2):  # 1 initial + 2 retries
        try:
            chat_completion = client.chat.completions.create(
                model=_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=512,
            )
            raw = chat_completion.choices[0].message.content
            logger.info("Groq response received (attempt %d)", attempt)
            return _parse_groq_response(raw)

        except Exception as exc:
            last_error = exc
            # Retry only on rate-limit errors
            exc_name = type(exc).__name__
            if "RateLimit" in exc_name and attempt <= _MAX_RETRIES:
                logger.warning(
                    "Groq RateLimitError (attempt %d/%d) – retrying in %ds",
                    attempt,
                    _MAX_RETRIES + 1,
                    _RETRY_DELAY_SECONDS,
                )
                time.sleep(_RETRY_DELAY_SECONDS)
            else:
                break

    # All retries exhausted or non-retryable error
    logger.error("Groq API failed after %d attempt(s): %s", _MAX_RETRIES + 1, last_error)
    return None


def _fallback_response(symptom_text: str) -> Dict[str, str]:
    """Generate a response using the local RuleBasedProvider."""
    from utils.ai_provider import RuleBasedProvider  # noqa: WPS433

    provider = RuleBasedProvider()
    result = provider.analyze_symptoms(symptom_text)

    return {
        "response": result.get("explanation", "Please consult a healthcare professional."),
        "urgency": result.get("urgency", "MEDIUM"),
        "specialist": result.get("specialties", ["General Physician"])[0],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_health_response(symptom_text: str, language: str = "en") -> Dict[str, Any]:
    """Return health guidance for the given symptoms.

    Tries Groq first; falls back to the local rule-based provider on failure.

    Args:
        symptom_text: Free-text description of symptoms.
        language: ``"en"`` for English, ``"kn"`` for Kannada.

    Returns:
        ``{"response": str, "urgency": str, "specialist": str, "source": str}``
    """
    groq_result = _call_groq(symptom_text, language)

    if groq_result is not None:
        groq_result["source"] = "groq"
        return groq_result

    logger.info("Falling back to local rule-based provider")
    fallback = _fallback_response(symptom_text)
    fallback["source"] = "rule-based"
    return fallback
