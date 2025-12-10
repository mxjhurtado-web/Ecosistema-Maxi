
import json
import logging
import os
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
# Estructura de cada key: {"key": "...", "status": "active" | "exhausted"}
GEMINI_API_KEYS = [] 
CURRENT_KEY_INDEX = 0
CURRENT_USER_EMAIL = None

KEYS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "api_keys.json")

def load_api_keys(user_email=None):
    """
    Carga las API keys desde archivo JSON para un usuario específico.
    Si detecta cambio de día, restablece el estatus de las keys a 'active'.
    """
    global GEMINI_API_KEYS, CURRENT_USER_EMAIL
    
    # Actualizar usuario actual si se provee
    if user_email:
        CURRENT_USER_EMAIL = user_email.lower().strip()
        
    target_email = CURRENT_USER_EMAIL or "default"
    
    try:
        if os.path.exists(KEYS_FILE):
            with open(KEYS_FILE, "r") as f:
                full_data = json.load(f)
                
                # Migrar estructura antigua (lista directa) a nueva (diccionario por usuario)
                if isinstance(full_data, list):
                    # Guardar backup de lo antiguo en "default" y estructura vacía
                    old_keys = full_data
                    full_data = {"default": {"keys": [], "last_reset_date": ""}}
                    for k in old_keys:
                        if isinstance(k, str):
                            full_data["default"]["keys"].append({"key": k, "status": "active"})
                        elif isinstance(k, dict):
                            full_data["default"]["keys"].append(k)

                # Cargar datos del usuario
                user_data = full_data.get(target_email, {"keys": [], "last_reset_date": ""})
                GEMINI_API_KEYS = user_data.get("keys", [])
                last_date = user_data.get("last_reset_date", "")
                
                # Verificar cambio de día para resetear
                today = datetime.now().strftime("%Y-%m-%d")
                if last_date != today and GEMINI_API_KEYS:
                    logger.info(f"📅 Nuevo día detectado ({today}). Restableciendo estatus de keys...")
                    for k in GEMINI_API_KEYS:
                        k["status"] = "active"
                    # Guardar actualización de fecha inmediatamente
                    save_api_keys(target_email)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(KEYS_FILE), exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error cargando keys: {e}")
        return False

