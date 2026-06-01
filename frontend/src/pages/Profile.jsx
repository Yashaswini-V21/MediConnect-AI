import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { User, Mail, Calendar, Shield, Droplet, Target, FileText, Edit2, X, TrendingUp, Activity, Calculator, Heart, Brain, LogOut, Star, Clock } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import api from '../services/api';
import AppointmentsTab from '../components/profile/AppointmentsTab';

const Profile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [isEditing, setIsEditing] = useState(false);


  
  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };
  
  // BMI Calculator State (for Tools tab)
  const [bmiData, setBmiData] = useState({ height: '', weight: '', result: null });
  
  // Water Tracker State
  const [waterGoal] = useState(8);
  const [waterDrunk, setWaterDrunk] = useState(() => {
    const saved = localStorage.getItem('waterDrunk');
    return saved ? parseInt(saved) : 0;
  });

  // Health Goals State
  const [healthGoals, setHealthGoals] = useState(() => {
    const saved = localStorage.getItem('healthGoals');
    return saved ? JSON.parse(saved) : [
      { id: 1, title: 'Exercise 30 mins daily', completed: false, progress: 40 },
      { id: 2, title: 'Sleep 8 hours', completed: false, progress: 60 },
      { id: 3, title: 'Eat 5 servings of fruits', completed: false, progress: 30 }
    ];
  });

  // Medical Records State
  const [medicalRecords, setMedicalRecords] = useState(() => {
    const saved = localStorage.getItem('medicalRecords');
    return saved ? JSON.parse(saved) : [
      { id: 1, type: 'Blood Test', date: '2025-12-15', doctor: 'Dr. Sharma', result: 'Normal' },
      { id: 2, type: 'X-Ray', date: '2025-11-20', doctor: 'Dr. Patel', result: 'No issues' }
    ];
  });

  // Profile Info State
  const [profileInfo, setProfileInfo] = useState(() => {
    const saved = localStorage.getItem('profileInfo');
    if (saved) {
      return JSON.parse(saved);
    }
    return {
      fullName: user?.displayName || user?.email?.split('@')[0] || 'User',
      email: user?.email || '',
      age: '25',
      bloodGroup: 'O+',
      height: '170 cm',
      weight: '70 kg'
    };
  });

  // Save data to localStorage
  useEffect(() => {
    localStorage.setItem('profileInfo', JSON.stringify(profileInfo));
  }, [profileInfo]);

  useEffect(() => {
    localStorage.setItem('waterDrunk', waterDrunk.toString());
  }, [waterDrunk]);

  useEffect(() => {
    localStorage.setItem('healthGoals', JSON.stringify(healthGoals));
  }, [healthGoals]);

  useEffect(() => {
    localStorage.setItem('medicalRecords', JSON.stringify(medicalRecords));
  }, [medicalRecords]);

  // Water Tracker Functions
  const addWater = () => {
    if (waterDrunk < waterGoal) {
      const newCount = waterDrunk + 1;
      setWaterDrunk(newCount);
      if (newCount === waterGoal) {
        toast.success('🎉 Daily water goal achieved!');
      } else {
        toast.success('💧 Glass added!');
      }
    }
  };

  const resetWater = () => {
    setWaterDrunk(0);
    toast.success('Water tracker reset!');
  };

  // Health Goals Functions
  const toggleGoal = (id) => {
    setHealthGoals(goals =>
      goals.map(goal =>
        goal.id === id ? { ...goal, completed: !goal.completed } : goal
      )
    );
  };

  const addGoal = () => {
    const goalText = prompt('Enter your health goal:');
    if (goalText) {
      const newGoal = {
        id: Date.now(),
        title: goalText,
        completed: false,
        progress: 0
      };
      setHealthGoals([...healthGoals, newGoal]);
      toast.success('Goal added!');
    }
  };

  // Medical Records Functions
  const addRecord = () => {
    const type = prompt('Enter record type (e.g., Blood Test, X-Ray):');
    if (!type) return;
    
    const doctor = prompt('Enter doctor name:');
    if (!doctor) return;

    const newRecord = {
      id: Date.now(),
      type,
      date: new Date().toISOString().split('T')[0],
      doctor,
      result: 'Pending'
    };
    setMedicalRecords([newRecord, ...medicalRecords]);
    toast.success('Medical record added!');
  };

  const waterPercentage = (waterDrunk / waterGoal) * 100;
  const completedGoals = healthGoals.filter(g => g.completed).length;

  // BMI Calculator Function
  const calculateBMI = () => {
    const height = parseFloat(bmiData.height);
    const weight = parseFloat(bmiData.weight);
    
    if (!height || !weight || height <= 0 || weight <= 0) {
      toast.error('Please enter valid height and weight');
      return;
    }
    
    const heightInMeters = height / 100;
    const bmi = (weight / (heightInMeters * heightInMeters)).toFixed(1);
    
    let category = '';
    let color = '';
    let advice = '';
    
    if (bmi < 18.5) {
      category = 'Underweight';
      color = 'text-blue-600';
      advice = 'Consider consulting a nutritionist for a healthy weight gain plan.';
    } else if (bmi < 25) {
      category = 'Normal';
      color = 'text-green-600';
      advice = 'Great! Maintain your healthy lifestyle with balanced diet and exercise.';
    } else if (bmi < 30) {
      category = 'Overweight';
      color = 'text-orange-600';
      advice = 'Consider regular exercise and a balanced diet to reach a healthy weight.';
    } else {
      category = 'Obese';
      color = 'text-red-600';
      advice = 'Consult a healthcare professional for a personalized weight management plan.';
    }
    
    setBmiData({ ...bmiData, result: { bmi, category, color, advice } });
    toast.success('BMI calculated!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-900 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-6"
        >
          <div className="inline-block p-4 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full mb-4 shadow-xl">
            <User className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
            My Profile
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Manage your health information and track your wellness
          </p>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex gap-3 mb-6 overflow-x-auto pb-2"
        >
          {[
            { id: 'overview', label: 'Overview', icon: User },
            { id: 'appointments', label: 'My Appointments', icon: Calendar },
            { id: 'health', label: 'Health Tracking', icon: Activity },
            { id: 'tools', label: 'Health Tools', icon: Calculator },
            { id: 'records', label: 'Medical Records', icon: FileText }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-xl scale-105'
                    : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:shadow-lg hover:scale-105'
                }`}
              >
                <Icon className="w-5 h-5" />
                {tab.label}
              </button>
            );
          })}
        </motion.div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid lg:grid-cols-3 gap-6"
          >
            {/* Left Column - Profile Info */}
            <div className="lg:col-span-1 space-y-6">
            {/* Profile Card */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-xl border-2 border-purple-200 dark:border-purple-800"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Profile Info</h2>
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className="p-2 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors"
                >
                  {isEditing ? <X className="w-5 h-5" /> : <Edit2 className="w-5 h-5" />}
                </button>
              </div>

              <div className="flex flex-col items-center mb-6">
                <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center text-white text-4xl font-bold mb-3 shadow-lg">
                  {profileInfo.fullName.charAt(0).toUpperCase()}
                </div>
                {isEditing ? (
                  <input
                    type="text"
                    value={profileInfo.fullName}
                    onChange={(e) => setProfileInfo({...profileInfo, fullName: e.target.value})}
                    className="w-full px-3 py-2 rounded-lg border-2 border-purple-300 dark:border-purple-700 bg-white dark:bg-slate-700 text-center text-slate-900 dark:text-white font-bold text-xl"
                  />
                ) : (
                  <h3 className="text-2xl font-bold text-slate-900 dark:text-white">{profileInfo.fullName}</h3>
                )}
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                  <Mail className="w-5 h-5 text-purple-600" />
                  <div className="flex-1">
                    <p className="text-xs text-slate-500 dark:text-slate-400">Email</p>
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">{profileInfo.email}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                  <Calendar className="w-5 h-5 text-purple-600" />
                  <div className="flex-1">
                    <p className="text-xs text-slate-500 dark:text-slate-400">Age</p>
                    {isEditing ? (
                      <input
                        type="text"
                        value={profileInfo.age}
                        onChange={(e) => setProfileInfo({...profileInfo, age: e.target.value})}
                        className="w-full px-2 py-1 rounded border border-purple-300 dark:border-purple-700 bg-white dark:bg-slate-600 text-sm text-slate-900 dark:text-white"
                      />
                    ) : (
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">{profileInfo.age} years</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                  <Shield className="w-5 h-5 text-red-600" />
                  <div className="flex-1">
                    <p className="text-xs text-slate-500 dark:text-slate-400">Blood Group</p>
                    {isEditing ? (
                      <input
                        type="text"
                        value={profileInfo.bloodGroup}
                        onChange={(e) => setProfileInfo({...profileInfo, bloodGroup: e.target.value})}
                        className="w-full px-2 py-1 rounded border border-purple-300 dark:border-purple-700 bg-white dark:bg-slate-600 text-sm text-slate-900 dark:text-white"
                      />
                    ) : (
                      <p className="text-sm font-semibold text-red-600">{profileInfo.bloodGroup}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                    <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Height</p>
                    {isEditing ? (
                      <input
                        type="text"
                        value={profileInfo.height}
                        onChange={(e) => setProfileInfo({...profileInfo, height: e.target.value})}
                        className="w-full px-2 py-1 rounded border border-purple-300 dark:border-purple-700 bg-white dark:bg-slate-600 text-xs text-slate-900 dark:text-white"
                      />
                    ) : (
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">{profileInfo.height}</p>
                    )}
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-700 rounded-xl">
                    <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">Weight</p>
                    {isEditing ? (
                      <input
                        type="text"
                        value={profileInfo.weight}
                        onChange={(e) => setProfileInfo({...profileInfo, weight: e.target.value})}
                        className="w-full px-2 py-1 rounded border border-purple-300 dark:border-purple-700 bg-white dark:bg-slate-600 text-xs text-slate-900 dark:text-white"
                      />
                    ) : (
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">{profileInfo.weight}</p>
                    )}
                  </div>
                </div>
              </div>

              {isEditing && (
                <button
                  onClick={() => {
                    setIsEditing(false);
                    toast.success('Profile updated!');
                  }}
                  className="w-full mt-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-bold hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg"
                >
                  Save Changes
                </button>
              )}
              
              {/* Logout Button */}
              <button
                onClick={handleLogout}
                className="w-full mt-3 py-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl font-bold hover:bg-red-100 dark:hover:bg-red-900/30 transition-all border-2 border-red-200 dark:border-red-800 flex items-center justify-center gap-2"
              >
                <LogOut className="w-5 h-5" />
                Logout
              </button>
            </motion.div>

            {/* Stats Card */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl p-6 shadow-xl text-white"
            >
              <h3 className="text-lg font-bold mb-4">Health Stats</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Water Goal</span>
                  <span className="text-xl font-bold">{Math.round(waterPercentage)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Goals Completed</span>
                  <span className="text-xl font-bold">{completedGoals}/{healthGoals.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Medical Records</span>
                  <span className="text-xl font-bold">{medicalRecords.length}</span>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Right Column - Quick Actions */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-xl border-2 border-slate-200 dark:border-slate-700"
            >
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">Quick Actions</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <button
                  onClick={() => setActiveTab('health')}
                  className="p-6 bg-gradient-to-br from-green-100 to-emerald-100 dark:from-green-900/30 dark:to-emerald-900/30 rounded-xl hover:shadow-lg transition-all text-left"
                >
                  <Activity className="w-8 h-8 text-green-600 mb-3" />
                  <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Health Tracking</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Track water intake and health goals</p>
                </button>
                <button
                  onClick={() => setActiveTab('tools')}
                  className="p-6 bg-gradient-to-br from-blue-100 to-cyan-100 dark:from-blue-900/30 dark:to-cyan-900/30 rounded-xl hover:shadow-lg transition-all text-left"
                >
                  <Calculator className="w-8 h-8 text-blue-600 mb-3" />
                  <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Health Tools</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400">BMI, calories, heart rate calculators</p>
                </button>
                <button
                  onClick={() => setActiveTab('records')}
                  className="p-6 bg-gradient-to-br from-orange-100 to-red-100 dark:from-orange-900/30 dark:to-red-900/30 rounded-xl hover:shadow-lg transition-all text-left"
                >
                  <FileText className="w-8 h-8 text-orange-600 mb-3" />
                  <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Medical Records</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400">View and manage your health records</p>
                </button>
                <button
                  onClick={() => window.location.href = '/emergency'}
                  className="p-6 bg-gradient-to-br from-red-100 to-pink-100 dark:from-red-900/30 dark:to-pink-900/30 rounded-xl hover:shadow-lg transition-all text-left"
                >
                  <Heart className="w-8 h-8 text-red-600 mb-3" />
                  <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Emergency SOS</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Quick access to emergency services</p>
                </button>
              </div>
            </motion.div>
          </div>
        </motion.div>
        )}

        {/* My Appointments Tab */}
        {activeTab === 'appointments' && (
          <AppointmentsTab profileInfo={profileInfo} navigate={navigate} />
        )}

        {/* Health Tracking Tab */}
        {activeTab === 'health' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid lg:grid-cols-2 gap-6"
          >
            {/* Water Tracker */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-xl border-2 border-blue-200 dark:border-blue-800">
              <div className="flex items-center gap-3 mb-4">
                <Droplet className="w-8 h-8 text-blue-600" />
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Daily Water Intake</h2>
              </div>

              <div className="flex items-center justify-between mb-6">
                <div>
                  <div className="text-5xl font-bold text-blue-600">{waterDrunk}/{waterGoal}</div>
                  <p className="text-slate-600 dark:text-slate-400">Glasses Today</p>
                </div>
                <div className="text-6xl">💧</div>
              </div>

              <div className="mb-6">
                <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${waterPercentage}%` }}
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-end pr-2"
                  >
                    {waterPercentage > 10 && (
                      <span className="text-white font-bold text-sm">{Math.round(waterPercentage)}%</span>
                    )}
                  </motion.div>
                </div>
              </div>

              <div className="grid grid-cols-4 gap-3 mb-6">
                {[...Array(waterGoal)].map((_, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: idx * 0.05 }}
                    className={`aspect-square rounded-xl flex items-center justify-center text-3xl transition-all ${
                      idx < waterDrunk
                        ? 'bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg'
                        : 'bg-slate-100 dark:bg-slate-700'
                    }`}
                  >
                    💧
                  </motion.div>
                ))}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={addWater}
                  disabled={waterDrunk >= waterGoal}
                  className={`flex-1 py-3 rounded-xl font-bold transition-all ${
                    waterDrunk >= waterGoal
                      ? 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
                      : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white shadow-lg'
                  }`}
                >
                  {waterDrunk >= waterGoal ? '🎉 Goal Achieved!' : 'Add Glass 💧'}
                </button>
                <button
                  onClick={resetWater}
                  className="px-6 py-3 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl font-bold hover:bg-slate-300 dark:hover:bg-slate-600 transition-all"
                >
                  Reset
                </button>
              </div>
            </div>

            {/* Health Goals */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-xl border-2 border-green-200 dark:border-green-800">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Target className="w-8 h-8 text-green-600" />
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Health Goals</h2>
                </div>
                <button
                  onClick={addGoal}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors"
                >
                  + Add
                </button>
              </div>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {healthGoals.map((goal) => (
                  <motion.div
                    key={goal.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      goal.completed
                        ? 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-800'
                        : 'bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <button
                        onClick={() => toggleGoal(goal.id)}
                        className={`w-6 h-6 rounded-full border-2 flex-shrink-0 mt-0.5 transition-all ${
                          goal.completed
                            ? 'bg-green-600 border-green-600'
                            : 'border-slate-300 dark:border-slate-600 hover:border-green-600'
                        }`}
                      >
                        {goal.completed && <span className="text-white text-sm">✓</span>}
                      </button>
                      <div className="flex-1">
                        <p className={`font-semibold ${
                          goal.completed
                            ? 'text-green-700 dark:text-green-400 line-through'
                            : 'text-slate-900 dark:text-white'
                        }`}>
                          {goal.title}
                        </p>
                        {!goal.completed && (
                          <div className="mt-2">
                            <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400 mb-1">
                              <span>Progress</span>
                              <span>{goal.progress}%</span>
                            </div>
                            <div className="h-2 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-green-500 to-emerald-500"
                                style={{ width: `${goal.progress}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Health Tools Tab */}
        {activeTab === 'tools' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid lg:grid-cols-2 gap-6"
          >
            {/* BMI Calculator */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-xl border-2 border-cyan-200 dark:border-cyan-800">
              <div className="flex items-center gap-3 mb-6">
                <Calculator className="w-8 h-8 text-cyan-600" />
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">BMI Calculator</h2>
              </div>

              <div className="grid md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g., 170"
                    value={bmiData.height}
                    onChange={(e) => setBmiData({ ...bmiData, height: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:border-cyan-600 focus:outline-none"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Weight (kg)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g., 70"
                    value={bmiData.weight}
                    onChange={(e) => setBmiData({ ...bmiData, weight: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:border-cyan-600 focus:outline-none"
                  />
                </div>
              </div>

              <button
                onClick={calculateBMI}
                className="w-full py-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white font-bold rounded-xl transition-all shadow-xl mb-6"
              >
                Calculate BMI
              </button>

              {bmiData.result && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="p-6 bg-gradient-to-br from-cyan-50 to-blue-50 dark:from-cyan-900/20 dark:to-blue-900/20 rounded-2xl border-2 border-cyan-200 dark:border-cyan-800"
                >
                  <div className="text-center mb-4">
                    <div className="text-6xl font-bold text-cyan-600 mb-2">{bmiData.result.bmi}</div>
                    <div className={`text-2xl font-bold ${bmiData.result.color} mb-4`}>
                      {bmiData.result.category}
                    </div>
                  </div>
                  
                  <p className="text-slate-600 dark:text-slate-400 text-center text-sm">
                    {bmiData.result.advice}
                  </p>
                </motion.div>
              )}
            </div>

            {/* Heart Rate Zone Calculator */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-xl border-2 border-pink-200 dark:border-pink-800">
              <div className="flex items-center gap-3 mb-6">
                <Heart className="w-8 h-8 text-pink-600" />
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Heart Rate Zones</h2>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Your Age
                </label>
                <input
                  type="number"
                  placeholder="e.g., 25"
                  defaultValue={profileInfo.age}
                  className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:border-pink-600 focus:outline-none"
                  onChange={(e) => {
                    const age = parseInt(e.target.value);
                    if (age > 0 && age < 120) {
                      const maxHR = 220 - age;
                      document.getElementById('maxHR').innerText = maxHR;
                      document.getElementById('zone1').innerText = `${Math.round(maxHR * 0.5)}-${Math.round(maxHR * 0.6)}`;
                      document.getElementById('zone2').innerText = `${Math.round(maxHR * 0.6)}-${Math.round(maxHR * 0.7)}`;
                      document.getElementById('zone3').innerText = `${Math.round(maxHR * 0.7)}-${Math.round(maxHR * 0.8)}`;
                      document.getElementById('zone4').innerText = `${Math.round(maxHR * 0.8)}-${Math.round(maxHR * 0.9)}`;
                    }
                  }}
                />
              </div>

              <div className="space-y-3">
                <div className="p-4 bg-blue-100 dark:bg-blue-900/30 rounded-xl">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-blue-700 dark:text-blue-400">Max Heart Rate</span>
                    <span className="text-lg font-bold text-blue-700 dark:text-blue-400" id="maxHR">
                      {220 - parseInt(profileInfo.age || 25)}
                    </span>
                  </div>
                  <p className="text-xs text-blue-600 dark:text-blue-400">bpm</p>
                </div>

                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-xl">
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold text-green-700 dark:text-green-400">💚 Zone 1 - Warm Up</span>
                    <span className="font-bold text-green-700 dark:text-green-400" id="zone1">
                      {Math.round((220 - parseInt(profileInfo.age || 25)) * 0.5)}-{Math.round((220 - parseInt(profileInfo.age || 25)) * 0.6)}
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-yellow-100 dark:bg-yellow-900/30 rounded-xl">
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold text-yellow-700 dark:text-yellow-400">💛 Zone 2 - Fat Burn</span>
                    <span className="font-bold text-yellow-700 dark:text-yellow-400" id="zone2">
                      {Math.round((220 - parseInt(profileInfo.age || 25)) * 0.6)}-{Math.round((220 - parseInt(profileInfo.age || 25)) * 0.7)}
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-xl">
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold text-orange-700 dark:text-orange-400">🧡 Zone 3 - Cardio</span>
                    <span className="font-bold text-orange-700 dark:text-orange-400" id="zone3">
                      {Math.round((220 - parseInt(profileInfo.age || 25)) * 0.7)}-{Math.round((220 - parseInt(profileInfo.age || 25)) * 0.8)}
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-xl">
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold text-red-700 dark:text-red-400">❤️ Zone 4 - Peak</span>
                    <span className="font-bold text-red-700 dark:text-red-400" id="zone4">
                      {Math.round((220 - parseInt(profileInfo.age || 25)) * 0.8)}-{Math.round((220 - parseInt(profileInfo.age || 25)) * 0.9)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Calorie Calculator */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-xl border-2 border-orange-200 dark:border-orange-800">
              <div className="flex items-center gap-3 mb-6">
                <TrendingUp className="w-8 h-8 text-orange-600" />
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Daily Calorie Needs</h2>
              </div>

              <div className="text-center p-6 bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 rounded-2xl mb-4">
                <div className="text-5xl font-bold text-orange-600 mb-2">
                  {(() => {
                    const weight = parseFloat(profileInfo.weight) || 70;
                    const height = parseFloat(profileInfo.height) || 170;
                    const age = parseInt(profileInfo.age) || 25;
                    // Mifflin-St Jeor Equation (assuming male)
                    const bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5;
                    const tdee = Math.round(bmr * 1.55); // Moderate activity
                    return tdee;
                  })()}
                </div>
                <p className="text-lg font-semibold text-orange-700 dark:text-orange-400">Calories/Day</p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">Moderate activity level</p>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-sm text-slate-700 dark:text-slate-300">Weight Loss</span>
                  <span className="font-bold text-blue-600">
                    {(() => {
                      const weight = parseFloat(profileInfo.weight) || 70;
                      const height = parseFloat(profileInfo.height) || 170;
                      const age = parseInt(profileInfo.age) || 25;
                      const bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5;
                      return Math.round(bmr * 1.55 - 500);
                    })()} cal
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-sm text-slate-700 dark:text-slate-300">Maintain Weight</span>
                  <span className="font-bold text-green-600">
                    {(() => {
                      const weight = parseFloat(profileInfo.weight) || 70;
                      const height = parseFloat(profileInfo.height) || 170;
                      const age = parseInt(profileInfo.age) || 25;
                      const bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5;
                      return Math.round(bmr * 1.55);
                    })()} cal
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <span className="text-sm text-slate-700 dark:text-slate-300">Weight Gain</span>
                  <span className="font-bold text-orange-600">
                    {(() => {
                      const weight = parseFloat(profileInfo.weight) || 70;
                      const height = parseFloat(profileInfo.height) || 170;
                      const age = parseInt(profileInfo.age) || 25;
                      const bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5;
                      return Math.round(bmr * 1.55 + 500);
                    })()} cal
                  </span>
                </div>
              </div>
            </div>

            {/* Ideal Weight Calculator */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-xl border-2 border-purple-200 dark:border-purple-800">
              <div className="flex items-center gap-3 mb-6">
                <Brain className="w-8 h-8 text-purple-600" />
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Ideal Weight Range</h2>
              </div>

              <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-2xl mb-4">
                <div className="text-4xl font-bold text-purple-600 mb-2">
                  {(() => {
                    const height = parseFloat(profileInfo.height) || 170;
                    const heightM = height / 100;
                    const minWeight = (18.5 * heightM * heightM).toFixed(1);
                    const maxWeight = (24.9 * heightM * heightM).toFixed(1);
                    return `${minWeight} - ${maxWeight}`;
                  })()} kg
                </div>
                <p className="text-lg font-semibold text-purple-700 dark:text-purple-400">Healthy Range</p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">Based on your height</p>
              </div>

              <div className="space-y-3">
                <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-xl">
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">Current Weight</span>
                    <span className="text-lg font-bold text-purple-600">{profileInfo.weight}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">Current Height</span>
                    <span className="text-lg font-bold text-purple-600">{profileInfo.height}</span>
                  </div>
                </div>

                <div className="p-4 bg-gradient-to-r from-purple-100 to-pink-100 dark:from-purple-900/30 dark:to-pink-900/30 rounded-xl">
                  <p className="text-xs text-slate-700 dark:text-slate-300 mb-2">💡 <strong>Tip:</strong></p>
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    Maintaining a healthy weight reduces risk of chronic diseases and improves overall well-being.
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Medical Records Tab */}
        {activeTab === 'records' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-xl border-2 border-orange-200 dark:border-orange-800"
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <FileText className="w-8 h-8 text-orange-600" />
                <h2 className="text-3xl font-bold text-slate-900 dark:text-white">Medical Records</h2>
              </div>
              <button
                onClick={addRecord}
                className="px-6 py-3 bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-xl font-semibold hover:from-orange-700 hover:to-red-700 transition-colors shadow-lg"
              >
                + Add Record
              </button>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {medicalRecords.map((record) => (
                <motion.div
                  key={record.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-5 bg-gradient-to-br from-slate-50 to-orange-50 dark:from-slate-700 dark:to-orange-900/20 rounded-xl border-2 border-slate-200 dark:border-slate-600 hover:shadow-lg transition-all"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-12 h-12 bg-orange-600 rounded-full flex items-center justify-center text-white text-xl">
                      📋
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      record.result === 'Normal' || record.result === 'No issues'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                    }`}>
                      {record.result}
                    </span>
                  </div>
                  <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">{record.type}</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">
                    <strong>Doctor:</strong> {record.doctor}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-500">
                    <strong>Date:</strong> {record.date}
                  </p>
                </motion.div>
              ))}
            </div>

            {medicalRecords.length === 0 && (
              <div className="text-center py-12">
                <FileText className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
                <p className="text-lg text-slate-600 dark:text-slate-400">No medical records yet</p>
                <p className="text-sm text-slate-500 dark:text-slate-500">Click "Add Record" to get started</p>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Profile;
