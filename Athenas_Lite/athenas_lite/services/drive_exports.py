
import io
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from ..config.settings import DRIVE_EXPORT_FOLDER_ID
from ..auth.google_auth import get_credentials

logger = logging.getLogger("athenas_lite")

def _drive_service():
    if not DRIVE_EXPORT_FOLDER_ID:
        return None
    creds = get_credentials(["https://www.googleapis.com/auth/drive"])
    if creds is None:
        return None
    return build("drive", "v3", credentials=creds)

def subir_csv_a_drive(df, filename: str):
    try:
        svc = _drive_service()
        if not svc:
            logger.warning("Drive service not available (check SA and Folder ID).")
            return None
        
        csv_bytes = df.to_csv(index=False, encoding="utf-8").encode("utf-8")
        media = MediaIoBaseUpload(io.BytesIO(csv_bytes), mimetype="text/csv", resumable=False)
        meta = {"name": filename, "mimeType": "text/csv", "parents": [DRIVE_EXPORT_FOLDER_ID]}
        
        logger.info(f"Uploading {filename} to Drive...")
        f = svc.files().create(body=meta, media_body=media, supportsAllDrives=True, fields="id, webViewLink").execute()
        link = f.get("webViewLink")
        logger.info(f"Upload successful: {link}")
        return link
    except Exception as e:
        logger.exception(f"Fallo subiendo a Drive: {e}")
        return None
