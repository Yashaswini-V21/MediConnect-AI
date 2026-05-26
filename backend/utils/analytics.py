import json
import os
from datetime import datetime, date, timedelta
from threading import Lock
from sqlalchemy import func
from models.user_model import db
from models.admin_model import Appointment, AppointmentStatus, UrgencyLevel
from models.analytics_model import AppointmentAnalytics

class Analytics:
    """Analytics tracking for MediConnect AI - Microsoft Imagine Cup 2026"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'analytics.json')
        self.lock = Lock()
        self.load_analytics()
    
    def load_analytics(self):
        """Load analytics data from JSON file"""
        try:
            # Create instance directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with open(self.db_path, 'r') as f:
                self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Initialize with default data
            self.data = {
                'total_searches': 0,
                'emergency_mode_uses': 0,
                'avg_response_time_ms': [],
                'top_symptoms': {},
                'top_hospitals_viewed': {},
                'languages_used': {'en': 0, 'kn': 0},
                'time_saved_minutes': 0,
                'total_users': 0,
                'searches_by_urgency': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
                'total_hospitals_called': 0,
                'total_directions_requested': 0,
                'created_at': datetime.utcnow().isoformat(),
                'last_updated': datetime.utcnow().isoformat()
            }
            self.save()
    
    def track_symptom_search(self, symptoms, urgency, response_time_ms, language='en'):
        """Track a symptom search event"""
        with self.lock:
            self.data['total_searches'] += 1
            self.data['searches_by_urgency'][urgency] += 1
            self.data['languages_used'][language] += 1
            self.data['avg_response_time_ms'].append(response_time_ms)
            
            # Keep only last 1000 response times to avoid memory issues
            if len(self.data['avg_response_time_ms']) > 1000:
                self.data['avg_response_time_ms'] = self.data['avg_response_time_ms'][-1000:]
            
            # Assuming 30 minutes saved per search (conservative estimate)
            self.data['time_saved_minutes'] += 30
            
            # Track popular symptoms
            symptom_key = symptoms.lower()[:100]  # Limit length
            if symptom_key in self.data['top_symptoms']:
                self.data['top_symptoms'][symptom_key] += 1
            else:
                self.data['top_symptoms'][symptom_key] = 1
            
            self.data['last_updated'] = datetime.utcnow().isoformat()
            self.save()
    
    def track_emergency_use(self):
        """Track emergency mode activation"""
        with self.lock:
            self.data['emergency_mode_uses'] += 1
            # Emergency saves more time (45 minutes)
            self.data['time_saved_minutes'] += 45
            self.data['last_updated'] = datetime.utcnow().isoformat()
            self.save()
    
    def track_hospital_view(self, hospital_id):
        """Track hospital detail view"""
        with self.lock:
            hospital_key = str(hospital_id)
            if hospital_key in self.data['top_hospitals_viewed']:
                self.data['top_hospitals_viewed'][hospital_key] += 1
            else:
                self.data['top_hospitals_viewed'][hospital_key] = 1
            
            self.data['last_updated'] = datetime.utcnow().isoformat()
            self.save()
    
    def track_hospital_call(self):
        """Track when user calls a hospital"""
        with self.lock:
            self.data['total_hospitals_called'] += 1
            self.data['last_updated'] = datetime.utcnow().isoformat()
            self.save()
    
    def track_directions_request(self):
        """Track when user requests directions"""
        with self.lock:
            self.data['total_directions_requested'] += 1
            self.data['last_updated'] = datetime.utcnow().isoformat()
            self.save()
    
    def track_new_user(self):
        """Track new user registration"""
        with self.lock:
            self.data['total_users'] += 1
            self.data['last_updated'] = datetime.utcnow().isoformat()
            self.save()
    
    def get_stats(self):
        """Get comprehensive analytics statistics"""
        with self.lock:
            # Calculate average response time
            avg_response = 0
            if self.data['avg_response_time_ms']:
                avg_response = sum(self.data['avg_response_time_ms']) / len(self.data['avg_response_time_ms'])
            
            # Calculate total searches
            total_searches = max(1, self.data['total_searches'])
            
            # Get top 5 symptoms
            top_symptoms = sorted(
                self.data['top_symptoms'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Get top 5 hospitals
            top_hospitals = sorted(
                self.data['top_hospitals_viewed'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Calculate percentages
            kannada_usage = (self.data['languages_used']['kn'] / total_searches) * 100
            high_urgency = (self.data['searches_by_urgency']['HIGH'] / total_searches) * 100
            medium_urgency = (self.data['searches_by_urgency']['MEDIUM'] / total_searches) * 100
            low_urgency = (self.data['searches_by_urgency']['LOW'] / total_searches) * 100
            
            # Calculate lives potentially saved (conservative: 1 life per 100 high-urgency searches)
            lives_saved = self.data['searches_by_urgency']['HIGH'] // 100
            
            # Calculate cost savings (₹8,500 per wrong hospital visit avoided)
            cost_saved_inr = self.data['total_searches'] * 8500
            
            return {
                # Core Metrics
                'total_searches': self.data['total_searches'],
                'emergency_uses': self.data['emergency_mode_uses'],
                'total_users': self.data['total_users'],
                
                # Performance Metrics
                'avg_response_time_ms': round(avg_response, 2),
                'avg_response_time_sec': round(avg_response / 1000, 2),
                
                # Time Saved
                'total_time_saved_minutes': self.data['time_saved_minutes'],
                'total_time_saved_hours': round(self.data['time_saved_minutes'] / 60, 1),
                'total_time_saved_days': round(self.data['time_saved_minutes'] / 1440, 1),
                
                # Language Usage
                'english_usage': self.data['languages_used']['en'],
                'kannada_usage': self.data['languages_used']['kn'],
                'kannada_usage_percent': round(kannada_usage, 1),
                
                # Urgency Distribution
                'high_urgency_searches': self.data['searches_by_urgency']['HIGH'],
                'medium_urgency_searches': self.data['searches_by_urgency']['MEDIUM'],
                'low_urgency_searches': self.data['searches_by_urgency']['LOW'],
                'high_urgency_percent': round(high_urgency, 1),
                'medium_urgency_percent': round(medium_urgency, 1),
                'low_urgency_percent': round(low_urgency, 1),
                
                # Engagement Metrics
                'total_hospitals_called': self.data['total_hospitals_called'],
                'total_directions_requested': self.data['total_directions_requested'],
                'engagement_rate': round((self.data['total_hospitals_called'] + self.data['total_directions_requested']) / total_searches * 100, 1) if total_searches > 0 else 0,
                
                # Top Data
                'top_symptoms': [{'symptom': s[0], 'count': s[1]} for s in top_symptoms],
                'top_hospitals_viewed': [{'hospital_id': h[0], 'views': h[1]} for h in top_hospitals],
                
                # Impact Metrics (for Imagine Cup!)
                'lives_potentially_saved': lives_saved,
                'cost_saved_inr': cost_saved_inr,
                'cost_saved_usd': round(cost_saved_inr / 83, 2),  # Approx conversion
                
                # Metadata
                'created_at': self.data['created_at'],
                'last_updated': self.data['last_updated']
            }
    
    def get_dashboard_stats(self):
        """Get simplified stats for dashboard display"""
        stats = self.get_stats()
        return {
            'total_searches': stats['total_searches'],
            'total_users': stats['total_users'],
            'avg_response_time_ms': stats['avg_response_time_ms'],
            'kannada_usage_percent': stats['kannada_usage_percent'],
            'high_urgency_percent': stats['high_urgency_percent'],
            'total_time_saved_hours': stats['total_time_saved_hours']
        }

    def run_daily_aggregation(self):
        """Aggregate appointment data for yesterday and store in database"""
        yesterday = date.today() - timedelta(days=1)
        
        # 1. Platform-wide aggregation
        self._aggregate_for_scope(yesterday, hospital_id=None)
        
        # 2. Per-hospital aggregation
        hospitals_with_appointments = db.session.query(Appointment.hospital_id).distinct().all()
        for hospital in hospitals_with_appointments:
            self._aggregate_for_scope(yesterday, hospital_id=hospital[0])
            
        return f"✅ Analytics aggregated for {yesterday}"

    def _aggregate_for_scope(self, target_date, hospital_id=None):
        """Internal helper to aggregate stats for a specific date and hospital scope"""
        query = Appointment.query.filter(func.date(Appointment.appointment_date) == target_date)
        
        if hospital_id:
            query = query.filter(Appointment.hospital_id == hospital_id)
            
        appointments = query.all()
        
        if not appointments:
            return
            
        stats = {
            "total": len(appointments),
            "confirmed": len([a for a in appointments if a.status == AppointmentStatus.CONFIRMED]),
            "completed": len([a for a in appointments if a.status == AppointmentStatus.COMPLETED]),
            "cancelled": len([a for a in appointments if a.status == AppointmentStatus.CANCELLED]),
            "no_show": len([a for a in appointments if a.status == AppointmentStatus.NO_SHOW]),
            "high": len([a for a in appointments if a.urgency_level == UrgencyLevel.HIGH]),
            "medium": len([a for a in appointments if a.urgency_level == UrgencyLevel.MEDIUM]),
            "low": len([a for a in appointments if a.urgency_level == UrgencyLevel.LOW])
        }
        
        # Check if record already exists
        record = AppointmentAnalytics.query.filter_by(date=target_date, hospital_id=hospital_id).first()
        
        if not record:
            record = AppointmentAnalytics(date=target_date, hospital_id=hospital_id)
            db.session.add(record)
            
        record.total_bookings = stats["total"]
        record.confirmed = stats["confirmed"]
        record.completed = stats["completed"]
        record.cancelled = stats["cancelled"]
        record.no_show = stats["no_show"]
        record.high_urgency = stats["high"]
        record.medium_urgency = stats["medium"]
        record.low_urgency = stats["low"]
        
        db.session.commit()

    def get_time_series_data(self, days=30, hospital_id=None):
        """Fetch historical data for charting (Recharts)"""
        start_date = date.today() - timedelta(days=days)
        
        query = AppointmentAnalytics.query.filter(AppointmentAnalytics.date >= start_date)
        
        if hospital_id:
            query = query.filter_by(hospital_id=hospital_id)
        else:
            query = query.filter(AppointmentAnalytics.hospital_id.is_(None))
            
        results = query.order_by(AppointmentAnalytics.date.asc()).all()
        
        return [r.to_dict() for r in results]
    
    def save(self):
        """Save analytics data to JSON file"""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving analytics: {e}")
    
    def reset_analytics(self):
        """Reset all analytics (admin only - for testing)"""
        with self.lock:
            self.data = {
                'total_searches': 0,
                'emergency_mode_uses': 0,
                'avg_response_time_ms': [],
                'top_symptoms': {},
                'top_hospitals_viewed': {},
                'languages_used': {'en': 0, 'kn': 0},
                'time_saved_minutes': 0,
                'total_users': 0,
                'searches_by_urgency': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
                'total_hospitals_called': 0,
                'total_directions_requested': 0,
                'created_at': datetime.utcnow().isoformat(),
                'last_updated': datetime.utcnow().isoformat()
            }
            self.save()


# Initialize global analytics instance
analytics = Analytics()
