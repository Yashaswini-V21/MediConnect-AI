"""
test_integration.py — End-to-end integration tests for MediConnect-AI.

These tests simulate realistic user journeys across multiple endpoints:
  Journey 1: signup → login → symptom check → hospital search → book appointment → cancel
  Journey 2: signup → search → add favorite → remove favorite
  Journey 3: Admin login → list appointments → update appointment status
"""
import pytest
from datetime import datetime, timedelta, timezone


class TestUserJourney1:
    """Full journey: Register → Verify → Login → Symptoms → Hospital → Book → Cancel."""

    def test_full_user_journey(self, client):
        # Step 1: Send OTP
        resp = client.post('/api/auth/send-otp', json={'email': 'journey1@example.com'})
        assert resp.status_code == 200
        otp = resp.get_json().get('otp_dev')
        assert otp, "OTP not returned in dev mode"

        # Step 2: Sign up
        resp = client.post('/api/auth/signup', json={
            'email': 'journey1@example.com',
            'password': 'JourneyPass1',
            'full_name': 'Journey User',
            'otp': otp
        })
        assert resp.status_code == 201, f"Signup failed: {resp.get_json()}"
        token = resp.get_json()['token']

        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        # Step 3: Verify can get profile
        resp = client.get('/api/auth/me', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['user']['email'] == 'journey1@example.com'

        # Step 4: Analyze symptoms
        resp = client.post('/api/analyze-symptoms', json={
            'symptoms': 'persistent headache and mild fever',
            'language': 'en'
        })
        assert resp.status_code == 200
        analysis = resp.get_json()
        assert 'urgency' in analysis

        # Step 5: Search hospitals based on specialties from analysis
        specialties = analysis.get('specialties', ['General Medicine'])
        resp = client.post('/api/hospitals/search', json={
            'specialties': specialties,
            'location': {'lat': 12.9716, 'lng': 77.5946},
            'urgency': analysis.get('urgency', 'LOW')
        })
        assert resp.status_code == 200

        # Step 6: Book appointment
        resp = client.post('/api/appointments/book', headers=headers, json={
            'hospital_id': 1,
            'hospital_name': 'Test General Hospital',
            'date': (datetime.now(timezone.utc) + timedelta(days=3)).strftime('%Y-%m-%d'),
            'time': '10:00 AM',
            'specialty': specialties[0] if specialties else 'General Medicine',
            'reason': 'Follow-up for headache and fever'
        })
        assert resp.status_code == 201, f"Booking failed: {resp.get_json()}"
        apt_id = resp.get_json()['appointment']['id']

        # Step 7: Verify appointment appears in my-appointments
        resp = client.get('/api/appointments/my-appointments', headers=headers)
        assert resp.status_code == 200
        apts = resp.get_json()['appointments']
        apt_ids = [a['id'] for a in apts]
        assert apt_id in apt_ids

        # Step 8: Cancel appointment
        resp = client.put(f'/api/appointments/{apt_id}/cancel', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['appointment']['status'] == 'CANCELLED'

        # Step 9: Verify appointment is cancelled
        resp = client.get(f'/api/appointments/{apt_id}', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['appointment']['status'] == 'CANCELLED'


class TestUserJourney2:
    """Journey: Register → Search hospitals → Add/remove favorites."""

    def test_favorites_journey(self, client):
        # Register
        resp = client.post('/api/auth/send-otp', json={'email': 'journey2@example.com'})
        otp = resp.get_json().get('otp_dev')

        resp = client.post('/api/auth/signup', json={
            'email': 'journey2@example.com',
            'password': 'JourneyPass2',
            'full_name': 'Favorites User',
            'otp': otp
        })
        assert resp.status_code == 201
        token = resp.get_json()['token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        # Add to favorites
        resp = client.post('/api/auth/favorites', headers=headers, json={
            'hospital_id': 'h-001',
            'hospital_name': 'Apollo Hospital'
        })
        assert resp.status_code in (200, 201)
        assert resp.get_json()['success'] is True

        # Get favorites
        resp = client.get('/api/auth/favorites', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        favs = data.get('favorites', [])
        assert any(f.get('hospital_id') == 'h-001' for f in favs)

        # Remove from favorites
        resp = client.delete('/api/auth/favorites/h-001', headers=headers)
        assert resp.status_code in (200, 404)

        # Verify removed
        resp = client.get('/api/auth/favorites', headers=headers)
        data = resp.get_json()
        favs = data.get('favorites', [])
        assert not any(f.get('hospital_id') == 'h-001' for f in favs)


class TestEmergencyJourney:
    """Journey: Emergency symptom check → Emergency hospitals → Route to hospital."""

    def test_emergency_flow(self, client):
        # Check emergency symptoms
        resp = client.post('/api/ai/health/emergency-check', json={
            'symptoms': 'severe chest pain and shortness of breath'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'is_emergency' in data
        assert 'guidance' in data

        # Find emergency hospitals
        resp = client.post('/api/hospitals/emergency', json={
            'location': {'lat': 12.9716, 'lng': 77.5946},
            'max_results': 3
        })
        assert resp.status_code == 200
        hospitals = resp.get_json()['hospitals']
        assert isinstance(hospitals, list)

        # Get route (if hospitals are returned)
        if hospitals:
            first_hospital = hospitals[0]
            hospital_id = first_hospital.get('id') or first_hospital.get('hospital_id')
            if hospital_id:
                resp = client.post('/api/ai/emergency/route', json={
                    'user_lat': 12.9716,
                    'user_lng': 77.5946,
                    'hospital_id': hospital_id,
                    'mode': 'ambulance'
                })
                # May be 200 or 400 depending on Google Maps config
                assert response.status_code in (200, 400)


class TestAdminJourney:
    """Admin journey: Login → View appointments → Update status."""

    def test_admin_management_flow(self, client, admin_user):
        import os
        admin, bearer = admin_user

        headers = {
            'Authorization': f'Bearer {bearer}',
            'Content-Type': 'application/json',
            'X-Admin-Email': admin.email,
            'X-Admin-Token': os.environ.get('ADMIN_SECRET_TOKEN', 'test-admin-token-abc123XYZ')
        }

        # Step 1: Get admin profile
        resp = client.get('/api/admin/me', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['admin']['email'] == admin.email

        # Step 2: Get appointments summary
        resp = client.get('/api/admin/analytics/summary', headers=headers)
        assert resp.status_code == 200
        summary = resp.get_json()['summary']
        assert 'total_appointments' in summary

        # Step 3: Get doctors list
        resp = client.get('/api/admin/doctors', headers=headers)
        assert resp.status_code == 200

        # Step 4: Create a support ticket (public) and then update it as admin
        resp = client.post('/api/admin/support-tickets', json={
            'user_id': 'integration-test-user',
            'subject': 'Integration Test Ticket',
            'description': 'This is a test ticket from integration tests.',
            'priority': 'LOW'
        })
        assert resp.status_code == 201
        ticket_id = resp.get_json()['ticket']['id']

        # Step 5: Update ticket as admin
        resp = client.put(
            f'/api/admin/support-tickets/{ticket_id}',
            headers=headers,
            json={'status': 'IN_PROGRESS', 'priority': 'HIGH'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
