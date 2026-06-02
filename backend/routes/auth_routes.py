from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models.user_model import db, User, SearchHistory, Favorite
from utils.email_sender import email_sender
from utils.analytics import analytics
from utils.auth_middleware import require_auth, get_authenticated_user_id
from utils.security import limiter
from datetime import timedelta
import re
import os
import logging

auth_bp = Blueprint('auth', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Valid"

# ============================================
# OTP ROUTES
# ============================================

@auth_bp.route('/send-otp', methods=['POST'])
@limiter.limit("3 per 10 minutes")
def send_otp():
    """Send OTP to email for verification"""
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        if len(email) > 120:
            return jsonify({'success': False, 'message': 'Invalid email address'}), 400

        if not validate_email(email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400

        # Send OTP
        success, otp_dev = email_sender.send_otp(email)

        if success:
            response = {
                'success': True,
                'message': 'OTP sent successfully to your email'
            }
            # Only include OTP in response in development mode — never in production
            if otp_dev and os.getenv('FLASK_ENV', 'development') == 'development':
                response['otp_dev'] = otp_dev

            logger.info(f"OTP sent to {email}")
            return jsonify(response), 200
        else:
            return jsonify({'success': False, 'message': 'Too many OTP requests. Please wait before requesting another.'}), 429

    except Exception as e:
        logger.error(f"Send OTP error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to send OTP. Please try again.'}), 500

@auth_bp.route('/verify-otp', methods=['POST'])
@limiter.limit("10 per minute")
def verify_otp():
    """Verify OTP for email"""
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        otp = data.get('otp', '').strip()

        if not email or not otp:
            return jsonify({'success': False, 'message': 'Email and OTP are required'}), 400

        # Verify OTP
        is_valid, message = email_sender.verify_otp(email, otp)

        if is_valid:
            logger.info(f"OTP verified for {email}")
            return jsonify({'success': True, 'message': message}), 200
        else:
            logger.warning(f"OTP verification failed for {email}: {message}")
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        logger.error(f"Verify OTP error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'OTP verification failed. Please try again.'}), 500

# ============================================
# AUTHENTICATION ROUTES (Updated with OTP)
# ============================================

@auth_bp.route('/signup', methods=['POST'])
@limiter.limit("5 per hour")
def signup():
    try:
        data = request.get_json() or {}

        # Validate required fields
        required_fields = ['email', 'password', 'full_name', 'otp']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'{field} is required'}), 400

        email = data['email'].strip().lower()
        full_name = data['full_name'].strip()

        # Validate lengths
        if len(email) > 120:
            return jsonify({'success': False, 'message': 'Email address is too long'}), 400
        if len(full_name) > 100:
            return jsonify({'success': False, 'message': 'Full name is too long (max 100 characters)'}), 400
        if len(data['password']) > 128:
            return jsonify({'success': False, 'message': 'Password is too long'}), 400

        # Validate email format
        if not validate_email(email):
            logger.warning(f"Invalid email format attempted: {email}")
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400

        # Verify OTP first (don't delete yet)
        is_valid, otp_message = email_sender.verify_otp(email, data['otp'], delete_after_verify=False)
        if not is_valid:
            return jsonify({'success': False, 'message': f'OTP verification failed: {otp_message}'}), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            logger.warning(f"Duplicate registration attempt: {email}")
            return jsonify({'success': False, 'message': 'Email already registered'}), 400

        # Validate password
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'success': False, 'message': message}), 400

        # Create new user
        new_user = User(
            email=email,
            full_name=full_name,
            phone=data.get('phone'),
            preferred_language=data.get('preferred_language', 'en')
        )
        new_user.set_password(data['password'])

        db.session.add(new_user)
        db.session.commit()

        # Delete OTP after successful signup
        email_sender.delete_otp(email)

        # Track new user registration
        analytics.track_new_user()

        logger.info(f"New user registered: {new_user.email}")

        # Create access token
        access_token = create_access_token(
            identity=str(new_user.id),
            expires_delta=timedelta(hours=24)
        )

        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'token': access_token,
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Signup error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    try:
        data = request.get_json() or {}

        email = data.get('email', '').strip().lower()
        otp = data.get('otp', '').strip()

        # Validate required fields
        if not email or not otp:
            return jsonify({'success': False, 'message': 'Email and OTP are required'}), 400

        if not validate_email(email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400

        # Verify OTP first (don't delete yet)
        is_valid, otp_message = email_sender.verify_otp(email, otp, delete_after_verify=False)
        if not is_valid:
            return jsonify({'success': False, 'message': f'OTP verification failed: {otp_message}'}), 400

        # Find user
        user = User.query.filter_by(email=email).first()

        if not user:
            logger.warning(f"Login attempt for non-existent email: {email}")
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

        if not user.is_active:
            logger.warning(f"Inactive account login attempt: {user.email}")
            return jsonify({'error': 'Account is deactivated'}), 403

        # Delete OTP after successful login
        email_sender.delete_otp(email)

        logger.info(f"User logged in: {user.email}")

        # Create access token (24h expiry for security)
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=24)
        )

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': access_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Login failed. Please try again.'}), 500

