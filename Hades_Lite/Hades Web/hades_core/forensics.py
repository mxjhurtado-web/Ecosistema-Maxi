"""
Módulo de análisis forense de documentos.

Análisis completo con Gemini Vision para detectar falsificación.
"""

import os
import base64
import io
from typing import Dict, List, Tuple, Optional
from enum import Enum
from PIL import Image, ImageOps

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


class SemaforoLevel(Enum):
    """Nivel del semáforo de autenticidad"""
    VERDE = "verde"    # Bajo riesgo (0-15 puntos)
    AMARILLO = "amarillo"  # Riesgo medio (16-40 puntos)
    ROJO = "rojo"      # Alto riesgo (41+ puntos)


class ForensicResult:
    """Resultado del análisis forense"""
    
    def __init__(self):
        self.score = 0
        self.semaforo = SemaforoLevel.VERDE
        self.details = []
        self.warnings = []
        self.security_elements = "No evaluado"
        self.print_quality = "No evaluado"
        self.manipulation_detected = False
        self.visual_analysis = ""
        
    def to_dict(self) -> Dict:
        """Convierte el resultado a diccionario"""
        return {
            "score": self.score,
            "semaforo": self.semaforo.value,
            "details": self.details,
            "warnings": self.warnings,
            "security_elements": self.security_elements,
            "print_quality": self.print_quality,
            "manipulation_detected": self.manipulation_detected,
            "visual_analysis": self.visual_analysis
        }


def gemini_vision_forensic_analysis(
    image_bytes: bytes,
    api_key: Optional[str] = None
) -> Tuple[int, List[str], str]:
    """
    Análisis forense avanzado con Gemini Vision.
    
    Analiza:
    - Elementos de seguridad (hologramas, marcas de agua)
    - Calidad de impresión
    - Detección de manipulación digital
    - Tipografía y layout
    - Calidad de fotografía
    
    Args:
        image_bytes: Bytes de la imagen
        api_key: API key de Gemini (opcional si está en entorno)
        
    Returns:
        Tupla de (score_adicional, detalles, análisis_completo)
    """
    if not GEMINI_AVAILABLE:
        return 0, ["Gemini Vision no disponible"], ""
    
    # Configurar API key
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return 0, ["API key de Gemini no disponible"], ""
    
    try:
        # Preparar imagen
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
        bio = io.BytesIO()
        image.save(bio, format="PNG")
        bio.seek(0)
        
        # Prompt forense avanzado
        prompt = (
            "Actúa como un experto forense en documentos de identidad. "
            "Analiza esta imagen con técnicas forenses profesionales.\n\n"
            "ANÁLISIS FORENSE REQUERIDO:\n"
            "1. ELEMENTOS DE SEGURIDAD:\n"
            "   - Hologramas, marcas de agua, microimpresiones\n"
            "   - Tintas especiales, guilloches (patrones de líneas)\n"
            "   - Elementos táctiles (relieve, textura)\n\n"
            "2. ANÁLISIS DE IMPRESIÓN:\n"
            "   - Calidad de impresión (offset profesional vs casera)\n"
            "   - Resolución y nitidez de texto/imágenes\n"
            "   - Alineación de capas (registro de color)\n"
            "   - Bordes de texto (limpios vs borrosos)\n\n"
            "3. DETECCIÓN DE MANIPULACIÓN DIGITAL:\n"
            "   - Clonación de áreas (stamp/clone tool)\n"
            "   - Bordes irregulares en foto o texto\n"
            "   - Inconsistencias de iluminación/sombras\n"
            "   - Artefactos de compresión JPEG sospechosos\n"
            "   - Transiciones de color no naturales\n\n"
            "4. TIPOGRAFÍA Y LAYOUT:\n"
            "   - Fuentes oficiales vs genéricas (Arial, Times)\n"
            "   - Espaciado y kerning profesional\n"
            "   - Alineación y márgenes estándar\n\n"
            "5. FOTOGRAFÍA:\n"
            "   - Calidad profesional vs casera\n"
            "   - Fondo uniforme y apropiado\n"
            "   - Iluminación frontal consistente\n"
            "   - Proporciones faciales correctas\n\n"
            "INSTRUCCIONES:\n"
            "- Evalúa cada categoría con score de 0-10 (10=muy sospechoso, 0=auténtico)\n"
            "- Menciona evidencia específica para scores >5\n"
            "- Sé directo y técnico, sin ambigüedades\n"
            "- Si detectas manipulación, especifica el tipo exacto"
        )
        
        # Configurar Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generar análisis
        response = model.generate_content(
            [{"mime_type": "image/png", "data": bio.getvalue()}, {"text": prompt}],
            generation_config={"temperature": 0.1, "top_p": 0.9, "max_output_tokens": 2048},
            request_options={"timeout": 60}
        )
        
        if not response or not response.text:
            return 0, ["Gemini no devolvió análisis"], ""
        
        visual_analysis = response.text.strip()
        analysis_lower = visual_analysis.lower()
        
        # Analizar respuesta y calcular score
        score_visual = 0
        detalles = []
        
        # Red flags con pesos
        red_flags = {
            # Manipulación digital (peso alto)
            "manipulación": 30,
            "manipulacion": 30,
            "editado": 30,
            "photoshop": 40,
            "clonación": 40,
            "clonacion": 40,
            "alterado": 30,
            "retocado": 25,
            
            # Falsificación directa (peso muy alto)
            "falso": 45,
            "falsificación": 45,
            "falsificacion": 45,
            "no auténtico": 40,
            "fraudulento": 45,
            
            # Inconsistencias (peso medio-alto)
            "inconsistente": 25,
            "sospechoso": 25,
            "irregular": 20,
            "anómalo": 25,
            "anomalo": 25,
            
            # Calidad (peso medio)
            "borroso": 15,
            "pixelado": 15,
            "baja calidad": 20,
            "amateur": 20,
            "casera": 25,
            
            # Elementos faltantes (peso alto)
            "sin holograma": 35,
            "falta marca de agua": 35,
            "ausencia de": 30,
            "no se observa": 25,
            
            # Tipografía (peso medio)
            "fuente genérica": 20,
            "fuente generica": 20,
            "arial": 15,
            "times new roman": 15,
            
            # Bordes y transiciones (peso medio-alto)
            "bordes irregulares": 30,
            "transición abrupta": 25,
            "transicion abrupta": 25,
            "recorte sospechoso": 30,
        }
        
        for keyword, penalty in red_flags.items():
            if keyword in analysis_lower:
                score_visual += penalty
                detalles.append(f"Detectado: '{keyword}' (+{penalty} puntos)")
        
        # Señales positivas (bonificación)
        positive_signals = [
            "auténtico", "autentico", "legítimo", "legitimo",
            "genuino", "profesional", "oficial"
        ]
        if any(word in analysis_lower for word in positive_signals):
            if score_visual == 0:
                detalles.append("Documento aparenta autenticidad")
            else:
                score_visual = max(0, score_visual - 10)
                detalles.append("Señales mixtas detectadas (-10 puntos)")
        
        # Cap a 50 para evitar falsos positivos
        score_visual = min(score_visual, 50)
        
        return score_visual, detalles, visual_analysis
        
    except Exception as e:
        return 0, [f"Error en análisis forense: {str(e)[:100]}"], ""


