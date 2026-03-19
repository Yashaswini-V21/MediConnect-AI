/**
 * Healthcare AI Platform API Service
 * Unified interface for all AI features
 */

import api from './api';

const AI_BASE = '/ai';

export const aiPlatformApi = {
  // ===== DIAGNOSTIC ENDPOINTS =====
  
  /**
   * Analyze symptoms with full triage
   */
  async analyzeSymptoms(symptoms, age = null, language = 'en') {
    try {
      const response = await api.post(`${AI_BASE}/health/analyze`, {
        symptoms,
        age,
        language
      });
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      console.error('❌ Symptom analysis error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Analysis failed',
        status: error.response?.status || 500
      };
    }
  },

  /**
   * Quick emergency check
   */
  async checkEmergency(symptoms) {
    try {
      const response = await api.post(`${AI_BASE}/health/emergency-check`, {
        symptoms
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('❌ Emergency check error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Check failed'
      };
    }
  },

  // ===== VOICE ENDPOINTS =====

  /**
   * Start voice input capture
   */
  async startVoiceInput(language = 'en-US') {
    try {
      const response = await api.post(`${AI_BASE}/voice/start`, {
        language
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('❌ Voice start error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Voice start failed'
      };
    }
  },

  /**
   * Stop voice input
   */
  async stopVoiceInput() {
    try {
      const response = await api.post(`${AI_BASE}/voice/stop`, {});
      return {
        success: true,
        data: response.data,
        transcript: response.data?.transcript || ''
      };
    } catch (error) {
      console.error('❌ Voice stop error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Voice stop failed'
      };
    }
  },

  /**
   * Speak response
   */
  async speakResponse(text, language = 'en-US') {
    try {
      const response = await api.post(`${AI_BASE}/voice/speak`, {
        text,
        language
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('❌ Speak error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Speak failed'
      };
    }
  },

  /**
   * Stop current speech
   */
  async stopSpeech() {
    try {
      const response = await api.post(`${AI_BASE}/voice/stop-speech`, {});
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('❌ Stop speech error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Stop speech failed'
      };
    }
  },

  // ===== ROUTING ENDPOINTS =====

  /**
   * Find nearby hospitals
   */
  async findHospitals(userLat, userLng, urgency = 'MODERATE') {
    try {
      const response = await api.post(`${AI_BASE}/emergency/hospitals`, {
        user_lat: userLat,
        user_lng: userLng,
        urgency
      });
      return {
        success: true,
        data: response.data,
        hospitals: response.data?.hospitals || []
      };
    } catch (error) {
      console.error('❌ Hospital search error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Hospital search failed',
        hospitals: []
      };
    }
  },

  /**
   * Get route to hospital
   */
  async getRoute(userLat, userLng, hospitalId, mode = 'ambulance') {
    try {
      const response = await api.post(`${AI_BASE}/emergency/route`, {
        user_lat: userLat,
        user_lng: userLng,
        hospital_id: hospitalId,
        mode
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('❌ Route error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Route failed'
      };
    }
  },

  // ===== ANALYTICS ENDPOINTS =====

  /**
   * Get reliability dashboard
   */
  async getDashboard() {
    try {
      const response = await api.get(`${AI_BASE}/analytics/dashboard`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('❌ Dashboard error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Dashboard failed'
      };
    }
  },

  /**
   * Get daily metrics
   */
  async getMetrics(date = null) {
    try {
      const params = date ? `?date=${date}` : '';
      const response = await api.get(`${AI_BASE}/analytics/metrics${params}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('❌ Metrics error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Metrics failed'
      };
    }
  },

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await api.get(`${AI_BASE}/health`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('❌ Health check error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Health check failed'
      };
    }
  }
};

export default aiPlatformApi;
