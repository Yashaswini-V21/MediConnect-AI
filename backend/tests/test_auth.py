"""
test_auth.py — Authentication endpoint tests for MediConnect-AI.

Tests:
  - OTP send (valid, invalid email)
  - OTP verify (valid, wrong, no OTP sent)
  - Signup (valid, duplicate email, invalid password, missing OTP)
  - Login (valid, wrong OTP, nonexistent user)
  - Profile get/update (authenticated and unauthenticated)
"""
import json
import pytest


class TestOTPSend:
    """Tests for /api/auth/send-otp"""

    def test_send_otp_valid_email(self, client):
        response = client.post(
            '/api/auth/send-otp',
            json={'email': 'user@example.com'}
        )
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] is True
        assert 'otp_dev' in data  # dev mode exposes OTP

    def test_send_otp_missing_email(self, client):
        response = client.post('/api/auth/send-otp', json={})
        assert response.status_code == 400
        assert response.get_json()['success'] is False

    def test_send_otp_invalid_email_format(self, client):
        response = client.post(
            '/api/auth/send-otp',
            json={'email': 'not-an-email'}
        )
        assert response.status_code == 400

    def test_send_otp_returns_otp_in_dev_mode(self, client):
        """In development mode, otp_dev field must be present."""
        response = client.post(
            '/api/auth/send-otp',
            json={'email': 'devtest@example.com'}
        )
        data = response.get_json()
        assert response.status_code == 200
        assert 'otp_dev' in data
        assert len(str(data['otp_dev'])) == 6


class TestOTPVerify:
    """Tests for /api/auth/verify-otp"""

    def test_verify_valid_otp(self, client):
        # First send
        send_resp = client.post(
            '/api/auth/send-otp',
            json={'email': 'verify@example.com'}
        )
        otp = send_resp.get_json()['otp_dev']

        # Then verify
        response = client.post(
            '/api/auth/verify-otp',
            json={'email': 'verify@example.com', 'otp': otp}
        )
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] is True

    def test_verify_wrong_otp(self, client):
        client.post('/api/auth/send-otp', json={'email': 'wrong@example.com'})
        response = client.post(
            '/api/auth/verify-otp',
            json={'email': 'wrong@example.com', 'otp': '000000'}
        )
        assert response.status_code == 400
        assert response.get_json()['success'] is False

    def test_verify_missing_fields(self, client):
        response = client.post('/api/auth/verify-otp', json={'email': 'test@example.com'})
        assert response.status_code == 400

    def test_verify_no_otp_sent(self, client):
        response = client.post(
            '/api/auth/verify-otp',
            json={'email': 'nosentmail@example.com', 'otp': '123456'}
        )
        assert response.status_code == 400


