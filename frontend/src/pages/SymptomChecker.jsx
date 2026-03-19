import React, { useState, useContext } from 'react';
import { motion } from 'framer-motion';
import { Send, AlertCircle, Plus, X, History, Shield, Globe } from 'lucide-react';
import aiPlatformApi from '../services/aiPlatformApi';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import VoiceInput from '../components/features/VoiceInput';
import HealthReportGenerator from '../components/features/HealthReportGenerator';
import { storageService } from '../services/storage';
import { LanguageContext } from '../context/LanguageContext';
import toast from 'react-hot-toast';

const SymptomChecker = () => {
  const { language, toggleLanguage } = useContext(LanguageContext);
  const [symptoms, setSymptoms] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedChips, setSelectedChips] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [symptomHistory, setSymptomHistory] = useState([]);

  // Common symptoms for quick selection
  const commonSymptoms = [
    '😷 Fever', '🤕 Headache', '🤧 Cough', '🌡️ Cold', 
    '😫 Body Pain', '🤢 Nausea', '😵 Dizziness', '😮‍💨 Breathing Difficulty',
    '💔 Chest Pain', '🤒 Sore Throat', '😴 Fatigue', '🤮 Vomiting'
  ];

  const toggleChip = (chip) => {
    if (selectedChips.includes(chip)) {
      setSelectedChips(selectedChips.filter(c => c !== chip));
    } else {
      setSelectedChips([...selectedChips, chip]);
    }
  };

  // Load symptom history on mount
  React.useEffect(() => {
    const history = JSON.parse(localStorage.getItem('symptomHistory') || '[]');
    setSymptomHistory(history.slice(0, 5)); // Show last 5
  }, []);

  const saveToHistory = (symptoms, analysis) => {
    const history = JSON.parse(localStorage.getItem('symptomHistory') || '[]');
    history.unshift({
      symptoms,
      analysis: analysis.possible_conditions?.[0] || 'General checkup',
      date: new Date().toISOString(),
      id: Date.now()
    });
    localStorage.setItem('symptomHistory', JSON.stringify(history.slice(0, 10))); // Keep last 10
    setSymptomHistory(history.slice(0, 5));
  };

  const handleAnalyze = async () => {
    const fullSymptoms = selectedChips.length > 0 
      ? `${selectedChips.join(', ')}. ${symptoms}`.trim()
      : symptoms;

    if (!fullSymptoms.trim()) {
      toast.error('Please describe your symptoms');
      return;
    }

    setLoading(true);
    try {
      // Use new AI Platform backend API
      const result = await aiPlatformApi.analyzeSymptoms(fullSymptoms, null, language);
      
      if (result.success && result.data.analysis) {
        setAnalysis(result.data.analysis);
        
        // Save to search history
        storageService.addToSearchHistory({
          symptoms: fullSymptoms,
          type: 'symptom',
          result: result.data.analysis,
          timestamp: new Date().toISOString(),
        });
        
        toast.success('✅ Analysis complete! Check the results below.');
      } else {
        toast.error(result.error || 'Analysis failed');
      }
    } catch (error) {
      console.error('Symptom analysis error:', error);
      toast.error('Failed to analyze symptoms. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-12 min-h-screen">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl mx-auto"
      >
        {/* Header - Glass Effect */}
        <div className="text-center mb-10">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 200 }}
            className="w-20 h-20 bg-purple-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-lg"
          >
            <AlertCircle className="w-10 h-10 text-white" />
          </motion.div>
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 dark:text-white mb-4">
            🩺 Symptom Checker
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-300 font-medium">
            Describe your symptoms and get instant AI-powered analysis
          </p>
          
          {/* Doctor Image */}
          <div className="mt-8 max-w-md mx-auto">
            <img 
              src="/assets/about-doctors.jpg" 
              alt="Medical professionals" 
              className="rounded-2xl shadow-lg w-full h-48 object-cover"
            />
          </div>
        </div>

        {/* Quick Symptom Chips - Premium Cards */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-lg mb-8 border border-slate-200 dark:border-slate-700"
        >
          <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-6 flex items-center gap-3">
            <Plus className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            Quick Select Common Symptoms
          </h3>
          <div className="flex flex-wrap gap-3">
            {commonSymptoms.map((symptom, idx) => (
              <motion.button
                key={idx}
                whileHover={{ scale: 1.1, rotate: 2 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => toggleChip(symptom)}
                className={`px-6 py-3 rounded-2xl text-base font-bold transition-all shadow-lg ${
                  selectedChips.includes(symptom)
                    ? 'bg-purple-600 text-white shadow-lg'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                }`}
              >
                {symptom}
                {selectedChips.includes(symptom) && (
                  <X className="inline-block w-3 h-3 ml-1" />
                )}
              </motion.button>
            ))}
          </div>
          {selectedChips.length > 0 && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-4 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800"
            >
              <p className="text-sm text-purple-700 dark:text-purple-300">
                Selected: <strong>{selectedChips.join(', ')}</strong>
              </p>
            </motion.div>
          )}
        </motion.div>

        {/* Input Card - Simplified (Voice Removed) */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-lg mb-6 border border-slate-200 dark:border-slate-700"
        >
          <div className="flex items-center justify-between mb-4">
            <label className="block text-lg font-semibold text-gray-900 dark:text-white">
              Describe Your Symptoms
            </label>
            
            {/* Health History Button */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-all"
            >
              <History className="w-4 h-4" />
              <span className="text-sm font-semibold">History</span>
            </button>
          </div>

          {/* Symptom History Dropdown */}
          {showHistory && symptomHistory.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl border-2 border-purple-200 dark:border-purple-800"
            >
              <h4 className="font-semibold text-purple-900 dark:text-purple-300 mb-3 flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Recent Health Records
              </h4>
              <div className="space-y-2">
                {symptomHistory.map((record) => (
                  <button
                    key={record.id}
                    onClick={() => setSymptoms(record.symptoms)}
                    className="w-full text-left p-3 bg-white dark:bg-slate-700 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-all border border-purple-200 dark:border-purple-700"
                  >
                    <div className="text-sm font-semibold text-slate-900 dark:text-white">{record.analysis}</div>
                    <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                      {new Date(record.date).toLocaleDateString()}
                    </div>
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          <div className="relative">
            <textarea
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              placeholder={language === 'kannada' 
                ? "ಉದಾ: ನನಗೆ 2 ದಿನಗಳಿಂದ ತಲೆನೋವು ಇದೆ, ಬೆಳಿಗ್ಗೆ ಹೆಚ್ಚು ಆಗುತ್ತದೆ..." 
                : "E.g., I have a headache for 2 days, it gets worse in the morning..."}
              className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:border-purple-600 focus:ring-2 focus:ring-purple-200 transition min-h-[120px] resize-none pr-28"
            />
            {/* Language Toggle & Voice Input Buttons */}
            <div className="absolute bottom-3 right-3 flex gap-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={toggleLanguage}
                className="p-3 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg hover:shadow-xl transition-all"
                title={`Switch to ${language === 'english' ? 'Kannada' : 'English'}`}
              >
                <Globe className="w-5 h-5" />
              </motion.button>
              <VoiceInput 
                onTranscript={(text) => setSymptoms(symptoms + ' ' + text)}
                className="shadow-lg"
              />
            </div>
          </div>

          <div className="flex justify-between items-center mt-4">
            <div className="flex items-center gap-3">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {selectedChips.length > 0 ? `✓ ${selectedChips.length} symptom(s) selected` : 'Select symptoms or type/speak'}
              </p>
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs font-semibold rounded-full">
                {language === 'kannada' ? '🇮🇳 ಕನ್ನಡ' : '🇬🇧 English'}
              </span>
            </div>
            <Button
              variant="primary"
              onClick={handleAnalyze}
              disabled={loading || (selectedChips.length === 0 && !symptoms.trim())}
              icon={Send}
              className="px-6 py-3"
            >
              {loading ? 'Analyzing...' : 'Analyze Symptoms'}
            </Button>
          </div>
        </motion.div>

        {/* Results */}
        {loading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner text="Analyzing your symptoms..." />
          </div>
        )}

        {analysis && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Urgency Alert */}
            <motion.div 
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              className={`bg-white rounded-2xl p-6 shadow-lg border-l-4 ${
                analysis.urgency_level === 'HIGH' ? 'border-red-500 bg-red-50' :
                analysis.urgency_level === 'MEDIUM' ? 'border-yellow-500 bg-yellow-50' :
                'border-green-500 bg-green-50'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  analysis.urgency_level === 'HIGH' ? 'bg-red-100' :
                  analysis.urgency_level === 'MEDIUM' ? 'bg-yellow-100' :
                  'bg-green-100'
                }`}>
                  <AlertCircle className={`w-6 h-6 ${
                    analysis.urgency_level === 'HIGH' ? 'text-red-600' :
                    analysis.urgency_level === 'MEDIUM' ? 'text-yellow-600' :
                    'text-green-600'
                  }`} />
                </div>
                <div className="flex-1">
                  <h3 className={`text-2xl font-bold mb-2 ${
                    analysis.urgency_level === 'HIGH' ? 'text-red-900' :
                    analysis.urgency_level === 'MEDIUM' ? 'text-yellow-900' :
                    'text-green-900'
                  }`}>
                    {analysis.urgency_level} Priority
                  </h3>
                  <p className="text-gray-700 text-lg">{analysis.recommendation}</p>
                </div>
              </div>
            </motion.div>

            {/* Matched Symptoms */}
            {analysis.matched_symptoms?.length > 0 && (
              <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-white rounded-2xl p-6 shadow-lg"
              >
                <h3 className="text-xl font-bold mb-4 text-gray-900">Matched Symptoms</h3>
                <div className="space-y-2">
                  {analysis.matched_symptoms.map((symptom, idx) => (
                    <motion.div 
                      key={idx}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className="flex justify-between items-center p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl hover:shadow-md transition"
                    >
                      <span className="font-medium text-gray-900">{symptom.name}</span>
                      <span className="px-3 py-1 bg-primary-500 text-white rounded-full text-sm font-medium">
                        {symptom.specialty}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* First Aid */}
            {analysis.first_aid_tips?.length > 0 && (
              <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-white rounded-2xl p-6 shadow-lg"
              >
                <h3 className="text-xl font-bold mb-4 text-gray-900">First Aid Tips</h3>
                <ul className="space-y-3">
                  {analysis.first_aid_tips.map((tip, idx) => (
                    <motion.li 
                      key={idx}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className="flex items-start gap-3 p-3 bg-green-50 rounded-lg"
                    >
                      <span className="text-green-600 font-bold text-xl">✓</span>
                      <span className="text-gray-700">{tip}</span>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            )}

            {/* Recommended Specialties */}
            {analysis.recommended_specialties?.length > 0 && (
              <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-white rounded-2xl p-6 shadow-lg"
              >
                <h3 className="text-xl font-bold mb-4 text-gray-900">Recommended Specialists</h3>
                <div className="flex flex-wrap gap-3">
                  {analysis.recommended_specialties.map((specialty, idx) => (
                    <motion.span 
                      key={idx}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: idx * 0.1 }}
                      whileHover={{ scale: 1.05 }}
                      className="px-5 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-full text-sm font-medium shadow-lg hover:shadow-xl transition cursor-pointer"
                    >
                      {specialty}
                    </motion.span>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Health Report Generator */}
            <HealthReportGenerator 
              analysis={analysis} 
              symptoms={selectedChips.length > 0 
                ? `${selectedChips.join(', ')}. ${symptoms}`.trim()
                : symptoms
              }
            />
          </motion.div>
        )}
      </motion.div>
    </div>
  );
};

export default SymptomChecker;
