import os
import base64
from datetime import datetime
from functools import wraps
from flask import request, g, jsonify
from cryptography.fernet import Fernet
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models.user_model import db, Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text

# --- PART 1: AES-256 Encryption ---
class HealthDataEncryption:
    def __init__(self):
        # In production, this should be in os.environ["ENCRYPTION_KEY"]
        key = os.environ.get("ENCRYPTION_KEY")
        if not key:
            # Generate a consistent key for this session if not provided
            # NOTE: In real production, this key must be persistent!
            key = Fernet.generate_key().decode()
            os.environ["ENCRYPTION_KEY"] = key
        
        # Ensure it's bytes for Fernet
        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, data: str) -> str:
        if not data: return data
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        if not encrypted: return encrypted
        try:
            return self.cipher.decrypt(encrypted.encode()).decode()
        except Exception:
            return encrypted # Return raw if decryption fails (e.g. not encrypted yet)

# Initialize encryption
encryption_service = HealthDataEncryption()

# --- PART 2: Audit Logging Model ---
class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100))
    action = Column(String(50))      # VIEW, CREATE, UPDATE, DELETE
    resource = Column(String(50))    # appointment, doctor, hospital
    resource_id = Column(String(36))
    ip_address = Column(String(45))
    user_agent = Column(String(200))
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)

def audit_log(action, resource):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function first
            response = f(*args, **kwargs)
            
            # Extract status code from response
            status_code = 200
            if isinstance(response, tuple):
                status_code = response[1]
            
            # Log the action
            try:
                user_id = getattr(g, 'user_id', 'ANONYMOUS')
                # For appointment updates, ID might be in kwargs
                res_id = kwargs.get('appointment_id') or kwargs.get('id') or 'N/A'
                
                new_log = AuditLog(
                    user_id=user_id,
                    action=action,
                    resource=resource,
                    resource_id=str(res_id),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    success=(200 <= status_code < 300)
                )
                db.session.add(new_log)
                db.session.commit()
            except Exception as e:
                print(f"Audit log failed: {e}")
                db.session.rollback()
                
            return response
        return decorated_function
    return decorator

# --- PART 3: Rate Limiting ---
# This will be initialized in app.py with the app instance
limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per hour"])

# --- PART 4: Secure Headers ---
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# --- PART 5: Input Validation (Simplified Pydantic concepts for existing routes) ---
# We'll use these in the routes
def validate_appointment_data(data):
    errors = []
    if not data.get('reason') or len(data.get('reason')) > 500:
        errors.append("Reason must be between 1 and 500 characters")
    if not data.get('hospital_id'):
        errors.append("Hospital ID is required")
    # Add more validations as needed
    return errors
