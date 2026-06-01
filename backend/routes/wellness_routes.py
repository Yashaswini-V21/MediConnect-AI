"""
Wellness Score API Routes
Provides a personalised AI-driven wellness score (0-100) based on
symptom history, appointment regularity, and self-reported health factors.
All scoring is local rule-based — no external API required.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from models.user_model import db, SearchHistory
from models.admin_model import Appointment, AppointmentStatus
from utils.auth_middleware import get_authenticated_user_id
import logging

logger = logging.getLogger(__name__)

wellness_bp = Blueprint('wellness', __name__)


# ─────────────────────────────────────────────────────────────
# Scoring Engine (fully local, rule-based)
# ─────────────────────────────────────────────────────────────

URGENCY_SCORE_IMPACT = {
    'HIGH':   -25,
    'MEDIUM': -10,
    'LOW':    -3,
}

SPECIALTY_WEIGHTS = {
    'Cardiology': -8,
    'Neurology':  -6,
    'Emergency Medicine': -10,
    'Pulmonology': -6,
}


def _score_from_symptom_history(history_entries: list) -> dict:
    """Compute a symptom sub-score from recent search history."""
    base = 100
    details = []

    if not history_entries:
        return {
            'score': 100,
            'max': 100,
            'label': 'No recent symptoms recorded',
            'details': [],
        }

    # Only consider last 30 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    recent = [h for h in history_entries
              if h.created_at and h.created_at.replace(tzinfo=timezone.utc) >= cutoff]

    for entry in recent[:5]:  # Cap at last 5 events
        impact = URGENCY_SCORE_IMPACT.get(entry.urgency_level, 0)
        base += impact
        if impact < 0:
            details.append(f"{entry.urgency_level.title()} urgency symptom ({impact} pts)")

    score = max(0, min(100, base))
    return {
        'score': score,
        'max': 100,
        'label': f"{len(recent)} symptom check(s) in past 30 days",
        'details': details,
    }


def _score_from_appointments(appointments: list) -> dict:
    """Reward regular health checkups via completed appointments."""
    if not appointments:
        return {
            'score': 60,
            'max': 100,
            'label': 'No appointments found — schedule a checkup!',
            'details': ['Book a preventive checkup (+40 pts potential)'],
        }

    completed = [a for a in appointments if a.status == AppointmentStatus.COMPLETED]
    recent_completed = [
        a for a in completed
        if a.updated_at and (
            datetime.now(timezone.utc) -
            a.updated_at.replace(tzinfo=timezone.utc)
        ).days <= 90
    ]

    if recent_completed:
        score = 95
        label = f"{len(recent_completed)} checkup(s) completed in last 90 days"
    elif completed:
        score = 75
        label = "Past checkups on record — schedule a new one soon"
    else:
        score = 55
        label = "Pending/cancelled appointments — try to complete your checkup"

    return {
        'score': score,
        'max': 100,
        'label': label,
        'details': [],
    }


def _score_lifestyle(bmi: float | None, sleep_hours: float | None,
                     exercise_days: int | None) -> dict:
    """Score lifestyle factors from optional query params."""
    score = 70  # Neutral baseline when no data provided
    details = []

    if bmi is not None:
        if 18.5 <= bmi < 25:
            score += 15
            details.append("Healthy BMI (+15 pts)")
        elif 25 <= bmi < 30:
            score += 5
            details.append("Slightly elevated BMI (+5 pts)")
        elif bmi < 18.5:
            score -= 5
            details.append("Underweight BMI (-5 pts)")
        else:
            score -= 10
            details.append("High BMI range (-10 pts)")

    if sleep_hours is not None:
        if 7 <= sleep_hours <= 9:
            score += 10
            details.append("Optimal sleep (+10 pts)")
        elif sleep_hours < 6:
            score -= 10
            details.append("Sleep deprivation (-10 pts)")
        else:
            score += 3
            details.append("Adequate sleep (+3 pts)")

    if exercise_days is not None:
        if exercise_days >= 5:
            score += 15
            details.append("Excellent activity level (+15 pts)")
        elif exercise_days >= 3:
            score += 10
            details.append("Good activity level (+10 pts)")
        elif exercise_days >= 1:
            score += 5
            details.append("Some activity (+5 pts)")
        else:
            score -= 5
            details.append("Sedentary lifestyle (-5 pts)")

    score = max(0, min(100, score))
    return {
        'score': score,
        'max': 100,
        'label': "Based on provided lifestyle data",
        'details': details,
    }


def _generate_tips(symptom_score: int, appt_score: int, lifestyle_score: int) -> list:
    """Return top 3 personalised wellness tips based on scores."""
    tips = []

    if symptom_score < 70:
        tips.append({
            'icon': '🩺',
            'title': 'Monitor Your Symptoms',
            'text': 'You have had high-urgency symptoms recently. Consider seeing a specialist soon.',
        })
    else:
        tips.append({
            'icon': '✅',
            'title': 'Symptom Health Looks Good',
            'text': 'No critical symptoms detected recently. Keep monitoring and stay hydrated.',
        })

    if appt_score < 70:
        tips.append({
            'icon': '📅',
            'title': 'Schedule a Checkup',
            'text': 'Regular preventive checkups can catch issues early. Book an appointment today.',
        })
    else:
        tips.append({
            'icon': '🏥',
            'title': 'Keep Up Your Checkups',
            'text': 'Great job staying on top of your appointments! Aim for quarterly reviews.',
        })

    if lifestyle_score < 65:
        tips.append({
            'icon': '🏃',
            'title': 'Boost Your Activity',
            'text': 'Aim for 30 minutes of moderate exercise at least 5 days a week.',
        })
    else:
        tips.append({
            'icon': '🌟',
            'title': 'Excellent Lifestyle Balance',
            'text': 'Your sleep and activity levels look great. Maintain this healthy routine!',
        })

    return tips


def _label_from_score(score: int) -> str:
    if score >= 85:   return 'Excellent'
    if score >= 70:   return 'Good'
    if score >= 55:   return 'Fair'
    if score >= 40:   return 'Needs Attention'
    return 'At Risk'


def _color_from_score(score: int) -> str:
    if score >= 85:   return '#22c55e'   # green
    if score >= 70:   return '#84cc16'   # lime
    if score >= 55:   return '#f59e0b'   # amber
    if score >= 40:   return '#f97316'   # orange
    return '#ef4444'                      # red


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@wellness_bp.route('/score', methods=['GET'])
def get_wellness_score():
    """
    GET /api/wellness/score

    Optional query params:
      bmi=<float>           e.g. 22.5
      sleep_hours=<float>   e.g. 7.5
      exercise_days=<int>   e.g. 4   (days/week)

    Returns a wellness score 0–100 with category breakdown and tips.
    If the user is authenticated, pulls real symptom + appointment history.
    Works for anonymous users too (lifestyle-only scoring).
    """
    try:
        # Parse optional lifestyle inputs
        bmi           = None
        sleep_hours   = None
        exercise_days = None

        try:
            if request.args.get('bmi'):
                bmi = float(request.args['bmi'])
        except ValueError:
            pass
        try:
            if request.args.get('sleep_hours'):
                sleep_hours = float(request.args['sleep_hours'])
        except ValueError:
            pass
        try:
            if request.args.get('exercise_days'):
                exercise_days = int(request.args['exercise_days'])
        except ValueError:
            pass

        # Try to get authenticated user (optional — works for guests too)
        user_id = get_authenticated_user_id(optional=True)

        # Pull DB data if logged in
        symptom_entries  = []
        appt_entries     = []
        if user_id:
            symptom_entries = (
                SearchHistory.query
                .filter_by(user_id=user_id)
                .order_by(SearchHistory.created_at.desc())
                .limit(20)
                .all()
            )
            appt_entries = (
                Appointment.query
                .filter_by(user_id=str(user_id))
                .order_by(Appointment.created_at.desc())
                .limit(20)
                .all()
            )

        # Score each category
        symptom_result  = _score_from_symptom_history(symptom_entries)
        appt_result     = _score_from_appointments(appt_entries)
        lifestyle_result = _score_lifestyle(bmi, sleep_hours, exercise_days)

        # Weighted overall score
        # Symptoms: 35%, Appointments: 25%, Lifestyle: 40%
        overall = round(
            (symptom_result['score']  * 0.35) +
            (appt_result['score']     * 0.25) +
            (lifestyle_result['score'] * 0.40)
        )

        tips = _generate_tips(
            symptom_result['score'],
            appt_result['score'],
            lifestyle_result['score'],
        )

        return jsonify({
            'success': True,
            'wellness_score': overall,
            'label': _label_from_score(overall),
            'color': _color_from_score(overall),
            'categories': {
                'symptom_health': symptom_result,
                'appointment_regularity': appt_result,
                'lifestyle': lifestyle_result,
            },
            'tips': tips,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'authenticated': user_id is not None,
        }), 200

    except Exception as exc:
        logger.error(f"Wellness score error: {exc}", exc_info=True)
        return jsonify({'success': False, 'error': str(exc)}), 500


@wellness_bp.route('/history', methods=['GET'])
def get_wellness_history():
    """
    GET /api/wellness/history

    Returns last 7 days of symptom urgency data for trend charting.
    Requires authentication.
    """
    try:
        user_id = get_authenticated_user_id(optional=False)
    except PermissionError:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        entries = (
            SearchHistory.query
            .filter_by(user_id=user_id)
            .filter(SearchHistory.created_at >= cutoff)
            .order_by(SearchHistory.created_at.asc())
            .all()
        )

        history = [
            {
                'date': e.created_at.date().isoformat() if e.created_at else None,
                'urgency': e.urgency_level,
                'specialties': e.specialties,
            }
            for e in entries
        ]

        return jsonify({'success': True, 'history': history}), 200

    except Exception as exc:
        logger.error(f"Wellness history error: {exc}", exc_info=True)
        return jsonify({'success': False, 'error': str(exc)}), 500
