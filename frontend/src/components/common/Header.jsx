import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, Menu, Bell, LogOut } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import LanguageToggle from '../features/LanguageToggle';
import ThemeToggle from './ThemeToggle';

const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const displayName = user?.displayName || user?.email;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div className="w-9 h-9 bg-purple-600 rounded-lg flex items-center justify-center">
              <Heart className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-slate-900 dark:text-white">MediConnect</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden lg:flex items-center space-x-0.5">
            {[
              { to: '/', label: 'Home' },
              { to: '/symptom-checker', label: 'Symptoms' },
              { to: '/hospitals', label: 'Hospitals' },
              { to: '/skincare', label: 'Skincare' },
              { to: '/first-aid', label: 'First Aid' },
              { to: '/medicine-reminder', label: 'Meds' },
              { to: '/profile', label: 'Profile' },
              { to: '/emergency', label: 'SOS' }
            ].map((link, idx) => (
              <Link key={idx} to={link.to}>
                <button className="px-2.5 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 hover:text-purple-600 dark:hover:text-purple-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
                  {link.label}
                </button>
              </Link>
            ))}
          </nav>

          {/* Right Side */}
          <div className="flex items-center space-x-2">
            <ThemeToggle />
            <LanguageToggle />
            
            {user ? (
              <>
                <Link to="/favorites" className="p-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors" title="Favorites">
                  <Heart className="w-5 h-5" />
                </Link>
                <div className="relative">
                  <button className="p-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors" title="Notifications">
                    <Bell className="w-5 h-5" />
                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                  </button>
                </div>
                <Link to="/profile">
                  <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center font-semibold text-white text-sm cursor-pointer hover:bg-purple-700 transition-colors">
                    {(displayName || 'U').charAt(0).toUpperCase()}
                  </div>
                </Link>
                <button 
                  onClick={handleLogout}
                  className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors" 
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </>
            ) : (
              <Link to="/login">
                <button className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors">
                  Sign In
                </button>
              </Link>
            )}

            <button className="md:hidden p-2 text-slate-700 dark:text-slate-300">
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
