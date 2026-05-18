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
        
        # 2. Search in Google Drive folder
        try:
            search_url = "https://www.googleapis.com/drive/v3/files"
            q = f"name = '{self.sheet_name}' and '{self.parent_folder_id}' in parents and trashed = false"
            params = {
                "q": q,
                "spaces": "drive",
                "fields": "files(id, name)"
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

        # 3. Create a new Spreadsheet in the folder
        try:
            create_url = "https://www.googleapis.com/drive/v3/files"
            payload = {
                "name": self.sheet_name,
                "mimeType": "application/vnd.google-apps.spreadsheet",
                "parents": [self.parent_folder_id]
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(create_url, json=payload, headers=headers)
                if response.status_code == 200:
                    spreadsheet_id = response.json().get("id")
                    logger.info(f"✨ Created NEW Google Sheet in Drive: {spreadsheet_id}")
                    
                    # Write headers immediately
                    await self._write_headers(spreadsheet_id, token)
                    
                    if redis:
                        try:
                            await redis.set("google_sheets:spreadsheet_id", spreadsheet_id)
                        except Exception:
                            pass
                    return spreadsheet_id
                else:
                    logger.error(f"❌ Failed to create Google Sheet ({response.status_code}): {response.text}")
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
            cached_faq = await redis.get(f"google_sheets:faq_cache:{spreadsheet_id}")
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
                        await redis.setex(f"google_sheets:faq_cache:{spreadsheet_id}", 60, faq_text)
                        logger.info("Saved FAQ to Redis cache (60s TTL)")
                    except Exception:
                        pass
                        
                return faq_text
                
        except Exception as e:
            logger.error(f"Failed to fetch or parse FAQ from Google Sheets: {str(e)}")
            return None


# Singleton instance
google_sheets_service = GoogleSheetsService()
