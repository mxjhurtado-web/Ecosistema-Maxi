
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
    api_key = (api_key or "").strip()
    if not api_key:
        USE_REAL_MODEL = False
        API_KEY_GEMINI = None
        return False
    try:
        genai.configure(api_key=api_key)
        API_KEY_GEMINI = api_key
        USE_REAL_MODEL = True
        logger.info("Gemini configured successfully.")
        return True
    except Exception as e:
        logger.error(f"Error configuring Gemini: {e}")
        USE_REAL_MODEL = False
        return False

def _gemini_model(name="gemini-2.5-flash"):
    if USE_REAL_MODEL:
        try:
            return genai.GenerativeModel(name)
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
