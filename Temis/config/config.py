"""
Google Drive and Gemini API Configuration for TEMIS
"""

import os
import json
import base64

# Google Drive Configuration
# Service Account JSON en BASE64 (configurable via env TEMIS_GOOGLE_SA_BASE64)
SA_JSON_B64 = os.getenv("TEMIS_GOOGLE_SA_BASE64", "").strip()

# Decodificar Service Account JSON
def get_service_account_info():
    """Decode and return service account info from environment"""
    if not SA_JSON_B64:
        raise ValueError("Variable de entorno TEMIS_GOOGLE_SA_BASE64 no configurada o vacía.")
    try:
        b64_clean = "".join(SA_JSON_B64.split())
        b64_clean += "=" * (-len(b64_clean) % 4)
        sa_json_str = base64.b64decode(b64_clean.encode('utf-8')).decode('utf-8')
        return json.loads(sa_json_str)
    except Exception as e:
        raise ValueError(f"Error decodificando TEMIS_GOOGLE_SA_BASE64: {e}")

# Carpeta destino en Shared Drive
DRIVE_FOLDER_ID = os.getenv("TEMIS_DRIVE_FOLDER_ID", "1NA32b-o473ZxcpuLxHPf2xDOt5XHn2CI")

# Scopes para Google Drive
DRIVE_SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]

# Gemini API Configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # Using Gemini 2.5 Flash for high-speed & high-reasoning processing
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Backend API Configuration
API_BASE_URL = "http://localhost:8000/api"

# Get API key from environment or config
def get_gemini_api_key():
    """Get Gemini API key from environment or local config"""
    # Try environment variable first
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key
    
    # Try local config file
    try:
        from desktop.core.gemini_config import GeminiConfig
        config = GeminiConfig()
        return config.get_api_key()
    except:
        return None


# Project structure in Drive
# Each project will have this folder structure:
# Project_Name/
#   00_Portafolio/
#   01_Diagnostico/
#   02_Inicio/
#   03_Planificacion/
#   04_Ejecucion/
#   05_Monitoreo/
#   06_Mejora_Continua/
#   07_Cierre/
#   Diarios/
#   Entregables_Finales/

PHASE_FOLDERS = [
    "00_Portafolio",
    "01_Diagnostico",
    "02_Inicio",
    "03_Planificacion",
    "04_Ejecucion",
    "05_Monitoreo",
    "06_Mejora_Continua",
    "07_Cierre",
    "Diarios",
    "Entregables_Finales"
]
