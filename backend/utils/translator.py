"""Translation utilities for multi-language support"""

TRANSLATIONS = {
    'english': {
        'chest_pain': 'chest pain',
        'headache': 'headache',
        'fever': 'fever',
        'cough': 'cough',
        'breathing_difficulty': 'difficulty breathing'
    },
    'kannada': {
        'chest_pain': 'ಎದೆ ನೋವು',
        'headache': 'ತಲೆನೋವು',
        'fever': 'ಜ್ವರ',
        'cough': 'ಕೆಮ್ಮು',
        'breathing_difficulty': 'ಉಸಿರಾಟದ ತೊಂದರೆ'
    },
    'hindi': {
        'chest_pain': 'सीने में दर्द',
        'headache': 'सरदर्द',
        'fever': 'बुखार',
        'cough': 'खांसी',
        'breathing_difficulty': 'सांस लेने में कठिनाई'
    },
    'tamil': {
        'chest_pain': 'மார்பு வலி',
        'headache': 'தலைவலி',
        'fever': 'காய்ச்சல்',
        'cough': 'இருமல்',
        'breathing_difficulty': 'சுவாசிப்பதில் சிரமம்'
    }
}

def translate_text(text, from_lang='english', to_lang='kannada'):
    """
    Translate text between supported languages
    
    Args:
        text (str): Text to translate
        from_lang (str): Source language
        to_lang (str): Target language
    
    Returns:
        str: Translated text or original if not found
    """
    text_lower = text.lower().replace(' ', '_')
    
    # Find key in source language
    source_dict = TRANSLATIONS.get(from_lang, {})
    target_dict = TRANSLATIONS.get(to_lang, {})
    
    # Direct lookup
    if text_lower in source_dict.values():
        key = [k for k, v in source_dict.items() if v == text_lower]
        if key and key[0] in target_dict:
            return target_dict[key[0]]
    
    # Reverse lookup
    for key, value in source_dict.items():
        if value.lower() == text_lower:
            return target_dict.get(key, text)
    
    return text


# If an external Sarvam AI key is configured, prefer using the external service
try:
    from .sarvam import translate_via_sarvam, SARVAM_API_KEY  # type: ignore
except Exception:
    translate_via_sarvam = None
    SARVAM_API_KEY = None


def translate(text: str, from_lang: str = 'english', to_lang: str = 'kannada') -> str:
    """High-level translate that uses Sarvam when available, otherwise falls back to local table.

    Args:
        text: str
        from_lang: str
        to_lang: str

    Returns:
        str: translated text
    """
    # Map short codes to translator internal names
    lang_map = {
        'en': 'english', 'english': 'english',
        'kn': 'kannada', 'kannada': 'kannada',
        'hi': 'hindi', 'hindi': 'hindi',
        'ta': 'tamil', 'tamil': 'tamil'
    }

    src = lang_map.get(from_lang.lower(), from_lang.lower())
    tgt = lang_map.get(to_lang.lower(), to_lang.lower())

    # Prefer external API if configured
    if SARVAM_API_KEY and translate_via_sarvam:
        try:
                return translate_via_sarvam(text, source=src, target=tgt)
        except Exception:
            # Fall back to local translate on failure
            pass

    return translate_text(text, from_lang=src, to_lang=tgt)


def get_supported_languages():
    """Get list of supported languages"""
    return list(TRANSLATIONS.keys())

def detect_language(text):
    """
    Simple language detection based on character sets
    
    Args:
        text (str): Text to detect language
    
    Returns:
        str: Detected language code
    """
    # Kannada Unicode range
    if any('\u0C80' <= char <= '\u0CFF' for char in text):
        return 'kannada'
    
    # Devanagari (Hindi) Unicode range
    if any('\u0900' <= char <= '\u097F' for char in text):
        return 'hindi'
    
    # Tamil Unicode range
    if any('\u0B80' <= char <= '\u0BFF' for char in text):
        return 'tamil'
    
    # Default to English
    return 'english'
