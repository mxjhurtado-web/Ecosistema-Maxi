"""
Service for logging conversations to Google Sheets in real-time.
Uses the same Service Account credentials configured for Google Chat.
"""

import base64
import json
import logging
import httpx
from typing import Optional
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from .config_manager import config_manager
from shared.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """Service to interact with Google Sheets and Google Drive using the Service Account"""
    
    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.parent_folder_id = "1WDoC72ycPqsBvtjc_dj9Ljcue1QmvPMy"
        self.sheet_name = "ORBIT_Conversations_Log"
        
    async def _get_credentials(self, sa_b64: str):
        """Decode SA and load credentials with sheets and drive scopes"""
        try:
            sa_json = base64.b64decode(sa_b64).decode('utf-8')
            sa_info = json.loads(sa_json)
            logger.info(f"🔑 [CREDENTIAL DIAGNOSTIC] Loaded Service Account email: {sa_info.get('client_email')}")
            return service_account.Credentials.from_service_account_info(
                sa_info, scopes=self.scopes
            )
        except Exception as e:
            logger.error(f"Failed to load Google Sheets Service Account: {str(e)}")
            return None
            
    async def _get_spreadsheet_id(self, creds) -> Optional[str]:
        """Get existing spreadsheet ID from Redis or find/create it in Google Drive"""
        redis = None
        # 1. Try Redis cache first
        try:
            redis = await get_redis_client()
            cached_id = await redis.get("google_sheets:spreadsheet_id")
            if cached_id:
                return cached_id.decode('utf-8')
        except Exception as e:
            logger.warning(f"Redis cache check failed for sheet ID: {str(e)}")

        token = creds.token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 1.5. Intentar buscar una carpeta llamada "Registro Orbit" compartida con la Service Account
        folder_id = self.parent_folder_id
        try:
            folder_search_url = "https://www.googleapis.com/drive/v3/files"
            q_folder = "mimeType = 'application/vnd.google-apps.folder' and name = 'Registro Orbit' and trashed = false"
            params_folder = {
                "q": q_folder,
                "spaces": "drive",
                "fields": "files(id, name)",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true"
            }
            async with httpx.AsyncClient() as client:
                folder_response = await client.get(folder_search_url, headers=headers, params=params_folder)
                if folder_response.status_code == 200:
                    folders = folder_response.json().get("files", [])
                    if folders:
                        folder_id = folders[0]["id"]
                        logger.info(f"📁 Dynamically discovered folder 'Registro Orbit' ID: {folder_id}")
        except Exception as fe:
            logger.warning(f"Failed to dynamically search for 'Registro Orbit' folder: {str(fe)}")

        # 2. Search in Google Drive folder
        try:
            search_url = "https://www.googleapis.com/drive/v3/files"
            q = f"name = '{self.sheet_name}' and '{folder_id}' in parents and trashed = false"
            params = {
                "q": q,
                "spaces": "drive",
                "fields": "files(id, name)",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true"
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(search_url, headers=headers, params=params)
                if response.status_code == 200:
                    files = response.json().get("files", [])
                    if files:
                        spreadsheet_id = files[0]["id"]
                        logger.info(f"📁 Found existing Google Sheet in Drive: {spreadsheet_id}")
                        if redis:
                            try:
                                await redis.set("google_sheets:spreadsheet_id", spreadsheet_id)
                            except Exception:
                                pass
                        return spreadsheet_id
        except Exception as e:
            logger.error(f"Failed to search for Google Sheet in Drive: {str(e)}")

        # 3. Create a new Spreadsheet in the folder (with fallback to root Drive)
        try:
            create_url = "https://www.googleapis.com/drive/v3/files?supportsAllDrives=true"
            payload = {
                "name": self.sheet_name,
                "mimeType": "application/vnd.google-apps.spreadsheet",
                "parents": [folder_id]
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(create_url, json=payload, headers=headers)
                if response.status_code == 200:
                    spreadsheet_id = response.json().get("id")
                    logger.info(f"✨ Created NEW Google Sheet in folder '{folder_id}': {spreadsheet_id}")
                    
                    # Write headers immediately
                    await self._write_headers(spreadsheet_id, token)
                    
                    if redis:
                        try:
                            await redis.set("google_sheets:spreadsheet_id", spreadsheet_id)
                        except Exception:
                            pass
                    return spreadsheet_id
                else:
                    logger.warning(f"⚠️ Failed to create Google Sheet in folder '{folder_id}' ({response.status_code}): {response.text}. Retrying in root drive...")
                    
                    # Fallback to root Drive
                    payload_fallback = {
                        "name": self.sheet_name,
                        "mimeType": "application/vnd.google-apps.spreadsheet"
                    }
                    response_fallback = await client.post(create_url, json=payload_fallback, headers=headers)
                    if response_fallback.status_code == 200:
                        spreadsheet_id = response_fallback.json().get("id")
                        logger.info(f"✨ Created NEW Google Sheet in ROOT drive: {spreadsheet_id}")
                        
                        await self._write_headers(spreadsheet_id, token)
                        
                        if redis:
                            try:
                                await redis.set("google_sheets:spreadsheet_id", spreadsheet_id)
                            except Exception:
                                pass
                        return spreadsheet_id
                    else:
                        logger.error(f"❌ Failed to create Google Sheet in root drive ({response_fallback.status_code}): {response_fallback.text}")
        except Exception as e:
            logger.error(f"Failed to create Google Sheet: {str(e)}")
            
        return None

    async def _write_headers(self, spreadsheet_id: str, token: str):
        """Write the initial column headers to the spreadsheet"""
        headers_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:I1?valueInputOption=USER_ENTERED"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "values": [[
                "Fecha",
                "Trace ID",
                "ID Conversación",
                "ID Contacto",
                "Canal",
                "Mensaje Usuario",
                "Respuesta Bot",
                "Latencia (ms)",
                "Estatus"
            ]]
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(headers_url, json=payload, headers=headers)
                if response.status_code == 200:
                    logger.info("✅ Written column headers to the spreadsheet successfully!")
                else:
                    logger.error(f"Failed to write headers ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"Failed to write headers: {str(e)}")

    async def append_log(
        self,
        timestamp: str,
        trace_id: str,
        conversation_id: str,
        contact_id: str,
        channel: str,
        user_text: str,
        bot_response: str,
        latency_ms: int,
        status: str
    ) -> bool:
        """Append a conversation log row to the Google Sheet"""
        config = await config_manager.get_google_chat_config()
        sa_b64 = config.sa_json_b64
        
        if not sa_b64:
            logger.warning("Google Sheet logging skipped: Service Account credentials not configured")
            return False
            
        try:
            # 1. Get credentials and refresh token
            creds = await self._get_credentials(sa_b64)
            if not creds:
                logger.error("Failed to load credentials for Google Sheets")
                return False
                
            creds.refresh(Request())
            
            # 2. Get spreadsheet ID
            spreadsheet_id = await self._get_spreadsheet_id(creds)
            if not spreadsheet_id:
                logger.error("Failed to get spreadsheet ID")
                return False
                
            # 3. Append row
            append_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:append?valueInputOption=USER_ENTERED"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            payload = {
                "values": [[
                    timestamp,
                    trace_id,
                    conversation_id,
                    contact_id,
                    channel,
                    user_text,
                    bot_response,
                    latency_ms,
                    status
                ]]
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(append_url, json=payload, headers=headers)
                if response.status_code == 200:
                    logger.info(f"📊 Log appended to Google Sheets for trace {trace_id}")
                    return True
                else:
                    logger.error(f"Failed to append log row to Google Sheets ({response.status_code}): {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Failed to append log row to Google Sheets: {str(e)}")
            return False

    async def append_csat_log(
        self,
        timestamp: str,
        contact_id: str,
        contact_name: str,
        rating: int,
        comment: str,
        assigned_agent: str
    ) -> bool:
        """Append a CSAT response row to the designated Google Sheet"""
        config = await config_manager.get_google_chat_config()
        sa_b64 = config.sa_json_b64
        
        if not sa_b64:
            logger.warning("Google Sheet CSAT logging skipped: Service Account credentials not configured")
            return False
            
        try:
            creds = await self._get_credentials(sa_b64)
            if not creds:
                logger.error("Failed to load credentials for Google Sheets")
                return False
                
            creds.refresh(Request())
            
            spreadsheet_id = "1cpHiHYIHYZcDHdxgGrW5RD1ufefo_ROzqO4FwMRtG9Y"
            
            append_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:append?valueInputOption=USER_ENTERED"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            payload = {
                "values": [[
                    timestamp,
                    contact_id,
                    contact_name,
                    rating,
                    comment,
                    assigned_agent
                ]]
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(append_url, json=payload, headers=headers)
                if response.status_code == 200:
                    logger.info(f"📊 CSAT log appended to Google Sheet for contact {contact_id}")
                    return True
                else:
                    logger.error(f"Failed to append CSAT log to Google Sheets ({response.status_code}): {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Failed to append CSAT log to Google Sheets: {str(e)}")
            return False

    async def fetch_faq_data(self, spreadsheet_id: str) -> Optional[str]:
        """Fetch FAQ data from a Google Sheet and format it as a knowledge base block for Gemini"""
        config = await config_manager.get_google_chat_config()
        sa_b64 = config.sa_json_b64
        
        if not sa_b64:
            logger.warning("Google Sheet FAQ fetch skipped: Service Account credentials not configured")
            return None
            
        redis = None
        # 1. Try Redis cache first to avoid hitting Google API limits
        try:
            redis = await get_redis_client()
            cached_faq = await redis.get(f"google_sheets:faq_cache:v3:{spreadsheet_id}")
            if cached_faq:
                logger.info(f"✅ Loaded FAQ from Redis cache for sheet {spreadsheet_id}")
                return cached_faq.decode('utf-8')
        except Exception as e:
            logger.warning(f"Redis cache check failed for FAQ: {str(e)}")

        try:
            # 2. Get credentials and refresh token
            creds = await self._get_credentials(sa_b64)
            if not creds:
                logger.error("Failed to load credentials for Google Sheets FAQ fetch")
                return None
                
            creds.refresh(Request())
            
            # 3. Fetch sheet values (Contenido!A1:C with fallback to A1:C)
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/Contenido!A1:C"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    logger.warning("Failed to fetch FAQ from tab 'Contenido', trying default leftmost tab...")
                    url_fallback = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:C"
                    response = await client.get(url_fallback, headers=headers)
                    
                if response.status_code != 200:
                    logger.error(f"Failed to fetch FAQ from Google Sheets ({response.status_code}): {response.text}")
                    return None
                    
                data = response.json()
                rows = data.get("values", [])
                
                if not rows:
                    logger.warning("Google Sheets FAQ is empty")
                    return None
                
                # Format rows into a clean knowledge base string
                faq_lines = []
                
                # Dynamic column mapping based on headers
                q_idx = 0
                a_idx = 1
                start_idx = 0
                
                first_row = [str(cell).lower().strip() for cell in rows[0]]
                logger.info(f"📊 [FAQ DIAGNOSTIC] Detected headers: {first_row}")
                
                # Check if first row is a header
                is_header = False
                for idx, cell in enumerate(first_row):
                    if "pregunta" in cell or "question" in cell or "faq" in cell:
                        q_idx = idx
                        is_header = True
                    if "respuesta" in cell or "answer" in cell or "solución" in cell or "solucion" in cell:
                        a_idx = idx
                        is_header = True
                        
                if is_header:
                    start_idx = 1
                    logger.info(f"🎯 [FAQ DIAGNOSTIC] Dynamic mapping: Question col={q_idx}, Answer col={a_idx}")
                else:
                    logger.info("⚠️ [FAQ DIAGNOSTIC] No header row recognized, using default mapping (col 0: Question, col 1: Answer)")

                for idx, row in enumerate(rows[start_idx:]):
                    if len(row) > max(q_idx, a_idx):
                        question = row[q_idx].strip()
                        answer = row[a_idx].strip()
                        if question and answer:
                            faq_lines.append(f"Pregunta {idx+1}: {question}\nRespuesta {idx+1}: {answer}\n")
                            
                faq_text = "\n".join(faq_lines)
                
                if faq_text and redis:
                    try:
                        # Cache for 60 seconds (1 minute) during testing and setup
                        await redis.setex(f"google_sheets:faq_cache:v3:{spreadsheet_id}", 60, faq_text)
                        logger.info("Saved FAQ to Redis cache (60s TTL)")
                    except Exception:
                        pass
                        
                return faq_text
                
        except Exception as e:
            logger.error(f"Failed to fetch or parse FAQ from Google Sheets: {str(e)}")
            return None

    async def read_drive_document(self, file_id: str, file_type: str) -> Optional[str]:
        """
        Read the content of a Google Doc, Google Sheet, PDF, or Plain Text file from Google Drive
        using the Service Account credentials.
        """
        config = await config_manager.get_google_chat_config()
        sa_b64 = config.sa_json_b64
        
        if not sa_b64:
            logger.warning("Google Drive read skipped: Service Account credentials not configured")
            return None
            
        try:
            # 1. Get credentials and refresh token
            creds = await self._get_credentials(sa_b64)
            if not creds:
                logger.error("Failed to load credentials for Google Drive read")
                return None
                
            creds.refresh(Request())
            token = creds.token
            headers = {
                "Authorization": f"Bearer {token}",
            }
            
            async with httpx.AsyncClient() as client:
                # Handle Google Doc export
                if file_type == "google_doc":
                    logger.info(f"📄 Exporting Google Doc {file_id} to text (supportsAllDrives=true)...")
                    url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType=text/plain&supportsAllDrives=true"
                    response = await client.get(url, headers=headers, timeout=20)
                    if response.status_code == 200:
                        return response.text
                    else:
                        logger.error(f"Failed to export Google Doc ({response.status_code}): {response.text}")
                        return None
                        
                # Handle Google Sheet export
                elif file_type == "google_sheet":
                    logger.info(f"📊 Exporting Google Sheet {file_id} to CSV (supportsAllDrives=true)...")
                    url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType=text/csv&supportsAllDrives=true"
                    response = await client.get(url, headers=headers, timeout=20)
                    if response.status_code == 200:
                        return response.text
                    else:
                        logger.error(f"Failed to export Google Sheet ({response.status_code}): {response.text}")
                        return None
                        
                # Handle generic file download (PDF or Plain Text)
                else:
                    # 1. Fetch metadata first to know the mimeType
                    meta_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=name,mimeType&supportsAllDrives=true"
                    meta_response = await client.get(meta_url, headers=headers, timeout=10)
                    mime_type = "unknown"
                    file_name = "unknown"
                    if meta_response.status_code == 200:
                        meta = meta_response.json()
                        mime_type = meta.get("mimeType", "unknown").lower()
                        file_name = meta.get("name", "unknown")
                        logger.info(f"📂 Found Drive file: '{file_name}' | MimeType: {mime_type}")
                    
                    # 2. Download raw content
                    logger.info(f"📥 Downloading Drive file content {file_id} (supportsAllDrives=true)...")
                    download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&supportsAllDrives=true"
                    response = await client.get(download_url, headers=headers, timeout=30)
                    if response.status_code != 200:
                        logger.error(f"Failed to download Drive file ({response.status_code}): {response.text}")
                        return None
                        
                    content_bytes = response.content
                    
                    # 3. Parse content based on mimeType
                    if "pdf" in mime_type:
                        logger.info(f"🛠️ Parsing PDF content using pypdf ({len(content_bytes)} bytes)...")
                        try:
                            import io
                            from pypdf import PdfReader
                            reader = PdfReader(io.BytesIO(content_bytes))
                            text_pages = []
                            for idx, page in enumerate(reader.pages):
                                page_text = page.extract_text()
                                if page_text:
                                    text_pages.append(f"--- [PÁGINA {idx+1}] ---\n{page_text}")
                            return "\n\n".join(text_pages)
                        except Exception as pdf_err:
                            logger.error(f"Failed to parse PDF using pypdf: {str(pdf_err)}")
                            return f"[Error al parsear el PDF '{file_name}']: {str(pdf_err)}"
                    
                    elif "text" in mime_type or mime_type == "unknown" or "javascript" in mime_type or "json" in mime_type:
                        try:
                            return content_bytes.decode('utf-8', errors='ignore')
                        except Exception as dec_err:
                            logger.error(f"Failed to decode text file: {str(dec_err)}")
                            return None
                    
                    else:
                        return f"[Archivo no soportado]: El archivo '{file_name}' es de tipo {mime_type}, el cual no se puede leer directamente como texto."
                        
        except Exception as e:
            logger.error(f"Error reading document from Google Drive: {str(e)}")
            return None

    async def fetch_official_scripts(self, spreadsheet_id: str) -> Optional[dict]:
        """Fetch official scripts from Google Sheets and return as key-value pairs (Code -> Text)"""
        config = await config_manager.get_google_chat_config()
        sa_b64 = config.sa_json_b64
        
        if not sa_b64:
            logger.warning("Google Sheets script fetch skipped: Service Account credentials not configured")
            return None
            
        try:
            creds = await self._get_credentials(sa_b64)
            if not creds:
                logger.error("Failed to load credentials for Google Sheets script fetch")
                return None
                
            creds.refresh(Request())
            
            # Fetch from default tab A1:H150
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:H150"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    # Try Hoja 1 tab explicitly
                    url_fallback = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/'Hoja 1'!A1:H150"
                    response = await client.get(url_fallback, headers=headers)
                    
                if response.status_code != 200:
                    logger.error(f"Failed to fetch scripts from Google Sheets ({response.status_code}): {response.text}")
                    return None
                    
                data = response.json()
                rows = data.get("values", [])
                
                if not rows:
                    logger.warning("Google Sheets scripts is empty")
                    return None
                
                scripts = {}
                logger.info(f"Fetched {len(rows)} rows from Google Sheet scripts. First row: {rows[0] if rows else 'None'}")
                for row in rows:
                    cells = [str(x).strip() if x is not None else "" for x in row]
                    for idx, cell in enumerate(cells):
                        # Match SC.xxx or CU.xxx
                        if cell.startswith("SC.") or cell.startswith("CU."):
                            code = cell.replace(" ", "").upper()
                            text = ""
                            if idx + 1 < len(cells):
                                text = cells[idx + 1]
                            if code and text:
                                scripts[code] = text
                                
                logger.info(f"Successfully parsed {len(scripts)} scripts. Keys: {list(scripts.keys())}")
                return scripts
                
        except Exception as e:
            logger.error(f"Failed to fetch or parse scripts from Google Sheets: {str(e)}")
            return None

    async def fetch_business_rules(self, spreadsheet_id: str) -> Optional[dict]:
        """Fetch business rules from Google Sheets and return as key-value pairs (Code -> Description)"""
        config = await config_manager.get_google_chat_config()
        sa_b64 = config.sa_json_b64
        
        if not sa_b64:
            logger.warning("Google Sheets rules fetch skipped: Service Account credentials not configured")
            return None
            
        try:
            creds = await self._get_credentials(sa_b64)
            if not creds:
                logger.error("Failed to load credentials for Google Sheets rules fetch")
                return None
                
            creds.refresh(Request())
            
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:H150"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    url_fallback = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/'Hoja 1'!A1:H150"
                    response = await client.get(url_fallback, headers=headers)
                    
                if response.status_code != 200:
                    logger.error(f"Failed to fetch rules from Google Sheets ({response.status_code}): {response.text}")
                    return None
                    
                data = response.json()
                rows = data.get("values", [])
                
                if not rows:
                    logger.warning("Google Sheets rules is empty")
                    return None
                
                rules = {}
                logger.info(f"Fetched {len(rows)} rows from Google Sheet rules. First row: {rows[0] if rows else 'None'}")
                for row in rows:
                    cells = [str(x).strip() if x is not None else "" for x in row]
                    for idx, cell in enumerate(cells):
                        # Match RNE.xxx or COL.xxx
                        if cell.startswith("RNE.") or cell.startswith("COL."):
                            code = cell.replace(" ", "").upper()
                            text = ""
                            if idx + 1 < len(cells):
                                text = cells[idx + 1]
                            if code and text:
                                rules[code] = text
                                
                logger.info(f"Successfully parsed {len(rules)} rules. Keys: {list(rules.keys())}")
                return rules
                
        except Exception as e:
            logger.error(f"Failed to fetch or parse rules from Google Sheets: {str(e)}")
            return None

    async def fetch_status_rules(self, spreadsheet_id: str) -> Optional[dict]:
        """Fetch status routing rules from Google Sheets and return grouped by transaction type"""
        config = await config_manager.get_google_chat_config()
        sa_b64 = config.sa_json_b64
        
        if not sa_b64:
            logger.warning("Google Sheets status rules fetch skipped: Service Account credentials not configured")
            return None
            
        try:
            creds = await self._get_credentials(sa_b64)
            if not creds:
                return None
            creds.refresh(Request())
            
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:G150"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    url_fallback = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/'Hoja 1'!A1:G150"
                    response = await client.get(url_fallback, headers=headers)
                    
                if response.status_code != 200:
                    logger.error(f"Failed to fetch status rules from Google Sheets ({response.status_code}): {response.text}")
                    return None
                    
                data = response.json()
                rows = data.get("values", [])
                
                if not rows:
                    logger.warning("Google Sheets status rules is empty")
                    return None
                    
                return self._parse_status_rows(rows)
                
        except Exception as e:
            logger.error(f"Failed to fetch or parse status rules from Google Sheets: {str(e)}")
            return None

    async def fetch_bill_status_rules(self, spreadsheet_id: str) -> Optional[list]:
        """Fetch bill payment status rules from Google Sheets and return parsed rules list"""
        config = await config_manager.get_google_chat_config()
        sa_b64 = config.sa_json_b64
        
        if not sa_b64:
            logger.warning("Google Sheets bill status rules fetch skipped: Service Account credentials not configured")
            return None
            
        try:
            creds = await self._get_credentials(sa_b64)
            if not creds:
                return None
            creds.refresh(Request())
            
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:H150"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    url_fallback = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/'Hoja 1'!A1:H150"
                    response = await client.get(url_fallback, headers=headers)
                    
                if response.status_code != 200:
                    logger.error(f"Failed to fetch bill status rules from Google Sheets ({response.status_code}): {response.text}")
                    return None
                    
                data = response.json()
                rows = data.get("values", [])
                
                if not rows:
                    logger.warning("Google Sheets bill status rules is empty")
                    return None
                    
                return self._parse_bill_status_rows(rows)
                
        except Exception as e:
            logger.error(f"Failed to fetch or parse bill status rules from Google Sheets: {str(e)}")
            return None

    def _parse_bill_status_rows(self, rows) -> list:
        """Parse raw bill status sheet rows into a structured list of dicts"""
        rules = []
        # Expecting headers: Categoria, Derivación a Departamento, Caso, Tipo de status, Status, Tipo de perfil, Código Script, Script Servicio al cliente
        # Row 0: Headers
        for idx, row in enumerate(rows):
            if idx == 0:
                continue
            cols = [str(x).strip() if x is not None else "" for x in row]
            if not any(cols) or len(cols) < 5:
                continue
            
            # Categoria, Derivacion, Caso, Tipo, Status, Perfil, Codigo, Script
            categoria = cols[0]
            derivacion = cols[1] if len(cols) > 1 else "NA"
            caso = cols[2] if len(cols) > 2 else ""
            tipo_status = cols[3] if len(cols) > 3 else ""
            status = cols[4] if len(cols) > 4 else ""
            perfil = cols[5] if len(cols) > 5 else ""
            code_script = cols[6] if len(cols) > 6 else ""
            script = cols[7] if len(cols) > 7 else ""
            
            rules.append({
                "categoria": categoria,
                "derivacion": derivacion,
                "caso": caso,
                "tipo_status": tipo_status,
                "status": status,
                "perfil": perfil,
                "code_script": code_script,
                "script": script
            })
        return rules

    def _parse_status_rows(self, rows) -> dict:
        """Parse raw status sheet rows into a structured dict grouped by type"""
        rules = {
            "remesa": [],
            "bill": [],
            "recarga": []
        }
        
        current_type = "remesa"
        for row in rows:
            cols = [str(x).strip() if x is not None else "" for x in row]
            if not any(cols):
                continue
                
            first_col = cols[0].upper()
            
            # Backward compatibility for old divider headers
            if "PAGOS DE BILL" in first_col:
                current_type = "bill"
                continue
            elif "RECARGAS" in first_col:
                current_type = "recarga"
                continue
            elif first_col in ["ESTATUS", "CATEGORIA", "CATEGORÍA"]:
                # Header row
                continue
            elif len(cols) > 1 and ("PERFIL DE CLIENTE" in cols[1].upper() or "CASOS" in cols[1].upper()):
                # Header row
                continue
                
            # If it's the new 7-column sheet layout
            # Columns: Categoria, Casos, Tipo de status, Status, Tipo de perfil, Código Script, Script Servicio al cliente
            if len(cols) >= 6:
                categoria = cols[0]
                casos = cols[1]
                tipo_status = cols[2]
                estatus = cols[3]
                perfil = cols[4]
                
                code_script = cols[5]
                script = cols[6] if len(cols) > 6 else ""
                
                # Determine type
                casos_upper = casos.upper()
                if "BILL" in casos_upper or "BILL" in tipo_status.upper() or "BILL" in estatus.upper():
                    row_type = "bill"
                elif "RECARGA" in casos_upper:
                    row_type = "recarga"
                else:
                    row_type = "remesa"
                    
                # Determine derivation based on code_script
                if code_script == "SC.012":
                    deriv = "Cumplimiento"
                elif code_script == "SC.035":
                    deriv = "Prevencion de Fraudes"
                elif code_script in ["SC.024.1", "SC.025"]:
                    deriv = "Servicio al Cliente"
                else:
                    deriv = "NA"
            else:
                # Old 4-column layout
                estatus = cols[0]
                perfil = cols[1] if len(cols) > 1 else ""
                script = cols[2] if len(cols) > 2 else ""
                deriv = cols[3] if len(cols) > 3 else ""
                row_type = current_type
                
            if not estatus:
                continue
                
            rules[row_type].append({
                "estatus": estatus,
                "perfil": perfil,
                "script": script,
                "derivacion": deriv
            })
            
        return rules


# Singleton instance
google_sheets_service = GoogleSheetsService()

