#!/usr/bin/env python3
"""Migrate appointments from backend/data/appointments.json into the SQL DB.
Run from repository root: `python scripts/migrate_appointments.py`
"""
import os
import sys
import json
from datetime import datetime

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ''))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
# Also ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app import app
from models.admin_model import Appointment, AppointmentStatus
from models.user_model import db


def parse_datetime(date_str, time_str):
    try:
        date_part = datetime.fromisoformat(date_str)
    except Exception:
        return None
    try:
        time_part = datetime.strptime(time_str, '%I:%M %p').time()
    except Exception:
        time_part = None

    return datetime(
        date_part.year, date_part.month, date_part.day,
        time_part.hour if time_part else 0,
        time_part.minute if time_part else 0
    )


def main():
    data_file = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'appointments.json')
    if not os.path.exists(data_file):
        print('No appointments.json found, nothing to migrate.')
        return

    with open(data_file, 'r') as f:
        items = json.load(f) or []

    with app.app_context():
        inserted = 0
        for it in items:
            # Skip if already exists
            if Appointment.query.get(it.get('id')):
                continue

            appt_dt = parse_datetime(it.get('date', ''), it.get('time', ''))
            apt = Appointment(
                id=it.get('id'),
                user_id=it.get('user_id') or it.get('user'),
                hospital_id=int(it.get('hospital_id') or 0),
                hospital_name=it.get('hospital_name',''),
                appointment_date=appt_dt or datetime.utcnow(),
                appointment_time=it.get('time'),
                specialty=it.get('specialty'),
                patient_name=it.get('patient_name'),
                patient_phone=it.get('patient_phone'),
                patient_email=it.get('patient_email'),
                reason=it.get('reason'),
                status=(it.get('status') or 'PENDING').upper(),
            )
            db.session.add(apt)
            inserted += 1

        db.session.commit()
        print(f'Migrated {inserted} appointments into the database')


if __name__ == '__main__':
    main()
