"""
Google Maps Smart Routing
ETA calculation, route modes, and emergency-aware hospital ranking
"""

import logging
from typing import Dict, List, Any, Tuple
from enum import Enum
import math

logger = logging.getLogger(__name__)


class RouteMode(Enum):
    DRIVING = "driving"
    AMBULANCE = "ambulance"
    EMERGENCY = "emergency"
    PUBLIC_TRANSIT = "transit"
    WALKING = "walking"


class EmergencyRelevance(Enum):
    CRITICAL = 1.0      # Emergency department, ICU available
    HIGH = 0.8          # Full hospital with ER
    MODERATE = 0.6      # Primary care center with basic ER
    LOW = 0.4           # Clinic without full ER
    MINIMAL = 0.2       # Specialty center, non-emergency


class SmartMapRouter:
    """
    Intelligent hospital routing with emergency awareness
    - ETA calculation by route type
    - Emergency priority ranking
    - Distance-based hospital selection
    """
    
    # Sample hospital data (would normally come from database)
    SAMPLE_HOSPITALS = [
        {
            'id': 'hosp_001',
            'name': 'Apollo Hospitals',
            'lat': 12.9716,
            'lng': 77.6412,
            'has_emergency': True,
            'has_icu': True,
            'has_trauma': True,
            'rating': 4.8,
            'emergency_relevance': EmergencyRelevance.CRITICAL.value
        },
        {
            'id': 'hosp_002',
            'name': 'Fortis Bangalore',
            'lat': 12.9352,
            'lng': 77.6245,
            'has_emergency': True,
            'has_icu': True,
            'has_trauma': True,
            'rating': 4.7,
            'emergency_relevance': EmergencyRelevance.CRITICAL.value
        },
        {
            'id': 'hosp_003',
            'name': 'St. Johns Bangalore',
            'lat': 13.0011,
            'lng': 77.5722,
            'has_emergency': True,
            'has_icu': True,
            'has_trauma': False,
            'rating': 4.5,
            'emergency_relevance': EmergencyRelevance.HIGH.value
        },
        {
            'id': 'hosp_004',
            'name': 'Manipal Hospital',
            'lat': 13.0059,
            'lng': 77.5845,
            'has_emergency': True,
            'has_icu': True,
            'has_trauma': True,
            'rating': 4.6,
            'emergency_relevance': EmergencyRelevance.CRITICAL.value
        },
        {
            'id': 'hosp_005',
            'name': 'Max Healthcare',
            'lat': 12.97,
            'lng': 77.66,
            'has_emergency': True,
            'has_icu': False,
            'has_trauma': False,
            'rating': 4.4,
            'emergency_relevance': EmergencyRelevance.MODERATE.value
        }
    ]
    
    def __init__(self):
        self.user_location: Tuple[float, float] = None
        self.hospitals = self.SAMPLE_HOSPITALS.copy()
    
    def set_user_location(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Set current user location"""
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return {'success': False, 'message': 'Invalid coordinates'}
        
        self.user_location = (latitude, longitude)
        logger.info(f"User location set: {latitude}, {longitude}")
        
        return {
            'success': True,
            'location': {'lat': latitude, 'lng': longitude}
        }
    
    def find_nearest_hospital(
        self,
        user_lat: float,
        user_lng: float,
        urgency: str = "MODERATE",
        max_distance_km: float = 10
    ) -> Dict[str, Any]:
        """
        Find nearest hospital ranked by emergency relevance
        
        Args:
            user_lat, user_lng: User coordinates
            urgency: CRITICAL, HIGH, MODERATE, LOW
            max_distance_km: Maximum search radius
            
        Returns:
            Ranked list of hospitals with ETA
        """
        if not self.user_location and (user_lat is None or user_lng is None):
            return {'success': False, 'hospitals': []}
        
        if self.user_location:
            user_lat, user_lng = self.user_location
        
        # Calculate distance and emergency score for each hospital
        hospitals_scored = []
        for hospital in self.hospitals:
            distance_km = self._calculate_distance(
                user_lat, user_lng,
                hospital['lat'], hospital['lng']
            )
            
            if distance_km > max_distance_km:
                continue
            
            # Emergency relevance score (higher for critical facilities)
            relevance = hospital['emergency_relevance']
            if urgency == "CRITICAL":
                # For critical cases, heavily weight emergency dept availability
                if hospital['has_trauma']:
                    relevance *= 1.2
                if hospital['has_icu']:
                    relevance *= 1.1
            
            # Calculate ETA by mode
            eta_map = self._calculate_eta(distance_km)
            
            hospitals_scored.append({
                'id': hospital['id'],
                'name': hospital['name'],
                'lat': hospital['lat'],
                'lng': hospital['lng'],
                'distance_km': round(distance_km, 2),
                'emergency_relevance': relevance,
                'capabilities': {
                    'emergency_dept': hospital['has_emergency'],
                    'icu': hospital['has_icu'],
                    'trauma_center': hospital['has_trauma']
                },
                'rating': hospital['rating'],
                'eta': eta_map,
                'rank_score': self._calculate_rank_score(
                    distance_km,
                    relevance,
                    hospital['rating'],
                    urgency
                )
            })
        
        # Sort by rank score (highest first)
        hospitals_scored.sort(key=lambda x: x['rank_score'], reverse=True)
        
        logger.info(f"Found {len(hospitals_scored)} hospitals for urgency {urgency}")
        
        return {
            'success': True,
            'user_location': {'lat': user_lat, 'lng': user_lng},
            'urgency': urgency,
            'hospitals': hospitals_scored[:5],  # Top 5
            'total_found': len(hospitals_scored)
        }
    
    def get_route(
        self,
        user_lat: float,
        user_lng: float,
        hospital_id: str,
        route_mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        Get route to hospital
        
        Args:
            user_lat, user_lng: Start point
            hospital_id: Destination hospital
            route_mode: driving, ambulance, transit, walking
            
        Returns:
            Route details with directions
        """
        # Find hospital
        hospital = next((h for h in self.hospitals if h['id'] == hospital_id), None)
        if not hospital:
            return {'success': False, 'message': 'Hospital not found'}
        
        distance_km = self._calculate_distance(
            user_lat, user_lng,
            hospital['lat'], hospital['lng']
        )
        
        eta_data = self._calculate_eta(distance_km, route_mode)
        
        return {
            'success': True,
            'route': {
                'from': {'lat': user_lat, 'lng': user_lng},
                'to': {
                    'lat': hospital['lat'],
                    'lng': hospital['lng'],
                    'name': hospital['name']
                },
                'distance_km': round(distance_km, 2),
                'eta': eta_data,
                'mode': route_mode,
                'directions': self._generate_directions(route_mode, distance_km),
                'google_maps_url': self._generate_maps_url(user_lat, user_lng, hospital['lat'], hospital['lng']),
                'call_ambulance': route_mode == "ambulance"
            }
        }
    
    def rank_hospitals_by_emergency(
        self,
        user_lat: float,
        user_lng: float,
        urgency: str = "CRITICAL",
        specialties_needed: List[str] = None
    ) -> Dict[str, Any]:
        """
        Rank hospitals specifically for emergency situations
        Prioritizes facilities with required capabilities
        """
        result = self.find_nearest_hospital(user_lat, user_lng, urgency)
        
        if not result['success']:
            return result
        
        # If specialties specified, further rank
        if specialties_needed:
            for hospital in result['hospitals']:
                hospital['specialty_match'] = self._check_specialty_match(
                    hospital, specialties_needed
                )
            # Re-sort by specialty match
            result['hospitals'].sort(
                key=lambda x: (x.get('specialty_match', 0), x['rank_score']),
                reverse=True
            )
        
        return result
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Haversine formula for distance between coordinates"""
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _calculate_eta(self, distance_km: float, route_mode: str = "driving") -> Dict[str, Any]:
        """Calculate ETA by route mode"""
        # Average speeds (km/h)
        speeds = {
            "driving": 30,
            "ambulance": 50,
            "emergency": 50,
            "transit": 20,
            "walking": 5
        }
        
        speed = speeds.get(route_mode, 30)
        time_hours = distance_km / speed if speed > 0 else 0
        time_minutes = int(time_hours * 60)
        time_seconds = int((time_hours * 3600) % 60)
        
        return {
            'distance_km': round(distance_km, 2),
            'mode': route_mode,
            'eta_minutes': time_minutes,
            'eta_seconds': time_seconds,
            'eta_display': f"{time_minutes}m {time_seconds}s" if time_minutes > 0 else f"{time_seconds}s"
        }
    
    def _calculate_rank_score(
        self,
        distance_km: float,
        emergency_relevance: float,
        rating: float,
        urgency: str
    ) -> float:
        """Calculate ranking score for hospital"""
        # Normalize distance (lower is better, max 10km)
        distance_score = max(0, 100 - (distance_km * 10))
        
        # Emergency relevance score (0-100)
        relevance_score = emergency_relevance * 100
        
        # Rating boost (0-10 points)
        rating_score = (rating / 5.0) * 10
        
        # For critical urgency, weight emergency relevance heavily
        if urgency == "CRITICAL":
            return (relevance_score * 0.6) + (distance_score * 0.3) + (rating_score * 0.1)
        else:
            return (distance_score * 0.5) + (relevance_score * 0.3) + (rating_score * 0.2)
    
    def _check_specialty_match(self, hospital: Dict, specialties: List[str]) -> int:
        """Check hospital capability match with required specialties"""
        match_count = 0
        for specialty in specialties:
            if 'cardiac' in specialty.lower() and hospital['capabilities']['icu']:
                match_count += 1
            elif 'trauma' in specialty.lower() and hospital['capabilities']['trauma_center']:
                match_count += 1
            elif 'neuro' in specialty.lower() and hospital['capabilities']['icu']:
                match_count += 1
        return match_count
    
    def _generate_directions(self, mode: str, distance_km: float) -> List[str]:
        """Generate simple directions"""
        return [
            f"Head towards hospital ({distance_km:.1f} km away)",
            f"Use {mode.title()} mode for fastest arrival",
            "Follow the route on Google Maps for turn-by-turn directions",
            f"ETA updates will refresh as you travel"
        ]
    
    def _generate_maps_url(self, from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> str:
        """Generate Google Maps URL"""
        return f"https://maps.google.com/?saddr={from_lat},{from_lng}&daddr={to_lat},{to_lng}"


def get_smart_router() -> SmartMapRouter:
    """Get singleton router instance"""
    return SmartMapRouter()
