"""
Google Drive and Gemini API Configuration for TEMIS
"""

import os
import json
import base64

# Google Drive Configuration
# Service Account JSON en BASE64 (temis-sa@temis-509017.iam.gserviceaccount.com)
SA_JSON_B64 = os.getenv("TEMIS_GOOGLE_SA_BASE64", "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogInRlbWlzLTUwOTAxNyIsICJwcml2YXRlX2tleV9pZCI6ICJjM2UyYTRhNGUxMGUyMDg2Yjk4NmY4ZDY0YmQ5NzViNWFkN2NlMDQ3IiwgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXZnSUJBREFOQmdrcWhraUc5dzBCQVFFRkFBU0NCS2d3Z2dTa0FnRUFBb0lCQVFEWGJZWWhreHJLelRYblxub0NyUGREakpVTTd3NTJ1a2xuZGx4SndkWDhVdDBRU01yNGRqRjVOZUNNK3JjclFWK05lN2gvaHZneWhGMCt3UlxuWjNoK01ZTVQvZWk2R0RNd0RzeWtZRy85N244dnZqcUcvZ3pIby8rWklCaTBWaklIOGlqeVlwVGtnZUVHdThFaVxuamNqajk5MERZLzBtckxVS1ZoQXBCWVBYZTlicEV1UkY2WW1QVWhVSjVsblBEUzNhZ3ZXdFNBM1owN2dDRWNGS1xuNkViYVVBNVhKRXFEVUFidUxEdzBiVWJCc3FMcmUzbGg0RVpJeHFoL08yZnJlTVFBa1ZpR2ZBZnZLdXVacjVJR1xudkNOMExyU3kvZGpLQlhUQTFoQnkveWVJdXlFUnBxYTBiTGRuNXR3TGFQSzJJY0MzMjZ5dExtaE9pYkVoeVhROFxuZ0JBcTRPNXZBZ01CQUFFQ2dnRUFSK1FTYTNqcWEzeEEvV3VyYmJDMDFLWGxjV3BoTnp0SlhBcFpLTXBSaElFb1xudWdSSHM0OW1DKzczMHBqRU5VTG1SM3hRTVhKOUNaUjN4clVYZGxGeWswVGNHZUpDanNxWmkwOXRnRG5MY3ZUU1xuRmtPSW8wVDg0cTVkNEN5VnBLWXcrUFppQnNHN0JTSzZDSngxU25Kb2JKMjlHTjl3eVNMQVlOZ296OHZSZzlTL1xuVnFMVjlHU1hTcC9GcjdYUDMrUGRHQnY5czh1ak5pSWRNSmxSTzBLcnJ0bXphSVozU0J1NkQwb3VIVVVydmlLTFxuL0QwcGVoMDRsU29ES2t3dmxUeCthWHhqU2lPamwvR2Njc0VDRjVROFZpZ0IvREZPbU1OM2dFQncxL01tWEJ4RFxuN0pRR2pRUDFmZk8xV1JIRFhLeGNXTno5UGVTQVBkdGJmZzJHbzlKRHVRS0JnUUQvSXIvenRjamkxS0xvVzdsb1xuc0t5b2l4Zkk3TzVwanN5L0xCanhoaCt4Sm0xZ0o1cEZISlR5a1QwSEMzSzA1STRHL1lYbEUxdnhVTmNSU1ZoeFxucDBYN2F0TkFiWDA4VDNsZXNPMGkwTFd3U3hMNUd5d0VLVEhrOGszTi95cFR2WFZDeWgyQ3hHZUM5K0N1dXVSSVxueFBVZnU2VVpJRkpjSVRDOFVqU0Rid1JIeVFLQmdRRFlLRmNKTEZhamtLL0tFTDdaVkVpUmV4ekp2RjRaVGlGOFxuSUxCQ0FLZkxJem05LzUxTG5McmFKUVU5THlUcmRFVFV3bnd0Ri9WUE4yWGxyNEhTYzc5VTloOXpMbmR3bHZSMFxuREtDM1FGckVGTFpoUFluN0tKQTlGbG5qQzlibXVld0RSY2ZoS1g1TTNPYkd0Vm8vS3RaaXBsWjZXMVpMOTdBTVxuZko5VzhhOFFkd0tCZ1FEV3ZlL2tkL2dxZTZEV2hBV05pVTc1MllEZWZCVzdRUmN5UFRLTmJ6K1RnbTJEQmpKQlxudzJuV3RNb3grTC9HWTZ6clUwMzBYcFAvaS9SSk4zdTZ4WGtRd1h3bmVVQjBsOHZuR0hHdjRRMWI0Z1NKS1FhbVxuUmVvWjhwdnNLNzM3bDdadnplQ0M1VDdlckRZdnUxeFRwM3RPQjBsUjJiT1ltZE1FWHdpV0s4WGxpUUtCZ0cvZFxuNkxWUm9nRUNkMGVQQlFZNmpWZmxMQS9ua1pkdERQMU5lWXFmQmplbUlsTUhQK09LMkZUZlJlZlZSemtuc2h1ZVxuRDEvUy8xeWc0ZlpOcjFVNEcvUWZjRVZPN2ZkeDJFOWEzYTRZK3lCeFM3WGxnRXhnUU0yc2pKWnBZUzJGV1BTVVxubjQ0U3lFK0ZIMVlGTXhCdjNnV3Q2aUZtdGJHWkhSNUpQTGxsV09HZkFvR0JBT1RkdkJmNHhrQkJkU3FPZUpGVlxuZ01scUp1M3pFZFh5TzRPUGdhazFldE44UEVZaThjQjExOU9IUWJFcC9ieUlDMTdnamJndmVyRkF4TmJBeitPQlxuRXRIdHBsUG5SVVpZdU12UWVqTzc0UWl5SnJrUUtuSzV5U0h5VmJYOEFwdUlDV2pVMkJMOE1KOElEUG1Oc3VlNlxuRmVuZjcyNWg2cFBRbXVGMnl0U3NqYm9MXG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLCAiY2xpZW50X2VtYWlsIjogInRlbWlzLXNhQHRlbWlzLTUwOTAxNy5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsICJjbGllbnRfaWQiOiAiMTE0OTg5MjU4NTQ2Nzk2MTkzODM3IiwgImF1dGhfdXJpIjogImh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9hdXRoIiwgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsICJhdXRoX3Byb3ZpZGVyX3g1MDlfY2VydF91cmwiOiAiaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vb2F1dGgyL3YxL2NlcnRzIiwgImNsaWVudF94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL3JvYm90L3YxL21ldGFkYXRhL3g1MDkvdGVtaXMtc2ElNDB0ZW1pcy01MDkwMTcuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIn0=")

# Decodificar Service Account JSON
def get_service_account_info():
    """Decode and return service account info"""
    sa_json_str = base64.b64decode(SA_JSON_B64).decode('utf-8')
    return json.loads(sa_json_str)

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
