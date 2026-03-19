from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models.user_model import db, User, SearchHistory, Favorite
from utils.email_sender import email_sender
from utils.analytics import analytics
from utils.auth_middleware import require_auth, get_authenticated_user_id
from datetime import timedelta
import re
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
def send_otp():
    """Send OTP to email for verification"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        if not validate_email(email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Send OTP
        success, otp_dev = email_sender.send_otp(email)
        
        if success:
            response = {
                'success': True,
                'message': 'OTP sent successfully to your email'
            }
            # Include OTP in response for development mode
            if otp_dev:
                response['otp_dev'] = otp_dev  # Only for testing
            
            logger.info(f"OTP sent to {email}")
            return jsonify(response), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP'}), 500
            
    except Exception as e:
        logger.error(f"Send OTP error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP for email"""
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        
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
        logger.error(f"Verify OTP error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================
# AUTHENTICATION ROUTES (Updated with OTP)
# ============================================

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'full_name', 'otp']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            logger.warning(f"Invalid email format attempted: {data['email']}")
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Verify OTP first (don't delete yet)
        is_valid, otp_message = email_sender.verify_otp(data['email'], data['otp'], delete_after_verify=False)
        if not is_valid:
            return jsonify({'success': False, 'message': f'OTP verification failed: {otp_message}'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            logger.warning(f"Duplicate registration attempt: {data['email']}")
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Validate password
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            logger.warning(f"Weak password attempt for: {data['email']}")
            return jsonify({'success': False, 'message': message}), 400
        
        # Create new user
        new_user = User(
            email=data['email'],
            full_name=data['full_name'],
            phone=data.get('phone'),
            preferred_language=data.get('preferred_language', 'en')
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        # Delete OTP after successful signup
        email_sender.delete_otp(data['email'])
        
        # Track new user registration
        analytics.track_new_user()
        
        logger.info(f"New user registered: {new_user.email}")
        
        # Create access token
        access_token = create_access_token(
            identity=new_user.id,
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'token': access_token,
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Signup error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('otp'):
            return jsonify({'success': False, 'message': 'Email and OTP are required'}), 400
        
        # Verify OTP first (don't delete yet)
        is_valid, otp_message = email_sender.verify_otp(data['email'], data['otp'], delete_after_verify=False)
        if not is_valid:
            return jsonify({'success': False, 'message': f'OTP verification failed: {otp_message}'}), 400
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            logger.warning(f"Failed login attempt for: {data.get('email')}")
            return jsonify({'success': False, 'message': 'User not found'}), 401
        
        if not user.is_active:
            logger.warning(f"Inactive account login attempt: {user.email}")
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Delete OTP after successful login
        email_sender.delete_otp(data['email'])
        
        logger.info(f"User logged in: {user.email}")
        
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@require_auth()
def get_current_user():
    try:
        user_id = get_authenticated_user_id()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        return jsonify({'success': True, 'user': user.to_dict()}), 200
        
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth()
def get_profile():
    try:
        user_id = get_authenticated_user_id()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        return jsonify({'success': True, 'user': user.to_dict()}), 200
        
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@require_auth()
def update_profile():
    try:
        user_id = get_authenticated_user_id()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'blood_group' in data:
            user.blood_group = data['blood_group']
        if 'emergency_contact' in data:
            user.emergency_contact = data['emergency_contact']
        if 'preferred_language' in data:
            user.preferred_language = data['preferred_language']
        
        db.session.commit()
        
        logger.info(f"Profile updated: {user.email}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update profile error: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
def change_password():
    try:
        user_id = get_authenticated_user_id()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
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
        logger.error(f"Change password error: {str(e)}")
        return jsonify({'error': str(e)}), 500
