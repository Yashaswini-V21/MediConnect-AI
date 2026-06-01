"""
MediConnect-AI M3: Admin Routes Blueprint
All admin API endpoints with RBAC enforcement.

Endpoints:
  POST   /api/admin/login
  GET    /api/admin/me
  GET    /api/admin/appointments
  GET    /api/admin/appointments/<id>
  PUT    /api/admin/appointments/<id>/status
  GET    /api/admin/doctors
  POST   /api/admin/doctors
  PUT    /api/admin/doctors/<id>
  DELETE /api/admin/doctors/<id>
  GET    /api/admin/hospitals
  PUT    /api/admin/hospitals/<id>
  GET    /api/admin/analytics/summary
  GET    /api/admin/analytics/trends
  GET    /api/admin/notifications
  POST   /api/admin/notifications/send
  GET    /api/admin/support-tickets
  PUT    /api/admin/support-tickets/<id>
  POST   /api/admin/users                    (PLATFORM_ADMIN only)
  GET    /api/admin/users                    (PLATFORM_ADMIN only)
  PUT    /api/admin/users/<id>               (PLATFORM_ADMIN only)
"""

import logging
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict

from flask import Blueprint, request, jsonify, g, Response
from models.user_model import db
from models.admin_model import (
    AdminUser, Doctor, Appointment, Notification, SupportTicket,
    AdminRole, AppointmentStatus, UrgencyLevel,
    NotificationType, NotificationChannel, TicketStatus, TicketPriority
)
from middleware.rbac import (
    require_admin_role, get_current_admin,
    platform_admin_only, hospital_admin_or_above, any_admin,
    enforce_hospital_scope
)
from utils.notification_service import (
    notify_appointment_status_change, create_custom_notification,
    get_user_notifications, mark_notifications_read, get_unread_count
)
from utils.realtime import subscribe, unsubscribe, publish_event
from extensions import socketio
import base64
from flask import request as flask_request

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

def get_admin_secret_token():
    """Read the admin secret token from the environment or `.env` file at runtime.

    This explicitly attempts to load `.env` from the repository root so that
    the server can pick up changes without requiring a process restart.
    """
    # First try environment
    token = os.getenv('ADMIN_SECRET_TOKEN')
    if token:
        return token

    # Attempt to locate and load .env from repo root
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        repo_root = Path(__file__).resolve().parents[2]
        env_file = repo_root / '.env'
        if env_file.exists():
            load_dotenv(dotenv_path=str(env_file))
            return os.getenv('ADMIN_SECRET_TOKEN')
    except Exception:
        # If dotenv is not available or load fails, fall through
        pass

    # Fallback: try parsing .env manually (robust even without python-dotenv)
    try:
        from pathlib import Path
        repo_root = Path(__file__).resolve().parents[2]
        env_file = repo_root / '.env'
        if env_file.exists():
            for line in env_file.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('ADMIN_SECRET_TOKEN='):
                    # Split only once, support quoted values
                    _, val = line.split('=', 1)
                    val = val.strip().strip('"').strip("'")
                    return val
    except Exception:
        pass

    return None


# ════════════════════════════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """
    Admin login — returns admin profile if credentials are valid.
    Body: { "email": "...", "token": "..." }
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    token = data.get('token', '')

    if not email or not token:
        return jsonify({'error': 'email and token are required'}), 400

    # Ensure admin secret is configured in non-development environments
    admin_token = get_admin_secret_token()
    if not admin_token:
        return jsonify({'error': 'Admin token not configured on server'}), 500

    if token != admin_token:
        return jsonify({'error': 'Invalid credentials'}), 401

    admin = AdminUser.query.filter_by(email=email, is_active=True).first()
    if not admin:
        return jsonify({'error': 'Admin account not found or inactive'}), 404

    admin.last_login = datetime.utcnow()
    db.session.commit()


    bearer = base64.b64encode(f"{email}:{token}".encode()).decode()

    return jsonify({
        'success': True,
        'admin': admin.to_dict(),
        'bearer_token': bearer,
        'message': f'Welcome, {admin.email} [{admin.role}]'
    }), 200


@admin_bp.route('/me', methods=['GET'])
@any_admin
def get_me():
    """Return current admin's profile."""
    admin = get_current_admin()
    return jsonify({'success': True, 'admin': admin.to_dict()}), 200


