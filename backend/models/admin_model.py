"""
MediConnect-AI M3: Admin Models
SQLAlchemy ORM for the 5 new M3 database tables.
Tables: admin_users, appointments, doctors, notifications, support_tickets
"""

import uuid
from datetime import datetime
from models.user_model import db


# ─── Enums as string constants ────────────────────────────────────────────────

class AdminRole:
    PLATFORM_ADMIN = 'PLATFORM_ADMIN'
    HOSPITAL_ADMIN  = 'HOSPITAL_ADMIN'
    SUPPORT_STAFF   = 'SUPPORT_STAFF'
    ALL = [PLATFORM_ADMIN, HOSPITAL_ADMIN, SUPPORT_STAFF]


class AppointmentStatus:
    PENDING   = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'
    NO_SHOW   = 'NO_SHOW'
    ALL = [PENDING, CONFIRMED, COMPLETED, CANCELLED, NO_SHOW]

    # Valid state transitions
    TRANSITIONS = {
        PENDING:   [CONFIRMED, CANCELLED],
        CONFIRMED: [COMPLETED, CANCELLED, NO_SHOW],
        COMPLETED: [],
        CANCELLED: [],
        NO_SHOW:   [],
    }

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        return target in cls.TRANSITIONS.get(current, [])


class UrgencyLevel:
    HIGH   = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW    = 'LOW'
    ALL = [HIGH, MEDIUM, LOW]


class NotificationType:
    BOOKING_CONFIRMATION = 'BOOKING_CONFIRMATION'
    CONFIRMED            = 'CONFIRMED'
    CANCELLED            = 'CANCELLED'
    RESCHEDULED          = 'RESCHEDULED'
    REMINDER             = 'REMINDER'
    GENERAL              = 'GENERAL'
    ALL = [BOOKING_CONFIRMATION, CONFIRMED, CANCELLED, RESCHEDULED, REMINDER, GENERAL]


class NotificationChannel:
    IN_APP = 'IN_APP'
    EMAIL  = 'EMAIL'
    SMS    = 'SMS'
    ALL = [IN_APP, EMAIL, SMS]


class TicketStatus:
    OPEN        = 'OPEN'
    IN_PROGRESS = 'IN_PROGRESS'
    RESOLVED    = 'RESOLVED'
    ALL = [OPEN, IN_PROGRESS, RESOLVED]


class TicketPriority:
    LOW    = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH   = 'HIGH'
    ALL = [LOW, MEDIUM, HIGH]


# ─── Helper ───────────────────────────────────────────────────────────────────

def _uuid() -> str:
    return str(uuid.uuid4())


# ─── Models ───────────────────────────────────────────────────────────────────

class AdminUser(db.Model):
    """
    Admin users with role-based access control.
    Roles: PLATFORM_ADMIN | HOSPITAL_ADMIN | SUPPORT_STAFF
    """
    __tablename__ = 'admin_users'

    id           = db.Column(db.String(36), primary_key=True, default=_uuid)
    email        = db.Column(db.String(120), unique=True, nullable=False, index=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False)
    role         = db.Column(db.String(20), nullable=False)
    # hospital_id is NULL for PLATFORM_ADMIN / SUPPORT_STAFF
    hospital_id  = db.Column(db.Integer, nullable=True)
    permissions  = db.Column(db.JSON, default=list)
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    last_login   = db.Column(db.DateTime, nullable=True)

    # Relationships
    notifications_sent = db.relationship(
        'Notification', backref='sender', lazy='dynamic',
        foreign_keys='Notification.sent_by_admin_id'
    )
    tickets_handled = db.relationship(
        'SupportTicket', backref='handler', lazy='dynamic',
        foreign_keys='SupportTicket.admin_id'
    )

    def to_dict(self):
        return {
            'id':          self.id,
            'email':       self.email,
            'role':        self.role,
            'hospital_id': self.hospital_id,
            'permissions': self.permissions or [],
            'is_active':   self.is_active,
            'created_at':  self.created_at.isoformat(),
            'last_login':  self.last_login.isoformat() if self.last_login else None,
        }

    def has_permission(self, permission: str) -> bool:
        """Check if this admin has a specific permission string."""
        if self.role == AdminRole.PLATFORM_ADMIN:
            return True
        return permission in (self.permissions or [])

    def can_access_hospital(self, hospital_id: int) -> bool:
        """PLATFORM_ADMIN sees all; HOSPITAL_ADMIN sees only their own."""
        if self.role == AdminRole.PLATFORM_ADMIN:
            return True
        return self.hospital_id == hospital_id

    def __repr__(self):
        return f'<AdminUser {self.email} [{self.role}]>'


