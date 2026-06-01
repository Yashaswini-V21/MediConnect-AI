"""Triage Pipeline for MediConnect AI"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class SymptomParser:
    @staticmethod
    def parse(text: str) -> List[str]:
        text_lower = text.lower()
        symptoms = []
        if "chest pain" in text_lower or "heart" in text_lower:
            symptoms.append("Chest Pain")
        if "breathing" in text_lower or "breath" in text_lower:
            symptoms.append("Shortness of Breath")
        if "cough" in text_lower:
            symptoms.append("Cough")
        if "fever" in text_lower:
            symptoms.append("Fever")
        return symptoms

class RiskScorer:
    @staticmethod
    def score(parsed_symptoms: List[str], raw_text: str) -> Dict[str, Any]:
        has_severe = any(s in ["Chest Pain", "Shortness of Breath"] for s in parsed_symptoms)
        raw_lower = raw_text.lower()
        is_critical = "severe" in raw_lower or "critical" in raw_lower or "emergency" in raw_lower
        
        if is_critical or has_severe:
            risk_level = "HIGH"
            urgency_score = 9
        elif parsed_symptoms:
            risk_level = "MEDIUM"
            urgency_score = 5
        else:
            risk_level = "LOW"
            urgency_score = 2
            
        return {
            "risk_level": risk_level,
            "urgency_score": urgency_score,
            "symptoms": parsed_symptoms
        }

class CareNavigator:
    @staticmethod
    def navigate(risk_score: Dict[str, Any]) -> Dict[str, Any]:
        risk_level = risk_score.get("risk_level", "LOW")
        if risk_level == "HIGH":
            return {
                "action": "EMERGENCY",
                "recommended_action": "Seek emergency medical care immediately",
                "recommended_specialties": ["Emergency Medicine", "Cardiology"],
                "emergency_contact": "108"
            }
        else:
            return {
                "action": "ROUTINE",
                "recommended_action": "Consult a general physician",
                "recommended_specialties": ["General Medicine"],
                "emergency_contact": "Nearest Clinic"
            }

class TriagePipeline:
    def __init__(self):
        pass
        
    def analyze(self, text: str) -> Dict[str, Any]:
        parsed = SymptomParser.parse(text)
        risk = RiskScorer.score(parsed, text)
        nav = CareNavigator.navigate(risk)
        return {
            "risk_assessment": risk,
            "care_navigation": nav,
            "symptoms_extracted": parsed,
            "urgency": risk["risk_level"],
            "urgency_score": risk["urgency_score"]
        }

_pipeline_instance = None

def get_triage_pipeline() -> TriagePipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = TriagePipeline()
    return _pipeline_instance