# Socket.IO admin namespace authentication
@socketio.on('connect', namespace='/admin')
def handle_admin_connect(auth):
    """Authenticate admin socket connections using the base64 bearer token."""
    token = None
    if isinstance(auth, dict):
        token = auth.get('token')
    if not token:
        token = flask_request.args.get('token')

    if not token:
        return False

    try:
        decoded = base64.b64decode(token).decode()
        email, t = decoded.split(':', 1)
    except Exception:
        return False

    admin_token = get_admin_secret_token()
    if t != admin_token:
        return False

    admin = AdminUser.query.filter_by(email=email, is_active=True).first()
    if not admin:
        return False

    # authenticated — connection accepted
    return True


@admin_bp.route('/stream')
def admin_stream():
    """Server-Sent Events stream for admin clients.
    Clients must supply `?token=<bearer>` where bearer is the base64 token
    returned by `/api/admin/login`.
    """
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'token is required'}), 401

    import base64
    try:
        decoded = base64.b64decode(token).decode()
        email, t = decoded.split(':', 1)
    except Exception:
        return jsonify({'error': 'invalid token'}), 400

    admin_token = get_admin_secret_token()
    if t != admin_token:
        return jsonify({'error': 'invalid credentials'}), 401

    admin = AdminUser.query.filter_by(email=email, is_active=True).first()
    if not admin:
        return jsonify({'error': 'admin not found'}), 404

    q = subscribe()

    def event_stream():
        try:
            while True:
                ev = q.get()
                yield f"data: {json.dumps(ev)}\n\n"
        finally:
            unsubscribe(q)

    return Response(event_stream(), mimetype='text/event-stream')


# ════════════════════════════════════════════════════════════════════════════════
# APPOINTMENTS
# ════════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/appointments', methods=['GET'])
@hospital_admin_or_above
def list_appointments():
    """
    List appointments scoped by role.
    Query params: status, hospital_id, urgency, date_from, date_to, page, per_page
    """
    admin = get_current_admin()

    q = Appointment.query

    # --- Scope ---
    if admin.role == AdminRole.HOSPITAL_ADMIN:
        q = q.filter_by(hospital_id=admin.hospital_id)
    else:
        # PLATFORM_ADMIN: allow optional hospital_id filter
        hospital_id = request.args.get('hospital_id', type=int)
        if hospital_id:
            q = q.filter_by(hospital_id=hospital_id)

    # --- Filters ---
    status = request.args.get('status')
    if status and status in AppointmentStatus.ALL:
        q = q.filter_by(status=status)

    urgency = request.args.get('urgency')
    if urgency and urgency in UrgencyLevel.ALL:
        q = q.filter_by(urgency_level=urgency)

    date_from = request.args.get('date_from')
    if date_from:
        try:
            q = q.filter(Appointment.appointment_date >= datetime.fromisoformat(date_from))
        except ValueError:
            pass

    date_to = request.args.get('date_to')
    if date_to:
        try:
            q = q.filter(Appointment.appointment_date <= datetime.fromisoformat(date_to))
        except ValueError:
            pass

    # --- Pagination ---
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    paginated = q.order_by(Appointment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'success': True,
        'appointments': [a.to_dict() for a in paginated.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': paginated.total,
            'pages': paginated.pages,
        }
    }), 200


@admin_bp.route('/appointments/<appointment_id>', methods=['GET'])
@hospital_admin_or_above
def get_appointment(appointment_id):
    """Get a single appointment by ID."""
    admin = get_current_admin()
    apt = Appointment.query.get_or_404(appointment_id,
        description='Appointment not found')

    if admin.role == AdminRole.HOSPITAL_ADMIN and apt.hospital_id != admin.hospital_id:
        return jsonify({'error': 'Forbidden — not your hospital'}), 403

    return jsonify({'success': True, 'appointment': apt.to_dict()}), 200


