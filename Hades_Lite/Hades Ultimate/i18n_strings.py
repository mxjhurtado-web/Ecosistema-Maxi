# i18n_strings.py
# Sistema de internacionalización para Hades Lite 2.2
# Soporta Español e Inglés Americano

import json
from pathlib import Path
from typing import Dict, Any

# Diccionario completo de traducciones
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'es': {
        # Ventana principal
        'app_title': 'HADES: El Guardián de tu Información',
        'load_images': 'Cargar imágenes',
        'paste_clipboard': 'Pegar portapapeles',
        'api_config': 'Configurar API',
        'result_ocr': 'Resultado OCR',
        'drag_drop_hint': 'Arrastra y suelta imágenes aquí, o usa Cargar / Ctrl+V.',
        
        # Botones principales
        'analyze': '🔍 Analizar',
        'analyze_id': '🪪 Analizar identificación',
        'export': '💾 Exportar',
        'clear': '🧹 Borrar',
        
        # Ventana de API Keys
        'api_window_title': 'Configurar API Key',
        'api_window_header': '🔑 Configuración de API Keys',
        'gemini_api_label': 'Gemini API Key (Google):',
        'get_api_key': '🔗 Obtener Gemini API Key',
        'save': '💾 Guardar',
        'cancel': '❌ Cancelar',
        'language_label': '🌐 Idioma / Language:',
        'verify_email_first': 'Primero verifica tu correo (se hace al iniciar).',
        
        # Selector de idioma
        'lang_spanish': '🇪🇸 Español',
        'lang_english': '🇺🇸 English',
        
        # Mensajes de estado
        'api_configured': '✅ API Key configurada: Gemini',
        'no_api_configured': '⚠️ No se configuró API Key',
        'images_added': 'Se agregaron {count} imagen(es). Total: {total}',
        'language_changed': 'Idioma cambiado a: {lang}',
        
        # Panel de traducción
        'detected_language': '🌐 Detectado: {source} → {target}',
        'language_label_simple': '🌐 Idioma: {lang}',
        'view_original': 'Ver original',
        'view_translation': 'Ver traducción',
        
        # Análisis forense
        'authenticity_analysis': 'Análisis de Autenticidad',
        'risk_low': 'Riesgo Bajo',
        'risk_medium': 'Riesgo Medio',
        'risk_high': 'Riesgo Alto',
        
        # Procesamiento
        'processing_image': '⏳ Procesando imagen con Gemini Vision...',
        'ocr_completed': '✓ OCR completado',
        'analyzing_authenticity': '⏳ Analizando autenticidad...',
        'processing_carousel': '⏳ Procesando {current}/{total} imágenes...',
        'processing_ids': '⏳ Procesando {current}/{total} identificaciones (frente + reverso)...',
        
        # Errores
        'timeout_error': '⚠️ Timeout: Gemini tardó demasiado. Intenta con una imagen más pequeña.',
        'no_connection': '⚠️ Sin conexión a internet. Verifica tu red.',
        'general_error': '⚠️ Error al extraer texto: {detail}',
        
        # Nombres de idiomas
        'lang_name_es': 'Español',
        'lang_name_en': 'English',
        'lang_name_pt': 'Português',
        'lang_name_fr': 'Français',
        'lang_name_de': 'Deutsch',
        'lang_name_it': 'Italiano',
        'lang_name_zh': '中文',
        'lang_name_ja': '日本語',
        'lang_name_ko': '한국어',
        'lang_name_ar': 'العربية',
        'lang_name_ru': 'Русский',
        'lang_name_vi': 'Tiếng Việt',
        'lang_name_th': 'ไทย',
        'lang_name_hi': 'हिन्दी',
    },
    
    'en': {
        # Main window
        'app_title': 'HADES: Guardian of Your Information',
        'load_images': 'Load images',
        'paste_clipboard': 'Paste clipboard',
        'api_config': 'Configure API',
        'result_ocr': 'OCR Result',
        'drag_drop_hint': 'Drag and drop images here, or use Load / Ctrl+V.',
        
        # Main buttons
        'analyze': '🔍 Analyze',
        'analyze_id': '🪪 Analyze ID',
        'export': '💾 Export',
        'clear': '🧹 Clear',
        
        # API Keys window
        'api_window_title': 'Configure API Key',
        'api_window_header': '🔑 API Keys Configuration',
        'gemini_api_label': 'Gemini API Key (Google):',
        'get_api_key': '🔗 Get Gemini API Key',
        'save': '💾 Save',
        'cancel': '❌ Cancel',
        'language_label': '🌐 Idioma / Language:',
        'verify_email_first': 'Please verify your email first (done at startup).',
        
        # Language selector
        'lang_spanish': '🇪🇸 Español',
        'lang_english': '🇺🇸 English',
        
        # Status messages
        'api_configured': '✅ API Key configured: Gemini',
        'no_api_configured': '⚠️ No API Key configured',
        'images_added': 'Added {count} image(s). Total: {total}',
        'language_changed': 'Language changed to: {lang}',
        
        # Translation panel
        'detected_language': '🌐 Detected: {source} → {target}',
        'language_label_simple': '🌐 Language: {lang}',
        'view_original': 'View original',
        'view_translation': 'View translation',
        
        # Forensic analysis
        'authenticity_analysis': 'Authenticity Analysis',
        'risk_low': 'Low Risk',
        'risk_medium': 'Medium Risk',
        'risk_high': 'High Risk',
        
        # Processing
        'processing_image': '⏳ Processing image with Gemini Vision...',
        'ocr_completed': '✓ OCR completed',
        'analyzing_authenticity': '⏳ Analyzing authenticity...',
        'processing_carousel': '⏳ Processing {current}/{total} images...',
        'processing_ids': '⏳ Processing {current}/{total} IDs (front + back)...',
        
        # Errors
        'timeout_error': '⚠️ Timeout: Gemini took too long. Try with a smaller image.',
        'no_connection': '⚠️ No internet connection. Check your network.',
        'general_error': '⚠️ Error extracting text: {detail}',
        
        # Language names
        'lang_name_es': 'Spanish',
        'lang_name_en': 'English',
        'lang_name_pt': 'Portuguese',
        'lang_name_fr': 'French',
        'lang_name_de': 'German',
        'lang_name_it': 'Italian',
        'lang_name_zh': 'Chinese',
        'lang_name_ja': 'Japanese',
        'lang_name_ko': 'Korean',
        'lang_name_ar': 'Arabic',
        'lang_name_ru': 'Russian',
        'lang_name_vi': 'Vietnamese',
        'lang_name_th': 'Thai',
        'lang_name_hi': 'Hindi',
    }
}

