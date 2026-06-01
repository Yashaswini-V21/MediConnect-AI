"""
Verify seeded accounts by sending OTPs and performing login via Flask test client.
Run with: python backend/scripts/verify_accounts.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import app
import json


def verify(email):
    with app.app_context():
        client = app.test_client()
        # Send OTP
        r = client.post('/api/auth/send-otp', json={'email': email})
        data = r.get_json() or {}
        otp = data.get('otp_dev')
        print(f'Send OTP response for {email}:', data)

        if not otp:
            print('No dev OTP returned; cannot verify login automatically.')
            return

        # Login using OTP
        r2 = client.post('/api/auth/login', json={'email': email, 'otp': otp})
        data2 = r2.get_json() or {}
        print(f'Login response for {email}:', json.dumps(data2, indent=2))


if __name__ == '__main__':
    emails = ['yash123@gmail.com', 'admin123@gmail.com']
    for e in emails:
        print('---')
        if e.endswith('@gmail.com') and e.startswith('admin'):
            print(f'Admin account exists: {e}. To login via /api/admin/login you must set the ADMIN_SECRET_TOKEN environment variable on the server and use that token.')
            continue
        verify(e)
