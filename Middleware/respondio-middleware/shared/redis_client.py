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
            if settings.REDIS_URL:
                logger.info("🔗 Connecting to Redis using URL...")
                _redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=False,
                    socket_connect_timeout=2
                )
            else:
                logger.info(f"💾 Connecting to local Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}...")
                _redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=False,
                    socket_connect_timeout=2
                )
            
            # Test connection
            await _redis_client.ping()
            logger.info("✅ Redis client established and verified")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {str(e)}")
            _redis_client = None
            raise
    
    return _redis_client


async def close_redis_client():
    """Close Redis client"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")