@admin_bp.route('/appointments/<appointment_id>/status', methods=['PUT'])
@hospital_admin_or_above
def update_appointment_status(appointment_id):
    """
    Update appointment status (state machine enforced).
    Body: { "status": "CONFIRMED", "notes": "..." }
    """
    admin = get_current_admin()
    apt = Appointment.query.get_or_404(appointment_id,
        description='Appointment not found')

    if admin.role == AdminRole.HOSPITAL_ADMIN and apt.hospital_id != admin.hospital_id:
        return jsonify({'error': 'Forbidden — not your hospital'}), 403

    data = request.get_json() or {}
    new_status = data.get('status', '').upper()

    if new_status not in AppointmentStatus.ALL:
        return jsonify({
            'error': 'Invalid status',
            'valid_statuses': AppointmentStatus.ALL
        }), 400

    if not apt.transition_to(new_status):
        return jsonify({
            'error': f'Cannot transition from {apt.status} to {new_status}',
            'allowed_transitions': AppointmentStatus.TRANSITIONS.get(apt.status, [])
        }), 422

    if data.get('notes'):
        apt.notes = data['notes']

    db.session.commit()

    # Fire notification
    notify_appointment_status_change(apt, sent_by_admin_id=admin.id)

    # Emit Socket.IO event to connected admin clients
    try:
        socketio.emit('appointment_updated', apt.to_dict(), namespace='/admin')
    except Exception:
        logger.exception('Failed to emit socket event')

    return jsonify({
        'success': True,
        'message': f'Appointment {new_status.lower()} successfully',
        'appointment': apt.to_dict()
    }), 200


# ════════════════════════════════════════════════════════════════════════════════
# DOCTORS
# ════════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/doctors', methods=['GET'])
@hospital_admin_or_above
def list_doctors():
    """List doctors scoped by role."""
    admin = get_current_admin()

    q = Doctor.query
    if admin.role == AdminRole.HOSPITAL_ADMIN:
        q = q.filter_by(hospital_id=admin.hospital_id)
    else:
        hospital_id = request.args.get('hospital_id', type=int)
        if hospital_id:
            q = q.filter_by(hospital_id=hospital_id)

    specialty = request.args.get('specialty')
    if specialty:
        q = q.filter(Doctor.specialty.ilike(f'%{specialty}%'))

    active_only = request.args.get('active_only', 'true').lower() == 'true'
    if active_only:
        q = q.filter_by(is_active=True)

    doctors = q.order_by(Doctor.name).all()
    return jsonify({
        'success': True,
        'doctors': [d.to_dict() for d in doctors],
        'count': len(doctors)
    }), 200


@admin_bp.route('/doctors', methods=['POST'])
@hospital_admin_or_above
def create_doctor():
    """Add a new doctor. HOSPITAL_ADMIN can only add to their own hospital."""
    admin = get_current_admin()
    data = request.get_json() or {}

    required = ['name', 'specialty', 'hospital_id']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing required fields: {missing}'}), 400

    hospital_id = int(data['hospital_id'])
    allowed, err = enforce_hospital_scope(hospital_id)
    if not allowed:
        return jsonify(err), 403

    doctor = Doctor(
        hospital_id=hospital_id,
        name=data['name'].strip(),
        specialty=data['specialty'].strip(),
        degree=data.get('degree', '').strip() or None,
        experience_years=data.get('experience_years', 0),
        available_slots=data.get('available_slots', {}),
        max_daily_bookings=data.get('max_daily_bookings', 20),
        is_active=data.get('is_active', True)
    )
    db.session.add(doctor)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Doctor created successfully',
        'doctor': doctor.to_dict()
    }), 201


@admin_bp.route('/doctors/<int:doctor_id>', methods=['PUT'])
@hospital_admin_or_above
def update_doctor(doctor_id):
    """Update doctor profile."""
    admin = get_current_admin()
    doctor = Doctor.query.get_or_404(doctor_id, description='Doctor not found')

    allowed, err = enforce_hospital_scope(doctor.hospital_id)
    if not allowed:
        return jsonify(err), 403

    data = request.get_json() or {}
    for field in ['name', 'specialty', 'degree']:
        if field in data:
            setattr(doctor, field, data[field].strip())
    for field in ['experience_years', 'max_daily_bookings']:
        if field in data:
            setattr(doctor, field, int(data[field]))
    if 'available_slots' in data:
        doctor.available_slots = data['available_slots']
    if 'is_active' in data:
        doctor.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify({'success': True, 'doctor': doctor.to_dict()}), 200


@admin_bp.route('/doctors/<int:doctor_id>', methods=['DELETE'])
@hospital_admin_or_above
def deactivate_doctor(doctor_id):
    """Soft-delete (deactivate) a doctor."""
    doctor = Doctor.query.get_or_404(doctor_id, description='Doctor not found')
    allowed, err = enforce_hospital_scope(doctor.hospital_id)
    if not allowed:
        return jsonify(err), 403

    doctor.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': 'Doctor deactivated'}), 200


