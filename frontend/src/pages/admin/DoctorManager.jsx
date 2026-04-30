/**
 * DoctorManager.jsx — M3
 * Add / edit / deactivate doctors with specialty and availability slots.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useAdminAuth } from '../../context/AdminAuthContext';

const SPECIALTIES = [
  'Cardiology','Neurology','Orthopedics','Pediatrics','Dermatology',
  'Gastroenterology','Oncology','Ophthalmology','Psychiatry','General Medicine',
  'Emergency Medicine','ENT','Radiology','Urology','Gynecology',
];
const DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
const TIME_SLOTS = ['08:00','08:30','09:00','09:30','10:00','10:30','11:00','11:30',
  '12:00','14:00','14:30','15:00','15:30','16:00','16:30','17:00','17:30'];

const EMPTY_FORM = {
  name: '', specialty: SPECIALTIES[0], degree: '', experience_years: 0,
  max_daily_bookings: 20, is_active: true, hospital_id: '', available_slots: {},
};

export default function DoctorManager() {
  const { adminFetch, isPlatformAdmin, hospitalId } = useAdminAuth();
  const [doctors, setDoctors]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm]         = useState(EMPTY_FORM);
  const [editId, setEditId]     = useState(null);
  const [toast, setToast]       = useState(null);
  const [saving, setSaving]     = useState(false);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const loadDoctors = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminFetch('/doctors?active_only=false');
      setDoctors(data.doctors || []);
    } catch (e) { showToast(e.message, 'error'); }
    finally { setLoading(false); }
  }, [adminFetch]);

  useEffect(() => { loadDoctors(); }, [loadDoctors]);

  const openAdd = () => {
    setForm({ ...EMPTY_FORM, hospital_id: hospitalId || '' });
    setEditId(null);
    setShowForm(true);
  };

  const openEdit = (doctor) => {
    setForm({ ...doctor });
    setEditId(doctor.id);
    setShowForm(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { showToast('Doctor name is required', 'error'); return; }
    setSaving(true);
    try {
      if (editId) {
        await adminFetch(`/doctors/${editId}`, { method: 'PUT', body: JSON.stringify(form) });
        showToast('Doctor updated successfully');
      } else {
        await adminFetch('/doctors', { method: 'POST', body: JSON.stringify(form) });
        showToast('Doctor added successfully');
      }
      setShowForm(false);
      loadDoctors();
    } catch (e) { showToast(e.message, 'error'); }
    finally { setSaving(false); }
  };

  const handleDeactivate = async (id) => {
    if (!window.confirm('Deactivate this doctor?')) return;
    try {
      await adminFetch(`/doctors/${id}`, { method: 'DELETE' });
      showToast('Doctor deactivated');
      loadDoctors();
    } catch (e) { showToast(e.message, 'error'); }
  };

  const toggleSlot = (day, time) => {
    setForm(f => {
      const slots = { ...(f.available_slots || {}) };
      if (!slots[day]) slots[day] = [];
      if (slots[day].includes(time)) slots[day] = slots[day].filter(t => t !== time);
      else slots[day] = [...slots[day], time].sort();
      return { ...f, available_slots: slots };
    });
  };

  return (
    <div style={s.wrap}>
      {toast && (
        <div style={{ ...s.toast, background: toast.type === 'error' ? '#ef444422' : '#10b98122', borderColor: toast.type === 'error' ? '#ef4444' : '#10b981' }}>
          {toast.type === 'error' ? '❌' : '✅'} {toast.msg}
        </div>
      )}

      {/* Header */}
      <div style={s.header}>
        <div>
          <h3 style={s.title}>Doctor Management</h3>
          <p style={s.sub}>{doctors.length} doctors registered</p>
        </div>
        <button style={s.addBtn} onClick={openAdd}>+ Add Doctor</button>
      </div>

      {/* Doctor grid */}
      {loading
        ? <p style={s.loading}>Loading doctors…</p>
        : (
          <div style={s.grid}>
            {doctors.length === 0
              ? <p style={s.empty}>No doctors yet. Add one to get started.</p>
              : doctors.map(doc => (
                <div key={doc.id} style={{ ...s.card, opacity: doc.is_active ? 1 : 0.5 }}>
                  <div style={s.cardTop}>
                    <span style={s.docAvatar}>{doc.name.charAt(0).toUpperCase()}</span>
                    <div style={{ flex: 1 }}>
                      <p style={s.docName}>Dr. {doc.name}</p>
                      <p style={s.docSpec}>{doc.specialty}</p>
                    </div>
                    {!doc.is_active && <span style={s.inactiveBadge}>Inactive</span>}
                  </div>
                  <div style={s.cardMeta}>
                    <span>🎓 {doc.degree || 'MBBS'}</span>
                    <span>📅 {doc.experience_years}yr exp.</span>
                    <span>🏥 Hospital #{doc.hospital_id}</span>
                  </div>
                  <div style={s.cardActions}>
                    <button style={s.editBtn} onClick={() => openEdit(doc)}>✏️ Edit</button>
                    {doc.is_active && (
                      <button style={s.deactBtn} onClick={() => handleDeactivate(doc.id)}>🚫 Deactivate</button>
                    )}
                  </div>
                </div>
              ))
            }
          </div>
        )
      }

      {/* Add/Edit Form Modal */}
      {showForm && (
        <div style={s.overlay} onClick={() => setShowForm(false)}>
          <div style={s.modal} onClick={e => e.stopPropagation()}>
            <h3 style={s.modalTitle}>{editId ? '✏️ Edit Doctor' : '➕ Add Doctor'}</h3>
            <form onSubmit={handleSave} style={s.form}>
              <div style={s.formRow}>
                <div style={s.formGroup}>
                  <label style={s.label}>Full Name *</label>
                  <input style={s.input} value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Dr. Name" />
                </div>
                <div style={s.formGroup}>
                  <label style={s.label}>Specialty *</label>
                  <select style={s.input} value={form.specialty} onChange={e => setForm(f => ({ ...f, specialty: e.target.value }))}>
                    {SPECIALTIES.map(sp => <option key={sp}>{sp}</option>)}
                  </select>
                </div>
              </div>
              <div style={s.formRow}>
                <div style={s.formGroup}>
                  <label style={s.label}>Degree</label>
                  <input style={s.input} value={form.degree} onChange={e => setForm(f => ({ ...f, degree: e.target.value }))} placeholder="MBBS, MD, DM…" />
                </div>
                <div style={s.formGroup}>
                  <label style={s.label}>Experience (years)</label>
                  <input style={s.input} type="number" min={0} value={form.experience_years} onChange={e => setForm(f => ({ ...f, experience_years: Number(e.target.value) }))} />
                </div>
              </div>
              <div style={s.formRow}>
                <div style={s.formGroup}>
                  <label style={s.label}>Max Daily Bookings</label>
                  <input style={s.input} type="number" min={1} value={form.max_daily_bookings} onChange={e => setForm(f => ({ ...f, max_daily_bookings: Number(e.target.value) }))} />
                </div>
                {isPlatformAdmin && (
                  <div style={s.formGroup}>
                    <label style={s.label}>Hospital ID *</label>
                    <input style={s.input} type="number" value={form.hospital_id} onChange={e => setForm(f => ({ ...f, hospital_id: Number(e.target.value) }))} />
                  </div>
                )}
              </div>

              {/* Availability slots */}
              <div style={s.formGroup}>
                <label style={s.label}>Availability Slots</label>
                <div style={s.slotsGrid}>
                  {DAYS.map(day => (
                    <div key={day} style={s.dayCol}>
                      <p style={s.dayLabel}>{day}</p>
                      {TIME_SLOTS.map(time => {
                        const selected = (form.available_slots?.[day] || []).includes(time);
                        return (
                          <button
                            key={time} type="button"
                            onClick={() => toggleSlot(day, time)}
                            style={{ ...s.slotBtn, ...(selected ? s.slotBtnActive : {}) }}
                          >
                            {time}
                          </button>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button type="button" onClick={() => setShowForm(false)} style={s.cancelBtn}>Cancel</button>
                <button type="submit" style={s.saveBtn} disabled={saving}>
                  {saving ? 'Saving…' : (editId ? '✅ Update Doctor' : '✅ Add Doctor')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const s = {
  wrap: { display: 'flex', flexDirection: 'column', gap: 20, position: 'relative' },
  toast: { position: 'fixed', top: 20, right: 20, zIndex: 999, padding: '12px 20px', borderRadius: 10, border: '1px solid', fontSize: 14, color: '#f0fdf4', backdropFilter: 'blur(10px)' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 16, fontWeight: 700, color: '#f0fdf4', margin: 0 },
  sub: { fontSize: 12, color: 'rgba(240,253,244,.4)', marginTop: 4 },
  addBtn: { padding: '10px 20px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#10b981,#059669)', color: '#fff', fontWeight: 600, fontSize: 14, cursor: 'pointer' },
  loading: { color: 'rgba(240,253,244,.4)', textAlign: 'center', padding: 48 },
  empty: { color: 'rgba(240,253,244,.3)', textAlign: 'center', padding: 48, fontSize: 14 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 },
  card: { background: 'rgba(255,255,255,.04)', border: '1px solid rgba(16,185,129,.15)', borderRadius: 14, padding: 20, transition: 'all .2s' },
  cardTop: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 },
  docAvatar: { width: 44, height: 44, borderRadius: '50%', background: 'linear-gradient(135deg,#10b981,#059669)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 700, color: '#fff', flexShrink: 0 },
  docName: { fontSize: 15, fontWeight: 600, color: '#f0fdf4', margin: 0 },
  docSpec: { fontSize: 12, color: '#10b981', margin: '2px 0 0' },
  inactiveBadge: { fontSize: 10, padding: '2px 8px', background: '#ef444422', color: '#ef4444', borderRadius: 20, fontWeight: 600 },
  cardMeta: { display: 'flex', gap: 8, fontSize: 11, color: 'rgba(240,253,244,.5)', flexWrap: 'wrap', marginBottom: 14 },
  cardActions: { display: 'flex', gap: 8 },
  editBtn: { flex: 1, padding: '8px', borderRadius: 8, border: '1px solid rgba(99,102,241,.4)', background: 'rgba(99,102,241,.1)', color: '#a5b4fc', cursor: 'pointer', fontSize: 12, fontWeight: 600 },
  deactBtn: { flex: 1, padding: '8px', borderRadius: 8, border: '1px solid rgba(239,68,68,.3)', background: 'rgba(239,68,68,.08)', color: '#f87171', cursor: 'pointer', fontSize: 12, fontWeight: 600 },
  overlay: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,.75)', backdropFilter: 'blur(4px)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 },
  modal: { background: '#0a1628', border: '1px solid rgba(16,185,129,.3)', borderRadius: 16, padding: 32, maxWidth: 720, width: '100%', maxHeight: '90vh', overflowY: 'auto' },
  modalTitle: { fontSize: 18, fontWeight: 700, color: '#f0fdf4', marginBottom: 24 },
  form: { display: 'flex', flexDirection: 'column', gap: 16 },
  formRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  formGroup: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: 12, color: 'rgba(240,253,244,.5)', fontWeight: 600 },
  input: { padding: '10px 12px', borderRadius: 8, border: '1px solid rgba(16,185,129,.25)', background: 'rgba(255,255,255,.06)', color: '#f0fdf4', fontSize: 14, fontFamily: 'Inter, sans-serif', outline: 'none' },
  slotsGrid: { display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 8 },
  dayCol: { display: 'flex', flexDirection: 'column', gap: 4, minWidth: 60 },
  dayLabel: { fontSize: 11, fontWeight: 700, color: '#10b981', textAlign: 'center', margin: '0 0 4px' },
  slotBtn: { padding: '3px 4px', borderRadius: 4, border: '1px solid rgba(255,255,255,.1)', background: 'transparent', color: 'rgba(240,253,244,.4)', fontSize: 10, cursor: 'pointer', whiteSpace: 'nowrap', transition: 'all .1s' },
  slotBtnActive: { background: 'rgba(16,185,129,.2)', borderColor: '#10b981', color: '#10b981' },
  cancelBtn: { padding: '10px 20px', borderRadius: 10, border: '1px solid rgba(255,255,255,.15)', background: 'transparent', color: 'rgba(240,253,244,.6)', cursor: 'pointer', fontSize: 14 },
  saveBtn: { padding: '10px 24px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg,#10b981,#059669)', color: '#fff', fontWeight: 600, fontSize: 14, cursor: 'pointer' },
};
