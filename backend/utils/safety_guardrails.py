"""Safety Guardrails for MediConnect AI"""
from typing import Dict, Any

class Guardrail:
    def evaluate(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        is_emergency = any(kw in text_lower for kw in ["chest pain", "breathing", "heart attack", "stroke", "severe"])
        return {
            "is_emergency": is_emergency,
            "guidance": "🚨 Critical emergency detected. Call 108 immediately." if is_emergency else "Symptom checker analysis complete.",
            "action_required": "EMERGENCY_SOS" if is_emergency else "ROUTINE_CONSULT"
        }

class SafetyGate:
    def __init__(self, triage_pipeline):
        self.triage_pipeline = triage_pipeline
        self.guardrail = Guardrail()
        
    def check_emergency(self, text: str) -> Dict[str, Any]:
        evaluation = self.guardrail.evaluate(text)
        return {
            "is_emergency": evaluation["is_emergency"],
            "guidance": evaluation["guidance"]
        }
        
    def evaluate_with_safety(self, text: str) -> Dict[str, Any]:
        triage_result = {}
        if self.triage_pipeline:
            triage_result = self.triage_pipeline.analyze(text)
            
        safety_check = self.guardrail.evaluate(text)
        return {
            "triage_result": triage_result,
            "safety_check": safety_check,
            "is_emergency": safety_check["is_emergency"]
        }

def create_safety_gate(triage_pipeline) -> SafetyGate:
    return SafetyGate(triage_pipeline)
