/**
 * AdminLogin.jsx — M3 Admin Login Page
 * Premium dark glassmorphism design.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAdminAuth } from '../../context/AdminAuthContext';

const ROLE_DEMO_ACCOUNTS = [
  { email: 'platform@mediconnect.ai', role: 'Platform Admin',  icon: '🌐', color: '#6366f1' },
  { email: 'hospital@mediconnect.ai',  role: 'Hospital Admin',  icon: '🏥', color: '#10b981' },
  { email: 'support@mediconnect.ai',   role: 'Support Staff',   icon: '🎧', color: '#f59e0b' },
];

export default function AdminLogin() {
  const { login, isAuthenticated } = useAdminAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/admin/dashboard';

  const [email, setEmail]     = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');

  useEffect(() => {
    if (isAuthenticated) navigate(from, { replace: true });
  }, [isAuthenticated, navigate, from]);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!email.trim()) { setError('Please enter admin email'); return; }
    setLoading(true);
    setError('');
    const result = await login(email.trim().toLowerCase());
    setLoading(false);
    if (!result.success) setError(result.error || 'Login failed');
  };

  const handleQuickLogin = async (demoEmail) => {
    setEmail(demoEmail);
    setLoading(true);
    setError('');
    const result = await login(demoEmail);
    setLoading(false);
    if (!result.success) setError(result.error || 'Login failed');
  };

  return (
    <div style={styles.root}>
      {/* Animated background */}
      <div style={styles.bg} />
      <div style={styles.grid} />

      <div style={styles.card}>
        {/* Logo */}
        <div style={styles.logoWrap}>
          <span style={styles.logo}>🏥</span>
          <div>
            <h1 style={styles.brand}>MediConnect</h1>
            <p style={styles.brandSub}>Admin Portal · M3</p>
          </div>
        </div>

        <p style={styles.tagline}>Multi-tenant Healthcare SaaS Administration</p>

        {/* Quick demo access */}
        <div style={styles.demoSection}>
          <p style={styles.demoLabel}>Quick Demo Access</p>
          <div style={styles.demoGrid}>
            {ROLE_DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                onClick={() => handleQuickLogin(acc.email)}
                style={{ ...styles.demoBtn, borderColor: acc.color + '44', background: acc.color + '11' }}
                disabled={loading}
              >
                <span style={styles.demoIcon}>{acc.icon}</span>
                <span style={{ ...styles.demoRole, color: acc.color }}>{acc.role}</span>
                <span style={styles.demoEmail}>{acc.email}</span>
              </button>
            ))}
          </div>
        </div>

        <div style={styles.divider}><span style={styles.dividerText}>or enter email manually</span></div>

        {/* Manual login form */}
        <form onSubmit={handleLogin} style={styles.form}>
          <div style={styles.inputWrap}>
            <span style={styles.inputIcon}>📧</span>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="admin@mediconnect.ai"
              style={styles.input}
              autoComplete="email"
            />
          </div>

          {error && <p style={styles.error}>{error}</p>}

          <button type="submit" style={styles.submitBtn} disabled={loading}>
            {loading
              ? <><span style={styles.spinner} /> Authenticating…</>
              : '🔐 Admin Sign In'
            }
          </button>
        </form>

        <p style={styles.hint}>
          Token is auto-injected in development mode.<br />
          Set <code style={styles.code}>REACT_APP_ADMIN_TOKEN</code> in production.
        </p>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * { box-sizing: border-box; }
        @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100%{opacity:.4} 50%{opacity:.8} }
      `}</style>
    </div>
  );
}

const styles = {
  root: {
    minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
    background: '#060d1a', fontFamily: "'Inter', sans-serif", padding: 24, position: 'relative',
    overflow: 'hidden',
  },
  bg: {
    position: 'fixed', inset: 0,
    background: 'radial-gradient(ellipse at 20% 50%, #0d2a1a44 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, #1a1a6644 0%, transparent 60%)',
    pointerEvents: 'none',
  },
  grid: {
    position: 'fixed', inset: 0,
    backgroundImage: 'linear-gradient(rgba(16,185,129,.04) 1px, transparent 1px), linear-gradient(90deg, rgba(16,185,129,.04) 1px, transparent 1px)',
    backgroundSize: '40px 40px', pointerEvents: 'none',
  },
  card: {
    width: '100%', maxWidth: 480, position: 'relative', zIndex: 10,
    background: 'rgba(255,255,255,.04)', backdropFilter: 'blur(20px)',
    border: '1px solid rgba(16,185,129,.2)', borderRadius: 20,
    padding: '40px 36px', boxShadow: '0 24px 64px rgba(0,0,0,.5)',
  },
  logoWrap: { display: 'flex', alignItems: 'center', gap: 14, marginBottom: 8 },
  logo: { fontSize: 40, animation: 'float 3s ease-in-out infinite' },
  brand: { margin: 0, fontSize: 22, fontWeight: 700, color: '#f0fdf4' },
  brandSub: { margin: 0, fontSize: 12, color: '#10b981', fontWeight: 500, letterSpacing: 1 },
  tagline: { color: 'rgba(240,253,244,.5)', fontSize: 13, marginBottom: 28, marginTop: 4 },
  demoSection: { marginBottom: 20 },
  demoLabel: { color: 'rgba(240,253,244,.4)', fontSize: 11, fontWeight: 600, letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 12 },
  demoGrid: { display: 'flex', flexDirection: 'column', gap: 8 },
  demoBtn: {
    display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px',
    border: '1px solid', borderRadius: 10, cursor: 'pointer',
    transition: 'all .2s', textAlign: 'left', width: '100%',
  },
  demoIcon: { fontSize: 20, flexShrink: 0 },
  demoRole: { fontSize: 13, fontWeight: 600, flexShrink: 0, minWidth: 120 },
  demoEmail: { fontSize: 11, color: 'rgba(240,253,244,.5)', fontFamily: 'monospace' },
  divider: { margin: '20px 0', textAlign: 'center', borderTop: '1px solid rgba(255,255,255,.08)', paddingTop: 0, position: 'relative' },
  dividerText: { position: 'relative', top: -10, background: 'transparent', padding: '0 12px', color: 'rgba(240,253,244,.3)', fontSize: 11 },
  form: { display: 'flex', flexDirection: 'column', gap: 14 },
  inputWrap: { position: 'relative', display: 'flex', alignItems: 'center' },
  inputIcon: { position: 'absolute', left: 12, fontSize: 16, pointerEvents: 'none' },
  input: {
    width: '100%', padding: '12px 14px 12px 40px', borderRadius: 10,
    border: '1px solid rgba(16,185,129,.25)', background: 'rgba(255,255,255,.06)',
    color: '#f0fdf4', fontSize: 14, outline: 'none',
    fontFamily: 'Inter, sans-serif', transition: 'border-color .2s',
  },
  error: { color: '#f87171', fontSize: 13, margin: 0, padding: '8px 12px', background: 'rgba(239,68,68,.1)', borderRadius: 8 },
  submitBtn: {
    padding: '13px', borderRadius: 10, border: 'none',
    background: 'linear-gradient(135deg, #10b981, #059669)',
    color: '#fff', fontWeight: 600, fontSize: 15, cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    transition: 'opacity .2s', letterSpacing: .3,
  },
  spinner: {
    width: 16, height: 16, border: '2px solid rgba(255,255,255,.4)',
    borderTopColor: '#fff', borderRadius: '50%',
    display: 'inline-block', animation: 'spin .7s linear infinite',
  },
  hint: { marginTop: 20, color: 'rgba(240,253,244,.3)', fontSize: 11, textAlign: 'center', lineHeight: 1.7 },
  code: { background: 'rgba(16,185,129,.15)', color: '#10b981', padding: '1px 6px', borderRadius: 4, fontFamily: 'monospace', fontSize: 11 },
};
