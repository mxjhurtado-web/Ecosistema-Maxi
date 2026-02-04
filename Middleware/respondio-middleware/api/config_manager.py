"""
Configuration manager for dynamic config updates via Redis.
"""

from typing import Optional
from .models import MCPConfig, CacheConfig, SecurityConfig
from .config import settings
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages dynamic configuration stored in Redis"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.enabled = redis_client is not None
    
    # ============================================================
    # MCP Configuration
    # ============================================================
    
    async def get_mcp_config(self) -> MCPConfig:
        """Get current MCP configuration"""
        if not self.enabled:
            # Return default from settings
            return MCPConfig(
                url=settings.MCP_URL,
                timeout=settings.MCP_TIMEOUT,
                max_retries=settings.MCP_MAX_RETRIES,
                retry_delay=settings.MCP_RETRY_DELAY,
                gemini_api_key=None
            )
        
        try:
            # Get from Redis
            url = await self.redis.get("config:mcp:url")
            timeout = await self.redis.get("config:mcp:timeout")
            max_retries = await self.redis.get("config:mcp:max_retries")
            retry_delay = await self.redis.get("config:mcp:retry_delay")
            gemini_api_key = await self.redis.get("config:mcp:gemini_api_key")
            
            return MCPConfig(
                url=url.decode() if url else settings.MCP_URL,
                timeout=int(timeout) if timeout else settings.MCP_TIMEOUT,
                max_retries=int(max_retries) if max_retries else settings.MCP_MAX_RETRIES,
                retry_delay=int(retry_delay) if retry_delay else settings.MCP_RETRY_DELAY,
                gemini_api_key=gemini_api_key.decode() if gemini_api_key else None
            )
        except Exception as e:
            logger.error(f"Failed to get MCP config from Redis: {str(e)}")
            # Fallback to settings
            return MCPConfig(
                url=settings.MCP_URL,
                timeout=settings.MCP_TIMEOUT,
                max_retries=settings.MCP_MAX_RETRIES,
                retry_delay=settings.MCP_RETRY_DELAY,
                gemini_api_key=None
            )
    
    async def update_mcp_config(self, config: MCPConfig):
        """Update MCP configuration"""
        if not self.enabled:
            logger.warning("Cannot update config: Redis not available")
            return False
        
        try:
            await self.redis.set("config:mcp:url", config.url)
            await self.redis.set("config:mcp:timeout", config.timeout)
            await self.redis.set("config:mcp:max_retries", config.max_retries)
            await self.redis.set("config:mcp:retry_delay", config.retry_delay)
            if config.gemini_api_key:
                await self.redis.set("config:mcp:gemini_api_key", config.gemini_api_key)
            else:
                await self.redis.delete("config:mcp:gemini_api_key")
            
            logger.info(f"MCP config updated: {config.url}")
            return True
        except Exception as e:
            logger.error(f"Failed to update MCP config: {str(e)}")
            return False
    
    # ============================================================
    # Cache Configuration
    # ============================================================
    
    async def get_cache_config(self) -> CacheConfig:
        """Get current cache configuration"""
        if not self.enabled:
            return CacheConfig(
                enabled=settings.CACHE_ENABLED,
                ttl=settings.CACHE_TTL,
                max_size=settings.CACHE_MAX_SIZE
            )
        
        try:
            enabled = await self.redis.get("config:cache:enabled")
            ttl = await self.redis.get("config:cache:ttl")
            max_size = await self.redis.get("config:cache:max_size")
            
            return CacheConfig(
                enabled=enabled.decode() == "true" if enabled else settings.CACHE_ENABLED,
                ttl=int(ttl) if ttl else settings.CACHE_TTL,
                max_size=int(max_size) if max_size else settings.CACHE_MAX_SIZE
            )
        except Exception as e:
            logger.error(f"Failed to get cache config: {str(e)}")
            return CacheConfig(
                enabled=settings.CACHE_ENABLED,
                ttl=settings.CACHE_TTL,
                max_size=settings.CACHE_MAX_SIZE
            )
    
    async def update_cache_config(self, config: CacheConfig):
        """Update cache configuration"""
        if not self.enabled:
            return False
        
        try:
            await self.redis.set("config:cache:enabled", "true" if config.enabled else "false")
            await self.redis.set("config:cache:ttl", config.ttl)
            await self.redis.set("config:cache:max_size", config.max_size)
            
            logger.info(f"Cache config updated: enabled={config.enabled}, ttl={config.ttl}")
            return True
        except Exception as e:
            logger.error(f"Failed to update cache config: {str(e)}")
            return False
    
    # ============================================================
    # Security Configuration
    # ============================================================
    
    async def get_security_config(self) -> SecurityConfig:
        """Get current security configuration"""
        if not self.enabled:
            return SecurityConfig(
                webhook_secret=settings.WEBHOOK_SECRET,
                rate_limit=settings.RATE_LIMIT_PER_MINUTE
            )
        
        try:
            webhook_secret = await self.redis.get("config:security:webhook_secret")
            rate_limit = await self.redis.get("config:security:rate_limit")
            
            return SecurityConfig(
                webhook_secret=webhook_secret.decode() if webhook_secret else settings.WEBHOOK_SECRET,
                rate_limit=int(rate_limit) if rate_limit else settings.RATE_LIMIT_PER_MINUTE
            )
        except Exception as e:
            logger.error(f"Failed to get security config: {str(e)}")
            return SecurityConfig(
                webhook_secret=settings.WEBHOOK_SECRET,
                rate_limit=settings.RATE_LIMIT_PER_MINUTE
            )
    
    async def update_security_config(self, config: SecurityConfig):
        """Update security configuration"""
        if not self.enabled:
            return False
        
        try:
            await self.redis.set("config:security:webhook_secret", config.webhook_secret)
            await self.redis.set("config:security:rate_limit", config.rate_limit)
            
            logger.info("Security config updated")
            return True
        except Exception as e:
            logger.error(f"Failed to update security config: {str(e)}")
            return False
    
    # ============================================================
    # Utilities
    # ============================================================
    
    async def reload_config(self):
        """Force reload configuration from Redis"""
        logger.info("Configuration reloaded from Redis")
        return True
    
    async def clear_cache(self):
        """Clear all cached data"""
        if not self.enabled:
            return False
        
        try:
            # Clear cache keys (implement based on your cache strategy)
            keys = await self.redis.keys("cache:*")
            if keys:
                await self.redis.delete(*keys)
            
            logger.info(f"Cleared {len(keys)} cache entries")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return False


# Singleton instance
config_manager = ConfigManager()
