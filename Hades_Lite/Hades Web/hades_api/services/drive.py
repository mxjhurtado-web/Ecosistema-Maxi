"""
Servicio de Google Drive para exportación de resultados.

Usa la misma service account que Hades Ultimate.
"""

import base64
import json
import re
import io
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


# Service Account JSON (Base64) - MISMO QUE HADES ULTIMATE
SA_JSON_B64 = "ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAibWF4aWJvdC00NzI0MjMiLAogICJwcml2YXRlX2tleV9pZCI6ICJmOTFkMGRjYWM2ODA4NTYyY2IxOTRlOWM0NmU5ZDM2MGY1ZTNjNTczIiwKICAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUURIN0IrZ0JnTU9ScElmXG50ejJQSWRieXpoUnduSitVcitZN05JT1FsRGpNMWgweEl3dUIrNHZ6M2w4M1J1dWJ5VEQvbUQ1NklDckJONkg2XG50RkNDcTErbytsMWl0T1lHYkNVajdCcnBZM3ZnbHJmUVJFcUdnV1EzT2lxdGR6bHE3b3RhZk11K1d6bVlKODVQXG5QNnl1SUVJbnUyVXFEYW5WV3ZrL2Q1WnlaRkF3UG9IRDVIMldKcGlwblNhTW1HcXhDRG5RWTAxVDAwUWRiaStIXG42NlFscXdCQURFajZXWHhCNm1BdXZIdXRJTG4vaWRsYWpZRU4zVDd3OTJ1Q2JPNVk1dlFuUlI1TGViS1paaE5hXG5ZbTlPanp3TE9SekFPVG9rWCswWXZxUGFhTXplV2lncWY5RDJMZ3NMbE1sZnpBNXpxQkhEV0szaTJGMngvYWNXXG5jVkJIRzI2N0FnTUJBQUVDZ2dFQUNndWVSeThtSmloN25TWmE3SDg1eXJkNkpYSnBQbEpjVWl0QVZScHRoRFZhXG5BQ2NQby9kY3YrTXppNVovcmpNOHlBc0JVS2VmSGxoS1JrdWJKQVd5Wjg0MHRRbjc2T1MwTlFyZkMwMFpZMTZQXG5XK0tpa0FHZVpId0N1dmFicHZqWGZiTjVsVllHSGRRYU5MY3hXUXA3NkgwdEJ5RHFvTExTaFZMZjkxMTgvZjkvXG5RVGlIMk1pMkZNS3crVS93ckVsbmV0SFIrSE1vV2Fia2picGx4cEZQRDNMTkpWU0oybHkwUzBzb2praDV0WEZ5XG5ubDJXVUJPd1FTVmNmQzhvVHNwQXM3SUpXRzZVYldBc2dkZHlWZUU1VDRkZGFoa0JDSEhYQVFBUVYzYjJFTGM2XG54USs5WVFxS2VJNmNTMW5OeHNRUjBlK1V3OG1zT3V1MElSS3Mva2hmQVFLQmdRRHlzUGVGaFJUZ01kd1NsS2dCXG5vVHlnTUxtd3JVUGhzMXJ6d1g1eEVaUWtSRmVjb2F4M0U3WDJFTnRpR1AyRm9oU0R4VVd4TFE3czMyaFFOU0RpXG5tbmh1NWs4SVk1Nmt2VGxjbzlMeDV5TEF5UHEyTFNQWDUrYmowZXkzdEZkVXFaT0dqWlRrV0R3NUh4QlBRMHIyXG5BbFFKT01RUURMRHFPQnFXWUd4YksydHdPd0tCZ1FEUzRyNDkybk92TGhMaHYyMm0yUTlVa3BRcis4RC9udXQ5XG45ajJwSzFQQ1dRRmJhSHRVWit3NFhPUk1pczVqM3ZaTkg3aDd0Z3hvM0FhTGhGMS8wSlJYaTlpS2V2SmpKU0JjXG5zREI2SFE5cFBmNUU0SHNPOE9zejBDNjMzYXNMUFNZakIwNFdUWkVtQ0J2dFoxeGtXZHpQdG1VajZSYThSZUkwXG56TkFDeXpLVGdRS0JnQmZ3enlvVHU4QjJDckNtaTRCRnFKWmcyQ0NPcHhDZndjd2ovVllvRnNZUkc5ZHV0M1d6XG5zeEtJRFN3N0xOOCs0dWt3ejdRdnJyWTlQNndSNGFHWS9XSnJROGFmRlNwSkpGeDRLTG9HUkE1aWhTRHRpUWltXG5ic2R3a1BwNlJ0Y3FOMHhoc1J0cGZOOWhxaGszbVRCMWdGYThpOUxOZmJKTlFJb3ZEdUZiZ2lpN0FvR0FPdGdZXG5PNHdzUVpKNnBGRlZHSHh5NGFkdy93RGxycTQ2aWRCZkRraFB1K2c0RDdpTXlWV2lQV3YyTEVHREs2ejRUemJ0XG50Rjl0QVFsOExnd0dSdmI5blp3aEZTc1BYWWpyaWRHRUJWNzhnT0pTaEFlYmJ1VGN6SDFudTloM3ROQWdSeC92XG5zeHQ3eC8vMVF2NVhjb3o4cDF6K3hkRnhqYUYyYUVOS082MVZkSUVDZ1lFQXovMTRCVnZDQ2MzRGg0elBFOXlBXG4weEp0ZDhzNUw2YUdnT3h5RzRZR3VuKzZ0QTBKOWZvUWV4cHd2azFpWGlOYXZvWTNWN3haRUNSSm1ua2l4TEEzXG53bWZ3YzZFTkVWWjg0b2Y0VU42SVRSdCtHRytGZThTaE05STBFVHpFYWlTcmQvT0VxQ1VQZVlNelNQQVNIakRCXG5PdW1LWHlkU2N5NWhlNUdpNm9rc2MyWT1cbi0tLS0tRU5EIFBSSVWQVRFIEtFWS0tLS0tXG4iLAogICJjbGllbnRfZW1haWwiOiAibWF4aWJvdC1zYUBtYXhpYm90LTQ3MjQyMy5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMTY5MjAxMTQ4NzE4MDE2MTExMzkiLAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsCiAgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L21heGlib3Qtc2ElNDBtYXhpYm90LTQ3MjQyMy5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgInVuaXZlcnNlX2RvbWFpbiI6ICJnb29nbGVhcGlzLmNvbSIKfQo="

