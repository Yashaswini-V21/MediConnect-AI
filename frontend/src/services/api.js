import axios from 'axios';
import { authHelpers } from './firebaseClient';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,       // 15s request timeout — prevents hanging requests
  withCredentials: false,
});

// ── Request interceptor: attach auth token ────────────────────────────────────
api.interceptors.request.use(
  async (config) => {
    let token = null;

    try {
      // Firebase token takes priority (always fresh)
      token = await authHelpers.getIdToken();
    } catch {
      token = null;
    }

    if (!token) {
      // Fallback to sessionStorage JWT (legacy / OTP-based login)
      token = sessionStorage.getItem('mc_token') || localStorage.getItem('token');
    }

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response interceptor: handle errors cleanly ───────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      // Timeout — surface a user-friendly message
      const timeoutError = new Error('Request timed out. Please check your connection and try again.');
      timeoutError.isTimeout = true;
      return Promise.reject(timeoutError);
    }

    if (error.response?.status === 401) {
      // Clear auth data on unauthorized — prevent stale token loops
      sessionStorage.removeItem('mc_token');
      sessionStorage.removeItem('mc_user');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Only redirect if not already on auth pages
      if (
        !window.location.pathname.includes('/login') &&
        !window.location.pathname.includes('/signup')
      ) {
        window.location.href = '/login';
      }
    }

    if (error.response?.status === 429) {
      // Surface rate-limit error clearly
      const rateLimitError = new Error(
        error.response.data?.message ||
        'Too many requests. Please wait a moment and try again.'
      );
      rateLimitError.isRateLimit = true;
      rateLimitError.response = error.response;
      return Promise.reject(rateLimitError);
    }

    // Sanitize error message — never expose internal server details to users
    if (error.response?.status >= 500) {
      const serverError = new Error('A server error occurred. Please try again later.');
      serverError.response = error.response;
      serverError.isServerError = true;
      return Promise.reject(serverError);
    }

    return Promise.reject(error);
  }
);

export default api;
