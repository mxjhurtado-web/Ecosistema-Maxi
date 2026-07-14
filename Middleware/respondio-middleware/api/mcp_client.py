"""
HTTP client for MCP communication with retry logic and circuit breaker.
"""

import httpx
import time
import asyncio
import base64
import re
from typing import Optional, Tuple
from .models import MCPRequest, MCPResponse, ResponseStatus
from .config import settings
from .auth import KeycloakAuthService
from .shared_logic import get_compliance_scripts
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
            from .google_chat_service import google_chat_service
            from .config_manager import config_manager
            
            async def fire_cb_alert():
                # Email alert
                email_config = await config_manager.get_email_config()
                if email_config.enabled and email_config.alert_on_circuit_breaker:
                    await email_service.send_alert(
                        "Circuit Breaker Opened",
                        f"The ORBIT circuit breaker has been activated after {self.failure_count} consecutive failures. "
                        "Middleware is now in safety mode (returning fallbacks)."
                    )
                
                # Google Chat alert
                chat_config = await config_manager.get_google_chat_config()
                if chat_config.enabled and chat_config.alert_on_circuit_breaker:
                    await google_chat_service.send_alert(
                        "Circuit Breaker Activado",
                        f"El Circuit Breaker de ORBIT se ha abierto tras {self.failure_count} fallos consecutivos. El middleware está en modo de seguridad.",
                        level="ERROR"
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
        
        # Diagnostic logging for Render env variables
        import os
        env_keys = [k for k in os.environ.keys() if "GEMINI" in k or "API_KEY" in k]
        logger.info(f"🔍 [DIAGNOSTIC] env_keys starting with GEMINI or API_KEY: {env_keys}")
        logger.info(f"⚙️ [DIAGNOSTIC] Configured MCP URL: {self.url} | Gemini API Key present: {'YES' if self.gemini_api_key else 'NO'}")
        
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

        # --- PHASE 28: COMPLIANCE SYSTEM PROMPT INJECTION ---
        scripts = get_compliance_scripts()
        compliance_footer = f"""
### REGLAS DE CUMPLIMIENTO DE WHATSAPP (OBLIGATORIO) ###
Usted es ÚNICAMENTE UN CANAL DE COMUNICACIÓN. NO está autorizado para realizar validaciones ni toma de decisiones finales. 
Todas las actividades reguladas (KYC, aprobación, liberación de fondos) se realizan fuera de WhatsApp en el sistema Chronos.

USE ESTOS SCRIPTS DE FORMA LITERAL (SIN IMPROVISAR):
- Soporte General: "{scripts.get('A2_GENERAL_SUPPORT', '')}"
- Documentación Necesaria: "{scripts.get('A3_DOCUMENTATION', '')}"
- Disputa/Reembolso/Error: "{scripts.get('A4_DISPUTE_REDIRECTION', '')}"
- Seguridad/Actividad Sospechosa: "{scripts.get('A5_SUSPICIOUS_ACTIVITY', '')}"
- Derechos de Privacidad: "{scripts.get('A6_PRIVACY_REDIRECTION', '')}"

REGLAS ESTRICTAS:
1. PROHIBIDO improvisar o parafrasear los scripts anteriores.
2. PROHIBIDO realizar validaciones de identidad o verificación de documentos (evite "todo se ve bien", "verificado").
3. PROHIBIDO confirmar resultados de transacciones (evite "está aprobado", "está liberado").
4. Si un usuario solicita una disputa o derecho de privacidad, DEBE usar el script de redirección correspondiente de inmediato.
5. Toda documentación recibida debe confirmarse con el script A3 ("recibida y transferida para procesamiento").
"""
        if system_prompt:
            system_prompt = f"{system_prompt}\n\n{compliance_footer}"
        else:
            system_prompt = compliance_footer

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

        # --- PHASE 28: AUTOMATED COMPLIANCE TRIGGERS ---
        scripts = get_compliance_scripts()
        user_text_lower = user_text.lower()
        
        # Dispute detection (A4 Script)
        dispute_keywords = ["disputa", "reembolso", "error", "reclamo", "dispute", "refund", "claim", "re-embolso"]
        if any(kw in user_text_lower for kw in dispute_keywords):
            logger.info("🛡️ Automated compliance trigger: Dispute detected")
            return (
                scripts.get("A4_DISPUTE_REDIRECTION", "Disputes cannot be handled here."),
                ResponseStatus.OK,
                10,
                0
            )
            
        # Privacy detection (A6 Script)
        privacy_keywords = ["privacidad", "datos", "borrar", "privacy", "data", "delete", "identity rights"]
        if any(kw in user_text_lower for kw in privacy_keywords):
            logger.info("🛡️ Automated compliance trigger: Privacy request detected")
            return (
                scripts.get("A6_PRIVACY_REDIRECTION", "Privacy requests cannot be handled here."),
                ResponseStatus.OK,
                10,
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
        
        # --- DEVOPS MCP ROUTING (MAXIBOT) ---
        # Solo rutear al DevOps MCP si SSO está activo Y tenemos un token de espacio válido.
        # Si KC_USE_AUTH=False (modo de prueba/dev), caer en Gemini conversacional directamente.
        bot_name = full_context.get("bot_identity")
        space_token = full_context.get("space_token")
        if bot_name == "MaxiBot" and self.gemini_api_key and settings.KC_USE_AUTH and space_token:
            logger.info("🔧 Routing query to DevOps MCP for MaxiBot (SSO token available)...")
            response_text = await self._query_devops_mcp(user_text, full_context)
            
            # Post-processing for simulation logic
            mock_response = await self._simulate_logic(user_text, context, response_text)
            if mock_response:
                response_text = mock_response

            return (
                response_text,
                ResponseStatus.OK,
                2000,  # Estimated latency
                0
            )
        elif bot_name == "MaxiBot" and not settings.KC_USE_AUTH:
            logger.info("🤖 MaxiBot en modo conversacional (KC_USE_AUTH=False). Usando Gemini directo...")
            
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
        
        # --- SMART HYBRID ROUTER (AUTO-AGENT FOR CONVERSATIONAL QUERIES) ---
        # Si no hay un código de seguimiento en el texto, y tenemos la API Key de Gemini activa,
        # respondemos la consulta de forma conversacional y amigable directamente usando Gemini (Auto-Agent).
        # Esto evita respuestas robóticas y cuadradas ante preguntas de ayuda generales.
        import re
        def extraer_codigo_router(texto: str) -> Optional[str]:
            # Eliminar URLs para evitar que los IDs de archivos (Docs, Drive, etc.) se confundan con códigos de seguimiento
            texto_limpio = re.sub(r'https?://\S+', '', texto)
            
            patrones = [
                r'\b[A-Z]{2}\d{9,}\b',   # CE17016886149
                r'\b[A-Z0-9]{10,}\b',    # Genérico largo
            ]
            for patron in patrones:
                m = re.search(patron, texto_limpio.upper())
                if m:
                    codigo_candidato = m.group()
                    # CRÍTICO: Si el código consiste únicamente en letras sin números (ej. "middleware"), lo ignoramos.
                    # Esto previene falsos positivos causados por el nombre del Bot o palabras del diccionario.
                    if codigo_candidato.isalpha():
                        continue
                    return codigo_candidato
            return None

        has_code = extraer_codigo_router(user_text) is not None

        if not has_code and self.gemini_api_key:
            logger.info("🤖 Auto-Agent: No tracking code detected. Routing directly to Gemini for conversational response.")
            
            # --- DETECCIÓN DE ENLACES DE GOOGLE DRIVE / DOCS ---
            doc_id = None
            doc_type = None
            doc_content = None
            
            doc_re = re.search(r"docs\.google\.com/document/d/([a-zA-Z0-9-_]+)", user_text)
            sheet_re = re.search(r"docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)", user_text)
            file_re = re.search(r"drive\.google\.com/file/d/([a-zA-Z0-9-_]+)", user_text)
            
            if doc_re:
                doc_id = doc_re.group(1)
                doc_type = "google_doc"
            elif sheet_re:
                doc_id = sheet_re.group(1)
                doc_type = "google_sheet"
            elif file_re:
                doc_id = file_re.group(1)
                doc_type = "drive_file"
                
            if doc_id and doc_type:
                logger.info(f"📂 Detected Google Drive link ({doc_type}) with ID: {doc_id}. Fetching content...")
                try:
                    from .google_sheets_service import google_sheets_service
                    doc_content = await google_sheets_service.read_drive_document(doc_id, doc_type)
                    if doc_content:
                        logger.info(f"✅ Successfully read {len(doc_content)} characters from Drive document.")
                    else:
                        logger.warning("⚠️ Google Drive read returned empty content.")
                except Exception as doc_err:
                    logger.error(f"Failed to read Drive document: {str(doc_err)}")

            # --- BASE DE CONOCIMIENTO DINÁMICA (GOOGLE SHEETS FAQ) ---
            faq_spreadsheet_id = "1wrtj7SZ6wB9h1yd_9h613DYNPGjI69_Zj1gLigiUHtE"
            faq_knowledge = None
            try:
                from .google_sheets_service import google_sheets_service
                faq_knowledge = await google_sheets_service.fetch_faq_data(faq_spreadsheet_id)
            except Exception as faq_err:
                logger.error(f"Failed to fetch dynamic FAQ sheet: {str(faq_err)}")

            # Obtener el nombre del bot dinámicamente desde el contexto
            bot_name = "ORBIT Bot"
            if context and isinstance(context, dict):
                bot_name = context.get("bot_identity", "ORBIT Bot")

            conversational_prompt = f"""
### GUÍA DE ATENCIÓN CONVERSACIONAL (AUTO-AGENTE) ###
Usted es {bot_name}, el asistente inteligente y amigable de soporte e integración del ecosistema Maxi. Su tono debe ser sumamente cálido, natural, empático y servicial en español.

### REGLAS DE ATENCIÓN FLEXIBLE:
1. Si el usuario pregunta por temas corporativos, procesos o soporte de Maxi, use la base de conocimientos oficial provista abajo.
2. Si el usuario le hace preguntas generales, pláticas casuales, consultas creativas, de entretenimiento o recomendaciones generales (por ejemplo: "¿qué me sugieres comer hoy?", chistes, consejos generales, datos curiosos, etc.), responda con total libertad, entusiasmo y creatividad usando todo su conocimiento general como Gemini, manteniendo siempre la calidez, amabilidad y empatía de Maxi. ¡No se limite a temas de Maxi si el usuario desea charlar de forma casual o general!
"""
            if faq_knowledge:
                conversational_prompt += f"""
### BASE DE CONOCIMIENTO OFICIAL (FAQs de Maxi) ###
Utilice las siguientes preguntas y respuestas oficiales para resolver las dudas del usuario. Responda de manera sumamente humana y conversacional. Si el usuario pregunta algo sobre Maxi que no está cubierto por estas FAQs, use el sentido común amigable de Maxi o sugiérale amablemente contactar al soporte humano:

{faq_knowledge}
"""
            else:
                conversational_prompt += """
Si el usuario pregunta cómo encontrar su código de envío, dónde buscarlo o indica que no lo tiene:
1. Explíquele de forma muy amigable que el código es una clave alfanumérica única (generalmente inicia con dos letras como "CE" seguidas de números, ej: CE17016886149).
2. Indíquele que puede encontrar este código de las siguientes formas:
   - Impreso en el recibo físico de MaxiSend que le entregaron en la sucursal al realizar el envío.
   - En el correo electrónico de confirmación que recibió de MaxiSend al enviar.
   - En mensajes de WhatsApp o SMS anteriores de notificaciones oficiales de MaxiSend.
3. Invítelo cordialmente a buscar su código y escribirlo en el chat para que usted pueda consultar el estatus en tiempo real en la base de datos de Supabase.
4. Si no cuenta con él o lo ha extraviado, sugiérale amablemente contactar al soporte de Maxi (soporte humano) o verificar con la persona que le realizó el envío.
"""
            if doc_content:
                conversational_prompt += f"""

### CONTENIDO DEL DOCUMENTO ADJUNTO (LEÍDO DESDE GOOGLE DRIVE) ###
El usuario ha adjuntado un documento de Google Drive/Docs. A continuación se muestra su contenido extraído en texto plano:

{doc_content}

### INSTRUCCIONES DE RESPUESTA PARA EL DOCUMENTO ADJUNTO:
1. El usuario te ha proporcionado este documento para que lo leas, analices, respondas preguntas específicas, realices un resumen o lleves a cabo alguna tarea sobre él.
2. Utiliza la información real que se encuentra en el texto de arriba para responder a la solicitud sobre el documento.
3. Menciona de forma muy amigable, entusiasta y cálida que has podido leer el documento adjunto y que con gusto le das la información o el resumen que te ha pedido.
"""
            elif doc_id:
                conversational_prompt += f"""

### ERROR CRÍTICO: NO SE PUDO DESCARGAR EL DOCUMENTO ADJUNTO ###
El usuario incluyó un enlace a un archivo de Google Drive/Docs (ID: **{doc_id}**), pero el bot no pudo descargar su contenido debido a un error 404 de la API (problema de permisos).

### INSTRUCCIONES DE RESPUESTA CRÍTICAS (EVITAR ALUCINACIÓN):
1. **NO te inventes ni alucines el contenido del documento.** (Prohibido simular que leíste la guía de firmas, políticas de WhatsApp, planes, o cualquier otro tema ficticio).
2. Explícale al usuario de forma sumamente cálida y empática que no pudiste leer el documento porque la API de Google arrojó un error **404 (No Encontrado / Sin Permisos de Acceso)**.
3. Pídele amablemente que por favor comparta el archivo dándole acceso de **Lector** o **Editor** al correo de la Service Account que esté configurada en el bot, para que así puedas acceder a él sin problemas.
4. Explícale que en cuanto comparta el acceso al correo del bot, podrá volver a enviarte el enlace para resumirlo de inmediato.
"""

            conversational_prompt += "\nSiempre conteste en español de manera fluida y humana. Prohibido usar respuestas cortas o robóticas.\n"

            # Combine with the existing system prompt
            if system_prompt:
                full_context["system_prompt"] = f"{conversational_prompt}\n\n{system_prompt}"
            else:
                full_context["system_prompt"] = conversational_prompt
                
            response_text = await self._query_gemini_direct(user_text, full_context)
            self._record_success()
            
            return (
                response_text,
                ResponseStatus.OK,
                150,  # Simulated latency for direct Gemini REST call
                0
            )

        mcp_request = MCPRequest(
            query=user_text,
            context=full_context,
            media=context.get("media", []) if context else []
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
        from .google_chat_service import google_chat_service
        from .config_manager import config_manager
        
        async def fire_mcp_alert():
            # Email alert
            email_config = await config_manager.get_email_config()
            if email_config.enabled and email_config.alert_on_mcp_error:
                await email_service.send_alert(
                    "MCP Connection Failure",
                    f"A query failed after {retry_count} retries.\nError: {last_error}\nQuery: {user_text[:100]}..."
                )
            
            # Google Chat alert
            chat_config = await config_manager.get_google_chat_config()
            if chat_config.enabled and chat_config.alert_on_mcp_error:
                await google_chat_service.send_alert(
                    "Fallo de Conexión MCP",
                    f"Una consulta falló tras {retry_count} reintentos.\n*Error:* {last_error}\n*Consulta:* {user_text[:100]}...",
                    level="WARNING"
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
        
        # Multimodal parts
        parts = [{"text": prompt_text}]
        
        # Add media if present
        media_list = context.get("media", [])
        for item in media_list:
            mime_type = item.mime_type if hasattr(item, 'mime_type') else item.get('mime_type')
            data = item.data if hasattr(item, 'data') else item.get('data')
            url_source = item.url if hasattr(item, 'url') else item.get('url')
            
            # If data is empty but URL is present, try to fetch it
            if not data and url_source:
                try:
                    logger.info(f"Downloading media from {url_source}")
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(url_source, timeout=10)
                        resp.raise_for_status()
                        data = base64.b64encode(resp.content).decode('utf-8')
                        logger.debug(f"Media downloaded and encoded successfully ({len(data)} bytes)")
                except Exception as e:
                    logger.error(f"Failed to fetch media from URL {url_source}: {str(e)}")
                    continue # Skip this media item if download fails
            
            if data and mime_type:
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": data
                    }
                })
        
        payload = {
            "contents": [{
                "parts": parts
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

    async def _query_devops_mcp(self, query: str, context: dict) -> str:
        """Connect directly to the standard DevOps MCP server and run queries using Gemini"""
        # 1. Obtener token de Keycloak (priorizar el token del espacio recibido)
        kc_token = context.get("space_token") if context else None
        
        if not kc_token:
            logger.info("🔑 No space_token provided in context, falling back to client credentials...")
            # Inicializar el servicio de autenticación de Keycloak si no existe pero los parámetros están configurados
            if not self.kc_auth and settings.KC_SERVER_URL:
                self.kc_auth = KeycloakAuthService(
                    server_url=settings.KC_SERVER_URL,
                    realm=settings.KC_REALM,
                    client_id=settings.KC_CLIENT_ID,
                    client_secret=settings.KC_CLIENT_SECRET
                )
                
            if self.kc_auth:
                try:
                    kc_token = await self.kc_auth.get_access_token()
                except Exception as e:
                    logger.error(f"Failed to fetch Keycloak token for DevOps MCP: {e}")
                    
        if not kc_token:
            return "Error: No se pudo obtener el token de autenticación SSO de Keycloak para DevOps MCP."

        # 2. Configurar headers y endpoint
        devops_url = settings.DEVOPS_MCP_URL
        headers = {
            "Authorization": f"Bearer {kc_token}",
            "X-Forwarded-Proto": "https"
        }
        
        logger.info(f"🔗 Conectando al DevOps MCP: {devops_url}...")
        
        try:
            from mcp.client.streamable_http import streamablehttp_client
            from mcp import ClientSession
            from google import genai
            
            # Formular el prompt con las instrucciones conversacionales del bot
            system_prompt = context.get("system_prompt", "Usted es un asistente inteligente y amigable de DevOps.")
            prompt_text = f"{system_prompt}\n\nPregunta del usuario: {query}"
            
            # Inicializar cliente de Google GenAI SDK con la API key
            if not self.gemini_api_key:
                return "Error: API Key de Gemini no configurada."
                
            gemini_client = genai.Client(api_key=self.gemini_api_key)
            
            # Conexión asíncrona mediante Server-Sent Events (SSE) al DevOps MCP
            async with streamablehttp_client(devops_url, headers=headers) as streams:
                read_stream, write_stream = streams[0], streams[1]
                
                async with ClientSession(read_stream, write_stream) as session:
                    # Inicializar la negociación del protocolo
                    await session.initialize()
                    
                    logger.info("🤖 Iniciando consulta con Gemini y sesión de herramientas MCP activa...")
                    
                    # Ejecutar loop de llamadas con Gemini usando la sesión MCP como herramientas
                    response = await gemini_client.aio.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt_text,
                        config=genai.types.GenerateContentConfig(
                            temperature=0,
                            tools=[session]
                        )
                    )
                    
                    logger.info("✅ Consulta completada exitosamente.")
                    return response.text or "No recibí respuesta del modelo de IA."
                    
        except Exception as err:
            logger.error(f"Error durante consulta al DevOps MCP: {str(err)}", exc_info=True)
            return f"Error al procesar la consulta con DevOps MCP: {str(err)}"

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
