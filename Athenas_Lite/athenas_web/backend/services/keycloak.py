"""
Keycloak SSO integration service
Adapted from MaxiBot keycloak_auth.py for web application use
"""
import os
import requests
from typing import Dict, Optional, Tuple
from jose import jwt, JWTError
from datetime import datetime, timedelta

class KeycloakService:
    """Keycloak OAuth 2.0 / OpenID Connect integration"""
    
    def __init__(self):
        self.keycloak_url = os.getenv("KEYCLOAK_URL", "https://sso.maxilabs.net/auth")
        self.realm = os.getenv("KEYCLOAK_REALM", "zeusDev")
        self.client_id = os.getenv("KEYCLOAK_CLIENT_ID", "maxi-business-ai")
        self.client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("KEYCLOAK_REDIRECT_URI", "http://localhost:8080/callback")
        
        # Construct endpoints
        self.auth_endpoint = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/auth"
        self.token_endpoint = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"
        self.userinfo_endpoint = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/userinfo"
        self.logout_endpoint = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/logout"
    
    def get_auth_url(self, state: str = "athenas_auth") -> str:
        """Generate Keycloak authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile email',
            'state': state
        }
        from urllib.parse import urlencode
        return f"{self.auth_endpoint}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code: str) -> Tuple[bool, Dict]:
        """Exchange authorization code for access and refresh tokens"""
        try:
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': self.redirect_uri
            }
            
            response = requests.post(self.token_endpoint, data=data, timeout=30)
            
            if response.status_code == 200:
                tokens = response.json()
                return True, tokens
            else:
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            return False, {"error": str(e)}
    
    def get_user_info(self, access_token: str) -> Tuple[bool, Dict]:
        """Get user information from Keycloak"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(self.userinfo_endpoint, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            return False, {"error": str(e)}
    
    def extract_roles_from_token(self, access_token: str) -> list:
        """Extract roles from JWT token without verification"""
        try:
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            roles = decoded.get('realm_access', {}).get('roles', [])
            return roles
        except JWTError:
            return []
    
    def get_athenas_role(self, access_token: str, email: str) -> Optional[str]:
        """
        Determine ATHENAS role from internal database, not Keycloak
        Keycloak is only used for authentication
        Returns: 'admin' or 'user' based on internal DB
        """
        # Super admin hardcoded
        if email == "mxjhurtado@maxillc.com":
            return 'admin'
        
        # For all other users, role will be determined by database
        # Default to 'user' if not found in DB
        return None  # Will be set by storage service
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Dict]:
        """Refresh access token using refresh token"""
        try:
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token
            }
            
            response = requests.post(self.token_endpoint, data=data, timeout=30)
            
            if response.status_code == 200:
                tokens = response.json()
                return True, tokens
            else:
                return False, {"error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return False, {"error": str(e)}
    
    def logout(self, refresh_token: str) -> bool:
        """Logout from Keycloak"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token
            }
            response = requests.post(self.logout_endpoint, data=data, timeout=10)
            return response.status_code == 204
        except Exception:
            return False

# Global instance
keycloak_service = KeycloakService()
