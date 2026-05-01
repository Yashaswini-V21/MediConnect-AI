import sys
import os
from datetime import date, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import app
from utils.analytics import Analytics
from models.user_model import db

def seed_analytics():
    with app.app_context():
        # Only seed if table is empty
        try:
            from models.analytics_model import AppointmentAnalytics
            if AppointmentAnalytics.query.count() > 0:
                print("Analytics already seeded.")
                return
        except:
            print("Creating tables...")
            db.create_all()

        analyzer = Analytics()
        
        # Seed last 30 days of data
        today = date.today()
        for i in range(30, 0, -1):
            d = today - timedelta(days=i)
            # Create dummy records
            record = AppointmentAnalytics(
                date=d,
                hospital_id=None,
                total_bookings=10 + (i % 5),
                confirmed=8 + (i % 3),
                completed=5 + (i % 2),
                cancelled=1,
                high_urgency=2,
                medium_urgency=5,
                low_urgency=3
            )
            db.session.add(record)
        
        db.session.commit()
        print("✅ Seeded 30 days of analytics trends.")

if __name__ == "__main__":
    seed_analytics()
