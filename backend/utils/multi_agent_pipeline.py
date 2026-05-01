"""
MediConnect-AI M6: LangGraph Multi-Agent Pipeline
6-Agent sequence for medical triage, diagnosis, and routing.
"""

import os
import json
from typing import TypedDict, List, Optional, Annotated, Dict
import operator

# State Definition
class MedicalState(TypedDict):
    input_text: str              # original input
    language: str                # "en" or "kn"
    symptoms: List[str]          # extracted symptoms
    translated_text: str         # english equivalent
    conditions: List[Dict]       # possible conditions
    specialists: List[str]       # recommended specialist types
    hospitals: List[Dict]        # ranked hospitals
    urgency_level: str           # HIGH, MEDIUM, LOW
    confidence_score: float      # confidence from ML
    reasoning_chain: List[str]   # steps taken
    final_explanation: str       # human-readable summary
    error: Optional[str]         # error handling

class MultiAgentPipeline:
    def __init__(self):
        # We'll use the existing models and agents instead of raw LangGraph if not installed
        from models.symptom_analyzer import get_symptom_analyzer
        from models.hospital_matcher import get_hospital_matcher
        from models.ml_classifier import MediConnectMLClassifier
        
        self.analyzer = get_symptom_analyzer()
        self.matcher = get_hospital_matcher()
        self.classifier = MediConnectMLClassifier()
        
    def run(self, input_text: str, language: str = 'en') -> MedicalState:
        """
        Runs the 6-agent simulation using existing project logic.
        """
        state: MedicalState = {
            "input_text": input_text,
            "language": language,
            "symptoms": [],
            "translated_text": "",
            "conditions": [],
            "specialists": [],
            "hospitals": [],
            "urgency_level": "LOW",
            "confidence_score": 0.0,
            "reasoning_chain": [],
            "final_explanation": "",
            "error": None
        }
        
        try:
            # 1. Symptom Extraction Agent
            state["reasoning_chain"].append("Agent 1: Extracting symptoms")
            analysis = self.analyzer.analyze(input_text, language=language)
            state["symptoms"] = analysis.get("symptoms", [])
            state["translated_text"] = analysis.get("translated_text", input_text)
            
            # 2. Knowledge Retrieval Agent
            state["reasoning_chain"].append("Agent 2: Retrieving matches from Knowledge Base")
            # Logic normally inside analyzer.analyze but we make it explicit for M6
            matches = analysis.get("conditions", [])
            state["conditions"] = matches[:3]
            
            # 3. Specialist Recommender Agent
            state["reasoning_chain"].append("Agent 3: Mapping conditions to specialists")
            for cond in matches:
                specs = cond.get("specialists", [])
                for s in specs:
                    if s not in state["specialists"]:
                        state["specialists"].append(s)
            
            # 4. Hospital Router Agent
            state["reasoning_chain"].append("Agent 4: Routing to nearest specialized hospitals")
            hospital_results = self.matcher.find_hospitals(state["symptoms"])
            state["hospitals"] = hospital_results[:3]
            
            # 5. Risk Assessor Agent (ML-First)
            state["reasoning_chain"].append("Agent 5: Performing ML Risk Assessment")
            prediction = self.classifier.predict_urgency(state["symptoms"])
            state["urgency_level"] = prediction["urgency"]
            state["confidence_score"] = prediction["confidence"]
            
            # 6. Explainer Agent
            state["reasoning_chain"].append("Agent 6: Generating human-readable summary")
            urgency_map = {"HIGH": "Emergency", "MEDIUM": "Urgent", "LOW": "Non-urgent"}
            exp = f"Based on our analysis, we detected {len(state['symptoms'])} symptoms. "
            exp += f"This appears to be a {urgency_map[state['urgency_level']]} situation. "
            exp += f"We recommend consulting a {', '.join(state['specialists'][:1])}."
            state["final_explanation"] = exp
            
        except Exception as e:
            state["error"] = str(e)
            state["reasoning_chain"].append(f"ERROR: {str(e)}")
            
        return state

_pipeline_instance = None
def get_pipeline():
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = MultiAgentPipeline()
    return _pipeline_instance
