"""
Service for uploading and downloading conversation transcripts to/from Google Drive.
Uses the same Service Account credentials configured for Google Chat.
"""

import base64
import json
import logging
import httpx
from typing import Optional, Dict, Any
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from .config_manager import config_manager
from .config import settings

logger = logging.getLogger(__name__)


class GoogleDriveService:
    """Service to upload and download chat histories to Google Drive using the Service Account"""
    
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/drive"]
        self.root_folder_id = "17mijvtxqCJ1y1EcQw0IByBbxyN9eTYj2"

    async def _get_credentials(self) -> Optional[service_account.Credentials]:
        """Load service account credentials dynamically from config manager or settings"""
        try:
            # Try config manager (Redis config) first
            config = await config_manager.get_google_chat_config()
            sa_b64 = config.sa_json_b64
            
            # Fallback to settings
            if not sa_b64:
                sa_b64 = settings.GOOGLE_CHATS_SA_BASE64 or settings.MAXIBOT_SA_BASE64

            if not sa_b64:
                logger.warning("Google Drive credentials skipped: Service Account not configured")
                return None

            sa_json = base64.b64decode(sa_b64).decode('utf-8')
            sa_info = json.loads(sa_json)
            return service_account.Credentials.from_service_account_info(
                sa_info, scopes=self.scopes
            )
        except Exception as e:
            logger.error(f"Failed to load Google Drive Service Account credentials: {str(e)}")
            return None

    async def _get_token(self) -> Optional[str]:
        """Fetch and refresh OAuth2 token"""
        creds = await self._get_credentials()
        if not creds:
            return None
        try:
            creds.refresh(Request())
            return creds.token
        except Exception as e:
            logger.error(f"Failed to refresh Google Drive token: {str(e)}")
            return None

    async def _get_or_create_daily_folder(self, token: str, date_str: str) -> Optional[str]:
        """Find or create a subfolder with date_str inside root folder"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 1. Search for folder
        try:
            search_url = "https://www.googleapis.com/drive/v3/files"
            q = f"name = '{date_str}' and '{self.root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            params = {
                "q": q,
                "spaces": "drive",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
                "fields": "files(id)"
            }
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(search_url, headers=headers, params=params)
                if res.status_code == 200:
                    files = res.json().get("files", [])
                    if files:
                        return files[0]["id"]
        except Exception as e:
            logger.error(f"Error searching daily folder in Google Drive: {str(e)}")

        # 2. Create folder if not found
        try:
            create_url = "https://www.googleapis.com/drive/v3/files?supportsAllDrives=true"
            body = {
                "name": date_str,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [self.root_folder_id]
            }
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(create_url, headers=headers, json=body)
                if res.status_code == 200:
                    folder_id = res.json().get("id")
                    logger.info(f"📁 Created daily folder '{date_str}' in Google Drive: {folder_id}")
                    return folder_id
                else:
                    logger.error(f"Failed to create daily folder in Google Drive ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Error creating daily folder in Google Drive: {str(e)}")
            
        return None

    async def upload_chat_json(self, conversation_id: str, chat_data: Dict[str, Any], date_str: str) -> Optional[str]:
        """Upload chat transcript JSON to Google Drive daily folder"""
        token = await self._get_token()
        if not token:
            logger.warning("Skipping chat JSON upload to Drive: credentials token not obtained")
            return None

        folder_id = await self._get_or_create_daily_folder(token, date_str)
        if not folder_id:
            logger.warning("Skipping chat JSON upload: daily folder ID not available")
            return None

        file_name = f"conv_{conversation_id}.json"
        
        # We perform a multipart/related upload to upload metadata and content together
        upload_url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true"
        boundary = "orbit_drive_upload_boundary"
        
        metadata = {
            "name": file_name,
            "parents": [folder_id],
            "mimeType": "application/json"
        }
        
        content_str = json.dumps(chat_data, ensure_ascii=False, indent=2)
        
        body = (
            f"--{boundary}\r\n"
            f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{json.dumps(metadata)}\r\n"
            f"--{boundary}\r\n"
            f"Content-Type: application/json\r\n\r\n"
            f"{content_str}\r\n"
            f"--{boundary}--"
        )
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary}"
        }

        try:
            # Check if file already exists to overwrite/update it
            search_url = "https://www.googleapis.com/drive/v3/files"
            q = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
            params = {
                "q": q,
                "spaces": "drive",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
                "fields": "files(id)"
            }
            async with httpx.AsyncClient(timeout=10) as client:
                search_res = await client.get(search_url, headers=headers, params=params)
                if search_res.status_code == 200:
                    files = search_res.json().get("files", [])
                    if files:
                        # File exists, update it using PATCH/PUT upload
                        existing_id = files[0]["id"]
                        update_url = f"https://www.googleapis.com/upload/drive/v3/files/{existing_id}?uploadType=media&supportsAllDrives=true"
                        headers_update = {
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        }
                        res = await client.patch(update_url, headers=headers_update, content=content_str.encode('utf-8'))
                        if res.status_code == 200:
                            logger.info(f"✅ Updated existing chat JSON in Drive: {existing_id}")
                            return existing_id

            # Create new file
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(upload_url, headers=headers, content=body.encode('utf-8'))
                if res.status_code == 200:
                    file_id = res.json().get("id")
                    logger.info(f"✅ Uploaded chat JSON to Google Drive: {file_name} -> ID: {file_id}")
                    return file_id
                else:
                    logger.error(f"Failed to upload chat JSON to Google Drive ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Error uploading chat JSON to Google Drive: {str(e)}")
            
        return None

    async def download_chat_json(self, conversation_id: str, date_str: str) -> Optional[Dict[str, Any]]:
        """Find and download chat transcript JSON from Google Drive daily folder"""
        token = await self._get_token()
        if not token:
            logger.warning("Skipping chat JSON download from Drive: credentials token not obtained")
            return None

        # 1. Find daily folder
        folder_id = await self._get_or_create_daily_folder(token, date_str)
        if not folder_id:
            logger.warning("Skipping chat JSON download: daily folder ID not available")
            return None

        file_name = f"conv_{conversation_id}.json"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        try:
            # 2. Search for the file in folder
            search_url = "https://www.googleapis.com/drive/v3/files"
            q = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
            params = {
                "q": q,
                "spaces": "drive",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
                "fields": "files(id)"
            }
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(search_url, headers=headers, params=params)
                if res.status_code == 200:
                    files = res.json().get("files", [])
                    if files:
                        file_id = files[0]["id"]
                        # 3. Download media content
                        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&supportsAllDrives=true"
                        dl_res = await client.get(download_url, headers=headers)
                        if dl_res.status_code == 200:
                            return dl_res.json()
                        else:
                            logger.error(f"Failed to download Drive file media ({dl_res.status_code}): {dl_res.text}")
                    else:
                        logger.warning(f"File {file_name} not found in Google Drive folder {folder_id}")
                else:
                    logger.error(f"Failed to search for file {file_name} in Google Drive ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Error downloading chat JSON from Google Drive: {str(e)}")

        return None


# Singleton instance
google_drive_service = GoogleDriveService()
