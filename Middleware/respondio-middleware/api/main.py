"""
Main FastAPI application - Middleware for Respond.io to MCP.
"""

from fastapi import FastAPI, Header, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import time
import uuid
import re
from datetime import datetime, timedelta, timezone
import logging
import json
import os
from typing import Optional, List, Dict, Any
from .shared_logic import get_compliance_scripts, resolve_script_text, translate_script_if_needed
from shared.redis_client import get_redis_client

from .models import (
    RespondioRequest,
    RespondioResponse,
    ResponseStatus,
    RequestLog,
    determine_request_category,
    HealthResponse,
    StatusCheckRequest,
    StatusCheckResponse,
    BillCheckRequest,
    BillCheckResponse,
    CSATLogRequest,
    CSATLogResponse,
    TopupCheckRequest,
    TopupCheckResponse
)
from .config import settings
from .mcp_client import mcp_client
from .telemetry import telemetry_service
from .admin_api import router as admin_router, public_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ORBIT - Integration Middleware",
    description="Production middleware connecting Respond.io to internal MCP",
    version=settings.API_VERSION
)

# Include routers
app.include_router(admin_router)
app.include_router(public_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Startup/Shutdown Events
# ============================================================

# Sheet ID for QA audits (Estatus sheet, tab "Auditoria_QA")
AUDITS_SHEET_ID = "14BdjBuXPXPkjXMKS-955fA6bNw5qRMv5IWCNhMZGIXc"
AUDITS_TAB_NAME = "Auditoria_QA"
AUDITS_HEADERS = [
    "conversation_id", "contact_id", "contact_name", "date",
    "rating_intent", "rating_resolution", "rating_formal_tone", "rating_no_repetition",
    "comments", "audited_by", "audited_at"
]

def get_audits_sheet():
    """Return the gspread worksheet for QA audits, creating the tab + headers if needed."""
    try:
        import gspread
        import base64, json
        from google.oauth2 import service_account

        # Load SA credentials the same way google_drive_service does
        sa_b64 = settings.GOOGLE_CHATS_SA_BASE64 or getattr(settings, "MAXIBOT_SA_BASE64", None)
        if not sa_b64:
            logger.error("get_audits_sheet: No SA base64 credentials configured (GOOGLE_CHATS_SA_BASE64)")
            return None

        sa_info = json.loads(base64.b64decode(sa_b64).decode("utf-8"))
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = service_account.Credentials.from_service_account_info(sa_info, scopes=scopes)
        gc = gspread.authorize(creds)

        sh = gc.open_by_key(AUDITS_SHEET_ID)
        try:
            ws = sh.worksheet(AUDITS_TAB_NAME)
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title=AUDITS_TAB_NAME, rows=1000, cols=len(AUDITS_HEADERS))
            ws.append_row(AUDITS_HEADERS, value_input_option="RAW")
            logger.info(f"✅ Created sheet tab '{AUDITS_TAB_NAME}' with headers")

        # Add headers if sheet is empty
        existing = ws.row_values(1)
        if not existing:
            ws.append_row(AUDITS_HEADERS, value_input_option="RAW")
        return ws
    except Exception as e:
        logger.error(f"Error accessing audits sheet: {e}")
        return None



