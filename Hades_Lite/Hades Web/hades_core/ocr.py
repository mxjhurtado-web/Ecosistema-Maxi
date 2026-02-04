"""
Módulo de OCR usando Google Gemini Vision.

Extraído y simplificado de Hades Ultimate.
"""

import os
import base64
from typing import Optional, Tuple
from PIL import Image
import io

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


def configure_gemini(api_key: Optional[str] = None):
    """
    Configura la API de Gemini.
    
    Args:
        api_key: API key de Google Gemini. Si es None, intenta usar GEMINI_API_KEY del entorno.
    """
    if not GEMINI_AVAILABLE:
        raise ImportError("google-generativeai no está instalado. Instala con: pip install google-generativeai")
    
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("API key de Gemini no proporcionada. Define GEMINI_API_KEY en el entorno o pásala como parámetro.")
    
    genai.configure(api_key=api_key)


def extract_text_from_image(
    image_bytes: bytes,
    api_key: Optional[str] = None,
    timeout: int = 30
) -> Tuple[str, dict]:
    """
    Extrae texto de una imagen usando Gemini Vision.
    
    Args:
        image_bytes: Bytes de la imagen
        api_key: API key de Gemini (opcional si está en entorno)
        timeout: Timeout en segundos
        
    Returns:
        Tupla de (texto_ocr, metadata)
        
    Raises:
        Exception: Si falla el OCR
    """
    if not GEMINI_AVAILABLE:
        raise ImportError("google-generativeai no está instalado")
    
    # Configurar Gemini
    configure_gemini(api_key)
    
    # Cargar imagen
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Error al cargar imagen: {e}")
    
    # Prompt para OCR (copiado de Hades Ultimate)
    prompt = """
Extrae TODO el texto visible en esta imagen de documento de identificación.

INSTRUCCIONES:
1. Transcribe EXACTAMENTE todo el texto tal como aparece
2. Mantén el formato original (saltos de línea, espaciado)
3. Incluye TODAS las fechas exactamente como están escritas
4. No reformatees ni interpretes nada
5. Si hay texto en múltiples idiomas, transcríbelo todo

IMPORTANTE: Las fechas deben copiarse EXACTAMENTE como aparecen.
Ejemplo: Si dice "01/15/2024", escribe "01/15/2024" (NO lo cambies a "15/01/2024")

Formato de salida:
[Transcripción exacta del documento]
"""
    
    try:
        # Usar Gemini 2.5 Flash (modelo más reciente)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        response = model.generate_content(
            [prompt, image],
            request_options={"timeout": timeout}
        )
        
        if not response or not response.text:
            raise Exception("Gemini no devolvió texto")
        
        ocr_text = response.text.strip()
        
        # Metadata
        metadata = {
            "model": "gemini-1.5-flash",
            "success": True,
            "char_count": len(ocr_text)
        }
        
        return ocr_text, metadata
        
    except Exception as e:
        raise Exception(f"Error en OCR con Gemini: {str(e)}")


def extract_text_from_file(
    file_path: str,
    api_key: Optional[str] = None,
    timeout: int = 30
) -> Tuple[str, dict]:
    """
    Extrae texto de un archivo de imagen.
    
    Args:
        file_path: Ruta al archivo de imagen
        api_key: API key de Gemini
        timeout: Timeout en segundos
        
    Returns:
        Tupla de (texto_ocr, metadata)
    """
    with open(file_path, 'rb') as f:
        image_bytes = f.read()
    
    return extract_text_from_image(image_bytes, api_key, timeout)
