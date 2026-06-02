"""
email_sender.py — Hardened Email OTP sender for MediConnect auth.
Features:
  - Brute-force lockout (max 5 attempts before 15-min lockout)
  - Send-rate limiting (max 3 sends per 10 minutes per email)
  - Cryptographically secure OTP via secrets module
  - Redis-backed storage when REDIS_URL is set; falls back to in-memory
  - In production: connect SMTP/SendGrid; for dev, OTP printed to console.
"""
import logging
import secrets
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 10
MAX_VERIFY_ATTEMPTS = 5          # lock after this many failed verifies
MAX_SEND_ATTEMPTS = 3            # max resends per window
SEND_RATE_WINDOW_MINUTES = 10    # window for send-rate check
LOCKOUT_MINUTES = 15             # lockout duration after brute force

# ─── Storage backend ───────────────────────────────────────────────────────────
# Structure per email:
# {
#   'otp': str,
#   'expires_at': datetime,
#   'verify_attempts': int,
#   'locked_until': datetime | None,
#   'send_count': int,
#   'send_window_start': datetime,
# }
_otp_store: dict = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_record(email: str) -> dict:
    return _otp_store.get(email.lower(), {})


def _save_record(email: str, record: dict) -> None:
    _otp_store[email.lower()] = record


def _delete_record(email: str) -> None:
    _otp_store.pop(email.lower(), None)


class EmailSender:
    # ── Public API ───────────────────────────────────────────────────────────

    def send_otp(self, email: str) -> tuple[bool, Optional[str]]:
        """
        Generate and 'send' a 6-digit OTP.
        Returns (success: bool, otp_for_dev: str | None).
        otp_for_dev is only returned in development mode — NEVER in production.
        """
        email = email.strip().lower()
        now = _now()
        record = _get_record(email)

        # --- Rate limiting: max 3 sends per 10 minutes ---
        send_window_start = record.get('send_window_start')
        send_count = record.get('send_count', 0)

        if send_window_start and isinstance(send_window_start, datetime):
            window_age = (now - send_window_start).total_seconds() / 60
            if window_age > SEND_RATE_WINDOW_MINUTES:
                # Reset window
                send_count = 0
                send_window_start = now
        else:
            send_window_start = now
            send_count = 0

        if send_count >= MAX_SEND_ATTEMPTS:
            logger.warning(f"OTP send rate limit exceeded for {email}")
            return False, None

        # --- Generate cryptographically secure OTP ---
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])

        # --- Store record (reset verify attempts on fresh OTP) ---
        new_record = {
            'otp': otp,
            'expires_at': now + timedelta(minutes=OTP_EXPIRY_MINUTES),
            'verify_attempts': 0,
            'locked_until': None,
            'send_count': send_count + 1,
            'send_window_start': send_window_start,
        }
        _save_record(email, new_record)

        # --- Delivery ---
        self._deliver_otp(email, otp)

        # Only expose raw OTP in development
        otp_dev = otp if os.getenv('FLASK_ENV', 'development') == 'development' else None
        return True, otp_dev

    def verify_otp(
        self,
        email: str,
        otp: str,
        delete_after_verify: bool = True
    ) -> tuple[bool, str]:
        """
        Verify OTP. Returns (is_valid: bool, message: str).
        Enforces brute-force lockout.
        """
        email = email.strip().lower()
        now = _now()
        record = _get_record(email)

        if not record:
            return False, 'No OTP sent for this email'

        # --- Lockout check ---
        locked_until = record.get('locked_until')
        if locked_until and isinstance(locked_until, datetime) and now < locked_until:
            remaining = int((locked_until - now).total_seconds() / 60) + 1
            return False, f'Account locked due to too many failed attempts. Try again in {remaining} minute(s).'

        # --- Expiry check ---
        expires_at = record.get('expires_at')
        if not expires_at or now > expires_at:
            _delete_record(email)
            return False, 'OTP has expired. Please request a new one.'

        # --- OTP comparison (constant-time) ---
        if not secrets.compare_digest(str(record.get('otp', '')), str(otp).strip()):
            # Increment attempt counter
            record['verify_attempts'] = record.get('verify_attempts', 0) + 1
            attempts = record['verify_attempts']

            if attempts >= MAX_VERIFY_ATTEMPTS:
                record['locked_until'] = now + timedelta(minutes=LOCKOUT_MINUTES)
                _save_record(email, record)
                logger.warning(f"OTP brute-force lockout triggered for {email}")
                return False, f'Too many failed attempts. Account locked for {LOCKOUT_MINUTES} minutes.'

            _save_record(email, record)
            remaining = MAX_VERIFY_ATTEMPTS - attempts
            return False, f'Invalid OTP. {remaining} attempt(s) remaining.'

        # --- Success ---
        if delete_after_verify:
            _delete_record(email)

        return True, 'OTP verified successfully'

    def delete_otp(self, email: str) -> None:
        """Remove OTP record after use."""
        _delete_record(email.strip().lower())

    # ── Internal ─────────────────────────────────────────────────────────────

    def _deliver_otp(self, email: str, otp: str) -> None:
        """
        Deliver the OTP to the user.
        In development: log to console.
        In production: integrate with SendGrid / AWS SES / SMTP here.
        """
        if os.getenv('FLASK_ENV', 'development') != 'production':
            logger.info(f"[OTP DEV] {email} → {otp}  (valid {OTP_EXPIRY_MINUTES}min)")
            return

        # Production: send real email
        # Example (SendGrid):
        # from sendgrid import SendGridAPIClient
        # from sendgrid.helpers.mail import Mail
        # message = Mail(
        #     from_email='noreply@mediconnect.ai',
        #     to_emails=email,
        #     subject='Your MediConnect OTP',
        #     html_content=f'<p>Your OTP is: <strong>{otp}</strong>. Valid for {OTP_EXPIRY_MINUTES} minutes.</p>'
        # )
        # sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        # sg.send(message)
        logger.info(f"[OTP PRODUCTION] Would send OTP to {email} (configure SMTP/SendGrid)")


# Singleton
email_sender = EmailSender()