# Idioma actual (se carga desde config)
CURRENT_LANGUAGE = 'es'


def get_text(key: str, **kwargs) -> str:
    """
    Obtiene texto traducido para el idioma actual.
    
    Args:
        key: Clave del texto en el diccionario
        **kwargs: Variables para formatear el texto (ej: count=5, total=10)
    
    Returns:
        Texto traducido y formateado
    
    Example:
        >>> get_text('images_added', count=3, total=10)
        'Se agregaron 3 imagen(es). Total: 10'
    """
    text = TRANSLATIONS.get(CURRENT_LANGUAGE, {}).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def set_language(lang: str) -> None:
    """
    Cambia el idioma de la aplicación.
    
    Args:
        lang: 'es' o 'en'
    """
    global CURRENT_LANGUAGE
    if lang in TRANSLATIONS:
        CURRENT_LANGUAGE = lang
        save_language_preference(lang)


def get_current_language() -> str:
    """
    Retorna el idioma actual.
    
    Returns:
        'es' o 'en'
    """
    return CURRENT_LANGUAGE


def get_language_name(lang_code: str) -> str:
    """
    Obtiene el nombre del idioma en el idioma actual de la UI.
    
    Args:
        lang_code: Código ISO del idioma (ej: 'es', 'en', 'pt', 'fr')
    
    Returns:
        Nombre del idioma traducido
    
    Example:
        >>> set_language('es')
        >>> get_language_name('en')
        'English'
        >>> set_language('en')
        >>> get_language_name('es')
        'Spanish'
    """
    # Normalizar código de idioma
    lang_code_lower = lang_code.lower()[:2]
    
    # Mapeo de códigos a claves
    lang_key = f'lang_name_{lang_code_lower}'
    
    # Obtener nombre traducido
    return get_text(lang_key)


def load_language_preference() -> str:
    """
    Carga preferencia de idioma desde archivo de configuración.
    
    Returns:
        'es' o 'en' (default: 'es')
    """
    try:
        config_file = Path.home() / '.hades' / 'config.json'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                lang = config.get('language', 'es')
                if lang in TRANSLATIONS:
                    return lang
    except Exception as e:
        print(f"[i18n] Error loading language preference: {e}")
    
    return 'es'


def save_language_preference(lang: str) -> None:
    """
    Guarda preferencia de idioma en archivo de configuración.
    
    Args:
        lang: 'es' o 'en'
    """
    try:
        config_dir = Path.home() / '.hades'
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / 'config.json'
        
        config = {}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                config = {}
        
        config['language'] = lang
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"[i18n] Language preference saved: {lang}")
    except Exception as e:
        print(f"[i18n] Error saving language preference: {e}")


def initialize_language() -> str:
    """
    Inicializa el sistema de idiomas cargando la preferencia guardada.
    
    Returns:
        Idioma cargado ('es' o 'en')
    """
    global CURRENT_LANGUAGE
    CURRENT_LANGUAGE = load_language_preference()
    return CURRENT_LANGUAGE


# Inicializar al importar el módulo
initialize_language()
