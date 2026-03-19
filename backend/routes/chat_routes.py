"""
AI Doctor Chat Routes
Rule-based health assistant with multilingual support (no external API calls)
"""
from flask import Blueprint, request, jsonify
from utils.ai_provider import RuleBasedProvider
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

# Initialize rule-based provider
provider = RuleBasedProvider()


def get_fallback_response(message: str) -> str:
    """Fallback responses when Azure OpenAI is unavailable"""
    return provider.get_health_advice(message)


@chat_bp.route('/doctor', methods=['POST'])
def doctor_chat():
    """
    AI Doctor chatbot endpoint
    Rule-based responses with Kannada support - no external API calls
    """
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        language = data.get('language', 'english')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        logger.info(f"AI Doctor request - Language: {language}, Message: {message[:50]}...")
        
        # Get response from rule-based provider
        response = provider.get_health_advice(message)
        
        return jsonify({
            'success': True,
            'response': response,
            'language': language
        })
    
    except Exception as e:
        logger.error(f"AI Doctor chat error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to process your message',
            'details': str(e)
        }), 500



@chat_bp.route('/quick-advice', methods=['POST'])
def quick_advice():
    """
    Quick health advice for common symptoms
    """
    try:
        data = request.get_json()
        symptom = data.get('symptom', '').strip()
        language = data.get('language', 'english')
        
        if not symptom:
            return jsonify({'error': 'Symptom is required'}), 400
        
        # Quick advice templates
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
        return jsonify({'error': 'Failed to get advice'}), 500
