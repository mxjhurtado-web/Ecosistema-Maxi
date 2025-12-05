
import base64
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from ..config.settings import SA_JSON_B64, GS_AUTH_SHEET_ID

logger = logging.getLogger("athenas_lite")

def _load_sa_info():
    if not SA_JSON_B64:
        return None
    try:
        b64c = "".join(SA_JSON_B64.strip().split())
        b64c += "=" * (-len(b64c) % 4)
        data = base64.b64decode(b64c.encode("utf-8"))
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        logger.error(f"Error decoding SA_JSON_B64: {e}")
        return None

def get_credentials(scopes):
    info = _load_sa_info()
    if not info:
        return None
    try:
        return service_account.Credentials.from_service_account_info(info, scopes=scopes)
    except Exception as e:
        logger.error(f"Error creating credentials: {e}")
        return None

def _sheets_service():
    if not GS_AUTH_SHEET_ID:
        return None
    creds = get_credentials(["https://www.googleapis.com/auth/spreadsheets.readonly"])
    if creds is None:
        return None
    return build("sheets", "v4", credentials=creds)

def verificar_correo_online(correo: str):
    logger.info(f"Verificando correo: {correo}")
    try:
        svc = _sheets_service()
        if not svc:
            logger.error("No Service Account or Sheet ID configured.")
            return False, None
            
        meta = svc.spreadsheets().get(spreadsheetId=GS_AUTH_SHEET_ID).execute()
        for s in meta.get("sheets", []):
            title = s["properties"]["title"]
            rows = svc.spreadsheets().values().get(spreadsheetId=GS_AUTH_SHEET_ID, range=f"'{title}'!A:Z").execute().get("values", [])
            if not rows:
                continue
            header = [str(h).strip().lower() for h in rows[0]]
            if "correo" in header:
                i_c = header.index("correo")
                i_n = header.index("nombre") if "nombre" in header else None
                for r in rows[1:]:
                    if i_c < len(r) and str(r[i_c]).strip().lower() == correo.strip().lower():
                        nombre = str(r[i_n]).strip() if (i_n is not None and i_n < len(r)) else correo
                        return True, nombre
    except Exception as e:
        logger.exception(f"Error validando correo online: {e}")
    return False, None
