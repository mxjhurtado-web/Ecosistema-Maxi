"""
Módulo principal de análisis de documentos.

Integra OCR, detección de país, fechas, extracción de datos, traducción y análisis forense.
"""

from typing import Dict, Optional
from datetime import datetime

from .ocr import extract_text_from_image
from .country import detect_country, get_country_name
from .dates.dates import process_dates_by_type, DateInfo
from .extraction import extract_all_data, ExtractedData
from .translation import translate_to_spanish, detect_language, should_translate
from .forensics import analyze_document_authenticity, SemaforoLevel


class AnalysisResult:
    """Resultado completo del análisis de un documento"""
    
    def __init__(self):
        self.ocr_text = ""
        self.ocr_text_translated = ""
        self.language_detected = "unknown"
        self.was_translated = False
        self.country_code = None
        self.country_name = None
        self.dates = {}
        self.name = None
        self.id_number = None
        self.id_type = None
        self.forensic_result = None
        self.semaforo = None
        self.score = 0
        self.warnings = []
        self.metadata = {}
        
    def to_dict(self) -> Dict:
        """Convierte el resultado a diccionario para API"""
        # Convertir DateInfo a dict
        dates_dict = {}
        for date_type, date_info in self.dates.items():
            if date_info:
                dates_dict[date_type] = {
                    "original": date_info.original,
                    "display": date_info.display,
                    "format": date_info.format_detected.value,
                    "confidence": date_info.confidence,
                    "is_valid": date_info.is_valid,
                    "is_ambiguous": date_info.is_ambiguous,
                    "warnings": date_info.warnings,
                    "is_expired": date_info.is_expired,
                    "days_until_expiry": date_info.days_until_expiry
                }
        
        return {
            "ocr_text": self.ocr_text,
            "ocr_text_translated": self.ocr_text_translated,
            "language_detected": self.language_detected,
            "was_translated": self.was_translated,
            "country": {
                "code": self.country_code,
                "name": self.country_name
            },
            "dates": dates_dict,
            "extracted_data": {
                "name": self.name,
                "id_number": self.id_number,
                "id_type": self.id_type
            },
            "forensics": self.forensic_result.to_dict() if self.forensic_result else None,
            "semaforo": self.semaforo.value if self.semaforo else None,
            "score": self.score,
            "warnings": self.warnings,
            "metadata": self.metadata
        }


def analyze_image(
    image_bytes: bytes,
    gemini_api_key: Optional[str] = None,
    config: Optional[Dict] = None
) -> AnalysisResult:
    """
    Analiza una imagen de documento completa.
    
    Esta es la función principal del motor de análisis.
    
    Proceso:
    1. OCR - Extrae texto con Gemini Vision
    2. Detección de país
    3. Traducción automática (si necesario)
    4. Procesamiento de fechas (CON PRESERVACIÓN)
    5. Extracción de nombres e IDs
    6. Análisis forense completo
    
    Args:
        image_bytes: Bytes de la imagen a analizar
        gemini_api_key: API key de Gemini (opcional si está en entorno)
        config: Configuración adicional (opcional)
        
    Returns:
        AnalysisResult con todos los datos del análisis
        
    Ejemplo:
        >>> with open("license.jpg", "rb") as f:
        ...     image_bytes = f.read()
        >>> result = analyze_image(image_bytes)
        >>> print(result.semaforo)  # verde/amarillo/rojo
        >>> print(result.dates["expiration"].display)  # "01/15/2024"
        >>> print(result.name)  # "John Doe"
    """
    result = AnalysisResult()
    config = config or {}
    
    # 1. OCR - Extraer texto
    try:
        ocr_text, ocr_metadata = extract_text_from_image(
            image_bytes,
            api_key=gemini_api_key,
            timeout=config.get("ocr_timeout", 30)
        )
        result.ocr_text = ocr_text
        result.metadata["ocr"] = ocr_metadata
    except Exception as e:
        result.warnings.append(f"Error en OCR: {str(e)}")
        result.ocr_text = ""
    
    # 2. Detectar país
    if result.ocr_text:
        result.country_code = detect_country(result.ocr_text)
        if result.country_code:
            result.country_name = get_country_name(result.country_code)
    
    # 3. Traducción automática (si necesario)
    if result.ocr_text and config.get("auto_translate", True):
        try:
            result.language_detected = detect_language(result.ocr_text)
            
            if should_translate(result.ocr_text):
                translated_text, translation_metadata = translate_to_spanish(
                    result.ocr_text,
                    source_lang=result.language_detected,
                    api_key=gemini_api_key
                )
                result.ocr_text_translated = translated_text
                result.was_translated = translation_metadata.get("translated", False)
                result.metadata["translation"] = translation_metadata
            else:
                result.ocr_text_translated = result.ocr_text
                result.was_translated = False
        except Exception as e:
            result.warnings.append(f"Error en traducción: {str(e)}")
            result.ocr_text_translated = result.ocr_text
    
    # 4. Procesar fechas (CON PRESERVACIÓN) - usar texto original
    if result.ocr_text:
        try:
            dates_dict = process_dates_by_type(
                result.ocr_text,
                country_hint=result.country_code
            )
            result.dates = dates_dict
            
            # Agregar warnings de fechas ambiguas
            for date_type, date_info in dates_dict.items():
                if date_info and date_info.is_ambiguous:
                    result.warnings.extend(date_info.warnings)
                    
        except Exception as e:
            result.warnings.append(f"Error procesando fechas: {str(e)}")
    
    # 5. Extracción de nombres e IDs - usar texto traducido si está disponible
    text_for_extraction = result.ocr_text_translated or result.ocr_text
    if text_for_extraction:
        try:
            extracted_data = extract_all_data(
                text_for_extraction,
                country=result.country_code
            )
            result.name = extracted_data.name
            result.id_number = extracted_data.id_number
            result.id_type = extracted_data.id_type
            result.metadata["extraction_confidence"] = extracted_data.confidence
        except Exception as e:
            result.warnings.append(f"Error extrayendo datos: {str(e)}")
    
    # 6. Análisis forense completo
    try:
        forensic_result = analyze_document_authenticity(
            result.ocr_text,
            image_bytes,
            api_key=gemini_api_key
        )
        result.forensic_result = forensic_result
        result.semaforo = forensic_result.semaforo
        result.score = forensic_result.score
        result.warnings.extend(forensic_result.warnings)
    except Exception as e:
        result.warnings.append(f"Error en análisis forense: {str(e)}")
        result.semaforo = SemaforoLevel.AMARILLO
        result.score = 50
    
    # 7. Metadata final
    result.metadata["analysis_timestamp"] = datetime.now().isoformat()
    result.metadata["country_detected"] = result.country_code is not None
    result.metadata["dates_found"] = len([d for d in result.dates.values() if d is not None])
    result.metadata["name_extracted"] = result.name is not None
    result.metadata["id_extracted"] = result.id_number is not None
    
    return result
