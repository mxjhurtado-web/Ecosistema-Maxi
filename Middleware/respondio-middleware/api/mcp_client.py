"""
HTTP client for MCP communication with retry logic and circuit breaker.
"""

import httpx
import time
import asyncio
from typing import Optional, Tuple
from .models import MCPRequest, MCPResponse, ResponseStatus
from .config import settings
from .auth import KeycloakAuthService
import logging

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for communicating with MCP server"""
    
    def __init__(self):
        self.url = settings.MCP_URL
        self.timeout = settings.MCP_TIMEOUT
        self.max_retries = settings.MCP_MAX_RETRIES
        self.retry_delay = settings.MCP_RETRY_DELAY
        self.mcp_token = settings.MCP_TOKEN
        self.gemini_api_key = None
        
        # Keycloak Auth Service
        self.kc_auth = None
        if settings.KC_USE_AUTH and settings.KC_SERVER_URL:
            self.kc_auth = KeycloakAuthService(
                server_url=settings.KC_SERVER_URL,
                realm=settings.KC_REALM,
                client_id=settings.KC_CLIENT_ID,
                client_secret=settings.KC_CLIENT_SECRET
            )
        
        # Circuit breaker state
        self.failure_count = 0
        self.circuit_open = False
        self.circuit_open_time = None
    
    def _check_circuit(self) -> bool:
        """Check if circuit breaker is open"""
        if not settings.CIRCUIT_BREAKER_ENABLED:
            return False
        
        if self.circuit_open:
            # Check if timeout has passed
            if time.time() - self.circuit_open_time > settings.CIRCUIT_TIMEOUT:
                logger.info("Circuit breaker timeout passed, attempting to close")
                self.circuit_open = False
                self.failure_count = 0
                return False
            return True
        
        return False
    
    def _record_success(self):
        """Record successful call"""
        self.failure_count = 0
        if self.circuit_open:
            logger.info("Circuit breaker closed after successful call")
            self.circuit_open = False
    
    def _record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        
        if settings.CIRCUIT_BREAKER_ENABLED and \
           self.failure_count >= settings.CIRCUIT_FAILURE_THRESHOLD:
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")
            self.circuit_open = True
            self.circuit_open_time = time.time()
            
            # Fire alert trigger (background task since aiosmtplib is async)
            from .email_service import email_service
            from .config_manager import config_manager
            
            async def fire_cb_alert():
                config = await config_manager.get_email_config()
                if config.enabled and config.alert_on_circuit_breaker:
                    await email_service.send_alert(
                        "Circuit Breaker Opened",
                        f"The ORBIT circuit breaker has been activated after {self.failure_count} consecutive failures. "
                        "Middleware is now in safety mode (returning fallbacks)."
                    )
            
            asyncio.create_task(fire_cb_alert())
    
    async def query(
        self, 
        user_text: str, 
        context: Optional[dict] = None
    ) -> Tuple[Optional[str], ResponseStatus, int, int]:
        """
        Query the MCP server.
        
        Args:
            user_text: User's query text
            context: Additional context
        
        Returns:
            Tuple of (response_text, status, latency_ms, retry_count)
        """
        # Check circuit breaker
        if self._check_circuit():
            logger.warning("Circuit breaker is open, returning fallback")
            return (
                "Lo siento, el servicio está temporalmente no disponible. Por favor intenta más tarde.",
                ResponseStatus.ERROR,
                0,
                0
            )
        
        # Prepare request
        full_context = context.copy() if context else {}
        full_context["gemini_api_key"] = self.gemini_api_key
        
        mcp_request = MCPRequest(
            query=user_text,
            context=full_context
        )
        
        retry_count = 0
        last_error = None
        
        # Retry loop
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                # Set headers for MCP authentication
                headers = {}
                
                # Priority: Keycloak Service Account > Manual Token
                auth_token = self.mcp_token
                if self.kc_auth:
                    kc_token = await self.kc_auth.get_access_token()
                    if kc_token:
                        auth_token = kc_token
                
                if auth_token:
                    headers["Authorization"] = f"Bearer {auth_token}"
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.url,
                        json=mcp_request.model_dump(),
                        headers=headers,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    
                    latency_ms = int((time.time() - start_time) * 1000)
                    
                    # Parse response
                    mcp_response = MCPResponse(**response.json())
                    
                    # Record success
                    self._record_success()
                    
                    # Determine status based on latency
                    if latency_ms > 5000:
                        status = ResponseStatus.DEGRADED
                    else:
                        status = ResponseStatus.OK
                    
                    logger.info(
                        f"MCP query successful",
                        extra={
                            "latency_ms": latency_ms,
                            "retry_count": retry_count,
                            "status": status
                        }
                    )
                    
                    return (
                        mcp_response.response,
                        status,
                        latency_ms,
                        retry_count
                    )
            
            except httpx.TimeoutException as e:
                last_error = f"MCP timeout: {str(e)}"
                logger.warning(f"MCP timeout on attempt {attempt + 1}/{self.max_retries + 1}")
                retry_count += 1
                
            except httpx.HTTPStatusError as e:
                last_error = f"MCP HTTP error: {e.response.status_code}"
                logger.error(f"MCP HTTP error: {e.response.status_code}")
                retry_count += 1
                
            except Exception as e:
                last_error = f"MCP error: {str(e)}"
                logger.error(f"Unexpected MCP error: {str(e)}")
                retry_count += 1
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay)
        
        # All retries failed
        self._record_failure()
        
        logger.error(
            f"MCP query failed after {retry_count} retries",
            extra={"error": last_error}
        )
        
        # Fire alert trigger for MCP Error
        from .email_service import email_service
        from .config_manager import config_manager
        
        async def fire_mcp_alert():
            config = await config_manager.get_email_config()
            if config.enabled and config.alert_on_mcp_error:
                await email_service.send_alert(
                    "MCP Connection Failure",
                    f"A query failed after {retry_count} retries.\nError: {last_error}\nQuery: {user_text[:100]}..."
                )
        
        asyncio.create_task(fire_mcp_alert())
        
        # Return fallback message
        return (
            "Lo siento, no pude procesar tu solicitud en este momento. Por favor intenta nuevamente.",
            ResponseStatus.ERROR,
            0,
            retry_count
        )
    
    async def health_check(self) -> bool:
        """Check if MCP is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.url.replace("/query", "/health"),
                    timeout=2
                )
                return response.status_code == 200
        except Exception:
            return False


# Singleton instance
import asyncio
mcp_client = MCPClient()
