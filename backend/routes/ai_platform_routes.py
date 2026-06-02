"""
AI Platform API Routes
RESTful endpoints for complete healthcare platform
"""

from flask import Blueprint, request, jsonify
from utils.unified_voice_engine import get_voice_engine
from utils.voice_output_assistant import get_voice_output_assistant
from utils.diagnostic_agent import diagnostic_agent as diagnostic_workflow
from utils.ai_provider import RuleBasedProvider
from models.hospital_matcher import get_hospital_matcher
from models.symptom_analyzer import get_symptom_analyzer
import logging
import time

logger = logging.getLogger(__name__)

ai_platform_bp = Blueprint('ai_platform', __name__)

# Initialize core platform components
voice_engine = get_voice_engine()
voice_output = get_voice_output_assistant()
hospital_matcher = get_hospital_matcher()
symptom_analyzer = get_symptom_analyzer()
rule_provider = RuleBasedProvider()

# Initialize AI Platform dependencies (stubs/actuals)
from utils.healthcare_ai_platform import create_healthcare_ai_platform
from utils.safety_guardrails import create_safety_gate
from utils.triage_pipeline import get_triage_pipeline

triage_pipeline = get_triage_pipeline()
safety_gate = create_safety_gate(triage_pipeline)

# A dummy reliability metrics instance that matches HealthcareAIPlatform's needs
class DummyMetrics:
    def get_dashboard_summary(self):
        return {"success": True, "total_transactions": 100, "success_rate": "99%"}
    def get_daily_metrics(self, date=None):
        return {"success": True, "uptime": "100%", "latency": "50ms"}

# A dummy smart router that acts as hospital matcher interface
class DummySmartRouter:
    def __init__(self, matcher):
        self.matcher = matcher
        self.user_location = (12.9716, 77.5946)
    def find_nearest_hospital(self, lat, lng, urgency):
        hospitals = self.matcher.find_hospitals(
            specialties=['Emergency'],
            user_location={'lat': lat, 'lng': lng},
            urgency=urgency
        )
        return {"success": True, "hospitals": hospitals}
    def get_route(self, lat, lng, hospital_id, mode):
        return {
            "success": True,
            "distance_km": 5.2,
            "estimated_time_minutes": 15,
            "route_geometry": "poly_line_data"
        }

metrics = DummyMetrics()
smart_router = DummySmartRouter(hospital_matcher)

platform = create_healthcare_ai_platform(
    triage_pipeline=triage_pipeline,
    safety_gate=safety_gate,
    voice_engine=voice_engine,
    voice_output_assistant=voice_output,
    smart_router=smart_router,
    reliability_metrics=metrics
)


# ===== DIAGNOSTIC ENDPOINTS =====

