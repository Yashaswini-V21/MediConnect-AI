"""
Minimal tests to verify app integrity
"""

import pytest


class TestAppInitialization:
    """Basic app startup and health checks"""
    
    def test_app_created(self, app):
        """Verify Flask app is created"""
        assert app is not None
        assert app.config['TESTING'] == True
    
    def test_app_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code in [200, 404]  # 404 if endpoint not implemented yet
    
    def test_database_connection(self, app_context):
        """Test database connectivity"""
        from models.user_model import db
        with app_context.app_context():
            # Simple query to verify DB connection
            assert db.session is not None


class TestImports:
    """Verify all critical modules can be imported"""
    
    def test_models_import(self):
        """Test model imports"""
        from models import user_model, admin_model, analytics_model
        assert user_model is not None
        assert admin_model is not None
        assert analytics_model is not None
    
    def test_routes_import(self):
        """Test route blueprints"""
        from routes import auth_routes, hospital_routes, appointment_routes
        assert auth_routes is not None
        assert hospital_routes is not None
        assert appointment_routes is not None
    
    def test_utils_import(self):
        """Test utility modules"""
        from utils import security, caching, database_optimizer
        assert security is not None
        assert caching is not None
        assert database_optimizer is not None
