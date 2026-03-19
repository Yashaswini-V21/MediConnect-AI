"""
Rule-Based AI Provider (Fallback)
No external API calls - pure local logic for symptom analysis and health advice
"""

import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class RuleBasedProvider:
    """Rule-based health advice and symptom analysis (no external APIs)"""
    
    HEALTH_ADVICE_RESPONSES = {
        'greeting': {
            'keywords': ['hello', 'hi', 'hey', 'hii', 'helo'],
            'response': "Hello! 👋 I'm your AI Health Assistant. I can help you with:\n• Understanding symptoms\n• General health advice\n• When to see a doctor\n• Basic first aid\n\nWhat's concerning you today?"
        },
        'kannada': {
            'keywords': ['kannada', 'kannaad', 'ಕನ್ನಡ', 'kannda'],
            'response': "Sure! I can help you in Kannada. Please switch the language using the language toggle (🌐 button) in the top header. After switching, I'll automatically respond in Kannada. How can I assist you?"
        },
        'headache': {
            'keywords': ['headache', 'head pain', 'migraine', 'head ache'],
            'response': "**Headache Relief:**\n• Rest in a quiet, dark room\n• Drink plenty of water (dehydration is common)\n• Apply cold compress to forehead\n• Avoid screens and bright lights\n• Try gentle neck stretches\n\n⚠️ **See a doctor if:** Severe sudden headache, with fever/stiff neck, or persistent (>3 days)"
        },
        'fever': {
            'keywords': ['fever', 'temperature', 'hot', 'burning'],
            'response': "**Fever Care:**\n• Rest and stay hydrated (water, ORS, clear fluids)\n• Take temperature regularly\n• Light clothing and cool room\n• Lukewarm sponge bath if needed\n• Paracetamol can help (follow dosage)\n\n⚠️ **Seek medical help if:** Fever >101°F for >3 days, with severe symptoms, or infants <3 months"
        },
        'chest_pain': {
            'keywords': ['chest pain', 'chest', 'heart'],
            'response': "⚠️ **CHEST PAIN IS SERIOUS!**\n\n🚨 **Call 108 IMMEDIATELY if:**\n- Crushing/squeezing chest pain\n- Pain spreading to arm, jaw, or back\n- Shortness of breath\n- Sweating, nausea, dizziness\n\n**For mild discomfort:** Rest and see doctor today"
        },
        'breathing': {
            'keywords': ['breath', 'breathing', 'asthma', 'wheez'],
            'response': "🚨 **BREATHING DIFFICULTY - URGENT!**\n\n**Call 108 immediately if:**\n- Severe difficulty, blue lips/fingernails\n- Unable to speak full sentences\n- Chest tightness\n\n**For mild breathlessness:** Sit upright, breathe slowly, use inhaler if prescribed"
        },
        'emergency': {
            'keywords': ['emergency', 'urgent', '108', 'ambulance', 'serious'],
            'response': "🚨 **FOR EMERGENCIES:**\n\n📞 **Call 108** (India Emergency)\n\n**When to call:** Severe chest/breathing issues, unconsciousness, severe bleeding, suspected heart attack/stroke, severe allergic reaction, poisoning, major injury\n\n⏱️ **Time is critical - don't delay!**"
        }
    }
    
    def get_health_advice(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Get health advice using rule-based matching"""
        message_lower = message.lower()
        
        for category, data in self.HEALTH_ADVICE_RESPONSES.items():
            if any(keyword in message_lower for keyword in data['keywords']):
                logger.info(f"Rule-based match: {category}")
                return data['response']
        
        # Default response
        logger.info("Rule-based: using default response")
        return "I'm here to help with your health questions! You can ask me about:\n\n🤒 Symptoms (fever, headache, cough, stomach issues)\n💊 Conditions (diabetes, blood pressure, general health)\n🚨 When to see a doctor or call emergency services\n🏥 Self-care tips and home remedies\n\nWhat would you like to know?"
    
    def analyze_symptoms(self, symptoms_text: str) -> Dict[str, Any]:
        """Analyze symptoms using simple rule-based logic"""
        logger.info(f"Rule-based analyzing: {symptoms_text[:50]}...")
        
        severity_keywords = {
            'HIGH': ['chest', 'heart', 'breathing', 'difficulty', 'severe', 'emergency', 'unconscious', 'bleeding', 'stroke'],
            'MEDIUM': ['fever', 'pain', 'nausea', 'vomit', 'dizzy', 'weakness', 'severe'],
            'LOW': ['cold', 'cough', 'headache', 'tired', 'minor', 'slight']
        }
        
        text_lower = symptoms_text.lower()
        
        # Determine urgency
        urgency = 'LOW'
        for level in ['HIGH', 'MEDIUM', 'LOW']:
            if any(keyword in text_lower for keyword in severity_keywords[level]):
                urgency = level
                if level == 'HIGH':
                    break
        
        # Map to specialties
        specialty_map = {
            'chest': 'Cardiologist',
            'heart': 'Cardiologist',
            'breathing': 'Pulmonologist',
            'fever': 'General Physician',
            'headache': 'Neurologist',
            'stomach': 'Gastroenterologist',
            'pain': 'General Physician',
            'skin': 'Dermatologist',
            'mental': 'Psychiatrist',
        }
        
        specialties = []
        for keyword, specialty in specialty_map.items():
            if keyword in text_lower and specialty not in specialties:
                specialties.append(specialty)
        
        if not specialties:
            specialties = ['General Physician']
        
        return {
            'urgency': urgency,
            'specialties': specialties[:3],
            'explanation': f"Based on your symptoms, this appears to be a {urgency.lower()} priority issue. Please consult with a healthcare professional for proper evaluation."
        }

