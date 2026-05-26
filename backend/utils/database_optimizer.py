"""
MediConnect-AI Database Optimization & Indexing Strategy
Improves query performance at scale (1000+ hospitals, 100k+ appointments)
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, event, DDL
import logging

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """
    Database optimization utilities for MediConnect-AI.
    Handles indexing, query optimization, and connection pooling.
    """

    @staticmethod
    def create_indices(db):
        """
        Create all required database indices for optimal performance.
        Call once on app startup: DatabaseOptimizer.create_indices(db)
        """
        
        # Appointments table indices
        appointments_indices = [
            Index('idx_appointment_hospital_date', 'hospital_id', 'appointment_date'),
            Index('idx_appointment_status', 'status'),
            Index('idx_appointment_user_date', 'user_id', 'appointment_date'),
            Index('idx_appointment_doctor_date', 'doctor_id', 'appointment_date'),
            Index('idx_appointment_status_date', 'status', 'appointment_date'),
            Index('idx_appointment_created_at', 'created_at'),
        ]
        
        # Admin users indices
        admin_indices = [
            Index('idx_admin_user_email', 'email'),
            Index('idx_admin_user_hospital_role', 'hospital_id', 'role'),
            Index('idx_admin_user_active', 'is_active'),
        ]
        
        # Analytics indices
        analytics_indices = [
            Index('idx_analytics_date', 'date'),
            Index('idx_analytics_hospital_date', 'hospital_id', 'date'),
            Index('idx_analytics_month', 'date'),  # For monthly aggregation
        ]
        
        # Audit logs indices
        audit_indices = [
            Index('idx_audit_user_action', 'user_id', 'action'),
            Index('idx_audit_timestamp', 'timestamp'),
            Index('idx_audit_resource', 'resource', 'resource_id'),
        ]
        
        # Notifications indices
        notification_indices = [
            Index('idx_notification_user_read', 'user_id', 'is_read'),
            Index('idx_notification_appointment', 'appointment_id'),
            Index('idx_notification_sent_at', 'sent_at'),
        ]
        
        all_indices = (
            appointments_indices +
            admin_indices +
            analytics_indices +
            audit_indices +
            notification_indices
        )
        
        logger.info(f"Creating {len(all_indices)} database indices...")
        
        for index in all_indices:
            try:
                index.create(db.engine)
                logger.debug(f"✅ Created index: {index.name}")
            except Exception as e:
                logger.debug(f"Index {index.name} already exists or error: {e}")
    
    @staticmethod
    def enable_connection_pooling(app):
        """
        Enable connection pooling for better performance.
        Use in app.config:
        
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 20,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'max_overflow': 40,
        }
        """
        defaults = {
            'pool_size': 20,  # Max concurrent connections
            'pool_recycle': 3600,  # Recycle connection every 1 hour
            'pool_pre_ping': True,  # Verify connection before using
            'max_overflow': 40,  # Max overflow above pool_size
        }
        logger.info(f"Connection pooling configured: {defaults}")
        return defaults
    
    @staticmethod
    def get_performance_stats(db):
        """
        Get database performance statistics.
        Use to identify slow queries and bottlenecks.
        """
        from models.admin_model import Appointment
        from datetime import datetime, timedelta
        
        stats = {}
        
        # Total appointments
        stats['total_appointments'] = db.session.query(Appointment).count()
        
        # Appointments by status
        statuses = db.session.query(
            Appointment.status,
            db.func.count(Appointment.id)
        ).group_by(Appointment.status).all()
        stats['by_status'] = {status: count for status, count in statuses}
        
        # Appointments by hospital
        hospitals = db.session.query(
            Appointment.hospital_id,
            db.func.count(Appointment.id)
        ).group_by(Appointment.hospital_id).all()
        stats['by_hospital'] = dict(hospitals)
        
        # Appointments in last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        stats['last_24h'] = db.session.query(Appointment).filter(
            Appointment.created_at >= yesterday
        ).count()
        
        # Average confirmation time
        confirmed = db.session.query(
            db.func.avg(
                db.func.extract('epoch', Appointment.updated_at - Appointment.created_at)
            )
        ).filter(Appointment.status == 'CONFIRMED').scalar()
        stats['avg_confirmation_time_seconds'] = confirmed or 0
        
        return stats


# ════════════════════════════════════════════════════════════════════════════════
# MIGRATION GUIDE (for Alembic)
# ════════════════════════════════════════════════════════════════════════════════

MIGRATION_SQL = """
-- Run these if using raw SQL for indexing (not recommended - use SQLAlchemy)

