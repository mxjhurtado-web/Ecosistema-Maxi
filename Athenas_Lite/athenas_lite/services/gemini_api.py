
import json
import logging
import re
import time
from datetime import datetime, timedelta
import google.generativeai as genai
from .system_tools import guess_mime

logger = logging.getLogger("athenas_lite")

API_KEY_GEMINI = None
USE_REAL_MODEL = False
GEMINI_MODEL_SELECTED = "gemini-2.5-flash"  # Modelo por defecto (soporta audio)

# Sistema de rotación de API Keys
GEMINI_API_KEYS = []  # Lista de API keys disponibles
CURRENT_KEY_INDEX = 0  # Índice de la key actual

# ===== RATE LIMITER =====
class RateLimiter:
    """
    Controla el rate de requests a Gemini API para evitar agotar cuota.
    Gemini 2.5 Flash: 15 RPM (requests per minute)
    """
    def __init__(self, max_requests=14, time_window=60):
        """
        Args:
            max_requests: Máximo de requests permitidos (14 para margen de seguridad)
            time_window: Ventana de tiempo en segundos (60 = 1 minuto)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []  # Lista de timestamps
    
    def wait_if_needed(self):
        """
        Espera automáticamente si se está cerca del límite de rate.
        Retorna el tiempo esperado (0 si no esperó).
        """
        now = datetime.now()
        
        # Limpiar requests antiguos (fuera de la ventana de tiempo)
        self.requests = [r for r in self.requests 
                        if (now - r).total_seconds() < self.time_window]
        
        # Si alcanzamos el límite, esperar
        if len(self.requests) >= self.max_requests:
            oldest = min(self.requests)
            wait_time = self.time_window - (now - oldest).total_seconds() + 1
            
            if wait_time > 0:
                logger.warning(f"⏳ Rate limit alcanzado ({len(self.requests)}/{self.max_requests} requests). "
                             f"Esperando {wait_time:.1f}s para continuar...")
                time.sleep(wait_time)
                # Limpiar después de esperar
                self.requests = []
                return wait_time
        
        # Registrar este request
        self.requests.append(now)
        remaining = self.max_requests - len(self.requests)
        logger.info(f"📊 Requests: {len(self.requests)}/{self.max_requests} (quedan {remaining})")
        return 0

# Instancia global del rate limiter
rate_limiter = RateLimiter(max_requests=14, time_window=60)

SENTIMENT_PROMPT = r"""
Escucha el audio y devuelve SOLO este texto (sin JSON):
### Resumen Cálido
<texto>

### Comentario Emocional
<texto>

