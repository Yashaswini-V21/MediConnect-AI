import React from 'react';
import { Link } from 'react-router-dom';
import { Github, Linkedin, Phone, Mail, MapPin, Shield, Heart, Activity, ExternalLink } from 'lucide-react';

const QUICK_LINKS = [
  { to: '/',                label: 'Home' },
  { to: '/symptom-checker', label: 'Symptom Checker' },
  { to: '/hospitals',       label: 'Find Hospitals' },
  { to: '/wellness',        label: 'Wellness Score ✨' },
  { to: '/emergency',       label: 'Emergency SOS' },
  { to: '/appointments',    label: 'Appointments' },
];

const FEATURE_LINKS = [
  { to: '/skincare',          label: 'AI Skincare' },
  { to: '/first-aid',         label: 'First Aid Guide' },
  { to: '/medicine-reminder', label: 'Medicine Reminders' },
  { to: '/health-tools',      label: 'Health Tools' },
  { to: '/chat-doctor',       label: 'AI Doctor Chat' },
  { to: '/specialists',       label: 'Specialists' },
];

const EMERGENCY_LINES = [
  { label: 'National Emergency', number: '108', icon: '🚨' },
  { label: 'Medical / Ambulance', number: '102', icon: '🚑' },
  { label: 'Police',              number: '100', icon: '👮' },
  { label: 'Women Helpline',      number: '1091', icon: '💜' },
];

