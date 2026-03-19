from flask import current_app
import json
import re
import os
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

class SymptomAnalyzer:
    """Intelligent symptom analysis engine with multi-language support"""
    
    def __init__(self, symptoms_db_path=None):
        if symptoms_db_path is None:
            symptoms_db_path = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'symptoms.json'
            )
        self.symptoms_db_path = symptoms_db_path
        self.symptoms_data = self._load_symptoms()
        logger.info(f"SymptomAnalyzer initialized with {len(self.symptoms_data)} symptoms")
    
    def _load_symptoms(self):
        """Load symptoms database from JSON file"""
        try:
            with open(self.symptoms_db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                symptoms = data.get('symptoms', [])
                logger.info(f"Successfully loaded {len(symptoms)} symptoms from database")
                return symptoms
        except FileNotFoundError:
            logger.error(f"Symptoms file not found: {self.symptoms_db_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing symptoms JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading symptoms: {e}")
            return []
    
    def analyze(self, text, language='en'):
        """
        Main analysis function
        
        Args:
            text (str): User's symptom description
            language (str): Language code (en, ka, hi, ta)
        
        Returns:
            dict: {
                'urgency': 'HIGH/MEDIUM/LOW',
                'urgency_score': 1-10,
                'matched_symptoms': [],
                'specialties': [],
                'description': '',
                'first_aid': [],
                'red_flags': [],
                'symptom_details': []
            }
        """
        logger.info(f"Analyzing symptoms: '{text[:50]}...' (language: {language})")
        
        # Clean and prepare text
        cleaned_text = self._clean_text(text)
        
        if not cleaned_text:
            logger.warning("Empty text provided for analysis")
            return self._empty_result()
        
        # Use rule-based local analysis (no external API calls needed)
        logger.info("Performing local rule-based analysis...")
        
        # Match symptoms
        matched_symptoms = self._match_symptoms(cleaned_text, language)
        
        if not matched_symptoms:
            logger.info("No symptoms matched")
            return self._empty_result()
        
        logger.info(f"Matched {len(matched_symptoms)} symptoms")
        
        # Calculate urgency
        urgency, urgency_score = self._calculate_urgency(matched_symptoms)
        
        # Get recommended specialties
        specialties = self._get_specialties(matched_symptoms)
        
        # Generate description
        description = self._generate_description(matched_symptoms, urgency)
        
        # Collect first aid tips
        first_aid = self._collect_first_aid(matched_symptoms)
        
        # Collect red flags
        red_flags = self._collect_red_flags(matched_symptoms)
        
        result = {
            'urgency_level': urgency,
            'urgency_score': urgency_score,
            'matched_symptoms': matched_symptoms,
            'recommended_specialties': specialties,
            'recommendation': description,
            'first_aid_tips': first_aid,
            'red_flags': red_flags,
            'ai_powered': False,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Analysis complete: Urgency={urgency}, Score={urgency_score}, "
                   f"Symptoms={len(matched_symptoms)}, Specialties={specialties}")
        
        return result
    
    def _empty_result(self):
        """Return default result when no symptoms matched"""
        return {
            'urgency_level': 'LOW',
            'urgency_score': 1,
            'matched_symptoms': [],
            'recommended_specialties': ['General Medicine'],
            'recommendation': 'No specific symptoms identified. Please describe your symptoms in more detail or consult a general physician.',
            'first_aid_tips': ['Rest and monitor symptoms', 'Stay hydrated', 'Maintain a healthy diet'],
            'red_flags': [],
            'ai_powered': False,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _clean_text(self, text):
        """Clean and normalize input text"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove special characters but keep spaces and basic punctuation
        text = re.sub(r'[^\w\s,.]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove very short words (likely noise)
        words = text.split()
        words = [w for w in words if len(w) > 2 or w in ['i', 'a']]
        text = ' '.join(words)
        
        return text
    
    def _match_symptoms(self, text, language):
        """Match user input against symptom database"""
        matched = []
        text_lower = text.lower()
        
        for symptom in self.symptoms_data:
            match_score = 0
            matched_keywords = []
            
            # Check language-specific terms
            if language == 'kn' and 'kannada' in symptom:
                kannada_term = symptom['kannada'].lower()
                if kannada_term in text_lower:
                    match_score = 10
                    matched_keywords.append(kannada_term)
            elif language == 'hi' and 'hindi' in symptom:
                hindi_term = symptom['hindi'].lower()
                if hindi_term in text_lower:
                    match_score = 10
                    matched_keywords.append(hindi_term)
            elif language == 'ta' and 'tamil' in symptom:
                tamil_term = symptom['tamil'].lower()
                if tamil_term in text_lower:
                    match_score = 10
                    matched_keywords.append(tamil_term)
            
            # Check English keywords
            keywords = symptom.get('keywords', [])
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Exact word match (highest priority)
                word_pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                if re.search(word_pattern, text_lower):
                    match_score = max(match_score, 10)
                    matched_keywords.append(keyword)
                    break
                
                # Partial match
                elif keyword_lower in text_lower:
                    match_score = max(match_score, 7)
                    matched_keywords.append(keyword)
            
            # Add to matched if score > 0
            if match_score > 0:
                matched.append({
                    **symptom,
                    'match_score': match_score,
                    'matched_keywords': matched_keywords
                })
        
        # Remove duplicates based on symptom ID
        seen = set()
        unique_matched = []
        for s in matched:
            symptom_id = s.get('id', s.get('name'))
            if symptom_id not in seen:
                seen.add(symptom_id)
                unique_matched.append(s)
        
        # Sort by match score, then by urgency score
        unique_matched.sort(
            key=lambda x: (x['match_score'], x.get('urgency_score', 0)),
            reverse=True
        )
        
        return unique_matched
    
    def _calculate_urgency(self, matched_symptoms):
        """Calculate overall urgency level and score"""
        if not matched_symptoms:
            return 'LOW', 1
        
        # Get urgency scores
        urgency_scores = [s.get('urgency_score', 1) for s in matched_symptoms]
        max_urgency = max(urgency_scores)
        avg_urgency = sum(urgency_scores) / len(urgency_scores)
        
        # Count high urgency symptoms
        high_count = sum(1 for s in matched_symptoms if s.get('urgency') == 'HIGH')
        medium_count = sum(1 for s in matched_symptoms if s.get('urgency') == 'MEDIUM')
        
        # Decision logic
        # Multiple high urgency symptoms = definitely high
        if high_count >= 2:
            return 'HIGH', 10
        
        # Single high urgency symptom with high score
        if max_urgency >= 8:
            return 'HIGH', max_urgency
        
        # Multiple symptoms with medium-high urgency
        if len(matched_symptoms) >= 3 and avg_urgency >= 6:
            return 'HIGH', 8
        
        # Multiple medium urgency symptoms
        if medium_count >= 2 and max_urgency >= 6:
            return 'MEDIUM', 7
        
        # Medium urgency range
        if max_urgency >= 5:
            return 'MEDIUM', max_urgency
        
        # Medium urgency with multiple symptoms
        if len(matched_symptoms) >= 2 and avg_urgency >= 4:
            return 'MEDIUM', 5
        
        # Low urgency
        return 'LOW', max_urgency
    
    def _get_specialties(self, matched_symptoms):
        """Extract and prioritize medical specialties"""
        specialties_dict = {}
        
        for symptom in matched_symptoms:
            # Weight by match score and urgency
            weight = symptom.get('match_score', 1) * (1 + symptom.get('urgency_score', 1) / 10)
            
            for specialty in symptom.get('specialties', []):
                if specialty in specialties_dict:
                    specialties_dict[specialty] += weight
                else:
                    specialties_dict[specialty] = weight
        
        # Sort by weighted score
        sorted_specialties = sorted(
            specialties_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return top 3 specialties
        result = [s[0] for s in sorted_specialties[:3]]
        
        # Always include General Medicine if no specialties found
        if not result:
            result = ['General Medicine']
        
        return result
    
    def _generate_description(self, matched_symptoms, urgency):
        """Generate human-readable description"""
        if not matched_symptoms:
            return "No specific symptoms identified. Please consult a healthcare provider."
        
        # Urgency prefix
        if urgency == 'HIGH':
            prefix = "⚠️ URGENT: "
        elif urgency == 'MEDIUM':
            prefix = "⚡ Important: "
        else:
            prefix = "ℹ️ "
        
        # Get most severe symptom
        top_symptom = matched_symptoms[0]
        base_description = top_symptom.get('description', 'Medical attention may be needed.')
        
        # Add urgency-specific advice
        if urgency == 'HIGH':
            advice = " Please seek immediate medical attention or visit the emergency department."
        elif urgency == 'MEDIUM':
            advice = " It's advisable to see a doctor soon, preferably within 24-48 hours."
        else:
            advice = " Monitor your symptoms and consult a doctor if they persist or worsen."
        
        # Add symptom count if multiple
        if len(matched_symptoms) > 1:
            symptom_info = f" You have reported {len(matched_symptoms)} concerning symptoms."
        else:
            symptom_info = ""
        
        description = prefix + base_description + symptom_info + advice
        
        return description
    
    def _collect_first_aid(self, matched_symptoms):
        """Collect unique first aid tips"""
        tips = []
        seen = set()
        
        # Prioritize by urgency score
        sorted_symptoms = sorted(
            matched_symptoms,
            key=lambda x: x.get('urgency_score', 0),
            reverse=True
        )
        
        for symptom in sorted_symptoms:
            for tip in symptom.get('first_aid', []):
                if tip not in seen and tip:
                    seen.add(tip)
                    tips.append(tip)
                    if len(tips) >= 5:  # Max 5 tips
                        return tips
        
        # Add generic tips if needed
        if not tips:
            tips = [
                'Rest and avoid strenuous activity',
                'Stay hydrated with water',
                'Monitor your symptoms',
                'Avoid self-medication',
                'Seek medical advice if symptoms worsen'
            ]
        
        return tips[:5]
    
    def _collect_red_flags(self, matched_symptoms):
        """Collect red flag warnings"""
        flags = []
        seen = set()
        
        # Only collect from high urgency symptoms
        high_urgency_symptoms = [
            s for s in matched_symptoms 
            if s.get('urgency') == 'HIGH' or s.get('urgency_score', 0) >= 7
        ]
        
        for symptom in high_urgency_symptoms:
            for flag in symptom.get('red_flags', []):
                if flag not in seen and flag:
                    seen.add(flag)
                    flags.append(flag)
                    if len(flags) >= 5:  # Max 5 flags
                        return flags
        
        return flags[:5]
    
    def get_symptom_by_id(self, symptom_id):
        """Get detailed symptom information by ID"""
        for symptom in self.symptoms_data:
            if symptom.get('id') == symptom_id:
                return symptom
        return None
    
    def get_all_symptoms(self):
        """Get all symptoms in database"""
        return self.symptoms_data
    
    def search_symptoms(self, query, limit=10):
        """Search symptoms by keyword"""
        query_lower = query.lower()
        results = []
        
        for symptom in self.symptoms_data:
            # Check name
            if query_lower in symptom.get('name', '').lower():
                results.append(symptom)
                continue
            
            # Check keywords
            for keyword in symptom.get('keywords', []):
                if query_lower in keyword.lower():
                    results.append(symptom)
                    break
        
        return results[:limit]


# Global analyzer instance
symptom_analyzer = None

def get_symptom_analyzer():
    """Get or create symptom analyzer instance"""
    global symptom_analyzer
    if symptom_analyzer is None:
        symptom_analyzer = SymptomAnalyzer()
    return symptom_analyzer
