"""
Módulo de traducción automática de documentos.

Detecta el idioma y traduce a español usando Gemini.
"""

import os
from typing import Optional, Tuple
import re

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


def detect_language(text: str) -> str:
    """
    Detecta el idioma del texto.
    
    Args:
        text: Texto a analizar
        
    Returns:
        Código de idioma: 'es', 'en', 'pt', 'vi', etc.
    """
    if not text:
        return "unknown"
    
    text_lower = text.lower()
    
    # Detección simple por palabras clave
    # Español
    spanish_keywords = ['nombre', 'apellido', 'fecha', 'nacimiento', 'expedición', 'vencimiento']
    spanish_count = sum(1 for kw in spanish_keywords if kw in text_lower)
    
    # Inglés
    english_keywords = ['name', 'surname', 'date', 'birth', 'issue', 'expiration', 'license']
    english_count = sum(1 for kw in english_keywords if kw in text_lower)
    
    # Portugués
    portuguese_keywords = ['nome', 'sobrenome', 'data', 'nascimento', 'emissão', 'validade']
    portuguese_count = sum(1 for kw in portuguese_keywords if kw in text_lower)
    
    # Vietnamita
    vietnamese_keywords = ['họ', 'tên', 'ngày', 'sinh', 'cấp', 'hết hạn']
    vietnamese_count = sum(1 for kw in vietnamese_keywords if kw in text_lower)
    
    # Determinar idioma por mayor coincidencia
    counts = {
        'es': spanish_count,
        'en': english_count,
        'pt': portuguese_count,
        'vi': vietnamese_count
    }
    
    max_lang = max(counts, key=counts.get)
    
    # Si no hay suficientes coincidencias, retornar español por defecto
    if counts[max_lang] < 2:
        return 'es'
    
    return max_lang


def translate_to_spanish(
    text: str,
    source_lang: Optional[str] = None,
    api_key: Optional[str] = None
) -> Tuple[str, dict]:
    """
    Traduce texto a español usando Gemini.
    
    Args:
        text: Texto a traducir
        source_lang: Idioma origen (opcional, se detecta automáticamente)
        api_key: API key de Gemini (opcional si está en entorno)
        
    Returns:
        Tupla de (texto_traducido, metadata)
    """
    if not GEMINI_AVAILABLE:
        return text, {"error": "Gemini no disponible", "translated": False}
    
    # Detectar idioma si no se proporciona
    if not source_lang:
        source_lang = detect_language(text)
    
    # Si ya está en español, no traducir
    if source_lang == 'es':
        return text, {"source_lang": "es", "translated": False}
    
    # Configurar Gemini
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return text, {"error": "API key no disponible", "translated": False}
    
    genai.configure(api_key=api_key)
    
    # Prompt para traducción
    prompt = f"""
Traduce el siguiente texto de un documento de identificación al español.

INSTRUCCIONES:
1. Mantén el formato original (saltos de línea, espaciado)
2. Traduce SOLO el texto, no agregues explicaciones
3. Preserva EXACTAMENTE las fechas como aparecen (no las reformatees)
4. Preserva números de ID exactamente como aparecen
5. Traduce nombres de campos (NAME → NOMBRE, etc.)

Idioma origen: {source_lang.upper()}

Texto a traducir:
{text}

Traducción al español:
"""
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1, "top_p": 0.9},
            request_options={"timeout": 30}
        )
        
        if not response or not response.text:
            return text, {"error": "Gemini no devolvió respuesta", "translated": False}
        
        translated_text = response.text.strip()
        
        metadata = {
            "source_lang": source_lang,
            "target_lang": "es",
            "translated": True,
            "model": "gemini-1.5-flash"
        }
        
        return translated_text, metadata
        
    except Exception as e:
        return text, {"error": str(e), "translated": False}


def should_translate(text: str) -> bool:
    """
    Determina si un texto necesita traducción.
    
    Args:
        text: Texto a evaluar
        
    Returns:
        True si necesita traducción, False si ya está en español
    """
    lang = detect_language(text)
    return lang != 'es'
