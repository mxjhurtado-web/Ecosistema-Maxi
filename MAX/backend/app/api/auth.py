"""
Authentication API endpoints with Keycloak.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.keycloak_auth import get_current_user, keycloak_settings
from app.models.user import User
from typing import Dict

router = APIRouter()


@router.get("/config")
async def get_auth_config():
    """
    Get Keycloak configuration for frontend.
    Frontend will use this to redirect users to Keycloak login.
    """
    return {
        "auth_url": keycloak_settings.auth_endpoint,
        "token_url": keycloak_settings.token_endpoint,
        "client_id": keycloak_settings.KEYCLOAK_CLIENT_ID,
        "realm": keycloak_settings.KEYCLOAK_REALM,
    }


@router.get("/me")
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user information.
    Creates user in MAX database if doesn't exist (first login).
    """
    keycloak_id = current_user["keycloak_id"]
    
    # Check if user exists in MAX database
    result = await db.execute(
        select(User).where(User.keycloak_id == keycloak_id)
    )
    user = result.scalar_one_or_none()
    
    # Create user if doesn't exist (first login)
    if not user:
        # Determine role from Keycloak roles
        roles = current_user["roles"]
        if "maxibot-admin" in roles or "admin" in roles:
            role = "admin"
        elif "supervisor" in roles:
            role = "supervisor"
        elif "team_lead" in roles:
            role = "team_lead"
        else:
            role = "agent"
        
        user = User(
            keycloak_id=keycloak_id,
            email=current_user["email"],
            full_name=current_user["name"] or current_user["email"],
            role=role,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return {
        "id": str(user.id),
        "keycloak_id": user.keycloak_id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "keycloak_roles": current_user["roles"]
    }


@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    Frontend should clear local token and redirect to Keycloak logout.
    """
    return {
        "message": "Logout successful",
        "logout_url": keycloak_settings.logout_endpoint
    }
