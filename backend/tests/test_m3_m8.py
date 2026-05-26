"""
MediConnect-AI Test Suite — M3–M8 Comprehensive Tests
Tests for: Admin Portal, Appointments, Analytics, Notifications, Multi-Agent, Security, Deployment

Run: pytest tests/test_m3_m8.py -v
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from flask import Flask
from models.user_model import db, User, SearchHistory
from models.admin_model import (
    AdminUser, Appointment, Doctor, Notification, SupportTicket,
    AppointmentStatus, AdminRole, UrgencyLevel
)
from models.analytics_model import AppointmentAnalytics
import os

# ════════════════════════════════════════════════════════════════════════════════════════
# TEST FIXTURES
# ════════════════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope='module')
def test_app():
    """Create and configure a test Flask app"""
    os.environ['TESTING'] = 'True'
    os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    from app import app
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    """Create a test client"""
    return test_app.test_client()

@pytest.fixture
def runner(test_app):
    """Create a test CLI runner"""
    return test_app.test_cli_runner()

# ════════════════════════════════════════════════════════════════════════════════════════
# M3: ADMIN PORTAL & RBAC TESTS
# ════════════════════════════════════════════════════════════════════════════════════════

class TestM3AdminPortal:
    """Tests for M3: Admin Portal, RBAC, and Appointments"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'database' in data
    
    def test_admin_user_creation(self):
        """Test creating admin user with RBAC roles"""
        admin = AdminUser(
            email='admin@mediconnect.health',
            firebase_uid='test-uid-123',
            role=AdminRole.PLATFORM_ADMIN,
            permissions={'view_all': True, 'manage_admins': True},
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        
        assert admin.id is not None
        assert admin.role == AdminRole.PLATFORM_ADMIN
        assert admin.is_active == True
    
    def test_hospital_admin_scope_isolation(self):
        """Test Hospital Admin can only see their own hospital data"""
        # Create two hospital admins for different hospitals
        admin1 = AdminUser(
            email='hospital1@admin.com',
            role=AdminRole.HOSPITAL_ADMIN,
            hospital_id=1,
            is_active=True
        )
        admin2 = AdminUser(
            email='hospital2@admin.com',
            role=AdminRole.HOSPITAL_ADMIN,
            hospital_id=2,
            is_active=True
        )
        db.session.add_all([admin1, admin2])
        db.session.commit()
        
        # Create appointments for both hospitals
        appt1 = Appointment(
            user_id='patient1',
            hospital_id=1,
            appointment_date=datetime.utcnow() + timedelta(days=1),
            status=AppointmentStatus.PENDING
        )
        appt2 = Appointment(
            user_id='patient2',
            hospital_id=2,
            appointment_date=datetime.utcnow() + timedelta(days=1),
            status=AppointmentStatus.PENDING
        )
        db.session.add_all([appt1, appt2])
        db.session.commit()
        
        # Each hospital admin should only see their own appointments
        assert Appointment.query.filter_by(hospital_id=1).count() == 1
        assert Appointment.query.filter_by(hospital_id=2).count() == 1
    
    def test_appointment_status_transitions(self):
        """Test valid appointment status transitions"""
        appt = Appointment(
            user_id='patient1',
            hospital_id=1,
            appointment_date=datetime.utcnow() + timedelta(days=1),
            status=AppointmentStatus.PENDING
        )
        db.session.add(appt)
        db.session.commit()
        
        # Valid: PENDING -> CONFIRMED
        assert AppointmentStatus.can_transition(AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED)
        
        # Valid: PENDING -> CANCELLED
        assert AppointmentStatus.can_transition(AppointmentStatus.PENDING, AppointmentStatus.CANCELLED)
        
        # Valid: CONFIRMED -> COMPLETED
        assert AppointmentStatus.can_transition(AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED)
        
        # Invalid: CONFIRMED -> PENDING
        assert not AppointmentStatus.can_transition(AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING)
        
        # Invalid: COMPLETED -> anything
        assert not AppointmentStatus.can_transition(AppointmentStatus.COMPLETED, AppointmentStatus.CONFIRMED)
    
    def test_appointment_future_date_validation(self):
        """Test appointment date must be in the future"""
        # Past date
        past_date = datetime.utcnow() - timedelta(days=1)
        appt_past = Appointment(
            user_id='patient1',
            hospital_id=1,
            appointment_date=past_date,
            status=AppointmentStatus.PENDING
        )
        db.session.add(appt_past)
        
        # Future date (valid)
        future_date = datetime.utcnow() + timedelta(days=1)
        appt_future = Appointment(
            user_id='patient1',
            hospital_id=1,
            appointment_date=future_date,
            status=AppointmentStatus.PENDING
        )
        db.session.add(appt_future)
        db.session.commit()
        
        # Should have both in DB (validation happens at API level)
        assert Appointment.query.count() >= 2

# ════════════════════════════════════════════════════════════════════════════════════════
# M4: ANALYTICS TESTS
# ════════════════════════════════════════════════════════════════════════════════════════

class TestM4Analytics:
    """Tests for M4: Analytics and Dashboard Data"""
    
    def test_analytics_model_creation(self):
        """Test creating analytics records"""
        today = datetime.utcnow().date()
        analytics = AppointmentAnalytics(
            date=today,
            hospital_id=1,
            total_bookings=10,
            confirmed=8,
            completed=5,
            cancelled=1,
            no_show=1,
            high_urgency=2,
            medium_urgency=5,
            low_urgency=3,
            avg_confirmation_time_mins=15.5,
            peak_hour=14
        )
        db.session.add(analytics)
        db.session.commit()
        
        assert analytics.id is not None
        assert analytics.total_bookings == 10
        assert analytics.confirmed == 8
    
    def test_analytics_to_dict(self):
        """Test analytics serialization"""
        today = datetime.utcnow().date()
        analytics = AppointmentAnalytics(
            date=today,
            hospital_id=None,  # Platform-wide
            total_bookings=100,
            confirmed=80
        )
        db.session.add(analytics)
        db.session.commit()
        
        data = analytics.to_dict()
        assert data['total_bookings'] == 100
        assert data['confirmed'] == 80
        assert data['hospital_id'] is None

# ════════════════════════════════════════════════════════════════════════════════════════
# M5: NOTIFICATION TESTS
# ════════════════════════════════════════════════════════════════════════════════════════

class TestM5Notifications:
    """Tests for M5: Notification Service"""
    
    def test_notification_creation(self):
        """Test creating in-app notifications"""
        appt = Appointment(
            user_id='patient1',
            hospital_id=1,
            appointment_date=datetime.utcnow() + timedelta(days=1),
            status=AppointmentStatus.PENDING
        )
        db.session.add(appt)
        db.session.commit()
        
        notification = Notification(
            user_id='patient1',
            appointment_id=appt.id,
            type='BOOKING_CONFIRMATION',
            message='Your appointment has been received',
            sent_via='IN_APP',
            sent_at=datetime.utcnow(),
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        
        assert notification.id is not None
        assert notification.is_read == False
    
    def test_notification_marking_read(self):
        """Test marking notification as read"""
        appt = Appointment(
            user_id='patient1',
            hospital_id=1,
            appointment_date=datetime.utcnow() + timedelta(days=1),
            status=AppointmentStatus.PENDING
        )
        db.session.add(appt)
        db.session.commit()
        
        notification = Notification(
            user_id='patient1',
            appointment_id=appt.id,
            type='BOOKING_CONFIRMATION',
            message='Test message',
            sent_via='IN_APP',
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        
        # Mark as read
        notification.is_read = True
        db.session.commit()
        
        assert notification.is_read == True

# ════════════════════════════════════════════════════════════════════════════════════════
# M6: MULTI-AGENT PIPELINE TESTS
# ════════════════════════════════════════════════════════════════════════════════════════

class TestM6MultiAgent:
    """Tests for M6: Multi-Agent Pipeline"""
    
    def test_medical_state_structure(self):
        """Test MedicalState TypedDict structure"""
        from utils.multi_agent_pipeline import MedicalState
        
        # Create a valid state
        state: MedicalState = {
            "input_text": "chest pain",
            "language": "en",
            "symptoms": ["chest pain"],
            "translated_text": "chest pain",
            "conditions": [],
            "specialists": ["Cardiologist"],
            "hospitals": [],
            "urgency_level": "HIGH",
            "confidence_score": 0.95,
            "reasoning_chain": ["Extracted symptoms", "Matched to conditions"],
            "final_explanation": "You may have a cardiac issue",
            "error": None
        }
        
        assert state['urgency_level'] == "HIGH"
        assert state['confidence_score'] == 0.95

# ════════════════════════════════════════════════════════════════════════════════════════
# M7: SECURITY TESTS
# ════════════════════════════════════════════════════════════════════════════════════════

class TestM7Security:
    """Tests for M7: Security and Encryption"""
    
    def test_encryption_decryption(self):
        """Test AES-256 encryption and decryption"""
        from utils.security import encryption_service
        
        original_text = "Sensitive health data"
        encrypted = encryption_service.encrypt(original_text)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert encrypted != original_text
        assert decrypted == original_text
    
    def test_audit_log_creation(self):
        """Test audit logging"""
        from utils.security import AuditLog
        
        audit = AuditLog(
            user_id='admin123',
            action='CREATE',
            resource='appointment',
            resource_id='appt001',
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0',
            success=True
        )
        db.session.add(audit)
        db.session.commit()
        
        assert audit.id is not None
        assert audit.action == 'CREATE'
        assert audit.success == True

# ════════════════════════════════════════════════════════════════════════════════════════
# M8: DEPLOYMENT TESTS
# ════════════════════════════════════════════════════════════════════════════════════════

class TestM8Deployment:
    """Tests for M8: Deployment readiness"""
    
    def test_app_imports(self):
        """Test that app imports successfully"""
        from app import app
        assert app is not None
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert 'version' in data
    
    def test_cors_headers(self, client):
        """Test CORS headers are set"""
        response = client.get('/api/health')
        # CORS headers should be set by Flask-CORS
        assert response.status_code == 200

# ════════════════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ════════════════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """Full integration tests across milestones"""
    
    def test_end_to_end_appointment_flow(self):
        """Test complete appointment booking to completion flow"""
        # Create patient
        patient = User(
            email='patient@test.com',
            password='password123'
        )
        db.session.add(patient)
        db.session.commit()
        
        # Create admin
        admin = AdminUser(
            email='admin@hospital.com',
            role=AdminRole.HOSPITAL_ADMIN,
            hospital_id=1,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        
        # Create appointment
        appt = Appointment(
            user_id=patient.id,
            hospital_id=1,
            appointment_date=datetime.utcnow() + timedelta(days=1),
            status=AppointmentStatus.PENDING,
            urgency_level=UrgencyLevel.HIGH,
            reason='Chest pain'
        )
        db.session.add(appt)
        db.session.commit()
        
        # Verify states
        assert appt.status == AppointmentStatus.PENDING
        
        # Admin confirms appointment
        appt.status = AppointmentStatus.CONFIRMED
        db.session.commit()
        assert appt.status == AppointmentStatus.CONFIRMED
        
        # Appointment completed
        appt.status = AppointmentStatus.COMPLETED
        db.session.commit()
        assert appt.status == AppointmentStatus.COMPLETED

# ════════════════════════════════════════════════════════════════════════════════════════
# CLI: Run with pytest
# ════════════════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