# ════════════════════════════════════════════════════════════════════════════════
# HOSPITALS (lightweight edit — full data lives in hospital_matcher JSON)
# ════════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/hospitals', methods=['GET'])
@any_admin
def list_hospitals_admin():
    """
    Return hospital list from hospital_matcher.
    HOSPITAL_ADMIN sees only their own.
    """
    from models.hospital_matcher import get_hospital_matcher
    matcher = get_hospital_matcher()
    admin = get_current_admin()

    hospitals = matcher.hospitals or []
    if admin.role == AdminRole.HOSPITAL_ADMIN:
        hospitals = [h for h in hospitals if h.get('id') == admin.hospital_id]

    return jsonify({
        'success': True,
        'hospitals': hospitals,
        'count': len(hospitals)
    }), 200


@admin_bp.route('/hospitals/<int:hospital_id>', methods=['PUT'])
@hospital_admin_or_above
def update_hospital(hospital_id):
    """
    Update hospital editable fields (stored in an override JSON file).
    Full hospital data stays in hospital_matcher; overrides are merged at read time.
    """
    admin = get_current_admin()
    allowed, err = enforce_hospital_scope(hospital_id)
    if not allowed:
        return jsonify(err), 403

    data = request.get_json() or {}
    OVERRIDE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'hospital_overrides.json')

    try:
        overrides = {}
        if os.path.exists(OVERRIDE_FILE):
            with open(OVERRIDE_FILE) as f:
                overrides = json.load(f)

        key = str(hospital_id)
        if key not in overrides:
            overrides[key] = {}

        # Allowed editable fields
        editable = ['phone', 'email', 'capacity', 'notes', 'is_accepting_patients']
        for field in editable:
            if field in data:
                overrides[key][field] = data[field]
        overrides[key]['updated_at'] = datetime.utcnow().isoformat()
        overrides[key]['updated_by'] = admin.email

        os.makedirs(os.path.dirname(OVERRIDE_FILE), exist_ok=True)
        with open(OVERRIDE_FILE, 'w') as f:
            json.dump(overrides, f, indent=2)

        return jsonify({
            'success': True,
            'message': 'Hospital updated',
            'overrides': overrides[key]
        }), 200
    except Exception as e:
        logger.error(f"Error updating hospital: {e}")
        return jsonify({'error': str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ════════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/analytics/summary', methods=['GET'])
@any_admin
def analytics_summary():
    """Dashboard KPI cards: totals, by-status counts, today's numbers."""
    admin = get_current_admin()

    q = Appointment.query
    if admin.role == AdminRole.HOSPITAL_ADMIN:
        q = q.filter_by(hospital_id=admin.hospital_id)

    total = q.count()
    by_status = {s: q.filter_by(status=s).count() for s in AppointmentStatus.ALL}

    today = datetime.utcnow().date()
    today_q = q.filter(
        Appointment.appointment_date >= datetime.combine(today, datetime.min.time()),
        Appointment.appointment_date < datetime.combine(today + timedelta(days=1), datetime.min.time())
    )
    today_total = today_q.count()
    today_pending = today_q.filter_by(status=AppointmentStatus.PENDING).count()

    doctor_count = Doctor.query
    if admin.role == AdminRole.HOSPITAL_ADMIN:
        doctor_count = doctor_count.filter_by(hospital_id=admin.hospital_id)
    doctor_count = doctor_count.filter_by(is_active=True).count()

    open_tickets = SupportTicket.query.filter_by(status=TicketStatus.OPEN).count()

    return jsonify({
        'success': True,
        'summary': {
            'total_appointments': total,
            'by_status': by_status,
            'today': {
                'total': today_total,
                'pending': today_pending
            },
            'active_doctors': doctor_count,
            'open_support_tickets': open_tickets,
        }
    }), 200


@admin_bp.route('/analytics/trends', methods=['GET'])
@hospital_admin_or_above
def analytics_trends():
    """
    Daily appointment counts for the last N days.
    Query param: days (default 30)
    """
    admin = get_current_admin()
    days = min(request.args.get('days', 30, type=int), 90)

    q = Appointment.query
    if admin.role == AdminRole.HOSPITAL_ADMIN:
        q = q.filter_by(hospital_id=admin.hospital_id)

    since = datetime.utcnow() - timedelta(days=days)
    appointments = q.filter(Appointment.created_at >= since).all()

    # Aggregate by date
    daily: dict[str, dict] = defaultdict(lambda: {
        'total': 0, 'confirmed': 0, 'cancelled': 0, 'completed': 0
    })
    for apt in appointments:
        day_key = apt.created_at.strftime('%Y-%m-%d')
        daily[day_key]['total'] += 1
        if apt.status in (AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED,
                          AppointmentStatus.CANCELLED):
            daily[day_key][apt.status.lower()] += 1

    # Specialty demand
    specialty_demand: dict[str, int] = defaultdict(int)
    for apt in appointments:
        if apt.specialty:
            specialty_demand[apt.specialty] += 1

    sorted_days = sorted(daily.items())
    return jsonify({
        'success': True,
        'period_days': days,
        'daily_trends': [{'date': k, **v} for k, v in sorted_days],
        'specialty_demand': dict(sorted(specialty_demand.items(), key=lambda x: -x[1])[:10])
    }), 200


# ════════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ════════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/notifications', methods=['GET'])
@any_admin
def list_notifications():
    """List notifications (admin view — all channels)."""
    admin = get_current_admin()

    q = Notification.query
    if request.args.get('user_id'):
        q = q.filter_by(user_id=request.args['user_id'])

    page = request.args.get('page', 1, type=int)
    paginated = q.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )

    return jsonify({
        'success': True,
        'notifications': [n.to_dict() for n in paginated.items],
        'total': paginated.total
    }), 200


@admin_bp.route('/notifications/send', methods=['POST'])
@hospital_admin_or_above
def send_notification():
    """Manually send a notification to a user."""
    admin = get_current_admin()
    data = request.get_json() or {}

    user_id = data.get('user_id', '').strip()
    message = data.get('message', '').strip()

    if not user_id or not message:
        return jsonify({'error': 'user_id and message are required'}), 400

    notif = create_custom_notification(
        user_id=user_id,
        message=message,
        notif_type=data.get('type', NotificationType.GENERAL),
        appointment_id=data.get('appointment_id'),
        sent_by_admin_id=admin.id
    )

    if notif:
        return jsonify({'success': True, 'notification': notif.to_dict()}), 201
    return jsonify({'error': 'Failed to send notification'}), 500


# ════════════════════════════════════════════════════════════════════════════════
# SUPPORT TICKETS
# ════════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/support-tickets', methods=['GET'])
@any_admin
def list_tickets():
    """List support tickets. SUPPORT_STAFF and PLATFORM_ADMIN see all."""
    q = SupportTicket.query

    status = request.args.get('status')
    if status and status in TicketStatus.ALL:
        q = q.filter_by(status=status)

    priority = request.args.get('priority')
    if priority and priority in TicketPriority.ALL:
        q = q.filter_by(priority=priority)

    page = request.args.get('page', 1, type=int)
    paginated = q.order_by(SupportTicket.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return jsonify({
        'success': True,
        'tickets': [t.to_dict() for t in paginated.items],
        'total': paginated.total
    }), 200


@admin_bp.route('/support-tickets/<ticket_id>', methods=['PUT'])
@any_admin
def update_ticket(ticket_id):
    """Update ticket status / assign admin."""
    admin = get_current_admin()
    ticket = SupportTicket.query.get_or_404(ticket_id, description='Ticket not found')

    data = request.get_json() or {}
    new_status = data.get('status', '').upper()

    if new_status:
        if new_status not in TicketStatus.ALL:
            return jsonify({'error': 'Invalid status', 'valid': TicketStatus.ALL}), 400
        ticket.status = new_status
        if new_status == TicketStatus.RESOLVED:
            ticket.resolve()

    if data.get('priority'):
        if data['priority'] not in TicketPriority.ALL:
            return jsonify({'error': 'Invalid priority'}), 400
        ticket.priority = data['priority']

    ticket.admin_id = admin.id
    db.session.commit()

    return jsonify({'success': True, 'ticket': ticket.to_dict()}), 200


# Patient: create a support ticket (no admin auth needed)
@admin_bp.route('/support-tickets', methods=['POST'])
def create_ticket():
    """Patient creates a support ticket (public endpoint)."""
    data = request.get_json() or {}
    user_id = data.get('user_id', '').strip()
    subject = data.get('subject', '').strip()

    if not user_id or not subject:
        return jsonify({'error': 'user_id and subject are required'}), 400

    ticket = SupportTicket(
        user_id=user_id,
        subject=subject,
        description=data.get('description', ''),
        priority=data.get('priority', TicketPriority.MEDIUM)
    )
    db.session.add(ticket)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Support ticket created',
        'ticket': ticket.to_dict()
    }), 201


