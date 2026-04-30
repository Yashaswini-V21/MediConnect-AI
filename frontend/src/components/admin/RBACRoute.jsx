/**
 * RBACRoute.jsx — Protected route guard for admin portal.
 * Usage: wrap admin routes in App.jsx with <RBACRoute allowedRoles={[...]} />
 */
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAdminAuth } from '../../context/AdminAuthContext';

export default function RBACRoute({ children, allowedRoles = [] }) {
  const { isAuthenticated, role, loading } = useAdminAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', background: '#0a0f1a', color: '#10b981'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 48, height: 48, border: '3px solid #10b981',
            borderTopColor: 'transparent', borderRadius: '50%',
            animation: 'spin 0.8s linear infinite', margin: '0 auto 16px'
          }} />
          <p style={{ fontFamily: 'Inter, sans-serif', fontSize: 14, opacity: 0.7 }}>
            Verifying admin access…
          </p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(role)) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', background: '#0a0f1a', color: '#ef4444',
        fontFamily: 'Inter, sans-serif', textAlign: 'center', padding: 24
      }}>
        <div>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🚫</div>
          <h2 style={{ marginBottom: 8, fontSize: 22 }}>Access Denied</h2>
          <p style={{ opacity: 0.7, marginBottom: 24 }}>
            Your role <strong>{role}</strong> is not allowed to view this page.
          </p>
          <a href="/admin/dashboard" style={{ color: '#10b981', textDecoration: 'none' }}>
            ← Back to Dashboard
          </a>
        </div>
      </div>
    );
  }

  return children;
}