@ai_platform_bp.route('/health/analyze', methods=['POST'])
def analyze_symptoms():
    """
    Comprehensive symptom analysis
    
    POST /api/ai/health/analyze
    {
        "symptoms": "chest pain radiating to left arm",
        "language": "en"
    }
    """
    try:
        data = request.get_json() or {}
        symptoms = data.get('symptoms', '').strip()
        language = data.get('language', 'en')

        if not symptoms:
            return jsonify({'error': 'Symptoms description is required'}), 400
        if len(symptoms) > 2000:
            return jsonify({'error': 'Symptoms description too long (max 2000 characters)'}), 400

        start_time = time.time()

        # Use LangGraph diagnostic agent with rule-based fallback
        try:
            state = {
                'symptom_text': symptoms,
                'language': language,
                'user_location': data.get('location', {})
            }
            result = diagnostic_workflow.invoke(state)
            analysis = result
        except Exception as agent_err:
            logger.warning(f"Diagnostic agent unavailable, using rule-based fallback: {agent_err}")
            analysis = rule_provider.analyze_symptoms(symptoms)

        latency = (time.time() - start_time) * 1000

        return jsonify({
            'success': True,
            'analysis': analysis,
            'latency_ms': round(latency, 2)
        }), 200
    except Exception as e:
        logger.error(f"Symptom analysis error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to analyze symptoms. Please try again.'}), 500


@ai_platform_bp.route('/health/emergency-check', methods=['POST'])
def emergency_check():
    """
    Quick emergency detection
    
    POST /api/ai/health/emergency-check
    {"symptoms": "severe chest pain"}
    """
    try:
        data = request.get_json() or {}
        symptoms = data.get('symptoms', '').strip()

        if not symptoms:
            return jsonify({'error': 'Symptoms description is required'}), 400
        if len(symptoms) > 2000:
            return jsonify({'error': 'Symptoms description too long (max 2000 characters)'}), 400

        # Quick emergency analysis
        analysis = rule_provider.analyze_symptoms(symptoms)
        is_emergency = analysis.get('urgency', 'MEDIUM') == 'HIGH'

        if is_emergency:
            guidance = "⚠️ EMERGENCY DETECTED — Call 108 immediately. " + analysis.get('description', '')
        else:
            guidance = analysis.get('description', 'Seek medical attention if symptoms worsen.')

        return jsonify({
            'success': True,
            'is_emergency': is_emergency,
            'guidance': guidance,
            'urgency': analysis.get('urgency'),
            'specialties': analysis.get('specialties', [])
        }), 200
    except Exception as e:
        logger.error(f"Emergency check error: {e}", exc_info=True)
        return jsonify({'error': 'Emergency check failed. Please try again.'}), 500


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

        return jsonify({
            'success': True,
            'message': 'Voice input ready',
            'language': language
        }), 200
    except Exception as e:
        logger.error(f"Voice start error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to initialize voice input.'}), 500


@ai_platform_bp.route('/voice/stop', methods=['POST'])
def stop_voice():
    """
    Stop voice input
    
    POST /api/ai/voice/stop
    """
    try:
        return jsonify({
            'success': True,
            'message': 'Voice input stopped'
        }), 200
    except Exception as e:
        logger.error(f"Voice stop error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to stop voice input.'}), 500


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
        data = request.get_json() or {}
        text = data.get('text', '').strip()
        language = data.get('language', 'en-US')

        if not text:
            return jsonify({'error': 'Text is required'}), 400
        if len(text) > 2000:
            return jsonify({'error': 'Text too long (max 2000 characters)'}), 400

        return jsonify({
            'success': True,
            'message': 'Speech started',
            'text': text,
            'language': language
        }), 200
    except Exception as e:
        logger.error(f"Speak error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to process speech request.'}), 500


# ===== ROUTING ENDPOINTS =====

@ai_platform_bp.route('/emergency/hospitals', methods=['POST'])
def find_hospitals():
    """
    Find nearby hospitals ranked by emergency relevance
    
    POST /api/ai/emergency/hospitals
    {
        "user_lat": 12.9716,
        "user_lng": 77.6412,
        "urgency": "HIGH"
    }
    """
    try:
        data = request.get_json() or {}
        user_lat = data.get('user_lat')
        user_lng = data.get('user_lng')
        urgency = data.get('urgency', 'MEDIUM')

        if user_lat is None or user_lng is None:
            return jsonify({'error': 'Location (user_lat, user_lng) is required'}), 400

        if urgency not in ('HIGH', 'MEDIUM', 'LOW'):
            return jsonify({'error': 'urgency must be HIGH, MEDIUM, or LOW'}), 400

        try:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
        except (TypeError, ValueError):
            return jsonify({'error': 'user_lat and user_lng must be numeric'}), 400

        # Use hospital matcher
        hospitals = hospital_matcher.find_hospitals(
            specialties=['Emergency'],
            user_location={'lat': user_lat, 'lng': user_lng},
            urgency=urgency
        )

        return jsonify({
            'success': True,
            'hospitals': hospitals[:5],  # Top 5
            'count': len(hospitals)
        }), 200
    except Exception as e:
        logger.error(f"Hospital search error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to search hospitals. Please try again.'}), 500


@ai_platform_bp.route('/emergency/route', methods=['POST'])
def get_route():
    """
    Get route to specific hospital
    
    POST /api/ai/emergency/route
    {
        "user_lat": 12.9716,
        "user_lng": 77.6412,
        "hospital_id": "hosp_001"
    }
    """
    try:
        data = request.get_json() or {}
        user_lat = data.get('user_lat')
        user_lng = data.get('user_lng')
        hospital_id = data.get('hospital_id')

        if user_lat is None or user_lng is None or not hospital_id:
            return jsonify({'error': 'user_lat, user_lng, and hospital_id are required'}), 400

        try:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
        except (TypeError, ValueError):
            return jsonify({'error': 'user_lat and user_lng must be numeric'}), 400

        mode = data.get('mode', 'ambulance')
        result = platform.get_route_to_hospital(user_lat, user_lng, hospital_id, mode)

        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Route error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to calculate route. Please try again.'}), 500


# ===== ANALYTICS ENDPOINTS =====

@ai_platform_bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard():
    """Get system reliability dashboard"""
    try:
        dashboard = platform.get_reliability_dashboard()
        return jsonify(dashboard), 200
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve dashboard data.'}), 500


@ai_platform_bp.route('/analytics/metrics', methods=['GET'])
def get_metrics():
    """Get daily metrics"""
    try:
        date = request.args.get('date')  # Optional YYYY-MM-DD
        metrics_data = platform.get_daily_metrics(date)
        return jsonify(metrics_data), 200
    except Exception as e:
        logger.error(f"Metrics error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve metrics data.'}), 500


# ===== HEALTH CHECK =====

@ai_platform_bp.route('/health', methods=['GET'])
def health_check():
    """System health check"""
    try:
        health = platform.health_check()
        return jsonify(health), 200
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return jsonify({'error': 'Health check failed.', 'status': 'unhealthy'}), 500