def analyze_document_authenticity(
    ocr_text: str,
    image_bytes: bytes = None,
    api_key: Optional[str] = None
) -> ForensicResult:
    """
    Analiza la autenticidad de un documento.
    
    Combina análisis de texto y análisis visual con Gemini Vision.
    
    Args:
        ocr_text: Texto extraído del documento
        image_bytes: Bytes de la imagen (para análisis visual)
        api_key: API key de Gemini (opcional)
        
    Returns:
        ForensicResult con el análisis completo
    """
    result = ForensicResult()
    score = 0
    
    # 1. Análisis de texto (palabras sospechosas)
    suspicious_words = [
        "muestra", "sample", "specimen", "ejemplo", "void",
        "photoshop", "fake", "falso", "copia", "copy"
    ]
    
    text_lower = ocr_text.lower()
    
    for word in suspicious_words:
        if word in text_lower:
            score += 10
            result.details.append(f"Palabra sospechosa: '{word}'")
            result.warnings.append(f"Documento contiene: '{word}'")
    
    # 2. Análisis visual con Gemini Vision (si hay imagen)
    if image_bytes and GEMINI_AVAILABLE:
        visual_score, visual_details, visual_analysis = gemini_vision_forensic_analysis(
            image_bytes,
            api_key
        )
        
        score += visual_score
        result.details.extend(visual_details)
        result.visual_analysis = visual_analysis
        
        # Evaluar elementos de seguridad basándose en el análisis
        if visual_score == 0:
            result.security_elements = "Presentes (análisis completo)"
            result.print_quality = "Profesional"
            result.manipulation_detected = False
        elif visual_score < 25:
            result.security_elements = "Parcialmente presentes"
            result.print_quality = "Aceptable"
            result.manipulation_detected = False
        else:
            result.security_elements = "Requiere verificación"
            result.print_quality = "Sospechosa"
            result.manipulation_detected = True
    else:
        # Análisis básico sin imagen
        if score == 0:
            result.security_elements = "No evaluado (sin imagen)"
            result.print_quality = "No evaluado (sin imagen)"
            result.manipulation_detected = False
        else:
            result.security_elements = "Requiere verificación"
            result.print_quality = "Requiere verificación"
            result.manipulation_detected = True
    
    # 3. Determinar semáforo
    result.score = score
    result.semaforo = calculate_semaforo(score)
    
    return result


def calculate_semaforo(score: int) -> SemaforoLevel:
    """
    Calcula el nivel del semáforo basándose en el score.
    
    Args:
        score: Puntuación de riesgo (0-100)
        
    Returns:
        Nivel del semáforo
    """
    if score <= 15:
        return SemaforoLevel.VERDE
    elif score <= 40:
        return SemaforoLevel.AMARILLO
    else:
        return SemaforoLevel.ROJO
