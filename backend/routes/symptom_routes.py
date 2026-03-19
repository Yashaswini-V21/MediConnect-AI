from flask import Blueprint, request, jsonify
from utils.ai_provider import RuleBasedProvider
from models.user_model import db, SearchHistory
from utils.analytics import analytics
from utils.azure_translator_service import translate_to_kannada, translate_list
import logging
import time

symptom_bp = Blueprint('symptoms', __name__)
logger = logging.getLogger(__name__)

# Initialize rule-based provider for symptom analysis
provider = RuleBasedProvider()

@symptom_bp.route('/analyze', methods=['POST'])
def analyze_symptoms():
    """Analyze user symptoms and recommend specialties using rule-based logic"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('symptoms'):
            return jsonify({'error': 'Symptoms description is required'}), 400
        
        symptoms_text = data['symptoms']
        language = data.get('language', 'en')
        
        # Analyze symptoms using rule-based provider
        analysis_result = provider.analyze_symptoms(symptoms_text)
        
        # Add matched symptoms field for compatibility
        analysis_result['matched_symptoms'] = [symptoms_text[:30]]
        
        # Translate to Kannada if requested
        if language == 'kn':
            try:
                logger.info("Translating analysis result to Kannada...")
                # Translate recommendation
                if analysis_result.get('explanation'):
                    analysis_result['explanation'] = translate_to_kannada(analysis_result['explanation'])
                
                # Translate specialties
                if analysis_result.get('specialties'):
                    analysis_result['specialties'] = translate_list(
                        analysis_result['specialties'], 'kn'
                    )
                
                logger.info("Translation to Kannada completed")
            except Exception as trans_error:
                logger.warning(f"Translation failed, keeping English: {trans_error}")
                # Continue with English results if translation fails
        
        # Track analytics
        response_time = (time.time() - start_time) * 1000  # milliseconds
        urgency = analysis_result.get('urgency', 'MEDIUM')
        analytics.track_symptom_search(symptoms_text, urgency, response_time, language)
        
        logger.info(f"Symptom analysis completed: {urgency} urgency, {response_time:.2f}ms")
        
        return jsonify({
            'success': True,
            'analysis': analysis_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing symptoms: {e}")
        return jsonify({'error': str(e)}), 500

@symptom_bp.route('/list', methods=['GET'])
def list_symptoms():
    """Get list of all available symptoms"""
    try:
        # Return common symptoms that the rule-based provider recognizes
        symptoms = [
            'chest pain', 'headache', 'fever', 'breathing difficulty', 'cough',
            'cold', 'stomach pain', 'nausea', 'dizzy', 'fatigue', 'weak',
            'sore throat', 'vomit', 'pain', 'migraine', 'asthma', 'diabetes',
            'blood pressure', 'heart', 'fever', 'skin issue'
        ]
        
        return jsonify({
            'success': True,
            'symptoms': symptoms,
            'total': len(symptoms)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing symptoms: {e}")
        return jsonify({'error': str(e)}), 500

@symptom_bp.route('/search', methods=['GET'])
def search_symptoms():
    """Search symptoms by keyword"""
    try:
        query = request.args.get('q', '').lower().strip()
        
        if not query:
            return jsonify({'error': 'Search query required'}), 400
        
        # Common symptoms list
        all_symptoms = [
            'chest pain', 'headache', 'fever', 'breathing difficulty', 'cough',
            'cold', 'stomach pain', 'nausea', 'dizzy', 'fatigue', 'weak',
            'sore throat', 'vomit', 'pain', 'migraine', 'asthma', 'diabetes',
            'blood pressure', 'heart', 'flu', 'skin issue'
        ]
        
        # Filter by query
        results = [s for s in all_symptoms if query in s.lower()]
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching symptoms: {e}")
        return jsonify({'error': str(e)}), 500
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        analyzer = get_symptom_analyzer()
        results = analyzer.search_symptoms(query, limit)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'total': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching symptoms: {e}")
        return jsonify({'error': str(e)}), 500

@symptom_bp.route('/<symptom_id>', methods=['GET'])
def get_symptom_details(symptom_id):
    """Get detailed information about a specific symptom"""
    try:
        analyzer = get_symptom_analyzer()
        symptom = analyzer.get_symptom_by_id(symptom_id)
        
        if not symptom:
            return jsonify({'error': 'Symptom not found'}), 404
        
        return jsonify({
            'success': True,
            'symptom': symptom
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@symptom_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all symptom categories"""
    try:
        categories = analyzer.symptoms_data.get('categories', [])
        
        return jsonify({
            'success': True,
            'categories': categories
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@symptom_bp.route('/emergency-check', methods=['POST'])
def check_emergency():
    """Quick emergency symptom check"""
    try:
        data = request.get_json()
        
        if not data.get('symptoms'):
            return jsonify({'error': 'Symptoms description is required'}), 400
        
        symptoms_text = data['symptoms']
        language = data.get('language', 'english')
        
        # Analyze symptoms
        analysis_result = analyzer.analyze_symptoms(symptoms_text, language)
        
        # Check if emergency
        is_emergency = analysis_result['requires_emergency']
        urgency_level = analysis_result['urgency_level']
        
        return jsonify({
            'success': True,
            'is_emergency': is_emergency,
            'urgency_level': urgency_level,
            'urgency_score': analysis_result['urgency_score'],
            'message': 'Seek immediate medical attention' if is_emergency else 'Consult a doctor soon',
            'first_aid': analysis_result['first_aid_tips'],
            'red_flags': analysis_result['red_flags']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
