"""
MediConnect-AI API Versioning System
Allows multiple API versions to coexist without breaking clients
"""

from functools import wraps
from flask import Blueprint, request, jsonify, __version__ as flask_version
import logging

logger = logging.getLogger(__name__)


class APIVersion:
    """API version enum"""
    V1 = 'v1'
    V2 = 'v2'
    
    CURRENT = V1
    SUPPORTED = [V1, V2]


class VersionedAPI:
    """
    Manages multiple API versions.
    
    Usage:
        versioned_api = VersionedAPI()
        
        @versioned_api.route('/appointments', methods=['GET'], versions=['v1', 'v2'])
        def get_appointments():
            ...
    """
    
    def __init__(self):
        self.blueprints = {}
        self.version_routes = {}
    
    def create_versioned_blueprint(self, version):
        """Create blueprint for specific API version"""
        bp = Blueprint(
            f'api_{version}',
            __name__,
            url_prefix=f'/api/{version}'
        )
        self.blueprints[version] = bp
        self.version_routes[version] = {}
        return bp
    
    def register_blueprints(self, app):
        """Register all version blueprints to Flask app"""
        for version, bp in self.blueprints.items():
            app.register_blueprint(bp)
            logger.info(f"✅ Registered API version {version}")
    
    def deprecated(self, version, replacement_version, message=""):
        """
        Mark a route as deprecated in a specific version.
        
        Usage:
            @v1_api.route('/old-endpoint')
            @versioned_api.deprecated('v1', 'v2', 'Use /api/v2/new-endpoint instead')
            def old_endpoint():
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Add deprecation header
                from flask import make_response
                response = make_response(func(*args, **kwargs))
                response.headers['Deprecation'] = 'true'
                response.headers['Sunset'] = 'Sun, 01 Jan 2027 00:00:00 GMT'
                response.headers['Link'] = f'</api/{replacement_version}>; rel="successor-version"'
                
                logger.warning(
                    f"Deprecated endpoint called: {request.path} "
                    f"(use /api/{replacement_version} instead)"
                )
                
                return response
            
            return wrapper
        return decorator


# ════════════════════════════════════════════════════════════════════════════════
# API VERSIONING SETUP
# ════════════════════════════════════════════════════════════════════════════════

def setup_api_versioning(app):
    """
    Setup API versioning in Flask app.
    
    Usage in app.py:
        from utils.api_versioning import setup_api_versioning
        setup_api_versioning(app)
    
    Provides:
    - /api/v1/* - Current stable API
    - /api/v2/* - Next version (in development)
    - /api/health - Current version health check
    - /api/versions - List available versions
    """
    
    # Create versioned blueprints
    v1_api = Blueprint('v1', __name__, url_prefix='/api/v1')
    v2_api = Blueprint('v2', __name__, url_prefix='/api/v2')
    
    # V1 Routes (Stable)
    @v1_api.route('/appointments', methods=['GET'])
    def v1_get_appointments():
        """GET /api/v1/appointments - List appointments (V1)"""
        return {'message': 'V1 appointments endpoint'}
    
    @v1_api.route('/appointments', methods=['POST'])
    def v1_create_appointment():
        """POST /api/v1/appointments - Create appointment (V1)"""
        return {'message': 'V1 create appointment endpoint'}, 201
    
    # V2 Routes (Future - with improvements)
    @v2_api.route('/appointments', methods=['GET'])
    def v2_get_appointments():
        """GET /api/v2/appointments - List appointments (V2, improved)"""
        # V2 could have better filtering, pagination, etc.
        return {'message': 'V2 appointments endpoint', 'features': ['pagination', 'filtering']}
    
    # Register blueprints
    app.register_blueprint(v1_api)
    app.register_blueprint(v2_api)
    
    # API metadata endpoint
    @app.route('/api/versions', methods=['GET'])
    def list_versions():
        """List all available API versions"""
        return {
            'current': APIVersion.CURRENT,
            'supported': APIVersion.SUPPORTED,
            'deprecated': [],
            'endpoints': {
                'v1': {
                    'status': 'stable',
                    'base_url': 'https://mediconnect.health/api/v1',
                    'endpoints': [
                        'GET /appointments',
                        'POST /appointments',
                        'GET /hospitals/search',
                    ]
                },
                'v2': {
                    'status': 'beta',
                    'base_url': 'https://mediconnect.health/api/v2',
                    'endpoints': [
                        'GET /appointments?page=1&limit=20',
                        'POST /appointments (with validation)',
                        'GET /hospitals/search (improved)',
                    ]
                }
            }
        }
    
    logger.info("✅ API versioning setup complete")
    logger.info(f"   Available versions: {APIVersion.SUPPORTED}")
    logger.info(f"   Current version: {APIVersion.CURRENT}")


# ════════════════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY HELPERS
# ════════════════════════════════════════════════════════════════════════════════

def v1_to_v2_migration_guide():
    """
    Migration guide for API consumers updating from V1 to V2.
    """
    return """
    ═════════════════════════════════════════════════════════════════
    MediConnect-AI API V1 → V2 Migration Guide
    ═════════════════════════════════════════════════════════════════
    
    BREAKING CHANGES:
    ─────────────────
    
    1. Pagination now required for list endpoints
       
       V1: GET /api/v1/appointments
           Returns all appointments (could be 10,000+)
       
       V2: GET /api/v2/appointments?page=1&limit=20
           Returns paginated results (default 20 per page)
           
       Migration:
           Add ?page=1&limit=50 to your requests
           Handle "has_next" and "has_prev" in response
    
    2. Error response format changed
       
       V1: {"error": "Bad request"}
       
       V2: {"error": "Bad request", "code": "VALIDATION_ERROR", "details": {...}}
       
       Migration:
           Update error handling to check "code" field instead of "error"
    
    3. Timestamps now ISO 8601 format (no change if already parsing datetime)
       
       V1: "created_at": "2026-05-26 14:30:00"
       V2: "created_at": "2026-05-26T14:30:00Z"
       
       Migration:
           Update datetime parsing to handle ISO format
    
    NON-BREAKING IMPROVEMENTS:
    ──────────────────────────
    
    ✅ Rate limit headers now include retry-after
    ✅ New filtering options on list endpoints
    ✅ Response time improved (added caching)
    ✅ Better error messages with helpful suggestions
    
    DEPRECATION TIMELINE:
    ────────────────────
    
    - 2026-06-01: V1 still supported
    - 2026-09-01: V1 will return deprecation headers
    - 2027-01-01: V1 will be sunset (disabled)
    
    SUPPORT:
    ────────
    
    Questions? Email: support@mediconnect.health
    Docs: https://mediconnect.health/docs
    """


# ════════════════════════════════════════════════════════════════════════════════
# CLIENT VERSION HEADER DETECTION
# ════════════════════════════════════════════════════════════════════════════════

def detect_client_version():
    """
    Detect which API version client is using.
    Called automatically by middleware.
    """
    
    from flask import request
    
    # Check request path
    if '/api/v1/' in request.path:
        return 'v1'
    elif '/api/v2/' in request.path:
        return 'v2'
    
    # Check Accept-Version header
    version_header = request.headers.get('Accept-Version')
    if version_header in APIVersion.SUPPORTED:
        return version_header
    
    # Default to current
    return APIVersion.CURRENT


def add_version_info_to_response(app):
    """
    Add API version info to every response.
    """
    
    @app.after_request
    def add_version_headers(response):
        version = detect_client_version()
        response.headers['API-Version'] = version
        response.headers['API-Supported-Versions'] = ', '.join(APIVersion.SUPPORTED)
        return response
    
    logger.info("✅ Version info headers added to all responses")


# ════════════════════════════════════════════════════════════════════════════════
# VERSION DEPRECATION TRACKING
# ════════════════════════════════════════════════════════════════════════════════

DEPRECATION_SCHEDULE = {
    'v0.9': {
        'deprecated_date': '2026-01-01',
        'sunset_date': '2026-04-01',
        'replacement': 'v1'
    },
    'v1': {
        'deprecated_date': '2026-09-01',
        'sunset_date': '2027-01-01',
        'replacement': 'v2'
    }
}

def check_version_deprecation(version):
    """
    Check if an API version is deprecated.
    Returns deprecation info if applicable.
    """
    if version in DEPRECATION_SCHEDULE:
        return DEPRECATION_SCHEDULE[version]
    return None
