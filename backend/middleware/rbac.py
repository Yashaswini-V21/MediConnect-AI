"""
MediConnect-AI M3: RBAC Middleware
Decorator-based role access control for admin routes.

Usage:
    from middleware.rbac import require_admin_role, get_current_admin

    @admin_bp.route('/appointments')
    @require_admin_role('PLATFORM_ADMIN', 'HOSPITAL_ADMIN')
    def list_appointments():
        admin = get_current_admin()
        ...
"""

import logging
from functools import wraps
from flask import request, jsonify, g
from models.admin_model import AdminUser, AdminRole

logger = logging.getLogger(__name__)


# ─── Helper: extract admin from request ───────────────────────────────────────

def _resolve_admin_from_request() -> AdminUser | None:
    """
    Resolve an AdminUser from the current request.
    Strategy:
      1. Check X-Admin-Email header (dev/test shortcut with X-Admin-Token)
      2. Check Authorization: Bearer <jwt> (future Firebase Admin SDK)
    Returns the AdminUser object or None.
    """
    # --- Dev / simple-token approach (no Firebase Admin SDK required for M3) ---
    admin_email = request.headers.get('X-Admin-Email')
    admin_token = request.headers.get('X-Admin-Token')  # shared secret stored in env

    if admin_email and admin_token:
        import os
        expected = os.getenv('ADMIN_SECRET_TOKEN', 'mediconnect-admin-dev-token')
        if admin_token != expected:
            return None
        admin = AdminUser.query.filter_by(email=admin_email, is_active=True).first()
        return admin

    # --- Authorization: Bearer <token> fallback ---
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        # Lightweight: treat token as "email:secret" encoded base64
        try:
            import base64
            decoded = base64.b64decode(token).decode()
            email, secret = decoded.split(':', 1)
            import os
            expected = os.getenv('ADMIN_SECRET_TOKEN', 'mediconnect-admin-dev-token')
            if secret == expected:
                admin = AdminUser.query.filter_by(email=email, is_active=True).first()
                return admin
        except Exception:
            pass

    return None


def get_current_admin() -> AdminUser | None:
    """Return the currently authenticated admin (set by require_admin_role)."""
    return getattr(g, '_current_admin', None)


# ─── Main decorator ───────────────────────────────────────────────────────────

def require_admin_role(*allowed_roles: str):
    """
    Decorator that enforces role-based access control for admin routes.

    Args:
        *allowed_roles: One or more of AdminRole.PLATFORM_ADMIN,
                        AdminRole.HOSPITAL_ADMIN, AdminRole.SUPPORT_STAFF.
                        Pass nothing to allow any authenticated admin.

    Example:
        @require_admin_role('PLATFORM_ADMIN', 'HOSPITAL_ADMIN')
        def my_route():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            admin = _resolve_admin_from_request()

            if admin is None:
                logger.warning(f"Admin auth failed for {request.path}")
                return jsonify({
                    'error': 'Admin authentication required',
                    'message': 'Provide X-Admin-Email + X-Admin-Token headers or '
                               'Authorization: Bearer <base64(email:secret)>'
                }), 401

            # Role check
            if allowed_roles and admin.role not in allowed_roles:
                logger.warning(
                    f"Role denied: {admin.email} [{admin.role}] tried {request.path} "
                    f"(needs {allowed_roles})"
                )
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Your role ({admin.role}) is not allowed to access this resource.',
                    'required_roles': list(allowed_roles)
                }), 403

            # Store admin in Flask g for the duration of the request
            g._current_admin = admin

            # Update last login (lightweight — no commit needed here; routes handle commits)
            from datetime import datetime
            admin.last_login = datetime.utcnow()

            logger.info(f"Admin access: {admin.email} [{admin.role}] → {request.method} {request.path}")
            return fn(*args, **kwargs)

        return wrapper
    return decorator


# ─── Convenience aliases ──────────────────────────────────────────────────────

def platform_admin_only(fn):
    """Shortcut: only PLATFORM_ADMIN."""
    return require_admin_role(AdminRole.PLATFORM_ADMIN)(fn)


def hospital_admin_or_above(fn):
    """Shortcut: PLATFORM_ADMIN or HOSPITAL_ADMIN."""
    return require_admin_role(AdminRole.PLATFORM_ADMIN, AdminRole.HOSPITAL_ADMIN)(fn)


def any_admin(fn):
    """Shortcut: any authenticated admin role."""
    return require_admin_role(*AdminRole.ALL)(fn)


# ─── Hospital scope guard ─────────────────────────────────────────────────────

def enforce_hospital_scope(hospital_id: int) -> tuple[bool, dict]:
    """
    Call inside a route after require_admin_role to verify hospital scope.
    PLATFORM_ADMIN passes always.
    HOSPITAL_ADMIN passes only if their hospital_id matches.

    Returns (allowed: bool, error_response: dict | None)
    """
    admin = get_current_admin()
    if admin is None:
        return False, {'error': 'Not authenticated'}
    if not admin.can_access_hospital(hospital_id):
        return False, {
            'error': 'Forbidden',
            'message': f'You can only access data for your assigned hospital (ID {admin.hospital_id}).'
        }
    return True, None
