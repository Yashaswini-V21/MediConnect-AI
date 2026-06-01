import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity, Heart, Calendar, Zap, TrendingUp,
  RefreshCw, Info, ChevronRight, Award
} from 'lucide-react';
import api from '../services/api';

// ──────────────────────────────────────────────
// Circular Score Gauge (pure SVG)
// ──────────────────────────────────────────────
function ScoreGauge({ score, color, label }) {
  const r    = 88;
  const circ = 2 * Math.PI * r;
  const [displayScore, setDisplayScore] = useState(0);
  const [strokeDash, setStrokeDash]     = useState(circ);

  useEffect(() => {
    let frame;
    let current = 0;
    const target = score;
    const step   = () => {
      current = Math.min(current + 2, target);
      setDisplayScore(current);
      setStrokeDash(circ - (circ * current) / 100);
      if (current < target) frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [score, circ]);

  return (
    <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width={220} height={220} style={{ transform: 'rotate(-90deg)' }}>
        {/* Track */}
        <circle
          cx={110} cy={110} r={r}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={14}
        />
        {/* Progress */}
        <circle
          cx={110} cy={110} r={r}
          fill="none"
          stroke={color}
          strokeWidth={14}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={strokeDash}
          style={{ transition: 'stroke 0.4s ease' }}
        />
      </svg>
      <div style={{
        position: 'absolute',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}>
        <span style={{ fontSize: '3rem', fontWeight: 800, color, lineHeight: 1 }}>
          {displayScore}
        </span>
        <span style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)', marginTop: 4 }}>out of 100</span>
        <span style={{
          marginTop: 8,
          fontSize: '0.95rem',
          fontWeight: 600,
          color,
          background: `${color}22`,
          padding: '3px 12px',
          borderRadius: 20,
        }}>
          {label}
        </span>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// Category Card
// ──────────────────────────────────────────────
function CategoryCard({ icon: Icon, title, score, label, details, accentColor }) {
  const pct = `${score}%`;
  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 16,
      padding: '20px 22px',
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          background: `${accentColor}22`,
          borderRadius: 10,
          padding: 8,
          display: 'flex',
        }}>
          <Icon size={20} color={accentColor} />
        </div>
        <div>
          <div style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.5)', fontWeight: 500 }}>
            {title}
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fff' }}>
            {score}<span style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)' }}>/100</span>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: pct,
          background: `linear-gradient(90deg, ${accentColor}99, ${accentColor})`,
          borderRadius: 4,
          transition: 'width 1s ease',
        }} />
      </div>

      <div style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.45)' }}>{label}</div>

      {details && details.length > 0 && (
        <ul style={{ margin: 0, padding: '0 0 0 16px', listStyle: 'disc' }}>
          {details.map((d, i) => (
            <li key={i} style={{ fontSize: '0.78rem', color: 'rgba(255,255,255,0.4)', marginBottom: 2 }}>
              {d}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────
// Tip Card
// ──────────────────────────────────────────────
function TipCard({ icon, title, text }) {
  return (
    <div style={{
      background: 'rgba(99,102,241,0.08)',
      border: '1px solid rgba(99,102,241,0.18)',
      borderRadius: 14,
      padding: '16px 18px',
      display: 'flex',
      gap: 14,
      alignItems: 'flex-start',
    }}>
      <span style={{ fontSize: '1.6rem', lineHeight: 1.2 }}>{icon}</span>
      <div>
        <div style={{ fontWeight: 600, color: '#a5b4fc', marginBottom: 4, fontSize: '0.9rem' }}>{title}</div>
        <div style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.55)', lineHeight: 1.5 }}>{text}</div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// Lifestyle Input Section
// ──────────────────────────────────────────────
function LifestyleInputs({ values, onChange }) {
  const inputStyle = {
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: 10,
    color: '#fff',
    padding: '10px 14px',
    width: '100%',
    fontSize: '0.9rem',
    outline: 'none',
    boxSizing: 'border-box',
  };
  const labelStyle = {
    fontSize: '0.8rem',
    color: 'rgba(255,255,255,0.5)',
    marginBottom: 6,
    display: 'block',
  };

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: 16,
      padding: '20px 22px',
    }}>
      <div style={{ fontWeight: 600, color: '#a5b4fc', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
        <Info size={16} /> Optional: Enter lifestyle data for a more accurate score
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 14 }}>
        <div>
          <label style={labelStyle}>BMI</label>
          <input
            style={inputStyle}
            type="number"
            placeholder="e.g. 22.5"
            min={10} max={60} step={0.1}
            value={values.bmi}
            onChange={e => onChange('bmi', e.target.value)}
          />
        </div>
        <div>
          <label style={labelStyle}>Sleep hours / night</label>
          <input
            style={inputStyle}
            type="number"
            placeholder="e.g. 7.5"
            min={0} max={24} step={0.5}
            value={values.sleep_hours}
            onChange={e => onChange('sleep_hours', e.target.value)}
          />
        </div>
        <div>
          <label style={labelStyle}>Exercise days / week</label>
          <input
            style={inputStyle}
            type="number"
            placeholder="e.g. 4"
            min={0} max={7} step={1}
            value={values.exercise_days}
            onChange={e => onChange('exercise_days', e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// Main Page
// ──────────────────────────────────────────────
export default function WellnessScore() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const [lifestyle, setLifestyle] = useState({ bmi: '', sleep_hours: '', exercise_days: '' });

  const fetchScore = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (lifestyle.bmi)           params.bmi           = lifestyle.bmi;
      if (lifestyle.sleep_hours)   params.sleep_hours   = lifestyle.sleep_hours;
      if (lifestyle.exercise_days) params.exercise_days = lifestyle.exercise_days;

      const qs  = new URLSearchParams(params).toString();
      const url = `/api/wellness/score${qs ? `?${qs}` : ''}`;
      const res = await api.get(url);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load wellness score. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [lifestyle]);

  useEffect(() => {
    fetchScore();
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const handleLifestyleChange = (key, val) => {
    setLifestyle(prev => ({ ...prev, [key]: val }));
  };

  const categories = data ? [
    {
      icon: Heart,
      title: 'Symptom Health',
      accentColor: '#f87171',
      ...data.categories.symptom_health,
    },
    {
      icon: Calendar,
      title: 'Appointment Regularity',
      accentColor: '#60a5fa',
      ...data.categories.appointment_regularity,
    },
    {
      icon: Zap,
      title: 'Lifestyle',
      accentColor: '#34d399',
      ...data.categories.lifestyle,
    },
  ] : [];

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f0c29 0%, #1a1040 50%, #0f172a 100%)',
      padding: '32px 16px 64px',
      fontFamily: "'Inter', system-ui, sans-serif",
    }}>
      <div style={{ maxWidth: 860, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 10,
            background: 'rgba(99,102,241,0.15)',
            border: '1px solid rgba(99,102,241,0.3)',
            borderRadius: 30, padding: '6px 18px', marginBottom: 16,
          }}>
            <Award size={16} color="#a5b4fc" />
            <span style={{ color: '#a5b4fc', fontSize: '0.85rem', fontWeight: 600 }}>
              AI Wellness Intelligence
            </span>
          </div>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: '#fff', margin: 0, lineHeight: 1.2 }}>
            Your Wellness Score
          </h1>
          <p style={{ color: 'rgba(255,255,255,0.5)', marginTop: 10, fontSize: '0.95rem' }}>
            A personalised health score powered by your symptom history, appointments, and lifestyle.
          </p>
        </div>

        {/* Lifestyle Inputs */}
        <LifestyleInputs values={lifestyle} onChange={handleLifestyleChange} />

        {/* Calculate Button */}
        <div style={{ textAlign: 'center', margin: '20px 0 32px' }}>
          <button
            id="wellness-calculate-btn"
            onClick={fetchScore}
            disabled={loading}
            style={{
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              color: '#fff',
              border: 'none',
              borderRadius: 12,
              padding: '13px 32px',
              fontSize: '0.95rem',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              transition: 'transform 0.15s ease',
            }}
            onMouseEnter={e => { if (!loading) e.currentTarget.style.transform = 'scale(1.03)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; }}
          >
            <RefreshCw size={16} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            {loading ? 'Calculating…' : 'Calculate My Score'}
          </button>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239,68,68,0.12)',
            border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: 12,
            padding: '14px 18px',
            color: '#fca5a5',
            textAlign: 'center',
            marginBottom: 24,
          }}>
            {error}
          </div>
        )}

        {data && (
          <>
            {/* Score Gauge */}
            <div style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 24,
              padding: '36px 24px',
              textAlign: 'center',
              marginBottom: 24,
            }}>
              <ScoreGauge
                score={data.wellness_score}
                color={data.color}
                label={data.label}
              />
              <div style={{
                marginTop: 16,
                fontSize: '0.8rem',
                color: 'rgba(255,255,255,0.35)',
              }}>
                {data.authenticated
                  ? 'Personalised from your health history'
                  : 'Sign in for a personalised score from your history'}
              </div>
            </div>

            {/* Category Breakdown */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: 16,
              marginBottom: 24,
            }}>
              {categories.map((cat, i) => (
                <CategoryCard key={i} {...cat} />
              ))}
            </div>

            {/* Tips */}
            <div style={{ marginBottom: 24 }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                marginBottom: 14,
              }}>
                <TrendingUp size={18} color="#a5b4fc" />
                <span style={{ fontWeight: 700, color: '#fff', fontSize: '1rem' }}>
                  Personalised Health Tips
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {data.tips.map((tip, i) => (
                  <TipCard key={i} {...tip} />
                ))}
              </div>
            </div>

            {/* CTA Banner */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2))',
              border: '1px solid rgba(99,102,241,0.3)',
              borderRadius: 16,
              padding: '20px 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 12,
            }}>
              <div>
                <div style={{ fontWeight: 700, color: '#c7d2fe', marginBottom: 4 }}>
                  Want to improve your score?
                </div>
                <div style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.5)' }}>
                  Check your symptoms early and book a preventive appointment.
                </div>
              </div>
              <a
                href="/appointments"
                style={{
                  background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                  color: '#fff',
                  textDecoration: 'none',
                  borderRadius: 10,
                  padding: '10px 20px',
                  fontWeight: 600,
                  fontSize: '0.88rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  whiteSpace: 'nowrap',
                }}
              >
                Book Appointment <ChevronRight size={15} />
              </a>
            </div>

            <div style={{
              textAlign: 'center',
              marginTop: 20,
              fontSize: '0.75rem',
              color: 'rgba(255,255,255,0.25)',
            }}>
              <Activity size={12} style={{ display: 'inline', marginRight: 4 }} />
              Last updated: {new Date(data.generated_at).toLocaleString()}
            </div>
          </>
        )}
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
