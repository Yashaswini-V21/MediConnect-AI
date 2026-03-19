"""
Healthcare AI Platform Integration
Complete orchestration of all components
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthcareAIPlatform:
    """
    Complete healthcare AI platform integrating:
    - Triage pipeline
    - Safety guardrails
    - Voice engines (input + output)
    - Smart routing
    - Emergency flow
    - Metrics/analytics
    """
    
    def __init__(
        self,
        triage_pipeline,
        safety_gate,
        voice_engine,
        voice_output_assistant,
        smart_router,
        reliability_metrics
    ):
        self.triage_pipeline = triage_pipeline
        self.safety_gate = safety_gate
        self.voice_engine = voice_engine
        self.voice_output_assistant = voice_output_assistant
        self.smart_router = smart_router
        self.metrics = reliability_metrics
        
        logger.info("Healthcare AI Platform initialized")
    
    # ===== DIAGNOSTIC API =====
    
    def analyze_symptoms_text(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Comprehensive symptom analysis
        
        Args:
            text: Symptom description
            context: Optional patient context (age, history, etc.)
            
        Returns:
            Full diagnostic result with triage + routing
        """
        try:
            # Execute through safety gate
            safe_result = self.safety_gate.evaluate_with_safety(text)
            
            # Extract triage result
            triage = safe_result.get('triage_result', {})
            
            return {
                'success': True,
                'analysis': {
                    'symptom_input': text,
                    'triage': triage,
                    'is_emergency': safe_result['safety_check'].get('is_emergency', False),
                    'safety_guidance': safe_result['safety_check'].get('guidance')
                }
            }
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_emergency_guidance(self, text: str) -> Dict[str, Any]:
        """Get immediate emergency guidance if needed"""
        safety_check = self.safety_gate.guardrail.evaluate(text)
        
        if safety_check['is_emergency']:
            return {
                'is_emergency': True,
                'guidance': safety_check['guidance'],
                'action': safety_check['action_required'],
                'contact': '108'
            }
        return {'is_emergency': False}
    
    # ===== VOICE API =====
    
    def start_voice_input(
        self,
        language: str = "en-US",
        transcript_callback = None
    ) -> Dict[str, Any]:
        """Start voice input capture"""
        return self.voice_engine.start_listening(
            language=language,
            transcript_callback=transcript_callback
        )
    
    def stop_voice_input(self) -> Dict[str, Any]:
        """Stop voice input and get transcript"""
        return self.voice_engine.stop_listening()
    
    def speak_response(
        self,
        text: str,
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """Speak response in selected language"""
        return self.voice_output_assistant.speak(text, language=language)
    
    def stop_speech(self) -> Dict[str, Any]:
        """Stop current speech"""
        return self.voice_output_assistant.stop()
    
    # ===== ROUTING API =====
    
    def find_nearest_hospitals(
        self,
        user_lat: float,
        user_lng: float,
        urgency: str = "MODERATE"
    ) -> Dict[str, Any]:
        """Find nearby hospitals ranked by emergency relevance"""
        return self.smart_router.find_nearest_hospital(user_lat, user_lng, urgency)
    
    def get_route_to_hospital(
        self,
        user_lat: float,
        user_lng: float,
        hospital_id: str,
        mode: str = "ambulance"
    ) -> Dict[str, Any]:
        """Get navigation route to hospital"""
        return self.smart_router.get_route(user_lat, user_lng, hospital_id, mode)
    
    # ===== ANALYTICS API =====
    
    def get_reliability_dashboard(self) -> Dict[str, Any]:
        """Get system reliability metrics"""
        return self.metrics.get_dashboard_summary()
    
    def get_daily_metrics(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily performance metrics"""
        return self.metrics.get_daily_metrics(date)
    
    # ===== HEALTH CHECK API =====
    
    def health_check(self) -> Dict[str, Any]:
        """Check system health"""
        return {
            'status': 'healthy',
            'components': {
                'triage_pipeline': 'ready',
                'safety_guardrails': 'ready',
                'voice_input': self.voice_engine.get_state(),
                'voice_output': self.voice_output_assistant.get_state(),
                'routing': 'ready',
                'metrics': 'ready'
            },
            'timestamp': datetime.utcnow().isoformat()
        }


def create_healthcare_ai_platform(
    triage_pipeline,
    safety_gate,
    voice_engine,
    voice_output_assistant,
    smart_router,
    reliability_metrics
) -> HealthcareAIPlatform:
    """Factory for healthcare AI platform"""
    return HealthcareAIPlatform(
        triage_pipeline,
        safety_gate,
        voice_engine,
        voice_output_assistant,
        smart_router,
        reliability_metrics
    )
