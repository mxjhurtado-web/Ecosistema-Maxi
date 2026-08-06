"""
Service for reading live governance rules from Google Docs (ID: 12-fLM7wAFF3I0_ifY3Y1lahU7EfBeV5uA5GzFkkHBUw).
Uses the same Service Account credentials configured for Google Chat and Drive.
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

DEFAULT_GOVERNANCE_DOC_ID = "12-fLM7wAFF3I0_ifY3Y1lahU7EfBeV5uA5GzFkkHBUw"


class GoogleDocsService:
    """Service to fetch and parse live Governance rules (AUD, SEG, COL, REJ, LNG) from Google Docs"""

    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/documents.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]

    async def _get_credentials(self) -> Optional[service_account.Credentials]:
        """Load service account credentials dynamically from config manager or settings"""
        try:
            config = await config_manager.get_google_chat_config()
            sa_b64 = config.sa_json_b64

            if not sa_b64:
                sa_b64 = settings.GOOGLE_CHATS_SA_BASE64 or settings.MAXIBOT_SA_BASE64

            if not sa_b64:
                logger.warning("Google Docs credentials skipped: Service Account not configured")
                return None

            sa_json = base64.b64decode(sa_b64).decode('utf-8')
            sa_info = json.loads(sa_json)
            return service_account.Credentials.from_service_account_info(
                sa_info, scopes=self.scopes
            )
        except Exception as e:
            logger.error(f"Failed to load Google Docs Service Account credentials: {str(e)}")
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
            logger.error(f"Failed to refresh Google Docs token: {str(e)}")
            return None

    async def get_document_text(self, document_id: str = DEFAULT_GOVERNANCE_DOC_ID) -> Optional[str]:
        """Fetch raw document text from Google Docs API v1"""
        token = await self._get_token()
        if not token:
            logger.warning("Skipping Google Docs fetch: token not available")
            return None

        url = f"https://docs.googleapis.com/v1/documents/{document_id}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    doc = res.json()
                    title = doc.get("title", "Sin Título")
                    logger.info(f"📄 Successfully loaded Google Doc: '{title}' (ID: {document_id})")
                    
                    # Parse structural elements to extract plain text
                    text_parts = []
                    body = doc.get("body", {}).get("content", [])
                    for element in body:
                        paragraph = element.get("paragraph")
                        if paragraph:
                            for elem in paragraph.get("elements", []):
                                text_run = elem.get("textRun")
                                if text_run:
                                    text_parts.append(text_run.get("content", ""))
                    
                    full_text = "".join(text_parts)
                    return full_text
                else:
                    logger.error(f"Failed to fetch Google Doc ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Error reading Google Doc ID {document_id}: {str(e)}")

        return None


# Singleton instance
google_docs_service = GoogleDocsService()
