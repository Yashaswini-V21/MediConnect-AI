import React from 'react';
import { Github, Twitter, Linkedin, Phone, Mail, MapPin, Shield } from 'lucide-react';
import Logo from './Logo';

const Footer = () => {
  return (
    <footer className="relative bg-gradient-to-br from-slate-800 via-slate-900 to-black text-white overflow-hidden">
      {/* Simple Pattern Background */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)',
          backgroundSize: '30px 30px'
        }} />
      </div>
      
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
          {/* Brand Section */}
          <div className="col-span-1">
            <div className="mb-6">
              <Logo size="small" animated={false} showText={true} />
            </div>
            <p className="text-lg text-cyan-300 mb-4 font-semibold leading-relaxed">
              AI-Powered Healthcare Navigation
            </p>
            <p className="text-sm text-slate-300 leading-relaxed">
              Connecting patients with the right medical care, instantly.
            </p>
            <div className="mt-6 flex items-center space-x-2 text-sm text-cyan-400">
              <Shield className="w-5 h-5" />
              <span className="font-bold">Trusted Healthcare Partner</span>
            </div>
          </div>

          {/* Quick Access */}
          <div>
            <h3 className="text-white font-bold text-xl mb-6 tracking-wide">
              Quick Links
            </h3>
            <ul className="space-y-3">
              <li><a href="/" className="text-slate-300 hover:text-cyan-400 transition-colors text-base block">Home</a></li>
              <li><a href="/symptoms" className="text-slate-300 hover:text-cyan-400 transition-colors text-base block">Symptom Checker</a></li>
              <li><a href="/hospitals" className="text-slate-300 hover:text-cyan-400 transition-colors text-base block">Find Hospitals</a></li>
              <li><a href="/dashboard" className="text-slate-300 hover:text-cyan-400 transition-colors text-base block">Dashboard</a></li>
              <li><a href="/emergency" className="text-slate-300 hover:text-cyan-400 transition-colors text-base block">Emergency</a></li>
            </ul>
          </div>

          {/* Important Links */}
          <div>
            <h3 className="text-white font-black text-lg mb-6 tracking-wide">📋 Information</h3>
            <ul className="space-y-3">
              <li><a href="/about" className="text-teal-100 hover:text-emerald-400 transition-colors font-bold text-base block">About MediConnect</a></li>
              <li><a href="/how-it-works" className="text-teal-100 hover:text-emerald-400 transition-colors font-bold text-base block">How It Works</a></li>
              <li><a href="/privacy" className="text-teal-100 hover:text-emerald-400 transition-colors font-bold text-base block">Privacy & Security</a></li>
              <li><a href="/terms" className="text-teal-100 hover:text-emerald-400 transition-colors font-bold text-base block">Terms of Service</a></li>
              <li><a href="/contact" className="text-teal-100 hover:text-emerald-400 transition-colors font-bold text-base block">Contact Support</a></li>
            </ul>
          </div>

          {/* Emergency Contacts */}
          <div className="bg-gradient-to-br from-red-600 via-red-700 to-rose-800 rounded-2xl p-6 shadow-2xl border-2 border-red-400">
            <h3 className="text-white font-black text-xl mb-4 flex items-center tracking-wide">
              <Phone className="w-6 h-6 mr-2 animate-pulse" />
              Emergency Helplines
            </h3>
            <div className="space-y-4">
              <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3 border border-white/30">
                <p className="text-xs text-red-100 mb-1 font-black">🚨 EMERGENCY</p>
                <a href="tel:108" className="text-2xl font-black text-white hover:text-yellow-300 transition-colors block">108</a>
                <p className="text-xs text-red-100 mt-1 font-bold">National Emergency</p>
              </div>
              <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3 border border-white/30">
                <p className="text-xs text-red-100 mb-1 font-black">🚑 AMBULANCE</p>
                <a href="tel:102" className="text-2xl font-black text-white hover:text-yellow-300 transition-colors block">102</a>
                <p className="text-xs text-red-100 mt-1 font-bold">Medical Emergency</p>
              </div>
              <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3 border border-white/30">
                <p className="text-xs text-red-100 mb-1 font-black">👮 POLICE</p>
                <a href="tel:100" className="text-2xl font-black text-white hover:text-yellow-300 transition-colors block">100</a>
                <p className="text-xs text-red-100 mt-1 font-bold">Security Emergency</p>
              </div>
            </div>
            <p className="text-xs text-red-100 mt-4 text-center font-black tracking-wider">⚡ Available 24/7</p>
          </div>
        </div>

        {/* Contact Bar */}
        <div className="mt-12 pt-8 border-t border-emerald-700/50">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="flex items-center space-x-3 text-teal-100">
              <Mail className="w-5 h-5 text-emerald-400" />
              <div>
                <p className="text-xs text-emerald-300 font-black">EMAIL</p>
                <a href="mailto:support@mediconnect.ai" className="text-base font-black hover:text-emerald-400 transition-colors">support@mediconnect.ai</a>
              </div>
            </div>
            <div className="flex items-center space-x-3 text-teal-100">
              <Phone className="w-5 h-5 text-emerald-400" />
              <div>
                <p className="text-xs text-emerald-300 font-black">HELPLINE</p>
                <a href="tel:1800-MEDICONNECT" className="text-base font-black hover:text-emerald-400 transition-colors">1800-MEDICONNECT</a>
              </div>
            </div>
            <div className="flex items-center space-x-3 text-teal-100">
              <MapPin className="w-5 h-5 text-emerald-400" />
              <div>
                <p className="text-xs text-emerald-300 font-black">HEADQUARTERS</p>
                <p className="text-base font-black">Bangalore, Karnataka, India</p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-emerald-700/50 flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div className="text-center md:text-left">
            <p className="text-base font-black text-white mb-1 tracking-wide">
              © 2026 MediConnect AI. All Rights Reserved.
            </p>
            <p className="text-sm text-emerald-200 font-black tracking-wide">
              🏆 Microsoft Imagine Cup 2026 Project | Made with ❤️ in India
            </p>
          </div>
          <div className="flex space-x-6">
            <a href="https://github.com/Yashaswini-V21/mediconnect-ai" target="_blank" rel="noopener noreferrer" 
               className="bg-white/10 hover:bg-white/20 backdrop-blur-sm p-3 rounded-full transition-all hover:scale-110">
              <Github className="w-6 h-6 text-white" />
            </a>
            <a href="https://x.com" target="_blank" rel="noopener noreferrer" className="bg-white/10 hover:bg-white/20 backdrop-blur-sm p-3 rounded-full transition-all hover:scale-110">
              <Twitter className="w-6 h-6 text-white" />
            </a>
            <a href="https://www.linkedin.com" target="_blank" rel="noopener noreferrer" className="bg-white/10 hover:bg-white/20 backdrop-blur-sm p-3 rounded-full transition-all hover:scale-110">
              <Linkedin className="w-6 h-6 text-white" />
            </a>
          </div>
        </div>

        {/* Trust Badge */}
        <div className="mt-8 text-center">
          <p className="text-sm text-emerald-200 font-black inline-flex items-center justify-center space-x-2 tracking-wide">
            <Shield className="w-4 h-4" />
            <span>Trusted Healthcare Navigation Platform | HIPAA Compliant | Secure & Private</span>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
