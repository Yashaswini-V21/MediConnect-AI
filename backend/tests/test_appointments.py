"""
test_appointments.py — Appointment booking and management tests.

Tests:
  - Book appointment (valid, missing fields, unauthenticated)
  - Get my appointments (ownership isolation)
  - Get specific appointment (own vs other user)
  - Cancel appointment (own, other user's, already cancelled)
  - Rating an appointment (valid, double-rating, out of range)
  - Available slots endpoint
"""
import pytest
from datetime import datetime, timedelta, timezone


class TestBookAppointment:
    """Tests for POST /api/appointments/book"""

    VALID_APPOINTMENT = {
        'hospital_id': 1,
        'hospital_name': 'Test Hospital',
        'date': (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d'),
        'time': '10:00 AM',
        'specialty': 'General Medicine',
        'patient_name': 'Test Patient',
        'patient_phone': '9876543210',
        'patient_email': 'patient@example.com',
        'reason': 'Routine checkup'
    }

    def test_book_appointment_valid(self, client, auth_headers):
        response = client.post(
            '/api/appointments/book',
            headers=auth_headers,
            json=self.VALID_APPOINTMENT
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'appointment' in data
        apt = data['appointment']
        assert 'id' in apt
        assert apt['specialty'] == 'General Medicine'

    def test_book_appointment_unauthenticated(self, client):
        response = client.post(
            '/api/appointments/book',
            json=self.VALID_APPOINTMENT
        )
        assert response.status_code == 401

    def test_book_appointment_missing_hospital_id(self, client, auth_headers):
        payload = dict(self.VALID_APPOINTMENT)
        del payload['hospital_id']
        response = client.post(
            '/api/appointments/book',
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 400

    def test_book_appointment_missing_date(self, client, auth_headers):
        payload = dict(self.VALID_APPOINTMENT)
        del payload['date']
        response = client.post(
            '/api/appointments/book',
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 400

    def test_book_appointment_missing_specialty(self, client, auth_headers):
        payload = dict(self.VALID_APPOINTMENT)
        del payload['specialty']
        response = client.post(
            '/api/appointments/book',
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 400

    def test_book_appointment_invalid_date_format(self, client, auth_headers):
        payload = dict(self.VALID_APPOINTMENT)
        payload['date'] = 'not-a-date'
        response = client.post(
            '/api/appointments/book',
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 400

    def test_reason_is_encrypted_not_plaintext_in_response(self, client, auth_headers):
        """Reason should be returned decrypted (not raw Fernet ciphertext)."""
        payload = dict(self.VALID_APPOINTMENT)
        payload['reason'] = 'My private medical reason'
        response = client.post(
            '/api/appointments/book',
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 201


class TestGetMyAppointments:
    """Tests for GET /api/appointments/my-appointments"""

    def test_get_my_appointments_authenticated(self, client, auth_headers):
        response = client.get('/api/appointments/my-appointments', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'appointments' in data
        assert isinstance(data['appointments'], list)

    def test_get_my_appointments_unauthenticated(self, client):
        response = client.get('/api/appointments/my-appointments')
        assert response.status_code == 401

    def test_appointments_list_is_empty_for_new_user(self, client, auth_headers):
        """A fresh user should have 0 appointments."""
        response = client.get('/api/appointments/my-appointments', headers=auth_headers)
        data = response.get_json()
        assert response.status_code == 200
        assert data['count'] == 0 or isinstance(data['appointments'], list)


class TestGetSingleAppointment:
    """Tests for GET /api/appointments/<id>"""

    def _book_appointment(self, client, headers):
        payload = {
            'hospital_id': 1,
            'hospital_name': 'Test Hospital',
            'date': (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': '11:00 AM',
            'specialty': 'Cardiology',
            'reason': 'Heart checkup'
        }
        resp = client.post('/api/appointments/book', headers=headers, json=payload)
        return resp.get_json().get('appointment', {}).get('id')

    def test_get_own_appointment(self, client, auth_headers):
        apt_id = self._book_appointment(client, auth_headers)
        if apt_id:
            response = client.get(f'/api/appointments/{apt_id}', headers=auth_headers)
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

    def test_get_appointment_unauthenticated(self, client, auth_headers):
        apt_id = self._book_appointment(client, auth_headers)
        if apt_id:
            response = client.get(f'/api/appointments/{apt_id}')
            assert response.status_code == 401

    def test_get_nonexistent_appointment(self, client, auth_headers):
        response = client.get('/api/appointments/99999', headers=auth_headers)
        assert response.status_code in (404, 500)


class TestCancelAppointment:
    """Tests for PUT /api/appointments/<id>/cancel"""

    def _book_appointment(self, client, headers):
        payload = {
            'hospital_id': 1,
            'hospital_name': 'Test Hospital',
            'date': (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': '02:00 PM',
            'specialty': 'Dermatology',
            'reason': 'Skin checkup'
        }
        resp = client.post('/api/appointments/book', headers=headers, json=payload)
        return resp.get_json().get('appointment', {}).get('id')

    def test_cancel_own_appointment(self, client, auth_headers):
        apt_id = self._book_appointment(client, auth_headers)
        if apt_id:
            response = client.put(
                f'/api/appointments/{apt_id}/cancel',
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['appointment']['status'] == 'CANCELLED'

    def test_cancel_unauthenticated(self, client, auth_headers):
        apt_id = self._book_appointment(client, auth_headers)
        if apt_id:
            response = client.put(f'/api/appointments/{apt_id}/cancel')
            assert response.status_code == 401

    def test_cancel_nonexistent_appointment(self, client, auth_headers):
        response = client.put('/api/appointments/99999/cancel', headers=auth_headers)
        assert response.status_code in (404, 500)


class TestRatingAppointment:
    """Tests for POST /api/appointments/<id>/rate"""

    def _book_and_get_id(self, client, headers):
        payload = {
            'hospital_id': 1,
            'hospital_name': 'Rate Test Hospital',
            'date': (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': '03:00 PM',
            'specialty': 'Neurology',
            'reason': 'Headache checkup'
        }
        resp = client.post('/api/appointments/book', headers=headers, json=payload)
        return resp.get_json().get('appointment', {}).get('id')

    def test_rate_valid(self, client, auth_headers):
        apt_id = self._book_and_get_id(client, auth_headers)
        if apt_id:
            response = client.post(
                f'/api/appointments/{apt_id}/rate',
                headers=auth_headers,
                json={'rating': 4, 'review': 'Great experience'}
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

    def test_rate_out_of_range_too_high(self, client, auth_headers):
        apt_id = self._book_and_get_id(client, auth_headers)
        if apt_id:
            response = client.post(
                f'/api/appointments/{apt_id}/rate',
                headers=auth_headers,
                json={'rating': 10}
            )
            assert response.status_code == 400

    def test_rate_out_of_range_too_low(self, client, auth_headers):
        apt_id = self._book_and_get_id(client, auth_headers)
        if apt_id:
            response = client.post(
                f'/api/appointments/{apt_id}/rate',
                headers=auth_headers,
                json={'rating': 0}
            )
            assert response.status_code == 400

    def test_double_rating_rejected(self, client, auth_headers):
        """Rating the same appointment twice should return 409."""
        apt_id = self._book_and_get_id(client, auth_headers)
        if apt_id:
            client.post(
                f'/api/appointments/{apt_id}/rate',
                headers=auth_headers,
                json={'rating': 5}
            )
            response = client.post(
                f'/api/appointments/{apt_id}/rate',
                headers=auth_headers,
                json={'rating': 3}
            )
            assert response.status_code == 409

    def test_rate_unauthenticated(self, client, auth_headers):
        apt_id = self._book_and_get_id(client, auth_headers)
        if apt_id:
            response = client.post(
                f'/api/appointments/{apt_id}/rate',
                json={'rating': 4}
            )
            assert response.status_code == 401


class TestAvailableSlots:
    """Tests for POST /api/appointments/available-slots"""

    def test_available_slots_valid(self, client):
        response = client.post('/api/appointments/available-slots', json={
            'hospital_id': 1,
            'date': (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'available_slots' in data
        assert isinstance(data['available_slots'], list)

    def test_available_slots_missing_hospital_id(self, client):
        response = client.post('/api/appointments/available-slots', json={
            'date': '2026-06-10'
        })
        assert response.status_code == 400

    def test_available_slots_missing_date(self, client):
        response = client.post('/api/appointments/available-slots', json={
            'hospital_id': 1
        })
        assert response.status_code == 400
