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
from .models import GoogleChatAlertConfig

logger = logging.getLogger(__name__)


class GoogleChatService:
    """Service to send messages to Google Chat using a Service Account"""
    
    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/chat.messages.create",
            "https://www.googleapis.com/auth/chat.bot"
        ]
        self._credentials_cache = {}

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

    async def send_message(self, text: str, space_id: Optional[str] = None, config_override: Optional[GoogleChatAlertConfig] = None) -> bool:
        """
        Send a message to a Google Chat space.
        """
        if config_override:
            config = config_override
        else:
            config = await config_manager.get_google_chat_config()

        if not config.enabled and not config_override:
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
            creds = self._credentials_cache.get(sa_b64)
            if not creds:
                logger.info(f"🔑 Cargando credenciales por primera vez para el espacio: {target_space}")
                creds = await self._get_credentials(sa_b64)
                if creds:
                    self._credentials_cache[sa_b64] = creds
            
            if not creds:
                logger.error("❌ No se pudieron obtener las credenciales de la Service Account")
                return False
            
            # Refresh token solo si no es válido
            if not creds.valid:
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

    async def send_alert(self, title: str, message: str, level: str = "INFO", space_id: Optional[str] = None, sa_b64_override: Optional[str] = None) -> bool:
        """Helper to send a formatted alert message (returns bool status)"""
        ok, _ = await self.send_alert_detailed(title, message, level, space_id, sa_b64_override)
        return ok

    async def send_alert_detailed(
        self, 
        title: str, 
        message: str, 
        level: str = "INFO", 
        space_id: Optional[str] = None,
        sa_b64_override: Optional[str] = None
    ) -> tuple[bool, str]:
        """Send a formatted alert message and return detailed result status"""
        icon = "ℹ️"
        if level == "ERROR": icon = "🚨"
        elif level == "WARNING": icon = "⚠️"
        elif level == "SUCCESS": icon = "✅"
        
        formatted_text = f"{icon} *{title}*\n{message}"
        
        config = await config_manager.get_google_chat_config()
        
        sa_b64 = sa_b64_override or config.sa_json_b64
        target_space = space_id or config.default_space_id

        if not sa_b64:
            return False, "Google Chat configuration incomplete: Service Account JSON (sa_json_b64) is missing or empty"
            
        if not target_space:
            return False, "Google Chat configuration incomplete: Space ID is missing or empty"

        # Space ID normalization (must start with spaces/)
        if not target_space.startswith("spaces/"):
            target_space = f"spaces/{target_space}"

        # If general config is disabled and no explicit space_id or override was passed, prevent it.
        # But if space_id or sa_b64_override is explicitly passed, let it proceed!
        if not config.enabled and not space_id and not sa_b64_override:
            return False, "Google Chat alerts are globally disabled (enabled = False) and no explicit space_id or override was provided"

        try:
            # Decode and load credentials
            creds = await self._get_credentials(sa_b64)
            if not creds:
                return False, "Failed to decode or parse Service Account credentials"
            
            # Refresh token
            creds.refresh(Request())

            url = f"https://chat.googleapis.com/v1/{target_space}/messages"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            
            payload = {"text": formatted_text}

            logger.info(f"🚀 Disparando POST a Google Chat API: {url}")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    error_msg = f"Google Chat API returned status {response.status_code}: {response.text}"
                    logger.error(f"❌ {error_msg}")
                    return False, error_msg
                    
                logger.info(f"✅ ¡Mensaje enviado con éxito a {target_space}!")
                return True, "Message sent successfully"

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP status error: {e.response.status_code} - {e.response.text}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected exception: {str(e)}"
            logger.error(f"💥 {error_msg}")
            return False, error_msg


# Singleton instance
google_chat_service = GoogleChatService()

