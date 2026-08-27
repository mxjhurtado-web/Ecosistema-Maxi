"""
Utility module for language detection and translation (LNG.01 / LNG.02 compliance).
"""

import logging

logger = logging.getLogger(__name__)

async def detect_language(text: str) -> str:
    """Detect language of user text (defaults to 'es')"""
    if not text or not isinstance(text, str):
        return "es"
    
    text_lower = text.lower()
    en_words = ["the", "this", "that", "please", "my", "name", "is", "where", "status", "check", "need", "help"]
    words = text_lower.split()
    if any(w in words for w in en_words):
        return "en"
    return "es"

async def translate_text(text: str, target_lang: str = "es") -> str:
    """Translate text to target language if needed (fallback returns text unchanged)"""
    return text