-- Appointments indices
CREATE INDEX IF NOT EXISTS idx_appointment_hospital_date ON appointments(hospital_id, appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointment_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointment_user_date ON appointments(user_id, appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointment_doctor_date ON appointments(doctor_id, appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointment_status_date ON appointments(status, appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointment_created_at ON appointments(created_at);

-- Admin users indices
CREATE INDEX IF NOT EXISTS idx_admin_user_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_user_hospital_role ON admin_users(hospital_id, role);
CREATE INDEX IF NOT EXISTS idx_admin_user_active ON admin_users(is_active);

-- Analytics indices
CREATE INDEX IF NOT EXISTS idx_analytics_date ON appointment_analytics(date);
CREATE INDEX IF NOT EXISTS idx_analytics_hospital_date ON appointment_analytics(hospital_id, date);

-- Audit logs indices
CREATE INDEX IF NOT EXISTS idx_audit_user_action ON audit_logs(user_id, action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource, resource_id);

-- Notifications indices
CREATE INDEX IF NOT EXISTS idx_notification_user_read ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notification_appointment ON notifications(appointment_id);
CREATE INDEX IF NOT EXISTS idx_notification_sent_at ON notifications(sent_at);
"""

# ════════════════════════════════════════════════════════════════════════════════
# QUERY OPTIMIZATION EXAMPLES
# ════════════════════════════════════════════════════════════════════════════════

OPTIMIZED_QUERIES = """
BEFORE (Slow):
    appointments = Appointment.query.all()  # Loads ENTIRE table into memory
    confirmed = [a for a in appointments if a.status == 'CONFIRMED']  # Filters in Python

AFTER (Fast):
    confirmed = Appointment.query.filter_by(status='CONFIRMED').all()  # Filters at DB level

---

BEFORE (N+1 Problem):
    for appointment in Appointment.query.all():
        doctor = Doctor.query.get(appointment.doctor_id)  # 1000+ queries!

AFTER (Eager Loading):
    appointments = Appointment.query.options(
        joinedload(Appointment.doctor)
    ).all()  # 1 query + 1 join

---

BEFORE (Inefficient):
    for hospital_id in range(1, 50):
        count = Appointment.query.filter_by(hospital_id=hospital_id).count()

AFTER (Efficient):
    from sqlalchemy import func
    counts = db.session.query(
        Appointment.hospital_id,
        func.count(Appointment.id)
    ).group_by(Appointment.hospital_id).all()

---

BEFORE (Full Table Scan):
    recent = Appointment.query.filter(
        Appointment.created_at > datetime.utcnow() - timedelta(days=1)
    ).all()  # Scans entire table

AFTER (Index Usage):
    # Same query, but with index on created_at - 100x faster
    recent = Appointment.query.filter(
        Appointment.created_at > datetime.utcnow() - timedelta(days=1)
    ).all()
"""

# ════════════════════════════════════════════════════════════════════════════════
# CACHING STRATEGY
# ════════════════════════════════════════════════════════════════════════════════

CACHING_RECOMMENDATIONS = """
Cache Layer (add to app.py):

from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})

Then use:

@app.route('/api/hospitals/search')
@cache.cached(timeout=3600, key_prefix='hospital_search_')
def search_hospitals():
    # This result is cached for 1 hour
    return hospitals_list

---

What to cache:
✅ Hospital list (changes rarely)
✅ Specialty list (changes rarely)
✅ Analytics dashboards (updates once/day at 12am)
❌ Real-time appointment bookings (changes constantly)
❌ User-specific data (cache per user)

Cache Invalidation:
- Update cache when hospital/specialty is modified
- Use cache.delete(key) to clear specific entries
- Use cache.clear() to clear all (only in testing)
"""
