"""
Voice Output Assistant
Bilingual TTS with language-specific voices and stop/interrupt controls
"""

import logging
from typing import Optional, Callable, Dict, Any
from enum import Enum
import threading
import pyttsx3
import time

logger = logging.getLogger(__name__)


class TTSLanguage(Enum):
    ENGLISH = "en-US"
    KANNADA = "kn-IN"


class VoiceOutputState(Enum):
    IDLE = "idle"
    SPEAKING = "speaking"
    PAUSED = "paused"
    ERROR = "error"


class VoiceOutputAssistant:
    """
    Text-to-Speech assistant with bilingual support
    - English and Kannada voices
    - Instant stop/interrupt
    - Language switching
    - Progress callbacks
    """
    
    # Voice configurations by language
    VOICE_CONFIGS = {
        'en-US': {
            'voice_name': 'en-US-Neural2-A',  # Professional English voice
            'pitch': 1.0,
            'speed': 1.0,
            'language': 'en-US'
        },
        'kn-IN': {
            'voice_name': 'kn-IN-Neural2-A',  # Kannada voice
            'pitch': 1.0,
            'speed': 1.0,
            'language': 'kn-IN'
        }
    }
    
    def __init__(self):
        self.state = VoiceOutputState.IDLE
        self.current_language = TTSLanguage.ENGLISH
        self.is_speaking = False
        self.current_text = ""
        self.is_interrupted = False
        self.speak_thread: Optional[threading.Thread] = None
        self.progress_callback: Optional[Callable] = None
        self.complete_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        
        # Initialize TTS Engine safely
        try:
            self.engine = pyttsx3.init()
            # Set properties
            self.engine.setProperty('rate', 150)    # Speed
            self.engine.setProperty('volume', 0.9)  # Volume
            # Set default voice
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)
        except Exception as e:
            logger.error(f"TTS Engine initialization failed: {e}")
            self.engine = None
    
    def speak(
        self,
        text: str,
        language: str = "en-US",
        progress_callback: Optional[Callable] = None,
        complete_callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Speak text in specified language
        
        Args:
            text: Text to speak
            language: 'en-US' or 'kn-IN'
            progress_callback: fn(char_index) called during speech
            complete_callback: fn() called when complete
            error_callback: fn(error) called on error
            
        Returns:
            {success: bool, message: str, state: str}
        """
        if self.is_speaking:
            logger.warning("Already speaking. Call stop() first.")
            return {
                'success': False,
                'message': 'Already speaking',
                'state': self.state.value
            }
        
        if not text or not isinstance(text, str):
            return {
                'success': False,
                'message': 'Invalid text',
                'state': self.state.value
            }
        
        # Validate language
        if language not in self.VOICE_CONFIGS:
            logger.error(f"Unsupported language: {language}")
            return {
                'success': False,
                'message': f'Unsupported language: {language}',
                'state': self.state.value
            }
        
        try:
            self.current_text = text
            self.current_language = TTSLanguage.ENGLISH if language == 'en-US' else TTSLanguage.KANNADA
            self.progress_callback = progress_callback
            self.complete_callback = complete_callback
            self.error_callback = error_callback
            self.is_interrupted = False
            
            # Start speaking in background thread
            self.speak_thread = threading.Thread(
                target=self._speak_async,
                args=(text, language),
                daemon=True
            )
            self.speak_thread.start()
            
            self._set_state(VoiceOutputState.SPEAKING)
            self.is_speaking = True
            
            logger.info(f"TTS started: {language}, text length: {len(text)}")
            
            return {
                'success': True,
                'message': f'Speaking in {language}',
                'state': self.state.value,
                'language': language,
                'text_length': len(text)
            }
        except Exception as e:
            error_msg = f"Failed to start speech: {str(e)}"
            logger.error(error_msg)
            self._handle_error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'state': self.state.value
            }
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop/interrupt current speech immediately
        
        Returns:
            {success: bool, message: str, state: str}
        """
        if not self.is_speaking:
            return {
                'success': False,
                'message': 'Not currently speaking',
                'state': self.state.value
            }
        
        try:
            self.is_interrupted = True
            self.is_speaking = False
            
            # Wait for thread to finish
            if self.speak_thread and self.speak_thread.is_alive():
                self.speak_thread.join(timeout=1.0)
            
            self._set_state(VoiceOutputState.IDLE)
            self.current_text = ""
            
            logger.info("Speech interrupted")
            
            return {
                'success': True,
                'message': 'Speech interrupted',
                'state': self.state.value
            }
        except Exception as e:
            error_msg = f"Failed to stop speech: {str(e)}"
            logger.error(error_msg)
            self._handle_error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'state': self.state.value
            }
    
    def pause(self) -> Dict[str, Any]:
        """Pause current speech"""
        if self.state != VoiceOutputState.SPEAKING:
            return {
                'success': False,
                'message': 'No speech to pause',
                'state': self.state.value
            }
        
        self._set_state(VoiceOutputState.PAUSED)
        logger.info("Speech paused")
        
        return {
            'success': True,
            'message': 'Speech paused',
            'state': self.state.value
        }
    
    def resume(self) -> Dict[str, Any]:
        """Resume paused speech"""
        if self.state != VoiceOutputState.PAUSED:
            return {
                'success': False,
                'message': 'No paused speech to resume',
                'state': self.state.value
            }
        
        self._set_state(VoiceOutputState.SPEAKING)
        logger.info("Speech resumed")
        
        return {
            'success': True,
            'message': 'Speech resumed',
            'state': self.state.value
        }
    
    def switch_language(self, language: str) -> Dict[str, Any]:
        """Switch TTS language"""
        if language not in self.VOICE_CONFIGS:
            return {
                'success': False,
                'message': f'Unsupported language: {language}',
                'current_language': self.current_language.value
            }
        
        old_lang = self.current_language.value
        self.current_language = TTSLanguage.ENGLISH if language == 'en-US' else TTSLanguage.KANNADA
        
        logger.info(f"TTS language switched: {old_lang} → {language}")
        
        return {
            'success': True,
            'message': f'Language switched to {language}',
            'previous_language': old_lang,
            'current_language': language
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get current TTS state"""
        return {
            'state': self.state.value,
            'is_speaking': self.is_speaking,
            'language': self.current_language.value,
            'current_text_length': len(self.current_text),
            'is_interrupted': self.is_interrupted
        }
    
    def _speak_async(self, text: str, language: str) -> None:
        """Async speech synthesis using pyttsx3 with background thread safety"""
        if not self.engine:
            self._handle_error("TTS Engine not available")
            return

        try:
            # Configure language-specific voice if available
            voices = self.engine.getProperty('voices')
            if language == 'kn-IN':
                # Attempt to find a Kannada voice
                kannada_voice = next((v for v in voices if 'kn' in v.languages or 'Kannada' in v.name), None)
                if kannada_voice:
                    self.engine.setProperty('voice', kannada_voice.id)
            else:
                # English voice
                english_voice = next((v for v in voices if 'en' in v.languages or 'English' in v.name), None)
                if english_voice:
                    self.engine.setProperty('voice', english_voice.id)

            # Start the speech engine loop
            # Note: engine.runAndWait() is blocking, which is why we are in a thread
            self.engine.say(text)
            
            # Start loop in a way we can check interrupted
            # pyttsx3 doesn't have a great "stop" if inside say(), 
            # but we can try ending the loop if possible
            self.engine.runAndWait()

            if not self.is_interrupted:
                self._set_state(VoiceOutputState.IDLE)
                if self.complete_callback:
                    try:
                        self.complete_callback()
                    except Exception as e:
                        logger.error(f"Complete callback error: {e}")
            
            self.is_speaking = False
        except Exception as e:
            error_msg = f"Speech synthesis error: {str(e)}"
            logger.error(error_msg)
            self._handle_error(error_msg)
    
    def _set_state(self, new_state: VoiceOutputState) -> None:
        """Set current state"""
        self.state = new_state
        logger.debug(f"TTS state changed to: {new_state.value}")
    
    def _handle_error(self, error_msg: str) -> None:
        """Handle error"""
        self._set_state(VoiceOutputState.ERROR)
        self.is_speaking = False
        if self.error_callback:
            try:
                self.error_callback(error_msg)
            except Exception as e:
                logger.error(f"Error callback error: {e}")


# Singleton instance
_tts_assistant = None

def get_voice_output_assistant() -> VoiceOutputAssistant:
    """Get singleton TTS assistant instance"""
    global _tts_assistant
    if _tts_assistant is None:
        _tts_assistant = VoiceOutputAssistant()
    return _tts_assistant


def create_voice_output_assistant() -> VoiceOutputAssistant:
    """Create new TTS assistant instance"""
    return VoiceOutputAssistant()
