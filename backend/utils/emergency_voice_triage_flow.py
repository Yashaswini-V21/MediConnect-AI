"""
Emergency Voice Triage Flow
End-to-end voice → severity → hospital routing (target <15 seconds)
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class VoiceTriageStep(str):
    """Triage flow step identifiers"""
    LISTENING = "listening"
    PROCESSING = "processing"
    TRIAGE = "triage"
    ROUTING = "routing"
    COMPLETE = "complete"
    ERROR = "error"


class EmergencyVoiceTriageFlow:
    """
    Orchestrates complete emergency response:
    1. Voice listening (speech capture)
    2. Symptom processing & safety check
    3. Triage pipeline (risk scoring)
    4. Route optimization & mapping
    """
    
    def __init__(self, triage_pipeline, safety_gate, voice_engine, smart_router):
        self.triage_pipeline = triage_pipeline
        self.safety_gate = safety_gate
        self.voice_engine = voice_engine
        self.smart_router = smart_router
        
        self.flow_id = None
        self.start_time = None
        self.current_step = None
        self.transcript = ""
        self.results = {}
        self.timeline = []
    
    def start_emergency_triage(
        self,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """
        Initiate emergency voice triage
        
        Goal: Complete in <15 seconds
        - 2 sec: voice listening
        - 3 sec: triage pipeline
        - 2 sec: safety check
        - 3 sec: routing
        - 5 sec: UI presentation
        """
        self.flow_id = self._generate_flow_id()
        self.start_time = time.time()
        self.transcript = ""
        self.results = {}
        self.timeline = []
        
        if user_lat and user_lng:
            self.smart_router.set_user_location(user_lat, user_lng)
        
        logger.info(f"Emergency voice triage started: {self.flow_id}, language: {language}")
        
        return {
            'success': True,
            'flow_id': self.flow_id,
            'message': f'Ready to receive voice input in {language}',
            'step': VoiceTriageStep.LISTENING,
            'listen_timeout_seconds': 10
        }
    
    def process_voice_transcript(
        self,
        transcript: str,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process user's spoken symptoms
        
        Executes full pipeline: triage → safety → routing
        """
        if not self.flow_id or not transcript:
            return {'success': False, 'message': 'Invalid flow or transcript'}
        
        self.transcript = transcript
        elapsed = time.time() - self.start_time
        
        try:
            # Step 1: Safety check (CRITICAL - happens first)
            logger.info(f"[{self._elapsed_str()}] Safety check starting...")
            safety_result = self._execute_safety_check(transcript)
            self._log_step(VoiceTriageStep.PROCESSING, "Safety check completed")
            
            # If emergency detected, return immediately with emergency guidance
            if safety_result.get('is_emergency'):
                emergency_output = self._generate_emergency_response(
                    safety_result,
                    user_lat,
                    user_lng
                )
                self._log_step(VoiceTriageStep.COMPLETE, "Emergency detected - immediate response")
                return emergency_output
            
            # Step 2: Triage pipeline (normal case)
            logger.info(f"[{self._elapsed_str()}] Triage pipeline starting...")
            triage_result = self._execute_triage(transcript)
            self._log_step(VoiceTriageStep.TRIAGE, "Triage analysis completed")
            
            # Step 3: Route to hospital (if needed)
            if triage_result.get('risk_assessment', {}).get('risk_level') in ['CRITICAL', 'HIGH']:
                logger.info(f"[{self._elapsed_str()}] Smart routing for {triage_result['risk_assessment']['risk_level']} case...")
                routing_result = self._execute_routing(
                    triage_result,
                    user_lat,
                    user_lng
                )
                self._log_step(VoiceTriageStep.ROUTING, "Hospital routing completed")
            else:
                routing_result = None
            
            # Step 4: Compile results
            self._log_step(VoiceTriageStep.COMPLETE, "Voice triage flow complete")
            
            total_time = time.time() - self.start_time
            logger.info(f"Emergency voice triage completed in {total_time:.2f}s")
            
            return {
                'success': True,
                'flow_id': self.flow_id,
                'timestamp': datetime.utcnow().isoformat(),
                'transcript': transcript,
                'triage_result': triage_result,
                'routing_result': routing_result,
                'timeline': self.timeline,
                'total_duration_seconds': round(total_time, 2),
                'performance_grade': self._grade_performance(total_time),
                'next_action': self._generate_next_action(triage_result, routing_result)
            }
        
        except Exception as e:
            error_msg = f"Voice triage flow error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._log_step(VoiceTriageStep.ERROR, error_msg)
            
            return {
                'success': False,
                'flow_id': self.flow_id,
                'message': error_msg,
                'step': VoiceTriageStep.ERROR
            }
    
    def _execute_safety_check(self, transcript: str) -> Dict[str, Any]:
        """Execute safety guardrail check"""
        try:
            safety_check = self.safety_gate.guardrail.evaluate(transcript)
            self.results['safety_check'] = safety_check
            return safety_check
        except Exception as e:
            logger.error(f"Safety check error: {e}")
            return {'is_emergency': False}
    
    def _execute_triage(self, transcript: str) -> Dict[str, Any]:
        """Execute triage pipeline"""
        try:
            triage_result = self.triage_pipeline.triage(transcript)
            self.results['triage_result'] = triage_result
            return triage_result
        except Exception as e:
            logger.error(f"Triage pipeline error: {e}")
            return {
                'risk_assessment': {'risk_level': 'MODERATE', 'risk_score': 50},
                'error': str(e)
            }
    
    def _execute_routing(
        self,
        triage_result: Dict,
        user_lat: Optional[float],
        user_lng: Optional[float]
    ) -> Dict[str, Any]:
        """Execute smart hospital routing"""
        try:
            if not user_lat or not user_lng:
                logger.warning("User location not available for routing")
                return None
            
            urgency = triage_result.get('risk_assessment', {}).get('risk_level', 'MODERATE')
            specialties = triage_result.get('care_navigation', {}).get('recommended_specialties', [])
            
            routing_result = self.smart_router.rank_hospitals_by_emergency(
                user_lat=user_lat,
                user_lng=user_lng,
                urgency=urgency,
                specialties_needed=specialties
            )
            
            self.results['routing_result'] = routing_result
            return routing_result
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return None
    
    def _generate_emergency_response(
        self,
        safety_result: Dict,
        user_lat: Optional[float],
        user_lng: Optional[float]
    ) -> Dict[str, Any]:
        """Generate immediate emergency response"""
        return {
            'success': True,
            'flow_id': self.flow_id,
            'timestamp': datetime.utcnow().isoformat(),
            'emergency_override': True,
            'emergency_type': safety_result.get('red_flag_match'),
            'severity': safety_result.get('safety_level'),
            'immediate_guidance': safety_result.get('guidance'),
            'emergency_number': '108',
            'call_ambulance_immediately': True,
            'total_duration_seconds': round(time.time() - self.start_time, 2),
            'timeline': self.timeline
        }
    
    def _generate_next_action(self, triage_result: Dict, routing_result: Optional[Dict]) -> Dict[str, Any]:
        """Generate next action for user"""
        urgency = triage_result.get('risk_assessment', {}).get('risk_level')
        
        if urgency == 'CRITICAL':
            if routing_result and routing_result.get('hospitals'):
                top_hospital = routing_result['hospitals'][0]
                return {
                    'action': 'ROUTE_TO_HOSPITAL',
                    'hospital': top_hospital['name'],
                    'eta_minutes': top_hospital['eta']['eta_minutes'],
                    'call_ambulance': True
                }
            else:
                return {
                    'action': 'CALL_AMBULANCE',
                    'number': '108'
                }
        elif urgency == 'HIGH':
            return {
                'action': 'URGENT_CARE',
                'message': 'Seek urgent medical evaluation',
                'time_limit': '30 minutes'
            }
        else:
            return {
                'action': 'SCHEDULE_APPOINTMENT',
                'message': 'Contact your doctor'
            }
    
    def _log_step(self, step: str, description: str) -> None:
        """Log triage step"""
        elapsed = self._elapsed_str()
        self.timeline.append({
            'timestamp': datetime.utcnow().isoformat(),
            'step': step,
            'description': description,
            'elapsed_seconds': time.time() - self.start_time
        })
        logger.info(f"[{elapsed}] {step}: {description}")
    
    def _elapsed_str(self) -> str:
        """Get elapsed time string"""
        if not self.start_time:
            return "0.0s"
        elapsed = time.time() - self.start_time
        return f"{elapsed:.1f}s"
    
    def _grade_performance(self, duration_seconds: float) -> str:
        """Grade performance vs target <15s"""
        if duration_seconds <= 5:
            return "EXCELLENT"
        elif duration_seconds <= 10:
            return "GOOD"
        elif duration_seconds <= 15:
            return "ACCEPTABLE"
        else:
            return "NEEDS_IMPROVEMENT"
    
    @staticmethod
    def _generate_flow_id() -> str:
        """Generate unique flow ID"""
        import uuid
        return f"EVT-{uuid.uuid4().hex[:8].upper()}"


def create_emergency_voice_triage_flow(
    triage_pipeline,
    safety_gate,
    voice_engine,
    smart_router
) -> EmergencyVoiceTriageFlow:
    """Factory for emergency voice triage flow"""
    return EmergencyVoiceTriageFlow(
        triage_pipeline,
        safety_gate,
        voice_engine,
        smart_router
    )
