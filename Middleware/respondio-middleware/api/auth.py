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

    async def verify_user_has_role(self, email: str, role_name: str) -> bool:
        """
        Query Keycloak Admin API to check if a user has the specified realm role.
        
        Args:
            email: The email address of the user to check
            role_name: The name of the role to verify (e.g., 'DevOps')
            
        Returns:
            bool: True if user exists and has the role, False otherwise
        """
        try:
            # 1. Get client access token
            token = await self.get_access_token()
            if not token:
                logger.error("verify_user_has_role: Failed to obtain client token")
                return False
                
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # 2. Find user by email
            # Endpoint: GET {server_url}/admin/realms/{realm}/users?email={email}
            users_url = f"{self.server_url}/admin/realms/{self.realm}/users"
            params = {"email": email, "exact": "true"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(users_url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                users = response.json()
                
                if not users:
                    logger.warning(f"verify_user_has_role: No user found with email {email}")
                    return False
                    
                user_id = users[0].get("id")
                if not user_id:
                    logger.error(f"verify_user_has_role: User found but ID is missing for email {email}")
                    return False
                    
                # 3. Get user's realm roles mappings
                # Endpoint: GET {server_url}/admin/realms/{realm}/users/{user_id}/role-mappings/realm
                roles_url = f"{self.server_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm"
                roles_response = await client.get(roles_url, headers=headers, timeout=10)
                roles_response.raise_for_status()
                roles = roles_response.json()
                
                # Check if role_name matches any realm role name (case-insensitive to be safe)
                target_role = role_name.lower()
                for role in roles:
                    curr_role_name = str(role.get("name", "")).lower()
                    if curr_role_name == target_role:
                        logger.info(f"verify_user_has_role: User {email} has authorized role '{role_name}'")
                        return True
                        
                logger.warning(f"verify_user_has_role: User {email} does NOT have role '{role_name}'")
                return False
                
        except Exception as e:
            logger.error(f"verify_user_has_role exception for email {email}: {str(e)}")
            return False

    def reset(self):
        """Reset the cached token"""
        self._access_token = None
        self._expires_at = 0

