"""
Configuration manager for dynamic config updates via Redis.
"""

from typing import Optional, List
import json
from .models import (
    MCPConfig, 
    CacheConfig, 
    SecurityConfig, 
    DashboardUser, 
    UserRole,
    AuditLogEntry,
    AuditAction,
    EmailAlertConfig
)
from .config import settings
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages dynamic configuration stored in Redis"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.enabled = redis_client is not None
        # In-memory fallback for when Redis is disabled
        self._memory_config = {}
        if not self.enabled:
            logger.warning("Redis is disabled. ConfigManager will use In-Memory storage (not persistent).")
    
    # ============================================================
    # MCP Configuration
    # ============================================================
    
    async def get_mcp_config(self) -> MCPConfig:
        """Get current MCP configuration"""
        if not self.enabled:
            # Return default from settings BUT include memory fallback for Gemini
            return MCPConfig(
                url=self._memory_config.get("url", settings.MCP_URL),
                timeout=settings.MCP_TIMEOUT,
                max_retries=settings.MCP_MAX_RETRIES,
                retry_delay=settings.MCP_RETRY_DELAY,
                mcp_token=settings.MCP_TOKEN,
                use_keycloak=settings.KC_USE_AUTH,
                kc_server_url=settings.KC_SERVER_URL,
                kc_realm=settings.KC_REALM,
                kc_client_id=settings.KC_CLIENT_ID,
                kc_client_secret=settings.KC_CLIENT_SECRET,
                gemini_api_key=self._memory_config.get("gemini_api_key")
            )
        
        try:
            # Get from Redis
            url = await self.redis.get("config:mcp:url")
            timeout = await self.redis.get("config:mcp:timeout")
            max_retries = await self.redis.get("config:mcp:max_retries")
            retry_delay = await self.redis.get("config:mcp:retry_delay")
            mcp_token = await self.redis.get("config:mcp:mcp_token")
            use_keycloak = await self.redis.get("config:mcp:use_keycloak")
            kc_server_url = await self.redis.get("config:mcp:kc_server_url")
            kc_realm = await self.redis.get("config:mcp:kc_realm")
            kc_client_id = await self.redis.get("config:mcp:kc_client_id")
            kc_client_secret = await self.redis.get("config:mcp:kc_client_secret")
            gemini_api_key = await self.redis.get("config:mcp:gemini_api_key")
            
            return MCPConfig(
                url=url.decode() if url else settings.MCP_URL,
                timeout=int(timeout) if timeout else settings.MCP_TIMEOUT,
                max_retries=int(max_retries) if max_retries else settings.MCP_MAX_RETRIES,
                retry_delay=int(retry_delay) if retry_delay else settings.MCP_RETRY_DELAY,
                mcp_token=mcp_token.decode() if mcp_token else settings.MCP_TOKEN,
                use_keycloak=use_keycloak.decode() == 'true' if use_keycloak else settings.KC_USE_AUTH,
                kc_server_url=kc_server_url.decode() if kc_server_url else settings.KC_SERVER_URL,
                kc_realm=kc_realm.decode() if kc_realm else settings.KC_REALM,
                kc_client_id=kc_client_id.decode() if kc_client_id else settings.KC_CLIENT_ID,
                kc_client_secret=kc_client_secret.decode() if kc_client_secret else settings.KC_CLIENT_SECRET,
                gemini_api_key=gemini_api_key.decode() if gemini_api_key else None
            )
        except Exception as e:
            logger.error(f"Failed to get MCP config from Redis: {str(e)}")
            # Fallback to settings + memory
            return MCPConfig(
                url=self._memory_config.get("url", settings.MCP_URL),
                timeout=settings.MCP_TIMEOUT,
                max_retries=settings.MCP_MAX_RETRIES,
                retry_delay=settings.MCP_RETRY_DELAY,
                mcp_token=settings.MCP_TOKEN,
                use_keycloak=settings.KC_USE_AUTH,
                kc_server_url=settings.KC_SERVER_URL,
                kc_realm=settings.KC_REALM,
                kc_client_id=settings.KC_CLIENT_ID,
                kc_client_secret=settings.KC_CLIENT_SECRET,
                gemini_api_key=self._memory_config.get("gemini_api_key")
            )
    
    async def update_mcp_config(self, config: MCPConfig):
        """Update MCP configuration"""
        if not self.enabled:
            logger.warning("Updating config in MEMORY (not persistent)")
            self._memory_config["url"] = config.url
            self._memory_config["gemini_api_key"] = config.gemini_api_key
            # ... other fields could be added here if needed, but these are the critical ones for Gemini
            return True
        
        try:
            await self.redis.set("config:mcp:url", config.url)
            await self.redis.set("config:mcp:timeout", config.timeout)
            await self.redis.set("config:mcp:max_retries", config.max_retries)
            await self.redis.set("config:mcp:retry_delay", config.retry_delay)
            
            if config.mcp_token:
                await self.redis.set("config:mcp:mcp_token", config.mcp_token)
            else:
                await self.redis.delete("config:mcp:mcp_token")

            await self.redis.set("config:mcp:use_keycloak", "true" if config.use_keycloak else "false")
            if config.kc_server_url: await self.redis.set("config:mcp:kc_server_url", config.kc_server_url)
            if config.kc_realm: await self.redis.set("config:mcp:kc_realm", config.kc_realm)
            if config.kc_client_id: await self.redis.set("config:mcp:kc_client_id", config.kc_client_id)
            if config.kc_client_secret: await self.redis.set("config:mcp:kc_client_secret", config.kc_client_secret)
            
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
    
    async def update_security_config(self, config: SecurityConfig) -> bool:
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
    # Email Alerts Configuration
    # ============================================================

    async def get_email_config(self) -> EmailAlertConfig:
        """Get current email alert configuration"""
        if not self.enabled:
            return EmailAlertConfig(
                smtp_server=settings.SMTP_SERVER,
                smtp_port=settings.SMTP_PORT,
                smtp_user=settings.SMTP_USER or "",
                smtp_password=settings.SMTP_PASSWORD or "",
                recipient_email=settings.ALERT_EMAIL_RECIPIENT or ""
            )
            
        try:
            enabled = await self.redis.get("config:email:enabled")
            smtp_server = await self.redis.get("config:email:smtp_server")
            smtp_port = await self.redis.get("config:email:smtp_port")
            smtp_user = await self.redis.get("config:email:smtp_user")
            smtp_password = await self.redis.get("config:email:smtp_password")
            recipient_email = await self.redis.get("config:email:recipient_email")
            alert_mcp = await self.redis.get("config:email:alert_on_mcp_error")
            alert_cb = await self.redis.get("config:email:alert_on_circuit_breaker")
            
            return EmailAlertConfig(
                enabled=enabled.decode() == "true" if enabled else False,
                smtp_server=smtp_server.decode() if smtp_server else settings.SMTP_SERVER,
                smtp_port=int(smtp_port) if smtp_port else settings.SMTP_PORT,
                smtp_user=smtp_user.decode() if smtp_user else (settings.SMTP_USER or ""),
                smtp_password=smtp_password.decode() if smtp_password else (settings.SMTP_PASSWORD or ""),
                recipient_email=recipient_email.decode() if recipient_email else (settings.ALERT_EMAIL_RECIPIENT or ""),
                alert_on_mcp_error=alert_mcp.decode() == "true" if alert_mcp else True,
                alert_on_circuit_breaker=alert_cb.decode() == "true" if alert_cb else True
            )
        except Exception as e:
            logger.error(f"Failed to get email config: {str(e)}")
            return EmailAlertConfig()

    async def update_email_config(self, config: EmailAlertConfig) -> bool:
        """Update email alert configuration"""
        if not self.enabled:
            return False
            
        try:
            await self.redis.set("config:email:enabled", "true" if config.enabled else "false")
            await self.redis.set("config:email:smtp_server", config.smtp_server)
            await self.redis.set("config:email:smtp_port", config.smtp_port)
            await self.redis.set("config:email:smtp_user", config.smtp_user)
            await self.redis.set("config:email:smtp_password", config.smtp_password)
            await self.redis.set("config:email:recipient_email", config.recipient_email)
            await self.redis.set("config:email:alert_on_mcp_error", "true" if config.alert_on_mcp_error else "false")
            await self.redis.set("config:email:alert_on_circuit_breaker", "true" if config.alert_on_circuit_breaker else "false")
            
            logger.info("Email alert config updated")
            return True
        except Exception as e:
            logger.error(f"Failed to update email config: {str(e)}")
            return False

    # ============================================================
    # User Management
    # ============================================================

    async def get_users(self) -> List[DashboardUser]:
        """Get all dashboard users"""
        if not self.enabled:
            # Return default admin from settings if no Redis
            return [DashboardUser(
                username=settings.DASHBOARD_USERNAME,
                password=settings.DASHBOARD_PASSWORD,
                role=UserRole.ADMIN
            )]
        
        try:
            # Get users from Redis (stored as a hash)
            user_keys = await self.redis.keys("config:users:*")
            users = []
            
            # If no users in Redis, add the default one
            if not user_keys:
                default_user = DashboardUser(
                    username=settings.DASHBOARD_USERNAME,
                    password=settings.DASHBOARD_PASSWORD,
                    role=UserRole.ADMIN
                )
                await self.add_user(default_user)
                return [default_user]

            for key in user_keys:
                user_data = await self.redis.get(key)
                if user_data:
                    users.append(DashboardUser.model_validate_json(user_data))
            
            return users
        except Exception as e:
            logger.error(f"Failed to get users: {str(e)}")
            return []

    async def add_user(self, user: DashboardUser) -> bool:
        """Add or update a user"""
        if not self.enabled:
            return False
            
        try:
            await self.redis.set(f"config:users:{user.username}", user.model_dump_json())
            return True
        except Exception as e:
            logger.error(f"Failed to add user: {str(e)}")
            return False

    async def delete_user(self, username: str) -> bool:
        """Delete a user"""
        if not self.enabled:
            return False
            
        try:
            # Don't delete the last admin or the default admin if possible (safety)
            if username == settings.DASHBOARD_USERNAME:
                logger.warning(f"Prevented deletion of default admin: {username}")
                return False
                
            await self.redis.delete(f"config:users:{username}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user: {str(e)}")
            return False

    # ============================================================
    # Audit Log Management
    # ============================================================

    async def log_audit_action(self, entry: AuditLogEntry) -> bool:
        """Log an administrative action to Redis"""
        if not self.enabled:
            return False
            
        try:
            key = "config:audit_log"
            # Push to the head of the list
            await self.redis.lpush(key, entry.model_dump_json())
            # Keep only the last 1000 entries
            await self.redis.ltrim(key, 0, 999)
            return True
        except Exception as e:
            logger.error(f"Failed to log audit action: {str(e)}")
            return False

    async def get_audit_logs(self, limit: int = 100) -> List[AuditLogEntry]:
        """Retrieve recent audit log entries"""
        if not self.enabled:
            return []
            
        try:
            key = "config:audit_log"
            # Limit to 1000 max for safety
            limit = min(limit, 1000)
            logs_data = await self.redis.lrange(key, 0, limit - 1)
            
            logs = []
            for item in logs_data:
                try:
                    logs.append(AuditLogEntry.model_validate_json(item))
                except Exception as ve:
                    logger.error(f"Value error parsing audit log entry: {str(ve)}")
                    
            return logs
        except Exception as e:
            logger.error(f"Failed to get audit logs: {str(e)}")
            return []
    
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
