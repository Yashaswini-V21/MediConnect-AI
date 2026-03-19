"""Authentication middleware with Firebase-first verification and JWT fallback."""

from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from firebase_admin import initialize_app, get_app
from firebase_admin.exceptions import FirebaseError
from models.user_model import db, User
import json
import logging
import os
import secrets

logger = logging.getLogger(__name__)

_firebase_initialized = False
_firebase_init_attempted = False


def _init_firebase():
    """Initialize Firebase Admin SDK once, if configuration is available."""
    global _firebase_initialized, _firebase_init_attempted

    if _firebase_initialized:
        return True

    if _firebase_init_attempted:
        return False

    _firebase_init_attempted = True

    try:
        try:
            get_app()
            _firebase_initialized = True
            return True
        except ValueError:
            pass

        service_account_file = os.getenv('FIREBASE_SERVICE_ACCOUNT_FILE', '').strip()
        service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', '').strip()
        project_id = os.getenv('FIREBASE_PROJECT_ID', '').strip()

        if service_account_file:
            cred = credentials.Certificate(service_account_file)
            initialize_app(cred)
            _firebase_initialized = True
            logger.info("Firebase Admin initialized using service account file")
            return True

        if service_account_json:
            parsed = json.loads(service_account_json)
            cred = credentials.Certificate(parsed)
            initialize_app(cred)
            _firebase_initialized = True
            logger.info("Firebase Admin initialized using service account JSON")
            return True

        if project_id:
            initialize_app(options={'projectId': project_id})
            _firebase_initialized = True
            logger.info("Firebase Admin initialized with project ID")
            return True

        logger.warning("Firebase Admin not initialized: missing Firebase environment configuration")
        return False

    except Exception as exc:
        logger.warning(f"Firebase Admin initialization failed: {exc}")
        return False


def _extract_bearer_token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1].strip()
    return token or None


def _resolve_or_create_local_user_from_firebase(claims):
    email = claims.get('email')
    if not email:
        return None

    user = User.query.filter_by(email=email).first()
    if user:
        return user

    display_name = claims.get('name') or email.split('@')[0]

    user = User(
        email=email,
        full_name=display_name,
        preferred_language='en'
    )
    # Generate an internal password hash for DB compatibility in Firebase-created users.
    user.set_password(secrets.token_urlsafe(24))

    db.session.add(user)
    db.session.commit()

    logger.info(f"Created local profile for Firebase user: {email}")
    return user


def _verify_firebase(token):
    if not token or not _init_firebase():
        return None

    try:
        claims = firebase_auth.verify_id_token(token)
        user = _resolve_or_create_local_user_from_firebase(claims)
        if not user:
            return None

        g.auth_provider = 'firebase'
        g.firebase_claims = claims
        return user.id
    except FirebaseError as exc:
        logger.debug(f"Firebase token verification failed: {exc}")
        return None
    except Exception as exc:
        logger.debug(f"Firebase verification error: {exc}")
        return None


def _verify_legacy_jwt(optional=False):
    try:
        verify_jwt_in_request(optional=optional)
        user_id = get_jwt_identity()
        if user_id:
            g.auth_provider = 'jwt'
        return user_id
    except Exception:
        return None


def get_authenticated_user_id(optional=False):
    """Return authenticated local user ID from Firebase token or legacy JWT."""
    token = _extract_bearer_token()

    user_id = _verify_firebase(token)
    if user_id:
        return user_id

    user_id = _verify_legacy_jwt(optional=optional)
    if user_id:
        return user_id

    if optional:
        return None

    raise PermissionError("Authentication required")


def require_auth():
    """Decorator for routes requiring authenticated users."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                user_id = get_authenticated_user_id(optional=False)
                g.current_user_id = user_id
                return func(*args, **kwargs)
            except PermissionError:
                return jsonify({
                    'success': False,
                    'error': 'Unauthorized',
                    'message': 'Valid Firebase ID token or JWT token is required'
                }), 401
            except Exception as exc:
                logger.error(f"Authentication middleware error: {exc}")
                return jsonify({
                    'success': False,
                    'error': 'Authentication failed',
                    'message': 'Unable to verify authentication token'
                }), 401
        return wrapper
    return decorator