### Valoración
<número 1-10>
"""

ROLE_SENTIMENT_PROMPT = """
Devuelve SOLO JSON:
{
    "cliente": {"valor": 1-10, "clasificacion": "Positiva|Neutra|Negativa", "comentario": "", "resumen": ""},
    "asesor":  {"valor": 1-10, "clasificacion": "Positiva|Neutra|Negativa", "comentario": "", "resumen": ""}
}
"""

def configurar_gemini(api_key: str) -> bool:
    global API_KEY_GEMINI, USE_REAL_MODEL
    """
    Configura Gemini con una o múltiples API keys.
    Si se pasan múltiples keys separadas por comas, se habilita rotación.
    """
    global API_KEY_GEMINI, USE_REAL_MODEL, GEMINI_API_KEYS, CURRENT_KEY_INDEX
    try:
        # Separar múltiples keys si están separadas por comas
        keys = [k.strip() for k in api_key.split(',') if k.strip()]
        
        if not keys:
            return False
        
        # Guardar todas las keys
        GEMINI_API_KEYS = keys
        CURRENT_KEY_INDEX = 0
        
        # Configurar la primera key
        API_KEY_GEMINI = keys[0]
        genai.configure(api_key=API_KEY_GEMINI)
        USE_REAL_MODEL = True
        
        if len(keys) > 1:
            logger.info(f"✅ Gemini configurado con {len(keys)} API keys (rotación habilitada)")
        else:
            logger.info("Gemini configured successfully.")
        
        return True
    except Exception as e:
        logger.error(f"Error configurando Gemini: {e}")
        USE_REAL_MODEL = False
        return False

def rotate_api_key() -> bool:
    """
    Rota a la siguiente API key disponible.
    Retorna True si hay más keys disponibles, False si ya se agotaron todas.
    """
    global API_KEY_GEMINI, CURRENT_KEY_INDEX, GEMINI_API_KEYS
    
    if not GEMINI_API_KEYS or len(GEMINI_API_KEYS) <= 1:
        logger.warning("⚠️ No hay más API keys para rotar")
        return False
    
    # Rotar al siguiente índice
    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GEMINI_API_KEYS)
    API_KEY_GEMINI = GEMINI_API_KEYS[CURRENT_KEY_INDEX]
    
    try:
        genai.configure(api_key=API_KEY_GEMINI)
        logger.info(f"🔄 Rotando a API Key #{CURRENT_KEY_INDEX + 1}/{len(GEMINI_API_KEYS)}")
        return True
    except Exception as e:
        logger.error(f"Error rotando API key: {e}")
        return False

def _gemini_model(name=None):
    """
    Retorna el modelo de Gemini configurado.
    Si no se especifica 'name', usa GEMINI_MODEL_SELECTED.
    """
    if USE_REAL_MODEL:
        try:
            model_name = name or GEMINI_MODEL_SELECTED
            return genai.GenerativeModel(model_name)
        except Exception:
            return None
    return None

def llm_json_or_mock(prompt: str, audio_path: str, fallback: dict) -> dict:
    model = _gemini_model()
    if model:
        try:
            # Esperar si es necesario para no agotar cuota
            wait_time = rate_limiter.wait_if_needed()
            
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            resp = model.generate_content(
                [prompt, {"mime_type": guess_mime(audio_path), "data": audio_bytes}],
                generation_config={"response_mime_type": "application/json"}
            )
            text = getattr(resp, "text", None) or ""
            return json.loads(text)
        except Exception as e:
            error_msg = str(e)
            
            # Detectar cuota agotada
            if "429" in error_msg or "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                logger.error(f"❌ CUOTA AGOTADA para modelo {GEMINI_MODEL_SELECTED}")
                
                # Intentar rotar a otra API key
                if rotate_api_key():
                    logger.info("🔄 Reintentando con nueva API key...")
                    # Reintentar con la nueva key
                    try:
                        wait_time = rate_limiter.wait_if_needed()
                        with open(audio_path, "rb") as f:
                            audio_bytes = f.read()
                        resp = model.generate_content(
                            [prompt, {"mime_type": guess_mime(audio_path), "data": audio_bytes}],
                            generation_config={"response_mime_type": "application/json"}
                        )
                        text = getattr(resp, "text", None) or ""
                        return json.loads(text)
                    except Exception as retry_error:
                        logger.error(f"Error en reintento: {retry_error}")
                        pass
                
                # Si no hay más keys o falló el reintento
                logger.error(f"💡 Solución: Abre 'Configurar API Key y Modelo' y agrega más API keys")
                
                # Mensaje específico según el modelo
                if GEMINI_MODEL_SELECTED == "gemini-2.5-flash":
                    logger.warning("⚠️ gemini-2.5-flash tiene límite de 20 requests/día")
                    logger.warning(f"💡 Keys disponibles: {len(GEMINI_API_KEYS)}, Key actual: #{CURRENT_KEY_INDEX + 1}")
                
                return fallback
            
            logger.error(f"Gemini output error (returning fallback): {e}")
            pass
    return fallback

def llm_text_or_mock(prompt: str, audio_path: str, fallback_text: str) -> str:
    model = _gemini_model()
    if model:
        try:
            # Esperar si es necesario para no agotar cuota
            wait_time = rate_limiter.wait_if_needed()
            
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            resp = model.generate_content([prompt, {"mime_type": guess_mime(audio_path), "data": audio_bytes}])
            return (getattr(resp, "text", None) or "").strip()
        except Exception as e:
            error_msg = str(e)
            
            # Detectar cuota agotada
            if "429" in error_msg or "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                logger.error(f"❌ CUOTA AGOTADA para modelo {GEMINI_MODEL_SELECTED}")
                
                # Intentar rotar a otra API key
                if rotate_api_key():
                    logger.info("🔄 Reintentando con nueva API key...")
                    # Reintentar con la nueva key
                    try:
                        wait_time = rate_limiter.wait_if_needed()
                        with open(audio_path, "rb") as f:
                            audio_bytes = f.read()
                        resp = model.generate_content([prompt, {"mime_type": guess_mime(audio_path), "data": audio_bytes}])
                        return (getattr(resp, "text", None) or "").strip()
                    except Exception as retry_error:
                        logger.error(f"Error en reintento: {retry_error}")
                        pass
                
                # Si no hay más keys o falló el reintento
                logger.error(f"💡 Solución: Abre 'Configurar API Key y Modelo' y agrega más API keys")
                
                # Mensaje específico según el modelo
                if GEMINI_MODEL_SELECTED == "gemini-2.5-flash":
                    logger.warning("⚠️ gemini-2.5-flash tiene límite de 20 requests/día")
                    logger.warning(f"💡 Keys disponibles: {len(GEMINI_API_KEYS)}, Key actual: #{CURRENT_KEY_INDEX + 1}")
                
                return fallback_text
            
            logger.error(f"Gemini output error (returning fallback): {e}")
            pass
    return fallback_text

def analizar_sentimiento(audio_path: str):
    text = llm_text_or_mock(SENTIMENT_PROMPT, audio_path,
                             "### Resumen Cálido\nMock\n\n### Comentario Emocional\nMock\n\n### Valoración\n7")
    resumen_match = re.search(r"### Resumen Cálido\s*(.*?)\s*### Comentario Emocional", text, re.DOTALL|re.IGNORECASE)
    comentario_match = re.search(r"### Comentario Emocional\s*(.*?)\s*### Valoración", text, re.DOTALL|re.IGNORECASE)
    valor_match = re.search(r"### Valoración\s*(\d{1,2})", text, re.IGNORECASE)

    resumen = (resumen_match.group(1).strip() if resumen_match else "").strip() or "Resumen no encontrado"
    comentario = (comentario_match.group(1).strip() if comentario_match else "").strip() or "Comentario no encontrado"
    try:
        valor = int(valor_match.group(1)) if valor_match else 7
    except Exception:
        valor = 7
    if valor >= 8:
        clasificacion = "Positiva"
    elif valor == 7:
        clasificacion = "Neutra"
    else:
        clasificacion = "Negativa"
    return valor, clasificacion, comentario, resumen

def analizar_sentimiento_por_roles(audio_path: str):
    fallback = {
        "cliente": {"valor": 6, "clasificacion": "Neutra", "comentario": "Mock", "resumen": "Mock"},
        "asesor":  {"valor": 8, "clasificacion": "Positiva", "comentario": "Mock", "resumen": "Mock"}
    }
    try:
        data = llm_json_or_mock(ROLE_SENTIMENT_PROMPT, audio_path, fallback)
    except Exception:
        data = fallback

    def _norm(d):
        v = d.get("valor", 7)
        try: v = int(v)
        except Exception: v = 7
        c = "Positiva" if v >= 8 else ("Neutra" if v == 7 else "Negativa")
        return {
            "valor": v,
            "clasificacion": d.get("clasificacion", c) or c,
            "comentario": d.get("comentario", ""),
            "resumen": d.get("resumen", "")
        }

    return _norm(data.get("cliente", {})), _norm(data.get("asesor", {}))
