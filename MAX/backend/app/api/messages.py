"""
Messages API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter()


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    limit: int = 50,
    before: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get messages for a conversation."""
    # TODO: Implement actual database query
    return {
        "messages": [],
        "has_more": False
    }


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    content_text: str,
    db: AsyncSession = Depends(get_db)
):
    """Send a message to a customer."""
    # TODO: Implement message sending logic
    return {
        "id": "message-id",
        "conversation_id": conversation_id,
        "content_text": content_text,
        "status": "pending"
    }
