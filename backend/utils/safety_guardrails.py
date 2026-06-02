"""Safety Guardrails for MediConnect AI — Production-hardened version."""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Comprehensive emergency keyword lists (expanded from minimal original)
EMERGENCY_KEYWORDS = {
    'critical': [
        'chest pain', 'heart attack', 'cardiac arrest', 'stroke', 'not breathing',
        'stopped breathing', 'unconscious', 'unresponsive', 'seizure', 'convulsion',
        'severe bleeding', 'heavy bleeding', 'blood everywhere', 'anaphylaxis',
        'anaphylactic shock', 'severe allergic reaction', 'throat closing',
        'can\'t breathe', 'cannot breathe', 'difficulty breathing', 'shortness of breath',
        'choking', 'drowning', 'overdose', 'poison', 'poisoning',
        'suicidal', 'suicide', 'self harm', 'self-harm',
        'paralysis', 'paralyzed', 'sudden weakness', 'face drooping',
        'arm weakness', 'slurred speech', 'sudden headache', 'worst headache',
        'blunt trauma', 'head injury', 'spinal injury', 'broken neck',
        'internal bleeding', 'organ failure', 'respiratory failure',
        'diabetic emergency', 'hypoglycemia severe', 'blood sugar crash',
    ],
    'high': [
        'severe pain', 'excruciating', 'extreme pain', 'unbearable pain',
        'high fever', 'very high temperature', 'fever above 104', 'fever above 40',
        'vomiting blood', 'coughing blood', 'blood in stool', 'rectal bleeding',
        'severe abdominal pain', 'severe stomach pain', 'appendicitis',
        'fracture', 'bone broken', 'compound fracture', 'dislocated',
        'burns severe', 'chemical burn', 'electrical shock',
        'severe dehydration', 'fainted', 'fainting', 'lost consciousness',
        'deep cut', 'deep wound', 'puncture wound', 'stab wound',
        'gunshot', 'accident', 'car accident', 'crash',
    ],
}

# Flatten for quick search
_ALL_CRITICAL = set(EMERGENCY_KEYWORDS['critical'])
_ALL_HIGH = set(EMERGENCY_KEYWORDS['high'])


class Guardrail:
    def evaluate(self, text: str) -> Dict[str, Any]:
        """
        Evaluate text for emergency indicators.
        Returns classification with severity level and confidence.
        """
        if not text:
            return self._routine_result()

        text_lower = text.lower()

        # Check critical first
        matched_critical = [kw for kw in _ALL_CRITICAL if kw in text_lower]
        if matched_critical:
            logger.warning(
                f"EMERGENCY DETECTED — critical keywords: {matched_critical[:3]}"
            )
            return {
                "is_emergency": True,
                "severity": "CRITICAL",
                "confidence": "HIGH",
                "matched_keywords": matched_critical[:5],
                "guidance": (
                    "🚨 CRITICAL EMERGENCY DETECTED. "
                    "Call 108 (Ambulance) immediately. "
                    "Do not wait — get emergency help now."
                ),
                "action_required": "EMERGENCY_SOS",
                "emergency_numbers": {
                    "ambulance": "108",
                    "police": "100",
                    "fire": "101",
                    "helpline": "112"
                }
            }

        # Check high urgency
        matched_high = [kw for kw in _ALL_HIGH if kw in text_lower]
        if matched_high:
            logger.info(f"High urgency detected — keywords: {matched_high[:3]}")
            return {
                "is_emergency": True,
                "severity": "HIGH",
                "confidence": "MEDIUM",
                "matched_keywords": matched_high[:5],
                "guidance": (
                    "⚠️ Urgent medical attention required. "
                    "Visit the nearest emergency room or call 108 if symptoms worsen."
                ),
                "action_required": "URGENT_CARE",
                "emergency_numbers": {
                    "ambulance": "108",
                    "helpline": "112"
                }
            }

        return self._routine_result()

    def _routine_result(self) -> Dict[str, Any]:
        return {
            "is_emergency": False,
            "severity": "LOW",
            "confidence": "HIGH",
            "matched_keywords": [],
            "guidance": "Symptom checker analysis complete. Consult a doctor if symptoms persist.",
            "action_required": "ROUTINE_CONSULT",
            "emergency_numbers": {
                "ambulance": "108",
                "helpline": "112"
            }
        }


class SafetyGate:
    def __init__(self, triage_pipeline):
        self.triage_pipeline = triage_pipeline
        self.guardrail = Guardrail()

    def check_emergency(self, text: str) -> Dict[str, Any]:
        evaluation = self.guardrail.evaluate(text)
        return {
            "is_emergency": evaluation["is_emergency"],
            "severity": evaluation.get("severity", "LOW"),
            "guidance": evaluation["guidance"],
            "action_required": evaluation.get("action_required", "ROUTINE_CONSULT"),
        }

    def evaluate_with_safety(self, text: str) -> Dict[str, Any]:
        triage_result = {}
        if self.triage_pipeline:
            try:
                triage_result = self.triage_pipeline.analyze(text)
            except Exception as exc:
                logger.warning(f"Triage pipeline error (non-fatal): {exc}")

        safety_check = self.guardrail.evaluate(text)
        return {
            "triage_result": triage_result,
            "safety_check": safety_check,
            "is_emergency": safety_check["is_emergency"],
            "severity": safety_check.get("severity", "LOW"),
        }


def create_safety_gate(triage_pipeline) -> SafetyGate:
    return SafetyGate(triage_pipeline)
