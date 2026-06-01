"""
Seed script to create a demo user and an admin account.
Run with: python backend/scripts/seed_accounts.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import app
from models.user_model import db, User
from models.admin_model import AdminUser, AdminRole
import uuid


def _uuid():
    return str(uuid.uuid4())


def seed():
    with app.app_context():
        # Create user
        user_email = 'yash123@gmail/com'
        user_password = 'yash123'
        user = User.query.filter_by(email=user_email).first()
        if user:
            print(f'User already exists: {user_email} (id={user.id})')
        else:
            user = User(email=user_email, full_name='Yash User')
            user.set_password(user_password)
            db.session.add(user)
            db.session.commit()
            print(f'Created user: {user_email} (id={user.id})')

        # Create admin
        admin_email = 'admin123@gmail.com'
        admin = AdminUser.query.filter_by(email=admin_email).first()
        if admin:
            print(f'Admin already exists: {admin_email} (id={admin.id})')
        else:
            admin = AdminUser(
                email=admin_email,
                firebase_uid=_uuid(),
                role=AdminRole.PLATFORM_ADMIN,
                hospital_id=None
            )
            db.session.add(admin)
            db.session.commit()
            print(f'Created admin: {admin_email} (id={admin.id})')

        print('\nNote: Admin login requires ADMIN_SECRET_TOKEN environment variable to be set.')


if __name__ == '__main__':
    seed()
