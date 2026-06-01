"""
Fix the seeded user's email if it was created with an invalid format.
Run with: python backend/scripts/fix_yash_email.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import app
from models.user_model import db, User


def fix():
    with app.app_context():
        bad = 'yash123@gmail/com'
        good = 'yash123@gmail.com'
        user = User.query.filter_by(email=bad).first()
        if not user:
            print('No user with invalid email found; nothing to do.')
            return
        if User.query.filter_by(email=good).first():
            print('A user with the corrected email already exists; removing bad one.')
            db.session.delete(user)
            db.session.commit()
            return
        user.email = good
        db.session.commit()
        print(f'Updated user email from {bad} to {good} (id={user.id})')


if __name__ == '__main__':
    fix()
