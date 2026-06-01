"""
AI Doctor Chat Routes
Uses Groq LLM for rich health guidance, with rule-based fallback.
"""
from flask import Blueprint, request, jsonify
from utils.groq_provider import get_health_response
from utils.ai_provider import RuleBasedProvider
from utils.diagnostic_agent import run_diagnostic  # New LangGraph agent
from utils.sarvam import SARVAM_API_KEY
from utils.sarvam import translate_via_sarvam
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

# Local rule-based provider (used for quick-advice and as import)
provider = RuleBasedProvider()


def _normalize_language(language: str) -> str:
    return (language or 'en').strip().lower()


def _translate_chat_response(text: str, language: str) -> str:
    """Translate a response to Kannada via Sarvam when configured."""
    if _normalize_language(language) not in ('kn', 'kannada'):
        return text
    if not SARVAM_API_KEY:
        return text

    try:
        return translate_via_sarvam(text, source='en', target='kn')
    except Exception:
        logger.exception('Sarvam translation failed for chatbot response')
        return text


@chat_bp.route('/doctor', methods=['POST'])
def doctor_chat():
    """
    AI Doctor chatbot endpoint.
    Tries Groq first, falls back to local rule-based provider automatically.
    """
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        language = _normalize_language(data.get('language', 'en'))

        if not message:
            return jsonify({
                'error': 'Message is required',
                'code': 400,
                'detail': 'The "message" field must be a non-empty string.'
            }), 400

        logger.info(f"AI Doctor request - Language: {language}, Message: {message[:50]}...")

        # Detect if this is likely a symptom query to use the advanced agent
        symptom_keywords = ['pain', 'fever', 'cough', 'ache', 'hurt', 'symptom', 'sick', 'condition']
        is_symptom = any(kw in message.lower() for kw in symptom_keywords) or len(message.split()) > 5

        if is_symptom:
            # Use LangGraph Agent for reactive, multi-node analysis
            logger.info("Using LangGraph Diagnostic Agent for reactive analysis")
            agent_result = run_diagnostic(message, language=language)
            
            response_text = _translate_chat_response(agent_result['final_response'], language)

            return jsonify({
                'success': True,
                'response': response_text,
                'urgency': agent_result['urgency_level'],
                'specialist': ', '.join(agent_result['matched_specialists']),
                'hospitals': agent_result['nearest_hospitals'],
                'source': 'langgraph',
                'language': language
            })
        
        # Regular chat fallback for conversational queries
        result = get_health_response(message, language)
        response_text = _translate_chat_response(result['response'], language)

        return jsonify({
            'success': True,
            'response': response_text,
            'urgency': result.get('urgency', 'LOW'),
            'specialist': result.get('specialist', 'General Physician'),
            'source': result.get('source', 'groq'),
            'language': language
        })

    except Exception as e:
        logger.error(f"AI Doctor chat error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to process your message',
            'code': 500,
            'detail': str(e)
        }), 500


@chat_bp.route('/quick-advice', methods=['POST'])
def quick_advice():
    """
    Quick health advice for common symptoms (always local, no LLM call).
    """
    try:
        data = request.get_json()
        symptom = data.get('symptom', '').strip()
        language = data.get('language', 'en')

        if not symptom:
            return jsonify({
                'error': 'Symptom is required',
                'code': 400,
                'detail': 'The "symptom" field must be a non-empty string.'
            }), 400

        # Quick advice templates (fast, no API call)
        quick_tips = {
            'headache': "Drink water, rest in a dark quiet room, apply cold compress. If severe or persistent, consult a doctor.",
            'fever': "Stay hydrated, rest, take temperature regularly. If fever >101°F or lasts >3 days, see a doctor immediately.",
            'cold': "Rest, drink warm fluids, use steam inhalation. Most colds resolve in 7-10 days. Seek help if breathing difficulty occurs.",
            'cough': "Stay hydrated, use honey (if no diabetes), avoid smoke. Persistent cough >2 weeks needs medical attention.",
            'stomach': "Eat light foods, stay hydrated with ORS, avoid spicy foods. Severe pain or blood requires immediate medical care."
        }

        # Find matching advice
        advice = None
        for key, value in quick_tips.items():
            if key in symptom.lower():
                advice = value
                break

        if not advice:
            advice = "For any health concern, it's best to consult with a healthcare professional for proper diagnosis and treatment."

        return jsonify({
            'success': True,
            'advice': advice,
            'language': language
        })

    except Exception as e:
        logger.error(f"Quick advice error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to get advice',
            'code': 500,
            'detail': str(e)
        }), 500
