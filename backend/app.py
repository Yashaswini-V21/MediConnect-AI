from flask import Flask, request, jsonify
import sys
from pathlib import Path

# Ensure `backend/` is on sys.path so imports like `utils.*` and `models.*` work
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta, datetime, timezone
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import text
from utils.auth_middleware import get_authenticated_user_id

# Load environment variables
load_dotenv()

# Import models and routes
from models.user_model import db, bcrypt, User, SearchHistory
from models.symptom_analyzer import get_symptom_analyzer
from models.hospital_matcher import get_hospital_matcher
from routes.auth_routes import auth_bp
from routes.symptom_routes import symptom_bp
from routes.hospital_routes import hospital_bp
from routes.appointment_routes import appointment_bp
from routes.chat_routes import chat_bp
from routes.ai_platform_routes import ai_platform_bp
from routes.admin_routes import admin_bp
from routes.wellness_routes import wellness_bp
from utils.security import add_security_headers, limiter, check_admin_token_security

# M3 admin models — import so SQLAlchemy registers the tables
import models.admin_model  # noqa: F401
import models.analytics_model  # noqa: F401
import utils.security as security_utils  # noqa: F401

# Initialize Flask app
app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================

app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or os.getenv('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # Reduced from 7 days for security
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///mediconnect.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1 MB max request body

# SQLAlchemy connection pool settings for production
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,     # Verify connections before use
    'pool_recycle': 300,       # Recycle connections every 5 minutes
}

# Security headers
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ============================================
# INITIALIZE EXTENSIONS
# ============================================

db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)
limiter.init_app(app)

# Initialize analyzers
symptom_analyzer = get_symptom_analyzer()
hospital_matcher = get_hospital_matcher()

# ============================================
# CORS CONFIGURATION
# ============================================

# Allow all Vercel domains and localhost by default; can be overridden by ALLOWED_ORIGINS
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://mediconnect-ai-nu.vercel.app"
]

# Get additional origins from environment variable (comma-separated)
env_origins = os.getenv('ALLOWED_ORIGINS', '')
if env_origins:
    allowed_origins = [o.strip() for o in env_origins.split(',') if o.strip()]

# In production prefer explicit allowed_origins; in development allow wildcard for convenience
cors_origins = allowed_origins if os.getenv('FLASK_ENV') == 'production' else "*"