# ════════════════════════════════════════════════════════════════════════════════
# ADMIN USER MANAGEMENT (PLATFORM_ADMIN only)
# ════════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/users', methods=['GET'])
@platform_admin_only
def list_admin_users():
    """List all admin accounts."""
    admins = AdminUser.query.order_by(AdminUser.created_at.desc()).all()
    return jsonify({
        'success': True,
        'admins': [a.to_dict() for a in admins],
        'count': len(admins)
    }), 200


@admin_bp.route('/users', methods=['POST'])
@platform_admin_only
def create_admin_user():
    """Create a new admin account."""
    data = request.get_json() or {}
    required = ['email', 'role', 'firebase_uid']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {missing}'}), 400

    if data['role'] not in AdminRole.ALL:
        return jsonify({'error': 'Invalid role', 'valid_roles': AdminRole.ALL}), 400

    if AdminUser.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Admin with this email already exists'}), 409

    admin = AdminUser(
        email=data['email'].strip().lower(),
        firebase_uid=data['firebase_uid'],
        role=data['role'],
        hospital_id=data.get('hospital_id'),
        permissions=data.get('permissions', []),
        is_active=data.get('is_active', True)
    )
    db.session.add(admin)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Admin user created',
        'admin': admin.to_dict()
    }), 201


