"""
Agentic-Light Triage Pipeline
3-stage local reasoning: Symptom Parser → Risk Scorer → Care Navigator
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class CareAction(Enum):
    EMERGENCY = "EMERGENCY"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"
    PREVENTIVE = "PREVENTIVE"


class SymptomParser:
    """Stage 1: Parse raw symptom text into structured components"""
    
    # Comprehensive symptom keywords mapped to categories
    SYMPTOM_CATEGORIES = {
        'cardiac': {
            'keywords': ['chest pain', 'chest tightness', 'angina', 'palpitations', 'heart', 'cardiac', 'arrhythmia'],
            'severity': 'high',
            'urgency': 'emergency'
        },
        'respiratory': {
            'keywords': ['shortness of breath', 'breathing difficulty', 'asthma', 'wheezing', 'dyspnea', 'respiratory', 'suffocation'],
            'severity': 'high',
            'urgency': 'emergency'
        },
        'neurological': {
            'keywords': ['stroke', 'loss of consciousness', 'seizure', 'severe headache', 'confusion', 'vertigo', 'unconscious', 'coma'],
            'severity': 'high',
            'urgency': 'emergency'
        },
        'trauma': {
            'keywords': ['severe bleeding', 'fracture', 'head injury', 'major injury', 'accident', 'trauma', 'severe burn'],
            'severity': 'high',
            'urgency': 'emergency'
        },
        'allergic': {
            'keywords': ['anaphylaxis', 'severe allergy', 'throat swelling', 'severe reaction', 'hives', 'angioedema'],
            'severity': 'high',
            'urgency': 'emergency'
        },
        'infection': {
            'keywords': ['fever', 'infection', 'sepsis', 'pneumonia', 'meningitis', 'high temperature', 'flu'],
            'severity': 'moderate',
            'urgency': 'urgent'
        },
        'gastrointestinal': {
            'keywords': ['severe abdominal pain', 'vomiting', 'bleeding', 'diarrhea', 'nausea', 'stomach pain'],
            'severity': 'moderate',
            'urgency': 'urgent'
        },
        'mental_health': {
            'keywords': ['suicidal', 'self-harm', 'depression', 'anxiety', 'psychiatric', 'mental crisis'],
            'severity': 'high',
            'urgency': 'emergency'
        },
        'minor': {
            'keywords': ['headache', 'cold', 'cough', 'sore throat', 'rash', 'minor', 'ache', 'pain'],
            'severity': 'low',
            'urgency': 'routine'
        }
    }
    
    @classmethod
    def parse(cls, symptom_text: str) -> Dict[str, Any]:
        """Parse symptom text into structured format"""
        if not symptom_text or not isinstance(symptom_text, str):
            logger.warning("Invalid symptom text")
            return cls._default_result()
        
        text_lower = symptom_text.lower()
        matched_categories = []
        max_severity = 'low'
        max_urgency = 'routine'
        
        # Match symptoms to categories
        for category, config in cls.SYMPTOM_CATEGORIES.items():
            if any(keyword in text_lower for keyword in config['keywords']):
                matched_categories.append(category)
                # Track highest severity/urgency
                if config['severity'] in ['high', 'moderate', 'low']:
                    severity_rank = {'high': 3, 'moderate': 2, 'low': 1}
                    if severity_rank.get(config['severity'], 0) > severity_rank.get(max_severity, 0):
                        max_severity = config['severity']
                if config['urgency'] in ['emergency', 'urgent', 'routine']:
                    urgency_rank = {'emergency': 3, 'urgent': 2, 'routine': 1}
                    if urgency_rank.get(config['urgency'], 0) > urgency_rank.get(max_urgency, 0):
                        max_urgency = config['urgency']
        
        if not matched_categories:
            matched_categories = ['minor']
        
        return {
            'raw_text': symptom_text,
            'categories': matched_categories,
            'primary_category': matched_categories[0],
            'symptom_count': len(text_lower.split()),
            'severity_indication': max_severity,
            'urgency_indication': max_urgency
        }
    
    @classmethod
    def _default_result(cls) -> Dict[str, Any]:
        return {
            'raw_text': '',
            'categories': ['unknown'],
            'primary_category': 'unknown',
            'symptom_count': 0,
            'severity_indication': 'low',
            'urgency_indication': 'routine'
        }


class RiskScorer:
    """Stage 2: Score risk based on parsed symptoms"""
    
    # Risk scoring rules
    RISK_SCORES = {
        'cardiac': {'base': 95, 'red_flags': ['severe', 'crushing', 'spreading', 'sweating']},
        'respiratory': {'base': 90, 'red_flags': ['severe', 'unable to speak', 'blue lips']},
        'neurological': {'base': 95, 'red_flags': ['sudden', 'severe', 'consciousness']},
        'trauma': {'base': 90, 'red_flags': ['severe', 'bleeding', 'unconscious']},
        'allergic': {'base': 85, 'red_flags': ['anaphylaxis', 'throat', 'swelling']},
        'infection': {'base': 60, 'red_flags': ['high fever', 'persistent', 'spreading']},
        'gastrointestinal': {'base': 50, 'red_flags': ['severe', 'bleeding', 'persistent']},
        'mental_health': {'base': 80, 'red_flags': ['suicidal', 'harm', 'crisis']},
        'minor': {'base': 20, 'red_flags': []}
    }
    
    @classmethod
    def score(cls, parsed_symptoms: Dict[str, Any], symptom_text: str) -> Dict[str, Any]:
        """Calculate risk score (0-100)"""
        primary = parsed_symptoms.get('primary_category', 'minor')
        base_score = cls.RISK_SCORES.get(primary, {}).get('base', 20)
        red_flags = cls.RISK_SCORES.get(primary, {}).get('red_flags', [])
        
        # Boost score for red flags
        text_lower = symptom_text.lower()
        for flag in red_flags:
            if flag.lower() in text_lower:
                base_score = min(100, base_score + 15)
        
        # Boost for multiple symptoms
        symptom_count = parsed_symptoms.get('symptom_count', 0)
        if symptom_count > 5:
            base_score = min(100, base_score + 10)
        
        # Determine risk level
        if base_score >= 80:
            risk_level = RiskLevel.CRITICAL
        elif base_score >= 60:
            risk_level = RiskLevel.HIGH
        elif base_score >= 40:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW
        
        return {
            'risk_score': base_score,
            'risk_level': risk_level.value,
            'primary_category': primary,
            'red_flags_detected': [f for f in red_flags if f.lower() in text_lower],
            'rationale': cls._score_rationale(base_score, primary)
        }
    
    @classmethod
    def _score_rationale(cls, score: int, category: str) -> str:
        if score >= 80:
            return f"Emergency-level risk detected ({category}). Immediate professional intervention required."
        elif score >= 60:
            return f"High-risk symptoms detected ({category}). Urgent medical evaluation needed."
        elif score >= 40:
            return f"Moderate symptoms detected ({category}). Medical evaluation recommended soon."
        else:
            return f"Low-risk condition ({category}). Self-care with monitoring recommended."


class CareNavigator:
    """Stage 3: Route to appropriate care action"""
    
    # Care routing logic
    CARE_PATHS = {
        'CRITICAL': {
            'action': CareAction.EMERGENCY,
            'recommended_route': 'Hospital Emergency Department',
            'triage_time': '<5 minutes',
            'contact': '108 - Ambulance',
            'reasoning': 'Life-threatening condition detected. Immediate emergency services required.'
        },
        'HIGH': {
            'action': CareAction.URGENT,
            'recommended_route': 'Urgent Care / Hospital ER',
            'triage_time': '<30 minutes',
            'contact': 'Nearest Hospital or 108',
            'reasoning': 'Urgent medical evaluation required. Do not delay.'
        },
        'MODERATE': {
            'action': CareAction.ROUTINE,
            'recommended_route': 'Primary Care / Clinic',
            'triage_time': '<24 hours',
            'contact': 'Schedule appointment with General Physician',
            'reasoning': 'Medical evaluation recommended. Can schedule for later today/tomorrow.'
        },
        'LOW': {
            'action': CareAction.PREVENTIVE,
            'recommended_route': 'Self-care / Monitor',
            'triage_time': 'As needed',
            'contact': 'Consult doctor if symptoms worsen',
            'reasoning': 'Minor condition. Self-care and monitoring appropriate. Seek help if worsens.'
        }
    }
    
    # Specialty recommendations by category
    SPECIALTY_MAP = {
        'cardiac': ['Cardiologist', 'General Physician'],
        'respiratory': ['Pulmonologist', 'General Physician'],
        'neurological': ['Neurologist', 'General Physician'],
        'trauma': ['General Surgeon', 'Emergency Medicine'],
        'allergic': ['Immunologist', 'General Physician'],
        'infection': ['Infectious Disease Specialist', 'General Physician'],
        'gastrointestinal': ['Gastroenterologist', 'General Physician'],
        'mental_health': ['Psychiatrist', 'Clinical Psychologist'],
        'minor': ['General Physician']
    }
    
    @classmethod
    def navigate(cls, risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate care navigation and recommendations"""
        risk_level = risk_assessment.get('risk_level', 'LOW')
        primary_category = risk_assessment.get('primary_category', 'minor')
        
        care_path = cls.CARE_PATHS.get(risk_level, cls.CARE_PATHS['LOW'])
        specialties = cls.SPECIALTY_MAP.get(primary_category, ['General Physician'])
        
        return {
            'recommended_action': care_path['action'],
            'recommended_route': care_path['recommended_route'],
            'recommended_specialties': specialties,
            'target_triage_time': care_path['triage_time'],
            'emergency_contact': care_path['contact'],
            'navigation_rationale': care_path['reasoning'],
            'next_steps': cls._generate_next_steps(risk_level, primary_category)
        }
    
    @classmethod
    def _generate_next_steps(cls, risk_level: str, category: str) -> List[str]:
        """Generate actionable next steps"""
        if risk_level == 'CRITICAL':
            return [
                'Call 108 emergency services immediately',
                'Do not drive - use ambulance',
                'Inform ambulance of main symptoms',
                'Have someone stay with you'
            ]
        elif risk_level == 'HIGH':
            return [
                'Contact hospital emergency department',
                'Gather medical history and current medications',
                'Prepare list of symptoms and onset time',
                'Request immediate appointment'
            ]
        elif risk_level == 'MODERATE':
            return [
                'Schedule appointment with primary care physician',
                'Note symptom timeline and intensity',
                'Avoid heavy activity',
                'Monitor for worsening symptoms'
            ]
        else:
            return [
                'Use home remedies and rest',
                'Monitor symptoms over next few days',
                'Seek help if symptoms worsen',
                'Follow preventive health practices'
            ]


