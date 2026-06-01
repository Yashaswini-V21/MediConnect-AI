import os
import base64
import hashlib
from datetime import datetime, timezone
from functools import wraps
from flask import request, g, jsonify
from cryptography.fernet import Fernet
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models.user_model import db
import logging

_security_logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# PART 1: AES-256 Encryption (Fernet)
# ─────────────────────────────────────────────────────────────
class HealthDataEncryption:
    """
    Provides AES-256 symmetric encryption for sensitive patient data.
    Always set ENCRYPTION_KEY in production via environment variable.
    """
    def __init__(self):
        key = os.environ.get("ENCRYPTION_KEY", "").strip()
        if not key:
            # Derive a deterministic Fernet key from SECRET_KEY so encrypted
            # data survives server restarts.  Operators must set ENCRYPTION_KEY
            # in production — we log a startup warning below.
            secret = (
                os.environ.get("SECRET_KEY")
                or os.environ.get("FLASK_SECRET_KEY")
                or "mediconnect-dev-fallback-not-for-production"
            )
            digest = hashlib.sha256(secret.encode()).digest()
            key = base64.urlsafe_b64encode(digest).decode()
            _security_logger.warning(
                "ENCRYPTION_KEY not set — deriving from SECRET_KEY. "
                "Set a persistent ENCRYPTION_KEY in production to avoid "
                "data-loss risk."
            )

        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, data: str) -> str:
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        if not encrypted:
            return encrypted
        try:
            return self.cipher.decrypt(encrypted.encode()).decode()
        except Exception:
            return encrypted  # Return raw if decryption fails (not yet encrypted)


# Singleton encryption service
encryption_service = HealthDataEncryption()


# ─────────────────────────────────────────────────────────────
# PART 2: Audit Logging Model
# ─────────────────────────────────────────────────────────────
class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id     = db.Column(db.String(100))
    action      = db.Column(db.String(50))       # VIEW, CREATE, UPDATE, DELETE
    resource    = db.Column(db.String(50))        # appointment, doctor, hospital
    resource_id = db.Column(db.String(36))
    ip_address  = db.Column(db.String(45))
    user_agent  = db.Column(db.String(200))
    timestamp   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    success     = db.Column(db.Boolean, default=True)


def audit_log(action: str, resource: str):
    """Decorator that writes an AuditLog entry after each request."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)

            status_code = 200
            if isinstance(response, tuple):
                status_code = response[1]

            try:
                user_id = getattr(g, 'user_id', 'ANONYMOUS')
                res_id  = kwargs.get('appointment_id') or kwargs.get('id') or 'N/A'

                entry = AuditLog(
                    user_id    = user_id,
                    action     = action,
                    resource   = resource,
                    resource_id= str(res_id),
                    ip_address = request.remote_addr,
                    user_agent = request.user_agent.string[:200],
                    success    = (200 <= status_code < 300),
                )
                db.session.add(entry)
                db.session.commit()
            except Exception as exc:
                _security_logger.warning(f"Audit log write failed: {exc}")
                db.session.rollback()

            return response
        return decorated_function
    return decorator


# ─────────────────────────────────────────────────────────────
# PART 3: Rate Limiting
# ─────────────────────────────────────────────────────────────
# Initialized in app.py via limiter.init_app(app)
# Uses Redis when REDIS_URL is set, falls back to in-memory for dev.
_storage_uri = os.environ.get("REDIS_URL") or None
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"],
    storage_uri=_storage_uri,
)


# ─────────────────────────────────────────────────────────────
# PART 4: Security Headers
# ─────────────────────────────────────────────────────────────
def add_security_headers(response):
    """
    Apply production-grade security headers to every response.
    CSP is configured to allow Firebase Auth, Google Maps, and Sarvam AI
    while blocking everything else by default.
    """
    # Content-Security-Policy — allow Firebase + Google Maps + self
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://maps.googleapis.com https://www.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https://*.googleapis.com https://*.gstatic.com; "
        "connect-src 'self' https://*.googleapis.com https://api.groq.com "
        "https://api.sarvam.ai https://identitytoolkit.googleapis.com; "
        "frame-src 'none'; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    response.headers["Content-Security-Policy"]   = csp
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["X-XSS-Protection"]          = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]        = (
        "camera=(), microphone=(self), geolocation=(self), "
        "payment=(), usb=()"
    )
    return response


# ─────────────────────────────────────────────────────────────
# PART 5: Input Validation Helpers
# ─────────────────────────────────────────────────────────────
def validate_appointment_data(data: dict) -> list:
    """Return a list of validation error strings, empty if valid."""
    errors = []
    reason = data.get('reason', '')
    if not reason or len(reason.strip()) < 3:
        errors.append("Reason must be at least 3 characters")
    if len(reason) > 500:
        errors.append("Reason must be 500 characters or fewer")
    if not data.get('hospital_id'):
        errors.append("hospital_id is required")
    return errors


def check_admin_token_security():
    """Warn loudly at startup if ADMIN_SECRET_TOKEN is insecure."""
    token = os.environ.get("ADMIN_SECRET_TOKEN", "")
    insecure_defaults = {"", "admin", "changeme", "admin-token-change-in-production",
                         "your_admin_token_here", "CHANGE_ME"}
    if token in insecure_defaults:
        _security_logger.warning(
            "ADMIN_SECRET_TOKEN is not set or uses an insecure default value. "
            "Set a strong random token before going to production."
        )
