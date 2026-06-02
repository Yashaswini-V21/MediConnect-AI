/**
 * storageService — Hardened local storage helpers for MediConnect.
 *
 * Security notes:
 *  - Auth tokens are stored in sessionStorage (cleared when tab closes, not XSS-persistent like localStorage)
 *  - Sensitive health data is NOT stored in plain localStorage — use server-side APIs where possible
 *  - All JSON.parse calls are wrapped in try/catch to prevent parse-error crashes
 *  - On sign-out, ALL keys are wiped
 */

// Keys
const KEYS = {
  TOKEN: 'mc_token',
  USER: 'mc_user',
  LANGUAGE: 'mc_language',
  SEARCH_HISTORY: 'mc_search_history',
  FAVORITES: 'mc_favorites',
  HEALTH_PROFILE: 'mc_health_profile',
  APPOINTMENTS: 'mc_appointments',
};

const safeParse = (raw) => {
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

export const storageService = {
  // ── Token management (sessionStorage — cleared on tab/browser close) ────────
  getToken: () => sessionStorage.getItem(KEYS.TOKEN),
  setToken: (token) => sessionStorage.setItem(KEYS.TOKEN, token),
  removeToken: () => sessionStorage.removeItem(KEYS.TOKEN),

  // ── User management (sessionStorage) ────────────────────────────────────────
  getUser: () => safeParse(sessionStorage.getItem(KEYS.USER)),
  setUser: (user) => sessionStorage.setItem(KEYS.USER, JSON.stringify(user)),
  removeUser: () => sessionStorage.removeItem(KEYS.USER),

  // ── Language preference (localStorage — non-sensitive, cross-session UX) ────
  getLanguage: () => localStorage.getItem(KEYS.LANGUAGE) || 'english',
  setLanguage: (language) => localStorage.setItem(KEYS.LANGUAGE, language),

  // ── Search history (localStorage — non-sensitive symptom descriptions) ──────
  getSearchHistory: () => safeParse(localStorage.getItem(KEYS.SEARCH_HISTORY)) || [],
  addToSearchHistory: (search) => {
    const history = storageService.getSearchHistory();
    history.unshift(search);
    localStorage.setItem(KEYS.SEARCH_HISTORY, JSON.stringify(history.slice(0, 10)));
  },
  clearSearchHistory: () => localStorage.removeItem(KEYS.SEARCH_HISTORY),

  // ── Favorites (localStorage — hospital IDs, non-sensitive) ──────────────────
  getFavorites: () => safeParse(localStorage.getItem(KEYS.FAVORITES)) || [],
  addFavorite: (hospital) => {
    const favorites = storageService.getFavorites();
    if (!favorites.find(fav => fav.id === hospital.id)) {
      favorites.push(hospital);
      localStorage.setItem(KEYS.FAVORITES, JSON.stringify(favorites));
    }
  },
  removeFavorite: (hospitalId) => {
    const favorites = storageService.getFavorites();
    const updated = favorites.filter(fav => fav.id !== hospitalId);
    localStorage.setItem(KEYS.FAVORITES, JSON.stringify(updated));
  },
  clearFavorites: () => localStorage.removeItem(KEYS.FAVORITES),

  // ── Health Profile (sessionStorage — contains PII, cleared on tab close) ────
  getHealthProfile: () => safeParse(sessionStorage.getItem(KEYS.HEALTH_PROFILE)),
  setHealthProfile: (profile) => {
    sessionStorage.setItem(KEYS.HEALTH_PROFILE, JSON.stringify(profile));
  },
  clearHealthProfile: () => sessionStorage.removeItem(KEYS.HEALTH_PROFILE),

  // ── Appointments (sessionStorage — contains PII) ─────────────────────────────
  getAppointments: () => safeParse(sessionStorage.getItem(KEYS.APPOINTMENTS)) || [],
  addAppointment: (appointment) => {
    const appointments = storageService.getAppointments();
    appointments.push(appointment);
    sessionStorage.setItem(KEYS.APPOINTMENTS, JSON.stringify(appointments));
  },
  clearAppointments: () => sessionStorage.removeItem(KEYS.APPOINTMENTS),

  // ── Nuclear clear — wipes ALL MediConnect data on sign-out ──────────────────
  clearAll: () => {
    // Clear sessionStorage keys
    Object.values(KEYS).forEach(key => {
      sessionStorage.removeItem(key);
    });
    // Clear only our localStorage keys (not other apps' data)
    [KEYS.LANGUAGE, KEYS.SEARCH_HISTORY, KEYS.FAVORITES].forEach(key => {
      localStorage.removeItem(key);
    });
    // Legacy key cleanup (in case old code stored under these names)
    ['token', 'user', 'searchHistory', 'favorites', 'healthProfile', 'appointments'].forEach(key => {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    });
  },
};