# Carpeta de destino en Google Drive - MISMA QUE HADES ULTIMATE
DRIVE_FOLDER_ID = "1eexrVXQYRZLk9hnJwLVYJp5PkYnjx2bt"

# Scopes necesarios
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]


def _load_sa_info() -> Dict[str, Any]:
    """
    Carga la información de la service account desde Base64.
    
    Mismo código que Hades Ultimate.
    """
    if not SA_JSON_B64 or "PEGA_AQUI" in SA_JSON_B64:
        raise RuntimeError("Falta SA_JSON_B64 (CONFIG MANUAL).")
    
    try:
        # Limpieza extrema
        b64c_raw = SA_JSON_B64.strip()
        b64c = re.sub(r'[^A-Za-z0-9+/=]', '', b64c_raw)
        
        # Asegurar padding correcto
        missing_padding = len(b64c) % 4
        if missing_padding != 0:
            b64c += '=' * (4 - missing_padding)
        
        # Decodificación
        data = base64.b64decode(b64c.encode("utf-8"))
        return json.loads(data.decode("utf-8"))
        
    except (base64.binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
        raise RuntimeError(
            f"SA_JSON_B64 es un Base64/JSON inválido. "
            f"Detalle: {e}"
        )


def get_drive_credentials():
    """
    Obtiene las credenciales de Google Drive.
    
    Returns:
        Credentials object
    """
    if not GOOGLE_AVAILABLE:
        raise RuntimeError("Google API no disponible. Instala: google-auth google-api-python-client")
    
    try:
        info = _load_sa_info()
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    except Exception as e:
        raise RuntimeError(f"Error al cargar credenciales: {e}")


def get_drive_service():
    """
    Obtiene el servicio de Google Drive.
    
    Returns:
        Google Drive service
    """
    if not GOOGLE_AVAILABLE:
        raise RuntimeError("Google API no disponible")
    
    try:
        credentials = get_drive_credentials()
        return build("drive", "v3", credentials=credentials, cache_discovery=False)
    except Exception as e:
        raise RuntimeError(f"Error al inicializar Drive API: {e}")


def validate_folder(folder_id: str = DRIVE_FOLDER_ID) -> Tuple[bool, Optional[str]]:
    """
    Valida que la carpeta de Drive exista y sea accesible.
    
    Args:
        folder_id: ID de la carpeta
        
    Returns:
        Tupla de (success, error_message)
    """
    try:
        service = get_drive_service()
        
        # Intentar obtener metadata de la carpeta
        file_metadata = service.files().get(
            fileId=folder_id,
            fields="id, name, mimeType"
        ).execute()
        
        # Verificar que sea una carpeta
        if file_metadata.get("mimeType") != "application/vnd.google-apps.folder":
            return False, f"El ID {folder_id} no es una carpeta"
        
        return True, None
        
    except HttpError as e:
        return False, f"Error al acceder a la carpeta: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def upload_json_to_drive(
    json_data: Dict[str, Any],
    filename: str,
    folder_id: str = DRIVE_FOLDER_ID
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Sube un archivo JSON a Google Drive.
    
    Args:
        json_data: Datos a subir
        filename: Nombre del archivo
        folder_id: ID de la carpeta destino
        
    Returns:
        Tupla de (success, file_id, error_message)
    """
    try:
        service = get_drive_service()
        
        # Convertir a JSON string
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        
        # Metadata del archivo
        file_metadata = {
            'name': filename,
            'parents': [folder_id],
            'mimeType': 'application/json'
        }
        
        # Media
        media = MediaIoBaseUpload(
            io.BytesIO(json_bytes),
            mimetype='application/json',
            resumable=True
        )
        
        # Upload
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        web_link = file.get('webViewLink')
        
        return True, file_id, web_link
        
    except HttpError as e:
        return False, None, f"Error HTTP: {e}"
    except Exception as e:
        return False, None, f"Error: {e}"


def export_result_to_drive(
    result_data: Dict[str, Any],
    user_email: str,
    job_id: str
) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Exporta un resultado de análisis a Google Drive.
    
    Organiza por fecha y usuario:
    - Carpeta raíz: DRIVE_FOLDER_ID
    - Subcarpeta: YYYY-MM-DD
    - Archivo: hades_{user_email}_{job_id}.json
    
    Args:
        result_data: Resultado del análisis
        user_email: Email del usuario
        job_id: ID del job
        
    Returns:
        Tupla de (success, file_id, web_link, error_message)
    """
    try:
        service = get_drive_service()
        
        # Crear subcarpeta por fecha (si no existe)
        today = datetime.now().strftime("%Y-%m-%d")
        date_folder_id = _get_or_create_folder(service, today, DRIVE_FOLDER_ID)
        
        # Nombre del archivo
        safe_email = user_email.replace("@", "_at_").replace(".", "_")
        filename = f"hades_{safe_email}_{job_id}.json"
        
        # Upload
        success, file_id, web_link = upload_json_to_drive(
            result_data,
            filename,
            date_folder_id
        )
        
        if success:
            return True, file_id, web_link, None
        else:
            return False, None, None, web_link  # web_link contiene el error
            
    except Exception as e:
        return False, None, None, f"Error: {e}"


def _get_or_create_folder(
    service,
    folder_name: str,
    parent_id: str
) -> str:
    """
    Obtiene o crea una subcarpeta.
    
    Args:
        service: Drive service
        folder_name: Nombre de la carpeta
        parent_id: ID de la carpeta padre
        
    Returns:
        ID de la carpeta
    """
    # Buscar si ya existe
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    files = results.get('files', [])
    
    if files:
        # Ya existe
        return files[0]['id']
    
    # Crear nueva carpeta
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    
    folder = service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()
    
    return folder.get('id')
