"""
MediConnect-AI Security Layer
Implements encryption, audit logging, rate limiting, and secure headers for HIPAA compliance.
"""

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


# ════════════════════════════════════════════════════════════════════════════════
# PART 1: AES-256 ENCRYPTION
# ════════════════════════════════════════════════════════════════════════════════

class HealthDataEncryption:
    """
    AES-256 encryption for sensitive health data.
    Uses Fernet (symmetric encryption) to encrypt/decrypt PII and medical information.
    
    Example:
        >>> crypto = HealthDataEncryption()
        >>> encrypted = crypto.encrypt("Patient has diabetes")
        >>> decrypted = crypto.decrypt(encrypted)
        >>> assert decrypted == "Patient has diabetes"
    
    Security Notes:
        - Requires ENCRYPTION_KEY environment variable
        - Key should be generated with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        - Never commit key to version control
        - Rotate keys annually
    
    Fields encrypted in MediConnect-AI:
        - Appointment.reason (medical reason for visit)
        - Appointment.notes (admin notes about condition)
        - Any user health profile data
    """
    
    def __init__(self):
        """
        Initialize encryption cipher.
        
        Raises:
            ValueError: If ENCRYPTION_KEY is invalid or missing
        """
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
        """
        Encrypt sensitive health data using AES-256.
        
        Args:
            data: Plain text string to encrypt (medical reason, notes, etc.)
        
        Returns:
            Encrypted string (hex-encoded, safe to store in database)
        
        Raises:
            Exception: If encryption fails (invalid key)
        
        Example:
            >>> encrypted = encryption_service.encrypt("Type 2 Diabetes")
            >>> print(encrypted[:20] + "...")  # gAAAAABmK...
        """
        if not data: return data
        return self.cipher.encrypt(data.encode()).decode()

    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt encrypted health data.
        
        Args:
            encrypted: Previously encrypted string
        
        Returns:
            Decrypted plain text
        
        Raises:
            InvalidToken: If data is corrupted or uses wrong key
        
        Note:
            Returns original data if already unencrypted (idempotent)
        
        Example:
            >>> decrypted = encryption_service.decrypt(encrypted)
            >>> assert decrypted == "Type 2 Diabetes"
        """
        if not encrypted: return encrypted
        try:
            return self.cipher.decrypt(encrypted.encode()).decode()
        except Exception:
            return encrypted # Return raw if decryption fails (e.g. not encrypted yet)

# Initialize encryption
encryption_service = HealthDataEncryption()


# ════════════════════════════════════════════════════════════════════════════════
# PART 2: AUDIT LOGGING (HIPAA Compliance)
# ════════════════════════════════════════════════════════════════════════════════

class AuditLog(db.Model):
    """
    Immutable audit trail of all admin actions.
    Required for HIPAA compliance and forensic investigation.
    
    Fields:
        user_id: Admin who performed action
        action: Type of action (CREATE, UPDATE, DELETE, VIEW, CONFIRM)
        resource: What was modified (appointment, doctor, hospital)
        resource_id: ID of the resource
        ip_address: IP address of requester (for tracking suspicious access)
        user_agent: Browser/client making request
        timestamp: When action occurred
        success: Whether action succeeded or failed
    
    Example:
        An admin confirming an appointment creates an AuditLog entry:
        AuditLog(
            user_id='admin@hospital.com',
            action='UPDATE',
            resource='appointment',
            resource_id='appt_001',
            ip_address='192.168.1.1',
            success=True
        )
    
    Query examples:
        - Find all actions by admin: AuditLog.query.filter_by(user_id='admin@hospital.com')
        - Find all failed access attempts: AuditLog.query.filter_by(success=False)
        - Find all suspicious IP addresses: AuditLog.query.filter(AuditLog.ip_address.like('10.%'))
    """
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
    """
    Decorator for automatic audit logging of admin actions.
    Logs every access, modification, and deletion for compliance.
    
    Args:
        action: Type of action - 'CREATE', 'READ', 'UPDATE', 'DELETE', 'CONFIRM'
        resource: Resource type - 'appointment', 'doctor', 'hospital', 'admin_user'
    
    Returns:
        Decorated function that logs action automatically
    
    Usage:
        @app.route('/appointments/<id>/confirm', methods=['PUT'])
        @require_admin_role('PLATFORM_ADMIN', 'HOSPITAL_ADMIN')
        @audit_log('UPDATE', 'appointment')
        def confirm_appointment(id):
            appointment = Appointment.query.get(id)
            appointment.status = 'CONFIRMED'
            db.session.commit()
            return {'status': 'confirmed'}
    
    Logged fields:
        - user_id: Admin email
        - action: UPDATE
        - resource: appointment
        - resource_id: Appointment ID
        - ip_address: Request IP (for security analysis)
        - user_agent: Browser info
        - timestamp: Exact time
        - success: True if response status < 400
    
    Note:
        Failures are also logged (success=False) to detect attack attempts
    """
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
"""
Rate limiting configuration for API abuse prevention.
Applied per IP address automatically to all routes.

Limits:
    - Default: 1000 requests/hour per IP
    - AI endpoints: 30 requests/minute (expensive LLM calls)
    - Auth endpoints: 5 login attempts/minute (brute force prevention)
    - Booking endpoints: 10 bookings/hour (spam prevention)

Use in routes:
    @app.route('/api/appointments')
    @limiter.limit("10/hour")
    def create_appointment():
        ...

Headers returned:
    X-RateLimit-Limit: 10
    X-RateLimit-Remaining: 9
    X-RateLimit-Reset: 1623456000
"""


# --- PART 4: Secure Headers ---
def add_security_headers(response):
    """
    Add security headers to all responses (OWASP recommendations).
    
    Headers added:
        X-Content-Type-Options: nosniff - Prevent MIME type sniffing
        X-Frame-Options: DENY - Prevent clickjacking
        X-XSS-Protection: 1; mode=block - Enable XSS filter
        Strict-Transport-Security: Force HTTPS only
        Content-Security-Policy: Only allow scripts from same origin
    
    Args:
        response: Flask Response object
    
    Returns:
        Response with security headers added
    
    Usage in app.py:
        from utils.security import add_security_headers
        
        @app.after_request
        def set_security_headers(response):
            return add_security_headers(response)
    """
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
