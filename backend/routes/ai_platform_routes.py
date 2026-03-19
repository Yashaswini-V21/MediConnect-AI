"""
AI Platform API Routes
RESTful endpoints for complete healthcare platform
"""

from flask import Blueprint, request, jsonify
from utils.triage_pipeline import get_triage_pipeline
from utils.safety_guardrails import create_safety_gate
from utils.unified_voice_engine import get_voice_engine
from utils.voice_output_assistant import get_voice_output_assistant
from utils.smart_maps_router import get_smart_router
from utils.reliability_metrics import get_reliability_metrics
from utils.healthcare_ai_platform import create_healthcare_ai_platform
import logging

logger = logging.getLogger(__name__)

ai_platform_bp = Blueprint('ai_platform', __name__)

# Initialize platform components
triage_pipeline = get_triage_pipeline()
safety_gate = create_safety_gate(triage_pipeline)
voice_engine = get_voice_engine()
voice_output = get_voice_output_assistant()
smart_router = get_smart_router()
metrics = get_reliability_metrics()

# Create platform
platform = create_healthcare_ai_platform(
    triage_pipeline,
    safety_gate,
    voice_engine,
    voice_output,
    smart_router,
    metrics
)


# ===== DIAGNOSTIC ENDPOINTS =====

@ai_platform_bp.route('/health/analyze', methods=['POST'])
def analyze_symptoms():
    """
    Comprehensive symptom analysis with triage and safety checks
    
    POST /api/ai/health/analyze
    {
        "symptoms": "chest pain radiating to left arm",
        "language": "en",
        "age": 45
    }
    """
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', '').strip()
        language = data.get('language', 'en')
        
        if not symptoms:
            return jsonify({'error': 'Symptoms required'}), 400
        
        result = platform.analyze_symptoms_text(symptoms)
        
        # Log to metrics
        if result['success'] and result['analysis'].get('triage'):
            metrics.log_triage_event(
                flow_id='web-analysis',
                risk_level=result['analysis']['triage'].get('risk_assessment', {}).get('risk_level', 'UNKNOWN'),
                latency_ms=0
            )
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Symptom analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_platform_bp.route('/health/emergency-check', methods=['POST'])
def emergency_check():
    """
    Quick emergency detection
    
    POST /api/ai/health/emergency-check
    {"symptoms": "severe chest pain"}
    """
    try:
        data = request.get_json()
        symptoms = data.get('symptoms', '').strip()
        
        if not symptoms:
            return jsonify({'error': 'Symptoms required'}), 400
        
        guidance = platform.get_emergency_guidance(symptoms)
        
        return jsonify(guidance), 200
    except Exception as e:
        logger.error(f"Emergency check error: {e}")
        return jsonify({'error': str(e)}), 500


# ===== VOICE ENDPOINTS =====

@ai_platform_bp.route('/voice/start', methods=['POST'])
def start_voice():
    """
    Start voice input capture
    
    POST /api/ai/voice/start
    {"language": "en-US"}
    """
    try:
        data = request.get_json() or {}
        language = data.get('language', 'en-US')
        
        result = platform.start_voice_input(language=language)
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Voice start error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_platform_bp.route('/voice/stop', methods=['POST'])
def stop_voice():
    """
    Stop voice input
    
    POST /api/ai/voice/stop
    """
    try:
        result = platform.stop_voice_input()
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Voice stop error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_platform_bp.route('/voice/speak', methods=['POST'])
def speak_response():
    """
    Speak response in selected language
    
    POST /api/ai/voice/speak
    {
        "text": "You need immediate medical attention",
        "language": "en-US"
    }
    """
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        language = data.get('language', 'en-US')
        
        if not text:
            return jsonify({'error': 'Text required'}), 400
        
        result = platform.speak_response(text, language=language)
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Speak error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_platform_bp.route('/voice/stop-speech', methods=['POST'])
def stop_speaking():
    """Stop current speech"""
    try:
        result = platform.stop_speech()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Stop speech error: {e}")
        return jsonify({'error': str(e)}), 500


# ===== ROUTING ENDPOINTS =====

@ai_platform_bp.route('/emergency/hospitals', methods=['POST'])
def find_hospitals():
    """
    Find nearby hospitals ranked by emergency relevance
    
    POST /api/ai/emergency/hospitals
    {
        "user_lat": 12.9716,
        "user_lng": 77.6412,
        "urgency": "CRITICAL"
    }
    """
    try:
        data = request.get_json()
        user_lat = data.get('user_lat')
        user_lng = data.get('user_lng')
        urgency = data.get('urgency', 'MODERATE')
        
        if user_lat is None or user_lng is None:
            return jsonify({'error': 'Location required'}), 400
        
        result = platform.find_nearest_hospitals(user_lat, user_lng, urgency)
        
        if result['success']:
            metrics.log_routing_event(
                flow_id='web-routing',
                hospitals_found=len(result.get('hospitals', [])),
                distance_to_nearest_km=result['hospitals'][0]['distance_km'] if result.get('hospitals') else 0,
                eta_minutes=result['hospitals'][0]['eta']['eta_minutes'] if result.get('hospitals') else 0
            )
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Hospital search error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_platform_bp.route('/emergency/route', methods=['POST'])
def get_route():
    """
    Get route to specific hospital
    
    POST /api/ai/emergency/route
    {
        "user_lat": 12.9716,
        "user_lng": 77.6412,
        "hospital_id": "hosp_001",
        "mode": "ambulance"
    }
    """
    try:
        data = request.get_json()
        user_lat = data.get('user_lat')
        user_lng = data.get('user_lng')
        hospital_id = data.get('hospital_id')
        mode = data.get('mode', 'ambulance')
        
        if not all([user_lat, user_lng, hospital_id]):
            return jsonify({'error': 'Required fields missing'}), 400
        
        result = platform.get_route_to_hospital(user_lat, user_lng, hospital_id, mode)
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Route error: {e}")
        return jsonify({'error': str(e)}), 500


# ===== ANALYTICS ENDPOINTS =====

@ai_platform_bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard():
    """Get system reliability dashboard"""
    try:
        dashboard = platform.get_reliability_dashboard()
        return jsonify(dashboard), 200
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_platform_bp.route('/analytics/metrics', methods=['GET'])
def get_metrics():
    """Get daily metrics"""
    try:
        date = request.args.get('date')  # Optional YYYY-MM-DD
        metrics_data = platform.get_daily_metrics(date)
        return jsonify(metrics_data), 200
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({'error': str(e)}), 500


# ===== HEALTH CHECK =====

@ai_platform_bp.route('/health', methods=['GET'])
def health_check():
    """System health check"""
    try:
        health = platform.health_check()
        return jsonify(health), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'error': str(e), 'status': 'unhealthy'}), 500
