"""
MediConnect-AI Monitoring & Error Tracking Setup
Real-time error alerting with Sentry + Datadog metrics
"""

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import logging
import os
from datetime import datetime
from functools import wraps


# ════════════════════════════════════════════════════════════════════════════════
# SENTRY SETUP (Production Error Tracking)
# ════════════════════════════════════════════════════════════════════════════════

def init_sentry(app):
    """
    Initialize Sentry for real-time error tracking.
    
    Steps:
    1. Create Sentry account: https://sentry.io
    2. Create project: Select Flask + Python
    3. Copy your DSN (Data Source Name)
    4. Set SENTRY_DSN environment variable
    
    Usage in app.py:
        from utils.monitoring import init_sentry
        init_sentry(app)
    """
    
    sentry_dsn = os.getenv('SENTRY_DSN')
    
    if not sentry_dsn:
        print("⚠️  SENTRY_DSN not set. Skipping Sentry initialization.")
        return
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FlaskIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of requests sampled
        environment=os.getenv('FLASK_ENV', 'development'),
        release=os.getenv('APP_VERSION', '2.0.0'),
        debug=os.getenv('DEBUG', 'False') == 'True',
    )
    
    print("✅ Sentry initialized for error tracking")


# ════════════════════════════════════════════════════════════════════════════════
# CUSTOM METRICS & LOGGING
# ════════════════════════════════════════════════════════════════════════════════

class PerformanceMonitor:
    """
    Track API performance metrics without external dependencies.
    Use for local development or small deployments.
    """
    
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'total_errors': 0,
            'total_success': 0,
            'response_times': [],  # List of response times in ms
            'endpoints': {},  # Per-endpoint stats
        }
    
    def record_request(self, endpoint, method, status_code, response_time_ms):
        """Record API request metrics"""
        self.metrics['total_requests'] += 1
        
        if status_code >= 400:
            self.metrics['total_errors'] += 1
        else:
            self.metrics['total_success'] += 1
        
        self.metrics['response_times'].append(response_time_ms)
        
        # Keep only last 1000 response times
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'].pop(0)
        
        # Per-endpoint stats
        key = f"{method} {endpoint}"
        if key not in self.metrics['endpoints']:
            self.metrics['endpoints'][key] = {
                'count': 0,
                'errors': 0,
                'avg_time': 0,
            }
        
        stats = self.metrics['endpoints'][key]
        stats['count'] += 1
        if status_code >= 400:
            stats['errors'] += 1
        stats['avg_time'] = response_time_ms
    
    def get_stats(self):
        """Get current performance statistics"""
        avg_response_time = (
            sum(self.metrics['response_times']) / len(self.metrics['response_times'])
            if self.metrics['response_times'] else 0
        )
        
        error_rate = (
            self.metrics['total_errors'] / self.metrics['total_requests']
            if self.metrics['total_requests'] > 0 else 0
        )
        
        return {
            'total_requests': self.metrics['total_requests'],
            'total_errors': self.metrics['total_errors'],
            'error_rate': f"{error_rate*100:.2f}%",
            'avg_response_time_ms': f"{avg_response_time:.2f}",
            'success_rate': f"{(1-error_rate)*100:.2f}%",
            'endpoints': self.metrics['endpoints'],
            'timestamp': datetime.utcnow().isoformat(),
        }


# Global monitor instance
performance_monitor = PerformanceMonitor()