const Footer = () => {
  const year = new Date().getFullYear();

  return (
    <footer className="bg-gradient-to-b from-slate-900 to-black text-white">

      {/* ── Top decorative accent ── */}
      <div className="h-px bg-gradient-to-r from-transparent via-purple-500 to-transparent" />

      {/* ── Main content ── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10">

          {/* Brand */}
          <div className="lg:col-span-1">
            <Link to="/" className="inline-flex items-center gap-2.5 mb-5 group">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30 group-hover:scale-105 transition-transform">
                <Heart className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-lg font-extrabold text-white leading-none tracking-tight">MediConnect AI</div>
                <div className="text-[9px] font-bold text-purple-400 tracking-widest uppercase mt-0.5">Healthcare Platform</div>
              </div>
            </Link>

            <p className="text-sm text-slate-400 leading-relaxed mb-6">
              AI-powered healthcare navigation connecting patients with the right medical care — instantly, securely, multilingually.
            </p>

            {/* Academic badge */}
            <div className="inline-flex flex-col gap-2">
              <div className="flex items-center gap-2 px-3 py-2 bg-purple-900/40 border border-purple-700/50 rounded-lg text-xs text-purple-300 font-semibold">
                <Activity className="w-3.5 h-3.5" />
                IBM SkillBuild × Edunet Foundation
              </div>
              <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/60 border border-slate-700/50 rounded-lg text-xs text-slate-400">
                <Shield className="w-3.5 h-3.5 text-green-400" />
                AES-256 Encrypted · RBAC Secured
              </div>
            </div>

            {/* Social links */}
            <div className="flex items-center gap-3 mt-6">
              <a
                href="https://github.com/Yashaswini-V21/MediConnect-AI"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 bg-slate-800 hover:bg-purple-600 rounded-lg flex items-center justify-center transition-colors"
                aria-label="GitHub"
              >
                <Github className="w-4 h-4" />
              </a>
              <a
                href="https://www.linkedin.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 bg-slate-800 hover:bg-blue-600 rounded-lg flex items-center justify-center transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin className="w-4 h-4" />
              </a>
              <a
                href="https://mediconnect-ai-nu.vercel.app"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 bg-slate-800 hover:bg-emerald-600 rounded-lg flex items-center justify-center transition-colors"
                aria-label="Live Demo"
                title="Live Demo"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-bold text-sm uppercase tracking-widest mb-5 flex items-center gap-2">
              <span className="w-1 h-4 bg-purple-500 rounded-full inline-block" />
              Quick Links
            </h3>
            <ul className="space-y-2.5">
              {QUICK_LINKS.map((link) => (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    className="text-sm text-slate-400 hover:text-purple-300 transition-colors flex items-center gap-1.5 group"
                  >
                    <span className="w-1 h-1 rounded-full bg-slate-600 group-hover:bg-purple-500 transition-colors shrink-0" />
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Features */}
          <div>
            <h3 className="text-white font-bold text-sm uppercase tracking-widest mb-5 flex items-center gap-2">
              <span className="w-1 h-4 bg-indigo-500 rounded-full inline-block" />
              Features
            </h3>
            <ul className="space-y-2.5">
              {FEATURE_LINKS.map((link) => (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    className="text-sm text-slate-400 hover:text-indigo-300 transition-colors flex items-center gap-1.5 group"
                  >
                    <span className="w-1 h-1 rounded-full bg-slate-600 group-hover:bg-indigo-500 transition-colors shrink-0" />
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Emergency Helplines */}
          <div>
            <h3 className="text-white font-bold text-sm uppercase tracking-widest mb-5 flex items-center gap-2">
              <span className="w-1 h-4 bg-red-500 rounded-full inline-block animate-pulse" />
              Emergency Helplines
            </h3>
            <div className="space-y-2.5">
              {EMERGENCY_LINES.map(({ label, number, icon }) => (
                <a
                  key={number}
                  href={`tel:${number}`}
                  className="flex items-center justify-between p-3 bg-slate-800/60 hover:bg-red-900/30 border border-slate-700/50 hover:border-red-700/50 rounded-xl transition-all group"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="text-base">{icon}</span>
                    <div>
                      <div className="text-xs text-slate-400 group-hover:text-red-300 transition-colors">{label}</div>
                      <div className="text-base font-extrabold text-white">{number}</div>
                    </div>
                  </div>
                  <Phone className="w-3.5 h-3.5 text-slate-500 group-hover:text-red-400 transition-colors" />
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* ── Contact Bar ── */}
        <div className="mt-12 pt-8 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="flex items-center gap-3 text-slate-400 hover:text-purple-300 transition-colors group">
            <div className="w-8 h-8 bg-slate-800 group-hover:bg-purple-900/40 rounded-lg flex items-center justify-center transition-colors">
              <Mail className="w-4 h-4 text-purple-400" />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Email</div>
              <a href="mailto:support@mediconnect.ai" className="text-sm font-semibold">support@mediconnect.ai</a>
            </div>
          </div>
          <div className="flex items-center gap-3 text-slate-400 hover:text-indigo-300 transition-colors group">
            <div className="w-8 h-8 bg-slate-800 group-hover:bg-indigo-900/40 rounded-lg flex items-center justify-center transition-colors">
              <Phone className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Helpline</div>
              <div className="text-sm font-semibold">1800-MEDICONNECT</div>
            </div>
          </div>
          <div className="flex items-center gap-3 text-slate-400 hover:text-emerald-300 transition-colors group">
            <div className="w-8 h-8 bg-slate-800 group-hover:bg-emerald-900/40 rounded-lg flex items-center justify-center transition-colors">
              <MapPin className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Location</div>
              <div className="text-sm font-semibold">Bangalore, Karnataka, India</div>
            </div>
          </div>
        </div>

        {/* ── Bottom Bar ── */}
        <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <p className="text-sm text-slate-500">
              © {year} <span className="text-slate-300 font-semibold">MediConnect AI</span>. All rights reserved.
            </p>
            <p className="text-xs text-slate-600 mt-1">
              Built for · IBM SkillBuild AIML Internship · Edunet Foundation Capstone Project
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-600">
            <span className="flex items-center gap-1.5">
              <Shield className="w-3 h-3 text-green-500" />
              AES-256 Encrypted
            </span>
            <span className="text-slate-700">·</span>
            <span className="flex items-center gap-1.5">
              <Heart className="w-3 h-3 text-red-500" />
              Made with love in India
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
