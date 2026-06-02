import React, { createContext, useState, useEffect, useRef } from 'react';
import { authHelpers } from '../services/firebaseClient';
import { storageService } from '../services/storage';
import api from '../services/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState(null);
  const [backendProfile, setBackendProfile] = useState(null);
  const lastSyncedUidRef = useRef(null);

  const syncProfileToBackend = async (firebaseUser, force = false) => {
    if (!firebaseUser) {
      setBackendProfile(null);
      lastSyncedUidRef.current = null;
      return;
    }

    if (!force && lastSyncedUidRef.current === firebaseUser.uid) {
      return;
    }

    try {
      const response = await api.post('/auth/firebase-sync', {
        email: firebaseUser.email || '',
        full_name: firebaseUser.displayName || ''
      });

      setBackendProfile(response?.data?.user || null);
      lastSyncedUidRef.current = firebaseUser.uid;
    } catch (error) {
      console.warn('Backend profile sync failed:', error?.response?.data?.message || error?.message);
    }
  };

  useEffect(() => {
    let isMounted = true;

    authHelpers.getSession().then(async ({ session: initialSession }) => {
      if (!isMounted) return;
      setSession(initialSession);
      setUser(initialSession?.user ?? null);
      await syncProfileToBackend(initialSession?.user ?? null, true);
      setLoading(false);
    });

    const { data: { subscription } } = authHelpers.onAuthStateChange(async (event, nextSession) => {
      if (!isMounted) return;
      setSession(nextSession);
      const firebaseUser = nextSession?.user ?? null;
      setUser(firebaseUser);
      await syncProfileToBackend(firebaseUser);
      if (event !== 'TOKEN_REFRESHED') {
        setLoading(false);
      }
    });

    return () => {
      isMounted = false;
      subscription?.unsubscribe();
    };
  }, []);

  const handleSignOut = async () => {
    await authHelpers.signOut();
    setUser(null);
    setSession(null);
    setBackendProfile(null);
    lastSyncedUidRef.current = null;
    // Wipe ALL MediConnect data from storage on sign-out
    storageService.clearAll();
  };

  const value = {
    user,
    backendProfile,
    session,
    loading,
    signUp: authHelpers.signUp,
    signIn: authHelpers.signIn,
    signOut: handleSignOut,
    logout: handleSignOut
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
