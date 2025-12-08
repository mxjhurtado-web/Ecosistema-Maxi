"""
Authentication API endpoints with Keycloak SSO
"""
from fastapi import APIRouter, HTTPException, Response, Cookie, Depends
from fastapi.responses import RedirectResponse
from typing import Optional
from models.schemas import TokenResponse, UserInfo
from services.keycloak import keycloak_service
import os

router = APIRouter()

@router.get("/login")
async def login():
    """Redirect to Keycloak login page"""
    auth_url = keycloak_service.get_auth_url()
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def callback(code: str, state: str, response: Response):
    """
    Handle OAuth callback from Keycloak
    Exchange code for tokens and set httpOnly cookie
    """
    # Exchange code for tokens
    success, result = keycloak_service.exchange_code_for_tokens(code)
    
    if not success:
        raise HTTPException(status_code=400, detail=result.get("error", "Authentication failed"))
    
    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")
    
    # Get user info
    success, user_data = keycloak_service.get_user_info(access_token)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to get user info")
    
    email = user_data.get("email")
    keycloak_id = user_data.get("sub")
    name = user_data.get("name", user_data.get("preferred_username", ""))
    
    # Sync user and get role from internal DB
    from services.storage import storage_service
    user_id, role = await storage_service.sync_user(email, keycloak_id, name)
    
    # Set httpOnly cookies
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    response = RedirectResponse(
        url=f"{frontend_url}/auth/success?role={role}"
    )
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=3600  # 1 hour
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400  # 24 hours
    )
    
    return response

@router.get("/me", response_model=UserInfo)
async def get_current_user(access_token: Optional[str] = Cookie(None)):
    """Get current user information from token and internal DB"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get user info from Keycloak
    success, user_data = keycloak_service.get_user_info(access_token)
    
    if not success:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    email = user_data.get("email")
    keycloak_id = user_data.get("sub")
    name = user_data.get("name", user_data.get("preferred_username", ""))
    
    # Get role from internal DB
    from services.storage import storage_service
    user_id, role = await storage_service.sync_user(email, keycloak_id, name)
    
    return UserInfo(
        email=email,
        name=name,
        role=role,
        keycloak_id=keycloak_id
    )

@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None)
):
    """Logout from Keycloak and clear cookies"""
    if refresh_token:
        keycloak_service.logout(refresh_token)
    
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"message": "Logged out successfully"}

@router.post("/refresh")
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None)
):
    """Refresh access token"""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    success, result = keycloak_service.refresh_access_token(refresh_token)
    
    if not success:
        raise HTTPException(status_code=401, detail="Failed to refresh token")
    
    new_access_token = result.get("access_token")
    new_refresh_token = result.get("refresh_token")
    
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=3600
    )
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400
    )
    
    return {"message": "Token refreshed"}
