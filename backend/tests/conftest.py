"""
Pytest configuration and shared fixtures for MediConnect-AI tests
"""

import os
import pytest
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask app for the entire test session"""
    # Set test environment variables
    os.environ['TESTING'] = 'True'
    os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'test-secret-key-do-not-use-in-production'
    os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key-do-not-use-in-production'
    
    from app import app as flask_app
    
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    flask_app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
    
    return flask_app


@pytest.fixture(scope='session')
def app_context(app):
    """Create an application context for the test session"""
    with app.app_context():
        from models.user_model import db
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_context):
    """Create a test client"""
    return app_context.test_client()


@pytest.fixture
def runner(app_context):
    """Create a test CLI runner"""
    return app_context.test_cli_runner()


@pytest.fixture(autouse=True)
def reset_db(app_context):
    """Reset database before each test"""
    from models.user_model import db
    yield
    db.session.rollback()


@pytest.fixture
def test_app(app_context):
    """Alias for app_context for compatibility"""
    return app_context
