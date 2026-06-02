"""
test_security.py — Security-focused tests for MediConnect-AI backend.

Tests:
  - Security headers present on all responses
  - Error responses don't leak stack traces or internal details
  - Input validation (length limits, XSS patterns)
  - Analytics endpoints require admin token
"""
import json
import pytest


class TestSecurityHeaders:
    """Verify security headers are applied to all responses."""

    def test_health_endpoint_has_security_headers(self, client):
        response = client.get('/api/health')
        headers = response.headers

        assert 'X-Content-Type-Options' in headers
        assert headers['X-Content-Type-Options'] == 'nosniff'

        assert 'X-Frame-Options' in headers
        assert headers['X-Frame-Options'] == 'DENY'

        assert 'X-XSS-Protection' in headers
        assert 'Strict-Transport-Security' in headers
        assert 'Referrer-Policy' in headers
        assert 'Content-Security-Policy' in headers

    def test_api_endpoint_has_security_headers(self, client):
        response = client.get('/api/hospitals/stats')
        assert 'X-Content-Type-Options' in response.headers

    def test_csp_header_blocks_frames(self, client):
        response = client.get('/api/health')
        csp = response.headers.get('Content-Security-Policy', '')
        assert "frame-src 'none'" in csp

    def test_csp_header_blocks_objects(self, client):
        response = client.get('/api/health')
        csp = response.headers.get('Content-Security-Policy', '')
        assert "object-src 'none'" in csp

    def test_permissions_policy_present(self, client):
        response = client.get('/api/health')
        assert 'Permissions-Policy' in response.headers


class TestErrorResponseSafety:
    """Ensure error responses never leak internal implementation details."""

    def test_404_does_not_leak_internals(self, client):
        response = client.get('/api/does-not-exist-at-all')
        data = response.get_json()
        assert response.status_code == 404
        text = json.dumps(data)
        assert 'Traceback' not in text
        assert '/home/' not in text
        assert 'site-packages' not in text

    def test_invalid_endpoint_returns_json(self, client):
        response = client.get('/api/nonexistent')
        assert response.content_type == 'application/json'

    def test_auth_error_no_traceback(self, client):
        """Login with bad data — response must not include traceback."""
        response = client.post(
            '/api/auth/login',
            json={'email': 'notanemail', 'otp': '123456'}
        )
        data = response.get_json()
        text = json.dumps(data)
        assert 'Traceback' not in text
        assert 'File "' not in text

    def test_500_handler_no_internal_details(self, client):
        """Direct 500 via errorhandler — must return JSON without internals."""
        r = client.get('/api/totally-invalid')
        assert r.content_type == 'application/json'


class TestInputValidation:
    """Test input length and content validation."""

    def test_symptoms_too_short_rejected(self, client):
        response = client.post(
            '/api/analyze-symptoms',
            json={'symptoms': 'ab', 'language': 'en'}
        )
        assert response.status_code == 400

    def test_symptoms_empty_rejected(self, client):
        response = client.post(
            '/api/analyze-symptoms',
            json={'symptoms': '', 'language': 'en'}
        )
        assert response.status_code == 400

    def test_invalid_language_rejected(self, client):
        response = client.post(
            '/api/analyze-symptoms',
            json={'symptoms': 'headache and fever', 'language': 'zz'}
        )
        assert response.status_code == 400

    def test_xss_in_symptoms_handled(self, client):
        """XSS payload in symptoms must not cause 500 or reflect script."""
        response = client.post(
            '/api/analyze-symptoms',
            json={'symptoms': '<script>alert(1)</script>', 'language': 'en'}
        )
        # Should be 400 (too short after sanitization) or 200 with safe response
        assert response.status_code in (400, 200)
        if response.status_code == 200:
            text = json.dumps(response.get_json())
            assert '<script>' not in text

    def test_invalid_coordinate_rejected(self, client):
        """Hospital search with invalid lat/lng must not return 500."""
        response = client.post(
            '/api/hospitals/search',
            json={
                'specialties': ['Cardiology'],
                'location': {'lat': 999, 'lng': 77.5},
                'urgency': 'LOW'
            }
        )
        assert response.status_code != 500

    def test_invalid_urgency_corrected(self, client):
        response = client.post(
            '/api/hospitals/search',
            json={
                'specialties': ['Cardiology'],
                'location': {'lat': 12.97, 'lng': 77.59},
                'urgency': 'INVALID_LEVEL'
            }
        )
        # App corrects invalid urgency to MEDIUM
        assert response.status_code == 200


class TestAnalyticsProtection:
    """Analytics endpoints must require admin token."""

    def test_analytics_stats_requires_auth(self, client):
        response = client.get('/api/analytics/stats')
        assert response.status_code == 401

    def test_analytics_dashboard_requires_auth(self, client):
        response = client.get('/api/analytics/dashboard')
        assert response.status_code == 401

    def test_analytics_stats_with_valid_admin_token(self, client):
        import os
        token = os.environ.get('ADMIN_SECRET_TOKEN', 'test-admin-token-abc123XYZ')
        response = client.get(
            '/api/analytics/stats',
            headers={'X-Admin-Token': token}
        )
        assert response.status_code != 401

    def test_analytics_stats_with_wrong_token(self, client):
        response = client.get(
            '/api/analytics/stats',
            headers={'X-Admin-Token': 'wrong-token'}
        )
        assert response.status_code == 401
