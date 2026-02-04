"""
Dependencies de FastAPI para autenticación.
"""

from fastapi import Depends, HTTPException, status
from typing import Dict
from .keycloak import verify_token, security, has_role


async def get_current_user(credentials = Depends(security)) -> Dict:
    """
    Dependency para obtener el usuario actual.
    
    Uso:
        @app.get("/me")
        def get_me(current_user: dict = Depends(get_current_user)):
            return current_user
    """
    return verify_token(credentials)


def require_role(role: str):
    """
    Dependency factory para requerir un rol específico.
    
    Uso:
        @app.get("/admin")
        def admin_only(user: dict = Depends(require_role("hades_admin"))):
            return {"message": "Admin access"}
    """
    async def role_checker(current_user: Dict = Depends(get_current_user)):
        if not has_role(current_user, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requiere rol: {role}"
            )
        return current_user
    return role_checker


# Shortcuts para roles comunes
async def require_admin(current_user: Dict = Depends(get_current_user)):
    """Requiere rol de admin"""
    if not has_role(current_user, "hades_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere rol de administrador"
        )
    return current_user


async def require_analyst(current_user: Dict = Depends(get_current_user)):
    """Requiere rol de analyst o admin"""
    if not (has_role(current_user, "hades_analyst") or has_role(current_user, "hades_admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere rol de analista"
        )
    return current_user