class Doctor(db.Model):
    """
    Doctor profiles linked to a hospital.
    available_slots: JSON dict { "Mon": ["09:00","10:00"], ... }
    """
    __tablename__ = 'doctors'

    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hospital_id       = db.Column(db.Integer, nullable=False, index=True)
    name              = db.Column(db.String(100), nullable=False)
    specialty         = db.Column(db.String(100), nullable=False)
    degree            = db.Column(db.String(100), nullable=True)
    experience_years  = db.Column(db.Integer, default=0)
    available_slots   = db.Column(db.JSON, default=dict)   # { "Mon": ["09:00","10:30"] }
    max_daily_bookings = db.Column(db.Integer, default=20)
    is_active         = db.Column(db.Boolean, default=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy='dynamic')

    def to_dict(self):
        return {
            'id':                 self.id,
            'hospital_id':        self.hospital_id,
            'name':               self.name,
            'specialty':          self.specialty,
            'degree':             self.degree,
            'experience_years':   self.experience_years,
            'available_slots':    self.available_slots or {},
            'max_daily_bookings': self.max_daily_bookings,
            'is_active':          self.is_active,
            'created_at':         self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Doctor {self.name} [{self.specialty}] at hospital {self.hospital_id}>'


class Appointment(db.Model):
    """
    Patient appointment with full state machine.
    States: PENDING → CONFIRMED → COMPLETED
                    ↘ CANCELLED
            CONFIRMED → NO_SHOW
    """
    __tablename__ = 'appointments'

    id               = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id          = db.Column(db.String(128), nullable=False, index=True)   # Firebase UID or int user id
    hospital_id      = db.Column(db.Integer, nullable=False, index=True)
    doctor_id        = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_time = db.Column(db.String(20), nullable=True)                  # "09:00 AM"
    status           = db.Column(db.String(20), default=AppointmentStatus.PENDING, index=True)
    urgency_level    = db.Column(db.String(10), nullable=True)
    specialty        = db.Column(db.String(100), nullable=True)
    patient_name     = db.Column(db.String(100), nullable=True)
    patient_phone    = db.Column(db.String(20), nullable=True)
    patient_email    = db.Column(db.String(120), nullable=True)
    reason           = db.Column(db.Text, nullable=True)
    notes            = db.Column(db.Text, nullable=True)
    hospital_name    = db.Column(db.String(200), nullable=True)                 # Denormalized for speed
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    notifications = db.relationship('Notification', backref='appointment', lazy='dynamic',
                                    foreign_keys='Notification.appointment_id')

    def transition_to(self, new_status: str) -> bool:
        """Attempt a state transition. Returns True on success."""
        if AppointmentStatus.can_transition(self.status, new_status):
            self.status = new_status
            self.updated_at = datetime.utcnow()
            return True
        return False

    def to_dict(self):
        return {
            'id':               self.id,
            'user_id':          self.user_id,
            'hospital_id':      self.hospital_id,
            'hospital_name':    self.hospital_name,
            'doctor_id':        self.doctor_id,
            'doctor_name':      self.doctor.name if self.doctor else None,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'appointment_time': self.appointment_time,
            'status':           self.status,
            'urgency_level':    self.urgency_level,
            'specialty':        self.specialty,
            'patient_name':     self.patient_name,
            'patient_phone':    self.patient_phone,
            'patient_email':    self.patient_email,
            'reason':           self.reason,
            'notes':            self.notes,
            'created_at':       self.created_at.isoformat(),
            'updated_at':       self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Appointment {self.id[:8]} [{self.status}] user={self.user_id[:8]}>'


class Notification(db.Model):
    """
    In-app notifications triggered by appointment state changes.
    Channel: IN_APP (M3) | EMAIL / SMS (M5)
    """
    __tablename__ = 'notifications'

    id                = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id           = db.Column(db.String(128), nullable=False, index=True)
    appointment_id    = db.Column(db.String(36), db.ForeignKey('appointments.id'), nullable=True)
    sent_by_admin_id  = db.Column(db.String(36), db.ForeignKey('admin_users.id'), nullable=True)
    type              = db.Column(db.String(30), default=NotificationType.GENERAL)
    message           = db.Column(db.Text, nullable=False)
    channel           = db.Column(db.String(10), default=NotificationChannel.IN_APP)
    is_read           = db.Column(db.Boolean, default=False)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':             self.id,
            'user_id':        self.user_id,
            'appointment_id': self.appointment_id,
            'type':           self.type,
            'message':        self.message,
            'channel':        self.channel,
            'is_read':        self.is_read,
            'created_at':     self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Notification {self.id[:8]} to {self.user_id[:8]} [{self.type}]>'


class SupportTicket(db.Model):
    """
    Support tickets raised by patients, handled by SUPPORT_STAFF.
    """
    __tablename__ = 'support_tickets'

    id          = db.Column(db.String(36), primary_key=True, default=_uuid)
    user_id     = db.Column(db.String(128), nullable=False, index=True)
    admin_id    = db.Column(db.String(36), db.ForeignKey('admin_users.id'), nullable=True)
    subject     = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status      = db.Column(db.String(20), default=TicketStatus.OPEN, index=True)
    priority    = db.Column(db.String(10), default=TicketPriority.MEDIUM)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def resolve(self):
        self.status = TicketStatus.RESOLVED
        self.resolved_at = datetime.utcnow()

    def to_dict(self):
        return {
            'id':          self.id,
            'user_id':     self.user_id,
            'admin_id':    self.admin_id,
            'subject':     self.subject,
            'description': self.description,
            'status':      self.status,
            'priority':    self.priority,
            'created_at':  self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
        }

    def __repr__(self):
        return f'<SupportTicket {self.id[:8]} [{self.status}] "{self.subject[:30]}">'
