import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Heart, Menu, X, Bell, LogOut, Activity } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import LanguageToggle from '../features/LanguageToggle';
import ThemeToggle from './ThemeToggle';

const NAV_LINKS = [
  { to: '/',                label: 'Home' },
  { to: '/symptom-checker', label: 'Symptoms' },
  { to: '/hospitals',       label: 'Hospitals' },
  { to: '/wellness',        label: 'Wellness ✨', highlight: true },
  { to: '/skincare',        label: 'Skincare' },
  { to: '/first-aid',       label: 'First Aid' },
  { to: '/medicine-reminder', label: 'Medicines' },
  { to: '/emergency',       label: '🚨 SOS', emergency: true },
];

const Header = () => {
  const { user, logout }   = useAuth();
  const navigate           = useNavigate();
  const location           = useLocation();
  const displayName        = user?.displayName || user?.email;
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMobileOpen(false);
  };

  const isActive = (to) =>
    to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);

  return (
    <header className="sticky top-0 z-50 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800/80 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">

          {/* ── Logo ── */}
          <Link to="/" className="flex items-center gap-2.5 group shrink-0">
            <div className="w-9 h-9 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/25 group-hover:shadow-purple-500/40 transition-all duration-200 group-hover:scale-105">
              <Heart className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-base font-extrabold text-slate-900 dark:text-white tracking-tight">
                MediConnect
              </span>
              <span className="text-[9px] font-semibold text-purple-600 dark:text-purple-400 tracking-widest uppercase">
                AI Platform
              </span>
            </div>
          </Link>

          {/* ── Desktop Nav ── */}
          <nav className="hidden lg:flex items-center gap-0.5">
            {NAV_LINKS.map((link) => (
              <Link key={link.to} to={link.to}>
                <button
                  className={`px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150 ${
                    link.emergency
                      ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                      : link.highlight
                      ? 'text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20'
                      : isActive(link.to)
                      ? 'text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-900/30'
                      : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  {link.label}
                </button>
              </Link>
            ))}
          </nav>

          {/* ── Right Controls ── */}
          <div className="flex items-center gap-1.5">
            <ThemeToggle />
            <LanguageToggle />

            {user ? (
              <>
                <Link
                  to="/favorites"
                  className="p-2 text-slate-500 dark:text-slate-400 hover:text-purple-600 dark:hover:text-purple-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                  title="Favourites"
                >
                  <Heart className="w-4.5 h-4.5" />
                </Link>

                <div className="relative">
                  <button
                    className="p-2 text-slate-500 dark:text-slate-400 hover:text-purple-600 dark:hover:text-purple-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                    title="Notifications"
                  >
                    <Bell className="w-4.5 h-4.5" />
                    <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full" />
                  </button>
                </div>

                <Link to="/wellness" title="Wellness Score">
                  <button className="p-2 text-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors">
                    <Activity className="w-4.5 h-4.5" />
                  </button>
                </Link>

                <Link to="/profile">
                  <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg flex items-center justify-center font-bold text-white text-xs cursor-pointer hover:scale-105 transition-transform shadow-md">
                    {(displayName || 'U').charAt(0).toUpperCase()}
                  </div>
                </Link>

                <button
                  onClick={handleLogout}
                  className="p-2 text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  title="Sign out"
                >
                  <LogOut className="w-4.5 h-4.5" />
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/login">
                  <button className="px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">
                    Sign In
                  </button>
                </Link>
                <Link to="/signup">
                  <button className="px-3.5 py-1.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white text-xs font-semibold rounded-lg shadow-md shadow-purple-500/25 hover:shadow-purple-500/40 transition-all duration-200">
                    Get Started
                  </button>
                </Link>
              </div>
            )}

            {/* Mobile hamburger */}
            <button
              className="lg:hidden p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* ── Mobile Menu ── */}
        {mobileOpen && (
          <div className="lg:hidden py-3 border-t border-slate-200 dark:border-slate-800 space-y-0.5">
            {NAV_LINKS.map((link) => (
              <Link key={link.to} to={link.to} onClick={() => setMobileOpen(false)}>
                <div className={`block px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                  link.emergency
                    ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                    : isActive(link.to)
                    ? 'text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-900/30'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}>
                  {link.label}
                </div>
              </Link>
            ))}
            {user && (
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2.5 rounded-lg text-sm font-semibold text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              >
                Sign Out
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
