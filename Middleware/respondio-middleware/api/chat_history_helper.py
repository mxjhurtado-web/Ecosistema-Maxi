"""
Helper for managing conversation chat history cache in Redis and uploading to Google Drive.
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo
from .google_drive_service import google_drive_service

logger = logging.getLogger(__name__)

REDIS_TTL = 24 * 60 * 60 # Keep raw active history for 24 hours in Redis


async def append_message_to_history(
    redis,
    conversation_id: str,
    sender: str,
    message: str,
    agent_name: Optional[str] = None
) -> None:
    """
    Appends a message to the conversation chat history list in Redis.
    
    sender values: 'client', 'bot_max', 'agent_specialized', 'agent_human'
    """
    if not redis or not conversation_id:
        return
        
    try:
        key = f"chat_history:{conversation_id}"
        
        # Get local time in Mexico timezone (UTC-6)
        local_dt = datetime.now(ZoneInfo("America/Mexico_City"))
        timestamp_str = local_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        msg_payload = {
            "sender": sender,
            "message": message,
            "agent_name": agent_name,
            "timestamp": timestamp_str
        }
        
        # Push to Redis list
        await redis.rpush(key, json.dumps(msg_payload))
        await redis.expire(key, REDIS_TTL)
        logger.info(f"💾 [Chat History Cache] Appended msg from '{sender}' to conversation '{conversation_id}'")
    except Exception as e:
        logger.error(f"Failed to append message to chat history cache: {str(e)}")


async def get_chat_history(redis, conversation_id: str) -> List[Dict[str, Any]]:
    """Retrieves list of messages in a conversation from Redis"""
    if not redis or not conversation_id:
        return []
        
    try:
        key = f"chat_history:{conversation_id}"
        elements = await redis.lrange(key, 0, -1)
        if not elements:
            return []
        return [json.loads(el.decode('utf-8')) for el in elements]
    except Exception as e:
        logger.error(f"Failed to get chat history from cache: {str(e)}")
        return []


async def clear_chat_history(redis, conversation_id: str) -> None:
    """Removes the chat history list from Redis"""
    if not redis or not conversation_id:
        return
    try:
        key = f"chat_history:{conversation_id}"
        await redis.delete(key)
    except Exception as e:
        logger.error(f"Failed to delete chat history from cache: {str(e)}")


async def upload_conversation_to_drive(
    redis,
    conversation_id: str,
    contact_id: str,
    contact_name: str
) -> Optional[str]:
    """
    Reads the cached conversation from Redis, uploads the JSON to Google Drive daily folder,
    and returns the file ID if successful.
    """
    if not redis or not conversation_id:
        return None
        
    try:
        history = await get_chat_history(redis, conversation_id)
        if not history:
            logger.warning(f"No chat history found in Redis cache for conversation '{conversation_id}' to upload to Drive")
            return None
            
        local_date = datetime.now(ZoneInfo("America/Mexico_City")).strftime("%Y-%m-%d")
        
        chat_data = {
            "conversation_id": conversation_id,
            "contact_id": contact_id,
            "contact_name": contact_name,
            "date": local_date,
            "messages": history
        }
        
        file_id = await google_drive_service.upload_chat_json(
            conversation_id=conversation_id,
            chat_data=chat_data,
            date_str=local_date
        )
        
        if file_id:
            logger.info(f"☁️ Saved chat history to Google Drive: {conversation_id} in {local_date}")
            # Clear cache
            await clear_chat_history(redis, conversation_id)
            return file_id
            
    except Exception as e:
        logger.error(f"Failed to upload conversation to Google Drive: {str(e)}")
        
    return None
