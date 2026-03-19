"""
Clinical Safety Guardrails
Red-flag detection and emergency override for MediConnect
"""

import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    SAFE = "SAFE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class EmergencyGuardrail:
    """Detects critical/emergency symptoms and triggers override"""
    
    # Red-flag symptom patterns (HIGH confidence triggers)
    RED_FLAGS = {
        'cardiac_arrest': {
            'keywords': ['no pulse', 'unconscious', 'not breathing', 'collapsed'],
            'severity': SafetyLevel.EMERGENCY,
            'action': 'IMMEDIATE_911',
            'guidance': 'PERSON NEEDS IMMEDIATE CPR AND EMERGENCY SERVICES. Call 108 now.'
        },
        'severe_chest_pain': {
            'keywords': ['crushing chest pain', 'severe chest', 'chest pain radiating', 'chest tightness severe', 'pressure chest'],
            'severity': SafetyLevel.EMERGENCY,
            'action': 'IMMEDIATE_911',
            'guidance': 'Possible heart attack. Chew aspirin if available. Call 108 immediately.'
        },
        'severe_breathing': {
            'keywords': ['unable to breathe', 'no air', 'suffocating', 'severe breathlessness', 'cannot breathe'],
            'severity': SafetyLevel.EMERGENCY,
            'action': 'IMMEDIATE_911',
            'guidance': 'Severe respiratory distress. Call 108 immediately. Sit upright if possible.'
        },
        'stroke_symptoms': {
            'keywords': ['face drooping', 'arm weakness', 'speech difficulty', 'sudden confusion', 'sudden numbness', 'sudden weakness', 'sudden vision', 'loss consciousness'],
            'severity': SafetyLevel.EMERGENCY,
            'action': 'IMMEDIATE_911',
            'guidance': 'Possible stroke. Note time of symptom onset. Call 108 immediately. Time is critical.'
        },
        'severe_bleeding': {
            'keywords': ['uncontrollable bleeding', 'severe bleeding', 'arterial bleeding', 'blood spurting', 'massive bleeding'],
            'severity': SafetyLevel.EMERGENCY,
            'action': 'IMMEDIATE_911',
            'guidance': 'Severe hemorrhage. Apply pressure immediately. Call 108 now. Elevate affected area.'
        },
        'anaphylaxis': {
            'keywords': ['anaphylaxis', 'throat closing', 'cannot swallow', 'swelling throat', 'severe allergic', 'tongue swelling'],
            'severity': SafetyLevel.EMERGENCY,
            'action': 'IMMEDIATE_911',
            'guidance': 'Anaphylactic shock. Use EpiPen if available. Call 108 immediately.'
        },
        'severe_poisoning': {
            'keywords': ['poison', 'overdose', 'toxin', 'chemical burn', 'accidental overdose'],
            'severity': SafetyLevel.EMERGENCY,
            'action': 'IMMEDIATE_911',
            'guidance': 'Suspected poisoning/overdose. Call 108 or Poison Control immediately. Have medication name ready.'
        },
        'severe_trauma': {
            'keywords': ['head trauma', 'spinal injury', 'multiple fractures', 'crush injury', 'internal bleeding'],
            'severity': SafetyLevel.EMERGENCY,
            'action': 'IMMEDIATE_911',
            'guidance': 'Severe trauma. Do not move victim. Call 108 immediately. Stabilize injured area.'
        },
        'suicidal_crisis': {
            'keywords': ['want to die', 'suicidal', 'harm myself', 'kill myself', 'end it all', 'no reason to live'],
            'severity': SafetyLevel.EMERGENCY,
            'action': 'CRISIS_SUPPORT',
            'guidance': 'Mental health crisis detected. Call Crisis Helpline: AASRA 9820466726. Talk to someone now.'
        },
        'severe_seizure': {
            'keywords': ['continuous seizure', 'status epilepticus', 'repeated seizures', 'seizure not stopping'],
            'severity': SafetyLevel.EMERGENCY,
            'action': 'IMMEDIATE_911',
            'guidance': 'Prolonged seizure activity. Call 108 immediately. Stay with person, keep airway clear.'
        },
        'septic_shock': {
            'keywords': ['septic shock', 'severe infection', 'organ failure', 'sepsis', 'extremely high fever'],
            'severity': SafetyLevel.EMERGENCY,
            'action': 'IMMEDIATE_911',
            'guidance': 'Possible septic shock. Call 108 immediately. Hospital admission required.'
        }
    }
    
    # WARNING flags (elevated risk, needs urgent attention)
    WARNING_FLAGS = {
        'moderate_chest_pain': {
            'keywords': ['chest pain', 'chest discomfort', 'chest pressure', 'chest tightness'],
            'severity': SafetyLevel.WARNING,
            'action': 'URGENT_EVAL',
            'guidance': 'Chest symptoms warrant urgent medical evaluation. Avoid strenuous activity. Seek help soon.'
        },
        'moderate_breathing': {
            'keywords': ['difficulty breathing', 'shortness of breath', 'struggling to breathe', 'breathless'],
            'severity': SafetyLevel.WARNING,
            'action': 'URGENT_EVAL',
            'guidance': 'Breathing difficulty noted. Rest, avoid exertion. See doctor same-day if possible.'
        },
        'high_fever': {
            'keywords': ['fever 103', 'fever 104', 'high fever', 'temperature 39', 'temperature 40'],
            'severity': SafetyLevel.WARNING,
            'action': 'URGENT_EVAL',
            'guidance': 'Very high fever detected. Seek urgent medical evaluation to rule out serious infection.'
        },
        'altered_consciousness': {
            'keywords': ['confused', 'confusion', 'delirious', 'disoriented', 'drowsy', 'lethargic'],
            'severity': SafetyLevel.WARNING,
            'action': 'URGENT_EVAL',
            'guidance': 'Altered mental state detected. Seek urgent medical evaluation. This could indicate serious illness.'
        },
        'severe_dehydration': {
            'keywords': ['severe dehydration', 'cannot drink', 'extreme thirst', 'no urine'],
            'severity': SafetyLevel.WARNING,
            'action': 'URGENT_EVAL',
            'guidance': 'Severe dehydration signs. Seek urgent care. IV fluids may be needed.'
        }
    }
    
    @classmethod
    def evaluate(cls, symptom_text: str) -> Dict[str, any]:
        """
        Evaluate symptom text for safety concerns
        
        Returns:
            {
                'safety_level': SafetyLevel enum,
                'is_emergency': bool,
                'red_flag_match': matched red flag or None,
                'action_required': action code,
                'guidance': actionable guidance,
                'override_normal_triage': bool
            }
        """
        if not symptom_text:
            return cls._safe_result()
        
        text_lower = symptom_text.lower()
        
        # Check RED FLAGS (highest priority)
        for flag_name, flag_config in cls.RED_FLAGS.items():
            if any(keyword in text_lower for keyword in flag_config['keywords']):
                logger.critical(f"EMERGENCY RED FLAG DETECTED: {flag_name}")
                return {
                    'safety_level': flag_config['severity'].value,
                    'is_emergency': True,
                    'red_flag_match': flag_name,
                    'action_required': flag_config['action'],
                    'guidance': flag_config['guidance'],
                    'override_normal_triage': True
                }
        
        # Check WARNING FLAGS
        for warning_name, warning_config in cls.WARNING_FLAGS.items():
            if any(keyword in text_lower for keyword in warning_config['keywords']):
                logger.warning(f"WARNING FLAG DETECTED: {warning_name}")
                return {
                    'safety_level': warning_config['severity'].value,
                    'is_emergency': False,
                    'red_flag_match': warning_name,
                    'action_required': warning_config['action'],
                    'guidance': warning_config['guidance'],
                    'override_normal_triage': True
                }
        
        # SAFE - proceed with normal triage
        return cls._safe_result()
    
    @classmethod
    def _safe_result(cls) -> Dict[str, any]:
        return {
            'safety_level': SafetyLevel.SAFE.value,
            'is_emergency': False,
            'red_flag_match': None,
            'action_required': 'NORMAL_TRIAGE',
            'guidance': None,
            'override_normal_triage': False
        }


