/**
 * AdminOverview.jsx — M3 Dashboard Overview / Home Page
 * Shows KPI cards, quick stats, recent activity.
 */
import React, { useEffect, useState } from 'react';
import { useAdminAuth } from '../../context/AdminAuthContext';

const STATUS_COLORS = {
  PENDING:   { fg: '#f59e0b', bg: '#f59e0b18', label: 'Pending'   },
  CONFIRMED: { fg: '#10b981', bg: '#10b98118', label: 'Confirmed' },
  COMPLETED: { fg: '#6366f1', bg: '#6366f118', label: 'Completed' },
  CANCELLED: { fg: '#ef4444', bg: '#ef444418', label: 'Cancelled' },
  NO_SHOW:   { fg: '#94a3b8', bg: '#94a3b818', label: 'No Show'   },
};

export default function AdminOverview() {
  const { adminFetch, role } = useAdminAuth();
  const [summary, setSummary]   = useState(null);
  const [recent, setRecent]     = useState([]);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      adminFetch('/analytics/summary'),
      adminFetch('/appointments?per_page=5'),
    ]).then(([s, r]) => {
      setSummary(s.summary);
      setRecent(r.appointments || []);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, [adminFetch]);

  if (loading) return <Skeleton />;

  const stats = summary || {};
  const byStatus = stats.by_status || {};

  return (
    <div style={s.wrap}>
      {/* KPI Cards */}
      <div style={s.kpiGrid}>
        <KPICard icon="📅" label="Total Appointments" value={stats.total_appointments ?? 0} color="#10b981" />
        <KPICard icon="⏳" label="Pending"            value={byStatus.PENDING ?? 0}         color="#f59e0b" />
        <KPICard icon="✅" label="Confirmed"           value={byStatus.CONFIRMED ?? 0}       color="#6366f1" />
        <KPICard icon="👨‍⚕️" label="Active Doctors"   value={stats.active_doctors ?? 0}     color="#ec4899" />
        <KPICard icon="🎧" label="Open Tickets"        value={stats.open_support_tickets ?? 0} color="#f87171" />
        <KPICard icon="☀️" label="Today's Appointments" value={stats.today?.total ?? 0}     color="#38bdf8" />
      </div>

      {/* Status breakdown */}
      <div style={s.row}>
        <div style={s.card}>
          <h3 style={s.cardTitle}>📊 Appointment Status Breakdown</h3>
          <div style={s.statusGrid}>
            {Object.entries(byStatus).map(([status, count]) => {
              const meta = STATUS_COLORS[status] || { fg: '#888', bg: '#88888818', label: status };
              const pct = stats.total_appointments ? Math.round((count / stats.total_appointments) * 100) : 0;
              return (
                <div key={status} style={{ ...s.statusChip, background: meta.bg, borderColor: meta.fg + '44' }}>
                  <span style={{ ...s.statusLabel, color: meta.fg }}>{meta.label}</span>
                  <span style={{ ...s.statusCount, color: meta.fg }}>{count}</span>
                  <div style={s.progressBar}>
                    <div style={{ ...s.progressFill, width: `${pct}%`, background: meta.fg }} />
                  </div>
                  <span style={s.statusPct}>{pct}%</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent appointments */}
        <div style={s.card}>
          <h3 style={s.cardTitle}>🕐 Recent Appointments</h3>
          {recent.length === 0
            ? <p style={s.empty}>No appointments yet.</p>
            : (
              <table style={s.table}>
                <thead>
                  <tr>
                    {['Patient', 'Specialty', 'Date', 'Status'].map(h => (
                      <th key={h} style={s.th}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {recent.map(apt => {
                    const meta = STATUS_COLORS[apt.status] || STATUS_COLORS.PENDING;
                    return (
                      <tr key={apt.id} style={s.tr}>
                        <td style={s.td}>{apt.patient_name || apt.user_id?.slice(0,8) || '—'}</td>
                        <td style={s.td}>{apt.specialty || '—'}</td>
                        <td style={s.td}>{apt.appointment_date ? apt.appointment_date.slice(0,10) : '—'}</td>
                        <td style={s.td}>
                          <span style={{ ...s.statusPill, background: meta.bg, color: meta.fg }}>
                            {meta.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )
          }
        </div>
      </div>

      {/* Role info */}
      <div style={s.roleInfo}>
        <span style={s.roleInfoIcon}>ℹ️</span>
        <span style={s.roleInfoText}>
          You are logged in as <strong style={{ color: '#10b981' }}>{role}</strong>.{' '}
          {role === 'HOSPITAL_ADMIN' && 'You see data scoped to your hospital only.'}
          {role === 'PLATFORM_ADMIN' && 'You have full system access across all hospitals.'}
          {role === 'SUPPORT_STAFF'  && 'You can view analytics and manage support tickets.'}
        </span>
      </div>
    </div>
  );
}

function KPICard({ icon, label, value, color }) {
  return (
    <div style={{ ...s.kpiCard, borderColor: color + '33', boxShadow: `0 0 20px ${color}15` }}>
      <span style={s.kpiIcon}>{icon}</span>
      <div>
        <p style={{ ...s.kpiValue, color }}>{value.toLocaleString()}</p>
        <p style={s.kpiLabel}>{label}</p>
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div style={{ padding: 32 }}>
      {[1, 2, 3].map(i => (
        <div key={i} style={{ height: 80, background: 'rgba(255,255,255,.04)', borderRadius: 12, marginBottom: 16, animation: 'pulse 1.5s infinite' }} />
      ))}
      <style>{`@keyframes pulse{0%,100%{opacity:.4}50%{opacity:.8}}`}</style>
    </div>
  );
}

const s = {
  wrap: { display: 'flex', flexDirection: 'column', gap: 24 },
  kpiGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16 },
  kpiCard: {
    background: 'rgba(255,255,255,.04)', border: '1px solid', borderRadius: 14,
    padding: '20px', display: 'flex', alignItems: 'center', gap: 16, transition: 'transform .2s',
  },
  kpiIcon: { fontSize: 32 },
  kpiValue: { fontSize: 28, fontWeight: 700, lineHeight: 1.1 },
  kpiLabel: { fontSize: 12, color: 'rgba(240,253,244,.5)', marginTop: 2 },
  row: { display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: 20 },
  card: { background: 'rgba(255,255,255,.04)', border: '1px solid rgba(16,185,129,.15)', borderRadius: 14, padding: 24 },
  cardTitle: { fontSize: 14, fontWeight: 600, color: 'rgba(240,253,244,.7)', marginBottom: 16 },
  statusGrid: { display: 'flex', flexDirection: 'column', gap: 10 },
  statusChip: {
    display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
    borderRadius: 10, border: '1px solid',
  },
  statusLabel: { fontSize: 12, fontWeight: 600, minWidth: 70 },
  statusCount: { fontSize: 18, fontWeight: 700, minWidth: 30 },
  progressBar: { flex: 1, height: 4, background: 'rgba(255,255,255,.08)', borderRadius: 2, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 2, transition: 'width .5s' },
  statusPct: { fontSize: 11, color: 'rgba(240,253,244,.4)', minWidth: 32, textAlign: 'right' },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { fontSize: 11, fontWeight: 600, color: 'rgba(240,253,244,.4)', padding: '6px 10px', textAlign: 'left', textTransform: 'uppercase', letterSpacing: .5 },
  tr: { borderBottom: '1px solid rgba(255,255,255,.04)' },
  td: { padding: '10px', fontSize: 13, color: 'rgba(240,253,244,.8)' },
  statusPill: { fontSize: 11, padding: '3px 8px', borderRadius: 20, fontWeight: 600 },
  empty: { color: 'rgba(240,253,244,.4)', fontSize: 13, textAlign: 'center', padding: '32px 0' },
  roleInfo: {
    display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px',
    background: 'rgba(16,185,129,.07)', border: '1px solid rgba(16,185,129,.2)', borderRadius: 10,
  },
  roleInfoIcon: { fontSize: 18 },
  roleInfoText: { fontSize: 13, color: 'rgba(240,253,244,.6)' },
};
