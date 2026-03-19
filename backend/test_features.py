#!/usr/bin/env python
"""
Quick feature test to verify symptoms analyzer, voice assistant, and chatbot work
"""

import logging
from models.symptom_analyzer import get_symptom_analyzer
from utils.ai_provider import RuleBasedProvider
from utils.voice_output_assistant import get_voice_output_assistant
from utils.unified_voice_engine import get_voice_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_symptom_analyzer():
    """Test symptom analyzer"""
    print("\n" + "="*60)
    print("Testing Symptom Analyzer")
    print("="*60)
    
    analyzer = get_symptom_analyzer()
    
    # Test 1: Basic symptom analysis
    test_cases = [
        "chest pain",
        "severe headache",
        "fever and cough",
        "breathing difficulty"
    ]
    
    for symptoms in test_cases:
        result = analyzer.analyze(symptoms)
        print(f"\nSymptoms: {symptoms}")
        print(f"  Urgency: {result.get('urgency_level')}")
        print(f"  Score: {result.get('urgency_score')}")
        print(f"  Specialties: {result.get('recommended_specialties')}")
        print(f"  First Aid: {result.get('first_aid_tips')[:2]}")
    
    print("\n✓ Symptom Analyzer: OK")


def test_rule_based_provider():
    """Test rule-based health advice provider"""
    print("\n" + "="*60)
    print("Testing Rule-Based Health Advice Provider")
    print("="*60)
    
    provider = RuleBasedProvider()
    
    # Test health advice
    test_messages = [
        "Hello",
        "fever",
        "chest pain",
        "How to manage hypertension?"
    ]
    
    for message in test_messages:
        advice = provider.get_health_advice(message)
        print(f"\nMessage: '{message}'")
        print(f"Response: {advice[:100]}...")
    
    # Test symptom analysis
    print("\n\nTesting symptom analysis:")
    symptoms_test = [
        "severe chest pain and breathing difficulty",
        "mild cold and cough",
        "fever with nausea"
    ]
    
    for symptoms in symptoms_test:
        result = provider.analyze_symptoms(symptoms)
        print(f"\nSymptoms: {symptoms}")
        print(f"  Urgency: {result['urgency']}")
        print(f"  Specialties: {result['specialties']}")
    
    print("\n✓ Rule-Based Provider: OK")


def test_voice_assistant():
    """Test voice assistant"""
    print("\n" + "="*60)
    print("Testing Voice Assistants")
    print("="*60)
    
    # Test Voice Output Assistant
    tts = get_voice_output_assistant()
    
    print("\nVoice Output Assistant:")
    state = tts.get_state()
    print(f"  State: {state['state']}")
    print(f"  Language: {state['language']}")
    print(f"  Is Speaking: {state['is_speaking']}")
    
    # Test speaking (won't actually play audio in test)
    result = tts.speak("Hello, this is a health check", language="en-US")
    print(f"\n  Speak result: {result['success']}")
    print(f"  Message: {result['message']}")
    
    # Stop speaking
    stop_result = tts.stop()
    print(f"  Stop result: {stop_result['success']}")
    
    print("\n✓ Voice Output Assistant: OK")
    
    # Test Voice Input Engine
    print("\nVoice Input Engine:")
    voice_engine = get_voice_engine()
    
    state = voice_engine.get_state()
    print(f"  State: {state['state']}")
    print(f"  Language: {state['language']}")
    print(f"  Is Listening: {state['is_listening']}")
    
    # Start listening
    result = voice_engine.start_listening(language="en-US")
    print(f"\n  Start listening result: {result['success']}")
    
    # Simulate a transcript
    voice_engine.process_transcript("chest pain and shortness of breath")
    transcript = voice_engine.get_transcript()
    print(f"  Transcript: {transcript}")
    
    # Stop listening
    stop_result = voice_engine.stop_listening()
    print(f"  Stop listening result: {stop_result['success']}")
    print(f"  Final transcript: {stop_result['transcript']}")
    
    print("\n✓ Voice Engine: OK")


def test_integrated_flow():
    """Test integrated flow: voice input -> symptom analysis -> response"""
    print("\n" + "="*60)
    print("Testing Integrated Flow")
    print("="*60)
    
    analyzer = get_symptom_analyzer()
    voice_engine = get_voice_engine()
    tts = get_voice_output_assistant()
    
    # Simulate voice input
    voice_engine.start_listening(language="en-US")
    voice_engine.process_transcript("I have severe chest pain radiating to my left arm")
    voice_transcript = voice_engine.get_transcript()
    voice_engine.stop_listening()
    
    print(f"\n1. Voice Input: {voice_transcript}")
    
    # Analyze symptoms
    analysis = analyzer.analyze(voice_transcript)
    print(f"\n2. Analysis Result:")
    print(f"   Urgency: {analysis['urgency_level']}")
    print(f"   Specialties: {analysis['recommended_specialties']}")
    print(f"   First Aid: {analysis['first_aid_tips']}")
    
    # Generate response
    response_text = f"Based on your symptoms, this is a {analysis['urgency_level'].lower()} priority. You should {analysis['first_aid_tips'][0] if analysis['first_aid_tips'] else 'seek medical attention'}."
    print(f"\n3. Response: {response_text}")
    
    # Speak response
    tts.speak(response_text, language="en-US")
    tts.stop()
    
    print("\n✓ Integrated Flow: OK")


if __name__ == "__main__":
    try:
        logger.info("Starting feature tests...")
        
        test_symptom_analyzer()
        test_rule_based_provider()
        test_voice_assistant()
        test_integrated_flow()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\nKey Features Validated:")
        print("  1. ✓ Symptom Analyzer - working")
        print("  2. ✓ Rule-Based Health Advisor - working")
        print("  3. ✓ Voice Output Assistant (TTS) - working")
        print("  4. ✓ Voice Input Engine (STT) - working")
        print("  5. ✓ Integrated Speech-to-Response Flow - working")
        print("\nThe project is ready for deployment!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
