"""
Advanced Voice Assistant
Enhanced voice interaction with emergency triage, real-time feedback, and smart routing
Integrates: Voice Input → Triage Pipeline → Emergency Flow → Hospital Routing → Voice Output
"""

import logging
from typing import Dict, Optional, Callable, Any
from datetime import datetime
from enum import Enum
import time

logger = logging.getLogger(__name__)


class VoiceAssistantMode(Enum):
    """Voice assistant operational modes"""
    NORMAL = "normal"
    EMERGENCY_TRIAGE = "emergency_triage"
    HOSPITAL_ROUTING = "hospital_routing"
    FOLLOW_UP = "follow_up"


class AdvancedVoiceAssistant:
    """
    Advanced voice assistant with:
    - Real-time symptom triage during voice capture
    - Emergency detection & immediate response
    - Hospital routing with voice guidance
    - Multi-language support (English + Kannada)
    - Progress callbacks for UI updates
    - Intelligent turn-taking and clarification
    """
    
    def __init__(
        self,
        voice_engine,
        voice_output,
        triage_pipeline,
        emergency_flow,
        hospital_matcher,
        safety_gate
    ):
        """Initialize advanced voice assistant with all components"""
        self.voice_engine = voice_engine
        self.voice_output = voice_output
        self.triage_pipeline = triage_pipeline
        self.emergency_flow = emergency_flow
        self.hospital_matcher = hospital_matcher
        self.safety_gate = safety_gate
        
        # Session tracking
        self.session_id = None
        self.mode = VoiceAssistantMode.NORMAL
        self.is_active = False
        self.current_transcript = ""
        self.conversation_history = []
        self.user_location = None
        self.user_language = "en-US"
        
        # Callbacks
        self.on_progress: Optional[Callable] = None
        self.on_emergency: Optional[Callable] = None
        self.on_triage_complete: Optional[Callable] = None
        self.on_hospital_found: Optional[Callable] = None
        
        logger.info("Advanced Voice Assistant initialized")
    
    def start_session(
        self,
        language: str = "en-US",
        user_location: Optional[Dict] = None,
        on_progress: Optional[Callable] = None,
        on_emergency: Optional[Callable] = None,
        on_triage_complete: Optional[Callable] = None,
        on_hospital_found: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Start a comprehensive voice session
        
        Args:
            language: 'en-US' or 'kn-IN'
            user_location: {'lat': float, 'lng': float}
            Callbacks for real-time updates
            
        Returns:
            Session info with greeting and instructions
        """
        self.session_id = self._generate_session_id()
        self.mode = VoiceAssistantMode.NORMAL
        self.is_active = True
        self.user_language = language
        self.user_location = user_location
        self.current_transcript = ""
        self.conversation_history = []
        
        # Register callbacks
        self.on_progress = on_progress
        self.on_emergency = on_emergency
        self.on_triage_complete = on_triage_complete
        self.on_hospital_found = on_hospital_found
        
        logger.info(f"Voice session started: {self.session_id}, language: {language}")
        
        # Start with greeting
        greeting = self._get_greeting(language)
        self.voice_output.speak(greeting, language=language)
        
        self._notify_progress({
            'stage': 'initialized',
            'message': 'Voice session started',
            'listening': True
        })
        
        # Start voice capture
        self.voice_engine.start_listening(
            language=language,
            transcript_callback=self._on_transcript_received
        )
        
        return {
            'success': True,
            'session_id': self.session_id,
            'greeting': greeting,
            'listening': True,
            'language': language
        }
    
    def stop_session(self) -> Dict[str, Any]:
        """Stop current voice session"""
        self.is_active = False
        
        # Stop voice capture
        voice_result = self.voice_engine.stop_listening()
        
        # Stop any playing audio
        self.voice_output.stop()
        
        logger.info(f"Voice session ended: {self.session_id}")
        
        return {
            'success': True,
            'session_id': self.session_id,
            'transcript': voice_result.get('transcript', ''),
            'duration_seconds': self._get_session_duration()
        }
    
    def process_full_flow(
        self,
        symptoms_text: str,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process complete flow: Triage → Emergency Check → Routing → Response
        Real-time feedback at each stage
        """
        start_time = time.time()
        self.current_transcript = symptoms_text
        
        try:
            # Stage 1: Safety Check (IMMEDIATE)
            self._notify_progress({'stage': 'safety_check', 'message': 'Checking for emergencies...'})
            safety_result = self.safety_gate.evaluate(symptoms_text)
            
            if safety_result.get('is_emergency'):
                self._handle_emergency(safety_result, symptoms_text, user_lat, user_lng)
                return {
                    'success': True,
                    'is_emergency': True,
                    'triage': safety_result,
                    'flow': 'emergency'
                }
            
            # Stage 2: Triage Pipeline
            self._notify_progress({'stage': 'triage', 'message': 'Analyzing symptoms...'})
            
            # Parse symptoms
            from utils.triage_pipeline import SymptomParser, RiskScorer, CareNavigator
            parsed = SymptomParser.parse(symptoms_text)
            risk_score = RiskScorer.score(parsed, symptoms_text)
            care_pathway = CareNavigator.navigate(risk_score)
            
            self._notify_progress({
                'stage': 'triage_complete',
                'risk_level': risk_score.get('risk_level'),
                'specialist': care_pathway.get('specialist'),
                'urgency': care_pathway.get('urgency')
            })
            
            if self.on_triage_complete:
                self.on_triage_complete({
                    'parsed': parsed,
                    'risk': risk_score,
                    'pathway': care_pathway
                })
            
            # Stage 3: Hospital Routing (if needed)
            if risk_score.get('risk_level') in ['CRITICAL', 'HIGH'] and user_lat and user_lng:
                self._notify_progress({'stage': 'routing', 'message': 'Finding nearby hospitals...'})
                
                hospitals = self.hospital_matcher.find_emergency_hospitals(
                    user_location={'lat': user_lat, 'lng': user_lng},
                    max_results=3
                )
                
                if hospitals:
                    self._announce_hospital(hospitals[0])
                    
                    if self.on_hospital_found:
                        self.on_hospital_found(hospitals)
            
            # Stage 4: Response Generation
            response = self._generate_response(care_pathway, parsed)
            elapsed = time.time() - start_time
            
            self._notify_progress({
                'stage': 'complete',
                'elapsed_seconds': elapsed,
                'response_ready': True
            })
            
            # Speak final advice
            self.voice_output.speak(response['advice'], language=self.user_language)
            
            return {
                'success': True,
                'is_emergency': False,
                'triage': {
                    'parsed': parsed,
                    'risk': risk_score,
                    'pathway': care_pathway
                },
                'response': response,
                'elapsed_seconds': elapsed,
                'flow': 'normal'
            }
        
        except Exception as e:
            logger.error(f"Flow processing error: {e}", exc_info=True)
            error_msg = "I encountered an issue. Please call emergency services or consult a healthcare professional."
            self.voice_output.speak(error_msg, language=self.user_language)
            return {
                'success': False,
                'error': str(e),
                'message': error_msg
            }
    
    def _on_transcript_received(self, transcript: str) -> None:
        """
        Callback when transcript is received
        Can trigger clarifying questions or immediate analysis
        """
        self.current_transcript += transcript
        self.conversation_history.append({
            'type': 'user',
            'text': transcript,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(f"Transcript received: {transcript[:50]}...")
        
        # Optional: Real-time analysis as user speaks
        # This could detect emergency keywords and interrupt for clarification
        if self._contains_emergency_keywords(transcript):
            logger.warning("Emergency keywords detected in transcript")
            self._notify_progress({'emergency_detected': True})
    
    def _handle_emergency(
        self,
        safety_result: Dict,
        symptoms_text: str,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None
    ) -> None:
        """Handle emergency scenario"""
        logger.critical(f"EMERGENCY DETECTED: {symptoms_text}")
        
        # Immediate voice announcement
        emergency_msg = safety_result.get('guidance', 'This is an emergency. Calling emergency services.')
        self.voice_output.speak(emergency_msg, language=self.user_language)
        
        self.mode = VoiceAssistantMode.EMERGENCY_TRIAGE
        
        # Notify emergency handler
        if self.on_emergency:
            self.on_emergency({
                'guidance': emergency_msg,
                'action': safety_result.get('action_required'),
                'contact': safety_result.get('contact', '108'),
                'location': {'lat': user_lat, 'lng': user_lng}
            })
        
        # Find nearest hospital with emergency
        if user_lat and user_lng:
            hospitals = self.hospital_matcher.find_emergency_hospitals(
                user_location={'lat': user_lat, 'lng': user_lng},
                max_results=1
            )
            
            if hospitals:
                self._announce_hospital(hospitals[0])
                
                if self.on_hospital_found:
                    self.on_hospital_found(hospitals)
    
    def _announce_hospital(self, hospital: Dict) -> None:
        """Announce nearest hospital with routing info"""
        announcement = (
            f"The nearest hospital is {hospital['name']}. "
            f"It's {hospital.get('distance_km', 0)} km away, "
            f"approximately {hospital.get('estimated_time_minutes', 0)} minutes drive. "
            f"Emergency services are available. "
        )
        
        logger.info(f"Announcing hospital: {hospital['name']}")
        self.voice_output.speak(announcement, language=self.user_language)
        
        self.conversation_history.append({
            'type': 'assistant',
            'text': announcement,
            'timestamp': datetime.utcnow().isoformat(),
            'hospital': hospital['id']
        })
    
    def _generate_response(self, care_pathway: Dict, parsed_symptoms: Dict) -> Dict[str, str]:
        """Generate contextual advice based on triage"""
        specialist = care_pathway.get('specialist', 'General Physician')
        urgency = care_pathway.get('urgency', 'ROUTINE')
        setting = care_pathway.get('setting', 'Clinic')
        
        if urgency == 'IMMEDIATE':
            advice = f"This requires immediate medical attention. Please visit the emergency department or call emergency services. You may need to see a {specialist}."
        elif urgency == 'URGENT':
            advice = f"You should see a {specialist} as soon as possible, preferably within a few hours. Visit an urgent care center or emergency department if symptoms worsen."
        elif urgency == 'ROUTINE':
            advice = f"It's recommended to schedule an appointment with a {specialist} for evaluation. Make sure to monitor your symptoms in the meantime."
        else:
            advice = "Monitor your symptoms and consult a healthcare professional if they persist or worsen."
        
        return {
            'advice': advice,
            'specialist': specialist,
            'setting': setting,
            'urgency': urgency
        }
    
    def _get_greeting(self, language: str) -> str:
        """Get language-specific greeting"""
        if language == 'kn-IN':
            return "ನಮಸ್ಕಾರ. ನಾನು ನಿಮ್ಮ ಆರೋಗ್ಯ ಸಹಾಯಕ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ರೋಗಲಕ್ಷಣಗಳನ್ನು ವಿವರಿಸಿ."
        else:
            return "Hello. I'm your health assistant. Please describe your symptoms."
    
    def _contains_emergency_keywords(self, text: str) -> bool:
        """Check if text contains emergency keywords"""
        emergency_keywords = [
            'chest pain', 'breathing difficulty', 'unconscious', 'severe bleeding',
            'stroke', 'heart attack', 'difficulty breathing', 'severe pain',
            'emergency', 'urgent', 'critical'
        ]
        return any(keyword in text.lower() for keyword in emergency_keywords)
    
    def _notify_progress(self, progress: Dict) -> None:
        """Notify progress callback"""
        if self.on_progress:
            try:
                self.on_progress({
                    'session_id': self.session_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    **progress
                })
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"vs_{int(time.time() * 1000)}"
    
    def _get_session_duration(self) -> float:
        """Get session duration in seconds"""
        # This would need start_time tracking
        return 0
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get complete session summary"""
        return {
            'session_id': self.session_id,
            'language': self.user_language,
            'mode': self.mode.value,
            'transcript_length': len(self.current_transcript),
            'conversation_turns': len(self.conversation_history),
            'status': 'active' if self.is_active else 'completed',
            'timestamp': datetime.utcnow().isoformat()
        }


# Singleton instance
_advanced_assistant = None

def get_advanced_voice_assistant(
    voice_engine=None,
    voice_output=None,
    triage_pipeline=None,
    emergency_flow=None,
    hospital_matcher=None,
    safety_gate=None
) -> AdvancedVoiceAssistant:
    """Get or create advanced voice assistant"""
    global _advanced_assistant
    if _advanced_assistant is None and all([
        voice_engine, voice_output, triage_pipeline,
        emergency_flow, hospital_matcher, safety_gate
    ]):
        _advanced_assistant = AdvancedVoiceAssistant(
            voice_engine,
            voice_output,
            triage_pipeline,
            emergency_flow,
            hospital_matcher,
            safety_gate
        )
    return _advanced_assistant
