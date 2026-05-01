import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from app import app, db
from models.admin_model import AdminUser, AdminRole, Doctor, Appointment, AppointmentStatus, UrgencyLevel
from datetime import datetime, timedelta

def seed():
    with app.app_context():
        # 1. Clear existing data to avoid duplicates
        AdminUser.query.delete()
        Doctor.query.delete()
        Appointment.query.delete()
        
        # 2. Seed Admin Users
        admins = [
            AdminUser(
                email='platform@mediconnect.ai',
                firebase_uid='platform-admin-uid-001',
                role=AdminRole.PLATFORM_ADMIN,
                hospital_id=None
            ),
            AdminUser(
                email='hospital@mediconnect.ai',
                firebase_uid='hospital-admin-uid-001',
                role=AdminRole.HOSPITAL_ADMIN,
                hospital_id=1
            )
        ]
        
        # 3. Seed Doctors
        doctors = [
            Doctor(
                name='Dr. Smith',
                specialty='Cardiology',
                hospital_id=1,
                degree='MD',
                experience_years=15,
                available_slots={'Mon': ['09:00', '10:00'], 'Tue': ['14:00']}
            ),
            Doctor(
                name='Dr. Jones',
                specialty='Neurology',
                hospital_id=1,
                degree='PhD',
                experience_years=10,
                available_slots={'Wed': ['11:00']}
            )
        ]
        
        # 4. Seed Appointments
        appointments = [
            Appointment(
                user_id='test-user-001',
                hospital_id=1,
                patient_name='John Doe',
                specialty='Cardiology',
                appointment_date=datetime.utcnow() + timedelta(days=1),
                appointment_time='09:00',
                status=AppointmentStatus.PENDING,
                urgency_level=UrgencyLevel.MEDIUM,
                hospital_name='City General'
            ),
            Appointment(
                user_id='test-user-002',
                hospital_id=1,
                patient_name='Jane Doe',
                specialty='Neurology',
                appointment_date=datetime.utcnow() + timedelta(days=2),
                appointment_time='11:00',
                status=AppointmentStatus.CONFIRMED,
                urgency_level=UrgencyLevel.LOW,
                hospital_name='City General'
            )
        ]
        
        db.session.add_all(admins)
        db.session.add_all(doctors)
        db.session.add_all(appointments)
        db.session.commit()
        print("M3 Seeding Complete!")

if __name__ == "__main__":
    seed()
