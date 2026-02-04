"""
Shared Redis client for configuration and telemetry.
"""

import redis.asyncio as redis
from typing import Optional
from api.config import settings
import logging

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client"""
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,
                socket_connect_timeout=5
            )
            
            # Test connection
            await _redis_client.ping()
            logger.info("Redis client created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create Redis client: {str(e)}")
            raise
    
    return _redis_client


async def close_redis_client():
    """Close Redis client"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")