CORS(app,
     resources={r"/api/*": {"origins": cors_origins}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Content-Type", "Authorization"]
)

from extensions import socketio

# Initialize Socket.IO (threading mode is compatible with Python 3.14 here)
socketio.init_app(
    app,
    async_mode=os.getenv('SOCKETIO_ASYNC_MODE', 'threading'),
    message_queue=os.getenv('REDIS_URL') or None,
    cors_allowed_origins=cors_origins,
)

# ============================================
# LOGGING CONFIGURATION
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Production-time environment checks: ensure critical secrets are configured
if os.getenv('FLASK_ENV') == 'production':
    missing = [k for k in ('SECRET_KEY', 'JWT_SECRET_KEY', 'ADMIN_SECRET_TOKEN') if not os.getenv(k)]
    if missing:
        logger.error(f"Missing required environment variables for production: {', '.join(missing)}")
        raise SystemExit(1)

# Always warn if admin token is insecure
check_admin_token_security()

# ============================================
# REGISTER BLUEPRINTS
# ============================================

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(symptom_bp, url_prefix='/api/symptoms')
app.register_blueprint(hospital_bp, url_prefix='/api/hospitals')
app.register_blueprint(appointment_bp, url_prefix='/api/appointments')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(ai_platform_bp, url_prefix='/api/ai')
app.register_blueprint(admin_bp, url_prefix='/api/admin')  # M3: Admin portal
app.register_blueprint(wellness_bp, url_prefix='/api/wellness')  # Wellness Score

# ============================================
# CREATE DATABASE TABLES
# ============================================

with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully")

# Apply security headers to every response
@app.after_request
def apply_security_headers(response):
    return add_security_headers(response)

# ============================================
# HEALTH CHECK & INFO ROUTES
# ============================================

@app.route('/')
def index():
    """Root endpoint with API information"""
    return jsonify({
        'message': 'MediConnect AI Backend API',
        'version': '1.0.0',
        'status': 'running',
        'description': 'Production-grade healthcare SaaS: ML-powered urgency detection, Groq LLaMA integration, multi-language support, real-time hospital matching',
        'endpoints': {
            'health': '/api/health',
            'auth': '/api/auth/*',
            'symptoms': '/api/analyze-symptoms',
            'hospitals_search': '/api/hospitals/search',
            'hospitals_emergency': '/api/hospitals/emergency',
            'hospitals_details': '/api/hospitals/<hospital_id>',
            'translate': '/api/translate'
        },
        'documentation': 'See README.md for complete API documentation'
    }), 200


@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'symptom_analyzer': 'active' if symptom_analyzer.symptoms_data else 'no data',
        'hospital_matcher': 'active' if hospital_matcher.hospitals else 'no data',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# ============================================
# ANALYTICS ROUTES (for Imagine Cup Demo!)
# ============================================

@app.route('/api/analytics/stats', methods=['GET'])
def get_analytics_stats():
    """Get comprehensive analytics statistics — requires admin token."""
    # Protect analytics from unauthenticated access
    admin_token = request.headers.get('X-Admin-Token', '')
    expected = os.getenv('ADMIN_SECRET_TOKEN', '')
    if not expected or admin_token != expected:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from utils.analytics import analytics
        stats = analytics.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        logger.error(f"Error getting analytics: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve analytics data.'}), 500


@app.route('/api/analytics/dashboard', methods=['GET'])
def get_analytics_dashboard():
    """Get simplified analytics for dashboard display — requires admin token."""
    # Protect analytics from unauthenticated access
    admin_token = request.headers.get('X-Admin-Token', '')
    expected = os.getenv('ADMIN_SECRET_TOKEN', '')
    if not expected or admin_token != expected:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from utils.analytics import analytics
        stats = analytics.get_dashboard_stats()
        return jsonify({
            'success': True,
            'dashboard': stats
        }), 200
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {e}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve dashboard data.'}), 500


# ============================================
# SYMPTOM ANALYSIS ROUTES
# ============================================

@app.route('/api/analyze-symptoms', methods=['POST'])
def analyze_symptoms():
    """
    Analyze user symptoms and provide recommendations
    
    Request body:
    {
        "symptoms": "chest pain and difficulty breathing",
        "language": "en" (optional, default: "en")
    }
    
    Response:
    {
        "urgency": "HIGH",
        "urgency_score": 9,
        "matched_symptoms": ["Chest Pain", "Shortness of Breath"],
        "specialties": ["Cardiology", "Emergency Medicine"],
        "description": "...",
        "first_aid": [...],
        "red_flags": [...]
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('symptoms'):
            return jsonify({
                'error': 'Symptoms are required',
                'message': 'Please provide symptoms description in the request body'
            }), 400
        
        symptoms_text = data['symptoms'].strip()
        language = data.get('language', 'en')
        
        # Validate language
        if language not in ['en', 'kn', 'hi', 'ta']:
            return jsonify({
                'error': 'Invalid language',
                'message': 'Supported languages: en, kn, hi, ta'
            }), 400
        
        if len(symptoms_text) < 3:
            return jsonify({
                'error': 'Symptoms too short',
                'message': 'Please provide more detailed symptoms (at least 3 characters)'
            }), 400
        
        # Analyze symptoms
        logger.info(f"Analyzing symptoms: {symptoms_text[:50]}... (language: {language})")
        analysis_result = symptom_analyzer.analyze(symptoms_text, language)
        
        # Save to search history if user is logged in
        try:
            user_id = get_authenticated_user_id(optional=True)
            
            if user_id:
                history_entry = SearchHistory(
                    user_id=user_id,
                    symptoms=symptoms_text,
                    urgency_level=analysis_result.get('urgency_level', analysis_result.get('urgency', 'LOW')),
                    specialties=','.join(analysis_result.get('recommended_specialties', analysis_result.get('specialties', [])))
                )
                db.session.add(history_entry)
                db.session.commit()
                logger.info(f"Saved search history for user {user_id}")
        except Exception as e:
            logger.warning(f"Could not save search history: {e}")
            # Continue even if saving history fails
        
        return jsonify(analysis_result), 200
        
    except Exception as e:
        logger.error(f"Error analyzing symptoms: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Analysis failed',
            'message': 'An error occurred while analyzing symptoms. Please try again.'
        }), 500


# ============================================
# HOSPITAL SEARCH ROUTES
# ============================================

@app.route('/api/hospitals/search', methods=['POST'])
def search_hospitals():
    """
    Find hospitals based on symptoms analysis and location
    
    Request body:
    {
        "specialties": ["Cardiology", "Emergency Medicine"],
        "location": {"lat": 12.9716, "lng": 77.5946},
        "urgency": "HIGH" (optional, default: "MEDIUM"),
        "filters": {
            "type": "Private" (optional),
            "emergency_only": true (optional),
            "max_distance": 10 (optional),
            "availability_24_7": true (optional)
        }
    }
    
    Response:
    {
        "success": true,
        "urgency": "HIGH",
        "total_results": 10,
        "hospitals": [
            {
                "id": "apollo-bangalore",
                "name": "Apollo Hospital",
                "distance_km": 5.2,
                "estimated_time_minutes": 18,
                "match_score": 98.0,
                "score_breakdown": {...},
                ...
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                'error': 'Request body is required',
                'message': 'Please provide search parameters'
            }), 400
        
        specialties = data.get('specialties', [])
        user_location = data.get('location')
        urgency = data.get('urgency', 'MEDIUM')
        filters = data.get('filters', {})
        
        # Validate urgency level
        if urgency not in ['HIGH', 'MEDIUM', 'LOW']:
            return jsonify({
                'error': 'Invalid urgency level',
                'message': 'Urgency must be HIGH, MEDIUM, or LOW'
            }), 400
        
        # Use Bangalore center as default if location not provided
        if not user_location:
            user_location = {'lat': 12.9716, 'lng': 77.5946}
            logger.warning("No location provided, using Bangalore center as default")
        
        # Validate location format
        if 'lat' not in user_location or 'lng' not in user_location:
            return jsonify({
                'error': 'Invalid location format',
                'message': 'Location must include lat and lng coordinates'
            }), 400
        
        # Find matching hospitals
        logger.info(f"Searching hospitals: specialties={specialties}, urgency={urgency}, filters={filters}")
        hospitals = hospital_matcher.find_hospitals(
            specialties=specialties,
            user_location=user_location,
            urgency=urgency,
            filters=filters
        )
        
        return jsonify({
            'success': True,
            'urgency': urgency,
            'total_results': len(hospitals),
            'hospitals': hospitals
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching hospitals: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Search failed',
            'message': 'An error occurred while searching hospitals. Please try again.'
        }), 500


@app.route('/api/hospitals/emergency', methods=['POST'])
def find_emergency_hospitals():
    """
    Find nearest emergency hospitals
    
    Request body:
    {
        "location": {"lat": 12.9716, "lng": 77.5946},
        "max_results": 5 (optional, default: 5)
    }
    
    Response:
    {
        "success": true,
        "total_results": 5,
        "message": "Found 5 emergency hospitals nearby",
        "hospitals": [
            {
                "id": "manipal-bangalore",
                "name": "Manipal Hospital",
                "distance_km": 3.2,
                "estimated_time_minutes": 10,
                "emergency_available": true,
                ...
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('location'):
            return jsonify({
                'error': 'Location is required',
                'message': 'Please provide your location for emergency search'
            }), 400
        
        user_location = data['location']
        
        # Validate location format
        if 'lat' not in user_location or 'lng' not in user_location:
            return jsonify({
                'error': 'Invalid location format',
                'message': 'Location must include lat and lng coordinates'
            }), 400
        
        max_results = data.get('max_results', 5)
        
        # Validate max_results
        if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
            return jsonify({
                'error': 'Invalid max_results',
                'message': 'max_results must be an integer between 1 and 20'
            }), 400
        
        # Find emergency hospitals
        logger.info(f"Finding emergency hospitals near {user_location}")
        hospitals = hospital_matcher.find_emergency_hospitals(
            user_location=user_location,
            max_results=max_results
        )
        
        if not hospitals:
            return jsonify({
                'success': True,
                'total_results': 0,
                'hospitals': [],
                'message': 'No emergency hospitals found nearby. Please call 108 (India) or local emergency number for immediate assistance.'
            }), 200
        
        return jsonify({
            'success': True,
            'total_results': len(hospitals),
            'message': f'Found {len(hospitals)} emergency hospital{"s" if len(hospitals) != 1 else ""} nearby',
            'hospitals': hospitals,
            'emergency_numbers': {
                'india': '108',
                'ambulance': '102',
                'police': '100'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error finding emergency hospitals: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Emergency search failed',
            'message': 'An error occurred while finding emergency hospitals. Please call 108 immediately.'
        }), 500


@app.route('/api/hospitals/<hospital_id>', methods=['GET'])
def get_hospital_details(hospital_id):
    """
    Get detailed information about a specific hospital
    
    Response:
    {
        "success": true,
        "hospital": {
            "id": "apollo-bangalore",
            "name": "Apollo Hospital",
            ...
        }
    }
    """
    try:
        hospital = hospital_matcher.get_hospital_by_id(hospital_id)
        
        if not hospital:
            return jsonify({
                'error': 'Hospital not found',
                'message': f'No hospital found with ID: {hospital_id}'
            }), 404
        
        return jsonify({
            'success': True,
            'hospital': hospital
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting hospital details: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve hospital',
            'message': 'An error occurred while fetching hospital details'
        }), 500


@app.route('/api/hospitals/specialty/<specialty>', methods=['GET'])
def get_hospitals_by_specialty(specialty):
    """
    Get all hospitals offering a specific specialty
    
    Response:
    {
        "success": true,
        "specialty": "Cardiology",
        "total_results": 15,
        "hospitals": [...]
    }
    """
    try:
        hospitals = hospital_matcher.get_hospitals_by_specialty(specialty)
        
        return jsonify({
            'success': True,
            'specialty': specialty,
            'total_results': len(hospitals),
            'hospitals': hospitals
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting hospitals by specialty: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve hospitals',
            'message': 'An error occurred while fetching hospitals'
        }), 500


@app.route('/api/hospitals/stats', methods=['GET'])
def get_hospital_stats():
    """
    Get hospital database statistics
    
    Response:
    {
        "success": true,
        "statistics": {
            "total_hospitals": 40,
            "emergency_available": 25,
            "open_24_7": 18,
            ...
        }
    }
    """
    try:
        stats = hospital_matcher.get_hospital_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting hospital statistics: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve statistics',
            'message': 'An error occurred while fetching hospital statistics'
        }), 500


# ============================================
# TRANSLATION ROUTE (OPTIONAL)
# ============================================

@app.route('/api/translate', methods=['POST'])
def translate_text():
    """
    Translate text between English and regional languages
    
    Request body:
    {
        "text": "chest pain",
        "target_language": "kn" (kn/hi/ta)
    }
    
    Response:
    {
        "success": true,
        "original": "chest pain",
        "translated": "ಎದೆ ನೋವು",
        "source_language": "en",
        "target_language": "kn"
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('text'):
            return jsonify({
                'error': 'Text is required',
                'message': 'Please provide text to translate'
            }), 400
        
        from utils.translator import translate, detect_language, get_supported_languages

        text = data['text']
        target = data.get('target_language', 'kn')

        if target not in ['kn', 'hi', 'ta', 'en', 'kannada', 'hindi', 'tamil', 'english']:
            return jsonify({
                'error': 'Invalid target language',
                'message': f'Supported languages: {", ".join(get_supported_languages())}'
            }), 400

        source = data.get('source_language') or detect_language(text)
        translated = translate(text, from_lang=source, to_lang=target)
        
        return jsonify({
            'success': True,
            'original': text,
            'translated': translated,
            'source_language': source,
            'target_language': target
        }), 200
        
    except Exception as e:
        logger.error(f"Error translating text: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Translation failed',
            'message': 'An error occurred during translation'
        }), 500


# ============================================
# COMBINED SEARCH ROUTE (Symptoms + Hospitals)
# ============================================

@app.route('/api/search', methods=['POST'])
def combined_search():
    """
    Combined endpoint: Analyze symptoms and find hospitals in one call
    
    Request body:
    {
        "symptoms": "chest pain and difficulty breathing",
        "language": "en",
        "location": {"lat": 12.9716, "lng": 77.5946},
        "filters": {...}
    }
    
    Response:
    {
        "success": true,
        "symptom_analysis": {...},
        "hospitals": [...]
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('symptoms'):
            return jsonify({
                'error': 'Symptoms are required',
                'message': 'Please provide symptoms for analysis'
            }), 400
        
        symptoms_text = data['symptoms'].strip()
        language = data.get('language', 'en')
        user_location = data.get('location', {'lat': 12.9716, 'lng': 77.5946})
        filters = data.get('filters', {})
        
        # Step 1: Analyze symptoms
        analysis_result = symptom_analyzer.analyze(symptoms_text, language)
        
        # Step 2: Find hospitals based on analysis
        specialties = analysis_result.get('recommended_specialties', analysis_result.get('specialties', ['General Medicine']))
        urgency = analysis_result.get('urgency_level', analysis_result.get('urgency', 'MEDIUM'))
        
        hospitals = hospital_matcher.find_hospitals(
            specialties=specialties,
            user_location=user_location,
            urgency=urgency,
            filters=filters
        )
        
        # Save to search history if user is logged in
        try:
            user_id = get_authenticated_user_id(optional=True)
            
            if user_id:
                history_entry = SearchHistory(
                    user_id=user_id,
                    symptoms=symptoms_text,
                    urgency_level=urgency,
                    specialties=','.join(specialties)
                )
                db.session.add(history_entry)
                db.session.commit()
        except Exception as history_err:
            logger.warning(f"Could not save search history: {history_err}")
        
        return jsonify({
            'success': True,
            'symptom_analysis': analysis_result,
            'hospitals': {
                'total_results': len(hospitals),
                'urgency': urgency,
                'results': hospitals
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in combined search: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Search failed',
            'message': 'An error occurred during the search'
        }), 500


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist',
        'status': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred. Please try again later.',
        'status': 500
    }), 500


@app.errorhandler(400)
def bad_request(error):
    """Handle 400 errors"""
    return jsonify({
        'error': 'Bad request',
        'message': 'The request was invalid or cannot be served',
        'status': 400
    }), 400


@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 errors"""
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Authentication is required to access this resource',
        'status': 401
    }), 401


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    return jsonify({
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource',
        'status': 403
    }), 403


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The HTTP method is not allowed for this endpoint',
        'status': 405
    }), 405


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle 413 Payload Too Large errors"""
    return jsonify({
        'error': 'Request too large',
        'message': 'Request body exceeds the maximum allowed size (1MB)',
        'status': 413
    }), 413


@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle 429 Too Many Requests errors"""
    return jsonify({
        'error': 'Too many requests',
        'message': 'Rate limit exceeded. Please slow down and try again later.',
        'status': 429
    }), 429


# ============================================
# JWT ERROR HANDLERS
# ============================================

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired JWT tokens"""
    return jsonify({
        'error': 'Token has expired',
        'message': 'Your session has expired. Please login again.'
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Handle invalid JWT tokens"""
    return jsonify({
        'error': 'Invalid token',
        'message': 'The provided token is invalid. Please login again.'
    }), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    """Handle missing JWT tokens"""
    return jsonify({
        'error': 'Authorization required',
        'message': 'Please provide a valid access token to access this resource.'
    }), 401


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    """Handle revoked JWT tokens"""
    return jsonify({
        'error': 'Token has been revoked',
        'message': 'This token is no longer valid. Please login again.'
    }), 401


# ============================================
# BEFORE REQUEST HOOKS
# ============================================

@app.before_request
def log_request():
    """Log all incoming requests"""
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")


@app.after_request
def after_request(response):
    """Add security headers to all responses (single unified handler)"""
    return add_security_headers(response)


# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting MediConnect AI Backend on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    logger.info(f"CORS origins: http://localhost:3000, http://localhost:3001")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
