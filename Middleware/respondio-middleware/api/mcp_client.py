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
        
        # Mock DB for simulation mode
        self.mock_db = {}
    
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
        context: Optional[dict] = None,
        agent_name: Optional[str] = None
    ) -> Tuple[Optional[str], ResponseStatus, int, int]:
        """
        Query the MCP server.
        
        Args:
            user_text: User's query text
            context: Additional context
            agent_name: Name of the agent to use
        
        Returns:
            Tuple of (response_text, status, latency_ms, retry_count)
        """
        # Fetch latest config from manager (handles Redis or In-Memory)
        from .config_manager import config_manager
        curr_config = await config_manager.get_mcp_config()
        
        # Default settings
        self.url = curr_config.url
        self.gemini_api_key = curr_config.gemini_api_key
        readonly = False
        system_prompt = None
        
        # Overwrite with Agent settings if provided
        agent_rules = {}
        knowledge_sources = []
        web_search = False
        
        if agent_name:
            agent = await config_manager.get_agent(agent_name)
            if agent:
                if agent.mcp_url:
                    self.url = agent.mcp_url
                readonly = agent.readonly
                system_prompt = agent.system_prompt
                agent_rules = agent.specific_rules or {}
                knowledge_sources = agent.knowledge_sources
                web_search = agent.web_search_enabled
                logger.info(f"Using agent '{agent_name}' config: readonly={readonly}, rules={bool(agent_rules)}, web={web_search}")
            else:
                logger.warning(f"Agent '{agent_name}' not found, falling back to default config")
        
        # Check circuit breaker (skip if emergency mode is active)
        is_emergency = curr_config.emergency_mode and self.gemini_api_key
        
        if not is_emergency and self._check_circuit():
            logger.warning("Circuit breaker is open, returning fallback")
            return (
                "Lo siento, el servicio está temporalmente no disponible (Circuit Breaker Abierto). Por favor intenta más tarde.",
                ResponseStatus.ERROR,
                0,
                0
            )
        
        # Prepare context
        full_context = context.copy() if context else {}
        full_context["gemini_api_key"] = self.gemini_api_key
        full_context["readonly"] = readonly
        full_context["knowledge_sources"] = knowledge_sources
        full_context["web_search_enabled"] = web_search
        
        # Process specific rules into system prompt as JSON
        if agent_rules:
            import json
            rules_json = json.dumps(agent_rules, indent=2, ensure_ascii=False)
            rules_text = f"\n\nMAPA DE REGLAS ESPECÍFICAS (JSON):\n```json\n{rules_json}\n```"
            if system_prompt:
                system_prompt += rules_text
            else:
                system_prompt = rules_text
        
        full_context["system_prompt"] = system_prompt
        full_context["agent_rules"] = agent_rules
        
        # --- Emergency Mode / Direct Gemini Support ---
        if curr_config.emergency_mode and self.gemini_api_key:
            logger.info("🚨 Emergency Mode Active: Using Direct Gemini Fallback")
            response_text = await self._query_gemini_direct(user_text, full_context)
            
            # Post-processing for simulation logic
            mock_response = await self._simulate_logic(user_text, context, response_text)
            if mock_response:
                response_text = mock_response

            return (
                response_text,
                ResponseStatus.OK,
                100, # Fake latency
                0
            )
        
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

    async def _query_gemini_direct(self, query: str, context: dict) -> str:
        """Call Gemini API directly via REST (when MCP is offline)"""
        api_key = context.get("gemini_api_key")
        if not api_key:
            return "Error: Gemini API Key no configurada."
            
        # Use Gemini 2.5 Flash (Standard for User's Projects)
        model_id = "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_id}:generateContent?key={api_key}"
        
        system_prompt = context.get("system_prompt", "Eres un asistente de IA útil.")
        prompt_text = f"{system_prompt}\n\nPregunta: {query}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=20)
                response.raise_for_status()
                data = response.json()
                return data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            logger.error(f"Direct Gemini call failed: {str(e)}")
            return f"Error en conexión directa con Gemini: {str(e)}"

    async def _simulate_logic(self, query: str, context: dict, response: str) -> Optional[str]:
        """Simulate database logic in memory for testing flows"""
        contact_id = context.get("contact_id", "default_user")
        
        # Detect intent for simulation (simplified)
        query_lower = query.lower()
        
        # 1. New User / Register flow
        if any(w in query_lower for w in ["envío", "enviar", "mandar"]) and not any(w in query_lower for w in ["estatus", "clima", "noticias"]):
            import uuid
            folio = f"MOCK-{uuid.uuid4().hex[:6].upper()}"
            
            if contact_id not in self.mock_db:
                self.mock_db[contact_id] = {"registros": []}
            
            self.mock_db[contact_id]["registros"].append({
                "folio": folio,
                "timestamp": time.time(),
                "text": query,
                "status": "En Proceso"
            })
            
            logger.info(f"💾 MOCK: Registro de envío guardado para {contact_id}. Folio: {folio}")
            return f"{response}\n\n✅ [MEMORIA TEMPORAL] Se ha simulado el registro de tu envío. Folio: **{folio}**"

        # 2. Status check flow
        if any(w in query_lower for w in ["estatus", "rastrear", "mi envío", "folio"]):
            if contact_id in self.mock_db and self.mock_db[contact_id]["registros"]:
                last_reg = self.mock_db[contact_id]["registros"][-1]
                logger.info(f"🔍 MOCK: Consulta de estatus para {contact_id}. Encontrado: {last_reg['folio']}")
                return f"{response}\n\n🔍 [MEMORIA TEMPORAL] Consultando el folio **{last_reg['folio']}**... Estatus: **{last_reg['status']}**."
            else:
                return f"{response}\n\nℹ️ [MEMORIA TEMPORAL] No encontré envíos previos en esta sesión simulada."

        return None
    
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
