"""
API endpoints for API key management
Handles adding, removing, and viewing API keys with encryption
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel
import logging

from services.storage import storage_service
from services.api_key_manager import get_api_key_manager
from .analysis import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class AddKeyRequest(BaseModel):
    api_key: str

class KeyInfo(BaseModel):
    id: int
    key_preview: str
    status: str
    last_used_at: str | None

class KeyStatusResponse(BaseModel):
    total: int
    active: int
    exhausted: int
    max_keys: int
    keys: List[KeyInfo]

class MessageResponse(BaseModel):
    message: str

@router.post("/add", response_model=MessageResponse)
async def add_api_key(
    request: AddKeyRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Add a new API key for the current user.
    Keys are encrypted before storage.
    Maximum 4 keys per user.
    """
    key_mgr = get_api_key_manager(storage_service)
    
    success, message = await key_mgr.add_key(user_id, request.api_key)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    logger.info(f"User {user_id} added new API key")
    return MessageResponse(message=message)

@router.delete("/{key_id}", response_model=MessageResponse)
async def remove_api_key(
    key_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Remove an API key by its ID.
    Only the owner can remove their keys.
    """
    key_mgr = get_api_key_manager(storage_service)
    
    # Verify ownership by loading user's keys
    keys = await key_mgr.load_user_keys(user_id)
    if not any(k["id"] == key_id for k in keys):
        raise HTTPException(status_code=403, detail="Access denied")
    
    success, message = await key_mgr.remove_key(user_id, key_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    logger.info(f"User {user_id} removed API key {key_id}")
    return MessageResponse(message=message)

@router.get("/status", response_model=KeyStatusResponse)
async def get_keys_status(
    user_id: int = Depends(get_current_user_id)
):
    """
    Get status of all API keys for current user.
    Shows masked key previews, status, and usage stats.
    """
    key_mgr = get_api_key_manager(storage_service)
    
    status = await key_mgr.get_keys_status(user_id)
    
    # Convert to response model
    keys_info = [
        KeyInfo(
            id=k["id"],
            key_preview=k["key_preview"],
            status=k["status"],
            last_used_at=k.get("last_used_at")
        )
        for k in status["keys"]
    ]
    
    return KeyStatusResponse(
        total=status["total"],
        active=status["active"],
        exhausted=status["exhausted"],
        max_keys=status["max_keys"],
        keys=keys_info
    )

@router.post("/reset", response_model=MessageResponse)
async def reset_all_keys(
    user_id: int = Depends(get_current_user_id)
):
    """
    Reset all API keys to active status.
    Useful for manual reset or testing.
    """
    key_mgr = get_api_key_manager(storage_service)
    
    success, message = await key_mgr.reset_all_keys(user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    logger.info(f"User {user_id} reset all API keys")
    return MessageResponse(message=message)
