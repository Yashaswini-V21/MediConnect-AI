"""
MediConnect-AI M4: Analytics Models
SQLAlchemy ORM for tracking appointment and hospital trends.
"""

from datetime import datetime
from models.user_model import db

class AppointmentAnalytics(db.Model):
    """
    Daily aggregated metrics for appointment trends.
    Used for dashboard visualizations and demand forecasting.
    """
    __tablename__ = 'appointment_analytics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False, index=True)
    hospital_id = db.Column(db.Integer, None, nullable=True, index=True) # NULL = platform-wide totals
    
    # Booking counts
    total_bookings = db.Column(db.Integer, default=0)
    confirmed = db.Column(db.Integer, default=0)
    completed = db.Column(db.Integer, default=0)
    cancelled = db.Column(db.Integer, default=0)
    no_show = db.Column(db.Integer, default=0)
    
    # Urgency metrics
    high_urgency = db.Column(db.Integer, default=0)
    medium_urgency = db.Column(db.Integer, default=0)
    low_urgency = db.Column(db.Integer, default=0)
    
    # Advanced metrics
    avg_confirmation_time_mins = db.Column(db.Float, default=0.0)
    peak_hour = db.Column(db.Integer, nullable=True) # 0-23
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "hospital_id": self.hospital_id,
            "total_bookings": self.total_bookings,
            "confirmed": self.confirmed,
            "completed": self.completed,
            "cancelled": self.cancelled,
            "no_show": self.no_show,
            "high_urgency": self.high_urgency,
            "medium_urgency": self.medium_urgency,
            "low_urgency": self.low_urgency,
            "avg_confirmation_time_mins": self.avg_confirmation_time_mins,
            "peak_hour": self.peak_hour
        }
