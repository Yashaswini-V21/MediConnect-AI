"""
Lightweight Sarvam AI integration wrapper.
Uses `SARVAM_API_KEY` and `SARVAM_API_URL` from environment.
Caller should handle exceptions and fall back to local translations.
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)

SARVAM_API_KEY = os.getenv('SARVAM_API_KEY')
SARVAM_API_URL = os.getenv('SARVAM_API_URL', 'https://api.sarvam.ai/v1/translate')

LANG_CODE_MAP = {
    'english': 'en', 'en': 'en',
    'kannada': 'kn', 'kn': 'kn',
    'hindi': 'hi', 'hi': 'hi',
    'tamil': 'ta', 'ta': 'ta',
}


def translate_via_sarvam(text: str, source: str = 'en', target: str = 'kn') -> str:
    """Call Sarvam API to translate text. Returns translated text or raises Exception."""
    if not SARVAM_API_KEY:
        raise RuntimeError('SARVAM_API_KEY not configured')

    payload = {
        'source': LANG_CODE_MAP.get(source.lower(), source.lower()),
        'target': LANG_CODE_MAP.get(target.lower(), target.lower()),
        'text': text
    }
    headers = {
        'Authorization': f'Bearer {SARVAM_API_KEY}',
        'Content-Type': 'application/json'
    }

    try:
        resp = requests.post(SARVAM_API_URL, json=payload, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        # Expect response like: { 'translated_text': '...' }
        if isinstance(data, dict) and 'translated_text' in data:
            return data['translated_text']
        # Fallback: try common shapes
        if isinstance(data, dict) and 'result' in data and 'text' in data['result']:
            return data['result']['text']
        logger.warning('Unexpected Sarvam response shape: %s', data)
        raise RuntimeError('Unexpected Sarvam response')
    except Exception as e:
        logger.exception('Sarvam translate failed: %s', e)
        raise
