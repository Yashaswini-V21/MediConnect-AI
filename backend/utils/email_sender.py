"""
email_sender.py — Email OTP sender stub for MediConnect auth.
In production, connect to SendGrid or AWS SES.
For dev, OTPs are printed to console and stored in memory.
"""
import logging
import random
import string
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory OTP store: { email: { otp, expires_at } }
_otp_store: dict = {}

OTP_EXPIRY_MINUTES = 10


class EmailSender:
    def send_otp(self, email: str) -> tuple[bool, str]:
        """Generate and 'send' OTP. Returns (success, otp_for_dev)."""
        otp = ''.join(random.choices(string.digits, k=6))
        _otp_store[email] = {
            'otp': otp,
            'expires_at': datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        }
        logger.info(f"[OTP DEV] {email} → {otp}  (valid {OTP_EXPIRY_MINUTES}min)")
        # In production: send email here
        return True, otp

    def verify_otp(self, email: str, otp: str, delete_after_verify: bool = True) -> tuple[bool, str]:
        """Verify OTP. Returns (is_valid, message)."""
        record = _otp_store.get(email)
        if not record:
            return False, 'No OTP sent for this email'
        if datetime.utcnow() > record['expires_at']:
            _otp_store.pop(email, None)
            return False, 'OTP has expired'
        if record['otp'] != str(otp).strip():
            return False, 'Invalid OTP'
        if delete_after_verify:
            _otp_store.pop(email, None)
        return True, 'OTP verified successfully'

    def delete_otp(self, email: str):
        """Remove OTP after use."""
        _otp_store.pop(email, None)


# Singleton
email_sender = EmailSender()