class TriagePipeline:
    """Complete 3-stage triage pipeline"""
    
    def __init__(self):
        self.parser = SymptomParser()
        self.scorer = RiskScorer()
        self.navigator = CareNavigator()
    
    def triage(self, symptom_text: str, patient_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute complete triage pipeline
        
        Args:
            symptom_text: Raw symptom description
            patient_context: Optional patient age, medical history, etc.
            
        Returns:
            Structured triage result with recommendations
        """
        logger.info(f"Starting triage pipeline for: {symptom_text[:50]}...")
        
        # Stage 1: Parse
        parsed = self.parser.parse(symptom_text)
        logger.info(f"Stage 1 (Parse) complete: {parsed['primary_category']}")
        
        # Stage 2: Score
        scored = self.scorer.score(parsed, symptom_text)
        logger.info(f"Stage 2 (Score) complete: {scored['risk_level']} ({scored['risk_score']}/100)")
        
        # Stage 3: Navigate
        navigated = self.navigator.navigate(scored)
        logger.info(f"Stage 3 (Navigate) complete: {navigated['recommended_action']}")
        
        return {
            'timestamp': self._timestamp(),
            'symptom_input': symptom_text,
            'parse_stage': parsed,
            'risk_assessment': scored,
            'care_navigation': navigated,
            'pipeline_version': '1.0',
            'rationale_chain': f"{parsed['primary_category']} → Risk:{scored['risk_level']} → Action:{navigated['recommended_action']}"
        }
    
    def analyze(self, symptom_text: str, patient_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Alias for triage() for API compatibility"""
        return self.triage(symptom_text, patient_context)
    
    @staticmethod
    def _timestamp():
        from datetime import datetime
        return datetime.utcnow().isoformat()


# Singleton instance
_pipeline_instance = None

def get_triage_pipeline() -> TriagePipeline:
    """Get singleton triage pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = TriagePipeline()
    return _pipeline_instance
