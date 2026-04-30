/**
 * AppointmentManager.jsx — M3
 * Full appointment table with filters, status transitions (approve/reject/complete),
 * and paginated results.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAdminAuth } from '../../context/AdminAuthContext';

const STATUS_META = {
  PENDING:   { fg: '#f59e0b', bg: '#f59e0b18', label: 'Pending',   actions: ['CONFIRMED', 'CANCELLED'] },
  CONFIRMED: { fg: '#10b981', bg: '#10b98118', label: 'Confirmed', actions: ['COMPLETED', 'CANCELLED', 'NO_SHOW'] },
  COMPLETED: { fg: '#6366f1', bg: '#6366f118', label: 'Completed', actions: [] },
  CANCELLED: { fg: '#ef4444', bg: '#ef444418', label: 'Cancelled', actions: [] },
  NO_SHOW:   { fg: '#94a3b8', bg: '#94a3b818', label: 'No Show',   actions: [] },
};

const ACTION_LABELS = {
  CONFIRMED:  { label: '✅ Confirm',   color: '#10b981' },
  CANCELLED:  { label: '❌ Cancel',    color: '#ef4444' },
  COMPLETED:  { label: '🏁 Complete',  color: '#6366f1' },
  NO_SHOW:    { label: '👻 No Show',   color: '#94a3b8' },
};

const ALL_STATUSES = ['', 'PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED', 'NO_SHOW'];

export default function AppointmentManager() {
  const { adminFetch, isPlatformAdmin } = useAdminAuth();

  const [appointments, setAppointments] = useState([]);
  const [pagination, setPagination]     = useState({ page: 1, total: 0, pages: 1, per_page: 20 });
  const [filters, setFilters]           = useState({ status: '', urgency: '', date_from: '', date_to: '' });
  const [loading, setLoading]           = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [selectedApt, setSelectedApt]   = useState(null);
  const [toast, setToast]               = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchAppointments = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, per_page: 20 });
      if (filters.status)    params.append('status',    filters.status);
      if (filters.urgency)   params.append('urgency',   filters.urgency);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to)   params.append('date_to',   filters.date_to);

      const data = await adminFetch(`/appointments?${params}`);
      setAppointments(data.appointments || []);
      setPagination(data.pagination || { page: 1, total: 0, pages: 1, per_page: 20 });
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }, [adminFetch, filters]);

  useEffect(() => { fetchAppointments(1); }, [filters]);

  const updateStatus = async (aptId, newStatus) => {
    setActionLoading(aptId + newStatus);
    try {
      await adminFetch(`/appointments/${aptId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: newStatus }),
      });
      showToast(`Appointment ${newStatus.toLowerCase()} successfully`);
      fetchAppointments(pagination.page);
      setSelectedApt(null);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div style={s.wrap}>
      {/* Toast */}
      {toast && (
        <div style={{ ...s.toast, background: toast.type === 'error' ? '#ef444422' : '#10b98122', borderColor: toast.type === 'error' ? '#ef4444' : '#10b981' }}>
          {toast.type === 'error' ? '❌' : '✅'} {toast.msg}
        </div>
      )}

      {/* Filters */}
      <div style={s.filterRow}>
        <select style={s.select} value={filters.status} onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}>
          {ALL_STATUSES.map(s => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
        </select>

        <select style={s.select} value={filters.urgency} onChange={e => setFilters(f => ({ ...f, urgency: e.target.value }))}>
          <option value="">All Urgency</option>
          {['HIGH', 'MEDIUM', 'LOW'].map(u => <option key={u}>{u}</option>)}
        </select>

        <input type="date" style={s.select} value={filters.date_from}
          onChange={e => setFilters(f => ({ ...f, date_from: e.target.value }))} placeholder="From date" />
        <input type="date" style={s.select} value={filters.date_to}
          onChange={e => setFilters(f => ({ ...f, date_to: e.target.value }))} placeholder="To date" />

        <button style={s.resetBtn} onClick={() => setFilters({ status: '', urgency: '', date_from: '', date_to: '' })}>
          ↺ Reset
        </button>

        <span style={s.totalBadge}>{pagination.total} appointments</span>
      </div>

      {/* Table */}
      {loading
        ? <div style={s.loadingRow}>Loading appointments…</div>
        : (
          <div style={s.tableWrap}>
            <table style={s.table}>
              <thead>
                <tr>
                  {['Patient', 'Specialty', 'Hospital', 'Date & Time', 'Urgency', 'Status', 'Actions'].map(h => (
                    <th key={h} style={s.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {appointments.length === 0
                  ? <tr><td colSpan={7} style={s.emptyCell}>No appointments found.</td></tr>
                  : appointments.map(apt => {
                    const meta = STATUS_META[apt.status] || STATUS_META.PENDING;
                    return (
                      <tr key={apt.id} style={s.tr} onClick={() => setSelectedApt(apt)}>
                        <td style={s.td}>
                          <strong style={{ color: '#f0fdf4' }}>{apt.patient_name || '—'}</strong>
                          <br /><small style={{ color: '#94a3b8', fontSize: 11 }}>{apt.patient_email || apt.user_id?.slice(0, 12)}</small>
                        </td>
                        <td style={s.td}>{apt.specialty || '—'}</td>
                        <td style={s.td}>{apt.hospital_name || `#${apt.hospital_id}`}</td>
                        <td style={s.td}>
                          <div style={{ fontSize: 13 }}>{apt.appointment_date?.slice(0,10) || '—'}</div>
                          <div style={{ fontSize: 11, color: '#94a3b8' }}>{apt.appointment_time || ''}</div>
                        </td>
                        <td style={s.td}>
                          {apt.urgency_level && (
                            <span style={{ ...s.urgencyPill, ...(apt.urgency_level === 'HIGH' ? { background: '#ef444420', color: '#ef4444' } : apt.urgency_level === 'MEDIUM' ? { background: '#f59e0b20', color: '#f59e0b' } : { background: '#10b98120', color: '#10b981' }) }}>
                              {apt.urgency_level}
                            </span>
                          )}
                        </td>
                        <td style={s.td}>
                          <span style={{ ...s.statusPill, background: meta.bg, color: meta.fg }}>
                            {meta.label}
                          </span>
                        </td>
                        <td style={s.td} onClick={e => e.stopPropagation()}>
                          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                            {meta.actions.map(action => {
                              const am = ACTION_LABELS[action];
                              const isLoading = actionLoading === apt.id + action;
                              return (
                                <button
                                  key={action}
                                  onClick={() => updateStatus(apt.id, action)}
                                  disabled={!!actionLoading}
                                  style={{ ...s.actionBtn, borderColor: am.color + '44', color: am.color, background: am.color + '11' }}
                                >
                                  {isLoading ? '…' : am.label}
                                </button>
                              );
                            })}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                }
              </tbody>
            </table>
          </div>
        )
      }

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div style={s.pagination}>
          {Array.from({ length: pagination.pages }, (_, i) => i + 1).map(p => (
            <button
              key={p}
              onClick={() => fetchAppointments(p)}
              style={{ ...s.pageBtn, ...(p === pagination.page ? s.pageBtnActive : {}) }}
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Detail modal */}
      {selectedApt && (
        <div style={s.modalOverlay} onClick={() => setSelectedApt(null)}>
          <div style={s.modal} onClick={e => e.stopPropagation()}>
            <h3 style={s.modalTitle}>📅 Appointment Details</h3>
            <div style={s.detailGrid}>
              {[
                ['ID',         selectedApt.id?.slice(0, 16) + '…'],
                ['Patient',    selectedApt.patient_name || '—'],
                ['Phone',      selectedApt.patient_phone || '—'],
                ['Email',      selectedApt.patient_email || '—'],
                ['Hospital',   selectedApt.hospital_name || `#${selectedApt.hospital_id}`],
                ['Doctor',     selectedApt.doctor_name || '—'],
                ['Specialty',  selectedApt.specialty || '—'],
                ['Date',       selectedApt.appointment_date?.slice(0, 10) || '—'],
                ['Time',       selectedApt.appointment_time || '—'],
                ['Urgency',    selectedApt.urgency_level || '—'],
                ['Status',     selectedApt.status],
                ['Reason',     selectedApt.reason || '—'],
                ['Notes',      selectedApt.notes || '—'],
                ['Created',    selectedApt.created_at?.slice(0, 19)?.replace('T', ' ') || '—'],
              ].map(([k, v]) => (
                <React.Fragment key={k}>
                  <span style={s.detailKey}>{k}</span>
                  <span style={s.detailVal}>{v}</span>
                </React.Fragment>
              ))}
            </div>
            <button onClick={() => setSelectedApt(null)} style={s.closeBtn}>Close ✕</button>
          </div>
        </div>
      )}
    </div>
  );
}

const s = {
  wrap: { display: 'flex', flexDirection: 'column', gap: 16, position: 'relative' },
  toast: { position: 'fixed', top: 20, right: 20, zIndex: 999, padding: '12px 20px', borderRadius: 10, border: '1px solid', fontSize: 14, color: '#f0fdf4', backdropFilter: 'blur(10px)' },
  filterRow: { display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' },
  select: { padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(16,185,129,.25)', background: 'rgba(255,255,255,.06)', color: '#f0fdf4', fontSize: 13, outline: 'none', fontFamily: 'Inter, sans-serif' },
  resetBtn: { padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,.15)', background: 'transparent', color: 'rgba(240,253,244,.6)', cursor: 'pointer', fontSize: 13 },
  totalBadge: { marginLeft: 'auto', fontSize: 12, color: '#10b981', fontWeight: 600 },
  tableWrap: { overflowX: 'auto', borderRadius: 12, border: '1px solid rgba(16,185,129,.15)' },
  table: { width: '100%', borderCollapse: 'collapse', minWidth: 900 },
  th: { padding: '12px 14px', fontSize: 11, fontWeight: 600, color: 'rgba(240,253,244,.4)', textAlign: 'left', textTransform: 'uppercase', letterSpacing: .5, background: 'rgba(255,255,255,.03)', borderBottom: '1px solid rgba(255,255,255,.06)' },
  tr: { borderBottom: '1px solid rgba(255,255,255,.04)', cursor: 'pointer', transition: 'background .15s' },
  td: { padding: '12px 14px', fontSize: 13, color: 'rgba(240,253,244,.8)', verticalAlign: 'middle' },
  emptyCell: { padding: 48, textAlign: 'center', color: 'rgba(240,253,244,.3)', fontSize: 14 },
  loadingRow: { padding: 48, textAlign: 'center', color: 'rgba(240,253,244,.4)', fontSize: 14 },
  statusPill: { fontSize: 11, padding: '3px 10px', borderRadius: 20, fontWeight: 600, display: 'inline-block' },
  urgencyPill: { fontSize: 11, padding: '3px 10px', borderRadius: 20, fontWeight: 700, display: 'inline-block' },
  actionBtn: { padding: '4px 8px', borderRadius: 6, border: '1px solid', cursor: 'pointer', fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap', transition: 'opacity .15s' },
  pagination: { display: 'flex', gap: 6, justifyContent: 'center', flexWrap: 'wrap' },
  pageBtn: { padding: '6px 12px', borderRadius: 6, border: '1px solid rgba(255,255,255,.15)', background: 'transparent', color: 'rgba(240,253,244,.6)', cursor: 'pointer', fontSize: 13 },
  pageBtnActive: { background: 'rgba(16,185,129,.2)', borderColor: '#10b981', color: '#10b981' },
  modalOverlay: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,.7)', backdropFilter: 'blur(4px)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 },
  modal: { background: '#0d1f2d', border: '1px solid rgba(16,185,129,.3)', borderRadius: 16, padding: 32, maxWidth: 520, width: '100%', maxHeight: '80vh', overflowY: 'auto' },
  modalTitle: { fontSize: 18, fontWeight: 700, color: '#f0fdf4', marginBottom: 20 },
  detailGrid: { display: 'grid', gridTemplateColumns: '120px 1fr', gap: '10px 16px', marginBottom: 24 },
  detailKey: { fontSize: 12, color: 'rgba(240,253,244,.4)', fontWeight: 600 },
  detailVal: { fontSize: 13, color: '#f0fdf4', wordBreak: 'break-all' },
  closeBtn: { padding: '10px 24px', borderRadius: 10, border: '1px solid rgba(255,255,255,.15)', background: 'transparent', color: 'rgba(240,253,244,.7)', cursor: 'pointer', fontSize: 14, width: '100%' },
};
