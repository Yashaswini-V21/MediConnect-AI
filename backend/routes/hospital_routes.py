from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.hospital_matcher import get_hospital_matcher
from utils.analytics import analytics
import logging

hospital_bp = Blueprint('hospitals', __name__)
logger = logging.getLogger(__name__)

@hospital_bp.route('/search', methods=['POST'])
def search_hospitals():
    """Search hospitals based on criteria"""
    try:
        data = request.get_json()
        
        # Extract search parameters
        specialties = data.get('specialties', [])
        user_location = data.get('location', {})
        urgency = data.get('urgency', 'MEDIUM')
        filters = data.get('filters', {})
        
        # Validate urgency level
        if urgency not in ['HIGH', 'MEDIUM', 'LOW']:
            urgency = 'MEDIUM'
        
        # Get matcher instance
        matcher = get_hospital_matcher()
        
        # Find matching hospitals
        hospitals = matcher.find_hospitals(
            specialties=specialties,
            user_location=user_location,
            urgency=urgency,
            filters=filters
        )
        
        logger.info(f"Hospital search: {len(hospitals)} results for urgency={urgency}")
        
        return jsonify({
            'success': True,
            'count': len(hospitals),
            'hospitals': hospitals,
            'urgency': urgency
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching hospitals: {e}")
        return jsonify({'error': str(e)}), 500

@hospital_bp.route('/emergency', methods=['POST'])
def get_emergency_hospitals():
    """Get nearest emergency hospitals"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('latitude') or not data.get('longitude'):
            return jsonify({'error': 'Location coordinates are required'}), 400
        
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        radius = float(data.get('radius', 10.0))
        limit = int(data.get('limit', 10))
        
        # Get matcher instance
        matcher = get_hospital_matcher()
        
        # Get nearby emergency hospitals
        hospitals = matcher.find_emergency_hospitals(
            user_location={'lat': latitude, 'lng': longitude},
            max_results=limit
        )
        
        # Track emergency use
        analytics.track_emergency_use()
        
        return jsonify({
            'success': True,
            'count': len(hospitals),
            'hospitals': hospitals
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hospital_bp.route('/<hospital_id>', methods=['GET'])
def get_hospital_details(hospital_id):
    """Get detailed information about a specific hospital"""
    try:
        matcher = get_hospital_matcher()
        hospital = matcher.get_hospital_by_id(hospital_id)
        
        if not hospital:
            return jsonify({'error': 'Hospital not found'}), 404
        
        # Track hospital view
        analytics.track_hospital_view(hospital_id)
        
        return jsonify({
            'success': True,
            'hospital': hospital
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hospital_bp.route('/track/call', methods=['POST'])
def track_hospital_call():
    """Track when user calls a hospital"""
    try:
        analytics.track_hospital_call()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hospital_bp.route('/track/directions', methods=['POST'])
def track_directions_request():
    """Track when user requests directions"""
    try:
        analytics.track_directions_request()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hospital_bp.route('/list', methods=['GET'])
def list_all_hospitals():
    """Get list of all hospitals"""
    try:
        # Get query parameters
        hospital_type = request.args.get('type')
        specialty = request.args.get('specialty')
        
        matcher = get_hospital_matcher()
        hospitals = matcher.hospitals.copy()
        
        # Filter by type
        if hospital_type:
            hospitals = [h for h in hospitals if h.get('type', '').lower() == hospital_type.lower()]
        
        # Filter by specialty
        if specialty:
            hospitals = [
                h for h in hospitals
                if any(specialty.lower() in s.lower() for s in h.get('specialties', []))
            ]
        
        return jsonify({
            'success': True,
            'count': len(hospitals),
            'hospitals': hospitals
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hospital_bp.route('/specialties', methods=['GET'])
def get_specialties():
    """Get list of all available specialties"""
    try:
        # Extract unique specialties from all hospitals
        specialties = set()
        matcher = get_hospital_matcher()
        for hospital in matcher.hospitals:
            specialties.update(hospital.get('specialties', []))
        
        return jsonify({
            'success': True,
            'specialties': sorted(list(specialties))
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
