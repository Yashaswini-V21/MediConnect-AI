"""
jwt_handler.py — Simple JWT utility stub.
The actual JWT handling is done by flask_jwt_extended in the app.
This module exists for backwards compatibility with utils/__init__.py imports.
"""
import os
from datetime import datetime, timedelta

try:
    import jwt as pyjwt
    _HAS_PYJWT = True
except ImportError:
    _HAS_PYJWT = False


SECRET = os.getenv('JWT_SECRET_KEY')


def _require_secret():
    if not SECRET:
        raise RuntimeError('JWT_SECRET_KEY is not set in environment')


def create_token(payload: dict, expires_hours: int = 168) -> str:
    """Create a JWT token using PyJWT. Requires `JWT_SECRET_KEY` env var."""
    if _HAS_PYJWT:
        _require_secret()
        payload = {**payload, 'exp': datetime.utcnow() + timedelta(hours=expires_hours)}
        return pyjwt.encode(payload, SECRET, algorithm='HS256')
    # Fallback: produce a non-cryptographic token for local dev only
    import base64, json
    return base64.b64encode(json.dumps(payload).encode()).decode()


def decode_token(token: str) -> dict:
    """Decode a JWT token. Returns empty dict on failure."""
    if _HAS_PYJWT:
        try:
            _require_secret()
            return pyjwt.decode(token, SECRET, algorithms=['HS256'])
        except Exception:
            return {}
    # Fallback: decode non-cryptographic token used for local dev only
    import base64, json
    try:
        return json.loads(base64.b64decode(token).decode())
    except Exception:
        return {}