def monitoring_middleware(app):
    """
    Add performance monitoring middleware to Flask app.
    
    Usage in app.py:
        from utils.monitoring import monitoring_middleware
        monitoring_middleware(app)
    """
    import time
    
    @app.before_request
    def before_request():
        """Start timer for request"""
        from flask import g
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Record metrics after response"""
        from flask import g, request
        
        if hasattr(g, 'start_time'):
            response_time_ms = (time.time() - g.start_time) * 1000
            performance_monitor.record_request(
                endpoint=request.endpoint or 'unknown',
                method=request.method,
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
        
        return response
    
    print("✅ Performance monitoring middleware installed")


# ════════════════════════════════════════════════════════════════════════════════
# ERROR DECORATORS
# ════════════════════════════════════════════════════════════════════════════════

def handle_errors(func):
    """
    Decorator for graceful error handling in routes.
    
    Usage:
        @app.route('/api/endpoint')
        @handle_errors
        def endpoint():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logging.warning(f"Validation error in {func.__name__}: {str(e)}")
            return {
                'error': str(e),
                'code': 'VALIDATION_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }, 400
        except PermissionError as e:
            logging.warning(f"Permission error in {func.__name__}: {str(e)}")
            return {'error': 'Insufficient permissions', 'code': 'FORBIDDEN'}, 403
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            # Send to Sentry
            if sentry_sdk.Hub.current.client:
                sentry_sdk.capture_exception(e)
            return {
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR',
                'timestamp': datetime.utcnow().isoformat()
            }, 500
    
    return wrapper


# ════════════════════════════════════════════════════════════════════════════════
# MONITORING DASHBOARD ENDPOINT
# ════════════════════════════════════════════════════════════════════════════════

def add_monitoring_routes(app):
    """
    Add monitoring endpoints to Flask app.
    
    GET /api/admin/monitoring/stats → Performance statistics
    GET /api/admin/monitoring/errors → Recent errors (from logs)
    GET /api/admin/monitoring/health → Detailed health check
    
    Usage in app.py:
        from utils.monitoring import add_monitoring_routes
        add_monitoring_routes(app)
    """
    
    @app.route('/api/admin/monitoring/stats', methods=['GET'])
    def monitoring_stats():
        """Get performance statistics (Platform Admin only)"""
        from middleware.rbac import require_admin_role
        require_admin_role('PLATFORM_ADMIN')(lambda: None)()
        
        return performance_monitor.get_stats(), 200
    
    @app.route('/api/admin/monitoring/health/detailed', methods=['GET'])
    def detailed_health():
        """Detailed health check with all systems"""
        from flask import g
        from models.user_model import db
        
        health = {
            'timestamp': datetime.utcnow().isoformat(),
            'services': {}
        }
        
        # Database
        try:
            db.session.execute('SELECT 1')
            health['services']['database'] = {
                'status': 'healthy',
                'response_time_ms': 'N/A'
            }
        except Exception as e:
            health['services']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Cache (Redis)
        try:
            # Try to import redis
            import redis
            r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
            r.ping()
            health['services']['cache'] = {'status': 'healthy'}
        except Exception as e:
            health['services']['cache'] = {
                'status': 'unavailable',
                'note': 'Redis not configured'
            }
        
        # Encryption
        try:
            from utils.security import encryption_service
            test_data = "test"
            encrypted = encryption_service.encrypt(test_data)
            decrypted = encryption_service.decrypt(encrypted)
            assert decrypted == test_data
            health['services']['encryption'] = {'status': 'healthy'}
        except Exception as e:
            health['services']['encryption'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # API Keys
        health['services']['api_keys'] = {
            'groq': 'configured' if os.getenv('GROQ_API_KEY') else 'missing',
            'bhashini': 'configured' if os.getenv('BHASHINI_API_KEY') else 'missing',
            'sendgrid': 'configured' if os.getenv('SENDGRID_API_KEY') else 'missing',
            'twilio': 'configured' if os.getenv('TWILIO_ACCOUNT_SID') else 'missing',
        }
        
        return health, 200
    
    print("✅ Monitoring endpoints added: /api/admin/monitoring/*")


# ════════════════════════════════════════════════════════════════════════════════
# SETUP INSTRUCTIONS
# ════════════════════════════════════════════════════════════════════════════════

SETUP_INSTRUCTIONS = """
═════════════════════════════════════════════════════════════════════════════
MONITORING SETUP GUIDE (Production)
═════════════════════════════════════════════════════════════════════════════

1. SENTRY ERROR TRACKING
   
   a) Create free account: https://sentry.io/signup
   
   b) Create new project:
      - Platform: Python
      - Name: MediConnect-AI
      - Team: Your team
   
   c) Copy your DSN (looks like: https://xxx@xxx.ingest.sentry.io/12345)
   
   d) Add to .env:
      SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/12345
   
   e) Errors are now tracked automatically! Check dashboard at sentry.io

2. LOCAL PERFORMANCE MONITORING
   
   No setup needed! Built-in monitoring:
   
   GET /api/admin/monitoring/stats
   {
       "total_requests": 1250,
       "total_errors": 3,
       "error_rate": "0.24%",
       "avg_response_time_ms": "45.23",
       "endpoints": {
           "POST /api/appointments": {"count": 250, "errors": 0},
           "GET /api/hospitals/search": {"count": 380, "errors": 2}
       }
   }

3. DATADOG (Advanced - Optional)
   
   For advanced monitoring:
   
   pip install datadog
   
   from datadog import initialize, api
   
   options = {
       'api_key': os.getenv('DATADOG_API_KEY'),
       'app_key': os.getenv('DATADOG_APP_KEY')
   }
   initialize(**options)

4. SLACK ALERTS (Optional)
   
   Connect Sentry to Slack:
   - Sentry Dashboard → Integrations → Slack
   - Connect workspace
   - Choose #alerts channel
   
   Errors now appear in Slack in real-time!

5. MONITORING CHECKLIST
   
   ☐ Set SENTRY_DSN in .env
   ☐ Test error tracking: trigger error, check sentry.io
   ☐ Check /api/admin/monitoring/stats endpoint
   ☐ Check /api/admin/monitoring/health/detailed endpoint
   ☐ Set up Slack integration (optional)
   ☐ Create Sentry alerts for error rate > 1%
   ☐ Monitor database performance
   ☐ Check response times (should be <200ms)

═════════════════════════════════════════════════════════════════════════════
"""

print(SETUP_INSTRUCTIONS)
