"""
Dependencias de autenticación para FastAPI
MODO DESARROLLO: Autenticación deshabilitada temporalmente
"""

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict

# Security scheme (opcional en dev mode)
security = HTTPBearer(auto_error=False)

# MODO DESARROLLO: Usuario mock con todos los campos requeridos
DEV_USER = {
    "sub": "dev-user-123",
    "user_id": "dev-user-123",  # Campo requerido por el backend
    "email": "developer@maxilabs.net",
    "name": "Developer User",
    "preferred_username": "developer",
    "realm_access": {
        "roles": ["analyst", "admin", "hades_analyst", "hades_admin"]
    }
}

def has_role(user: Dict, role: str) -> bool:
    """Check if user has a specific role"""
    roles = user.get("realm_access", {}).get("roles", [])
    return role in roles

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Dict:
    """
    MODO DESARROLLO: Retorna usuario mock sin validación
    """
    print("[DEV MODE] Using mock user authentication")
    return DEV_USER

async def require_analyst(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    MODO DESARROLLO: Siempre permite acceso
    """
    print("[DEV MODE] Analyst access granted")
    return current_user

async def require_admin(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    MODO DESARROLLO: Siempre permite acceso
    """
    print("[DEV MODE] Admin access granted")
    return current_user

def require_role(role: str):
    """
    Dependency factory para requerir un rol específico
    MODO DESARROLLO: Siempre permite acceso
    """
    async def role_checker(current_user: Dict = Depends(get_current_user)):
        print(f"[DEV MODE] Role '{role}' access granted")
        return current_user
    return role_checker
