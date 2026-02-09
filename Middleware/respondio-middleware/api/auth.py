"""
Keycloak Authentication Service for Service Accounts.
"""

import httpx
import time
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class KeycloakAuthService:
    """Service to handle Keycloak Service Account authentication"""
    
    def __init__(self, server_url: str, realm: str, client_id: str, client_secret: str):
        self.server_url = server_url.rstrip('/')
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        
        self.token_endpoint = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        # Token cache
        self._access_token: Optional[str] = None
        self._expires_at: float = 0
    
    async def get_access_token(self) -> Optional[str]:
        """Get a valid access token, fetching a new one if necessary"""
        # Return cached token if still valid (with 30s buffer)
        if self._access_token and time.time() < self._expires_at - 30:
            return self._access_token
        
        # Fetch new token
        return await self._fetch_new_token()
    
    async def _fetch_new_token(self) -> Optional[str]:
        """Fetch a new token using client_credentials flow"""
        try:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    timeout=10
                )
                response.raise_for_status()
                
                result = response.json()
                self._access_token = result.get("access_token")
                expires_in = result.get("expires_in", 60)
                self._expires_at = time.time() + expires_in
                
                logger.info(f"Successfully fetched new Keycloak token for client: {self.client_id}")
                return self._access_token
                
        except Exception as e:
            logger.error(f"Failed to fetch Keycloak token: {str(e)}")
            return None

    def reset(self):
        """Reset the cached token"""
        self._access_token = None
        self._expires_at = 0
