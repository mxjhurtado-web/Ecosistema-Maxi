"""
Webhook endpoints for WhatsApp and Chat App.
"""
from fastapi import APIRouter, Request, HTTPException, Query
from app.core.config import settings

router = APIRouter()


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """
    WhatsApp webhook verification endpoint.
    
    WhatsApp will call this endpoint to verify the webhook URL.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return int(hub_challenge)
    
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    WhatsApp webhook endpoint for receiving messages.
    
    This endpoint receives all WhatsApp events (messages, status updates, etc.)
    """
    body = await request.json()
    
    # TODO: Implement webhook processing
    # 1. Validate webhook signature
    # 2. Parse message data
    # 3. Create/update conversation
    # 4. Save message
    # 5. Trigger triage worker if new conversation
    
    print(f"Received WhatsApp webhook: {body}")
    
    return {"status": "ok"}


@router.post("/chat-app")
async def chat_app_webhook(request: Request):
    """
    Chat App webhook endpoint for receiving messages.
    """
    body = await request.json()
    
    # TODO: Implement webhook processing
    print(f"Received Chat App webhook: {body}")
    
    return {"status": "ok"}