class SafetyGate:
    """Wraps triage pipeline with safety guardrails"""
    
    def __init__(self, triage_pipeline):
        self.triage_pipeline = triage_pipeline
        self.guardrail = EmergencyGuardrail()
    
    def evaluate_with_safety(self, symptom_text: str) -> Dict[str, any]:
        """
        Evaluate symptoms through safety gate first, then optional normal triage
        
        If emergency detected: return emergency guidance, skip normal triage
        If safe: proceed with normal triage pipeline
        """
        logger.info(f"Safety gate evaluation: {symptom_text[:50]}...")
        
        # Stage 1: Safety evaluation
        safety_assessment = self.guardrail.evaluate(symptom_text)
        
        result = {
            'safety_check': safety_assessment,
            'triage_result': None
        }
        
        # If emergency, bypass normal triage and return emergency guidance immediately
        if safety_assessment['is_emergency']:
            logger.critical("EMERGENCY DETECTED - BYPASSING NORMAL TRIAGE")
            result['emergency_override'] = True
            result['emergency_guidance'] = self._generate_emergency_response(safety_assessment)
            return result
        
        # If warning but not emergency, proceed with normal triage + add warning
        if safety_assessment['override_normal_triage']:
            logger.warning("WARNING FLAG - PROCEEDING WITH TRIAGE + WARNING")
            result['warning_override'] = True
        
        # Stage 2: Normal triage pipeline
        try:
            triage_result = self.triage_pipeline.triage(symptom_text)
            result['triage_result'] = triage_result
        except Exception as e:
            logger.error(f"Triage pipeline error: {e}")
            result['triage_error'] = str(e)
        
        return result
    
    def check_emergency(self, symptom_text: str) -> Dict[str, bool]:
        """Alias for guardrail evaluate() for API compatibility"""
        result = self.guardrail.evaluate(symptom_text)
        return {
            'is_emergency': result.get('is_emergency', False),
            'safety_level': result.get('safety_level'),
            'red_flag_match': result.get('red_flag_match')
        }
    
    @staticmethod
    def _generate_emergency_response(safety_assessment: Dict) -> Dict[str, any]:
        """Generate emergency-focused response"""
        return {
            'emergency_type': safety_assessment['red_flag_match'],
            'severity': safety_assessment['safety_level'],
            'immediate_action': safety_assessment['action_required'],
            'guidance': safety_assessment['guidance'],
            'contact_emergency': True,
            'emergency_number': '108',
            'bypass_normal_chat': True
        }


def create_safety_gate(triage_pipeline):
    """Factory for safety gate"""
    return SafetyGate(triage_pipeline)
