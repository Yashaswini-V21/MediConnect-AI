import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Phone, MapPin, User, X, Check } from 'lucide-react';
import toast from 'react-hot-toast';

const EmergencySOS = () => {
  const [isSOSActive, setIsSOSActive] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const [emergencyContacts, setEmergencyContacts] = useState(() => {
    const saved = localStorage.getItem('emergencyContacts');
    return saved ? JSON.parse(saved) : [
      { name: 'Emergency Services', number: '108', type: 'ambulance' },
      { name: 'Police', number: '100', type: 'police' },
      { name: 'Fire Department', number: '101', type: 'fire' }
    ];
  });
  const [showAddContact, setShowAddContact] = useState(false);
  const [newContact, setNewContact] = useState({ name: '', number: '' });

  const handleSOSPress = () => {
    if (isSOSActive) return;
    
    setIsSOSActive(true);
    let count = 5;
    
    const interval = setInterval(() => {
      count--;
      setCountdown(count);
      
      if (count === 0) {
        clearInterval(interval);
        triggerSOS();
      }
    }, 1000);
  };

  const cancelSOS = () => {
    setIsSOSActive(false);
    setCountdown(5);
    toast.success('SOS cancelled');
  };

  const triggerSOS = async () => {
    setIsSOSActive(false);
    setCountdown(5);
    
    // Get current location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const locationUrl = `https://www.google.com/maps?q=${latitude},${longitude}`;
          
          // Call emergency contacts
          emergencyContacts.forEach((contact) => {
            if (contact.number !== '108' && contact.number !== '100' && contact.number !== '101') {
              // For personal contacts, try to send SMS (only works on mobile)
              const message = `🚨 EMERGENCY ALERT!\n\nI need immediate help!\n\nMy location: ${locationUrl}\n\nThis is an automated emergency message from MediConnect AI.`;
              
              if (window.location.protocol === 'https:' || window.location.hostname === 'localhost') {
                // Try SMS API (works on mobile devices)
                window.open(`sms:${contact.number}?body=${encodeURIComponent(message)}`, '_blank');
              }
            }
          });
          
          // Show alert with location
          toast.success(
            <div>
              <p className="font-bold">🚨 SOS ACTIVATED!</p>
              <p className="text-xs mt-1">Location shared with emergency contacts</p>
              <a 
                href={locationUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-500 underline text-xs"
              >
                View your location
              </a>
            </div>,
            { duration: 10000 }
          );
          
          // Call first emergency number (108)
          window.location.href = 'tel:108';
        },
        (error) => {
          toast.error('Could not get location. Enable location access.');
          window.location.href = 'tel:108';
        }
      );
    } else {
      // Fallback: Just call 108
      window.location.href = 'tel:108';
    }
  };

  const addContact = () => {
    if (!newContact.name || !newContact.number) {
      toast.error('Please enter name and number');
      return;
    }
    
    const updated = [...emergencyContacts, { ...newContact, type: 'personal' }];
    setEmergencyContacts(updated);
    localStorage.setItem('emergencyContacts', JSON.stringify(updated));
    setNewContact({ name: '', number: '' });
    setShowAddContact(false);
    toast.success('Emergency contact added!');
  };

  const removeContact = (index) => {
    const updated = emergencyContacts.filter((_, i) => i !== index);
    setEmergencyContacts(updated);
    localStorage.setItem('emergencyContacts', JSON.stringify(updated));
    toast.success('Contact removed');
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* SOS Button */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="relative"
      >
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onMouseDown={handleSOSPress}
          disabled={isSOSActive}
          className="w-full h-64 rounded-3xl bg-gradient-to-br from-red-500 via-red-600 to-red-700 text-white shadow-2xl hover:shadow-red-500/50 transition-all duration-300 relative overflow-hidden"
        >
          {/* Animated Background */}
          <motion.div
            animate={isSOSActive ? { scale: [1, 1.5, 1], opacity: [0.3, 0, 0.3] } : {}}
            transition={{ repeat: Infinity, duration: 1 }}
            className="absolute inset-0 bg-white rounded-3xl"
          />
          
          <div className="relative z-10 flex flex-col items-center justify-center h-full">
            <motion.div
              animate={isSOSActive ? { rotate: [0, 10, -10, 0] } : {}}
              transition={{ repeat: Infinity, duration: 0.5 }}
            >
              <AlertCircle className="w-24 h-24 mb-4" />
            </motion.div>
            
            {isSOSActive ? (
              <>
                <h2 className="text-5xl font-black mb-2">{countdown}</h2>
                <p className="text-xl font-bold">Calling Emergency Services...</p>
                <button
                  onClick={cancelSOS}
                  className="mt-6 px-8 py-3 bg-white text-red-600 rounded-full font-bold text-lg hover:bg-gray-100 transition"
                >
                  CANCEL
                </button>
              </>
            ) : (
              <>
                <h2 className="text-4xl font-black mb-2">EMERGENCY SOS</h2>
                <p className="text-lg opacity-90">Hold to activate</p>
                <p className="text-sm opacity-75 mt-2">Shares location & calls 108</p>
              </>
            )}
          </div>
        </motion.button>
      </motion.div>

      {/* Quick Dial Emergency Numbers */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Phone className="w-5 h-5 text-red-500" />
            Emergency Contacts
          </h3>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowAddContact(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-semibold hover:bg-purple-700 transition"
          >
            + Add Contact
          </motion.button>
        </div>

        <div className="grid gap-3">
          {emergencyContacts.map((contact, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-600 transition group"
            >
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  contact.type === 'ambulance' ? 'bg-red-100 text-red-600' :
                  contact.type === 'police' ? 'bg-blue-100 text-blue-600' :
                  contact.type === 'fire' ? 'bg-orange-100 text-orange-600' :
                  'bg-purple-100 text-purple-600'
                }`}>
                  {contact.type === 'personal' ? <User className="w-5 h-5" /> : <Phone className="w-5 h-5" />}
                </div>
                <div>
                  <h4 className="font-semibold text-slate-900 dark:text-white">{contact.name}</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400">{contact.number}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={`tel:${contact.number}`}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg font-semibold hover:bg-green-600 transition text-sm"
                >
                  Call
                </a>
                {contact.type === 'personal' && (
                  <button
                    onClick={() => removeContact(index)}
                    className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Add Contact Modal */}
      <AnimatePresence>
        {showAddContact && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowAddContact(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl"
            >
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Add Emergency Contact</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Contact Name
                  </label>
                  <input
                    type="text"
                    value={newContact.name}
                    onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                    placeholder="e.g., Mom, Dad, Doctor"
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:border-purple-600 focus:ring-2 focus:ring-purple-200 transition"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    value={newContact.number}
                    onChange={(e) => setNewContact({ ...newContact, number: e.target.value })}
                    placeholder="+91 98765 43210"
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:border-purple-600 focus:ring-2 focus:ring-purple-200 transition"
                  />
                </div>
                
                <div className="flex gap-3 mt-6">
                  <button
                    onClick={addContact}
                    className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-xl font-semibold hover:bg-purple-700 transition flex items-center justify-center gap-2"
                  >
                    <Check className="w-5 h-5" />
                    Add Contact
                  </button>
                  <button
                    onClick={() => setShowAddContact(false)}
                    className="px-6 py-3 bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white rounded-xl font-semibold hover:bg-slate-300 dark:hover:bg-slate-600 transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Info Card */}
      <div className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-2xl p-6 border-2 border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <MapPin className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-1" />
          <div>
            <h4 className="font-bold text-blue-900 dark:text-blue-200 mb-2">How SOS Works</h4>
            <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
              <li>• Hold the SOS button for 5 seconds</li>
              <li>• Your location is automatically shared</li>
              <li>• Emergency contacts receive SMS with your location</li>
              <li>• Automatically dials 108 (Ambulance Services)</li>
              <li>• Works even without internet (calls still work)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmergencySOS;
