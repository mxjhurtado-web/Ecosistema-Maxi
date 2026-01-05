"""
Keycloak authentication for FastAPI.
Validates JWT tokens from Keycloak.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt
from typing import Optional, Dict
import httpx
from app.core.keycloak_config import keycloak_settings


# OAuth2 scheme for Swagger UI
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=keycloak_settings.auth_endpoint,
    tokenUrl=keycloak_settings.token_endpoint,
)


class KeycloakAuth:
    """Keycloak authentication handler."""
    
    def __init__(self):
        self._public_key: Optional[str] = None
    
    async def get_public_key(self) -> str:
        """Get Keycloak public key for token validation."""
        if self._public_key:
            return self._public_key
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(keycloak_settings.jwks_uri)
                response.raise_for_status()
                jwks = response.json()
                
                # Get first key (usually there's only one)
                if jwks.get("keys"):
                    key_data = jwks["keys"][0]
                    # Convert to PEM format
                    from jose.backends import RSAKey
                    rsa_key = RSAKey(key_data, algorithm="RS256")
                    self._public_key = rsa_key.to_pem().decode("utf-8")
                    return self._public_key
                
                raise ValueError("No keys found in JWKS")
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching Keycloak public key: {str(e)}"
            )
    
    async def verify_token(self, token: str) -> Dict:
        """
        Verify and decode Keycloak JWT token.
        
        Args:
            token: JWT token from Keycloak
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # For development, we can skip signature verification
            if not keycloak_settings.KEYCLOAK_VERIFY_SIGNATURE:
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False}
                )
                return payload
            
            # Production: verify signature
            public_key = await self.get_public_key()
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=keycloak_settings.KEYCLOAK_CLIENT_ID if keycloak_settings.KEYCLOAK_VERIFY_AUD else None,
            )
            
            return payload
        
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_user_roles(self, token_payload: Dict) -> list:
        """Extract user roles from token."""
        realm_access = token_payload.get("realm_access", {})
        return realm_access.get("roles", [])
    
    def get_user_email(self, token_payload: Dict) -> Optional[str]:
        """Extract user email from token."""
        return token_payload.get("email")
    
    def get_user_name(self, token_payload: Dict) -> Optional[str]:
        """Extract user name from token."""
        return token_payload.get("name") or token_payload.get("preferred_username")
    
    def get_keycloak_id(self, token_payload: Dict) -> Optional[str]:
        """Extract Keycloak user ID from token."""
        return token_payload.get("sub")


# Global instance
keycloak_auth = KeycloakAuth()


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Dependency to get current authenticated user from token.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: Dict = Depends(get_current_user)):
            return {"user": user}
    """
    payload = await keycloak_auth.verify_token(token)
    
    return {
        "keycloak_id": keycloak_auth.get_keycloak_id(payload),
        "email": keycloak_auth.get_user_email(payload),
        "name": keycloak_auth.get_user_name(payload),
        "roles": keycloak_auth.get_user_roles(payload),
        "token_payload": payload
    }


async def require_role(required_role: str):
    """
    Dependency to require specific role.
    
    Usage:
        @app.get("/admin")
        async def admin_route(user: Dict = Depends(require_role("maxibot-admin"))):
            return {"message": "Admin access"}
    """
    async def role_checker(user: Dict = Depends(get_current_user)) -> Dict:
        if required_role not in user["roles"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return user
    
    return role_checker
