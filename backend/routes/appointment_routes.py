from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
import os
import logging
from utils.auth_middleware import require_auth, get_authenticated_user_id
from utils.security import encryption_service, audit_log, limiter
from models.user_model import db
from models.admin_model import Appointment, AppointmentStatus
from utils.realtime import publish_event
from extensions import socketio

appointment_bp = Blueprint('appointments', __name__)
logger = logging.getLogger(__name__)

"""
DB-backed appointment routes. Replaced JSON file storage with SQLAlchemy `Appointment` model.
"""

@appointment_bp.route('/book', methods=['POST'])
@limiter.limit("10 per hour")
@require_auth()
@audit_log("CREATE", "appointment")
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
        
        # Encrypt patient health data before saving
        raw_reason = data.get('reason', '')
        encrypted_reason = encryption_service.encrypt(raw_reason)

        # Parse date & time into a datetime
        date_str = data['date']
        time_str = data['time']
        try:
            date_part = datetime.fromisoformat(date_str)
        except Exception:
            return jsonify({'error': 'Invalid date format; expected YYYY-MM-DD'}), 400

        try:
            time_part = datetime.strptime(time_str, '%I:%M %p').time()
        except Exception:
            # Fallback: store time string and set appointment_date to date at midnight
            time_part = None

        appointment_dt = datetime(
            date_part.year, date_part.month, date_part.day,
            time_part.hour if time_part else 0,
            time_part.minute if time_part else 0
        )

        # Create Appointment model instance
        apt = Appointment(
            user_id=user_id,
            hospital_id=int(data['hospital_id']),
            hospital_name=data.get('hospital_name', ''),
            appointment_date=appointment_dt,
            appointment_time=time_str,
            specialty=data['specialty'],
            patient_name=data.get('patient_name', ''),
            patient_phone=data.get('patient_phone', ''),
            patient_email=data.get('patient_email', ''),
            reason=encrypted_reason,
            status=AppointmentStatus.PENDING,
        )

        db.session.add(apt)
        db.session.commit()

        logger.info(f"Appointment booked: {apt.id} for user {user_id}")

        # Emit Socket.IO event for admin dashboard
        try:
            socketio.emit('appointment_created', apt.to_dict(), namespace='/admin')
        except Exception:
            logger.exception('Failed to emit socket event')

        return jsonify({
            'success': True,
            'message': 'Appointment booked successfully',
            'appointment': apt.to_dict()
        }), 201
            
    except Exception as e:
        logger.error(f"Error booking appointment: {e}")
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/my-appointments', methods=['GET'])
@require_auth()
def get_my_appointments():
    """Get all appointments for the current user"""
    try:
        user_id = get_authenticated_user_id()
        # Query DB for user's appointments
        apts = Appointment.query.filter_by(user_id=user_id).order_by(Appointment.created_at.desc()).all()
        result = []
        for apt in apts:
            d = apt.to_dict()
            if 'reason' in d and d['reason']:
                try:
                    d['reason'] = encryption_service.decrypt(d['reason'])
                except Exception:
                    d['reason'] = None
            result.append(d)

        return jsonify({
            'success': True,
            'count': len(result),
            'appointments': result
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
        apt = Appointment.query.get(appointment_id)
        if not apt:
            return jsonify({'error': 'Appointment not found'}), 404

        if apt.user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        d = apt.to_dict()
        try:
            d['reason'] = encryption_service.decrypt(d.get('reason', ''))
        except Exception:
            d['reason'] = None

        return jsonify({
            'success': True,
            'appointment': d
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
        apt = Appointment.query.get(appointment_id)
        if not apt:
            return jsonify({'error': 'Appointment not found'}), 404

        if apt.user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        apt.status = AppointmentStatus.CANCELLED
        apt.updated_at = datetime.now()
        db.session.commit()

        # Publish realtime update
        try:
            publish_event({'type': 'appointment_updated', 'appointment': apt.to_dict()})
        except Exception:
            logger.exception('Failed to publish realtime event')

        logger.info(f"Appointment cancelled: {appointment_id} by user {user_id}")
        return jsonify({
            'success': True,
            'message': 'Appointment cancelled successfully',
            'appointment': apt.to_dict()
        }), 200
            
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
        
        # Query DB for booked slots
        booked = Appointment.query.filter_by(hospital_id=hospital_id).filter(
            Appointment.appointment_date >= datetime.fromisoformat(date),
            Appointment.appointment_date < datetime.fromisoformat(date) + timedelta(days=1),
            Appointment.status != AppointmentStatus.CANCELLED
        ).all()
        booked_slots = [b.appointment_time for b in booked if b.appointment_time]
        
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

@appointment_bp.route('/<appointment_id>/rate', methods=['POST'])
@require_auth()
def rate_appointment(appointment_id):
    """Rate and review a completed appointment"""
    try:
        user_id = get_authenticated_user_id()
        data = request.get_json()
        
        rating = data.get('rating')
        review = data.get('review', '')
        
        if not rating or not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
            return jsonify({'error': 'Valid rating (1-5) is required'}), 400
        
        apt = Appointment.query.get(appointment_id)
        if not apt:
            return jsonify({'error': 'Appointment not found'}), 404
            
        if apt.user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Prevent re-rating: once rated, the score is final
        if apt.rating is not None:
            return jsonify({
                'error': 'This appointment has already been rated',
                'existing_rating': apt.rating
            }), 409
            
        # Update rating and review in the database
        apt.rating = int(rating)
        apt.review = review
        db.session.commit()
        
        # Recalculate hospital average rating using true average of all ratings
        try:
            from models.hospital_matcher import get_hospital_matcher
            matcher = get_hospital_matcher()
            hospitals_list = matcher.hospitals
            
            # Compute true average from all rated appointments for this hospital
            rated_apts = Appointment.query.filter(
                Appointment.hospital_id == apt.hospital_id,
                Appointment.rating.isnot(None)
            ).all()

            if rated_apts:
                true_avg = round(sum(a.rating for a in rated_apts) / len(rated_apts), 1)
            else:
                true_avg = float(rating)

            # Find hospital in JSON and update
            for h in hospitals_list:
                if str(h.get('id')) == str(apt.hospital_id):
                    h['rating'] = true_avg
                    h['review_count'] = len(rated_apts)
                    
                    # Save back to file
                    with open(matcher.hospitals_db_path, 'w', encoding='utf-8') as fh:
                        json.dump({'hospitals': hospitals_list}, fh, indent=2)
                    
                    logger.info(
                        f"Updated hospital {apt.hospital_id} rating to {true_avg} "
                        f"({len(rated_apts)} reviews) in JSON"
                    )
                    break
        except Exception as ex:
            logger.error(f"Failed to update hospital rating in JSON: {ex}")
            
        logger.info(f"Appointment {appointment_id} rated: {rating} stars by user {user_id}")
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!',
            'appointment': apt.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error rating appointment: {e}")
        return jsonify({'error': str(e)}), 500

