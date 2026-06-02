"""
conftest.py — Shared pytest fixtures for MediConnect-AI backend tests.

Test database uses SQLite in-memory so tests are fast and isolated.
Each test function gets a fresh DB transaction that is rolled back after the test.
"""
import os
import pytest

# Set test env BEFORE importing app to avoid env-check crashes
# Use 'development' so that OTP dev mode works (returns otp_dev in response)
os.environ['FLASK_ENV'] = 'development'
os.environ.setdefault('SECRET_KEY', 'test-secret-key-not-for-production')
os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-not-for-production')
os.environ.setdefault('ADMIN_SECRET_TOKEN', 'test-admin-token-abc123XYZ')
os.environ.setdefault('ENCRYPTION_KEY', '')  # Will derive from SECRET_KEY in test
# Disable Flask-Limiter in tests to prevent rate-limit bleed across test cases
os.environ['RATELIMIT_ENABLED'] = 'false'


@pytest.fixture(scope='session')
def app():
    """Create a Flask test application with in-memory SQLite DB."""
    import sys
    from pathlib import Path
    # Ensure backend is on sys.path
    backend_dir = Path(__file__).resolve().parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    from app import app as flask_app
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'JWT_ACCESS_TOKEN_EXPIRES': False,  # No expiry in tests
        'MAX_CONTENT_LENGTH': 1 * 1024 * 1024,
        'RATELIMIT_ENABLED': False,          # Disable rate limiting in tests
    })

    # Disable Flask-Limiter at the extension level
    from utils.security import limiter
    limiter.enabled = False

    from models.user_model import db
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Provide a clean DB session per test; rollback after each test."""
    from models.user_model import db
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        yield db
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def sample_user(app, client):
    """Create a sample user and return (user, auth_token)."""
    from models.user_model import db, User
    from flask_jwt_extended import create_access_token

    with app.app_context():
        user = User(
            email='test@mediconnect.ai',
            full_name='Test User',
            preferred_language='en'
        )
        user.set_password('TestPass123')
        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=str(user.id))
        yield user, token

        # Cleanup
        db.session.delete(user)
        db.session.commit()


@pytest.fixture(scope='function')
def auth_headers(sample_user):
    """Authorization headers for an authenticated regular user."""
    _, token = sample_user
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture(scope='function')
def admin_user(app):
    """Create a sample admin user and return admin + bearer token."""
    from models.user_model import db
    from models.admin_model import AdminUser, AdminRole

    with app.app_context():
        import base64
        admin = AdminUser(
            email='admin@mediconnect.ai',
            firebase_uid='test-firebase-uid-admin',
            role=AdminRole.PLATFORM_ADMIN,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()

        secret = os.environ.get('ADMIN_SECRET_TOKEN', 'test-admin-token-abc123XYZ')
        bearer = base64.b64encode(f'admin@mediconnect.ai:{secret}'.encode()).decode()

        yield admin, bearer

        db.session.delete(admin)
        db.session.commit()


@pytest.fixture(scope='function')
def admin_headers(admin_user):
    """Authorization headers for an authenticated admin."""
    _, bearer = admin_user
    return {
        'Authorization': f'Bearer {bearer}',
        'Content-Type': 'application/json',
        'X-Admin-Email': 'admin@mediconnect.ai',
        'X-Admin-Token': os.environ.get('ADMIN_SECRET_TOKEN', 'test-admin-token-abc123XYZ'),
    }
