"""
Integración con Keycloak para autenticación.

Verifica JWT tokens usando las claves públicas de Keycloak.
"""

from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from typing import Dict
from ..config import settings

# Security scheme
security = HTTPBearer()

# URL del JWKS de Keycloak
jwks_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"

# Cliente JWKS (cachea las claves públicas)
jwks_client = PyJWKClient(jwks_url)


def verify_token(credentials: HTTPAuthorizationCredentials) -> Dict:
    """
    Verifica el JWT token con Keycloak.
    
    Args:
        credentials: Credenciales HTTP Bearer
        
    Returns:
        Dict con información del usuario:
        {
            "user_id": "uuid",
            "email": "user@example.com",
            "name": "John Doe",
            "roles": ["hades_analyst", ...]
        }
        
    Raises:
        HTTPException: Si el token es inválido o expiró
    """
    token = credentials.credentials
    
    try:
        # Obtener la clave pública de Keycloak
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decodificar y verificar el token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="account",
            options={"verify_exp": True}
        )
        
        # Extraer roles del realm
        realm_access = payload.get("realm_access", {})
        roles = realm_access.get("roles", [])
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "preferred_username": payload.get("preferred_username"),
            "roles": roles
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error verificando token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def has_role(user: Dict, role: str) -> bool:
    """
    Verifica si el usuario tiene un rol específico.
    
    Args:
        user: Dict del usuario (de verify_token)
        role: Nombre del rol
        
    Returns:
        True si tiene el rol
    """
    return role in user.get("roles", [])
