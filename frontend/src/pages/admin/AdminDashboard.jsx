/**
 * AdminDashboard.jsx — M3 Admin Portal Shell
 * Role-adaptive sidebar + header layout.
 * Renders child pages via <Outlet />.
 */
import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAdminAuth } from '../../context/AdminAuthContext';

// ── Navigation config per role ────────────────────────────────────────────────
const NAV_ITEMS = {
  PLATFORM_ADMIN: [
    { to: '/admin/overview',      icon: '📊', label: 'Overview'           },
    { to: '/admin/appointments',  icon: '📅', label: 'All Appointments'   },
    { to: '/admin/doctors',       icon: '👨‍⚕️', label: 'Doctors'           },
    { to: '/admin/hospitals',     icon: '🏥', label: 'Hospitals'          },
    { to: '/admin/analytics',     icon: '📈', label: 'Analytics'          },
    { to: '/admin/notifications', icon: '🔔', label: 'Notifications'      },
    { to: '/admin/tickets',       icon: '🎧', label: 'Support Tickets'    },
    { to: '/admin/users',         icon: '👥', label: 'Admin Users'        },
  ],
  HOSPITAL_ADMIN: [
    { to: '/admin/overview',      icon: '📊', label: 'Overview'           },
    { to: '/admin/appointments',  icon: '📅', label: 'Appointments'       },
    { to: '/admin/doctors',       icon: '👨‍⚕️', label: 'Doctors'           },
    { to: '/admin/hospitals',     icon: '🏥', label: 'My Hospital'        },
    { to: '/admin/analytics',     icon: '📈', label: 'Analytics'          },
    { to: '/admin/notifications', icon: '🔔', label: 'Notifications'      },
  ],
  SUPPORT_STAFF: [
    { to: '/admin/overview',      icon: '📊', label: 'Overview'           },
    { to: '/admin/tickets',       icon: '🎧', label: 'Support Tickets'    },
    { to: '/admin/analytics',     icon: '📈', label: 'Analytics (Read)'   },
    { to: '/admin/notifications', icon: '🔔', label: 'Notifications'      },
  ],
};

const ROLE_META = {
  PLATFORM_ADMIN: { label: 'Platform Admin', color: '#6366f1', bg: '#6366f111' },
  HOSPITAL_ADMIN: { label: 'Hospital Admin', color: '#10b981', bg: '#10b98111' },
  SUPPORT_STAFF:  { label: 'Support Staff',  color: '#f59e0b', bg: '#f59e0b11' },
};