def save_api_keys(user_email=None):
    """Guarda las API keys en archivo JSON bajo el email del usuario"""
    global CURRENT_USER_EMAIL
    
    # Actualizar usuario actual si se provee
    if user_email:
        CURRENT_USER_EMAIL = user_email.lower().strip()
        
    target_email = CURRENT_USER_EMAIL or "default"
    
    try:
        os.makedirs(os.path.dirname(KEYS_FILE), exist_ok=True)
        
        # Cargar todo el archivo primero para no sobrescribir otros usuarios
        full_data = {}
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, "r") as f:
                    read_data = json.load(f)
                    if isinstance(read_data, dict):
                        full_data = read_data
            except:
                pass # Si falla leer, sobrescribimos
        
        # Actualizar datos de ESTE usuario
        full_data[target_email] = {
            "keys": GEMINI_API_KEYS,
            "last_reset_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        with open(KEYS_FILE, "w") as f:
            json.dump(full_data, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error guardando keys: {e}")

def add_api_key(api_key, user_email=None):
    """Agrega una nueva API key y guarda"""
    api_key = api_key.strip()
    if not api_key: return False
    
    # Verificar duplicados
    for k in GEMINI_API_KEYS:
        if k["key"] == api_key:
            return False
            
    GEMINI_API_KEYS.append({"key": api_key, "status": "active"})
    save_api_keys(user_email)
    
    # Si es la primera, configurarla
    if len(GEMINI_API_KEYS) == 1:
        configurar_gemini()
        
    return True

def remove_api_key(index, user_email=None):
    """Elimina una API key por índice"""
    if 0 <= index < len(GEMINI_API_KEYS):
        GEMINI_API_KEYS.pop(index)
        save_api_keys(user_email)
        return True
    return False

def reset_keys_status(user_email=None):
    """Restablecer estatus de todas las keys a active"""
    for k in GEMINI_API_KEYS:
        k["status"] = "active"
    save_api_keys(user_email)
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

def configurar_gemini(api_key: str = None) -> bool:
    """
    Configura Gemini usando las keys almacenadas.
    El argumento api_key se mantiene por compatibilidad pero se prefiere usar GEMINI_API_KEYS.
    """
    global API_KEY_GEMINI, USE_REAL_MODEL, GEMINI_API_KEYS, CURRENT_KEY_INDEX, CURRENT_USER_EMAIL
    
    try:
        # Si se pasa una key directa string (antiguo método/input manual temporal)
        if api_key and isinstance(api_key, str):
            # No hacemos nada con string directo ahora, preferimos gestión por UI
            pass

        # Intento de carga si está vacío o si queremos asegurar contexto actual
        if not GEMINI_API_KEYS and CURRENT_USER_EMAIL:
            load_api_keys(CURRENT_USER_EMAIL)
        elif not GEMINI_API_KEYS:
             load_api_keys() # Carga default/sin usuario
            
        if not GEMINI_API_KEYS:
             # Fallback si no hay keys cargadas
             if api_key:
                 add_api_key(api_key, CURRENT_USER_EMAIL)
             else:
                 return False
        
        # Buscar primera key activa
        active_found = False
        for i, k in enumerate(GEMINI_API_KEYS):
            if k["status"] == "active":
                CURRENT_KEY_INDEX = i
                API_KEY_GEMINI = k["key"]
                active_found = True
                break
        
        if not active_found:
             # Si todas agotadas, usar la primera aunque falle (o rotar para mostrar error)
             CURRENT_KEY_INDEX = 0
             API_KEY_GEMINI = GEMINI_API_KEYS[0]["key"]

        genai.configure(api_key=API_KEY_GEMINI)
        USE_REAL_MODEL = True
        
        # Solo loguear si hay cambio significativo o es la primera vez
        active_key_masked = f"{API_KEY_GEMINI[:4]}..." if API_KEY_GEMINI else "None"
        logger.info(f"✅ Gemini activo. User: {CURRENT_USER_EMAIL or 'Default'}. Keys: {len(GEMINI_API_KEYS)}. Activa: {active_key_masked}")
        return True
    except Exception as e:
        logger.error(f"Error configurando Gemini: {e}")
        USE_REAL_MODEL = False
        return False

def rotate_api_key() -> bool:
    """
    Marca key actual como agotada y rota a la siguiente activa.
    """
    global API_KEY_GEMINI, CURRENT_KEY_INDEX, GEMINI_API_KEYS
    
    if not GEMINI_API_KEYS: return False
    
    # Marcar actual como agotada
    GEMINI_API_KEYS[CURRENT_KEY_INDEX]["status"] = "exhausted"
    save_api_keys() # Persistir estado
    
    # Buscar siguiente activa
    start_index = CURRENT_KEY_INDEX
    found = False
    
    for _ in range(len(GEMINI_API_KEYS)):
        CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GEMINI_API_KEYS)
        if GEMINI_API_KEYS[CURRENT_KEY_INDEX]["status"] == "active":
            found = True
            break
            
    if not found:
        # Si no hay activas, intentar restablecer ciclo o simplemente fallar
        # Por ahora fallar para que el usuario sepa
        logger.warning("⚠️ TODAS las API keys están agotadas")
        return False
    
    API_KEY_GEMINI = GEMINI_API_KEYS[CURRENT_KEY_INDEX]["key"]
    
    try:
        genai.configure(api_key=API_KEY_GEMINI)
        logger.info(f"🔄 Rotando a API Key #{CURRENT_KEY_INDEX + 1} (Activa)")
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
            # Manejo silencioso como en legacy - solo log mínimo
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning(f"⚠️ Cuota agotada. Rotando key si es posible...")
                if rotate_api_key():
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
                    except:
                        pass
            # Fallback silencioso (como legacy)
            pass
    return fallback

def llm_text_or_mock(prompt: str, audio_path: str, fallback_text: str = None) -> str:
    """Version texto simple"""
    global USE_REAL_MODEL
    
    if not USE_REAL_MODEL:
        return "Resumen Mock Texto"
        
    model = _gemini_model()
    if model:
        try:
            wait_time = rate_limiter.wait_if_needed()
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
                
            resp = model.generate_content(
                [prompt, {"mime_type": guess_mime(audio_path), "data": audio_bytes}]
            )
            return (getattr(resp, "text", None) or "").strip()
        except:
            # Fallback silencioso (como legacy)
            pass
    return fallback_text or ""

def analizar_sentimiento(audio_path: str):
    text = llm_text_or_mock(SENTIMENT_PROMPT, audio_path)
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
