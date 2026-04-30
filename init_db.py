#!/usr/bin/env python3
"""
M3 Database Initialization Script
Run this to create all M3 tables: admin_users, appointments, doctors, notifications, support_tickets
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import app, db
from backend.models.admin_model import (
    AdminUser, Doctor, Appointment, 
    Notification, SupportTicket
)

def init_database():
    """Create all database tables"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database initialization complete!")
            print("\n📋 M3 Tables created:")
            print("   1. admin_users    - Platform/Hospital admins with RBAC")
            print("   2. doctors        - Doctor profiles per hospital")
            print("   3. appointments   - Patient appointments (state machine)")
            print("   4. notifications  - In-app + SMS/Email notifications")
            print("   5. support_tickets - Support ticket tracking")
            print("\n📊 Enum Classes available:")
            print("   - AdminRole: PLATFORM_ADMIN, HOSPITAL_ADMIN, SUPPORT_STAFF")
            print("   - AppointmentStatus: PENDING, CONFIRMED, COMPLETED, CANCELLED, NO_SHOW")
            print("   - UrgencyLevel: HIGH, MEDIUM, LOW")
            print("   - NotificationType: BOOKING_CONFIRMATION, REMINDER, etc.")
            print("\n✨ M3 Step 1 COMPLETE!")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    init_database()
