
import json
import logging
import re
import google.generativeai as genai
from .system_tools import guess_mime

logger = logging.getLogger("athenas_lite")

API_KEY_GEMINI = None
USE_REAL_MODEL = False

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
