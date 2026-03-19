from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import os
import logging
from utils.auth_middleware import require_auth, get_authenticated_user_id

appointment_bp = Blueprint('appointments', __name__)
logger = logging.getLogger(__name__)

# Store appointments in JSON file (you can replace with database later)
APPOINTMENTS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'appointments.json')

def load_appointments():
    """Load appointments from JSON file"""
    try:
        if os.path.exists(APPOINTMENTS_FILE):
            with open(APPOINTMENTS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading appointments: {e}")
        return []

def save_appointments(appointments):
    """Save appointments to JSON file"""
    try:
        os.makedirs(os.path.dirname(APPOINTMENTS_FILE), exist_ok=True)
        with open(APPOINTMENTS_FILE, 'w') as f:
            json.dump(appointments, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving appointments: {e}")
        return False

@appointment_bp.route('/book', methods=['POST'])
@require_auth()
def book_appointment():
    """Book a new appointment"""
    try:
        user_id = get_authenticated_user_id()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['hospital_id', 'date', 'time', 'specialty']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Load existing appointments
        appointments = load_appointments()
        
        # Create new appointment
        new_appointment = {
            'id': f'apt_{len(appointments) + 1}_{int(datetime.now().timestamp())}',
            'user_id': user_id,
            'hospital_id': data['hospital_id'],
            'hospital_name': data.get('hospital_name', ''),
            'date': data['date'],
            'time': data['time'],
            'specialty': data['specialty'],
            'patient_name': data.get('patient_name', ''),
            'patient_phone': data.get('patient_phone', ''),
            'patient_email': data.get('patient_email', ''),
            'reason': data.get('reason', ''),
            'status': 'confirmed',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Add to appointments list
        appointments.append(new_appointment)
        
        # Save to file
        if save_appointments(appointments):
            logger.info(f"Appointment booked: {new_appointment['id']} for user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Appointment booked successfully',
                'appointment': new_appointment
            }), 201
        else:
            return jsonify({'error': 'Failed to save appointment'}), 500
            
    except Exception as e:
        logger.error(f"Error booking appointment: {e}")
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/my-appointments', methods=['GET'])
@require_auth()
def get_my_appointments():
    """Get all appointments for the current user"""
    try:
        user_id = get_authenticated_user_id()
        
        # Load all appointments
        all_appointments = load_appointments()
        
        # Filter by user_id
        user_appointments = [apt for apt in all_appointments if apt.get('user_id') == user_id]
        
        # Sort by date and time (most recent first)
        user_appointments.sort(key=lambda x: (x['date'], x['time']), reverse=True)
        
        return jsonify({
            'success': True,
            'count': len(user_appointments),
            'appointments': user_appointments
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching appointments: {e}")
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/<appointment_id>', methods=['GET'])
@require_auth()
def get_appointment(appointment_id):
    """Get a specific appointment by ID"""
    try:
        user_id = get_authenticated_user_id()
        
        # Load all appointments
        appointments = load_appointments()
        
        # Find the appointment
        appointment = next((apt for apt in appointments if apt['id'] == appointment_id), None)
        
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Check if user owns this appointment
        if appointment.get('user_id') != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({
            'success': True,
            'appointment': appointment
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching appointment: {e}")
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/<appointment_id>/cancel', methods=['PUT'])
@require_auth()
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    try:
        user_id = get_authenticated_user_id()
        
        # Load all appointments
        appointments = load_appointments()
        
        # Find the appointment
        appointment = next((apt for apt in appointments if apt['id'] == appointment_id), None)
        
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Check if user owns this appointment
        if appointment.get('user_id') != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Update status
        appointment['status'] = 'cancelled'
        appointment['updated_at'] = datetime.now().isoformat()
        
        # Save changes
        if save_appointments(appointments):
            logger.info(f"Appointment cancelled: {appointment_id} by user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Appointment cancelled successfully',
                'appointment': appointment
            }), 200
        else:
            return jsonify({'error': 'Failed to update appointment'}), 500
            
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/available-slots', methods=['POST'])
def get_available_slots():
    """Get available time slots for a hospital on a specific date"""
    try:
        data = request.get_json()
        hospital_id = data.get('hospital_id')
        date = data.get('date')
        
        if not hospital_id or not date:
            return jsonify({'error': 'Missing hospital_id or date'}), 400
        
        # Load all appointments
        appointments = load_appointments()
        
        # Find booked slots for this hospital and date
        booked_slots = [apt['time'] for apt in appointments 
                       if apt.get('hospital_id') == hospital_id 
                       and apt.get('date') == date
                       and apt.get('status') != 'cancelled']
        
        # All possible time slots
        all_slots = [
            '09:00 AM', '09:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM',
            '12:00 PM', '02:00 PM', '02:30 PM', '03:00 PM', '03:30 PM', '04:00 PM',
            '04:30 PM', '05:00 PM', '05:30 PM'
        ]
        
        # Filter out booked slots
        available_slots = [slot for slot in all_slots if slot not in booked_slots]
        
        return jsonify({
            'success': True,
            'date': date,
            'available_slots': available_slots,
            'booked_slots': booked_slots
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching available slots: {e}")
        return jsonify({'error': str(e)}), 500
