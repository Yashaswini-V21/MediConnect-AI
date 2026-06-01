import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { AuthProvider } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import { ThemeProvider } from './context/ThemeContext';
import { Toaster } from 'react-hot-toast';
import Header from './components/common/Header';
import Footer from './components/common/Footer';
import SplashScreen from './components/common/SplashScreen';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AIDoctorBot from './components/features/AIDoctorBot';
import Login from './components/auth/Login';
import Signup from './components/auth/Signup';
import Home from './pages/Home';
import SymptomChecker from './pages/SymptomChecker';
import Hospitals from './pages/Hospitals';
import Emergency from './pages/Emergency';
import Dashboard from './pages/Dashboard';
import Favorites from './components/features/Favorites';
import ChatDoctor from './pages/ChatDoctor';
import HealthProfile from './pages/HealthProfile';
import Appointments from './pages/Appointments';
import Specialists from './pages/Specialists';
import Skincare from './pages/Skincare';
import MedicineReminder from './pages/MedicineReminder';
import HealthTools from './pages/HealthTools';
import FirstAidGuide from './pages/FirstAidGuide';
import Profile from './pages/Profile';
import WellnessScore from './pages/WellnessScore';
// ── M3: Admin Portal ──────────────────────────────────────────────────────────
import { AdminAuthProvider } from './context/AdminAuthContext';
import AdminLogin from './pages/admin/AdminLogin';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminOverview from './pages/admin/AdminOverview';
import AppointmentManager from './pages/admin/AppointmentManager';
import DoctorManager from './pages/admin/DoctorManager';
import AdminAnalytics from './pages/admin/AdminAnalytics';
import RBACRoute from './components/admin/RBACRoute';

function App() {
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    const hasSeenSplash = sessionStorage.getItem('hasSeenSplash');
    if (hasSeenSplash) {
      setShowSplash(false);
    }
  }, []);

  const handleSplashComplete = () => {
    sessionStorage.setItem('hasSeenSplash', 'true');
    setShowSplash(false);
  };

  return (
    <ThemeProvider>
      <AuthProvider>
        <LanguageProvider>
          <BrowserRouter>
            <AnimatePresence mode="wait">
              {showSplash && (
                <SplashScreen key="splash" onComplete={handleSplashComplete} />
              )}
            </AnimatePresence>

            {!showSplash && (
              <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 dark:from-slate-950 dark:via-blue-950 dark:to-slate-900 flex flex-col transition-all duration-500">
                <Header />
                <main className="flex-grow">
                  <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/signup" element={<Signup />} />
                    <Route path="/emergency" element={<Emergency />} />
                    <Route
                      path="/symptom-checker"
                      element={
                        <ProtectedRoute>
                          <SymptomChecker />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/hospitals"
                      element={
                        <ProtectedRoute>
                          <Hospitals />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/dashboard"
                      element={
                        <ProtectedRoute>
                          <Dashboard />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/profile"
                      element={
                        <ProtectedRoute>
                          <Profile />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/favorites"
                      element={
                        <ProtectedRoute>
                          <Favorites />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/chat-doctor"
                      element={
                        <ProtectedRoute>
                          <ChatDoctor />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/health-profile"
                      element={
                        <ProtectedRoute>
                          <HealthProfile />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/appointments"
                      element={
                        <ProtectedRoute>
                          <Appointments />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/specialists"
                      element={
                        <ProtectedRoute>
                          <Specialists />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/skincare"
                      element={
                        <ProtectedRoute>
                          <Skincare />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/medicine-reminder"
                      element={
                        <ProtectedRoute>
                          <MedicineReminder />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/health-tools"
                      element={
                        <ProtectedRoute>
                          <HealthTools />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/first-aid"
                      element={
                        <ProtectedRoute>
                          <FirstAidGuide />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/wellness"
                      element={
                        <ProtectedRoute>
                          <WellnessScore />
                        </ProtectedRoute>
                      }
                    />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </main>
                <Footer />
                
                {/* AI Doctor Bot - Floating on all pages */}
                <AIDoctorBot />
                
                <Toaster 
                  position="top-right"
                  toastOptions={{
                    className: 'dark:bg-gray-800 dark:text-white',
                    style: {
                      background: 'var(--toast-bg)',
                      color: 'var(--toast-color)',
                    },
                  }}
                />
              </div>
            )}

            {/* ── M3: Admin Portal (separate from patient shell) ── */}
            <AdminAuthProvider>
              <Routes>
                <Route path="/admin/login" element={<AdminLogin />} />
                <Route path="/admin" element={
                  <RBACRoute>
                    <AdminDashboard />
                  </RBACRoute>
                }>
                  <Route index element={<Navigate to="/admin/overview" replace />} />
                  <Route path="overview"      element={<AdminOverview />} />
                  <Route path="appointments"  element={<AppointmentManager />} />
                  <Route path="doctors"       element={<DoctorManager />} />
                  <Route path="analytics"     element={<AdminAnalytics />} />
                  {/* Hospitals, Notifications, Tickets, Users — stubs, add pages later */}
                  <Route path="*"             element={<Navigate to="/admin/overview" replace />} />
                </Route>
              </Routes>
            </AdminAuthProvider>
          </BrowserRouter>
        </LanguageProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