@admin_bp.route('/users/<admin_id>', methods=['PUT'])
@platform_admin_only
def update_admin_user(admin_id):
    """Update admin role / status."""
    admin = AdminUser.query.get_or_404(admin_id, description='Admin not found')
    data = request.get_json() or {}

    if 'role' in data:
        if data['role'] not in AdminRole.ALL:
            return jsonify({'error': 'Invalid role'}), 400
        admin.role = data['role']
    if 'hospital_id' in data:
        admin.hospital_id = data['hospital_id']
    if 'is_active' in data:
        admin.is_active = bool(data['is_active'])
    if 'permissions' in data:
        admin.permissions = data['permissions']

    db.session.commit()
    return jsonify({'success': True, 'admin': admin.to_dict()}), 200


# ════════════════════════════════════════════════════════════════════════════════
# PATIENT-FACING: notifications (no admin auth — patient uses their own user_id)
# ════════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/my-notifications/<user_id>', methods=['GET'])
def my_notifications(user_id):
    """Patient fetches their own notifications (no admin auth)."""
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    notifs = get_user_notifications(user_id, unread_only=unread_only)
    unread = get_unread_count(user_id)
    return jsonify({'success': True, 'notifications': notifs, 'unread_count': unread}), 200


@admin_bp.route('/my-notifications/<user_id>/read', methods=['PUT'])
def mark_read(user_id):
    """Mark notifications as read."""
    data = request.get_json() or {}
    ids = data.get('notification_ids')  # None = mark all
    count = mark_notifications_read(user_id, notification_ids=ids)
    return jsonify({'success': True, 'marked_read': count}), 200


# ════════════════════════════════════════════════════════════════════════════════
# SEED UTILITY (dev only)
# ════════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/seed', methods=['POST'])
def seed_admin_users():
    """
    Seed 3 demo admin accounts (one per role).
    Only works when FLASK_ENV=development.
    """
    if os.getenv('FLASK_ENV', 'development') != 'development':
        return jsonify({'error': 'Only available in development'}), 403

    seeds = [
        {
            'email': 'platform@mediconnect.ai',
            'firebase_uid': 'platform-admin-uid-001',
            'role': AdminRole.PLATFORM_ADMIN,
            'hospital_id': None,
            'permissions': []
        },
        {
            'email': 'hospital@mediconnect.ai',
            'firebase_uid': 'hospital-admin-uid-001',
            'role': AdminRole.HOSPITAL_ADMIN,
            'hospital_id': 1,
            'permissions': ['approve_bookings', 'manage_doctors']
        },
        {
            'email': 'support@mediconnect.ai',
            'firebase_uid': 'support-staff-uid-001',
            'role': AdminRole.SUPPORT_STAFF,
            'hospital_id': None,
            'permissions': ['manage_tickets']
        }
    ]

    created = []
    for seed in seeds:
        if not AdminUser.query.filter_by(email=seed['email']).first():
            admin = AdminUser(**seed)
            db.session.add(admin)
            created.append(seed['email'])

    db.session.commit()
    return jsonify({
        'success': True,
        'created': created,
        'message': f'Seeded {len(created)} admin users. Use token: {ADMIN_SECRET_TOKEN}'
    }), 201