export default function AdminDashboard() {
  const { admin, role, logout, adminFetch } = useAdminAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [unreadCount, setUnreadCount]  = useState(0);
  const [summary, setSummary]          = useState(null);

  const navItems = NAV_ITEMS[role] || [];
  const roleMeta = ROLE_META[role] || { label: role, color: '#888', bg: '#88888811' };

  // ── Fetch summary for KPI bar ─────────────────────────────────────────────
  useEffect(() => {
    adminFetch('/analytics/summary')
      .then(d => setSummary(d.summary))
      .catch(() => {});
  }, [adminFetch]);

  const handleLogout = () => { logout(); navigate('/admin/login'); };

  return (
    <div style={s.root}>
      <style>{CSS}</style>

      {/* ── Sidebar ── */}
      <aside style={{ ...s.sidebar, width: sidebarOpen ? 240 : 64, transition: 'width .25s' }}>
        {/* Brand */}
        <div style={s.sidebarBrand}>
          <span style={s.sidebarLogo}>🏥</span>
          {sidebarOpen && <span style={s.sidebarTitle}>MediConnect</span>}
        </div>

        {/* Role badge */}
        {sidebarOpen && (
          <div style={{ ...s.roleBadge, background: roleMeta.bg, borderColor: roleMeta.color + '44' }}>
            <span style={{ ...s.roleText, color: roleMeta.color }}>{roleMeta.label}</span>
          </div>
        )}

        {/* Nav items */}
        <nav style={s.nav}>
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                ...s.navItem,
                ...(isActive ? s.navItemActive : {}),
                justifyContent: sidebarOpen ? 'flex-start' : 'center',
              })}
            >
              <span style={s.navIcon}>{item.icon}</span>
              {sidebarOpen && <span style={s.navLabel}>{item.label}</span>}
              {item.to === '/admin/notifications' && unreadCount > 0 && sidebarOpen && (
                <span style={s.badge}>{unreadCount}</span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Bottom: toggle + logout */}
        <div style={s.sidebarBottom}>
          <button onClick={() => setSidebarOpen(o => !o)} style={s.toggleBtn} title="Toggle sidebar">
            {sidebarOpen ? '◀' : '▶'}
          </button>
          {sidebarOpen && (
            <button onClick={handleLogout} style={s.logoutBtn}>🚪 Logout</button>
          )}
        </div>
      </aside>

      {/* ── Main ── */}
      <div style={s.main}>
        {/* Header */}
        <header style={s.header}>
          <div>
            <h2 style={s.pageTitle}>{getPageTitle(location.pathname)}</h2>
            <p style={s.pageSub}>
              Logged in as <strong style={{ color: roleMeta.color }}>{admin?.email}</strong>
            </p>
          </div>

          {/* KPI strip */}
          {summary && (
            <div style={s.kpiStrip}>
              <KPIChip label="Total" value={summary.total_appointments} color="#10b981" />
              <KPIChip label="Pending" value={summary.by_status?.PENDING || 0} color="#f59e0b" />
              <KPIChip label="Today" value={summary.today?.total || 0} color="#6366f1" />
              <KPIChip label="Doctors" value={summary.active_doctors || 0} color="#ec4899" />
            </div>
          )}
        </header>

        {/* Page content */}
        <div style={s.content}>
          <Outlet />
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────
function KPIChip({ label, value, color }) {
  return (
    <div style={{ ...s.kpiChip, borderColor: color + '33', background: color + '11' }}>
      <span style={{ ...s.kpiValue, color }}>{value}</span>
      <span style={s.kpiLabel}>{label}</span>
    </div>
  );
}

function getPageTitle(pathname) {
  const map = {
    '/admin/overview':      '📊 Dashboard Overview',
    '/admin/appointments':  '📅 Appointment Manager',
    '/admin/doctors':       '👨‍⚕️ Doctor Management',
    '/admin/hospitals':     '🏥 Hospital Console',
    '/admin/analytics':     '📈 Analytics',
    '/admin/notifications': '🔔 Notifications',
    '/admin/tickets':       '🎧 Support Tickets',
    '/admin/users':         '👥 Admin Users',
  };
  return map[pathname] || '🏥 Admin Portal';
}

// ── Styles ─────────────────────────────────────────────────────────────────────
const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #060d1a; font-family: 'Inter', sans-serif; }
  .admin-nav-active { background: rgba(16,185,129,.15) !important; color: #10b981 !important; border-left: 3px solid #10b981 !important; }
  a { text-decoration: none; }
  ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(16,185,129,.3); border-radius: 3px; }
`;

const s = {
  root: { display: 'flex', minHeight: '100vh', background: '#060d1a', color: '#f0fdf4' },
  sidebar: {
    background: 'rgba(255,255,255,.03)', borderRight: '1px solid rgba(16,185,129,.12)',
    display: 'flex', flexDirection: 'column', padding: '0 0 16px', minHeight: '100vh',
    position: 'sticky', top: 0, overflowX: 'hidden', flexShrink: 0,
  },
  sidebarBrand: { display: 'flex', alignItems: 'center', gap: 10, padding: '24px 16px 16px' },
  sidebarLogo: { fontSize: 28, flexShrink: 0 },
  sidebarTitle: { fontSize: 16, fontWeight: 700, color: '#f0fdf4', whiteSpace: 'nowrap' },
  roleBadge: { margin: '0 12px 16px', padding: '6px 12px', borderRadius: 8, border: '1px solid' },
  roleText: { fontSize: 11, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase' },
  nav: { flex: 1, display: 'flex', flexDirection: 'column', gap: 2, padding: '0 8px' },
  navItem: {
    display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
    borderRadius: 8, color: 'rgba(240,253,244,.6)', fontSize: 13, fontWeight: 500,
    transition: 'all .15s', border: '1px solid transparent', textDecoration: 'none',
  },
  navItemActive: {
    background: 'rgba(16,185,129,.12)', color: '#10b981',
    border: '1px solid rgba(16,185,129,.25)',
  },
  navIcon: { fontSize: 18, flexShrink: 0 },
  navLabel: { whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  badge: {
    marginLeft: 'auto', background: '#10b981', color: '#000',
    borderRadius: 10, fontSize: 10, fontWeight: 700, padding: '2px 6px',
  },
  sidebarBottom: { display: 'flex', flexDirection: 'column', gap: 8, padding: '0 12px' },
  toggleBtn: {
    padding: '8px', borderRadius: 8, border: '1px solid rgba(255,255,255,.1)',
    background: 'transparent', color: 'rgba(240,253,244,.5)', cursor: 'pointer', fontSize: 12,
  },
  logoutBtn: {
    padding: '8px 12px', borderRadius: 8, border: '1px solid rgba(239,68,68,.3)',
    background: 'rgba(239,68,68,.08)', color: '#f87171', cursor: 'pointer', fontSize: 13,
    fontWeight: 500, transition: 'all .2s',
  },
  main: { flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 },
  header: {
    padding: '20px 32px', borderBottom: '1px solid rgba(16,185,129,.1)',
    background: 'rgba(255,255,255,.02)', display: 'flex', alignItems: 'center',
    justifyContent: 'space-between', gap: 24, flexWrap: 'wrap',
  },
  pageTitle: { fontSize: 20, fontWeight: 700, color: '#f0fdf4', marginBottom: 2 },
  pageSub: { fontSize: 12, color: 'rgba(240,253,244,.4)' },
  kpiStrip: { display: 'flex', gap: 10, flexWrap: 'wrap' },
  kpiChip: {
    display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '8px 16px',
    borderRadius: 10, border: '1px solid', minWidth: 70,
  },
  kpiValue: { fontSize: 20, fontWeight: 700, lineHeight: 1.2 },
  kpiLabel: { fontSize: 10, color: 'rgba(240,253,244,.4)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: .5 },
  content: { flex: 1, padding: '24px 32px', overflowY: 'auto' },
};
