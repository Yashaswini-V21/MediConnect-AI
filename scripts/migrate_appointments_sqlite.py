#!/usr/bin/env python3
"""Lightweight migration: import appointments.json into SQLite DB without SQLAlchemy.
This avoids importing backend dependencies during migration.
"""
import os
import json
import sqlite3
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_FILE = os.path.join(REPO_ROOT, 'backend', 'data', 'appointments.json')
DB_FILE = os.path.join(REPO_ROOT, 'mediconnect.db')


def ensure_table(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        hospital_id INTEGER NOT NULL,
        doctor_id INTEGER,
        appointment_date TEXT,
        appointment_time TEXT,
        status TEXT,
        urgency_level TEXT,
        specialty TEXT,
        patient_name TEXT,
        patient_phone TEXT,
        patient_email TEXT,
        reason TEXT,
        notes TEXT,
        hospital_name TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')


def to_iso(dt_str):
    try:
        return datetime.fromisoformat(dt_str).isoformat()
    except Exception:
        return None


def main():
    if not os.path.exists(DATA_FILE):
        print('No appointments.json found; nothing to migrate.')
        return

    with open(DATA_FILE, 'r') as f:
        items = json.load(f) or []

    conn = sqlite3.connect(DB_FILE)
    ensure_table(conn)
    cur = conn.cursor()

    inserted = 0
    for it in items:
        aid = it.get('id') or f"apt_{inserted}_{int(datetime.now().timestamp())}"
        user_id = it.get('user_id') or it.get('user') or ''
        hospital_id = int(it.get('hospital_id') or 0)
        appointment_date = to_iso(it.get('date') or '')
        appointment_time = it.get('time')
        status = (it.get('status') or 'PENDING').upper()
        created_at = to_iso(it.get('created_at') or datetime.utcnow().isoformat())
        updated_at = to_iso(it.get('updated_at') or created_at)

        try:
            cur.execute('''INSERT OR IGNORE INTO appointments (
                id, user_id, hospital_id, doctor_id, appointment_date, appointment_time,
                status, urgency_level, specialty, patient_name, patient_phone, patient_email,
                reason, notes, hospital_name, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                aid, user_id, hospital_id, it.get('doctor_id'), appointment_date, appointment_time,
                status, it.get('urgency_level'), it.get('specialty'), it.get('patient_name'),
                it.get('patient_phone'), it.get('patient_email'), it.get('reason'), it.get('notes'),
                it.get('hospital_name'), created_at, updated_at
            ))
            inserted += cur.rowcount
        except Exception as e:
            print('Failed to insert', aid, e)

    conn.commit()
    conn.close()
    print(f'Migrated {inserted} appointments into {DB_FILE}')


if __name__ == '__main__':
    main()