class TestSignup:
    """Tests for /api/auth/signup"""

    def _get_otp(self, client, email):
        resp = client.post('/api/auth/send-otp', json={'email': email})
        return resp.get_json().get('otp_dev')

    def test_signup_valid(self, client):
        email = 'newuser@example.com'
        otp = self._get_otp(client, email)

        response = client.post('/api/auth/signup', json={
            'email': email,
            'password': 'SecurePass1',
            'full_name': 'New User',
            'otp': otp
        })
        data = response.get_json()
        assert response.status_code == 201
        assert data['success'] is True
        assert 'token' in data
        assert 'user' in data

    def test_signup_duplicate_email(self, client, sample_user):
        user, _ = sample_user
        otp = self._get_otp(client, user.email)

        response = client.post('/api/auth/signup', json={
            'email': user.email,
            'password': 'SecurePass1',
            'full_name': 'Duplicate User',
            'otp': otp
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'already' in data.get('message', '').lower() or \
               'registered' in data.get('message', '').lower()

    def test_signup_weak_password(self, client):
        email = 'weakpass@example.com'
        otp = self._get_otp(client, email)

        response = client.post('/api/auth/signup', json={
            'email': email,
            'password': 'weak',
            'full_name': 'Weak Pass User',
            'otp': otp
        })
        assert response.status_code == 400

    def test_signup_missing_otp(self, client):
        response = client.post('/api/auth/signup', json={
            'email': 'nootp@example.com',
            'password': 'SecurePass1',
            'full_name': 'No OTP User',
            'otp': ''
        })
        assert response.status_code == 400

    def test_signup_invalid_otp(self, client):
        email = 'invalidotp@example.com'
        self._get_otp(client, email)

        response = client.post('/api/auth/signup', json={
            'email': email,
            'password': 'SecurePass1',
            'full_name': 'Wrong OTP User',
            'otp': '000000'
        })
        assert response.status_code == 400

    def test_signup_missing_required_fields(self, client):
        response = client.post('/api/auth/signup', json={
            'email': 'incomplete@example.com'
        })
        assert response.status_code == 400

    def test_signup_full_name_too_long(self, client):
        email = 'longname@example.com'
        otp = self._get_otp(client, email)

        response = client.post('/api/auth/signup', json={
            'email': email,
            'password': 'SecurePass1',
            'full_name': 'A' * 200,
            'otp': otp
        })
        assert response.status_code == 400


class TestLogin:
    """Tests for /api/auth/login"""

    def _register_user(self, client, email='logintest@example.com'):
        resp = client.post('/api/auth/send-otp', json={'email': email})
        otp = resp.get_json().get('otp_dev')
        client.post('/api/auth/signup', json={
            'email': email,
            'password': 'LoginPass1',
            'full_name': 'Login Test',
            'otp': otp
        })
        return email

    def test_login_valid(self, client):
        email = self._register_user(client, 'validlogin@example.com')
        # Get fresh OTP for login
        resp = client.post('/api/auth/send-otp', json={'email': email})
        otp = resp.get_json().get('otp_dev')

        response = client.post('/api/auth/login', json={'email': email, 'otp': otp})
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] is True
        assert 'token' in data

    def test_login_wrong_otp(self, client):
        email = self._register_user(client, 'wrongotp@example.com')
        client.post('/api/auth/send-otp', json={'email': email})

        response = client.post('/api/auth/login', json={'email': email, 'otp': '000000'})
        assert response.status_code == 400

    def test_login_nonexistent_user(self, client):
        resp = client.post('/api/auth/send-otp', json={'email': 'ghost@example.com'})
        otp = resp.get_json().get('otp_dev')

        response = client.post(
            '/api/auth/login',
            json={'email': 'ghost@example.com', 'otp': otp}
        )
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        response = client.post('/api/auth/login', json={'email': 'test@example.com'})
        assert response.status_code == 400

    def test_login_invalid_email_format(self, client):
        response = client.post(
            '/api/auth/login',
            json={'email': 'notanemail', 'otp': '123456'}
        )
        assert response.status_code == 400


class TestProfileEndpoints:
    """Tests for /api/auth/me, /api/auth/profile"""

    def test_get_me_authenticated(self, client, auth_headers):
        response = client.get('/api/auth/me', headers=auth_headers)
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] is True
        assert 'user' in data
        assert 'password_hash' not in data['user']

    def test_get_me_unauthenticated(self, client):
        response = client.get('/api/auth/me')
        assert response.status_code == 401

    def test_update_profile_authenticated(self, client, auth_headers):
        response = client.put(
            '/api/auth/profile',
            headers=auth_headers,
            json={'full_name': 'Updated Name', 'preferred_language': 'hi'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['full_name'] == 'Updated Name'

    def test_update_profile_unauthenticated(self, client):
        response = client.put(
            '/api/auth/profile',
            json={'full_name': 'Hacker'}
        )
        assert response.status_code == 401

    def test_update_profile_full_name_too_long(self, client, auth_headers):
        response = client.put(
            '/api/auth/profile',
            headers=auth_headers,
            json={'full_name': 'A' * 200}
        )
        assert response.status_code == 400

    def test_password_not_in_profile_response(self, client, auth_headers):
        response = client.get('/api/auth/profile', headers=auth_headers)
        data = response.get_json()
        assert response.status_code == 200
        user = data.get('user', {})
        assert 'password_hash' not in user
        assert 'password' not in user
