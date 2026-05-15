"""
Service for sending notifications to Google Chat spaces.
"""

import base64
import json
import logging
import httpx
from typing import Optional
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from .config_manager import config_manager

logger = logging.getLogger(__name__)

class GoogleChatService:
    """Service to send messages to Google Chat using a Service Account"""
    
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/chat.messages.create"]
        self._credentials = None

    async def _get_credentials(self, sa_b64: str):
        """Decode SA and load credentials"""
        try:
            sa_json = base64.b64decode(sa_b64).decode('utf-8')
            sa_info = json.loads(sa_json)
            return service_account.Credentials.from_service_account_info(
                sa_info, scopes=self.scopes
            )
        except Exception as e:
            logger.error(f"Failed to load Google Chat Service Account: {str(e)}")
            return None

    async def send_message(self, text: str, space_id: Optional[str] = None) -> bool:
        """
        Send a message to a Google Chat space.
        
        Args:
            text: The message content
            space_id: Target space (e.g. 'spaces/AAAA1234'). If None, uses default from config.
        """
        config = await config_manager.get_google_chat_config()
        if not config.enabled:
            logger.debug("Google Chat alerts are disabled")
            return False

        sa_b64 = config.sa_json_b64
        target_space = space_id or config.default_space_id

        if not sa_b64 or not target_space:
            logger.warning("Google Chat configuration incomplete (SA or Space missing)")
            return False

        # Space ID normalization (must start with spaces/)
        if not target_space.startswith("spaces/"):
            target_space = f"spaces/{target_space}"

        try:
            logger.info(f"🔑 Cargando credenciales para el espacio: {target_space}")
            creds = await self._get_credentials(sa_b64)
            if not creds:
                logger.error("❌ No se pudieron obtener las credenciales de la Service Account")
                return False
            
            # Refresh token (usando el Request que ya importamos)
            logger.info("🔄 Refrescando token de Google Auth...")
            creds.refresh(Request())
            logger.info("🎟️ Token refrescado con éxito")

            url = f"https://chat.googleapis.com/v1/{target_space}/messages"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            
            payload = {"text": text}

            logger.info(f"🚀 Disparando POST a Google Chat API: {url}")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"❌ Error API Google Chat ({response.status_code}): {response.text}")
                    return False
                    
                logger.info(f"✅ ¡Mensaje enviado con éxito a {target_space}!")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Google Chat API error ({e.response.status_code}): {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"💥 Failed to send Google Chat message: {str(e)}")
            return False

    async def send_alert(self, title: str, message: str, level: str = "INFO", space_id: Optional[str] = None) -> bool:
        """Send a formatted alert message"""
        icon = "ℹ️"
        if level == "ERROR": icon = "🚨"
        elif level == "WARNING": icon = "⚠️"
        elif level == "SUCCESS": icon = "✅"
        
        formatted_text = f"{icon} *{title}*\n{message}"
        return await self.send_message(formatted_text, space_id)


# Singleton instance
google_chat_service = GoogleChatService()
