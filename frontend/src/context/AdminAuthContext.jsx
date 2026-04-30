/**
 * AdminAuthContext.jsx
 * M3: Admin authentication state management.
 * Separate from patient auth — admins use email + shared secret token.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AdminAuthContext = createContext(null);

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const ADMIN_TOKEN = process.env.REACT_APP_ADMIN_TOKEN || 'mediconnect-admin-dev-token';
const STORAGE_KEY = 'mediconnect_admin_session';

export function AdminAuthProvider({ children }) {
  const [admin, setAdmin]       = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);

  // ── Restore session from localStorage ──────────────────────────────────────
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const { admin: savedAdmin, bearer } = JSON.parse(saved);
        setAdmin({ ...savedAdmin, bearer });
      } catch (_) {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setLoading(false);
  }, []);

  // ── Login ──────────────────────────────────────────────────────────────────
  const login = useCallback(async (email) => {
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, token: ADMIN_TOKEN }),
      });
      const data = await res.json();

      if (!res.ok) throw new Error(data.error || 'Login failed');

      const session = { ...data.admin, bearer: data.bearer_token };
      setAdmin(session);
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        admin: data.admin,
        bearer: data.bearer_token,
      }));
      return { success: true, admin: session };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  }, []);

  // ── Logout ─────────────────────────────────────────────────────────────────
  const logout = useCallback(() => {
    setAdmin(null);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  // ── Auth headers helper ────────────────────────────────────────────────────
  const authHeaders = useCallback(() => {
    if (!admin) return {};
    return {
      'Authorization': `Bearer ${admin.bearer}`,
      'X-Admin-Email': admin.email,
      'X-Admin-Token': ADMIN_TOKEN,
      'Content-Type': 'application/json',
    };
  }, [admin]);

  // ── API helper ─────────────────────────────────────────────────────────────
  const adminFetch = useCallback(async (path, options = {}) => {
    const res = await fetch(`${API_BASE}/api/admin${path}`, {
      ...options,
      headers: { ...authHeaders(), ...(options.headers || {}) },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || data.message || 'API error');
    return data;
  }, [authHeaders]);

  const value = {
    admin,
    loading,
    error,
    isAuthenticated: !!admin,
    role: admin?.role || null,
    hospitalId: admin?.hospital_id || null,
    isPlatformAdmin: admin?.role === 'PLATFORM_ADMIN',
    isHospitalAdmin: admin?.role === 'HOSPITAL_ADMIN',
    isSupportStaff:  admin?.role === 'SUPPORT_STAFF',
    login,
    logout,
    authHeaders,
    adminFetch,
  };

  return (
    <AdminAuthContext.Provider value={value}>
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth() {
  const ctx = useContext(AdminAuthContext);
  if (!ctx) throw new Error('useAdminAuth must be used inside AdminAuthProvider');
  return ctx;
}
