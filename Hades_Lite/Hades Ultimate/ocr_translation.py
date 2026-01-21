# ocr_translation.py
# Wrapper para agregar traducción automática al OCR de Hades Lite
# Traduce automáticamente documentos en otros idiomas al español

from typing import Tuple, Optional
import sys

# Intentar importar translation_utils
try:
    from translation_utils import detect_language, translate_to_target, should_translate
    _TRANSLATION_OK = True
except:
    _TRANSLATION_OK = False
    print("[OCR Translation] Módulo translation_utils no disponible")


def process_ocr_with_translation(ocr_text: str, api_key: str) -> Tuple[str, dict]:
    """
    Procesa texto OCR y lo traduce al español si es necesario.
    
    Args:
        ocr_text: Texto extraído por OCR
        api_key: Gemini API key para traducción
    
    Returns:
        Tuple de (texto_final, metadata)
        - texto_final: Texto en español (original o traducido)
        - metadata: Dict con información de traducción
            {
                'idioma_detectado': str,
                'fue_traducido': bool,
                'texto_original': str (solo si fue traducido),
                'confianza': float
            }
    """
    if not ocr_text or not api_key or not _TRANSLATION_OK:
        return ocr_text, {
            'idioma_detectado': 'es',
            'fue_traducido': False,
            'texto_original': None,
            'confianza': 0.0
        }
    
    try:
        # 1. Detectar idioma
        idioma_detectado, confianza = detect_language(ocr_text, api_key)
        
        # 2. Verificar si necesita traducción
        if should_translate(idioma_detectado, 'es'):
            # 3. Traducir a español
            texto_traducido = translate_to_target(ocr_text, idioma_detectado, 'es', api_key)
            
            return texto_traducido, {
                'idioma_detectado': idioma_detectado,
                'fue_traducido': True,
                'texto_original': ocr_text,
                'confianza': confianza
            }
        else:
            # Ya está en español
            return ocr_text, {
                'idioma_detectado': idioma_detectado,
                'fue_traducido': False,
                'texto_original': None,
                'confianza': confianza
            }
    
    except Exception as e:
        print(f"[OCR Translation] Error en traducción: {e}")
        # En caso de error, retornar texto original
        return ocr_text, {
            'idioma_detectado': 'desconocido',
            'fue_traducido': False,
            'texto_original': None,
            'confianza': 0.0,
            'error': str(e)
        }


def get_language_display_name(lang_code: str) -> str:
    """
    Obtiene el nombre del idioma en español para mostrar en la UI.
    
    Args:
        lang_code: Código ISO del idioma (ej: 'en', 'pt', 'fr')
    
    Returns:
        Nombre del idioma en español
    """
    lang_names = {
        'es': 'Español',
        'en': 'Inglés',
        'pt': 'Portugués',
        'fr': 'Francés',
        'de': 'Alemán',
        'it': 'Italiano',
        'zh': 'Chino',
        'ja': 'Japonés',
        'ko': 'Coreano',
        'ar': 'Árabe',
        'ru': 'Ruso',
        'vi': 'Vietnamita',
        'th': 'Tailandés',
        'hi': 'Hindi',
        'nl': 'Holandés',
        'pl': 'Polaco',
        'tr': 'Turco',
        'sv': 'Sueco',
        'no': 'Noruego',
        'da': 'Danés',
        'fi': 'Finlandés'
    }
    
    return lang_names.get(lang_code.lower()[:2], lang_code.upper())
