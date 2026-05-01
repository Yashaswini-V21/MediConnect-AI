"""
MediConnect-AI M3: Notification Service
Creates and manages in-app notifications.
Email/SMS stubs are ready for M5 (Celery + SendGrid/Twilio).
"""

import logging
import os
from datetime import datetime
from models.user_model import db
from models.admin_model import (
    Notification, Appointment,
    NotificationType, NotificationChannel, AppointmentStatus
)

logger = logging.getLogger(__name__)

class NotificationService:
    """
    M5: Core Notification Service for email, SMS and in-app alerts.
    """
    def __init__(self):
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')

    def send_booking_confirmation(self, appointment, patient_email=None, patient_phone=None):
        """Send sync in-app + async email/SMS confirmations"""
        # In-app notification
        notify_appointment_status_change(appointment)
        
        # Stubs for M5 (SendGrid/Twilio integration)
        if patient_email:
            logger.info(f"M5 STUB: Sending SendGrid email to {patient_email}")
        if patient_phone:
            logger.info(f"M5 STUB: Sending Twilio SMS to {patient_phone}")

    def send_status_update(self, appointment, patient_email=None, patient_phone=None):
        """Notify patient of confirmation, cancellation or rescheduling"""
        notify_appointment_status_change(appointment)
        
        # M5 Stubs
        msg = f"Status update: {appointment.status} for appointment on {appointment.appointment_date}"
        logger.info(f"M5 STUB: {msg}")

# ─── Message templates ────────────────────────────────────────────────────────

_MESSAGES = {
    AppointmentStatus.PENDING: (
        NotificationType.BOOKING_CONFIRMATION,
        "Your appointment request at {hospital} on {date} has been received and is pending confirmation."
    ),
    AppointmentStatus.CONFIRMED: (
        NotificationType.CONFIRMED,
        "Great news! Your appointment at {hospital} on {date} at {time} has been CONFIRMED. Please arrive 10 minutes early."
    ),
    AppointmentStatus.CANCELLED: (
        NotificationType.CANCELLED,
        "Your appointment at {hospital} on {date} has been cancelled. Please book a new appointment if needed."
    ),
    AppointmentStatus.COMPLETED: (
        NotificationType.GENERAL,
        "Your appointment at {hospital} on {date} has been marked as completed. Thank you for visiting!"
    ),
    AppointmentStatus.NO_SHOW: (
        NotificationType.GENERAL,
        "You missed your appointment at {hospital} on {date}. Please contact the hospital to reschedule."
    ),
}


# ─── Core functions ───────────────────────────────────────────────────────────

def notify_appointment_status_change(
    appointment: Appointment,
    sent_by_admin_id: str | None = None
) -> Notification | None:
    """
    Create an in-app notification when appointment status changes.
    Called automatically by admin_routes after every status update.
    """
    try:
        template = _MESSAGES.get(appointment.status)
        if not template:
            return None

        notif_type, msg_template = template
        date_str = appointment.appointment_date.strftime('%d %b %Y') if appointment.appointment_date else 'N/A'

        message = msg_template.format(
            hospital=appointment.hospital_name or f'Hospital #{appointment.hospital_id}',
            date=date_str,
            time=appointment.appointment_time or ''
        )

        notif = Notification(
            user_id=appointment.user_id,
            appointment_id=appointment.id,
            sent_by_admin_id=sent_by_admin_id,
            type=notif_type,
            message=message,
            channel=NotificationChannel.IN_APP,
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()

        logger.info(f"Notification created: {notif.id[:8]} → user {appointment.user_id[:8]} [{notif_type}]")
        return notif

    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        db.session.rollback()
        return None


def create_custom_notification(
    user_id: str,
    message: str,
    notif_type: str = NotificationType.GENERAL,
    appointment_id: str | None = None,
    sent_by_admin_id: str | None = None,
    channel: str = NotificationChannel.IN_APP
) -> Notification | None:
    """
    Create a custom notification for any user.
    Used by admins to send manual messages.
    """
    try:
        notif = Notification(
            user_id=user_id,
            appointment_id=appointment_id,
            sent_by_admin_id=sent_by_admin_id,
            type=notif_type,
            message=message,
            channel=channel,
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()
        logger.info(f"Custom notification sent to user {user_id[:8]}")
        return notif
    except Exception as e:
        logger.error(f"Failed to create custom notification: {e}")
        db.session.rollback()
        return None


def get_user_notifications(user_id: str, unread_only: bool = False) -> list[dict]:
    """Fetch all notifications for a patient user."""
    query = Notification.query.filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    return [n.to_dict() for n in notifications]


def mark_notifications_read(user_id: str, notification_ids: list[str] | None = None) -> int:
    """
    Mark notifications as read.
    If notification_ids is None, marks ALL unread for user.
    Returns count of updated rows.
    """
    try:
        query = Notification.query.filter_by(user_id=user_id, is_read=False)
        if notification_ids:
            query = query.filter(Notification.id.in_(notification_ids))
        count = query.update({'is_read': True}, synchronize_session=False)
        db.session.commit()
        return count
    except Exception as e:
        logger.error(f"Failed to mark notifications read: {e}")
        db.session.rollback()
        return 0


def get_unread_count(user_id: str) -> int:
    """Quick unread count for notification badge."""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


# ─── M5 stubs (async email / SMS) ─────────────────────────────────────────────

def send_email_notification_stub(user_email: str, subject: str, body: str):
    """
    STUB — wired to Celery + SendGrid in M5.
    Logs intent for now.
    """
    logger.info(f"[EMAIL STUB] To: {user_email} | Subject: {subject}")


def send_sms_notification_stub(phone: str, message: str):
    """
    STUB — wired to Celery + Twilio in M5.
    Logs intent for now.
    """
    logger.info(f"[SMS STUB] To: {phone} | Message: {message[:60]}")