@auth_bp.route('/me', methods=['GET'])
@require_auth()
def get_current_user():
    try:
        user_id = get_authenticated_user_id()
        user = db.session.get(User, user_id)

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        return jsonify({'success': True, 'user': user.to_dict()}), 200

    except Exception as e:
        logger.error(f"Get current user error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to retrieve user profile.'}), 500


@auth_bp.route('/firebase-sync', methods=['POST'])
@require_auth()
def sync_firebase_profile():
    """Sync authenticated Firebase user profile data into local backend user record."""
    try:
        user_id = get_authenticated_user_id()
        user = User.query.get(user_id)

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        data = request.get_json(silent=True) or {}
        updated_fields = []

        full_name = (data.get('full_name') or data.get('display_name') or '').strip()
        phone = (data.get('phone') or '').strip()
        preferred_language = (data.get('preferred_language') or '').strip()
        email = (data.get('email') or '').strip().lower()

        if full_name and full_name != user.full_name:
            user.full_name = full_name
            updated_fields.append('full_name')

        if phone and phone != (user.phone or ''):
            user.phone = phone
            updated_fields.append('phone')

        if preferred_language and preferred_language != (user.preferred_language or 'en'):
            user.preferred_language = preferred_language
            updated_fields.append('preferred_language')

        if email and email != user.email:
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user.id:
                return jsonify({
                    'success': False,
                    'message': 'Email already exists for another account'
                }), 409
            user.email = email
            updated_fields.append('email')

        if updated_fields:
            db.session.commit()
            logger.info(f"Synced Firebase profile for user {user_id}: {', '.join(updated_fields)}")

        return jsonify({
            'success': True,
            'message': 'Profile synced successfully',
            'updated_fields': updated_fields,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Firebase profile sync error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth()
def get_profile():
    try:
        user_id = get_authenticated_user_id()
        user = db.session.get(User, user_id)

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        return jsonify({'success': True, 'user': user.to_dict()}), 200

    except Exception as e:
        logger.error(f"Get profile error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to retrieve profile.'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@require_auth()
def update_profile():
    try:
        user_id = get_authenticated_user_id()
        user = db.session.get(User, user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}

        # Update allowed fields with length validation
        if 'full_name' in data:
            name = str(data['full_name']).strip()
            if len(name) > 100:
                return jsonify({'error': 'Full name too long (max 100 characters)'}), 400
            user.full_name = name
        if 'phone' in data:
            phone = str(data['phone']).strip()
            if len(phone) > 15:
                return jsonify({'error': 'Phone number too long'}), 400
            user.phone = phone
        if 'blood_group' in data:
            user.blood_group = str(data['blood_group'])[:5]
        if 'emergency_contact' in data:
            user.emergency_contact = str(data['emergency_contact'])[:15]
        if 'preferred_language' in data:
            user.preferred_language = str(data['preferred_language'])[:5]

        db.session.commit()

        logger.info(f"Profile updated: {user.email}")

        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update profile error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update profile. Please try again.'}), 500

@auth_bp.route('/search-history', methods=['GET'])
@require_auth()
def get_search_history():
    try:
        user_id = get_authenticated_user_id()
        history = SearchHistory.query.filter_by(user_id=user_id)\
            .order_by(SearchHistory.timestamp.desc())\
            .limit(20).all()
        
        return jsonify({
            'history': [h.to_dict() for h in history]
        }), 200
        
    except Exception as e:
        logger.error(f"Get search history error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/search-history', methods=['POST'])
@require_auth()
def add_search_history():
    try:
        user_id = get_authenticated_user_id()
        data = request.get_json()
        
        if not data.get('symptoms'):
            return jsonify({'error': 'symptoms is required'}), 400
        
        history = SearchHistory(
            user_id=user_id,
            symptoms=data['symptoms'],
            urgency_level=data.get('urgency_level'),
            specialties=data.get('specialties')
        )
        
        db.session.add(history)
        db.session.commit()
        
        logger.info(f"Search history added for user: {user_id}")
        
        return jsonify({
            'message': 'Search history saved',
            'history': history.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Add search history error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/favorites', methods=['GET'])
@require_auth()
def get_favorites():
    try:
        user_id = get_authenticated_user_id()
        favorites = Favorite.query.filter_by(user_id=user_id)\
            .order_by(Favorite.added_at.desc()).all()
        
        return jsonify({
            'favorites': [f.to_dict() for f in favorites]
        }), 200
        
    except Exception as e:
        logger.error(f"Get favorites error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/favorites', methods=['POST'])
@require_auth()
def add_favorite():
    try:
        user_id = get_authenticated_user_id()
        data = request.get_json()
        
        if not data.get('hospital_id'):
            return jsonify({'error': 'hospital_id is required'}), 400
        
        # Check if already favorited
        existing = Favorite.query.filter_by(
            user_id=user_id,
            hospital_id=data['hospital_id']
        ).first()
        
        if existing:
            return jsonify({'error': 'Hospital already in favorites'}), 409
        
        favorite = Favorite(
            user_id=user_id,
            hospital_id=data['hospital_id']
        )
        
        db.session.add(favorite)
        db.session.commit()
        
        logger.info(f"Favorite added for user {user_id}: {data['hospital_id']}")
        
        return jsonify({
            'message': 'Added to favorites',
            'favorite': favorite.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Add favorite error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/favorites/<int:favorite_id>', methods=['DELETE'])
@require_auth()
def remove_favorite(favorite_id):
    try:
        user_id = get_authenticated_user_id()
        favorite = Favorite.query.filter_by(id=favorite_id, user_id=user_id).first()
        
        if not favorite:
            return jsonify({'error': 'Favorite not found'}), 404
        
        db.session.delete(favorite)
        db.session.commit()
        
        logger.info(f"Favorite removed for user {user_id}: {favorite_id}")
        
        return jsonify({'message': 'Removed from favorites'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Remove favorite error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@require_auth()
@limiter.limit("5 per hour")
def change_password():
    try:
        user_id = get_authenticated_user_id()
        user = db.session.get(User, user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}

        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current and new passwords are required'}), 400

        if not user.check_password(data['current_password']):
            logger.warning(f"Incorrect password attempt for user: {user.email}")
            return jsonify({'error': 'Current password is incorrect'}), 401

        # Validate new password
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': message}), 400

        user.set_password(data['new_password'])
        db.session.commit()

        logger.info(f"Password changed for user: {user.email}")

        return jsonify({'message': 'Password changed successfully'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Change password error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to change password. Please try again.'}), 500
