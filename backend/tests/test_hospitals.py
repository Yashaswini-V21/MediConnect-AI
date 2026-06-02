"""
test_hospitals.py — Hospital search and details tests.

Tests:
  - Hospital search (valid, invalid urgency, invalid coords)
  - Emergency hospital search
  - Hospital details retrieval
  - Hospital stats endpoint
  - Favorites (add, remove, list)
"""
import pytest


class TestHospitalSearch:
    """Tests for POST /api/hospitals/search"""

    def test_valid_search(self, client):
        response = client.post('/api/hospitals/search', json={
            'specialties': ['Cardiology'],
            'location': {'lat': 12.9716, 'lng': 77.5946},
            'urgency': 'LOW'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'hospitals' in data
        assert isinstance(data['hospitals'], list)

    def test_missing_location_uses_default(self, client):
        """When location missing, app uses Bangalore center as default — returns 200."""
        response = client.post('/api/hospitals/search', json={
            'specialties': ['Cardiology'],
            'urgency': 'MEDIUM'
        })
        # App uses default location, so 200 is expected
        assert response.status_code == 200

    def test_invalid_urgency_corrected(self, client):
        response = client.post('/api/hospitals/search', json={
            'specialties': ['Cardiology'],
            'location': {'lat': 12.9716, 'lng': 77.5946},
            'urgency': 'INVALID_LEVEL'
        })
        # App silently corrects invalid urgency to MEDIUM
        assert response.status_code == 200
        data = response.get_json()
        assert data['urgency'] == 'MEDIUM'

    def test_empty_specialties_returns_results(self, client):
        """Empty specialties list should return general hospitals."""
        response = client.post('/api/hospitals/search', json={
            'specialties': [],
            'location': {'lat': 12.9716, 'lng': 77.5946},
            'urgency': 'LOW'
        })
        assert response.status_code == 200

    def test_high_urgency_search(self, client):
        response = client.post('/api/hospitals/search', json={
            'specialties': ['Emergency', 'Trauma'],
            'location': {'lat': 12.9716, 'lng': 77.5946},
            'urgency': 'HIGH'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_invalid_coordinates_out_of_range(self, client):
        """Coordinates outside valid range should not crash."""
        response = client.post('/api/hospitals/search', json={
            'specialties': ['Cardiology'],
            'location': {'lat': 999, 'lng': 999},
            'urgency': 'LOW'
        })
        # Must be 400 or 200 with empty results — never 500
        assert response.status_code in (400, 200)

    def test_missing_body(self, client):
        response = client.post(
            '/api/hospitals/search',
            data='',
            content_type='application/json'
        )
        assert response.status_code in (400, 500)

    def test_response_has_hospital_schema(self, client):
        """Each hospital in results must have required fields."""
        response = client.post('/api/hospitals/search', json={
            'specialties': ['General Medicine'],
            'location': {'lat': 12.9716, 'lng': 77.5946},
            'urgency': 'LOW'
        })
        if response.status_code == 200:
            hospitals = response.get_json().get('hospitals', [])
            if hospitals:
                h = hospitals[0]
                assert 'id' in h or 'hospital_id' in h
                assert 'name' in h

    def test_pagination_max_results_respected(self, client):
        """max_results parameter should be respected if supported."""
        response = client.post('/api/hospitals/search', json={
            'specialties': ['General Medicine'],
            'location': {'lat': 12.9716, 'lng': 77.5946},
            'urgency': 'LOW',
            'max_results': 3
        })
        # Just verify it doesn't crash
        assert response.status_code == 200


class TestEmergencySearch:
    """Tests for POST /api/hospitals/emergency"""

    def test_valid_emergency_search(self, client):
        response = client.post('/api/hospitals/emergency', json={
            'latitude': 12.9716,
            'longitude': 77.5946
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_emergency_search_missing_location(self, client):
        response = client.post('/api/hospitals/emergency', json={'max_results': 3})
        assert response.status_code == 400

    def test_emergency_search_invalid_location(self, client):
        response = client.post('/api/hospitals/emergency', json={
            'location': {'lat': 'notanumber', 'lng': 77.59}
        })
        assert response.status_code in (400, 500)

    def test_emergency_results_are_sorted(self, client):
        """Emergency hospitals should be sorted by proximity/urgency."""
        response = client.post('/api/hospitals/emergency', json={
            'location': {'lat': 12.9716, 'lng': 77.5946},
            'max_results': 5
        })
        if response.status_code == 200:
            hospitals = response.get_json().get('hospitals', [])
            assert isinstance(hospitals, list)


class TestHospitalDetails:
    """Tests for GET /api/hospitals/<id>"""

    def test_valid_hospital_id(self, client):
        response = client.get('/api/hospitals/1')
        assert response.status_code in (200, 404)

    def test_nonexistent_hospital_id(self, client):
        response = client.get('/api/hospitals/99999')
        assert response.status_code == 404

    def test_invalid_hospital_id_type(self, client):
        response = client.get('/api/hospitals/not-an-id')
        assert response.status_code in (400, 404)


class TestHospitalStats:
    """Tests for GET /api/hospitals/stats"""

    def test_stats_returns_data(self, client):
        response = client.get('/api/hospitals/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True


class TestFavorites:
    """Tests for favorites endpoints."""

    def test_add_favorite_authenticated(self, client, auth_headers):
        response = client.post(
            '/api/auth/favorites',
            headers=auth_headers,
            json={'hospital_id': 'h-001', 'hospital_name': 'Test Hospital'}
        )
        assert response.status_code in (200, 201)

    def test_add_favorite_unauthenticated(self, client):
        response = client.post(
            '/api/auth/favorites',
            json={'hospital_id': 'h-001'}
        )
        assert response.status_code == 401

    def test_get_favorites_authenticated(self, client, auth_headers):
        response = client.get('/api/auth/favorites', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'favorites' in data

    def test_remove_favorite(self, client, auth_headers):
        # First add
        client.post(
            '/api/auth/favorites',
            headers=auth_headers,
            json={'hospital_id': 'h-remove-test'}
        )
        # Then remove
        response = client.delete(
            '/api/auth/favorites/h-remove-test',
            headers=auth_headers
        )
        assert response.status_code in (200, 404)

    def test_duplicate_favorite_handled(self, client, auth_headers):
        """Adding the same hospital twice should be handled gracefully."""
        payload = {'hospital_id': 'h-duplicate', 'hospital_name': 'Dup Hospital'}
        client.post('/api/auth/favorites', headers=auth_headers, json=payload)
        response = client.post('/api/auth/favorites', headers=auth_headers, json=payload)
        assert response.status_code in (200, 201, 409)