async def init_qa_agent_config():
    """Verify or register the default Agente Calidad in Redis if missing"""
    try:
        from .config_manager import config_manager
        from .models import AgentConfig
        
        agent = await config_manager.get_agent("Agente Calidad")
        if not agent:
            default_prompt = (
                "Eres el 'Agente Auditor de Calidad IA' para el Ecosistema Maxi. Tu función es auditar conversaciones "
                "de soporte y calificar su desempeño contra 4 criterios de calidad.\n\n"
                "Analiza el historial de conversación en JSON adjunto y responde estrictamente con un objeto JSON "
                "que contenga las siguientes llaves:\n"
                "1. 'rating_intent' (bool): true si el bot identificó correctamente la intención del usuario al inicio del chat "
                "y lo canalizó al flujo/agente especializado correspondiente. false si falló en entender el tema o lo derivó incorrectamente.\n"
                "2. 'rating_resolution' (bool): true si el bot resolvió de forma correcta el estatus o proporcionó la información "
                "final según las reglas de negocio. false si dio información confusa, incorrecta o no concluyó.\n"
                "3. 'rating_formal_tone' (bool): true si el bot se dirigió al cliente con el trato formal de 'Usted' en el 100% "
                "de la conversación. false si el bot tuteó al cliente en algún momento (ej. usando palabras como 'tú', 'tu', 'te', 'puedes', 'tienes', etc.).\n"
                "4. 'rating_no_repetition' (bool): true si el bot solicitó la información (ej. la clave de la transacción o nombres) "
                "una sola vez. false si pidió los mismos datos de forma redundante o repetitiva a pesar de haberlos recibido.\n"
                "5. 'comments' (string): Explicación breve de la evaluación. Si alguno de los criterios fue calificado como false, "
                "indica con precisión en qué línea del diálogo ocurrió el desvío.\n\n"
                "Reglas adicionales:\n"
                "- Evalúa únicamente las respuestas del bot ('bot_max' o 'agent_specialized'). Los mensajes de humanos ('agent_human') "
                "u otros emisores no deben penalizar la calificación del bot.\n"
                "- Sé sumamente estricto con el criterio 'rating_formal_tone': cualquier tuteo informal ('tú', 'te', 'tuyos', 'puedes', 'tienes') "
                "emitido por el bot es un fallo (false).\n"
                "Responde estrictamente con JSON válido."
            )
            
            qa_agent = AgentConfig(
                name="Agente Calidad",
                system_prompt=default_prompt,
                readonly=False,
                is_orchestrator=False
            )
            await config_manager.update_agent(qa_agent)
            logger.info("✅ Default 'Agente Calidad' initialized in Redis config")
    except Exception as e:
        logger.warning(f"Could not initialize default Agente Calidad: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(f"🚀 Starting Respond.io Middleware v{settings.API_VERSION}")
    logger.info(f"MCP URL: {settings.MCP_URL}")
    logger.info(f"Cache enabled: {settings.CACHE_ENABLED}")
    logger.info(f"Circuit breaker enabled: {settings.CIRCUIT_BREAKER_ENABLED}")
    
    # Ensure Google Sheets audits tab exists
    try:
        get_audits_sheet()
        logger.info("✅ Google Sheets audits tab verified")
    except Exception as e:
        logger.warning(f"Could not verify audits sheet: {e}")
    
    # Initialize Redis connection
    try:
        from shared.redis_client import get_redis_client
        redis = await get_redis_client()
        telemetry_service.redis = redis
        telemetry_service.enabled = True
        
        # Initialize config manager
        from .config_manager import config_manager
        config_manager.redis = redis
        config_manager.enabled = True
        
        logger.info("✅ Redis connected")
        
        # Pre-initialize dynamic QA auditor agent
        await init_qa_agent_config()
        
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {str(e)}")
        logger.warning("Telemetry and config management will be disabled")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down Respond.io Middleware")


# ============================================================
# Main Webhook Endpoint
# ============================================================

@app.post("/webhook", response_model=RespondioResponse)
async def webhook(
    request: Dict[str, Any] = Body(...),
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    x_webhook_secre: Optional[str] = Header(None, alias="X-Webhook-Secre"),
    secret: Optional[str] = None
):
    """
    Main webhook endpoint for Respond.io.
    
    Validates the request, calls MCP, and returns the response.
    """
    start_time = time.time()
    trace_id = str(uuid.uuid4())
    
    # Validate webhook secret
    incoming_secret = x_webhook_secret or x_webhook_secre or secret
    if incoming_secret != settings.WEBHOOK_SECRET:
        logger.warning(
            f"❌ Invalid webhook secret",
            extra={"trace_id": trace_id}
        )
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    is_global_webhook = "contact" in request and "message" in request
    if is_global_webhook:
        contact_id = str(request["contact"].get("id"))
        logger.info(f"📨 Global webhook received for contact {contact_id}")
        
        # Log the full payload for diagnostic purposes
        try:
            logger.info(f"📨 Global Webhook Payload: {json.dumps(request)}")
        except Exception as log_err:
            logger.warning(f"Could not stringify payload: {log_err}. Raw: {request}")

        # Extract text from global webhook message
        user_msg_text = None
        if "message" in request and isinstance(request["message"], dict):
            inner_msg = request["message"].get("message")
            if isinstance(inner_msg, dict):
                user_msg_text = inner_msg.get("text")
        
        if user_msg_text:
            user_msg_text = str(user_msg_text).strip()
            
        # Detect if the incoming message is a greeting to clean the session
        is_greeting = False
        if user_msg_text:
            text_lower = user_msg_text.lower().strip()
            greetings = ["hola", "buenos dias", "buenos días", "buenas tardes", "buenas noches", "hello", "hi", "buen dia", "buen día"]
            if text_lower in greetings:
                is_greeting = True

        # Recursively find image/pdf URL in the payload
        def find_image_url(obj) -> Optional[str]:
            if isinstance(obj, dict):
                url = obj.get("url")
                mime_type = str(obj.get("mimeType") or obj.get("mime_type") or "")
                attachment_type = str(obj.get("type") or "")
                if url and isinstance(url, str) and ("http" in url):
                    is_image = "image" in mime_type.lower() or "image" in attachment_type.lower() or any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"])
                    is_pdf = "pdf" in mime_type.lower() or "pdf" in attachment_type.lower() or url.lower().endswith(".pdf")
                    if is_image or is_pdf:
                        return url
                for v in obj.values():
                    res = find_image_url(v)
                    if res: return res
            elif isinstance(obj, list):
                for item in obj:
                    res = find_image_url(item)
                    if res: return res
            return None

        image_url = find_image_url(request)
                
        # Redis operations for global webhook caching & cleanup
        try:
            redis = await get_redis_client()
            
            # 1. Clean stale variables if a new greeting is received
            if is_greeting:
                logger.info(f"🧹 Clearing stale Redis variables for contact {contact_id} due to greeting")
                await redis.delete(f"contact:session_text:{contact_id}")
                await redis.delete(f"contact:last_image:{contact_id}")
                await redis.delete(f"status_attempts:{contact_id}")
                await redis.delete(f"name_attempts:{contact_id}")
                
            # 2. Append new message text to session text
            if user_msg_text:
                session_text_key = f"contact:session_text:{contact_id}"
                existing_bytes = await redis.get(session_text_key)
                existing_text = existing_bytes.decode('utf-8') if existing_bytes else ""
                new_text = f"{existing_text}\n{user_msg_text}".strip()
                await redis.set(session_text_key, new_text, ex=7200)  # 2 hours TTL
                logger.info(f"💾 [GLOBAL CACHE] Saved session text for contact {contact_id}: {user_msg_text}")
                
            # 3. Cache image/pdf URL if present
            if image_url:
                cache_key = f"contact:last_image:{contact_id}"
                await redis.set(cache_key, image_url, ex=3600)
                logger.info(f"💾 [GLOBAL CACHE] Saved last image URL for contact {contact_id}: {image_url}")
                
            # 4. Structured chat history caching for Client and Human Agent
            conversation_obj = request.get("conversation") or {}
            conversation_id = ""
            if isinstance(conversation_obj, dict):
                conversation_id = str(conversation_obj.get("id") or "")
            if not conversation_id:
                conversation_id = str(request.get("conversationId") or "")
                
            if conversation_id and user_msg_text:
                direction = ""
                sender_type = ""
                user_obj = None
                user_name = "Asesor Humano"
                
                message_obj = request.get("message") or {}
                if isinstance(message_obj, dict):
                    direction = str(message_obj.get("direction") or "")
                    sender_obj = message_obj.get("sender") or {}
                    if isinstance(sender_obj, dict):
                        sender_type = str(sender_obj.get("type") or "")
                    user_obj = message_obj.get("user")
                    if isinstance(user_obj, dict):
                        user_name = str(user_obj.get("name") or "Asesor Humano")
                        
                from .chat_history_helper import append_message_to_history
                if direction == "incoming":
                    await append_message_to_history(redis, conversation_id, "client", user_msg_text)
                elif direction == "outgoing":
                    if user_obj or sender_type in ["user", "agent"]:
                        await append_message_to_history(
                            redis, conversation_id, "agent_human", user_msg_text, agent_name=user_name
                        )
                
        except Exception as re_err:
            logger.warning(f"Failed to process Redis operations in global webhook: {re_err}")
                
        return RespondioResponse(
            status=ResponseStatus.OK,
            reply_text="",
            trace_id=trace_id,
            latency_ms=0
        )

    # If not global webhook, parse as standard RespondioRequest
    try:
        from .models import RespondioRequest
        request = RespondioRequest(**request)
    except Exception as parse_err:
        logger.error(f"Failed to parse custom webhook request: {parse_err}")
        raise HTTPException(status_code=422, detail=f"Validation error: {parse_err}")

    logger.info(
        f"📨 Webhook received",
        extra={
            "trace_id": trace_id,
            "conversation_id": request.conversation_id,
            "channel": request.channel
        }
    )

    # --- ENHANCEMENT: Extract Respond.io Attachments if root media is empty ---
    # Usually Respond.io sends message.attachments[].url/mimeType
    if not request.media and request.metadata.get("message", {}).get("attachments"):
        from .models import MediaItem
        attachments = request.metadata["message"]["attachments"]
        for att in attachments:
            if "url" in att and "mimeType" in att:
                request.media.append(MediaItem(
                    mime_type=att["mimeType"],
                    url=att["url"],
                    file_name=att.get("fileName")
                ))
        if request.media:
            logger.info(f"📎 Extracted {len(request.media)} attachments from Respond.io metadata")

    # Cache the last image or document (PDF) URL in Redis for this contact (valid for 1 hour)
    if request.media:
        for item in request.media:
            mime_lower = (item.mime_type or "").lower()
            url_lower = (item.url or "").lower()
            is_img = "image" in mime_lower
            is_pdf = "pdf" in mime_lower or url_lower.endswith(".pdf")
            if (is_img or is_pdf) and item.url:
                try:
                    redis = await get_redis_client()
                    cache_key = f"contact:last_image:{request.contact_id}"
                    await redis.set(cache_key, item.url, ex=3600)
                    logger.info(f"💾 [CACHE] Saved last media (image/pdf) URL for contact {request.contact_id}: {item.url}")
                    break
                except Exception as re_err:
                    logger.warning(f"Failed to cache last media in Redis: {re_err}")
    
    # --- PHASE 28: COMPLIANCE INITIAL DISCLOSURE ---
    needs_disclosure = False
    disclosure_text = ""
    try:
        redis = await get_redis_client()
        # Key to track if disclosure was sent to this contact today
        disclosure_key = f"compliance:disclosure:sent:{request.contact_id}"
        already_sent = await redis.get(disclosure_key)
        
        if not already_sent:
            needs_disclosure = True
            scripts = get_compliance_scripts()
            disclosure_text = scripts.get("A1_INITIAL_DISCLOSURE", "")
            # Mark as sent for 24 hours
            await redis.set(disclosure_key, "true", ex=86400)
            logger.info(f"🛡️ Initial Disclosure will be prepended for contact {request.contact_id}")
    except Exception as e:
        logger.error(f"Failed to check/set disclosure in Redis: {str(e)}")

    try:
        # --- INTERCEPT IMAGES FOR HADES CLOUD FORENSIC ANALYSIS ---
        image_media = None
        if request.media:
            for media in request.media:
                if "image" in (media.mime_type or "").lower():
                    user_msg = (request.user_text or "").lower()
                    keywords = ["analiza", "hades", "cedula", "pasaporte", "ine", "id", "verificar", "autenticidad"]
                    if not request.user_text or any(k in user_msg for k in keywords):
                        image_media = media
                        break

        if image_media:
            logger.info(f"📸 Interceptando imagen de Respond.io para HADES: {image_media.url}")
            try:
                async with httpx.AsyncClient() as client:
                    img_resp = await client.get(image_media.url, timeout=30)
                    if img_resp.status_code == 200:
                        from .hades_engine import hades_engine
                        hades_report = await hades_engine.analyze_document_image(img_resp.content, image_media.mime_type)
                        if hades_report.get("success"):
                            score = hades_report["score"]
                            riesgo = hades_report["riesgo"]
                            emoji = hades_report["emoji"]
                            data = hades_report["data"]
                            forensic = hades_report["forensic_details"]
                            details_user = hades_report["details_user"]
                            
                            mcp_response = (
                                f"🛡️ *INFORME DE CUMPLIMIENTO Y ANÁLISIS FORENSE (HADES CLOUD)*\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"📊 *Resultado de Autenticidad:* {emoji} *{riesgo}* (Score: `{score}/100`)\n"
                                f"👤 *Titular:* `{data['nombre']}`\n"
                                f"🆔 *Documento:* `{data['tipo']}` | ID: `{data['id']}`\n"
                                f"🌎 *País Emisor:* `{data['pais']}`\n"
                                f"📅 *Nacimiento:* `{data['nacimiento']}` | *Vigencia:* `{data['expiracion']}`\n"
                                f"⚖️ *Estatus de Compliance:* `{data['compliance_status']}`\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"🔍 *Detalles Forenses Visuales:*\n"
                            )
                            
                            if forensic.get("photoshop_detected"):
                                mcp_response += f"🚨 *MANIPULACIÓN DIGITAL:* Se detectó posible fotomontaje o edición digital.\n"
                            
                            scores = forensic.get("scores", {})
                            mcp_response += (
                                f"- 🛡️ Elementos de Seguridad: `{scores.get('security_elements', 0)}/10`\n"
                                f"- 🖨️ Calidad de Impresión: `{scores.get('printing_quality', 0)}/10`\n"
                                f"- 💻 Manipulación Digital: `{scores.get('digital_manipulation', 0)}/10`\n"
                                f"- 🔤 Tipografía: `{scores.get('typography', 0)}/10`\n"
                                f"- 📸 Fotografía: `{scores.get('photography', 0)}/10`\n"
                            )
                            
                            if forensic.get("evidences"):
                                mcp_response += "\n*Evidencias Encontradas:*\n"
                                for ev in forensic["evidences"][:3]:
                                    mcp_response += f"• _{ev}_\n"
                            
                            if details_user:
                                mcp_response += "\n*Observaciones de Operación:*\n"
                                for obs in details_user:
                                    mcp_response += f"⚠️ _{obs}_\n"
                                    
                            mcp_response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n_Análisis completado en {hades_report.get('latency_sec', 0):.2f}s_"
                            
                            total_latency_ms = int((time.time() - start_time) * 1000)
                            
                            try:
                                request_log = RequestLog(
                                    trace_id=trace_id,
                                    timestamp=datetime.utcnow(),
                                    conversation_id=request.conversation_id,
                                    contact_id=request.contact_id,
                                    channel=request.channel,
                                    user_text=request.user_text,
                                    mcp_response=mcp_response,
                                    status=ResponseStatus.OK,
                                    latency_ms=total_latency_ms,
                                    retry_count=0,
                                    category=determine_request_category(request.user_text, mcp_response)
                                )
                                await telemetry_service.log_request(request_log)
                            except Exception as tel_err:
                                logger.error(f"Failed to log Hades telemetry: {tel_err}")
                                
                            return RespondioResponse(
                                status=ResponseStatus.OK,
                                reply_text=mcp_response,
                                trace_id=trace_id,
                                latency_ms=total_latency_ms
                            )
                        else:
                            logger.error(f"HadesEngine failed: {hades_report.get('error')}")
            except Exception as download_err:
                logger.error(f"Failed downloading image for Hades: {download_err}")

        # --- INTERCEPT GREETINGS TO RETURN CU.A1 DIRECTLY ---
        user_msg_text = (request.user_text or "").strip()
        text_lower = user_msg_text.lower().strip(".,!?¡¿")
        greetings = ["hola", "buenos dias", "buenos días", "buenas tardes", "buenas noches", "hello", "hi", "buen dia", "buen día"]
        if text_lower in greetings:
            logger.info("👋 Greeting detected in custom webhook request. Returning CU.A1 welcome script directly.")
            scripts = get_compliance_scripts()
            mcp_response = scripts.get("CU.A1", "")
            
            # --- AUTO TRANSLATE RESPONSE IF CUSTOMER SPOKE ANOTHER LANGUAGE ---
            if mcp_response:
                mcp_response = await translate_script_if_needed(mcp_response, request.user_text)
                
            total_latency_ms = int((time.time() - start_time) * 1000)
            
            # Log telemetry
            try:
                request_log = RequestLog(
                    trace_id=trace_id,
                    timestamp=datetime.utcnow(),
                    conversation_id=request.conversation_id,
                    contact_id=request.contact_id,
                    channel=f"respond_consulta ({request.channel})",
                    user_text=request.user_text,
                    mcp_response=mcp_response,
                    status=ResponseStatus.OK,
                    latency_ms=total_latency_ms,
                    mcp_latency_ms=0,
                    error_message=None,
                    retry_count=0,
                    category=determine_request_category(request.user_text, mcp_response)
                )
                await telemetry_service.log_request(request_log)
            except Exception as tel_err:
                logger.error(f"Failed to log greeting telemetry: {tel_err}")

            # Structured chat history caching
            try:
                redis = await get_redis_client()
                from .chat_history_helper import append_message_to_history
                await append_message_to_history(redis, request.conversation_id, "bot_max", mcp_response)
            except Exception as hist_err:
                logger.warning(f"Failed to cache greeting in chat history: {hist_err}")

            return RespondioResponse(
                status=ResponseStatus.OK,
                reply_text=mcp_response,
                trace_id=trace_id,
                latency_ms=total_latency_ms
            )

        # Check if an agent is specified in metadata (useful for dashboard testing)
        agent_name = request.metadata.get("agent_name")
        
        # If no agent specified, fall back to Orchestrator
        if not agent_name:
            from .config_manager import config_manager
            orchestrator = await config_manager.get_orchestrator()
            agent_name = orchestrator.name if orchestrator else None
            
            if agent_name:
                logger.info(f"Routing request through orchestrator: {agent_name}")
        else:
            logger.info(f"Routing request through specified agent: {agent_name}")
        
        # Call MCP
        mcp_response, status, mcp_latency_ms, retry_count = await mcp_client.query(
            user_text=request.user_text,
            context={
                "conversation_id": request.conversation_id,
                "contact_id": request.contact_id,
                "channel": request.channel,
                "media": request.media,
                **request.metadata
            },
            agent_name=agent_name
        )
        
        # --- Handoff Protocol Integration ---
        import re
        handoff_match = re.search(r"\[TRANSFER:\s*(\w+)\]", mcp_response or "")
        
        if handoff_match and status == ResponseStatus.OK:
            new_agent_name = handoff_match.group(1)
            logger.info(f"🔄 Handoff detected: Transferring to {new_agent_name}")
            
            # recursive call with the new agent
            # We strip the transfer command from the response if we were to return it, 
            # but here we actually re-query the new agent.
            mcp_response, status, second_latency, second_retry = await mcp_client.query(
                user_text=request.user_text,
                context={
                    "conversation_id": request.conversation_id,
                    "contact_id": request.contact_id,
                    "channel": request.channel,
                    "handoff_from": agent_name,
                    **request.metadata
                },
                agent_name=new_agent_name
            )
            mcp_latency_ms += second_latency
            retry_count += second_retry
            logger.info(f"✅ Handoff to {new_agent_name} completed")
        
        # --- COMPLIANCE: PREPEND DISCLOSURE IF NEEDED ---
        if needs_disclosure and disclosure_text and mcp_response:
            mcp_response = f"{disclosure_text}\n\n---\n\n{mcp_response}"
            logger.debug("Disclosure prepended to final response")

        # --- AUTO TRANSLATE RESPONSE IF CUSTOMER SPOKE ANOTHER LANGUAGE ---
        if mcp_response and request.user_text:
            mcp_response = await translate_script_if_needed(mcp_response, request.user_text)

        # Calculate total latency
        total_latency_ms = int((time.time() - start_time) * 1000)
        
        # Log telemetry
        request_log = RequestLog(
            trace_id=trace_id,
            timestamp=datetime.utcnow(),
            conversation_id=request.conversation_id,
            contact_id=request.contact_id,
            channel=f"respond_consulta ({request.channel})",
            user_text=request.user_text,
            mcp_response=mcp_response,
            status=status,
            latency_ms=total_latency_ms,
            mcp_latency_ms=mcp_latency_ms,
            error_message=None if status != ResponseStatus.ERROR else "MCP error",
            retry_count=retry_count,
            category=determine_request_category(request.user_text, mcp_response)
        )
        
        await telemetry_service.log_request(request_log)
        
        logger.info(
            f"✅ Webhook processed",
            extra={
                "trace_id": trace_id,
                "status": status,
                "latency_ms": total_latency_ms,
                "mcp_latency_ms": mcp_latency_ms,
                "retry_count": retry_count
            }
        )
        
        # Structured chat history caching for Bot Max and Specialized Agent
        try:
            if request.conversation_id and mcp_response:
                redis_client = await get_redis_client()
                from .chat_history_helper import append_message_to_history
                role_type = "bot_max"
                if agent_name and agent_name not in ["Max", "Orquestador"]:
                    role_type = "agent_specialized"
                await append_message_to_history(
                    redis_client, request.conversation_id, role_type, mcp_response, agent_name=agent_name
                )
        except Exception as cache_err:
            logger.warning(f"Failed to append bot message to chat history: {cache_err}")

        # Return response
        return RespondioResponse(
            status=status,
            reply_text=mcp_response,
            trace_id=trace_id,
            latency_ms=total_latency_ms
        )
    
    except Exception as e:
        # Handle unexpected errors
        total_latency_ms = int((time.time() - start_time) * 1000)
        
        logger.error(
            f"💥 Unexpected error",
            extra={
                "trace_id": trace_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        # Log error telemetry
        request_log = RequestLog(
            trace_id=trace_id,
            timestamp=datetime.utcnow(),
            conversation_id=request.conversation_id,
            contact_id=request.contact_id,
            channel=f"respond_consulta ({request.channel})",
            user_text=request.user_text,
            mcp_response=None,
            status=ResponseStatus.ERROR,
            latency_ms=total_latency_ms,
            mcp_latency_ms=None,
            error_message=str(e),
            retry_count=0
        )
        
        await telemetry_service.log_request(request_log)
        
        # Return error response with fallback message
        return RespondioResponse(
            status=ResponseStatus.ERROR,
            reply_text="Lo siento, ocurrió un error inesperado. Por favor intenta nuevamente.",
            trace_id=trace_id,
            latency_ms=total_latency_ms
        )


# ============================================================
# Helpers for Status Check and Routing (Plan 3)
# ============================================================

def get_central_time() -> datetime:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Chicago"))
    except Exception:
        try:
            from zoneinfo import ZoneInfo
            return datetime.now(ZoneInfo("America/Mexico_City"))
        except Exception:
            return datetime.now(timezone.utc) - timedelta(hours=5)


def is_within_hours(dt: datetime, start_h: int, start_m: int, end_h: int, end_m: int, days: list = None) -> bool:
    if days is not None and dt.weekday() not in days:
        return False
    current_time_minutes = dt.hour * 60 + dt.minute
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    return start_minutes <= current_time_minutes <= end_minutes


def check_department_hours(depto: str, dt: datetime) -> bool:
    depto = depto.upper()
    if "CUMPLIMIENTO" in depto:
        # Lun-Dom: 08:00 a 23:00 hrs
        return is_within_hours(dt, 8, 0, 23, 0)
    elif "COBRANZA" in depto:
        # Lun-Vie: 08:00 a 23:00, Sab: 08:00 a 22:00, Dom: 09:00 a 21:00
        w = dt.weekday()
        if w in range(0, 5):
            return is_within_hours(dt, 8, 0, 23, 0)
        elif w == 5:
            return is_within_hours(dt, 8, 0, 22, 0)
        else:
            return is_within_hours(dt, 9, 0, 21, 0)
    elif "OVERSIGHT" in depto:
        # Lun-Vie: 08:00 a 19:00, Sab: 08:00 a 18:00
        w = dt.weekday()
        if w in range(0, 5):
            return is_within_hours(dt, 8, 0, 19, 0)
        elif w == 5:
            return is_within_hours(dt, 8, 0, 18, 0)
        return False
    elif "CAPACITACION" in depto:
        # Lun-Vie: 08:00 a 21:00
        return is_within_hours(dt, 8, 0, 21, 0, days=list(range(0, 5)))
    elif "CHEQUES" in depto:
        # Lun-Vie: 09:00 a 23:00, Sab: 09:00 a 22:00, Dom: 10:00 a 19:00
        w = dt.weekday()
        if w in range(0, 5):
            return is_within_hours(dt, 9, 0, 23, 0)
        elif w == 5:
            return is_within_hours(dt, 9, 0, 22, 0)
        else:
            return is_within_hours(dt, 10, 0, 19, 0)
    elif "TECNICO" in depto:
        # Lun-Dom: 07:00 a 23:00
        return is_within_hours(dt, 7, 0, 23, 0)
    elif "VENTAS" in depto:
        # Lun-Vie: 07:00 a 20:00, Sab: 07:00 a 18:00, Dom: 07:00 a 16:00
        w = dt.weekday()
        if w in range(0, 5):
            return is_within_hours(dt, 7, 0, 20, 0)
        elif w == 5:
            return is_within_hours(dt, 7, 0, 18, 0)
        else:
            return is_within_hours(dt, 7, 0, 16, 0)
    elif "SERVICIO AL CLIENTE" in depto or "SC" in depto:
        # Lun-Vie: 09:00 a 21:00, Sab-Dom: 09:00 a 19:00
        w = dt.weekday()
        if w in range(0, 5):
            return is_within_hours(dt, 9, 0, 21, 0)
        else:
            return is_within_hours(dt, 9, 0, 19, 0)
    elif "FRAUD" in depto or "PREVENCION DE FRAUDES" in depto:
        # Lun-Dom: 08:00 a 23:00
        return is_within_hours(dt, 8, 0, 23, 0)
    elif "BSA" in depto:
        # Lun-Vie: 08:00 a 19:00, Sab: 08:00 a 18:00
        w = dt.weekday()
        if w in range(0, 5):
            return is_within_hours(dt, 8, 0, 19, 0)
        elif w == 5:
            return is_within_hours(dt, 8, 0, 18, 0)
        return False
    return True


def extraer_codigo_router(texto: str) -> Optional[str]:
    texto_limpio = re.sub(r'https?://\S+', '', texto)
    patrones = [
        r'\bCE\d{8,}\b',
        r'\bTRK\d{6,}\b',
        r'\b[A-Z]{2}\d{8,}\b',
        r'\b[A-Z0-9]{8,}\b'
    ]
    for patron in patrones:
        m = re.search(patron, texto_limpio.upper())
        if m:
            code = m.group()
            if code.isalpha():
                continue
            return code
    return None


def match_names(user_name: str, db_name: str) -> bool:
    if not user_name or not db_name:
        return False
    user_words = set(re.findall(r'\w+', user_name.lower()))
    db_words = set(re.findall(r'\w+', db_name.lower()))
    intersection = user_words.intersection(db_words)
    return len(intersection) >= 1


def match_biller(user_biller: str, db_biller: str) -> bool:
    if not user_biller or not db_biller:
        return False
    generic_words = {
        "power", "electric", "service", "services", "gas", "water", "utility", 
        "utilities", "internet", "phone", "tv", "cable", "energy", "trash", 
        "waste", "management", "co", "company", "inc", "corp", "payment", 
        "payments", "bill", "bills", "system", "systems", "mobile"
    }
    user_words = set(w for w in re.findall(r'\w+', user_biller.lower()) if w not in generic_words)
    db_words = set(w for w in re.findall(r'\w+', db_biller.lower()) if w not in generic_words)
    
    if not user_words or not db_words:
        user_words = set(re.findall(r'\w+', user_biller.lower()))
        db_words = set(re.findall(r'\w+', db_biller.lower()))
        
    intersection = user_words.intersection(db_words)
    return len(intersection) >= 1


def match_customer_name(user_name: str, db_first: str, db_paterno: str, db_materno: str) -> bool:
    if not user_name:
        return False
    user_words = set(re.findall(r'\w+', user_name.lower()))
    
    first_words = set(re.findall(r'\w+', (db_first or "").lower()))
    surname_words = set(re.findall(r'\w+', f"{db_paterno or ''} {db_materno or ''}".lower()))
    
    if first_words and surname_words:
        has_first_match = len(user_words.intersection(first_words)) >= 1
        has_surname_match = len(user_words.intersection(surname_words)) >= 1
        return has_first_match and has_surname_match
    else:
        all_db_words = first_words.union(surname_words)
        return len(user_words.intersection(all_db_words)) >= 1




def append_courtesy_sc33(reply_text: str, contact_name: str = None) -> str:
    from .shared_logic import get_compliance_scripts
    scripts = get_compliance_scripts()
    sc33_template = scripts.get("SC.033", "[Nombre] ¿Hay algo más en lo que le pueda ayudar?.")
    clean_name = contact_name or "Cliente"
    sc33_text = sc33_template.replace("[Nombre]", clean_name).replace("“", "").replace("”", "").replace('"', "")
    return f"{reply_text}\n\n{sc33_text}"

@app.post("/api/v1/status/check", response_model=StatusCheckResponse)
async def check_transaction_status(
    request: StatusCheckRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    start_time = time.time()
    status_val = ResponseStatus.OK
    error_msg = None
    resp = None
    try:
        resp = await check_transaction_status_inner(request, x_webhook_secret, secret)
        return resp
    except Exception as e:
        status_val = ResponseStatus.ERROR
        error_msg = str(e)
        raise e
    finally:
        try:
            latency = int((time.time() - start_time) * 1000)
            request_log = RequestLog(
                trace_id=f"api-{uuid.uuid4()}",
                timestamp=datetime.utcnow(),
                conversation_id=request.contact_id or "unknown",
                contact_id=request.codigo_envio or "unknown",
                channel="respond_api",
                user_text=f"Status Check: {request.codigo_envio or ''}",
                mcp_response=resp.reply_text if resp else error_msg,
                status=status_val,
                latency_ms=latency,
                category="status_check"
            )
            await telemetry_service.log_request(request_log)
        except Exception as log_err:
            logger.error(f"Error logging status check telemetry: {log_err}")

async def check_transaction_status_inner(
    request: StatusCheckRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    """
    Endpoint for deterministic status checking and routing (Plan 3).
    Validates webhook secret, checks attempt limits in Redis, queries Supabase,
    and applies compliance / business rules for department routing.
    """
    # Validate secret
    incoming_secret = x_webhook_secret or secret
    if incoming_secret != settings.WEBHOOK_SECRET:
        logger.warning("❌ Invalid webhook secret in status check")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
    logger.info(f"📥 Received status check request: {request.dict()}")

    def sanitize_input(v: Any) -> Optional[str]:
        if v is None:
            return None
        v_str = str(v).strip().strip(",").strip()
        if (v_str in [",", "%", "", "null", "None"] or 
            v_str.startswith("$") or 
            "{{" in v_str or 
            "}}" in v_str):
            return None
        return v_str

    user_text = sanitize_input(request.user_text) or ""
    contact_id = sanitize_input(request.contact_id) or "-1"
    contact_name = sanitize_input(request.contact_name)
    
    metadata = request.metadata or {}
    codigo_envio = sanitize_input(request.codigo_envio) or sanitize_input(metadata.get("codigo_envio"))
    perfil = sanitize_input(request.perfil) or sanitize_input(metadata.get("perfil")) or sanitize_input(metadata.get("perfil_usuario"))
    
    if perfil:
        perfil = perfil.upper()
    else:
        perfil = "CLIENTE"
        
    # Get Redis client early
    redis = None
    try:
        redis = await get_redis_client()
    except Exception as redis_err:
        logger.warning(f"Redis connection not available for status check: {redis_err}")

    # Check for variable freshness using Redis session text
    if redis and contact_id != "-1":
        try:
            session_text_bytes = await redis.get(f"contact:session_text:{contact_id}")
            if session_text_bytes is not None:
                session_text = session_text_bytes.decode('utf-8')
                
                # 1. Validate code freshness
                code_fresh = False
                if codigo_envio:
                    clean_code = re.sub(r'[^A-Z0-9]', '', codigo_envio.upper())
                    clean_session = re.sub(r'[^A-Z0-9]', '', session_text.upper())
                    clean_user_text = re.sub(r'[^A-Z0-9]', '', user_text.upper())
                    if clean_code in clean_session or clean_code in clean_user_text:
                        code_fresh = True
                        
                # Check for receipt image in the session
                if not code_fresh:
                    img_cached = await redis.get(f"contact:last_image:{contact_id}")
                    if img_cached:
                        code_fresh = True
                        
                if codigo_envio and not code_fresh:
                    logger.info(f"🚫 Ignoring old/historical code {codigo_envio} for contact {contact_id}")
                    codigo_envio = None
        except Exception as e:
            logger.error(f"Error checking session text freshness in Redis: {e}")

    # Clean and validate the provided transaction code format
    is_valid_code = False
    if codigo_envio:
        codigo_str = str(codigo_envio).strip().upper()
        # A valid code must match one of our expected patterns and not be a wildcard or variable placeholder
        if not codigo_str.startswith("$") and codigo_str != "%" and len(codigo_str) >= 6:
            patrones = [
                r'^CE\d{8,}$',
                r'^TRK\d{6,}$',
                r'^[A-Z]{2}\d{8,}$',
                r'^[A-Z0-9]{8,}$'
            ]
            for patron in patrones:
                if re.match(patron, codigo_str):
                    if not codigo_str.isalpha(): # Ensure it's not purely alphabetic
                        codigo_envio = codigo_str
                        is_valid_code = True
                        break

    if not is_valid_code:
        codigo_envio = extraer_codigo_router(user_text)
        
    # Attempt counter key in Redis
    attempts_key = f"status_attempts:{contact_id}"
    attempts = 0
    if redis:
        try:
            attempts_val = await redis.get(attempts_key)
            attempts = int(attempts_val.decode('utf-8')) if attempts_val else 0
        except Exception as e:
            logger.error(f"Error reading status attempts from Redis: {e}")
            
    if not codigo_envio:
        attempts += 1
        if redis:
            try:
                await redis.set(attempts_key, str(attempts), ex=3600)
            except Exception as e:
                logger.error(f"Error setting status attempts to Redis: {e}")
                
        if attempts >= 2:
            if redis:
                try:
                    await redis.set(attempts_key, "0", ex=3600)
                except Exception as e:
                    logger.error(f"Error resetting attempts in Redis: {e}")
            return StatusCheckResponse(
                status="success",
                reply_text="No fue posible procesar su solicitud con la clave proporcionada. Lo transferiré con uno de nuestros asesores. Por favor espere un momento...",
                derivacion="Servicio al Cliente",
                validation_success=False
            )
        else:
            return StatusCheckResponse(
                status="success",
                reply_text="No he podido localizar la información con los datos que me ha proporcionado. Por favor, confirmelos y escríbalos nuevamente.",
                derivacion="NA",
                validation_success=False
            )
            
    # Query database
    record = None
    table_type = None # "remesa" or "bill"
    
    # Try Supabase REST API first (fastest, IPv4/IPv6 compatible via HTTPS)
    try:
        supabase_url = os.getenv("SUPABASE_URL", "https://tzlomvpugmrpdfatscxe.supabase.co")
        supabase_anon_key = os.getenv(
            "SUPABASE_ANON_KEY",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6bG9tdnB1Z21ycGRmYXRzY3hlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3NjI3MjcsImV4cCI6MjA4OTMzODcyN30.aH-p2YbLa8LPlnMVsZMlELsxFWwSSLZMA_LPpRz5DU8"
        )
        headers = {
            "apikey": supabase_anon_key,
            "Authorization": f"Bearer {supabase_anon_key}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=4.0) as client:
            if codigo_envio.startswith("TRK"):
                url = f"{supabase_url}/rest/v1/Pago%20de%20Bill"
                params = {
                    "tracking_number": f"ilike.{codigo_envio}",
                    "select": "*",
                    "limit": "1"
                }
                res = await client.get(url, headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json()
                    if data:
                        record = data[0]
                        table_type = "bill"
            else:
                url = f"{supabase_url}/rest/v1/Base_completa"
                params = {
                    "Codigo_de_envio": f"ilike.{codigo_envio}",
                    "select": "*",
                    "limit": "1"
                }
                res = await client.get(url, headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json()
                    if data:
                        record = data[0]
                        table_type = "remesa"
        if record:
            logger.info(f"✅ Record found via REST API for code {codigo_envio}")
    except Exception as rest_err:
        logger.warning(f"Supabase REST API fast query failed: {rest_err}")

    # Fallback to PostgreSQL if REST API didn't return a record
    if not record and settings.SUPABASE_URI:
        try:
            from .shared_logic import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if codigo_envio.startswith("TRK"):
                cursor.execute('SELECT * FROM "Pago de Bill" WHERE "tracking_number" = %s;', (codigo_envio,))
                row = cursor.fetchone()
                if row:
                    colnames = [desc[0] for desc in cursor.description]
                    record = dict(zip(colnames, row))
                    table_type = "bill"
            else:
                cursor.execute('SELECT * FROM "Base_completa" WHERE "Codigo_de_envio" = %s;', (codigo_envio,))
                row = cursor.fetchone()
                if row:
                    colnames = [desc[0] for desc in cursor.description]
                    record = dict(zip(colnames, row))
                    table_type = "remesa"
                    
            cursor.close()
            conn.close()
            logger.info(f"✅ Record found via PostgreSQL for code {codigo_envio}")
        except Exception as db_err:
            logger.warning(f"PostgreSQL fallback query failed: {db_err}")
            
    if not record:
        attempts += 1
        if redis:
            try:
                await redis.set(attempts_key, str(attempts), ex=3600)
            except Exception as e:
                logger.error(f"Error setting attempts in Redis: {e}")
                
        if attempts >= 2:
            if redis:
                try:
                    await redis.set(attempts_key, "0", ex=3600)
                except Exception as e:
                    logger.error(f"Error resetting attempts in Redis: {e}")
            return StatusCheckResponse(
                status="success",
                reply_text="No fue posible procesar su solicitud con la clave proporcionada. Lo transferiré con uno de nuestros asesores. Por favor espere un momento...",
                derivacion="Servicio al Cliente",
                validation_success=False
            )
        else:
            return StatusCheckResponse(
                status="success",
                reply_text="No he podido localizar la información con los datos que me ha proporcionado. Por favor, confirmelos y escríbalos nuevamente.",
                derivacion="NA",
                validation_success=False
            )
            
    # Reset attempts since code was successfully found
    if redis:
        try:
            await redis.set(attempts_key, "0", ex=3600)
        except Exception as e:
            logger.error(f"Error resetting code attempts in Redis: {e}")
            
    # Name Validation (only for remesas and client/beneficiary profiles)
    if table_type == "remesa" and perfil in ["CLIENTE", "BENEFICIARIO", "REMITENTE"]:
        def sanitize_name(v: Any) -> Optional[str]:
            if v is None:
                return None
            v_str = str(v).strip().strip(",").strip()
            if v_str in [",", "%", "", "null", "None"] or v_str.startswith("$"):
                return None
            return v_str
            
        user_sender = sanitize_name(request.nombre_remitente or metadata.get("nombre_remitente"))
        user_beneficiary = sanitize_name(request.nombre_beneficiario or metadata.get("nombre_beneficiario"))
        
        # Check freshness of names if session text exists in Redis
        if redis and contact_id != "-1":
            try:
                session_text_bytes = await redis.get(f"contact:session_text:{contact_id}")
                if session_text_bytes is not None:
                    session_text = session_text_bytes.decode('utf-8').upper()
                    clean_user_text = user_text.upper()
                    
                    def is_fresh(name_str: Optional[str]) -> bool:
                        if not name_str:
                            return False
                        words = [w for w in re.findall(r'\w+', name_str.upper()) if len(w) > 2]
                        if not words:
                            return False
                        return any(w in session_text or w in clean_user_text for w in words)
                        
                    if user_sender and not is_fresh(user_sender):
                        logger.info(f"🚫 Ignoring old/historical sender name {user_sender} for contact {contact_id}")
                        user_sender = None
                        
                    if user_beneficiary and not is_fresh(user_beneficiary):
                        logger.info(f"🚫 Ignoring old/historical beneficiary name {user_beneficiary} for contact {contact_id}")
                        user_beneficiary = None
            except Exception as e:
                logger.error(f"Error checking name freshness in Redis: {e}")

        # Fallback to user_text ONLY if BOTH are unresolved/missing
        if not user_sender and not user_beneficiary:
            user_sender = user_text
            user_beneficiary = user_text
            
        # Name columns handling database typos and spaces
        db_sender = f"{record.get('Nombre_Cliente', '')} {record.get('Cliente_ Apellido_Paterno', '')} {record.get('Cliente_Apellido_Materno', '')}".strip()
        db_beneficiary = f"{record.get('Beneficiario_Nombre', '')} {record.get('Benerificario_Primer_Apellido', '')} {record.get('Beneficiario_Segundo_Apellido', '')}".strip()
        
        db_sender = re.sub(r'\s+', ' ', db_sender)
        db_beneficiary = re.sub(r'\s+', ' ', db_beneficiary)
        
        if user_sender or user_beneficiary:
            sender_ok = True
            beneficiary_ok = True
            
            if user_sender:
                sender_ok = match_names(user_sender, db_sender)
            if user_beneficiary:
                beneficiary_ok = match_names(user_beneficiary, db_beneficiary)
                
            if not sender_ok or not beneficiary_ok:
                name_attempts_key = f"name_attempts:{contact_id}"
                name_attempts = 0
                if redis:
                    try:
                        name_attempts_val = await redis.get(name_attempts_key)
                        name_attempts = int(name_attempts_val.decode('utf-8')) if name_attempts_val else 0
                    except Exception as e:
                        logger.error(f"Error reading name attempts: {e}")
                        
                name_attempts += 1
                if redis:
                    try:
                        await redis.set(name_attempts_key, str(name_attempts), ex=3600)
                    except Exception as e:
                        logger.error(f"Error saving name attempts: {e}")
                        
                if name_attempts >= 2:
                    if redis:
                        try:
                            await redis.set(name_attempts_key, "0", ex=3600)
                        except Exception as e:
                            logger.error(f"Error resetting name attempts: {e}")
                    return StatusCheckResponse(
                        status="success",
                        reply_text="No fue posible validar su identidad con la información proporcionada. Lo transferiré con un asesor, para que reciba la asistencia necesaria.",
                        derivacion="Servicio al Cliente",
                        validation_success=False
                    )
                else:
                    return StatusCheckResponse(
                        status="success",
                        reply_text="Los nombres proporcionados no coinciden con nuestros registros por seguridad. Por favor verifíquelos y compártalos nuevamente.",
                        derivacion="NA",
                        validation_success=False
                    )
                    
    # Reset name attempts on success
    if redis:
        try:
            await redis.set(f"name_attempts:{contact_id}", "0", ex=3600)
        except Exception as e:
            logger.error(f"Error resetting name attempts: {e}")
            
    # 3. Rule Crossing (Matrix)
    status_db = record.get("status") or record.get("Estatus") or ""
    status_clean = status_db.strip()
    status_upper = status_clean.upper()
    
    derivacion = "NA"
    reply_text = ""
    
    ct_now = get_central_time()
    
    # Check for hardcoded critical exclusion first (RNE.57 / RNE.58)
    if status_upper in ["DETENIDO", "CONTACTAR AGENTE"]:
        if perfil == "BENEFICIARIO":
            reply_text = "Por seguridad, su solicitud debe ser atendida fuera de este canal. Por favor, solicite a la persona que le realizó el envío que acuda a la agencia donde realizó la operación. Gracias."
        else:
            reply_text = "Por seguridad, su solicitud debe ser atendida fuera de este canal. Por favor, acuda a la agencia donde realizó el envío para recibir la atención requerida. Muchas gracias."
        derivacion = "Exclusion"
        return StatusCheckResponse(
            status="success",
            reply_text=reply_text,
            derivacion=derivacion,
            validation_success=True,
            transaction_status=status_clean,
            client_profile=perfil
        )
        
    # Fetch status rules (from Google Sheets or local fallback)
    status_rules = None
    if settings.GOOGLE_SHEET_ID_ESTATUS:
        if redis:
            try:
                cached_val = await redis.get("google_sheets:status_cache")
                if cached_val:
                    status_rules = json.loads(cached_val.decode('utf-8'))
            except Exception as e:
                logger.error(f"Error reading status rules cache: {e}")
                
        if not status_rules:
            from .google_sheets_service import google_sheets_service
            status_rules = await google_sheets_service.fetch_status_rules(settings.GOOGLE_SHEET_ID_ESTATUS)
            if status_rules and redis:
                try:
                    await redis.setex("google_sheets:status_cache", 3600, json.dumps(status_rules))
                except Exception as e:
                    logger.error(f"Error caching status rules in Redis: {e}")
                    
    # Local fallback for development / test
    import sys
    if not status_rules and "pytest" not in sys.modules:
        local_excel = r"C:\Users\User\Downloads\ESTATUS ENVIOS.xlsx"
        if os.path.exists(local_excel):
            try:
                import pandas as pd
                df_local = pd.read_excel(local_excel, header=None)
                local_rows = []
                for _, r in df_local.iterrows():
                    local_rows.append([x if pd.notna(x) else "" for x in r])
                from .google_sheets_service import google_sheets_service
                status_rules = google_sheets_service._parse_status_rows(local_rows)
                logger.info(f"Loaded status rules from local fallback: {local_excel}")
            except Exception as exc:
                logger.warning(f"Failed to read local status rules fallback: {exc}")
                
    matched_rule = None
    if status_rules:
        type_key = "bill" if table_type == "bill" else "remesa"
        # Determine if it's recarga
        if metadata.get("tipo_transaccion") == "recarga" or "recarga" in user_text.lower():
            type_key = "recarga"
            
        rules_list = status_rules.get(type_key, [])
        perfil_upper = perfil.upper().strip()
        
        pagador_str = str(record.get("Transferencia_Pagador", "")).lower()
        payment_type = "cash"
        # Determine payment type from pagador name / record
        if "banco" in pagador_str or "cuenta" in pagador_str or "ahorro" in pagador_str:
            payment_type = "cuenta"
        elif "home" in pagador_str or "domicilio" in pagador_str:
            payment_type = "home delivery"
            
        def profile_matches(u_prof: str, r_prof: str) -> bool:
            if not r_prof:
                return True
            u_p = u_prof.upper().strip()
            r_p = r_prof.upper().strip()
            if "REMITE" in r_p or "AGENTE" in r_p or "BENEFICIARIO" in r_p:
                if u_p in ["CLIENTE", "REMITENTE", "AGENTE"]:
                    return "REMITE" in r_p or "AGENTE" in r_p
                elif u_p == "BENEFICIARIO":
                    return "BENEFICIARIO" in r_p
            return u_p == r_p

        for rule in rules_list:
            rule_estatus = rule["estatus"].lower().strip()
            rule_profile = rule["perfil"]
            
            if not profile_matches(perfil_upper, rule_profile):
                continue
                
            # Exact status match
            if status_upper.lower() == rule_estatus:
                matched_rule = rule
                break
                
            # Heuristics for Paid / Payment Ready / Stand by
            if "paid" in status_upper.lower() or "pagado" in status_upper.lower():
                if "paid" in rule_estatus:
                    if "home delivery" in rule_estatus and payment_type == "home delivery":
                        matched_rule = rule
                        break
                    elif "cuenta" in rule_estatus and payment_type == "cuenta":
                        matched_rule = rule
                        break
                    elif ("cash" in rule_estatus or "doméstico" in rule_estatus or "domestico" in rule_estatus) and payment_type == "cash":
                        matched_rule = rule
                        break
                    elif rule_estatus == "paid" or rule_estatus == "pagado":
                        matched_rule = rule
                        break
                        
            if "stand by" in status_upper.lower() or "payment ready" in status_upper.lower():
                is_guayaquil = "guayaquil" in pagador_str
                if is_guayaquil and "guayaquil" in rule_estatus:
                    status_type_matches = ("stand by" in status_upper.lower() and "stand by" in rule_estatus) or \
                                           ("payment ready" in status_upper.lower() and "payment ready" in rule_estatus)
                    if status_type_matches:
                        if "home delivery" in rule_estatus and payment_type == "home delivery":
                            matched_rule = rule
                            break
                        elif "cuenta" in rule_estatus and payment_type == "cuenta":
                            matched_rule = rule
                            break
                        elif ("cash" in rule_estatus or "doméstico" in rule_estatus or "domestico" in rule_estatus) and payment_type == "cash":
                            matched_rule = rule
                            break
                elif not is_guayaquil:
                    if "stand by" in status_upper.lower() and "excepto" in rule_estatus:
                        matched_rule = rule
                        break
                    elif "payment ready" in status_upper.lower() and "payment ready" in rule_estatus and "guayaquil" not in rule_estatus:
                        if "home delivery" in rule_estatus and payment_type == "home delivery":
                            matched_rule = rule
                            break
                        elif "cuenta" in rule_estatus and payment_type == "cuenta":
                            matched_rule = rule
                            break
                        elif ("cash" in rule_estatus or "doméstico" in rule_estatus or "domestico" in rule_estatus) and payment_type == "cash":
                            matched_rule = rule
                            break
                        elif rule_estatus == "payment ready" or rule_estatus == "payment ready ":
                            matched_rule = rule
                            break
                        
            # Substring match (e.g. "verify hold (o)")
            if rule_estatus in status_upper.lower() or status_upper.lower() in rule_estatus:
                if ("kyc" in rule_estatus) == ("kyc" in status_upper.lower()):
                    matched_rule = rule
                    break

    if matched_rule:
        deriv_raw = matched_rule["derivacion"].strip()
        script_text = resolve_script_text(matched_rule["script"])
        
        # Clean script text (replace quotes and name placeholder)
        clean_name = contact_name or "Cliente"
        script_text = script_text.replace("“", "").replace("”", "").replace('"', "")
        script_text = script_text.replace("Sr./Srita._________", clean_name).replace("Sr./Srita.____", clean_name)
        reply_text = script_text
        
        # Normalize derivation output and check operating hours
        if "CUMPLIMIENTO" in deriv_raw.upper():
            if check_department_hours("CUMPLIMIENTO", ct_now):
                derivacion = "Cumplimiento"
            else:
                derivacion = "Fuera de Horario Depto"
                reply_text = (
                    f"{reply_text}\n\n"
                    "Entiendo su solicitud. Su caso requiere atención de un área especializada (Cumplimiento) y por el momento no se encuentra disponible. "
                    "Se notificó sobre su caso y se comunicarán con usted en cuanto reinicien operaciones. Gracias por su paciencia."
                )
        elif "FRAUDE" in deriv_raw.upper():
            if check_department_hours("PREVENCION DE FRAUDES", ct_now):
                derivacion = "Fraudes"
            else:
                if check_department_hours("SERVICIO AL CLIENTE", ct_now):
                    derivacion = "Servicio al Cliente"
                    reply_text = (
                        f"{reply_text}\n\n"
                        "Entiendo la situación. Su solicitud es de alta prioridad para nosotros, lo comunicaré inmediatamente con un asesor de "
                        "Servicio al Cliente para darle atención urgente."
                    )
                else:
                    derivacion = "Fuera de Horario SC"
                    reply_text = (
                        f"{reply_text}\n\n"
                        "En este momento nuestros asesores no se encuentran disponibles. Un asesor dará seguimiento a su solicitud en cuanto "
                        "retomemos el servicio. Gracias por su paciencia."
                    )
        elif "SERVICIO AL CLIENTE" in deriv_raw.upper() or "SERVICIO A CLIENTE" in deriv_raw.upper() or "CERRAR-SERVICIO AL CLIENTE" in deriv_raw.upper():
            if check_department_hours("SERVICIO AL CLIENTE", ct_now):
                derivacion = "cerrar-Servicio al Cliente" if "CERRAR" in deriv_raw.upper() else "Servicio al Cliente"
            else:
                derivacion = "Fuera de Horario SC"
                reply_text = (
                    f"{reply_text}\n\n"
                    "En este momento nuestros asesores no se encuentran disponibles. Un asesor dará seguimiento a su solicitud en cuanto "
                    "retomemos el servicio. Gracias por su paciencia."
                )
        else:
            # Default is NA / none
            derivacion = "NA"
    else:
        # Fallback to standard hardcoded logic if no sheet rule is found
        logger.warning(f"No status rule found for status={status_clean}, perfil={perfil}, pagador={record.get('Transferencia_Pagador')}")
        if table_type == "remesa":
            # Exclusion (RNE.57 / RNE.58)
            if status_upper in ["DETENIDO", "CONTACTAR AGENTE"]:
                if perfil == "BENEFICIARIO":
                    reply_text = "Por seguridad, su solicitud debe ser atendida fuera de este canal. Por favor, solicite a la persona que le realizó el envío que acuda a la agencia donde realizó la operación. Gracias."
                else:
                    reply_text = "Por seguridad, su solicitud debe ser atendida fuera de este canal. Por favor, acuda a la agencia donde realizó el envío para recibir la atención requerida. Muchas gracias."
                derivacion = "Exclusion"
                
                return StatusCheckResponse(
                    status="success",
                    reply_text=reply_text,
                    derivacion=derivacion,
                    validation_success=True,
                    transaction_status=status_clean,
                    client_profile=perfil
                )
                
            if perfil == "BENEFICIARIO":
                transitorios_beneficiary = [
                    "CANCEL STAND BY", "CANCEL IN PROCESS", "CANCEL ACCEPTED", "STAND BY", 
                    "PENDING GATEWAY RESPONSE", "TRANSFER ACCEPTED", "VERIFY HOLD (S)", 
                    "VERIFY HOLD (DP)", "UPDATE IN PROGRESS", "ORIGIN/PENDING PAYMENT", 
                    "RETURNED", "UNCLAIMED HOLD"
                ]
                
                is_guayaquil_cash = (status_upper == "STAND BY") and (record.get("Transferencia_Pagador") == "Banco de Guayaquil")
                
                if status_upper in transitorios_beneficiary and not is_guayaquil_cash:
                    reply_text = "Entendemos su consulta. Sin embargo, por motivos de seguridad, únicamente podemos compartir información de la operación con la persona que realizó el envío. \n\nLe sugerimos pedirle que nos contacte directamente por este medio para poder ayudarle de forma adecuada.\nGracias por su comprensión."
                    derivacion = "NA"
                elif status_upper in ["PAID", "PAGADO"]:
                    reply_text = "Verificando la información, el envío aparece en el sistema como pagado."
                    derivacion = "NA"
                elif status_upper in ["PAYMENT READY", "PAYMENT READY "] or is_guayaquil_cash:
                    reply_text = "Verificando la información, el envío está disponible para cobro."
                    derivacion = "NA"
                elif status_upper in ["REJECTED", "CANCELLED"]:
                    reply_text = "Verificando la información, lamentablemente el envío no pudo ser procesado exitosamente. \n¿Le gustaría que lo comunique con un asesor?"
                    derivacion = "NA"
                elif "VERIFY HOLD" in status_upper or "GATEWAY INFO" in status_upper:
                    reply_text = "Entendemos su consulta. Sin embargo, por motivos de seguridad, únicamente podemos compartir información de la operación con la persona que realizó el envío. \n\nLe sugerimos pedirle que nos contacte directamente por este medio para poder ayudarle de forma adecuada.\nGracias por su comprensión."
                    derivacion = "NA"
                else:
                    reply_text = f"El estatus de su transacción es {status_clean}."
                    derivacion = "NA"
            else:
                # Perfil is REMITENTE/CLIENTE or AGENTE
                compliance_holds = ["GATEWAY INFO REQUIRED", "VERIFY HOLD (O)", "VERIFY HOLD (D)", "VERIFY HOLD (K)"]
                
                if status_upper in compliance_holds:
                    if check_department_hours("CUMPLIMIENTO", ct_now):
                        derivacion = "Cumplimiento"
                        reply_text = "Entiendo su solicitud. Este caso requiere atención de un área especializada (Cumplimiento). Canalizaré su solicitud para que un asesor pueda dar seguimiento y comunicarse con usted lo antes posible."
                    else:
                        derivacion = "Fuera de Horario Depto"
                        reply_text = "Entiendo su solicitud. Su caso requiere atención de un área especializada y por el momento no se encuentra disponible. Se notificó sobre su caso y se comunicarán con usted en cuanto reinicien operaciones. Gracias por su paciencia."
                elif "VERIFY HOLD (KYC)" in status_upper:
                    if check_department_hours("PREVENCION DE FRAUDES", ct_now):
                        derivacion = "Fraudes"
                        reply_text = "Entiendo su solicitud. Este caso requiere atención de un área especializada (Prevención de Fraudes). Canalizaré su solicitud para que un asesor pueda dar seguimiento y comunicarse con usted lo antes posible."
                    else:
                        # Emergency overflow (RNE.56)
                        if check_department_hours("SERVICIO AL CLIENTE", ct_now):
                            derivacion = "Servicio al Cliente"
                            reply_text = "Entiendo la situación. Su solicitud es de alta prioridad para nosotros, lo comunicaré inmediatamente con un asesor de Servicio al Cliente para darle atención urgente (Desborde de Emergencia por Horario)."
                        else:
                            derivacion = "Fuera de Horario SC"
                            reply_text = "En este momento nuestros asesores no se encuentran disponibles. Un asesor dará seguimiento a su solicitud en cuanto retomemos el servicio. Gracias por su paciencia."
                elif status_upper in ["PAID", "PAGADO"]:
                    reply_text = "Verificando la información, el envío aparece en el sistema como pagado."
                    derivacion = "NA"
                elif status_upper in ["PAYMENT READY", "PAYMENT READY "]:
                    reply_text = "Verificando la información, el envío está disponible para cobro."
                    derivacion = "NA"
                elif status_upper in ["REJECTED", "CANCELLED"]:
                    reply_text = "Verificando la información, lamentablemente el envío no pudo ser procesado exitosamente. \n¿Le gustaría que lo comunique con un asesor?"
                    derivacion = "NA"
                elif status_upper == "UNCLAIMED HOLD":
                    if check_department_hours("SERVICIO AL CLIENTE", ct_now):
                        derivacion = "Servicio al Cliente"
                        reply_text = "El plazo para cobrar el envío ha expirado, lo transferiré con un asesor. Por favor, espere un momento..."
                    else:
                        derivacion = "Fuera de Horario SC"
                        reply_text = "En este momento nuestros asesores no se encuentran disponibles. Un asesor dará seguimiento a su solicitud en cuanto retomemos el servicio. Gracias por su paciencia."
                elif status_upper in [
                    "CANCEL STAND BY", "CANCEL IN PROCESS", "CANCEL ACCEPTED", "STAND BY", 
                    "PENDING GATEWAY RESPONSE", "TRANSFER ACCEPTED", "VERIFY HOLD (S)", 
                    "VERIFY HOLD (DP)", "UPDATE IN PROGRESS", "ORIGIN/PENDING PAYMENT", "RETURNED"
                ]:
                    if check_department_hours("SERVICIO AL CLIENTE", ct_now):
                        derivacion = "Servicio al Cliente"
                        reply_text = "Su operación está siendo procesada, lo transferiré con un asesor para verificar la situación específica. Por favor, espere un momento..."
                    else:
                        derivacion = "Fuera de Horario SC"
                        reply_text = "En este momento nuestros asesores no se encuentran disponibles. Un asesor dará seguimiento a su solicitud en cuanto retomemos el servicio. Gracias por su paciencia."
                else:
                    reply_text = f"El estatus de su transacción es {status_clean}."
                    derivacion = "NA"
        else:
            # Table type is "bill"
            if status_upper in ["PAID", "ENTREGADO"]:
                reply_text = "Verificando el estatus de la operación, el pago se realizó exitosamente."
                derivacion = "NA"
            elif status_upper in ["CANCELLED", "CANCELADO"]:
                reply_text = "Verificando el estatus de la operación, lamentablemente el pago no se procesó exitosamente."
                derivacion = "NA"
            else:
                # Transitorio / Pending / Retrasado
                if check_department_hours("SERVICIO AL CLIENTE", ct_now):
                    derivacion = "Servicio al Cliente"
                    reply_text = "Su pago no ha sido procesado de forma definitiva aún, lo transferiré con un asesor de Servicio al Cliente para recibir asistencia personalizada. Por favor, espere."
                else:
                    derivacion = "Fuera de Horario SC"
                    reply_text = "En este momento nuestros asesores no se encuentran disponibles. Un asesor dará seguimiento a su solicitud en cuanto retomemos el servicio. Gracias por su paciencia."

    # Force compliance overrides for UNCLAIMED HOLD (RNE.39 / RNE.37)
    if status_upper == "UNCLAIMED HOLD":
        scripts = get_compliance_scripts()
        if perfil == "BENEFICIARIO":
            reply_text = scripts.get("SC.019", "Entendemos su consulta. Sin embargo, por motivos de seguridad, únicamente podemos compartir información...")
            derivacion = "NA"
        else:
            reply_text = scripts.get("SC.020", "El plazo para cobrar el envío ha expirado, lo transferiré con un asesor. Por favor, espere un momento.")
            if check_department_hours("SERVICIO AL CLIENTE", ct_now):
                derivacion = "Servicio al Cliente"
            else:
                derivacion = "Fuera de Horario SC"
                sc27 = scripts.get("SC.027", "En este momento nuestros asesores no se encuentran disponibles...")
                reply_text = f"{reply_text}\n\n{sc27}"

    # Concatenate SC.033 for self-service final states (derivacion == "NA")
    if derivacion == "NA":
        reply_text = append_courtesy_sc33(reply_text, contact_name)

    # Auto-translate response if customer wrote in a non-Spanish language
    if reply_text and user_text:
        reply_text = await translate_script_if_needed(reply_text, user_text)

    return StatusCheckResponse(
        status="success",
        reply_text=reply_text,
        derivacion=derivacion,
        validation_success=True,
        transaction_status=status_clean,
        client_profile=perfil
    )


@app.post("/api/v1/bill/check", response_model=BillCheckResponse)
async def check_bill_status(
    request: BillCheckRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    start_time = time.time()
    status_val = ResponseStatus.OK
    error_msg = None
    resp = None
    try:
        resp = await check_bill_status_inner(request, x_webhook_secret, secret)
        return resp
    except Exception as e:
        status_val = ResponseStatus.ERROR
        error_msg = str(e)
        raise e
    finally:
        try:
            latency = int((time.time() - start_time) * 1000)
            request_log = RequestLog(
                trace_id=f"api-{uuid.uuid4()}",
                timestamp=datetime.utcnow(),
                conversation_id=request.contact_id or "unknown",
                contact_id=request.codigo_envio or "unknown",
                channel="respond_api",
                user_text=f"Bill Check: {request.codigo_envio or ''}",
                mcp_response=resp.reply_text if resp else error_msg,
                status=status_val,
                latency_ms=latency,
                category="bill_check"
            )
            await telemetry_service.log_request(request_log)
        except Exception as log_err:
            logger.error(f"Error logging bill check telemetry: {log_err}")

async def check_bill_status_inner(
    request: BillCheckRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    """
    Endpoint for validating bill payments, checking name & biller matching,
    applying sheet-based status scripts and department routing.
    """
    # 1. Validate secret
    incoming_secret = x_webhook_secret or secret
    if incoming_secret != settings.WEBHOOK_SECRET:
        logger.warning("❌ Invalid webhook secret in bill status check")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
    logger.info(f"📥 Received bill check request: {request.dict()}")

    def sanitize_input(v: Any) -> Optional[str]:
        if v is None:
            return None
        v_str = str(v).strip().strip(",").strip()
        if (v_str in [",", "%", "", "null", "None"] or 
            v_str.startswith("$") or 
            "{{" in v_str or 
            "}}" in v_str):
            return None
        return v_str

    user_text = sanitize_input(request.user_text) or ""
    contact_id = sanitize_input(request.contact_id) or "-1"
    contact_name = sanitize_input(request.contact_name)
    
    metadata = request.metadata or {}
    tracking_number = sanitize_input(request.tracking_number) or sanitize_input(metadata.get("tracking_number"))
    biller = sanitize_input(request.biller) or sanitize_input(metadata.get("biller"))
    nombre_completo_customer = sanitize_input(request.nombre_completo_customer) or sanitize_input(metadata.get("nombre_completo_customer"))
    perfil = sanitize_input(request.perfil) or sanitize_input(metadata.get("perfil")) or sanitize_input(metadata.get("perfil_usuario"))
    
    if perfil:
        perfil = perfil.upper()
    else:
        perfil = "CLIENTE"
        
    # Get Redis client
    redis = None
    try:
        redis = await get_redis_client()
    except Exception as redis_err:
        logger.warning(f"Redis connection not available for bill check: {redis_err}")

    # Attempts handling for tracking_number / key lookup
    attempts_key = f"bill_attempts:{contact_id}"
    attempts = 0
    if redis:
        try:
            attempts_val = await redis.get(attempts_key)
            attempts = int(attempts_val.decode('utf-8')) if attempts_val else 0
        except Exception as e:
            logger.error(f"Error reading bill attempts from Redis: {e}")

    # If tracking_number is missing, handle error/re-verification
    if not tracking_number:
        attempts += 1
        if redis:
            try:
                await redis.set(attempts_key, str(attempts), ex=3600)
            except Exception as e:
                logger.error(f"Error setting bill attempts in Redis: {e}")
                
        if attempts >= 2:
            if redis:
                try:
                    await redis.set(attempts_key, "0", ex=3600)
                except Exception as e:
                    logger.error(f"Error resetting bill attempts: {e}")
            return BillCheckResponse(
                status="success",
                reply_text="No fue posible procesar su solicitud con la clave proporcionada. Lo transferiré con uno de nuestros asesores. Por favor espere un momento...",
                derivacion="Servicio al Cliente",
                validation_success=False
            )
        else:
            return BillCheckResponse(
                status="success",
                reply_text="No he podido localizar la información con los datos que me ha proporcionado. Por favor, confirmelos y escríbalos nuevamente.",
                derivacion="NA",
                validation_success=False
            )

    # Reset attempts since tracking_number was provided
    if redis:
        try:
            await redis.set(attempts_key, "0", ex=3600)
        except Exception as e:
            logger.error(f"Error resetting bill attempts: {e}")

    # Try Supabase REST API first (fastest, IPv4/IPv6 compatible via HTTPS)
    try:
        supabase_url = os.getenv("SUPABASE_URL", "https://tzlomvpugmrpdfatscxe.supabase.co")
        supabase_anon_key = os.getenv(
            "SUPABASE_ANON_KEY",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6bG9tdnB1Z21ycGRmYXRzY3hlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3NjI3MjcsImV4cCI6MjA4OTMzODcyN30.aH-p2YbLa8LPlnMVsZMlELsxFWwSSLZMA_LPpRz5DU8"
        )
        headers = {
            "apikey": supabase_anon_key,
            "Authorization": f"Bearer {supabase_anon_key}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=4.0) as client:
            url = f"{supabase_url}/rest/v1/Pago%20de%20Bill"
            params = {
                "tracking_number": f"ilike.{tracking_number}",
                "select": "*",
                "limit": "1"
            }
            res = await client.get(url, headers=headers, params=params)
            if res.status_code == 200:
                data = res.json()
                if data:
                    record = data[0]
        if record:
            logger.info(f"✅ Bill record found via REST API for tracking_number {tracking_number}")
    except Exception as rest_err:
        logger.warning(f"Supabase REST API bill query failed: {rest_err}")

    # Fallback to PostgreSQL if REST API didn't return a record
    if not record and settings.SUPABASE_URI:
        try:
            from .shared_logic import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM public."Pago de Bill" WHERE "tracking_number" = %s;', (tracking_number,))
            row = cursor.fetchone()
            if row:
                colnames = [desc[0] for desc in cursor.description]
                record = dict(zip(colnames, row))
            cursor.close()
            conn.close()
            logger.info(f"✅ Bill record found via PostgreSQL for tracking_number {tracking_number}")
        except Exception as db_err:
            logger.warning(f"PostgreSQL query failed for bill: {db_err}")

    # If record not found
    if not record:
        attempts += 1
        if redis:
            try:
                await redis.set(attempts_key, str(attempts), ex=3600)
            except Exception as e:
                logger.error(f"Error saving bill attempts: {e}")
        if attempts >= 2:
            if redis:
                try:
                    await redis.set(attempts_key, "0", ex=3600)
                except Exception as e:
                    logger.error(f"Error resetting attempts: {e}")
            return BillCheckResponse(
                status="success",
                reply_text="No fue posible procesar su solicitud con la clave proporcionada. Lo transferiré con uno de nuestros asesores. Por favor espere un momento...",
                derivacion="Servicio al Cliente",
                validation_success=False
            )
        else:
            return BillCheckResponse(
                status="success",
                reply_text="No he podido localizar la información con los datos que me ha proporcionado. Por favor, confirmelos y escríbalos nuevamente.",
                derivacion="NA",
                validation_success=False
            )

    # 2. Identity Verification: match Biller and Customer Name
    db_biller = record.get("biller", "")
    db_customer_name = f"{record.get('nombre_o_nombres', '')} {record.get('apellido_paterno', '')} {record.get('apellido_materno', '')}".strip()
    db_customer_name = re.sub(r'\s+', ' ', db_customer_name)
    
    user_biller = biller
    user_customer = nombre_completo_customer
    
    biller_ok = False
    customer_ok = False
    
    if user_biller:
        biller_ok = match_biller(user_biller, db_biller)
    if user_customer:
        customer_ok = match_customer_name(
            user_customer,
            record.get("nombre_o_nombres", ""),
            record.get("apellido_paterno", ""),
            record.get("apellido_materno", "")
        )
        
    validation_key = f"bill_val_attempts:{contact_id}"
    val_attempts = 0
    if redis:
        try:
            val_attempts_val = await redis.get(validation_key)
            val_attempts = int(val_attempts_val.decode('utf-8')) if val_attempts_val else 0
        except Exception as e:
            logger.error(f"Error reading validation attempts: {e}")

    if not biller_ok or not customer_ok:
        val_attempts += 1
        if redis:
            try:
                await redis.set(validation_key, str(val_attempts), ex=3600)
            except Exception as e:
                logger.error(f"Error saving validation attempts: {e}")
                
        if val_attempts >= 2:
            if redis:
                try:
                    await redis.set(validation_key, "0", ex=3600)
                except Exception as e:
                    logger.error(f"Error resetting validation attempts: {e}")
            return BillCheckResponse(
                status="success",
                reply_text="No fue posible validar su identidad con la información proporcionada. Lo transferiré con un asesor, para que reciba la asistencia necesaria.",
                derivacion="Servicio al Cliente",
                validation_success=False
            )
        else:
            return BillCheckResponse(
                status="success",
                reply_text="Los datos proporcionados (biller o nombre de cliente) no coinciden con nuestros registros. Por favor verifíquelos y compártalos nuevamente.",
                derivacion="NA",
                validation_success=False
            )

    # Reset validation attempts on success
    if redis:
        try:
            await redis.set(validation_key, "0", ex=3600)
        except Exception as e:
            logger.error(f"Error resetting validation attempts: {e}")

    # 3. Rule Crossing (Matrix)
    status_db = record.get("status") or ""
    status_clean = status_db.strip()
    status_upper = status_clean.upper()
    
    # Fetch status rules from Google Sheets
    status_rules = None
    sheet_id = settings.GOOGLE_SHEET_ID_BILL_ESTATUS or "16fB_MGtha0NUtp5mge7UwvHcWo1NYVnOGVv6Yntv9xo"
    if sheet_id:
        if redis:
            try:
                cached_val = await redis.get("google_sheets:bill_status_cache")
                if cached_val:
                    status_rules = json.loads(cached_val.decode('utf-8'))
            except Exception as e:
                logger.error(f"Error reading bill status rules cache: {e}")
                
        if not status_rules:
            from .google_sheets_service import google_sheets_service
            status_rules = await google_sheets_service.fetch_bill_status_rules(sheet_id)
            if status_rules and redis:
                try:
                    await redis.setex("google_sheets:bill_status_cache", 3600, json.dumps(status_rules))
                except Exception as e:
                    logger.error(f"Error caching bill status rules in Redis: {e}")

    matched_rule = None
    if status_rules:
        logger.info(f"Loaded status_rules from cache/sheets: {status_rules}")
        # Match rules against database status and profile
        perfil_upper = perfil.upper().strip()
        
        def profile_matches(u_prof: str, r_prof: str) -> bool:
            if not r_prof:
                return True
            u_p = u_prof.upper().strip()
            r_p = r_prof.upper().strip()
            if "REMITE" in r_p or "AGENTE" in r_p or "BENEFICIARIO" in r_p:
                if u_p in ["CLIENTE", "REMITENTE", "AGENTE"]:
                    return "REMITE" in r_p or "AGENTE" in r_p
                elif u_p == "BENEFICIARIO":
                    return "BENEFICIARIO" in r_p
            return u_p == r_p

        for rule in status_rules:
            rule_status = rule["status"].lower().strip()
            rule_profile = rule.get("perfil", "")
            db_status = status_clean.lower().strip()
            
            # Check profile first
            if not profile_matches(perfil_upper, rule_profile):
                continue
                
            is_match = (db_status == rule_status) or (db_status in rule_status) or (rule_status in db_status)
            
            # Translation equivalents:
            if not is_match:
                if db_status in ["cancelled", "cancelado"] and rule_status in ["cancelled", "cancelado"]:
                    is_match = True
                elif db_status in ["paid", "entregado", "pagado"] and rule_status in ["paid", "entregado", "pagado"]:
                    is_match = True
                elif db_status in ["origin", "creado", "creada", "transitorio", "pendiente"] and rule_status in ["origin", "creado", "creada", "transitorio", "pendiente"]:
                    is_match = True
            
            if is_match:
                matched_rule = rule
                break

    # Local fallback if sheet rules fetching failed
    if not matched_rule:
        logger.warning(f"No sheet status rule matched for bill status={status_clean}. Using local fallback.")
        if status_upper in ["PAID", "ENTREGADO"]:
            matched_rule = {
                "script": "Verificando el estatus de la operación, el pago se realizó exitosamente.",
                "derivacion": "NA"
            }
        elif status_upper in ["CANCELLED", "CANCELADO"]:
            matched_rule = {
                "script": "Verificando el estatus de la operación, lamentablemente el pago no se procesó exitosamente.",
                "derivacion": "Servicio al Cliente"
            }
        else: # Origin / Transitorio
            matched_rule = {
                "script": "Su pago no ha sido procesado, lo transferiré con un asesor para recibir asistencia personalizada. Por favor, espere mientras lo comunico.",
                "derivacion": "Servicio al Cliente"
            }
    else:
        logger.info(f"Matched rule from sheets: {matched_rule}")

    script_text = resolve_script_text(matched_rule["script"])
    deriv_raw = matched_rule["derivacion"].strip()
    
    # Clean script text
    clean_name = contact_name or "Cliente"
    script_text = script_text.replace("“", "").replace("”", "").replace('"', "")
    script_text = script_text.replace("Sr./Srita._________", clean_name).replace("Sr./Srita.____", clean_name)
    
    # Process Derivacion and Reply Text
    derivacion = "NA"
    reply_text = script_text
    ct_now = get_central_time()
    
    if "SERVICIO AL CLIENTE" in deriv_raw.upper() or "SERVICIO A CLIENTE" in deriv_raw.upper():
        if check_department_hours("SERVICIO AL CLIENTE", ct_now):
            derivacion = "Servicio al Cliente"
        else:
            derivacion = "Fuera de Horario SC"
            reply_text = (
                f"{reply_text}\n\n"
                "En este momento nuestros asesores no se encuentran disponibles. Un asesor dará seguimiento a su solicitud en cuanto "
                "retomemos el servicio. Gracias por su paciencia."
            )
    else:
        derivacion = "NA"
        reply_text = append_courtesy_sc33(reply_text, request.contact_name)

    # Prepend safety headers
    safety_header = f"[BILLER: {db_biller}] [NOMBRE DEL CUSTOMER: {db_customer_name}] [STATUS: {status_clean}] "
    
    # Auto-translate response if customer wrote in a non-Spanish language
    if reply_text and user_text:
        reply_text = await translate_script_if_needed(reply_text, user_text)

    reply_text_with_header = safety_header + reply_text

    return BillCheckResponse(
        status="success",
        reply_text=reply_text_with_header,
        derivacion=derivacion,
        validation_success=True,
        transaction_status=status_clean,
        client_profile=perfil
    )


@app.post("/api/v1/csat/log", response_model=CSATLogResponse)
async def log_csat_feedback(
    request: CSATLogRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    start_time = time.time()
    status_val = ResponseStatus.OK
    error_msg = None
    resp = None
    try:
        resp = await log_csat_feedback_inner(request, x_webhook_secret, secret)
        return resp
    except Exception as e:
        status_val = ResponseStatus.ERROR
        error_msg = str(e)
        raise e
    finally:
        try:
            latency = int((time.time() - start_time) * 1000)
            request_log = RequestLog(
                trace_id=f"api-{uuid.uuid4()}",
                timestamp=datetime.utcnow(),
                conversation_id=request.conversation_id or "unknown",
                contact_id=request.contact_id or "unknown",
                channel="respond_api",
                user_text=f"CSAT Log: Rating={request.score or 0}",
                mcp_response=resp.message if resp else error_msg,
                status=status_val,
                latency_ms=latency,
                category="csat_log"
            )
            await telemetry_service.log_request(request_log)
        except Exception as log_err:
            logger.error(f"Error logging CSAT telemetry: {log_err}")

async def log_csat_feedback_inner(
    request: CSATLogRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    """
    Endpoint to log CSAT survey feedback directly to Google Sheets
    using the Service Account.
    """
    incoming_secret = x_webhook_secret or secret
    if incoming_secret != settings.WEBHOOK_SECRET:
        logger.warning("❌ Invalid webhook secret in CSAT logging")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    logger.info(f"📥 Received CSAT log request: {request.dict()}")

    try:
        from api.google_sheets_service import GoogleSheetsService
        from datetime import datetime
        from zoneinfo import ZoneInfo

        # Get local MX/Central timestamp
        tz = ZoneInfo("America/Mexico_City")
        timestamp_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        sheets_service = GoogleSheetsService()
        success = await sheets_service.append_csat_log(
            timestamp=timestamp_str,
            contact_id=request.contact_id,
            contact_name=request.contact_name,
            rating=request.rating,
            comment=request.comment or "",
            assigned_agent=request.assigned_agent or "Desconocido"
        )

        if success:
            return CSATLogResponse(status="success", message="CSAT logged successfully to Google Sheets")
        else:
            raise HTTPException(status_code=500, detail="Failed to write CSAT row to Google Sheets")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in CSAT logging endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/api/v1/topup/check", response_model=TopupCheckResponse)
async def check_topup_status(
    request: TopupCheckRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    start_time = time.time()
    status_val = ResponseStatus.OK
    error_msg = None
    resp = None
    try:
        resp = await check_topup_status_inner(request, x_webhook_secret, secret)
        return resp
    except Exception as e:
        status_val = ResponseStatus.ERROR
        error_msg = str(e)
        raise e
    finally:
        try:
            latency = int((time.time() - start_time) * 1000)
            request_log = RequestLog(
                trace_id=f"api-{uuid.uuid4()}",
                timestamp=datetime.utcnow(),
                conversation_id=request.contact_id or "unknown",
                contact_id=request.phone_number or "unknown",
                channel="respond_api",
                user_text=f"Topup Check: {request.phone_number or ''}",
                mcp_response=resp.reply_text if resp else error_msg,
                status=status_val,
                latency_ms=latency,
                category="topup_check"
            )
            await telemetry_service.log_request(request_log)
        except Exception as log_err:
            logger.error(f"Error logging topup check telemetry: {log_err}")

async def check_topup_status_inner(
    request: TopupCheckRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    """
    Endpoint for validating mobile top-up checks, verifying customer number & cellular number,
    applying sheet-based status rules and department routing.
    """
    # 1. Validate secret
    incoming_secret = x_webhook_secret or secret
    if incoming_secret != settings.WEBHOOK_SECRET:
        logger.warning("❌ Invalid webhook secret in top-up status check")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
    logger.info(f"📥 Received top-up check request: {request.dict()}")

    def sanitize_input(v: Any) -> Optional[str]:
        if v is None:
            return None
        v_str = str(v).strip().strip(",").strip()
        if (v_str in [",", "%", "", "null", "None"] or 
            v_str.startswith("$") or 
            "{{" in v_str or 
            "}}" in v_str):
            return None
        return v_str

    user_text = sanitize_input(request.user_text) or ""
    contact_id = sanitize_input(request.contact_id) or "-1"
    contact_name = sanitize_input(request.contact_name)
    
    metadata = request.metadata or {}
    transaction_id = sanitize_input(request.transaction_id) or sanitize_input(metadata.get("transaction_id"))
    customer_number = sanitize_input(request.customer_number) or sanitize_input(metadata.get("customer_number"))
    cellular_number = sanitize_input(request.cellular_number) or sanitize_input(metadata.get("cellular_number"))
    perfil = sanitize_input(request.perfil) or sanitize_input(metadata.get("perfil")) or sanitize_input(metadata.get("perfil_usuario"))
    
    if perfil:
        perfil = perfil.upper()
    else:
        perfil = "CLIENTE"
        
    # Get Redis client
    redis = None
    try:
        redis = await get_redis_client()
    except Exception as redis_err:
        logger.warning(f"Redis connection not available for top-up check: {redis_err}")

    # Attempts keys
    attempts_key = f"topup_attempts:{contact_id}"
    validation_key = f"topup_val_attempts:{contact_id}"
    
    attempts = 0
    val_attempts = 0
    if redis:
        try:
            attempts_val = await redis.get(attempts_key)
            attempts = int(attempts_val.decode('utf-8')) if attempts_val else 0
            
            val_attempts_val = await redis.get(validation_key)
            val_attempts = int(val_attempts_val.decode('utf-8')) if val_attempts_val else 0
        except Exception as e:
            logger.error(f"Error reading top-up attempts from Redis: {e}")

    # If transaction_id is missing, handle error/re-verification
    if not transaction_id:
        attempts += 1
        if redis:
            try:
                await redis.set(attempts_key, str(attempts), ex=3600)
            except Exception as e:
                logger.error(f"Error setting top-up attempts in Redis: {e}")
                
        if attempts >= 2:
            if redis:
                try:
                    await redis.set(attempts_key, "0", ex=3600)
                except Exception as e:
                    logger.error(f"Error resetting top-up attempts: {e}")
            return TopupCheckResponse(
                status="success",
                reply_text="No fue posible procesar su solicitud con la clave proporcionada. Lo transferiré con uno de nuestros asesores. Por favor espere un momento.",
                derivacion="Servicio al Cliente",
                validation_success=False
            )
        else:
            return TopupCheckResponse(
                status="success",
                reply_text="No he podido localizar la información con los datos que me ha proporcionado. Por favor, confirmelos y escríbalos nuevamente para realizar una nueva consulta.",
                derivacion="NA",
                validation_success=False
            )

    # Reset lookup attempts since transaction_id was provided
    if redis:
        try:
            await redis.set(attempts_key, "0", ex=3600)
        except Exception as e:
            logger.error(f"Error resetting top-up attempts: {e}")

    # Query database for the record
    # Try Supabase REST API first (fastest, IPv4/IPv6 compatible via HTTPS)
    try:
        supabase_url = os.getenv("SUPABASE_URL", "https://tzlomvpugmrpdfatscxe.supabase.co")
        supabase_anon_key = os.getenv(
            "SUPABASE_ANON_KEY",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6bG9tdnB1Z21ycGRmYXRzY3hlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3NjI3MjcsImV4cCI6MjA4OTMzODcyN30.aH-p2YbLa8LPlnMVsZMlELsxFWwSSLZMA_LPpRz5DU8"
        )
        headers = {
            "apikey": supabase_anon_key,
            "Authorization": f"Bearer {supabase_anon_key}",
            "Content-Type": "application/json"
        }
        import httpx
        async with httpx.AsyncClient(timeout=4.0) as client:
            url = f"{supabase_url}/rest/v1/Recargas"
            params = {
                "Transaction ID": f"ilike.{transaction_id}",
                "select": "*",
                "limit": "1"
            }
            res = await client.get(url, headers=headers, params=params)
            if res.status_code == 200:
                data = res.json()
                if data:
                    record = data[0]
                    logger.info(f"✅ Top-up record found via REST API for transaction_id {transaction_id}")
    except Exception as rest_err:
        logger.warning(f"Supabase REST API query failed for top-up: {rest_err}")

    # Fallback to PostgreSQL if REST API didn't return a record
    if not record and settings.SUPABASE_URI:
        try:
            from .shared_logic import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM public."Recargas" WHERE "Transaction ID" = %s;', (transaction_id,))
            row = cursor.fetchone()
            if row:
                colnames = [desc[0] for desc in cursor.description]
                record = dict(zip(colnames, row))
            cursor.close()
            conn.close()
            logger.info(f"✅ Top-up record found via PostgreSQL for transaction_id {transaction_id}")
        except Exception as db_err:
            logger.warning(f"PostgreSQL query failed for top-up: {db_err}")

    if not record:
        # Not found
        val_attempts += 1
        if redis:
            try:
                await redis.set(validation_key, str(val_attempts), ex=3600)
            except Exception as e:
                logger.error(f"Error saving validation attempts in Redis: {e}")
                
        if val_attempts >= 2:
            if redis:
                try:
                    await redis.set(validation_key, "0", ex=3600)
                except Exception as e:
                    logger.error(f"Error resetting validation attempts: {e}")
            return TopupCheckResponse(
                status="success",
                reply_text="No fue posible procesar su solicitud con la clave proporcionada. Lo transferiré con uno de nuestros asesores. Por favor espere un momento.",
                derivacion="Servicio al Cliente",
                validation_success=False
            )
        else:
            return TopupCheckResponse(
                status="success",
                reply_text="No he podido localizar la información con los datos que me ha proporcionado. Por favor, confirmelos y escríbalos nuevamente para realizar una nueva consulta.",
                derivacion="NA",
                validation_success=False
            )

    # Identity Verification: match Customer Number and Cellular Number
    db_customer = record.get("Customer Number")
    db_cellular = record.get("Cellular Number")
    
    # Clean non-digits and parse as int for robust comparison
    def clean_phone_to_int(val: Any) -> Optional[int]:
        if val is None:
            return None
        cleaned = re.sub(r"\D", "", str(val))
        return int(cleaned) if cleaned else None

    user_customer_cleaned = clean_phone_to_int(customer_number)
    user_cellular_cleaned = clean_phone_to_int(cellular_number)
    
    db_customer_cleaned = clean_phone_to_int(db_customer)
    db_cellular_cleaned = clean_phone_to_int(db_cellular)
    
    customer_ok = (user_customer_cleaned == db_customer_cleaned) if (user_customer_cleaned is not None and db_customer_cleaned is not None) else False
    cellular_ok = (user_cellular_cleaned == db_cellular_cleaned) if (user_cellular_cleaned is not None and db_cellular_cleaned is not None) else False
    
    if not customer_ok or not cellular_ok:
        val_attempts += 1
        if redis:
            try:
                await redis.set(validation_key, str(val_attempts), ex=3600)
            except Exception as e:
                logger.error(f"Error saving validation attempts: {e}")
                
        if val_attempts >= 2:
            if redis:
                try:
                    await redis.set(validation_key, "0", ex=3600)
                except Exception as e:
                    logger.error(f"Error resetting validation attempts: {e}")
            return TopupCheckResponse(
                status="success",
                reply_text="No fue posible procesar su solicitud con la clave proporcionada. Lo transferiré con uno de nuestros asesores. Por favor espere un momento.",
                derivacion="Servicio al Cliente",
                validation_success=False
            )
        else:
            return TopupCheckResponse(
                status="success",
                reply_text="No he podido localizar la información con los datos que me ha proporcionado. Por favor, confirmelos y escríbalos nuevamente para realizar una nueva consulta.",
                derivacion="NA",
                validation_success=False
            )

    # Reset attempts upon successful match
    if redis:
        try:
            await redis.set(validation_key, "0", ex=3600)
        except Exception as e:
            logger.error(f"Error resetting validation attempts: {e}")

    # Match rules from Google Sheets
    status_rules = None
    sheet_id = settings.GOOGLE_SHEET_ID_TOPUP_ESTATUS or "1E3pNthg7myh7tgjEnb_TIxCnTLFi_gzWlcxk2LOdNCs"
    if sheet_id:
        if redis:
            try:
                cached_val = await redis.get("google_sheets:topup_status_cache")
                if cached_val:
                    status_rules = json.loads(cached_val.decode('utf-8'))
            except Exception as e:
                logger.error(f"Error reading top-up status rules cache: {e}")
                
        if not status_rules:
            from .google_sheets_service import google_sheets_service
            status_rules = await google_sheets_service.fetch_topup_status_rules(sheet_id)
            if status_rules and redis:
                try:
                    await redis.setex("google_sheets:topup_status_cache", 3600, json.dumps(status_rules))
                except Exception as e:
                    logger.error(f"Error caching top-up status rules: {e}")

    # Determine status matching
    db_status = str(record.get("Status", "")).strip()
    status_clean = db_status
    if db_status.lower() == "cancell":
        status_clean = "Cancelled"  # normalize to Cancelled to match sheet "Cancelled - Recarga Telefónica"

    perfil_upper = perfil.upper().strip()
    
    def profile_matches(u_prof: str, r_prof: str) -> bool:
        if not r_prof:
            return True
        u_p = u_prof.upper().strip()
        r_p = r_prof.upper().strip()
        if "REMITE" in r_p or "AGENTE" in r_p or "BENEFICIARIO" in r_p:
            if u_p in ["CLIENTE", "REMITENTE", "AGENTE"]:
                return "REMITE" in r_p or "AGENTE" in r_p
            elif u_p == "BENEFICIARIO":
                return "BENEFICIARIO" in r_p
        return u_p == r_p

    # Decidir si buscamos Solicitud de status o Consulta de status en Chronos
    user_intent = metadata.get("intencion_usuario") or ""
    category_to_match = "Solicitud de status"
    if user_intent and "estatus" not in user_intent.lower() and "status" not in user_intent.lower():
        category_to_match = "Consulta de status en Chronos"

    matched_rule = None
    if status_rules:
        logger.info(f"Loaded top-up status_rules: {status_rules}")
        for rule in status_rules:
            rule_status = rule["status"].lower().strip()
            rule_profile = rule.get("perfil", "")
            rule_category = rule.get("categoria", "").lower().strip()
            
            # Match profile
            if not profile_matches(perfil_upper, rule_profile):
                continue
                
            # Match category
            if category_to_match.lower().strip() not in rule_category:
                continue
                
            # Match status
            is_match = (status_clean.lower() == rule_status) or (status_clean.lower() in rule_status) or (rule_status in status_clean.lower())
            if not is_match:
                if status_clean.lower() in ["cancell", "cancelled"] and "cancel" in rule_status:
                    is_match = True
                elif status_clean.lower() == "paid" and "paid" in rule_status:
                    is_match = True
                    
            if is_match:
                matched_rule = rule
                break

    # Local fallback
    if not matched_rule:
        logger.warning(f"No sheet status rule matched for topup status={status_clean}. Using local fallback.")
        if status_clean.lower() == "paid":
            matched_rule = {
                "script": "Verificando la información, la recarga se realizó exitosamente.",
                "derivacion": "NA"
            }
        else:
            matched_rule = {
                "script": "Verificando la información, la recarga no se procesó exitosamente.\n¿Le gustaría que lo comunique con un asesor?",
                "derivacion": "NA"
            }

    script_text = resolve_script_text(matched_rule["script"])
    deriv_raw = matched_rule["derivacion"].strip()
    
    derivacion = "NA"
    reply_text = script_text
    
    if "SERVICIO AL CLIENTE" in deriv_raw.upper() or "SERVICIO A CLIENTE" in deriv_raw.upper():
        from .main import check_department_hours, get_central_time
        ct_now = get_central_time()
        if check_department_hours("SERVICIO AL CLIENTE", ct_now):
            derivacion = "Servicio al Cliente"
        else:
            derivacion = "Fuera de Horario SC"
            reply_text = (
                f"{reply_text}\n\n"
                "En este momento nuestros asesores no se encuentran disponibles. Un asesor dará seguimiento a su solicitud en cuanto "
                "retomemos el servicio. Gracias por su paciencia."
            )
            
    # Prepend safety headers
    safety_header = f"[TRANSACTION ID: {transaction_id}] [CUSTOMER NUMBER: {db_customer}] [CELLULAR NUMBER: {db_cellular}] [STATUS: {db_status}] "
    reply_text_with_header = safety_header + reply_text

    if derivacion == "NA":
        reply_text = append_courtesy_sc33(reply_text, request.contact_name)

    # Auto-translate response if customer wrote in a non-Spanish language
    if reply_text and user_text:
        reply_text = await translate_script_if_needed(reply_text, user_text)

    reply_text_with_header = safety_header + reply_text

    return TopupCheckResponse(
        status="success",
        reply_text=reply_text_with_header,
        derivacion=derivacion,
        validation_success=True,
        transaction_status=db_status,
        client_profile=perfil
    )



# ============================================================
# Event Webhook Endpoint (Respond.io Events)
# ============================================================

@app.post("/webhook/events")
async def webhook_events(
    request: Dict[str, Any] = Body(...),
    secret: Optional[str] = None,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
):
    """
    Endpoint for asynchronous events from Respond.io (like conversation closed).
    """
    incoming_secret = x_webhook_secret or secret
    if incoming_secret != settings.WEBHOOK_SECRET:
        logger.warning("❌ Invalid webhook secret in event webhook")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
    event = request.get("event") or request.get("type") or request.get("event_type")
    logger.info(f"Received Respond.io event: {event} with payload: {json.dumps(request)}")
    
    # Check if conversation is closed
    event_str = str(event or "").lower()
    is_closed_event = event_str in [
        "conversation.closed", "conversation.status_changed", "conversation_closed",
        "conversation.status_updated", "conversation_status_updated", "closed"
    ]
    conversation_data = request.get("conversation") or {}
    if not is_closed_event and isinstance(conversation_data, dict):
        status = conversation_data.get("status")
        if status == "closed":
            is_closed_event = True
            
    if is_closed_event:
        conversation = request.get("conversation") or {}
        contact = request.get("contact") or {}
        
        # Try finding conversation_id with extra fallback keys
        conversation_id = ""
        if isinstance(conversation, dict):
            conversation_id = str(conversation.get("id") or conversation.get("conversationId") or conversation.get("conversation_id") or "")
        if not conversation_id:
            conversation_id = str(request.get("conversationId") or request.get("conversation_id") or "")
            
        # Try finding contact_id with extra fallback keys
        contact_id = ""
        if isinstance(contact, dict):
            contact_id = str(contact.get("id") or contact.get("contactId") or contact.get("contact_id") or "")
        if not contact_id:
            contact_id = str(request.get("contactId") or request.get("contact_id") or "")
            
        first_name = contact.get("firstName") or "" if isinstance(contact, dict) else ""
        last_name = contact.get("lastName") or "" if isinstance(contact, dict) else ""
        full_name = f"{first_name} {last_name}".strip()
        contact_name = str(contact.get("name") or full_name or "Cliente") if isinstance(contact, dict) else "Cliente"
        
        if conversation_id:
            logger.info(f"🔒 Conversation {conversation_id} closed. Triggering Google Drive upload...")
            
            # Fetch Redis client
            try:
                from shared.redis_client import get_redis_client
                redis_client = await get_redis_client()
                
                # Fetch chat history from Redis before it's cleared by upload_conversation_to_drive
                from .chat_history_helper import get_chat_history, upload_conversation_to_drive
                chat_history = await get_chat_history(redis_client, conversation_id)
                
                # Upload conversation JSON to Google Drive
                file_id = await upload_conversation_to_drive(
                    redis_client, conversation_id, contact_id, contact_name
                )
                
                # Trigger the IA Quality Auditor Agent evaluation
                eval_res = {}
                if chat_history:
                    chat_data = {
                        "conversation_id": conversation_id,
                        "contact_id": contact_id,
                        "contact_name": contact_name,
                        "messages": chat_history
                    }
                    from .qa_auditor_agent import qa_auditor_agent
                    eval_res = await qa_auditor_agent.audit_conversation(chat_data)
                
                # Create entry in Google Sheets (Auditoria_QA tab) with audited_by and evaluations
                if file_id:
                    import random
                    from zoneinfo import ZoneInfo
                    local_date = datetime.now(ZoneInfo("America/Mexico_City")).date().isoformat()
                    now_timestamp = datetime.utcnow().isoformat()
                    
                    rating_intent = eval_res.get("rating_intent", True)
                    rating_resolution = eval_res.get("rating_resolution", True)
                    rating_formal_tone = eval_res.get("rating_formal_tone", True)
                    rating_no_repetition = eval_res.get("rating_no_repetition", True)
                    comments = eval_res.get("comments", "Auditoría realizada de forma automática.")
                    
                    # 5% random sampling OR quality deviation/failure => Human audit needed
                    ia_failed = not (rating_intent and rating_resolution and rating_formal_tone and rating_no_repetition)
                    is_human_review_required = ia_failed or (random.random() < 0.05)
                    
                    auditor_field = "" if is_human_review_required else "AI_AUDITOR"
                    audited_at_field = "" if is_human_review_required else now_timestamp
                    
                    if is_human_review_required:
                        ia_label = "⚠️ IA Auditor detectó posible desviación" if ia_failed else "🔬 IA Auditor (Muestra de Calibración Humana 5%)"
                        comments = f"[{ia_label}]: {comments}"
                    
                    ws = get_audits_sheet()
                    if ws:
                        # Check if conversation_id already exists (update in place)
                        try:
                            cell = ws.find(conversation_id, in_column=1)
                            row_num = cell.row
                            ws.update(f"A{row_num}:K{row_num}", [[
                                conversation_id, contact_id, contact_name, local_date,
                                str(rating_intent), str(rating_resolution),
                                str(rating_formal_tone), str(rating_no_repetition),
                                comments, auditor_field, audited_at_field
                            ]])
                            logger.info(f"✅ Updated existing audit row for {conversation_id} in Google Sheets")
                        except Exception:
                            # Not found — append new row
                            ws.append_row([
                                conversation_id, contact_id, contact_name, local_date,
                                str(rating_intent), str(rating_resolution),
                                str(rating_formal_tone), str(rating_no_repetition),
                                comments, auditor_field, audited_at_field
                            ], value_input_option="RAW")
                            logger.info(f"✅ Appended audit row for {conversation_id} in Google Sheets (Audited by: {auditor_field})")
            except Exception as e:
                logger.error(f"Error handling conversation closed event and running QA audit: {str(e)}")
                
    return {"status": "ok"}


# ============================================================
# Health Check Endpoints
# ============================================================


@app.api_route("/health", methods=["GET", "HEAD"], response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint optimized for Render.
    Responds quickly even if downstream services are slow.
    """
    start_time = time.time()
    
    # Check MCP health with strict 1s timeout
    mcp_healthy = False
    try:
        # We manually call the mcp health check with a shorter timeout here 
        # to ensure Render/UptimeRobot don't time out on the API itself
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.MCP_URL.replace("/query", "/health"),
                timeout=1.0
            )
            mcp_healthy = response.status_code == 200
    except Exception as e:
        logger.warning(f"Health check: MCP connection failed or timed out: {str(e)}")
        mcp_healthy = False

    mcp_status = "healthy" if mcp_healthy else "unhealthy"
    
    # Check Redis health (based on initialization in startup_event)
    redis_status = "healthy" if telemetry_service.enabled else "disabled"
    
    # Overall status: Always return 'healthy' if the API is running, 
    # but specify 'degraded' in the body if MCP is down.
    # This prevents Render from killing the container if MCP is just spinning up.
    overall_status = "healthy" if mcp_healthy else "degraded"
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.API_VERSION,
        mcp_status=mcp_status,
        redis_status=redis_status
    )


@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes/Cloud Run"""
    return {"status": "ready"}


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Respond.io ↔ MCP Middleware",
        "version": settings.API_VERSION,
        "status": "running",
        "endpoints": {
            "webhook": "POST /webhook",
            "health": "GET /health",
            "ready": "GET /ready",
            "admin": "GET /admin/* (requires auth)"
        }
    }


# ============================================================
# Knowledge Base Endpoint
# ============================================================

@app.get("/knowledge")
async def get_knowledge():
    """Knowledge Base / FAQ endpoint"""
    return {
        "faq": [
            {
                "question": "¿Qué significa transferencia pendiente?",
                "answer": "Significa que la operación está en proceso de validación y pronto será procesada por el sistema bancario."
            },
            {
                "question": "¿Cómo configurar el MCP?",
                "answer": "Accede a la pestaña 'Configuración' en el dashboard y asegúrate de que la URL del servidor MCP y el Token sean correctos."
            },
            {
                "question": "¿Por qué el estado aparece como Degraded?",
                "answer": "Esto sucede si el servidor MCP o Redis no responden. Verifica las conexiones en la pestaña de Mantenimiento."
            },
            {
                "question": "¿Qué es el Circuit Breaker?",
                "answer": "Es un mecanismo de seguridad que detiene las peticiones al MCP si este falla repetidamente, protegiendo al sistema de sobrecargas."
            }
        ],
        "links": [
            {"name": "Documentación API", "url": "/docs"},
            {"name": "Panel de Control Render", "url": "https://dashboard.render.com"}
        ]
    }


# ============================================================
# Official Scripts & Business Rules (Google Sheets Integration)
# ============================================================

@app.get("/api/v1/scripts")
async def get_scripts(codes: str):
    """
    Get official script verbatims from Google Sheets (cached in Redis).
    Query parameter `codes` is a comma-separated list of script codes (e.g. "SC.001,CU.A1").
    """
    start_time = time.time()
    resp = None
    try:
        resp = await get_scripts_inner(codes)
        return resp
    finally:
        try:
            latency = int((time.time() - start_time) * 1000)
            request_log = RequestLog(
                trace_id=f"api-{uuid.uuid4()}",
                timestamp=datetime.utcnow(),
                conversation_id="scripts_fetch",
                contact_id="scripts_fetch",
                channel="respond_api",
                user_text=f"GET /scripts?codes={codes}",
                mcp_response=f"Scripts retrieved: {list(resp.keys()) if resp else 'Error'}",
                status=ResponseStatus.OK,
                latency_ms=latency,
                category="scripts_fetch"
            )
            await telemetry_service.log_request(request_log)
        except Exception as log_err:
            logger.error(f"Error logging scripts telemetry: {log_err}")

async def get_scripts_inner(codes: str):
    codes_list = [c.strip().upper().replace(" ", "") for c in codes.split(",") if c.strip()]
    if not codes_list:
        raise HTTPException(status_code=400, detail="Missing codes query parameter")
        
    redis = None
    try:
        redis = await get_redis_client()
    except Exception as redis_err:
        logger.warning(f"Redis client not available in get_scripts: {redis_err}")
        
    cached_scripts = None
    if redis:
        try:
            cached_val = await redis.get("google_sheets:scripts_cache")
            if cached_val:
                cached_scripts = json.loads(cached_val.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error reading scripts cache from Redis: {e}")
            
    if not cached_scripts:
        logger.info(f"🔄 Fetching scripts from Google Sheet ID: {settings.GOOGLE_SHEET_ID_SCRIPTS}")
        from .google_sheets_service import google_sheets_service
        try:
            cached_scripts = await google_sheets_service.fetch_official_scripts(settings.GOOGLE_SHEET_ID_SCRIPTS)
            if cached_scripts and redis:
                try:
                    await redis.setex("google_sheets:scripts_cache", 3600, json.dumps(cached_scripts))
                    logger.info("Saved scripts to Redis cache (3600s TTL)")
                except Exception as cache_err:
                    logger.error(f"Failed to cache scripts in Redis: {cache_err}")
        except Exception as sheet_err:
            logger.error(f"Failed to fetch scripts from Google Sheets: {sheet_err}")
            
    if not cached_scripts:
        try:
            with open("api/compliance_scripts.json", "r", encoding="utf-8") as f:
                cached_scripts = json.load(f)
        except Exception:
            cached_scripts = {}
            
    response_data = {}
    for code in codes_list:
        response_data[code] = cached_scripts.get(code, f"[Script {code} not found]")
        
    return response_data


@app.get("/api/v1/rules")
async def get_rules(codes: str):
    """
    Get business rules from Google Sheets (cached in Redis).
    Query parameter `codes` is a comma-separated list of rule codes (e.g. "RNE.01,RNE.02").
    """
    start_time = time.time()
    resp = None
    try:
        resp = await get_rules_inner(codes)
        return resp
    finally:
        try:
            latency = int((time.time() - start_time) * 1000)
            request_log = RequestLog(
                trace_id=f"api-{uuid.uuid4()}",
                timestamp=datetime.utcnow(),
                conversation_id="rules_fetch",
                contact_id="rules_fetch",
                channel="respond_api",
                user_text=f"GET /rules?codes={codes}",
                mcp_response=f"Rules retrieved: {list(resp.keys()) if resp else 'Error'}",
                status=ResponseStatus.OK,
                latency_ms=latency,
                category="rules_fetch"
            )
            await telemetry_service.log_request(request_log)
        except Exception as log_err:
            logger.error(f"Error logging rules telemetry: {log_err}")

async def get_rules_inner(codes: str):
    codes_list = [c.strip().upper().replace(" ", "") for c in codes.split(",") if c.strip()]
    if not codes_list:
        raise HTTPException(status_code=400, detail="Missing codes query parameter")
        
    redis = None
    try:
        redis = await get_redis_client()
    except Exception as redis_err:
        logger.warning(f"Redis client not available in get_rules: {redis_err}")
        
    cached_rules = None
    if redis:
        try:
            cached_val = await redis.get("google_sheets:rules_cache")
            if cached_val:
                cached_rules = json.loads(cached_val.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error reading rules cache from Redis: {e}")
            
    if not cached_rules:
        logger.info(f"🔄 Fetching rules from Google Sheet ID: {settings.GOOGLE_SHEET_ID_REGLAS}")
        from .google_sheets_service import google_sheets_service
        try:
            cached_rules = await google_sheets_service.fetch_business_rules(settings.GOOGLE_SHEET_ID_REGLAS)
            if cached_rules and redis:
                try:
                    await redis.setex("google_sheets:rules_cache", 3600, json.dumps(cached_rules))
                    logger.info("Saved rules to Redis cache (3600s TTL)")
                except Exception as cache_err:
                    logger.error(f"Failed to cache rules in Redis: {cache_err}")
        except Exception as sheet_err:
            logger.error(f"Failed to fetch rules from Google Sheets: {sheet_err}")
            
    if not cached_rules:
        try:
            with open("api/compliance_rules.json", "r", encoding="utf-8") as f:
                cached_rules = json.load(f)
            logger.info("Loaded rules from local fallback compliance_rules.json")
        except Exception as e:
            logger.error(f"Failed to load local fallback rules: {e}")
            cached_rules = {}
        
    response_data = {}
    for code in codes_list:
        response_data[code] = cached_rules.get(code, f"[Rule {code} not found]")
        
    return response_data


@app.post("/api/v1/scripts/sync")
async def sync_scripts_and_rules():
    """Manual sync to clear cache and force reloading sheets"""
    redis = None
    try:
        redis = await get_redis_client()
    except Exception as redis_err:
        raise HTTPException(status_code=500, detail=f"Redis not available: {redis_err}")
        
    try:
        await redis.delete("google_sheets:scripts_cache")
        await redis.delete("google_sheets:rules_cache")
        await redis.delete("google_sheets:status_cache")
        await redis.delete("google_sheets:bill_status_cache")
        logger.info("Cleared scripts, rules, status, and bill status caches in Redis")
        return {"status": "success", "message": "All Google Sheet caches cleared. Next request will fetch fresh data from Google Sheets."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {e}")


# ============================================================
# Error Handlers
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
