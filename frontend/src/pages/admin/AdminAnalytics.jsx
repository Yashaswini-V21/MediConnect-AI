/**
 * AdminAnalytics.jsx — M3
 * Live analytics with Recharts: trends, specialty demand, status pie.
 */
import React, { useState, useEffect } from 'react';
import { useAdminAuth } from '../../context/AdminAuthContext';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const PIE_COLORS = ['#10b981','#f59e0b','#6366f1','#ef4444','#94a3b8'];
const STATUS_LABELS = { PENDING:'Pending', CONFIRMED:'Confirmed', COMPLETED:'Completed', CANCELLED:'Cancelled', NO_SHOW:'No Show' };

export default function AdminAnalytics() {
  const { adminFetch } = useAdminAuth();
  const [days, setDays]       = useState(30);
  const [trends, setTrends]   = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      adminFetch(`/analytics/trends?days=${days}`),
      adminFetch('/analytics/summary'),
    ]).then(([t, s]) => {
      setTrends(t);
      setSummary(s.summary);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, [adminFetch, days]);

  if (loading) return <Skeleton />;

  const daily = trends?.daily_trends || [];
  const specialtyData = Object.entries(trends?.specialty_demand || {}).map(([name, value]) => ({ name, value }));
  const statusPie = Object.entries(summary?.by_status || {}).map(([name, value]) => ({ name: STATUS_LABELS[name] || name, value }));

  const exportCSV = () => {
    const rows = [['Date','Total','Confirmed','Cancelled','Completed']];
    daily.forEach(d => rows.push([d.date, d.total, d.confirmed, d.cancelled, d.completed]));
    const csv = rows.map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mediconnect-analytics-${days}d.csv`;
    a.click();
  };

  return (
    <div style={s.wrap}>
      {/* Controls */}
      <div style={s.header}>
        <div>
          <h3 style={s.title}>📈 Analytics Dashboard</h3>
          <p style={s.sub}>Real-time appointment and demand data</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {[7, 14, 30, 60, 90].map(d => (
            <button key={d} onClick={() => setDays(d)} style={{ ...s.dayBtn, ...(d === days ? s.dayBtnActive : {}) }}>
              {d}d
            </button>
          ))}
          <button onClick={exportCSV} style={s.exportBtn}>⬇ CSV</button>
        </div>
      </div>

      {/* Line chart: Daily trends */}
      <div style={s.chartCard}>
        <h4 style={s.chartTitle}>Daily Appointment Trends (Last {days} days)</h4>
        {daily.length === 0
          ? <p style={s.empty}>No data for this period yet.</p>
          : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.06)" />
                <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={d => d.slice(5)} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#0d1f2d', border: '1px solid rgba(16,185,129,.3)', borderRadius: 8, color: '#f0fdf4' }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="total"     stroke="#10b981" strokeWidth={2} dot={false} name="Total" />
                <Line type="monotone" dataKey="confirmed" stroke="#6366f1" strokeWidth={2} dot={false} name="Confirmed" />
                <Line type="monotone" dataKey="cancelled" stroke="#ef4444" strokeWidth={2} dot={false} name="Cancelled" />
                <Line type="monotone" dataKey="completed" stroke="#f59e0b" strokeWidth={2} dot={false} name="Completed" />
              </LineChart>
            </ResponsiveContainer>
          )
        }
      </div>

      <div style={s.row}>
        {/* Specialty demand bar chart */}
        <div style={s.chartCard}>
          <h4 style={s.chartTitle}>🏥 Specialty Demand</h4>
          {specialtyData.length === 0
            ? <p style={s.empty}>No specialty data yet.</p>
            : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={specialtyData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.06)" />
                  <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} width={110} />
                  <Tooltip contentStyle={{ background: '#0d1f2d', border: '1px solid rgba(16,185,129,.3)', borderRadius: 8, color: '#f0fdf4' }} />
                  <Bar dataKey="value" fill="#10b981" radius={[0, 4, 4, 0]} name="Appointments" />
                </BarChart>
              </ResponsiveContainer>
            )
          }
        </div>

        {/* Status pie chart */}
        <div style={s.chartCard}>
          <h4 style={s.chartTitle}>📊 Status Distribution</h4>
          {statusPie.filter(d => d.value > 0).length === 0
            ? <p style={s.empty}>No status data yet.</p>
            : (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={statusPie.filter(d => d.value > 0)} dataKey="value" nameKey="name"
                    cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}>
                    {statusPie.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#0d1f2d', border: '1px solid rgba(16,185,129,.3)', borderRadius: 8, color: '#f0fdf4' }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            )
          }
        </div>
      </div>

      {/* Summary numbers */}
      <div style={s.summaryRow}>
        {[
          { label: 'Total Appointments', value: summary?.total_appointments ?? 0, color: '#10b981' },
          { label: "Today's Appointments", value: summary?.today?.total ?? 0, color: '#6366f1' },
          { label: 'Pending Today',        value: summary?.today?.pending ?? 0,  color: '#f59e0b' },
          { label: 'Active Doctors',        value: summary?.active_doctors ?? 0,  color: '#ec4899' },
          { label: 'Open Tickets',          value: summary?.open_support_tickets ?? 0, color: '#f87171' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ ...s.summaryCard, borderColor: color + '33' }}>
            <p style={{ ...s.summaryValue, color }}>{value.toLocaleString()}</p>
            <p style={s.summaryLabel}>{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div style={{ padding: 16 }}>
      {[1, 2].map(i => (
        <div key={i} style={{ height: 300, background: 'rgba(255,255,255,.04)', borderRadius: 14, marginBottom: 16, animation: 'pulse 1.5s infinite' }} />
      ))}
      <style>{`@keyframes pulse{0%,100%{opacity:.4}50%{opacity:.8}}`}</style>
    </div>
  );
}

const s = {
  wrap: { display: 'flex', flexDirection: 'column', gap: 20 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 },
  title: { fontSize: 16, fontWeight: 700, color: '#f0fdf4', margin: 0 },
  sub: { fontSize: 12, color: 'rgba(240,253,244,.4)', marginTop: 4 },
  dayBtn: { padding: '6px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,.15)', background: 'transparent', color: 'rgba(240,253,244,.5)', cursor: 'pointer', fontSize: 13, transition: 'all .15s' },
  dayBtnActive: { background: 'rgba(16,185,129,.2)', borderColor: '#10b981', color: '#10b981' },
  exportBtn: { padding: '6px 14px', borderRadius: 8, border: '1px solid rgba(16,185,129,.4)', background: 'rgba(16,185,129,.1)', color: '#10b981', cursor: 'pointer', fontSize: 13, fontWeight: 600 },
  chartCard: { background: 'rgba(255,255,255,.04)', border: '1px solid rgba(16,185,129,.15)', borderRadius: 14, padding: '20px 24px' },
  chartTitle: { fontSize: 14, fontWeight: 600, color: 'rgba(240,253,244,.7)', marginBottom: 16, margin: '0 0 16px' },
  row: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 },
  empty: { color: 'rgba(240,253,244,.3)', fontSize: 13, textAlign: 'center', padding: '40px 0' },
  summaryRow: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 },
  summaryCard: { background: 'rgba(255,255,255,.04)', border: '1px solid', borderRadius: 12, padding: '16px 20px', textAlign: 'center' },
  summaryValue: { fontSize: 28, fontWeight: 700, margin: '0 0 4px' },
  summaryLabel: { fontSize: 11, color: 'rgba(240,253,244,.4)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: .5, margin: 0 },
};
