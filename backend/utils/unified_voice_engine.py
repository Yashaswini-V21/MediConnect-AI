"""
Unified Voice Engine
Single reusable voice module for Kannada + English STT with stable controls
"""

import logging
from typing import Optional, Callable, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class VoiceLanguage(Enum):
    ENGLISH = "en-US"
    KANNADA = "kn-IN"


class VoiceState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"


class UnifiedVoiceEngine:
    """
    Single voice module for multilingual speech capture
    - Supports Kannada and English
    - Stable start/stop controls
    - Transcript callbacks
    - Consistent error handling
    """
    
    def __init__(self):
        self.state = VoiceState.IDLE
        self.current_language = VoiceLanguage.ENGLISH
        self.is_listening = False
        self.transcript_buffer = ""
        self.error_message = None
        self.transcript_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        self.state_callback: Optional[Callable] = None
    
    def start_listening(
        self,
        language: str = "en-US",
        transcript_callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
        state_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Start voice listening
        
        Args:
            language: 'en-US' or 'kn-IN'
            transcript_callback: fn(transcript) called with recognized text
            error_callback: fn(error) called on error
            state_callback: fn(state) called on state change
            
        Returns:
            {success: bool, message: str, state: str}
        """
        if self.is_listening:
            logger.warning("Already listening")
            return {
                'success': False,
                'message': 'Voice already listening',
                'state': self.state.value
            }
        
        # Validate language
        language_upper = language.upper()
        if language_upper not in ['EN-US', 'KN-IN']:
            logger.error(f"Unsupported language: {language}")
            return {
                'success': False,
                'message': 'Unsupported language. Use en-US or kn-IN',
                'state': self.state.value
            }
        
        try:
            self.current_language = VoiceLanguage.ENGLISH if language_upper == 'EN-US' else VoiceLanguage.KANNADA
            self.transcript_callback = transcript_callback
            self.error_callback = error_callback
            self.state_callback = state_callback
            
            self._set_state(VoiceState.LISTENING)
            self.is_listening = True
            self.transcript_buffer = ""
            self.error_message = None
            
            logger.info(f"Voice listening started: {language}")
            
            return {
                'success': True,
                'message': f'Voice listening started in {language}',
                'state': self.state.value,
                'language': language
            }
        except Exception as e:
            error_msg = f"Failed to start listening: {str(e)}"
            logger.error(error_msg)
            self._handle_error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'state': self.state.value
            }
    
    def stop_listening(self) -> Dict[str, Any]:
        """
        Stop voice listening and return transcript
        
        Returns:
            {success: bool, transcript: str, state: str}
        """
        if not self.is_listening:
            logger.warning("Not currently listening")
            return {
                'success': False,
                'message': 'Not listening',
                'transcript': '',
                'state': self.state.value
            }
        
        try:
            self.is_listening = False
            final_transcript = self.transcript_buffer
            
            self._set_state(VoiceState.IDLE)
            self.transcript_buffer = ""
            
            logger.info(f"Voice listening stopped. Transcript length: {len(final_transcript)}")
            
            return {
                'success': True,
                'message': 'Voice listening stopped',
                'transcript': final_transcript,
                'state': self.state.value
            }
        except Exception as e:
            error_msg = f"Failed to stop listening: {str(e)}"
            logger.error(error_msg)
            self._handle_error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'transcript': self.transcript_buffer,
                'state': self.state.value
            }
    
    def process_transcript(self, transcript_text: str) -> None:
        """Process recognized transcript"""
        if not transcript_text:
            return
        
        self.transcript_buffer += transcript_text
        
        # Callback with transcript
        if self.transcript_callback:
            try:
                self.transcript_callback(transcript_text)
            except Exception as e:
                logger.error(f"Transcript callback error: {e}")
    
    def switch_language(self, language: str) -> Dict[str, Any]:
        """Switch voice language mid-session"""
        language_upper = language.upper()
        if language_upper not in ['EN-US', 'KN-IN']:
            return {
                'success': False,
                'message': 'Unsupported language',
                'current_language': self.current_language.value
            }
        
        old_language = self.current_language
        self.current_language = VoiceLanguage.ENGLISH if language_upper == 'EN-US' else VoiceLanguage.KANNADA
        
        logger.info(f"Language switched: {old_language.value} → {self.current_language.value}")
        
        return {
            'success': True,
            'message': f'Language switched to {language}',
            'previous_language': old_language.value,
            'current_language': self.current_language.value
        }
    
    def get_transcript(self) -> str:
        """Get current transcript buffer"""
        return self.transcript_buffer
    
    def clear_transcript(self) -> None:
        """Clear transcript buffer"""
        self.transcript_buffer = ""
        logger.info("Transcript buffer cleared")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current engine state"""
        return {
            'state': self.state.value,
            'is_listening': self.is_listening,
            'language': self.current_language.value,
            'transcript_length': len(self.transcript_buffer),
            'error': self.error_message
        }
    
    def _set_state(self, new_state: VoiceState) -> None:
        """Set state and trigger callback"""
        if new_state != self.state:
            self.state = new_state
            if self.state_callback:
                try:
                    self.state_callback(new_state.value)
                except Exception as e:
                    logger.error(f"State callback error: {e}")
    
    def _handle_error(self, error_msg: str) -> None:
        """Handle error and trigger callback"""
        self.error_message = error_msg
        self.is_listening = False
        self._set_state(VoiceState.ERROR)
        
        if self.error_callback:
            try:
                self.error_callback(error_msg)
            except Exception as e:
                logger.error(f"Error callback error: {e}")
    
    def reset(self) -> None:
        """Reset engine to initial state"""
        self.state = VoiceState.IDLE
        self.is_listening = False
        self.transcript_buffer = ""
        self.error_message = None
        self.current_language = VoiceLanguage.ENGLISH
        logger.info("Voice engine reset to idle")


# Singleton instance
_voice_engine = None

def get_voice_engine() -> UnifiedVoiceEngine:
    """Get singleton voice engine instance"""
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = UnifiedVoiceEngine()
    return _voice_engine


def create_voice_engine() -> UnifiedVoiceEngine:
    """Create new voice engine instance"""
    return UnifiedVoiceEngine()
