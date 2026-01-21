# translation_utils.py
# Utilidades de traducción automática usando Gemini API
# Para Hades Lite 2.2

import requests
from typing import Tuple, Optional

# Timeout para operaciones de traducción
TRANSLATION_TIMEOUT = 20


def detect_language(text: str, api_key: str, model: str = "gemini-2.0-flash-exp", 
                   timeout: int = TRANSLATION_TIMEOUT) -> Tuple[str, float]:
    """
    Detecta el idioma del texto usando Gemini API.
    
    Args:
        text: Texto a analizar
        api_key: Gemini API key
        model: Modelo de Gemini a usar
        timeout: Timeout en segundos
    
    Returns:
        Tuple de (language_code, confidence)
        - language_code: Código ISO 639-1 (ej: 'es', 'en', 'pt', 'fr')
        - confidence: Nivel de confianza (0.0 - 1.0)
    
    Example:
        >>> lang, conf = detect_language("Hello world", api_key)
        >>> print(lang, conf)
        'en' 0.95
    """
    if not text or not api_key:
        return 'es', 0.0
    
    # Usar solo una muestra del texto para detección rápida
    sample = text[:500] if len(text) > 500 else text
    
    prompt = f"""Analyze the following text from an identity document. 
If the text is already primarily in Spanish (check labels and values), respond with 'es'.
If the values (names, addresses) are in another language or script, respond with that language code.

Text to analyze:
---
{sample}
---

Respond ONLY with the ISO 639-1 language code (e.g., 'en', 'es', 'pt', 'fr', 'ur', 'ar').
Language code:"""

Language code:"""
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.9,
                "maxOutputTokens": 10
            }
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(
            f"{url}?key={api_key}",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip().lower()
            
            # Limpiar resultado (puede venir con comillas o espacios)
            result = result.replace('"', '').replace("'", '').replace('.', '').strip()
            
            # Validar que sea un código de idioma válido (2 letras)
            if len(result) == 2 and result.isalpha():
                return result, 0.9
            
            # Mapeos comunes si el modelo responde el nombre del idioma
            if 'es' in result or 'spanish' in result or 'español' in result:
                return 'es', 0.8
            elif 'en' in result or 'english' in result or 'inglés' in result:
                return 'en', 0.8
            elif 'pt' in result or 'portuguese' in result or 'português' in result:
                return 'pt', 0.8
            elif 'fr' in result or 'french' in result or 'français' in result:
                return 'fr', 0.8
            elif 'ur' in result or 'urdu' in result:
                return 'ur', 0.8
            elif 'ar' in result or 'arabic' in result or 'árabe' in result:
                return 'ar', 0.8
            
            # Si tiene un código más largo (ej: zh-CN), tomar los primeros 2
            if len(result) > 2 and result[2] == '-' and len(result[:2]) == 2:
                return result[:2], 0.7
        
    except requests.Timeout:
        print("[Translation] Timeout detecting language")
    except requests.ConnectionError:
        print("[Translation] No connection for language detection")
    except Exception as e:
        print(f"[Translation] Error detecting language: {e}")
    
    # Fallback: asumir español si no se detectó nada claro
    return 'es', 0.5


def translate_to_target(text: str, source_lang: str, target_lang: str,
                       api_key: str, model: str = "gemini-2.0-flash-exp",
                       timeout: int = TRANSLATION_TIMEOUT) -> str:
    """
    Traduce texto al idioma de destino usando Gemini API.
    
    Args:
        text: Texto a traducir
        source_lang: Código de idioma origen (ej: 'en', 'pt', 'fr')
        target_lang: Código de idioma destino ('es' o 'en')
        api_key: Gemini API key
        model: Modelo de Gemini a usar
        timeout: Timeout en segundos
    
    Returns:
        Texto traducido
    
    Example:
        >>> translated = translate_to_target("Hello", "en", "es", api_key)
        >>> print(translated)
        'Hola'
    """
    if not text or not api_key:
        return text
    
    # Determinar idioma de destino en texto completo
    target_lang_name = {
        'es': 'español',
        'en': 'American English'
    }.get(target_lang, 'español')
    
    # Crear prompt según idioma de destino
    if target_lang == 'es':
        prompt = f"""Traduce el siguiente texto de un documento de identidad a español.

IMPORTANTE:
- Mantén el formato exacto (saltos de línea, estructura)
- Traduce los campos (ej: "Name" → "Nombre", "Date of Birth" → "Fecha de Nacimiento")
- NO traduzcas nombres propios, números de documento, o fechas
- Preserva los valores exactos

Texto original:
{text}

Traducción al español:"""
    else:  # en
        prompt = f"""Translate the following identity document text to American English.

IMPORTANT:
- Maintain exact formatting (line breaks, structure)
- Translate field names (e.g., "Nombre" → "Name", "Fecha de Nacimiento" → "Date of Birth")
- DO NOT translate proper names, document numbers, or dates
- Preserve exact values

Original text:
{text}

American English translation:"""
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.9,
                "maxOutputTokens": 2048
            }
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(
            f"{url}?key={api_key}",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            translated = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
            
            if translated:
                return translated
        
    except requests.Timeout:
        print("[Translation] Timeout translating text")
    except requests.ConnectionError:
        print("[Translation] No connection for translation")
    except Exception as e:
        print(f"[Translation] Error translating text: {e}")
    
    # Fallback: retornar texto original
    return text


def should_translate(detected_lang: str, target_lang: str) -> bool:
    """
    Determina si el texto necesita traducción.
    
    Args:
        detected_lang: Idioma detectado en el documento
        target_lang: Idioma de destino seleccionado por el usuario
    
    Returns:
        True si los idiomas son diferentes y se necesita traducción
    
    Example:
        >>> should_translate('en', 'es')
        True
        >>> should_translate('es', 'es')
        False
    """
    # Normalizar códigos de idioma
    lang_map = {
        'es': ['es', 'spa', 'spanish', 'español'],
        'en': ['en', 'eng', 'english', 'inglés']
    }
    
    detected_normalized = detected_lang.lower()
    
    # Verificar si el idioma detectado coincide con el idioma de destino
    for lang_code, variants in lang_map.items():
        if detected_normalized in variants and lang_code == target_lang:
            return False
    
    return True
