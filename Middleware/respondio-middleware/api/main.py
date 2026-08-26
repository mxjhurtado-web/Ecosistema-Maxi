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
    TopupCheckResponse,
    AgentInteractRequest,
    AgentInteractResponse,
    DecisionLogEntry,
    ResetSessionRequest,
    ResetSessionResponse
)
from .config import settings
from .mcp_client import mcp_client
from .telemetry import telemetry_service
from .decision_logger import save_decision_log
from .admin_api import router as admin_router, public_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def match_keyword_safe(keyword: str, text: str) -> bool:
    kw = keyword.lower().strip()
    txt = text.lower()
    if len(kw) <= 4 and kw.isalnum():
        import re
        return bool(re.search(r'\b' + re.escape(kw) + r'\b', txt))
    return kw in txt

async def log_fsm_decision(
    contact_id: str,
    active_agent: str,
    user_input: str,
    script_text: str,
    winning_rule_id: str = "RNE.AUTOMATED",
    derivacion: Optional[str] = None
):
    """Helper to persist FSM decision audit entries for Reflex Dashboard (/decision-logs)"""
    try:
        c_id = contact_id if contact_id and contact_id not in ["-1", "contact.id", "$contact.id"] else "simulator"
        
        # Determine Virtual Queue (Cola A vs Cola B) per AUD.03 & COL.02
        v_queue = "Cola B"
        txt_check = (script_text or "") + " " + (active_agent or "") + " " + (winning_rule_id or "") + " " + (derivacion or "")
        if any(k in txt_check for k in ["SC.030", "SC.038", "Fraude", "BSA", "Estafa", "Cola A", "DerivacionFraudes", "DerivacionBSA"]):
            v_queue = "Cola A"

        entry = DecisionLogEntry(
            trace_id=f"dec-{uuid.uuid4()}",
            contact_id=c_id,
            case_id=c_id,
            active_agent=active_agent or "Max",
            timestamp=datetime.utcnow(),
            profile="CLIENTE",
            user_input=user_input or "N/A",
            winning_rule_id=winning_rule_id,
            script_text=script_text or "",
            current_state="PROCESSING",
            next_state="COMPLETED",
            next_action="ASSIGN_TO_TEAM" if derivacion and derivacion != "NA" else "OFFER_HELP",
            destination_team=derivacion if derivacion != "NA" else None,
            virtual_queue=v_queue
        )
        await save_decision_log(entry)
    except Exception as err:
        logger.error(f"Failed to log FSM decision: {err}")
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
        
        # Pre-fetch and cache official scripts from Google Sheets (18VE3tdVt4E-eNrf0dD4zlk1aLV2nfv9_ncdUvLPaNic)
        try:
            from .google_sheets_service import google_sheets_service
            from .shared_logic import update_compliance_scripts_cache
            live_scripts = await google_sheets_service.fetch_official_scripts(settings.GOOGLE_SHEET_ID_SCRIPTS)
            if live_scripts:
                update_compliance_scripts_cache(live_scripts)
                logger.info(f"✅ Dynamic Scripts pre-loaded from Google Sheets: {len(live_scripts)} scripts active")
        except Exception as script_err:
            logger.warning(f"⚠️ Dynamic script pre-fetch skipped: {script_err}")
        
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
    derivacion = "NA"
    
    redis = None
    try:
        redis = await get_redis_client()
    except Exception as re_err:
        logger.warning(f"Redis client connection failed: {re_err}")
    
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
                if not user_msg_text and inner_msg.get("attachment") and isinstance(inner_msg["attachment"], dict):
                    user_msg_text = inner_msg["attachment"].get("description")
        
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
                await redis.set(f"contact:last_msg:{contact_id}", user_msg_text.strip(), ex=3600)
                
                # Cache mappings for self-healing contact_id fallback
                text_hash = f"text_to_contact:{user_msg_text.strip().lower()}"
                await redis.set(text_hash, contact_id, ex=30)  # 30 seconds TTL
                await redis.set("global:last_active_contact", contact_id, ex=60)  # 60 seconds TTL
                
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
            latency_ms=0,
            derivacion="NA"
        )

    # If not global webhook, parse as standard RespondioRequest
    try:
        from .models import RespondioRequest
        request = RespondioRequest(**request)
    except Exception as parse_err:
        logger.error(f"Failed to parse custom webhook request: {parse_err}")
        raise HTTPException(status_code=422, detail=f"Validation error: {parse_err}")

    # Clean braces from contact_id and conversation_id (e.g. "{{ 495413807 }}" -> "495413807")
    if request.contact_id:
        cleaned_id = request.contact_id.replace("{", "").replace("}", "").strip()
        if not cleaned_id.startswith("$"):
            request.contact_id = cleaned_id
            
    if request.conversation_id:
        cleaned_conv = request.conversation_id.replace("{", "").replace("}", "").strip()
        if not cleaned_conv.startswith("$"):
            request.conversation_id = cleaned_conv

    logger.info(
        f"📨 Webhook received",
        extra={
            "trace_id": trace_id,
            "conversation_id": request.conversation_id,
            "channel": request.channel
        }
    )

    # Retrieve user_text from cache if empty or literal template string
    user_text_val = (request.user_text or "").strip()
    if not user_text_val or "{{" in user_text_val or "$" in user_text_val:
        if redis and request.contact_id:
            try:
                cached_bytes = await redis.get(f"contact:session_text:{request.contact_id}")
                if cached_bytes:
                    cached_text = cached_bytes.decode('utf-8').strip()
                    last_msg = cached_text.split("\n")[-1].strip()
                    if last_msg:
                        logger.info(f"💾 Retrieved user_text from Redis cache: '{last_msg}'")
                        request.user_text = last_msg
            except Exception as cache_err:
                logger.warning(f"Failed to fetch cached user_text from Redis: {cache_err}")

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
                                latency_ms=total_latency_ms,
                                derivacion="NA"
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
            # Clear state machine variables in Redis
            if redis:
                try:
                    await redis.delete(f"session:state:{request.contact_id}")
                    await redis.delete(f"session:codigo_envio:{request.contact_id}")
                    await redis.delete(f"session:perfil:{request.contact_id}")
                except Exception as clear_err:
                    logger.warning(f"Failed to clear session state keys: {clear_err}")
                    
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
                from .chat_history_helper import append_message_to_history
                await append_message_to_history(redis, request.conversation_id, "bot_max", mcp_response)
            except Exception as hist_err:
                logger.warning(f"Failed to cache greeting in chat history: {hist_err}")

            return RespondioResponse(
                status=ResponseStatus.OK,
                reply_text=mcp_response,
                trace_id=trace_id,
                latency_ms=total_latency_ms,
                derivacion="NA"
            )

        # --- DETERMINISTIC CASCADING STATE MACHINE ---
        state_key = f"session:state:{request.contact_id}"
        code_key = f"session:codigo_envio:{request.contact_id}"
        profile_key = f"session:perfil:{request.contact_id}"
        attempts_key = f"session:attempts:{request.contact_id}"
        
        current_state_bytes = await redis.get(state_key) if redis else None
        current_state = current_state_bytes.decode('utf-8') if current_state_bytes else None
        
        user_text_clean = (request.user_text or "").strip()
        detected_code = extraer_codigo_router(user_text_clean)
        
        # 1. If we detect a tracking code anywhere in the user text, we jump straight to tracking mode
        if detected_code:
            logger.info(f"🔍 Tracking code '{detected_code}' detected. Starting status check flow.")
            profile_in_text = detect_profile_from_text(user_text_clean)
            
            # Single-Turn Extraction: If user text contains code AND profile AND (name or info), process immediately
            if profile_in_text:
                # Extract potential name (words excluding keywords and code)
                clean_name_words = [w for w in re.findall(r'\b[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}\b', user_text_clean) 
                                    if w.lower() not in ["hola", "buenos", "dias", "tardes", "noches", "estatus", "status", "envio", "cruz", "codigo", "folio", "remitente", "beneficiario", "para", "de", "mi", "el", "la", "los", "las", "un", "una"]]
                possible_name = " ".join(clean_name_words).strip()
                
                if len(possible_name) >= 3:
                    logger.info(f"⚡ Single-Turn Status Check triggered: Code={detected_code}, Profile={profile_in_text}, Name='{possible_name}'")
                    status_req = StatusCheckRequest(
                        codigo_envio=detected_code,
                        perfil=profile_in_text,
                        contact_id=request.contact_id,
                        contact_name=request.contact_name,
                        user_text=user_text_clean,
                        nombre_remitente=possible_name if profile_in_text == "REMITENTE" else None,
                        nombre_beneficiario=possible_name if profile_in_text == "BENEFICIARIO" else None,
                        metadata=request.metadata
                    )
                    status_resp = await check_transaction_status_inner(status_req, x_webhook_secret=settings.WEBHOOK_SECRET)
                    mcp_response = await translate_script_if_needed(status_resp.reply_text, request.user_text)
                    total_latency_ms = int((time.time() - start_time) * 1000)
                    return RespondioResponse(
                        status=ResponseStatus.OK,
                        reply_text=mcp_response,
                        trace_id=trace_id,
                        latency_ms=total_latency_ms,
                        derivacion=status_resp.derivacion
                    )
            if redis:
                await redis.set(code_key, detected_code, ex=3600)
                await redis.set(state_key, "AWAITING_PROFILE", ex=3600)
                await redis.set(attempts_key, "0", ex=3600)
            
            scripts = get_compliance_scripts()
            mcp_response = scripts.get("SC.003", "¿Es usted el remitente o el beneficiario?")
            derivacion = "NA"
            
            # Translate if needed
            mcp_response = await translate_script_if_needed(mcp_response, request.user_text)
            total_latency_ms = int((time.time() - start_time) * 1000)
            
            # Structured chat history caching
            try:
                from .chat_history_helper import append_message_to_history
                await append_message_to_history(redis, request.conversation_id, "bot_max", mcp_response)
            except Exception as hist_err:
                logger.warning(f"Failed to cache tracking start in chat history: {hist_err}")
 
            return RespondioResponse(
                status=ResponseStatus.OK,
                reply_text=mcp_response,
                trace_id=trace_id,
                latency_ms=total_latency_ms,
                derivacion=derivacion
            )
            
        # 2. If we are currently in the AWAITING_PROFILE state
        elif current_state == "AWAITING_PROFILE":
            profile = detect_profile_from_text(user_text_clean)
                
            if profile:
                logger.info(f"👤 Profile identified as {profile} for contact {request.contact_id}")
                if redis:
                    await redis.set(profile_key, profile, ex=3600)
                    await redis.set(state_key, "AWAITING_NAME", ex=3600)
                    await redis.set(attempts_key, "0", ex=3600)
                
                saved_code_bytes = await redis.get(code_key) if redis else None
                saved_code = saved_code_bytes.decode('utf-8') if saved_code_bytes else ""
                
                scripts = get_compliance_scripts()
                agent_name = request.metadata.get("agent_name")
                
                if agent_name == "VerificadorEstatusRecargas":
                    mcp_response = scripts.get("SC.010.2", "Para continuar, necesito validar algunos datos. ¿Me comparte el número telefónico de la persona quien hizo la recarga y el número al que se realizó, por favor?.")
                elif saved_code.upper().startswith("TRK"):
                    mcp_response = scripts.get("SC.010.1", "Para continuar, necesito validar algunos datos. ¿Me comparte el nombre completo de la persona que realizó el pago y el nombre de la compañía, por favor?.")
                else:
                    mcp_response = scripts.get("SC.008", "Para verificar su identidad, por favor indique su nombre completo.")
                
                derivacion = "NA"
            else:
                attempts_val = await redis.get(attempts_key) if redis else None
                attempts = int(attempts_val.decode('utf-8')) if attempts_val else 0
                attempts += 1
                
                if attempts >= 2:
                    if redis:
                        await redis.set(attempts_key, "0", ex=3600)
                    scripts = get_compliance_scripts()
                    mcp_response = scripts.get("SC.002", "Lo transferiré con uno de nuestros asesores...")
                    derivacion = "Servicio al Cliente"
                else:
                    if redis:
                        await redis.set(attempts_key, str(attempts), ex=3600)
                    scripts = get_compliance_scripts()
                    mcp_response = scripts.get("SC.003", "¿Es usted remitente, beneficiario o agente?")
                    derivacion = "NA"
                
            mcp_response = await translate_script_if_needed(mcp_response, request.user_text)
            total_latency_ms = int((time.time() - start_time) * 1000)
            
            # Structured chat history caching
            try:
                from .chat_history_helper import append_message_to_history
                await append_message_to_history(redis, request.conversation_id, "bot_max", mcp_response)
            except Exception as hist_err:
                logger.warning(f"Failed to cache profile response in chat history: {hist_err}")
 
            return RespondioResponse(
                status=ResponseStatus.OK,
                reply_text=mcp_response,
                trace_id=trace_id,
                latency_ms=total_latency_ms,
                derivacion=derivacion
            )
            
        # 3. If we are currently in the AWAITING_NAME state
        elif current_state == "AWAITING_NAME":
            saved_code_bytes = await redis.get(code_key) if redis else None
            saved_profile_bytes = await redis.get(profile_key) if redis else None
            
            saved_code = saved_code_bytes.decode('utf-8') if saved_code_bytes else None
            saved_profile = saved_profile_bytes.decode('utf-8') if saved_profile_bytes else None
            
            if saved_code and saved_profile:
                logger.info(f"⚡ Executing database status check for code {saved_code}, profile {saved_profile}, name/info: {user_text_clean}")
                
                # Check if it's a Topup check
                if request.metadata.get("agent_name") == "VerificadorEstatusRecargas":
                    phones = re.findall(r'\b\d{7,15}\b', user_text_clean)
                    cust_phone = phones[0] if len(phones) > 0 else user_text_clean
                    cell_phone = phones[1] if len(phones) > 1 else cust_phone
                    
                    topup_req = TopupCheckRequest(
                        contact_id=request.contact_id,
                        user_text=user_text_clean,
                        transaction_id=saved_code,
                        customer_number=cust_phone,
                        cellular_number=cell_phone,
                        perfil=saved_profile or "CLIENTE",
                        metadata=request.metadata
                    )
                    status_resp = await check_topup_status_inner(topup_req, x_webhook_secret=settings.WEBHOOK_SECRET)
                # Check if it's a Bill check (starts with TRK)
                elif saved_code.upper().startswith("TRK"):
                    bill_req = BillCheckRequest(
                        tracking_number=saved_code,
                        contact_id=request.contact_id,
                        contact_name=request.contact_name,
                        user_text=user_text_clean,
                        nombre_completo_customer=user_text_clean,
                        biller=user_text_clean,
                        perfil=saved_profile or "CLIENTE",
                        metadata=request.metadata
                    )
                    status_resp = await check_bill_status_inner(bill_req, x_webhook_secret=settings.WEBHOOK_SECRET)
                else:
                    status_req = StatusCheckRequest(
                        codigo_envio=saved_code,
                        perfil=saved_profile,
                        contact_id=request.contact_id,
                        contact_name=request.contact_name,
                        user_text=user_text_clean,
                        nombre_remitente=user_text_clean if saved_profile == "REMITENTE" else None,
                        nombre_beneficiario=user_text_clean if saved_profile == "BENEFICIARIO" else None,
                        metadata=request.metadata
                    )
                    status_resp = await check_transaction_status_inner(status_req, x_webhook_secret=settings.WEBHOOK_SECRET)
                
                derivacion = status_resp.derivacion
                
                # If validation succeeded or it reached max attempts, clear the state
                if status_resp.validation_success or status_resp.derivacion != "NA":
                    if redis:
                        await redis.delete(state_key)
                        await redis.delete(code_key)
                        await redis.delete(profile_key)
                        await redis.delete(attempts_key)
                    
                total_latency_ms = int((time.time() - start_time) * 1000)
                mcp_response = await translate_script_if_needed(status_resp.reply_text, request.user_text)
                
                # Structured chat history caching
                try:
                    from .chat_history_helper import append_message_to_history
                    await append_message_to_history(redis, request.conversation_id, "bot_max", mcp_response)
                except Exception as hist_err:
                    logger.warning(f"Failed to cache database status response in chat history: {hist_err}")
 
                return RespondioResponse(
                    status=ResponseStatus.OK,
                    reply_text=mcp_response,
                    trace_id=trace_id,
                    latency_ms=total_latency_ms,
                    derivacion=derivacion
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
        # Parse transfer tag for Respond.io human routing if present
        import re
        handoff_match = re.search(r"\[TRANSFER:\s*([^\]]+)\]", mcp_response or "")
        if handoff_match:
            derivacion = handoff_match.group(1).strip()
            mcp_response = re.sub(r"\[TRANSFER:\s*[^\]]+\]", "", mcp_response).strip()
            logger.info(f"🔄 Handoff parsed from response: {derivacion}")

        return RespondioResponse(
            status=status,
            reply_text=mcp_response,
            trace_id=trace_id,
            latency_ms=total_latency_ms,
            derivacion=derivacion
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


def detect_profile_from_text(text: str) -> Optional[str]:
    user_p_lower = text.lower().strip(".,!?¡¿() ")
    
    if user_p_lower == "1":
        return "REMITENTE"
    elif user_p_lower == "2":
        return "BENEFICIARIO"
    elif user_p_lower == "3":
        return "AGENTE"
        
    KEYWORDS_REMITENTE = [
        "remitente", "sender", "envia", "envió", "envio", "envié", 
        "hice un envio", "hice un envío", "hice el envio", "hice el envío",
        "hice una recarga", "hice un pago", "pago de servicio", "recarga telefonica",
        "yo envie", "yo envié", "hice la transferencia", "enviar dinero",
        "soy quien envio", "soy quien envió", "fui quien envio", "fui quien envió"
    ]
    KEYWORDS_BENEFICIARIO = [
        "beneficiario", "receptor", "recipient", "receiver", "recibe", "beneficiary",
        "me enviaron", "me mandaron", "me van a enviar", "me van a mandar",
        "soy quien recibe", "voy a recibir", "espero un envio", "espero el envio",
        "espero un envío", "espero el envío", "recibir dinero"
    ]
    KEYWORDS_AGENTE = [
        "agente", "agent", "soy agente", "soy el agente", "agente autorizado", "agente de maxi"
    ]
    
    if any(k in user_p_lower for k in KEYWORDS_REMITENTE):
        return "REMITENTE"
    elif any(k in user_p_lower for k in KEYWORDS_BENEFICIARIO):
        return "BENEFICIARIO"
    elif any(k in user_p_lower for k in KEYWORDS_AGENTE):
        return "AGENTE"
        
def is_no_more_help_needed(text: str) -> bool:
    if not text:
        return False
    t = text.lower().strip(".,!?¡¿() ")
    
    closure_phrases = [
        "no", "no gracias", "no, gracias", "no muchas gracias", "no, muchas gracias",
        "ninguna", "ninguno", "ningun", "ningún", "nada", "nada mas", "nada más",
        "seria todo", "sería todo", "todo bien", "todo claro", "gracias", "muchas gracias",
        "mil gracias", "listo", "ya quedo", "ya quedó", "eso es todo", "eso sería todo",
        "gracias por la ayuda", "ok", "ok gracias", "vale", "perfecto",
        "no thank you", "no thanks", "no, thank you", "thanks", "thank you",
        "that is all", "that would be all", "all good", "bye", "adios", "adiós"
    ]
    if t in closure_phrases:
        return True
        
    for p in ["seria todo", "sería todo", "eso es todo", "eso sería todo", "no gracias", "no, gracias", "ninguna duda", "ningun problema", "ningún problema"]:
        if p in t:
            return True
            
    if len(t) < 35 and any(w in t for w in ["gracias", "thank", "ok", "listo", "adios", "bye", "chao", "seria todo", "sería todo"]):
        return True
        
    return False


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
    clean_name = (contact_name or "").strip()
    if clean_name and clean_name.lower() != "cliente":
        sc33_text = sc33_template.replace("[Nombre]", clean_name)
    else:
        sc33_text = sc33_template.replace("[Nombre]", "").strip()
    sc33_text = sc33_text.replace("“", "").replace("”", "").replace('"', "").strip()
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
        if "{{" in v_str or "}}" in v_str:
            cleaned = v_str.replace("{", "").replace("}", "").strip()
            if cleaned.startswith("$"):
                return None
            v_str = cleaned
        if (v_str in [",", "%", "", "null", "None"] or 
            v_str.startswith("$")):
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
                    # Si el código se envió explícitamente en el JSON de la llamada HTTP, es fresco
                    if request.codigo_envio or (request.metadata and request.metadata.get("codigo_envio")):
                        code_fresh = True
                    else:
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
                
        scripts_dict = get_compliance_scripts()
        if attempts >= 2:
            if redis:
                try:
                    await redis.set(attempts_key, "0", ex=3600)
                except Exception as e:
                    logger.error(f"Error resetting attempts in Redis: {e}")
            sc12 = scripts_dict.get("SC.012", "No fue posible procesar su solicitud con la clave proporcionada. Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
            sc12 = await translate_script_if_needed(sc12, user_text)
            return StatusCheckResponse(
                status="success",
                reply_text=sc12,
                derivacion="Servicio al Cliente",
                validation_success=False
            )
        else:
            sc29 = scripts_dict.get("SC.029", "No he podido localizar la información con los datos que me ha proporcionado. Por favor, confírmelos y escríbalos nuevamente para realizar una nueva consulta.")
            sc29 = await translate_script_if_needed(sc29, user_text)
            return StatusCheckResponse(
                status="success",
                reply_text=sc29,
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
                    
                    explicit_sender = bool(request.nombre_remitente or (request.metadata and request.metadata.get("nombre_remitente")))
                    explicit_beneficiary = bool(request.nombre_beneficiario or (request.metadata and request.metadata.get("nombre_beneficiario")))
                    
                    def is_fresh(name_str: Optional[str], is_explicit: bool = False) -> bool:
                        if not name_str:
                            return False
                        if is_explicit:
                            return True
                        words = [w for w in re.findall(r'\w+', name_str.upper()) if len(w) > 2]
                        if not words:
                            return False
                        return any(w in session_text or w in clean_user_text for w in words)
                        
                    if user_sender and not is_fresh(user_sender, explicit_sender):
                        logger.info(f"🚫 Ignoring old/historical sender name {user_sender} for contact {contact_id}")
                        user_sender = None
                        
                    if user_beneficiary and not is_fresh(user_beneficiary, explicit_beneficiary):
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
            logger.info(f"🔍 Validating identity: perfil={perfil}, user_sender={user_sender}, user_beneficiary={user_beneficiary}")
            if perfil == "REMITENTE":
                valid_identity = match_names(user_sender, db_sender) if user_sender else False
            elif perfil == "BENEFICIARIO":
                valid_identity = match_names(user_beneficiary, db_beneficiary) if user_beneficiary else False
            else: # CLIENTE or None
                match_sender = match_names(user_sender, db_sender) if user_sender else False
                match_ben = match_names(user_beneficiary, db_beneficiary) if user_beneficiary else False
                valid_identity = match_sender or match_ben
                
            if not valid_identity:
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
    if status_rules and isinstance(status_rules, dict):
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
                    if check_department_hours("CUMPLIMIENTO", ct_now):
                        derivacion = "Cumplimiento"
                        scripts = get_compliance_scripts()
                        reply_text = scripts.get("SC.011.1", "Su operación está siendo procesada por nuestro departamento de Cumplimiento (BSA/KYC). Lo transferiré con un asesor para validar su documentación.")
                    else:
                        derivacion = "Fuera de Horario Depto"
                        reply_text = "Entiendo su solicitud. Su caso requiere atención del área de Cumplimiento (BSA) y por el momento no se encuentra disponible. Un asesor se comunicará en cuanto reinicien operaciones."
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

    await log_fsm_decision(
        contact_id=contact_id,
        active_agent="VerificadorEstatus",
        user_input=user_text or codigo_envio or "Rastreo de Giro",
        script_text=reply_text,
        winning_rule_id="RNE.STATUS_CHECK",
        derivacion=derivacion
    )

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
        if resp:
            await log_fsm_decision(
                contact_id=request.contact_id or "unknown",
                active_agent="VerificadorPagoBill",
                user_input=getattr(request, "tracking_number", None) or getattr(request, "user_text", None) or "Bill Check",
                script_text=resp.reply_text,
                winning_rule_id="RNE.BILL_CHECK",
                derivacion=resp.derivacion
            )
        return resp
    except Exception as e:
        status_val = ResponseStatus.ERROR
        error_msg = str(e)
        raise e
    finally:
        try:
            latency = int((time.time() - start_time) * 1000)
            tracking = getattr(request, "tracking_number", getattr(request, "contact_id", "unknown"))
            request_log = RequestLog(
                trace_id=f"api-{uuid.uuid4()}",
                timestamp=datetime.utcnow(),
                conversation_id=getattr(request, "contact_id", "unknown"),
                contact_id=tracking,
                channel="respond_api",
                user_text=f"Bill Check: {tracking}",
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
        if "{{" in v_str or "}}" in v_str:
            cleaned = v_str.replace("{", "").replace("}", "").strip()
            if cleaned.startswith("$"):
                return None
            v_str = cleaned
        if (v_str in [",", "%", "", "null", "None"] or 
            v_str.startswith("$")):
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
    if status_rules and isinstance(status_rules, list):
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
            cid = getattr(request, "contact_id", getattr(request, "conversation_id", "unknown"))
            rating_val = getattr(request, "rating", getattr(request, "score", 0))
            request_log = RequestLog(
                trace_id=f"api-{uuid.uuid4()}",
                timestamp=datetime.utcnow(),
                conversation_id=cid,
                contact_id=cid,
                channel="respond_api",
                user_text=f"CSAT Log: Rating={rating_val}",
                mcp_response=getattr(resp, "message", getattr(resp, "reply_text", "")) if resp else error_msg,
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
            next_script = "SC.036"
            next_text = resolve_script_text("SC.036")
            if request.rating and request.rating < 3 and not request.comment:
                next_script = "SC.035"
                next_text = resolve_script_text("SC.035")
                
            return CSATLogResponse(
                status="success",
                message=next_text or "CSAT logged successfully to Google Sheets"
            )
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
        if resp:
            await log_fsm_decision(
                contact_id=request.contact_id or "unknown",
                active_agent="VerificadorEstatusRecargas",
                user_input=getattr(request, "transaction_id", None) or getattr(request, "user_text", None) or "Topup Check",
                script_text=resp.reply_text,
                winning_rule_id="RNE.TOPUP_CHECK",
                derivacion=resp.derivacion
            )
        return resp
    except Exception as e:
        status_val = ResponseStatus.ERROR
        error_msg = str(e)
        raise e
    finally:
        try:
            latency = int((time.time() - start_time) * 1000)
            phone_txn = getattr(request, "cellular_number", getattr(request, "transaction_id", getattr(request, "contact_id", "unknown")))
            request_log = RequestLog(
                trace_id=f"api-{uuid.uuid4()}",
                timestamp=datetime.utcnow(),
                conversation_id=getattr(request, "contact_id", "unknown"),
                contact_id=phone_txn,
                channel="respond_api",
                user_text=f"Topup Check: {phone_txn}",
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
        if "{{" in v_str or "}}" in v_str:
            cleaned = v_str.replace("{", "").replace("}", "").strip()
            if cleaned.startswith("$"):
                return None
            v_str = cleaned
        if (v_str in [",", "%", "", "null", "None"] or 
            v_str.startswith("$")):
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
    record = None
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
    if status_rules and isinstance(status_rules, list):
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
            if cached_scripts:
                from .shared_logic import update_compliance_scripts_cache
                update_compliance_scripts_cache(cached_scripts)
                if redis:
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


async def run_ocr_on_media(media_url: str) -> Optional[Dict[str, Any]]:
    import base64
    try:
        redis = await get_redis_client()
        redis_key = await redis.get("config:mcp:gemini_api_key")
        api_key = redis_key.decode('utf-8') if redis_key else settings.GEMINI_API_KEY
        
        if not api_key:
            logger.error("❌ Gemini API Key not found for OCR")
            return None
            
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(media_url, timeout=15)
            if resp.status_code != 200:
                logger.error(f"❌ Failed to download media from {media_url}: status {resp.status_code}")
                return None
            img_bytes = resp.content
            content_type = resp.headers.get("content-type", "image/png")
            
        b64_img = base64.b64encode(img_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        prompt = (
            "Determine if this image is a money transfer receipt/ticket or transaction proof. "
            "If it is, extract the following fields in JSON format:\n"
            "- is_receipt: boolean (true if it is a transaction ticket/receipt/invoice)\n"
            "- tracking_code: string (the transaction reference/claim/confirmation code, e.g. CE... or TRK...)\n"
            "- sender_name: string (the name of the person sending the money)\n"
            "- beneficiary_name: string (the name of the person receiving the money)\n"
            "- amount: string (the transaction amount and currency)\n"
            "Respond ONLY with the JSON object."
        )
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": content_type,
                            "data": b64_img
                        }
                    }
                ]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                res_json = resp.json()
                text_out = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                try:
                    return json.loads(text_out)
                except Exception as json_err:
                    logger.error(f"❌ Failed to parse Gemini OCR response JSON: {json_err}. Raw: {text_out}")
            else:
                logger.error(f"❌ Gemini OCR request failed with status: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"❌ Error during media OCR analysis: {e}")
    return None


async def clear_redis_session(redis, contact_id: str):
    logger.info(f"🧹 Clearing Redis session variables for contact {contact_id}")
    keys = [
        f"session:state:{contact_id}",
        f"session:perfil:{contact_id}",
        f"session:codigo_envio:{contact_id}",
        f"session:nombre_usuario:{contact_id}",
        f"session:attempts:{contact_id}",
        f"session:ocr_sender:{contact_id}",
        f"session:ocr_beneficiary:{contact_id}",
        f"session:csat:step:{contact_id}",
        f"session:csat:rating:{contact_id}",
        f"session:status:attempts:{contact_id}",
        f"name_attempts:{contact_id}",
        f"session:mo:code:{contact_id}",
        f"session:mo:amount:{contact_id}",
        f"session:mo:reason:{contact_id}",
        f"session:welcome_sent:{contact_id}",
    ]
    for k in keys:
        try:
            await redis.delete(k)
        except Exception as e:
            logger.error(f"Error deleting Redis key {k}: {e}")


@app.post("/api/v1/agent/interact", response_model=AgentInteractResponse)
async def agent_interact(
    request: AgentInteractRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    resp = await agent_interact_inner(request, x_webhook_secret, secret)
    
    # GARANTÍA ABSOLUTA DEL SCRIPT DE BIENVENIDA OBLIGATORIO EN EL PRIMER TURNO (CU.A1 / RNE.01) Y DEDUPLICACIÓN
    if resp and resp.reply_text:
        contact_id = request.contact_id.replace("{", "").replace("}", "").strip()
        
        # Always strip internal code prefixes like SC.030: or SC.037.1: from response
        from .shared_logic import strip_script_code_prefix
        resp.reply_text = strip_script_code_prefix(resp.reply_text)
        
        if contact_id not in ["contact.id", "contactid", "$contact.id", ""]:
            try:
                redis = await get_redis_client()
                welcome_key = f"session:welcome_sent:{contact_id}"
                welcome_sent = await redis.get(welcome_key)
                
                if not welcome_sent:
                    await redis.set(welcome_key, "1", ex=3600)
                    scripts = get_compliance_scripts()
                    cuA1_text = scripts.get("CU.A1", "Gracias por comunicarse a Maxitransfers.\n\nSoy Max, su asistente virtual. Para comenzar a ayudarle, ¿puede indicarme su nombre completo, por favor?\n\nAl continuar en este chat, acepta el tratamiento de sus datos bajo nuestra Política de Privacidad en www.maxitransfers.com/privacidad.\n\n• Por su seguridad, la sesión se cerrará automáticamente si pasa 10 minutos sin actividad.\n• Puede terminar esta conversación en cualquier momento enviando la palabra \"Finalizar\".\n• Si desea hablar con un asesor envíe el mensaje \"Hablar con un asesor\".").strip()
                    cuA1_trans = await translate_script_if_needed(cuA1_text, request.user_text, contact_id=contact_id)
                    cuA1_clean = strip_script_code_prefix(cuA1_trans)
                    
                    # Deduplication check: do not prepend CU.A1 if resp.reply_text already starts with it
                    if cuA1_clean and not resp.reply_text.startswith(cuA1_clean[:30]):
                        resp.reply_text = f"{cuA1_clean}\n\n{resp.reply_text}"
                        logger.info(f"✨ Mandatory Turn 1 Welcome Script (CU.A1) prepended for contact {contact_id}")
            except Exception as w_err:
                logger.error(f"⚠️ Error enforcing mandatory welcome script CU.A1: {w_err}")

    if resp:
        if resp.reply_text:
            from .shared_logic import strip_script_code_prefix
            resp.reply_text = strip_script_code_prefix(resp.reply_text)
            
        await log_fsm_decision(
            contact_id=request.contact_id,
            active_agent=request.agent_name,
            user_input=request.user_text,
            script_text=resp.reply_text,
            winning_rule_id="RNE.CASCADE_AGENT",
            derivacion=resp.derivacion
        )
    return resp

async def agent_interact_inner(
    request: AgentInteractRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    incoming_secret = x_webhook_secret or secret
    if incoming_secret != settings.WEBHOOK_SECRET:
        logger.warning("❌ Invalid webhook secret in agent interaction")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    contact_id = request.contact_id.replace("{", "").replace("}", "").strip()
    user_text = request.user_text.strip()
    agent_name = request.agent_name.strip()
    media_url = request.media_url
    if media_url:
        media_url = media_url.strip()
        if media_url in ["", "null", "None", "undefined"] or "{{" in media_url or "}}" in media_url or not media_url.lower().startswith("http"):
            media_url = None
            
    redis = await get_redis_client()
    
    # Restore media_url from global webhook cache if not provided in payload
    if not media_url and contact_id and contact_id not in ["contact.id", "contactid", "$contact.id", ""]:
        cached_img = await redis.get(f"contact:last_image:{contact_id}")
        if cached_img:
            media_url = cached_img.decode('utf-8').strip()
            logger.info(f"📸 Restored media_url from global webhook Redis cache: {media_url}")
            await redis.delete(f"contact:last_image:{contact_id}")
    
    # Self-healing fallback for unresolved or simulator contact_id in production
    if contact_id in ["contact.id", "contactid", "$contact.id", ""]:
        # 1. Try to map by exact user text match
        text_hash = f"text_to_contact:{user_text.lower()}"
        cached_contact = await redis.get(text_hash)
        if cached_contact:
            contact_id = cached_contact.decode('utf-8')
            logger.info(f"🔮 Self-healed contact_id from text cache: {contact_id}")
        else:
            # 2. Fall back to the globally last active contact
            last_active = await redis.get("global:last_active_contact")
            if last_active:
                contact_id = last_active.decode('utf-8')
                logger.info(f"🔮 Self-healed contact_id from global last active cache: {contact_id}")

    if contact_id == "-1":
        # Always reset attempts for simulator synthetic contact ID (-1) to prevent stuck failure sessions
        await redis.set(f"attempts:{contact_id}", "0", ex=3600)
            
    # Self-healing fallback for unresolved user_text placeholders (e.g. $message.message)
    user_text_lower_temp = user_text.lower().strip()
    if (
        not user_text or
        "$" in user_text_lower_temp or
        "{" in user_text_lower_temp or
        "message" in user_text_lower_temp or
        "text" in user_text_lower_temp
    ):
        cached_last_msg = await redis.get(f"contact:last_msg:{contact_id}")
        if cached_last_msg:
            user_text = cached_last_msg.decode('utf-8').strip()
            logger.info(f"🔮 Self-healed user_text placeholder to actual message from cache: '{user_text}'")

    logger.info(f"📨 Agent interaction request received for agent: {agent_name}, contact: {contact_id}, user_text: '{user_text}', media_url: {media_url}")
    
    # Store session text in Redis cache
    session_text_key = f"contact:session_text:{contact_id}"
    await redis.set(session_text_key, user_text, ex=3600)
    
    # Pre-load scripts
    scripts = get_compliance_scripts()

    # AIS.05: CONTROL DE LONGITUD DE ENTRADA / TOKEN DEFENSE (>500 CARACTERES)
    if len(user_text) > 500:
        logger.warning(f"🛡️ AIS.05 Token Defense activated: contact {contact_id} sent message of length {len(user_text)} chars (>500)")
        sc_defense = "Por favor, para poder ayudarle de manera clara y directa, le pedimos que resuma su consulta en un mensaje más breve."
        translated_defense = await translate_script_if_needed(sc_defense, user_text, contact_id=contact_id)
        return AgentInteractResponse(
            status="success",
            reply_text=translated_defense,
            derivacion="NA"
        )
    
    # Handle global commands or keywords (e.g. human transfer or ending)
    user_text_lower = user_text.lower()
    
    # Matriz Canónica de Palabras Clave desde "Palabras clave derivacion.xlsx"
    fraud_keywords = [
        "estafa", "fraude", "engaño", "phishing", "robo", "robado", "extorsión", "extorsion", "sospechosa", "sospechoso", 
        "víctima", "victima", "scam", "estafado", "estafada", "me estafaron", "me engañaron", "fraude del beneficiario", 
        "estafa del beneficiario", "beneficiario me estafó", "beneficiario me engañó", "víctima de fraude", 
        "víctima de estafa", "fui víctima", "me defraudaron", "me hicieron fraude", "fraude contra el remitente", 
        "estafa contra el remitente", "cancelar por fraude", "cancelar por estafa", "cancelar porque me estafaron", 
        "cancelar porque me engañaron", "detener por fraude", "detener por estafa", "recuperar dinero por estafa", 
        "cliente estafado", "cliente estafada", "cliente víctima", "cliente fue engañado", "cliente fue estafado", 
        "beneficiario estafó al cliente", "beneficiario engañó al cliente", "fraude en agencia", "estafa en agencia", 
        "agencia víctima de fraude", "agencia fue estafada", "defraudaron a la agencia", "engañaron a la agencia", 
        "beneficiario fraudulento", "beneficiario estafador", "incluir por fraude", "incluir por estafa", 
        "bloquear por fraude", "bloquear por estafa", "reportar por fraude", "reportar por estafa",
        "pidiendo mi clave", "pidiendo clave", "pidiendo mi número", "pidiendo mi numero", "pidiendo datos", 
        "me piden mi clave", "me piden clave", "me piden datos", "me están hablando por teléfono", 
        "me estan hablando por telefono", "me están llamando", "me estan llamando", "hablando por teléfono", 
        "hablando por telefono", "llamando por teléfono", "llamando por telefono", "llamada por teléfono", 
        "llamada por telefono", "pidiendo la clave", "pidiendo mi nip", "pidiendo nip", "pidiendo contraseña", 
        "pidiendo contrasena", "clave para depositarme", "clave para depositar", "llamada sospechosa", 
        "llamaron por teléfono", "llamaron por telefono", "me dijeron que me iban a depositar", 
        "pidiendo mi clave para depositarme", "pidiendo clave para depositarme", "hablando por teléfono pidiendo",
        "hablando por telefono pidiendo", "pidieron clave", "pidieron mi clave", "clave por teléfono", 
        "clave por telefono", "para depositarme", "pedir clave", "pedir mi clave", "pedirme la clave", 
        "pedirme mi clave", "pidiendo la clave", "pidiéndome la clave", "pidiéndome mi clave", 
        "pidiendome mi clave", "pidiendome la clave", "me hablaron por teléfono", "me hablaron por telefono"
    ]
    fraud_collecting_key = f"session:fraud_collecting:{contact_id}"
    is_fraud_collecting = await redis.get(fraud_collecting_key)
    bsa_keywords = [
        "bsa", "fraccionar", "fraccionamiento", "estructuración", "ctr", "deny list", "lista negra", 
        "lista restrictiva", "notificacion", "notificación", "usando mi perfil", "alguien usando mi perfil", 
        "notificacion a mi celular", "notificación a mi celular", "no reconozco", "no reconozco el envío", 
        "envío no reconocido", "envío desconocido", "no hice el envío", "yo no hice ese envío", "no autoricé", 
        "no autoricé el envío", "no autoricé la transacción", "transacción no autorizada", "envío no autorizado", 
        "transferencia no autorizada", "recibí un mensaje de un envío que no hice", "alguien usó mi cuenta", 
        "alguien está usando mi perfil", "uso indebido del perfil", "uso no autorizado", "actividad no reconocida", 
        "más de $10,000", "más de 10 mil dólares", "superior a $10,000", "superior a 10 mil dólares", 
        "supera los $10,000", "supera los 10 mil dólares", "envíos por más de $10,000", "envíos superiores a $10,000", 
        "más de 10 mil en un día", "se negó a proporcionar información", "se negó a proporcionar identificación", 
        "no quiere proporcionar identificación", "se negó a proporcionar ssn", "no quiere proporcionar ssn", 
        "se negó a proporcionar número de seguridad social", "no quiere proporcionar número de seguridad social", 
        "se negó a presentar comprobante de ingresos", "no quiere presentar comprobante de ingresos", 
        "se negó a proporcionar documentación", "no quiere proporcionar documentación", "información para ctr", 
        "documentación para ctr", "actividad sospechosa", "actividad inusual", "comportamiento sospechoso", 
        "comportamiento inusual", "operación sospechosa", "operaciones sospechosas", "operación inusual", 
        "operaciones inusuales", "envío sospechoso", "envíos sospechosos", "envío inusual", "envíos inusuales", 
        "patrón sospechoso", "patrón inusual", "comportamiento extraño", "comportamiento irregular", 
        "actividad irregular", "actividad fuera de lo normal", "comportamiento fuera de lo normal", 
        "operaciones fuera de lo normal", "movimientos sospechosos", "transacciones sospechosas", 
        "transacción inusual", "transacciones inusuales", "múltiples envíos", "muchos envíos", "frecuencia inusual", 
        "patrón de envíos", "comportamiento atípico", "actividad atípica", "cantidades fuertes", "comprobante de ingresos", 
        "varios envíos", "varios envios", "mil o mas", "mil o más", "montos altos", "montos elevados", "sospechoso"
    ]
    is_bsa_report = any(match_keyword_safe(k, user_text_lower) for k in bsa_keywords)

    if (any(match_keyword_safe(k, user_text_lower) for k in fraud_keywords) or is_fraud_collecting):
        logger.info(f"🚨 Fraud/BSA flow active for contact {contact_id} (collecting={bool(is_fraud_collecting)})")
        
        if not is_fraud_collecting:
            # Turn 1: Deliver SC.030 + Request 3 Security Fields + Send Google Chat Alert Immediately!
            await redis.set(fraud_collecting_key, "1", ex=3600)
            
            # Fire Google Chat Alert immediately on Turn 1 so it is NEVER missed!
            try:
                from .google_chat_service import google_chat_service
                cached_url = await redis.get(f"contact:last_image:{contact_id}")
                media_attach = ""
                if cached_url:
                    try:
                        url_str = cached_url.decode('utf-8')
                        if url_str and "http" in url_str:
                            emoji_attach = "📄" if ".pdf" in url_str.lower() else "📷"
                            media_attach = f"\n\n{emoji_attach} *Adjunto:* {url_str}"
                    except Exception:
                        pass

                
                alert_header = "🚨 *ALERTA CRÍTICA - BSA MONITORING / CUMPLIMIENTO*" if is_bsa_report else "🚨 *ALERTA CRÍTICA DE FRAUDE/ESTAFA*"
                alert_intent = "Reporte de Actividad Sospechosa / BSA" if is_bsa_report else "Reporte de Fraude / Estafa"

                alert_msg = (
                    f"{alert_header}\n\n"
                    f"👤 *Usuario:* Contacto #{contact_id}\n"
                    f"🎯 *Intención:* {alert_intent}\n"
                    f"📝 *Detalle:* {user_text}{media_attach}"
                )
                target_gchat_space = (
                    os.getenv("GOOGLE_CHATS_BSA_SPACE") or getattr(settings, "GOOGLE_CHATS_BSA_SPACE", None) or "spaces/AAQA3WL2JIk"
                ) if is_bsa_report else (
                    os.getenv("GOOGLE_CHATS_FRAUDES_SPACE") or getattr(settings, "GOOGLE_CHATS_FRAUDES_SPACE", None) or "spaces/AAQAQM9pDpg"
                )

                await google_chat_service.send_alert_detailed(
                    title="Alerta de Orbit",
                    message=alert_msg,
                    level="ERROR",
                    space_id=target_gchat_space
                )
                logger.info(f"✅ Google Chat Alert sent successfully to {target_gchat_space} for contact {contact_id} on Turn 1")
            except Exception as gchat_err:
                logger.error(f"⚠️ Failed to send Google Chat Fraud Alert on Turn 1: {gchat_err}")

            # RNE.50 / RNE.51: Select SC.030.1 (In Hours) vs SC.030.2 (Out of Hours)
            from zoneinfo import ZoneInfo
            ct_now = datetime.now(ZoneInfo("America/Chicago"))
            target_dept = "BSA MONITORING" if is_bsa_report else "PREVENCION DE FRAUDES"
            in_hours = check_department_hours(target_dept, ct_now)

            sc_turn1_code = "SC.030.1" if in_hours else "SC.030.2"
            default_sc_turn1 = (
                "Lamento lo sucedido, su solicitud debe ser atendida con alta prioridad.\n\n"
                "Por favor compártame la siguiente información:\n"
                "1. Su nombre completo.\n"
                "2. Los detalles de lo ocurrido con la situación que reporta.\n\n"
                "Si conoce la siguiente información:\n"
                "3. Clave(s) de envío(s) de dinero.\n"
                "4. Número de agencia desde donde se comunica."
            )
            sc_turn1_text = scripts.get(sc_turn1_code, default_sc_turn1)
            sc_turn1_trans = await translate_script_if_needed(sc_turn1_text, user_text, contact_id=contact_id)

            if is_bsa_report:
                logger.info(f"⚖️ Direct immediate handoff to DerivacionBSA for contact {contact_id} using {sc_turn1_code}")
                return AgentInteractResponse(
                    status="success",
                    reply_text=sc_turn1_trans,
                    derivacion="DerivacionBSA"
                )
            else:
                logger.info(f"🚨 Direct immediate handoff for Fraud for contact {contact_id} using {sc_turn1_code}")
                return AgentInteractResponse(
                    status="success",
                    reply_text=sc_turn1_trans,
                    derivacion="NA"
                )
        else:
            # Turn 2: Received details from user -> Clear Redis state -> Send Google Chat Update -> Reassign to DerivacionFraudes
            await redis.delete(fraud_collecting_key)

            try:
                from .google_chat_service import google_chat_service
                alert_header_t2 = "📝 *DETALLES ADICIONALES DE BSA RECIBIDOS*" if is_bsa_report else "📝 *DETALLES ADICIONALES DE FRAUDE RECIBIDOS*"
                alert_msg = (
                    f"{alert_header_t2}\n\n"
                    f"👤 *Usuario:* Contacto #{contact_id}\n"
                    f"📝 *Datos proporcionados por el cliente:* {user_text}"
                )
                target_gchat_space_t2 = (
                    os.getenv("GOOGLE_CHATS_BSA_SPACE") or getattr(settings, "GOOGLE_CHATS_BSA_SPACE", None) or "spaces/AAQA3WL2JIk"
                ) if is_bsa_report else (
                    os.getenv("GOOGLE_CHATS_FRAUDES_SPACE") or getattr(settings, "GOOGLE_CHATS_FRAUDES_SPACE", None) or "spaces/AAQAQM9pDpg"
                )
                await google_chat_service.send_alert_detailed(
                    title="Alerta de Orbit",
                    message=alert_msg,
                    level="INFO",
                    space_id=target_gchat_space_t2
                )
                logger.info(f"✅ Google Chat Fraud Details update sent for contact {contact_id}")
            except Exception as gchat_err:
                logger.error(f"⚠️ Failed to send Google Chat Fraud Details update: {gchat_err}")

            # RNE.50 / RNE.51 / RNE.60 / RNE.61: Evaluate Department Operating Hours
            from zoneinfo import ZoneInfo
            ct_now = datetime.now(ZoneInfo("America/Chicago"))
            in_fraudes_hours = check_department_hours("PREVENCION DE FRAUDES", ct_now)
            
            # Check if user provided details or if empty text
            has_details = len(user_text.strip()) > 3 and not any(k in user_text.lower() for k in ["no", "nada", "no tengo", "ninguno"])
            
            if has_details:
                sc_code = "SC.037"
                default_sc = "Gracias por la información proporcionada. Su reporte ya fue canalizado con el área especializada y un asesor se pondrá en contacto con usted a través de otro canal oficial.\n\nGracias por comunicarse con Maxitransfers, le atendió Max."
            else:
                sc_code = "SC.037.1"
                default_sc = "Debido a que su solicitud es de alta prioridad. Su reporte ya fue canalizado con el área especializada y un asesor se pondrá en contacto con usted a través de otro canal oficial.\n\nGracias por comunicarse con Maxitransfers, le atendió Max."
            
            sc_text = scripts.get(sc_code, default_sc)
            sc_translated = await translate_script_if_needed(sc_text, user_text, contact_id=contact_id)
            
            if in_fraudes_hours:
                # RNE.50 / RNE.60 / RNE.61: Close conversation immediately when Fraudes is open
                logger.info(f"🔒 RNE.50/60/61: Fraudes open. Delivering {sc_code} and closing conversation for contact {contact_id}")
                return AgentInteractResponse(
                    status="success",
                    reply_text=sc_translated,
                    derivacion="cerrar"
                )
            else:
                # RNE.51: Transfer to Customer Service when Fraudes is closed
                logger.info(f"🕒 RNE.51: Fraudes closed. Delivering {sc_code} and routing to Servicio al Cliente for contact {contact_id}")
                return AgentInteractResponse(
                    status="success",
                    reply_text=sc_translated,
                    derivacion="Servicio al Cliente"
                )
        
    # ------------------------------------------------------------
    # ENRUTADOR INTELIGENTE DE DEPARTAMENTOS (AGENTE COMUNICADOR / NOTIFICACIONES HTTP)
    # ------------------------------------------------------------
    from .google_chat_service import google_chat_service

    # Script homologado oficial de canalización departamental (SC.011)
    sc11_default = "Gracias por su información. He canalizado su solicitud con nuestro departamento correspondiente. Un asesor le dará seguimiento a la brevedad."

    # 1. Agent Oversight (IRS / Carta del IRS / Auditoría / Supervisión de Agente)
    oversight_keywords = ["irs", "oversight", "auditoría", "auditoria", "visita de inspección", "inspección", "inspeccion", "supervisión", "supervision", "carta del irs"]
    if any(match_keyword_safe(k, user_text_lower) for k in oversight_keywords):
        logger.info(f"🛡️ Agent Oversight request detected for contact {contact_id}: '{user_text[:50]}'")
        try:
            msg = f"🛡️ *REPORTE DE AGENT OVERSIGHT*\n\n👤 *Contacto:* Contacto #{contact_id}\n🎯 *Intención:* Requerimiento IRS / Auditoría\n📝 *Resumen:* {user_text}"
            await google_chat_service.send_alert_detailed(title="Alerta de Orbit", message=msg, level="WARNING", space_id="spaces/AAQAJiVCDAU")
            logger.info("✅ Google Chat Agent Oversight alert sent to spaces/AAQAJiVCDAU")
        except Exception as err:
            logger.error(f"Failed to send Agent Oversight alert: {err}")
        sc11_text = scripts.get("SC.011", sc11_default)
        translated = await translate_script_if_needed(sc11_text, user_text, contact_id=contact_id)
        return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    # 2. Capacitación (Manuales / POS / Entrenamientos)
    capacitacion_keywords = ["capacitación", "capacitacion", "manual de uso", "entrenamiento", "curso pos", "capacitar"]
    if any(match_keyword_safe(k, user_text_lower) for k in capacitacion_keywords):
        logger.info(f"🎓 Capacitación request detected for contact {contact_id}: '{user_text[:50]}'")
        try:
            msg = f"🎓 *REPORTE DE CAPACITACIÓN*\n\n👤 *Contacto:* Contacto #{contact_id}\n🎯 *Intención:* Consulta de Capacitación\n📝 *Resumen:* {user_text}"
            await google_chat_service.send_alert_detailed(title="Alerta de Orbit", message=msg, level="INFO", space_id="spaces/AAQAMKgsazw")
        except Exception as err:
            logger.error(f"Failed to send Capacitacion alert: {err}")
        sc11_text = scripts.get("SC.011", sc11_default)
        translated = await translate_script_if_needed(sc11_text, user_text, contact_id=contact_id)
        return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    # 3. Cumplimiento (Forma P-4 / AML / KYC)
    cumplimiento_keywords = ["forma p-4", "forma p4", "p-4", "p4", "cumplimiento", "aml", "kyc", "regulatorio"]
    if any(match_keyword_safe(k, user_text_lower) for k in cumplimiento_keywords):
        logger.info(f"⚖️ Cumplimiento request detected for contact {contact_id}: '{user_text[:50]}'")
        try:
            msg = f"⚖️ *REPORTE DE CUMPLIMIENTO (AML/KYC)*\n\n👤 *Contacto:* Contacto #{contact_id}\n🎯 *Intención:* Requerimiento de Cumplimiento\n📝 *Resumen:* {user_text}"
            await google_chat_service.send_alert_detailed(title="Alerta de Orbit", message=msg, level="WARNING", space_id="spaces/AAQAbvCUAko")
        except Exception as err:
            logger.error(f"Failed to send Cumplimiento alert: {err}")
        sc11_text = scripts.get("SC.011", sc11_default)
        translated = await translate_script_if_needed(sc11_text, user_text, contact_id=contact_id)
        return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    # 4. Cobranza (Comisiones / Saldos / Adeudos)
    cobranza_keywords = ["cobranza", "cobranzas", "comisión", "comision", "comisiones", "saldo pendiente", "adeudo", "estado de cuenta", "depósito retenido", "deposito retenido", "factura de agencia"]
    if any(match_keyword_safe(k, user_text_lower) for k in cobranza_keywords):
        logger.info(f"💰 Cobranza request detected for contact {contact_id}: '{user_text[:50]}'")
        try:
            msg = f"💰 *REPORTE DE COBRANZA*\n\n👤 *Contacto:* Contacto #{contact_id}\n🎯 *Intención:* Consulta de Cobranza / Comisiones\n📝 *Resumen:* {user_text}"
            await google_chat_service.send_alert_detailed(title="Alerta de Orbit", message=msg, level="INFO", space_id="spaces/AAQAcEu8NTc")
        except Exception as err:
            logger.error(f"Failed to send Cobranza alert: {err}")
        sc11_text = scripts.get("SC.011", sc11_default)
        translated = await translate_script_if_needed(sc11_text, user_text, contact_id=contact_id)
        return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    # 5. Cheques (Depósitos / Nómina)
    cheques_keywords = ["cheque", "cheques", "nómina", "depósito de cheque", "paycheck"]
    if any(match_keyword_safe(k, user_text_lower) for k in cheques_keywords):
        logger.info(f"🎫 Cheques request detected for contact {contact_id}: '{user_text[:50]}'")
        try:
            msg = f"🎫 *REPORTE DE CHEQUES*\n\n👤 *Contacto:* Contacto #{contact_id}\n🎯 *Intención:* Consulta / Depósito de Cheque\n📝 *Resumen:* {user_text}"
            await google_chat_service.send_alert_detailed(title="Alerta de Orbit", message=msg, level="INFO", space_id="spaces/AAQAGZ_m434")
        except Exception as err:
            logger.error(f"Failed to send Cheques alert: {err}")
        sc11_text = scripts.get("SC.011", sc11_default)
        translated = await translate_script_if_needed(sc11_text, user_text, contact_id=contact_id)
        return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    # 6. Soporte Técnico / Hardware de Agencia (Scanner, Impresora, POS, Lector)
    tech_support_keywords = ["scanner", "escaner", "escáner", "impresora", "pos", "terminal", "lector", "falla técnica", "falla tecnica", "soporte técnico", "soporte tecnico"]
    if any(match_keyword_safe(k, user_text_lower) for k in tech_support_keywords):
        logger.info(f"🛠️ Tech support hardware request detected for contact {contact_id}: '{user_text[:50]}'")
        try:
            soporte_msg = (
                f"🛠️ *REPORTE DE SOPORTE TÉCNICO*\n\n"
                f"👤 *Usuario:* {contact_id}\n"
                f"🏢 *Agencia:* General\n"
                f"🎯 *Intención:* Soporte Técnico / Falla Hardware ({user_text[:40]})\n"
                f"📝 *Detalle:* {user_text}"
            )
            soporte_space = os.getenv("GOOGLE_CHATS_SOPORTE_SPACE") or "spaces/AAQAQhx5RTM"
            await google_chat_service.send_alert_detailed(title="Alerta de Soporte Técnico", message=soporte_msg, level="INFO", space_id=soporte_space)
        except Exception as gchat_err:
            logger.error(f"⚠️ Failed to send Google Chat Tech Support alert: {gchat_err}")
        sc11_text = scripts.get("SC.011", sc11_default)
        translated = await translate_script_if_needed(sc11_text, user_text, contact_id=contact_id)
        return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    # 7. Ventas Internas (Nuevas agencias / Registros)
    ventas_keywords = ["alta de agencia", "nueva agencia", "ventas internas", "registro de agencia", "abrir agencia"]
    if any(match_keyword_safe(k, user_text_lower) for k in ventas_keywords):
        logger.info(f"💼 Ventas Internas request detected for contact {contact_id}: '{user_text[:50]}'")
        try:
            msg = f"💼 *REPORTE DE VENTAS INTERNAS*\n\n👤 *Contacto:* Contacto #{contact_id}\n🎯 *Intención:* Solicitud de Nueva Agencia\n📝 *Detalle:* {user_text}"
            await google_chat_service.send_alert_detailed(title="Alerta de Orbit", message=msg, level="SUCCESS", space_id="spaces/AAQAUghCztE")
        except Exception as err:
            logger.error(f"Failed to send Ventas alert: {err}")
        sc11_text = scripts.get("SC.011", sc11_default)
        translated = await translate_script_if_needed(sc11_text, user_text, contact_id=contact_id)
        return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    # Asesor humano explícito (usando palabras completas para evitar que 'agente' coincida con 'agent')
    human_keywords = ["asesor", "humano", "persona", "hablar con alguien", "representative", "human agent"]
    if any(k in user_text_lower.split() or k in user_text_lower for k in human_keywords if k != "agent"):
        logger.info(f"👤 Explicit human request for contact {contact_id}")
        sc13_text = scripts.get("SC.013", "Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
        translated = await translate_script_if_needed(sc13_text, user_text, contact_id=contact_id)
        return AgentInteractResponse(
            status="success",
            reply_text=translated,
            derivacion="Servicio al Cliente"
        )
        
    # Comando Finalizar / Cierre
    exit_keywords = ["finalizar", "terminar", "adiós", "adios", "bye", "exit", "finish"]
    if any(k == user_text_lower for k in exit_keywords):
        logger.info(f"🚪 Exit request for contact {contact_id}")
        sc36_text = scripts.get("SC.036", "Gracias por comunicarse a Maxitransfers. Le atendió Max. Que tenga un buen día.")
        translated = await translate_script_if_needed(sc36_text, user_text)
        return AgentInteractResponse(
            status="success",
            reply_text=translated,
            derivacion="cerrar"
        )

    # State keys
    state_key = f"session:state:{contact_id}"
    perfil_key = f"session:perfil:{contact_id}"
    code_key = f"session:codigo_envio:{contact_id}"
    name_key = f"session:nombre_usuario:{contact_id}"
    attempts_key = f"session:attempts:{contact_id}"
    
    current_state = await redis.get(state_key)
    current_state = current_state.decode('utf-8') if current_state else "NEW"
    
    # ------------------------------------------------------------
    # 1. SPECIALIZED AGENT: CancelacionMoneyOrder
    # ------------------------------------------------------------
    if agent_name == "CancelacionMoneyOrder":
        m_code = await redis.get(f"session:mo:code:{contact_id}")
        m_amount = await redis.get(f"session:mo:amount:{contact_id}")
        m_reason = await redis.get(f"session:mo:reason:{contact_id}")
        
        m_code = m_code.decode('utf-8') if m_code else None
        m_amount = m_amount.decode('utf-8') if m_amount else None
        m_reason = m_reason.decode('utf-8') if m_reason else None
        
        if not m_code:
            # Check if user provided code in text
            mo_code = extraer_codigo_router(user_text)
            if mo_code:
                await redis.set(f"session:mo:code:{contact_id}", mo_code, ex=3600)
                reply = "Gracias. Por favor indique el monto en dólares exacto de su Money Order:"
                translated = await translate_script_if_needed(reply, user_text)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
            else:
                reply = "Por favor proporcione el número de serie o folio de su Money Order para comenzar:"
                translated = await translate_script_if_needed(reply, user_text)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
        elif not m_amount:
            await redis.set(f"session:mo:amount:{contact_id}", user_text, ex=3600)
            reply = "Gracias. ¿Cuál es el motivo de la cancelación de su Money Order?"
            translated = await translate_script_if_needed(reply, user_text)
            return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
        else:
            await redis.set(f"session:mo:reason:{contact_id}", user_text, ex=3600)
            # Fetch transfer script
            sc13_text = scripts.get("SC.013", "Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
            sc24_text = scripts.get("SC.024", "Para proceder con la solicitud de cancelación de su Money Order, compártame los datos del instrumento.")
            sc13_text = scripts.get("SC.013", "Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
            combined_text = f"{sc24_text}\n\n{sc13_text}"
            translated = await translate_script_if_needed(combined_text, user_text, contact_id=contact_id)
            # Clear money order session keys
            await redis.delete(f"session:mo:code:{contact_id}")
            await redis.delete(f"session:mo:amount:{contact_id}")
            await redis.delete(f"session:mo:reason:{contact_id}")
            return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    # ------------------------------------------------------------
    # 2. SPECIALIZED AGENTS: CancelacionEnvio / ModificacionDatos (RNE.52 / RNE.44)
    # ------------------------------------------------------------
    if agent_name in ["CancelacionEnvio", "ModificacionDatos"]:
        logger.info(f"🚫 Channel exclusion applied for {agent_name}")
        sc31_text = scripts.get("SC.031", "Por razones de seguridad transaccional, no es posible realizar modificaciones o cancelaciones a través de este canal de mensajería. Por favor acuda a la agencia física donde realizó el envío.")
        sc13_text = scripts.get("SC.013", "Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
        combined_text = f"{sc31_text}\n\n{sc13_text}"
        translated = await translate_script_if_needed(combined_text, user_text, contact_id=contact_id)
        return AgentInteractResponse(
            status="success",
            reply_text=translated,
            derivacion="Exclusion"
        )

    # ------------------------------------------------------------
    # 2b. SPECIALIZED AGENT: CancelacionBillRecargas
    # ------------------------------------------------------------
    if agent_name == "CancelacionBillRecargas":
        sc13_text = scripts.get("SC.013", "Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
        translated = await translate_script_if_needed(sc13_text, user_text, contact_id=contact_id)
        return AgentInteractResponse(
            status="success",
            reply_text=translated,
            derivacion="Servicio al Cliente"
        )

    # ------------------------------------------------------------
    # 2c. SPECIALIZED AGENTS: CoordinacionPago / AgenteComunicador / Derivaciones (RNE.41)
    # ------------------------------------------------------------
    if agent_name in ["CoordinacionPago", "AgenteComunicador"]:
        if agent_name == "CoordinacionPago":
            sc22_text = scripts.get("SC.022", "Para asistirlo con el detalle de las tarifas y comisiones de su envío:")
            sc13_text = scripts.get("SC.013", "Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
            combined_text = f"{sc22_text}\n\n{sc13_text}"
            translated = await translate_script_if_needed(combined_text, user_text, contact_id=contact_id)
            return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

        sc13_text = scripts.get("SC.013", "Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
        translated = await translate_script_if_needed(sc13_text, user_text, contact_id=contact_id)
        team = "Servicio al Cliente"
        if agent_name == "DerivacionFraudes":
            team = "DerivacionFraudes"
        elif agent_name == "DerivacionBSA":
            team = "DerivacionBSA"
        elif agent_name == "AgenteComunicador":
            team = "AgenteComunicador"
            
        return AgentInteractResponse(
            status="success",
            reply_text=translated,
            derivacion=team
        )

    # ------------------------------------------------------------
    # 3. SPECIALIZED AGENT: HistorialEnvios
    # ------------------------------------------------------------
    if agent_name == "HistorialEnvios":
        # Returns the last 3 transactions for the contact phone from Supabase
        phone_clean = re.sub(r'[^0-9]', '', contact_id)
        logger.info(f"📜 Querying history for phone clean: {phone_clean}")
        records = []
        try:
            from .shared_logic import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT "Fecha", "Monto_enviado", "Beneficiario_Nombre", "status" FROM "Base_completa" WHERE "Telefono_Remitente" = %s OR "Telefono_Beneficiario" = %s ORDER BY "Fecha" DESC LIMIT 3;',
                (phone_clean, phone_clean)
            )
            rows = cursor.fetchall()
            for r in rows:
                records.append({
                    "fecha": str(r[0]),
                    "monto": str(r[1]),
                    "beneficiario": str(r[2]),
                    "status": str(r[3])
                })
            cursor.close()
            conn.close()
        except Exception as db_err:
            logger.error(f"Error querying transaction history: {db_err}")
            
        if records:
            history_text = "Aquí tiene sus últimos 3 movimientos:\n"
            for idx, item in enumerate(records):
                history_text += f"{idx+1}. Fecha: {item['fecha']} | Monto: {item['monto']} | Destinatario: {item['beneficiario']} | Estatus: {item['status']}\n"
            translated = await translate_script_if_needed(history_text, user_text)
            return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
        else:
            reply = "No he podido localizar historial de transacciones registrado para su número de contacto."
            translated = await translate_script_if_needed(reply, user_text)
            return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    # ------------------------------------------------------------
    # 4. SPECIALIZED AGENT: AgenteCSAT
    # ------------------------------------------------------------
    if agent_name == "AgenteCSAT":
        csat_step_key = f"session:csat:step:{contact_id}"
        csat_step = await redis.get(csat_step_key)
        csat_step = csat_step.decode('utf-8') if csat_step else "1"
        
        if csat_step == "1":
            # Expecting rating (1-5)
            rating_match = re.search(r'\b([1-5])\b', user_text)
            if rating_match:
                rating = int(rating_match.group(1))
                await redis.set(f"session:csat:rating:{contact_id}", str(rating), ex=3600)
                await redis.set(csat_step_key, "2", ex=3600)
                sc35_text = scripts.get("SC.035", "Su opinión es muy valiosa. Por favor comparta cualquier comentario sobre cómo podemos mejorar.")
                translated = await translate_script_if_needed(sc35_text, user_text)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
            else:
                sc34_text = scripts.get("SC.034", "Por favor califique nuestro servicio del 1 al 5.")
                translated = await translate_script_if_needed(sc34_text, user_text)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
        else:
            # CSAT feedback complete, save it
            rating = await redis.get(f"session:csat:rating:{contact_id}")
            rating_val = int(rating.decode('utf-8')) if rating else 5
            # Clear CSAT session keys
            await redis.delete(csat_step_key)
            await redis.delete(f"session:csat:rating:{contact_id}")
            
            sc36_text = scripts.get("SC.036", "Gracias por comunicarse a Maxitransfers. Le atendió Max. Que tenga un buen día.")
            translated = await translate_script_if_needed(sc36_text, user_text)
            return AgentInteractResponse(status="success", reply_text=translated, derivacion="cerrar")

    # ------------------------------------------------------------
    # 4b. SPECIALIZED AGENT: OrquestadorDocumentos
    # ------------------------------------------------------------
    if agent_name == "OrquestadorDocumentos":
        if media_url:
            logger.info(f"📸 OrquestadorDocumentos analyzing media: {media_url}")
            ocr_result = await run_ocr_on_media(media_url)
            
            is_rec = ocr_result.get("is_receipt") if ocr_result else False
            t_code = ocr_result.get("tracking_code") if ocr_result else None
            
            if is_rec and t_code:
                t_code = t_code.strip().upper()
                await redis.set(code_key, t_code, ex=3600)
                
                # Save OCR names if present
                if ocr_result.get("sender_name"):
                    await redis.set(f"session:ocr_sender:{contact_id}", ocr_result["sender_name"].strip(), ex=3600)
                if ocr_result.get("beneficiary_name"):
                    await redis.set(f"session:ocr_beneficiary:{contact_id}", ocr_result["beneficiary_name"].strip(), ex=3600)
                
                # Transition state to WAITING_FOR_NAME
                await redis.set(state_key, "WAITING_FOR_NAME", ex=3600)
                
                # Reset doc attempts on success
                await redis.delete(f"session:attempts_doc:{contact_id}")
                
                # Determine destination depending on code format
                if t_code.startswith("TRK"):
                    dest = "VerificadorPagoBill"
                else:
                    dest = "VerificadorEstatus"
                    
                logger.info(f"🎯 OrquestadorDocumentos routed to {dest} with code {t_code}")
                return AgentInteractResponse(
                    status="success",
                    reply_text="",
                    derivacion=dest
                )
            else:
                attempts_doc_val = await redis.get(f"session:attempts_doc:{contact_id}")
                attempts_doc = int(attempts_doc_val.decode('utf-8')) if attempts_doc_val else 0
                attempts_doc += 1
                
                if attempts_doc >= 2:
                    await redis.delete(f"session:attempts_doc:{contact_id}")
                    sc2_text = scripts.get("SC.002", "Lo transferiré con uno de nuestros asesores para brindarle asistencia personalizada.")
                    translated = await translate_script_if_needed(sc2_text, user_text)
                    return AgentInteractResponse(
                        status="success",
                        reply_text=translated,
                        derivacion="Servicio al Cliente"
                    )
                else:
                    await redis.set(f"session:attempts_doc:{contact_id}", str(attempts_doc), ex=3600)
                    sc1_text = scripts.get("SC.001", "No fue posible procesar la información o imagen proporcionada. ¿Podría compartirla de nuevo por favor?")
                    translated = await translate_script_if_needed(sc1_text, user_text)
                    return AgentInteractResponse(
                        status="success",
                        reply_text=translated,
                        derivacion="NA"
                    )
        else:
            logger.info(f"🔄 OrquestadorDocumentos received text: '{user_text}'. Routing back to Max.")
            return AgentInteractResponse(
                status="success",
                reply_text="",
                derivacion="Max"
            )

    # ------------------------------------------------------------
    # 5. SPECIALIZED AGENT: VerificadorPagoBill
    # ------------------------------------------------------------
    if agent_name == "VerificadorPagoBill":
        bill_code = extraer_codigo_router(user_text)
        if not bill_code:
            cached_code = await redis.get(code_key)
            bill_code = cached_code.decode('utf-8') if cached_code else None
            
        if bill_code:
            # Call bill status check logic
            req = BillCheckRequest(
                contact_id=contact_id,
                user_text=f"{user_text} {bill_code}",
                tracking_number=bill_code
            )
            try:
                resp = await check_bill_status_inner(req, x_webhook_secret=settings.WEBHOOK_SECRET)
                return AgentInteractResponse(
                    status="success",
                    reply_text=resp.reply_text,
                    derivacion=resp.derivacion
                )
            except Exception as e:
                logger.error(f"Error querying bill status: {e}")
                sc13_text = scripts.get("SC.013", "Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
                translated = await translate_script_if_needed(sc13_text, user_text)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")
        else:
            sc10_1_text = scripts.get("SC.010.1", "Para continuar, necesito validar algunos datos. ¿Me comparte el nombre completo de la persona que realizó el pago y el nombre de la compañía, por favor?.")
            translated = await translate_script_if_needed(sc10_1_text, user_text)
            return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")

    # ------------------------------------------------------------
    # 6. CORE AGENTS: Max, VerificadorEstatus, OrquestadorDocumentos (Rastreo de Remesas)
    # ------------------------------------------------------------
    
    # Check if a greeting is sent (resets session) or starting fresh
    user_text_clean = re.sub(r'[^a-zñáéíóú\s]', '', user_text_lower).strip()
    
    greeting_words = ["hola", "buenos dias", "buenos días", "buenas tardes", "buenas noches", "hello", "hi", "buen dia", "buen día", "saludos"]
    
    is_greeting = False
    if media_url:
        logger.info(f"📸 media_url present for contact {contact_id}. Suppressing greeting session reset.")
        is_greeting = False
    elif user_text_clean in greeting_words:
        is_greeting = True
    elif len(user_text_clean) < 30:
        if any(w in user_text_clean for w in ["hola", "buen", "hi", "hello", "saludos"]):
            is_greeting = True
            
    # Support manual reset commands for simulation testing
    if user_text_clean in ["reset", "restablecer", "inicio", "clear", "reiniciar"]:
        logger.info(f"🧹 Manual session reset triggered for contact {contact_id}")
        is_greeting = True
        
    # OCR analysis from media_url if present
    ocr_result = None
    if media_url:
        logger.info(f"📸 Running OCR on media: {media_url}")
        ocr_result = await run_ocr_on_media(media_url)
        if ocr_result and ocr_result.get("is_receipt") and ocr_result.get("tracking_code"):
            codigo_envio = ocr_result["tracking_code"].strip().upper()
            await redis.set(code_key, codigo_envio, ex=3600)
            logger.info(f"🎯 OCR Extracted Claim Code: {codigo_envio}")
            if ocr_result.get("sender_name"):
                await redis.set(f"session:ocr_sender:{contact_id}", ocr_result["sender_name"], ex=3600)
            if ocr_result.get("beneficiary_name"):
                await redis.set(f"session:ocr_beneficiary:{contact_id}", ocr_result["beneficiary_name"], ex=3600)
            
            # If OCR extracted sender/beneficiary names, attempt direct status resolution
            ocr_sender = ocr_result.get("sender_name")
            ocr_ben = ocr_result.get("beneficiary_name")
            if ocr_sender or ocr_ben:
                try:
                    status_req = StatusCheckRequest(
                        contact_id=contact_id,
                        user_text=f"{user_text} {codigo_envio}",
                        nombre_remitente=ocr_sender or ocr_ben,
                        nombre_beneficiario=ocr_ben or ocr_sender,
                        codigo_envio=codigo_envio,
                        perfil="CLIENTE"
                    )
                    status_resp = await check_transaction_status_inner(status_req, x_webhook_secret=settings.WEBHOOK_SECRET)
                    if status_resp.validation_success:
                        await redis.set(state_key, "COMPLETED", ex=3600)
                        await redis.delete(perfil_key)
                        await redis.delete(code_key)
                        await redis.delete(name_key)
                        logger.info(f"🎯 Direct OCR Status Resolution Success for code: {codigo_envio}")
                        return AgentInteractResponse(
                            status="success",
                            reply_text=status_resp.reply_text,
                            derivacion=status_resp.derivacion
                        )
                except Exception as ocr_status_err:
                    logger.info(f"Direct status check from OCR failed: {ocr_status_err}")

            # Transition directly to WAITING_FOR_NAME with SC.010 prompt
            await redis.set(state_key, "WAITING_FOR_NAME", ex=3600)
            sc10_text = scripts.get("SC.010", "Para continuar, necesito validar algunos datos. ¿Me comparte el nombre completo de quien envió el dinero y el nombre completo de quien lo recibe, por favor?.")
            translated = await translate_script_if_needed(sc10_text, user_text)
            return AgentInteractResponse(
                status="success",
                reply_text=translated,
                derivacion="NA"
            )
        else:
            # If OCR cannot extract a valid code from the image, route to OrquestadorDocumentos without looping
            if agent_name != "OrquestadorDocumentos":
                logger.info(f"📄 Media URL unreadable by OCR or non-receipt image. Routing to OrquestadorDocumentos for contact {contact_id}")
                return AgentInteractResponse(
                    status="success",
                    reply_text="",
                    derivacion="OrquestadorDocumentos"
                )

    if is_greeting or current_state == "NEW":
        # VerificadorEstatus directly handles status inquiry without repeating CU.A1 greeting
        if agent_name == "VerificadorEstatus":
            cached_code = await redis.get(code_key)
            cached_code_str = cached_code.decode('utf-8') if cached_code else None
            if cached_code_str:
                logger.info(f"🎯 VerificadorEstatus starting with pre-extracted OCR code: {cached_code_str}")
                await redis.set(state_key, "WAITING_FOR_NAME", ex=3600)
                sc10_text = scripts.get("SC.010", "Por favor proporcione el nombre completo del remitente y del beneficiario:")
                translated = await translate_script_if_needed(sc10_text, user_text, contact_id=contact_id)
                return AgentInteractResponse(
                    status="success",
                    reply_text=translated,
                    derivacion="NA"
                )
            else:
                logger.info(f"🔍 VerificadorEstatus starting for contact {contact_id}. Requesting 3 required items (SC.008)")
                await redis.set(state_key, "WAITING_FOR_DATA", ex=3600)
                sc8_text = scripts.get("SC.008", "Para consultar el estatus de su envío, por favor compártame la siguiente información:\n• Nombre completo de la persona que realizó el envío\n• Nombre completo de la persona que recibe el envío\n• Clave del envío (CE...)").strip()
                translated = await translate_script_if_needed(sc8_text, user_text, contact_id=contact_id)
                return AgentInteractResponse(
                    status="success",
                    reply_text=translated,
                    derivacion="NA"
                )

        logger.info(f"🧹 Clearing Redis tracking state for contact {contact_id} due to greeting/NEW state")
        await clear_redis_session(redis, contact_id)
        
        cuA1_text = scripts.get("CU.A1", "Gracias por comunicarse a Maxitransfers. Soy Max, su asistente virtual. Para comenzar a ayudarle, ¿puede indicarme su nombre completo, por favor?")
        translated = await translate_script_if_needed(cuA1_text, user_text, contact_id=contact_id)
        await redis.set(state_key, "WAITING_FOR_PROFILE", ex=3600)
        return AgentInteractResponse(
            status="success",
            reply_text=translated,
            derivacion="NA"
        )

    # Retrieve current variables
    perfil = await redis.get(perfil_key)
    perfil = perfil.decode('utf-8') if perfil else None
    
    codigo_envio = await redis.get(code_key)
    codigo_envio = codigo_envio.decode('utf-8') if codigo_envio else None
    
    nombre_usuario = await redis.get(name_key)
    nombre_usuario = nombre_usuario.decode('utf-8') if nombre_usuario else None

    # OCR analysis from media_url if present
    ocr_result = None
    if media_url:
        logger.info(f"📸 Running OCR on media: {media_url}")
        ocr_result = await run_ocr_on_media(media_url)
        if ocr_result and ocr_result.get("is_receipt") and ocr_result.get("tracking_code"):
            codigo_envio = ocr_result["tracking_code"].strip().upper()
            await redis.set(code_key, codigo_envio, ex=3600)
            logger.info(f"🎯 OCR Extracted Claim Code: {codigo_envio}")
            if ocr_result.get("sender_name"):
                await redis.set(f"session:ocr_sender:{contact_id}", ocr_result["sender_name"], ex=3600)
            if ocr_result.get("beneficiary_name"):
                await redis.set(f"session:ocr_beneficiary:{contact_id}", ocr_result["beneficiary_name"], ex=3600)
        else:
            logger.info(f"📄 Media URL present but OCR could not extract claim code. Routing contact {contact_id} directly to OrquestadorDocumentos")
            return AgentInteractResponse(
                status="success",
                reply_text="",
                derivacion="OrquestadorDocumentos"
            )

    # Check for code in text if not resolved
    if not codigo_envio:
        codigo_envio = extraer_codigo_router(user_text)
        if codigo_envio:
            await redis.set(code_key, codigo_envio, ex=3600)
            logger.info(f"🎯 Text Extracted Claim Code: {codigo_envio}")

    # State Transitions
    if current_state == "WAITING_FOR_PROFILE":
        perfil = detect_profile_from_text(user_text)
            
        if perfil:
            await redis.set(perfil_key, perfil, ex=3600)
            await redis.set(attempts_key, "0", ex=3600)
            
            if not codigo_envio:
                sc8_text = scripts.get("SC.008", "Por favor comparta el ticket o escriba el código de envío:")
                translated = await translate_script_if_needed(sc8_text, user_text)
                await redis.set(state_key, "WAITING_FOR_CODE", ex=3600)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
            else:
                # --- Trial check: if user_text already contains names/info, attempt query immediately ---
                try:
                    if agent_name == "VerificadorEstatusRecargas":
                        phones = re.findall(r'\b\d{7,15}\b', user_text)
                        cust_phone = phones[0] if len(phones) > 0 else user_text
                        cell_phone = phones[1] if len(phones) > 1 else cust_phone
                        topup_req = TopupCheckRequest(
                            contact_id=contact_id,
                            user_text=f"{user_text} {codigo_envio}",
                            transaction_id=codigo_envio,
                            customer_number=cust_phone,
                            cellular_number=cell_phone,
                            perfil=perfil or "CLIENTE"
                        )
                        topup_resp = await check_topup_status_inner(topup_req, x_webhook_secret=settings.WEBHOOK_SECRET)
                        if topup_resp.validation_success:
                            await redis.set(state_key, "COMPLETED", ex=3600)
                            await redis.delete(perfil_key)
                            await redis.delete(code_key)
                            await redis.delete(name_key)
                            return AgentInteractResponse(status="success", reply_text=topup_resp.reply_text, derivacion=topup_resp.derivacion)
                    elif codigo_envio.upper().startswith("TRK"):
                        bill_req = BillCheckRequest(
                            contact_id=contact_id,
                            user_text=f"{user_text} {codigo_envio}",
                            tracking_number=codigo_envio,
                            biller=user_text,
                            nombre_completo_customer=user_text,
                            perfil=perfil or "CLIENTE"
                        )
                        bill_resp = await check_bill_status_inner(bill_req, x_webhook_secret=settings.WEBHOOK_SECRET)
                        if bill_resp.validation_success:
                            await redis.set(state_key, "COMPLETED", ex=3600)
                            await redis.delete(perfil_key)
                            await redis.delete(code_key)
                            await redis.delete(name_key)
                            return AgentInteractResponse(status="success", reply_text=bill_resp.reply_text, derivacion=bill_resp.derivacion)
                    else:
                        if not perfil:
                            nombre_rem = user_text
                            nombre_ben = user_text
                            perfil_to_send = "CLIENTE"
                        else:
                            nombre_rem = user_text if perfil == "REMITENTE" else None
                            nombre_ben = user_text if perfil == "BENEFICIARIO" else None
                            perfil_to_send = perfil
                        status_req = StatusCheckRequest(
                            contact_id=contact_id,
                            user_text=f"{user_text} {codigo_envio}",
                            nombre_remitente=nombre_rem,
                            nombre_beneficiario=nombre_ben,
                            codigo_envio=codigo_envio,
                            perfil=perfil_to_send
                        )
                        status_resp = await check_transaction_status_inner(status_req, x_webhook_secret=settings.WEBHOOK_SECRET)
                        if status_resp.validation_success:
                            await redis.set(state_key, "COMPLETED", ex=3600)
                            await redis.delete(perfil_key)
                            await redis.delete(code_key)
                            await redis.delete(name_key)
                            return AgentInteractResponse(status="success", reply_text=status_resp.reply_text, derivacion=status_resp.derivacion)
                except Exception as trial_err:
                    logger.info(f"Trial query in WAITING_FOR_PROFILE failed (missing info): {trial_err}")

                if agent_name == "VerificadorEstatusRecargas":
                    sc10_text = scripts.get("SC.010.2", "Para continuar, necesito validar algunos datos. ¿Me comparte el número telefónico de la persona quien hizo la recarga y el número al que se realizó, por favor?.")
                    translated = await translate_script_if_needed(sc10_text, user_text)
                    await redis.set(state_key, "WAITING_FOR_TOPUP_PHONES", ex=3600)
                    return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
                elif codigo_envio.upper().startswith("TRK"):
                    sc10_text = scripts.get("SC.010.1", "Para continuar, necesito validar algunos datos. ¿Me comparte el nombre completo de la persona que realizó el pago y el nombre de la compañía, por favor?.")
                    translated = await translate_script_if_needed(sc10_text, user_text)
                    await redis.set(state_key, "WAITING_FOR_BILL_INFO", ex=3600)
                    return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
                else:
                    sc10_text = scripts.get("SC.010", "Para continuar, necesito validar algunos datos. ¿Me comparte el nombre completo de quien envió el dinero y el nombre completo de quien lo recibe, por favor?.")
                    translated = await translate_script_if_needed(sc10_text, user_text)
                    await redis.set(state_key, "WAITING_FOR_NAME", ex=3600)
                    return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
        else:
            # Unrecognized profile input
            attempts_val = await redis.get(attempts_key)
            attempts = int(attempts_val.decode('utf-8')) if attempts_val else 0
            attempts += 1
            if attempts >= 2:
                sc2_text = scripts.get("SC.002", "Lo transferiré con uno de nuestros asesores...")
                translated = await translate_script_if_needed(sc2_text, user_text)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")
            else:
                await redis.set(attempts_key, str(attempts), ex=3600)
                sc3_text = scripts.get("SC.003", "¿Es usted remitente, beneficiario o agente?")
                translated = await translate_script_if_needed(sc3_text, user_text)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")

    elif current_state == "WAITING_FOR_CODE":
        if codigo_envio:
            await redis.set(attempts_key, "0", ex=3600)
            
            # --- Trial check: if user_text already contains names/info, attempt query immediately ---
            try:
                if agent_name == "VerificadorEstatusRecargas":
                    phones = re.findall(r'\b\d{7,15}\b', user_text)
                    cust_phone = phones[0] if len(phones) > 0 else user_text
                    cell_phone = phones[1] if len(phones) > 1 else cust_phone
                    topup_req = TopupCheckRequest(
                        contact_id=contact_id,
                        user_text=f"{user_text} {codigo_envio}",
                        transaction_id=codigo_envio,
                        customer_number=cust_phone,
                        cellular_number=cell_phone,
                        perfil=perfil or "CLIENTE"
                    )
                    topup_resp = await check_topup_status_inner(topup_req, x_webhook_secret=settings.WEBHOOK_SECRET)
                    if topup_resp.validation_success:
                        await redis.set(state_key, "COMPLETED", ex=3600)
                        await redis.delete(perfil_key)
                        await redis.delete(code_key)
                        await redis.delete(name_key)
                        return AgentInteractResponse(status="success", reply_text=topup_resp.reply_text, derivacion=topup_resp.derivacion)
                elif codigo_envio.upper().startswith("TRK"):
                    bill_req = BillCheckRequest(
                        contact_id=contact_id,
                        user_text=f"{user_text} {codigo_envio}",
                        tracking_number=codigo_envio,
                        biller=user_text,
                        nombre_completo_customer=user_text,
                        perfil=perfil or "CLIENTE"
                    )
                    bill_resp = await check_bill_status_inner(bill_req, x_webhook_secret=settings.WEBHOOK_SECRET)
                    if bill_resp.validation_success:
                        await redis.set(state_key, "COMPLETED", ex=3600)
                        await redis.delete(perfil_key)
                        await redis.delete(code_key)
                        await redis.delete(name_key)
                        return AgentInteractResponse(status="success", reply_text=bill_resp.reply_text, derivacion=bill_resp.derivacion)
                else:
                    if not perfil:
                        nombre_rem = user_text
                        nombre_ben = user_text
                        perfil_to_send = "CLIENTE"
                    else:
                        nombre_rem = user_text if perfil == "REMITENTE" else None
                        nombre_ben = user_text if perfil == "BENEFICIARIO" else None
                        perfil_to_send = perfil
                    status_req = StatusCheckRequest(
                        contact_id=contact_id,
                        user_text=f"{user_text} {codigo_envio}",
                        nombre_remitente=nombre_rem,
                        nombre_beneficiario=nombre_ben,
                        codigo_envio=codigo_envio,
                        perfil=perfil_to_send
                    )
                    status_resp = await check_transaction_status_inner(status_req, x_webhook_secret=settings.WEBHOOK_SECRET)
                    if status_resp.validation_success:
                        await redis.set(state_key, "COMPLETED", ex=3600)
                        await redis.delete(perfil_key)
                        await redis.delete(code_key)
                        await redis.delete(name_key)
                        return AgentInteractResponse(status="success", reply_text=status_resp.reply_text, derivacion=status_resp.derivacion)
            except Exception as trial_err:
                logger.info(f"Trial query in WAITING_FOR_CODE failed (missing info): {trial_err}")

            if agent_name == "VerificadorEstatusRecargas":
                sc10_text = scripts.get("SC.010.2", "Para continuar, necesito validar algunos datos. ¿Me comparte el número telefónico de la persona quien hizo la recarga y el número al que se realizó, por favor?.")
                translated = await translate_script_if_needed(sc10_text, user_text)
                await redis.set(state_key, "WAITING_FOR_TOPUP_PHONES", ex=3600)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
            elif codigo_envio.upper().startswith("TRK"):
                sc10_text = scripts.get("SC.010.1", "Para continuar, necesito validar algunos datos. ¿Me comparte el nombre completo de la persona que realizó el pago y el nombre de la compañía, por favor?.")
                translated = await translate_script_if_needed(sc10_text, user_text)
                await redis.set(state_key, "WAITING_FOR_BILL_INFO", ex=3600)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
            else:
                sc10_text = scripts.get("SC.010", "Para continuar, necesito validar algunos datos. ¿Me comparte el nombre completo de quien envió el dinero y el nombre completo de quien lo recibe, por favor?.")
                translated = await translate_script_if_needed(sc10_text, user_text)
                await redis.set(state_key, "WAITING_FOR_NAME", ex=3600)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
        else:
            attempts_val = await redis.get(attempts_key)
            attempts = int(attempts_val.decode('utf-8')) if attempts_val else 0
            attempts += 1
            if attempts >= 2:
                sc2_text = scripts.get("SC.002", "Lo transferiré con uno de nuestros asesores...")
                translated = await translate_script_if_needed(sc2_text, user_text)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")
            else:
                await redis.set(attempts_key, str(attempts), ex=3600)
                sc9_text = scripts.get("SC.009", "Entiendo que tiene dificultad para localizar la información solicitada. Le comparto una imagen de referencia para que pueda identificar estos datos.")
                translated = await translate_script_if_needed(sc9_text, user_text)
                return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")

    elif current_state == "WAITING_FOR_BILL_INFO":
        await redis.set(name_key, user_text, ex=3600)
        logger.info(f"⚡ Bill variables collected. Running Bill status query for code: {codigo_envio}")
        
        bill_req = BillCheckRequest(
            contact_id=contact_id,
            user_text=f"{user_text} {codigo_envio}",
            tracking_number=codigo_envio,
            biller=user_text,
            nombre_completo_customer=user_text,
            perfil=perfil or "CLIENTE"
        )
        
        try:
            bill_resp = await check_bill_status_inner(bill_req, x_webhook_secret=settings.WEBHOOK_SECRET)
            
            if bill_resp.validation_success:
                await redis.set(state_key, "COMPLETED", ex=3600)
                await redis.delete(perfil_key)
                await redis.delete(code_key)
                await redis.delete(name_key)
                
            return AgentInteractResponse(
                status="success",
                reply_text=bill_resp.reply_text,
                derivacion=bill_resp.derivacion
            )
        except Exception as e:
            logger.error(f"Error in atomic bill check: {e}")
            sc13_text = scripts.get("SC.013", "Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
            translated = await translate_script_if_needed(sc13_text, user_text)
            return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    elif current_state == "WAITING_FOR_TOPUP_PHONES":
        phones = re.findall(r'\b\d{7,15}\b', user_text)
        cust_phone = phones[0] if len(phones) > 0 else user_text
        cell_phone = phones[1] if len(phones) > 1 else cust_phone
        
        logger.info(f"⚡ Topup variables collected. Running Topup status query for code: {codigo_envio}")
        
        topup_req = TopupCheckRequest(
            contact_id=contact_id,
            user_text=f"{user_text} {codigo_envio}",
            transaction_id=codigo_envio,
            customer_number=cust_phone,
            cellular_number=cell_phone,
            perfil=perfil or "CLIENTE"
        )
        
        try:
            topup_resp = await check_topup_status_inner(topup_req, x_webhook_secret=settings.WEBHOOK_SECRET)
            
            if topup_resp.validation_success:
                await redis.set(state_key, "COMPLETED", ex=3600)
                await redis.delete(perfil_key)
                await redis.delete(code_key)
                await redis.delete(name_key)
                
            return AgentInteractResponse(
                status="success",
                reply_text=topup_resp.reply_text,
                derivacion=topup_resp.derivacion
            )
        except Exception as e:
            logger.error(f"Error in atomic topup check: {e}")
            sc13_text = scripts.get("SC.013", "Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
            translated = await translate_script_if_needed(sc13_text, user_text)
            return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    elif current_state == "WAITING_FOR_NAME":
        nombre_usuario = user_text
        await redis.set(name_key, nombre_usuario, ex=3600)
        
        # We now have: code, profile, and name. Proceed with atomic check!
        logger.info(f"⚡ All variables collected. Running atomic DB query for code: {codigo_envio}")
        
        # Prepare params
        if not perfil:
            nombre_rem = nombre_usuario
            nombre_ben = nombre_usuario
            perfil_to_send = "CLIENTE"
        else:
            nombre_rem = nombre_usuario if perfil == "REMITENTE" else None
            nombre_ben = nombre_usuario if perfil == "BENEFICIARIO" else None
            perfil_to_send = perfil
            
        status_req = StatusCheckRequest(
            contact_id=contact_id,
            user_text=f"{user_text} {codigo_envio}",
            nombre_remitente=nombre_rem,
            nombre_beneficiario=nombre_ben,
            codigo_envio=codigo_envio,
            perfil=perfil_to_send
        )
        
        try:
            status_resp = await check_transaction_status_inner(status_req, x_webhook_secret=settings.WEBHOOK_SECRET)
            
            if status_resp.validation_success:
                # Flow succeeded, change state to CSAT/Completed
                # According to design, we offer SC.033 (help additional)
                await redis.set(state_key, "COMPLETED", ex=3600)
                # Clear name/code keys
                await redis.delete(perfil_key)
                await redis.delete(code_key)
                await redis.delete(name_key)
                
            return AgentInteractResponse(
                status="success",
                reply_text=status_resp.reply_text,
                derivacion=status_resp.derivacion
            )
        except Exception as e:
            logger.error(f"Error in atomic transaction check: {e}")
            sc13_text = scripts.get("SC.013", "Lo transferiré con uno de nuestros asesores. Por favor espere un momento.")
            translated = await translate_script_if_needed(sc13_text, user_text)
            return AgentInteractResponse(status="success", reply_text=translated, derivacion="Servicio al Cliente")

    elif current_state == "COMPLETED":
        # Check if they said NO/NO MORE HELP to trigger CSAT
        if is_no_more_help_needed(user_text):
            # Trigger CSAT Survey
            await redis.set(state_key, "CSAT", ex=3600)
            sccsat_key = f"session:csat:step:{contact_id}"
            await redis.set(sccsat_key, "1", ex=3600)
            
            sc34_text = scripts.get("SC.034", "Por favor califique nuestro servicio del 1 al 5.")
            translated = await translate_script_if_needed(sc34_text, user_text)
            return AgentInteractResponse(status="success", reply_text=translated, derivacion="NA")
        else:
            # Re-route as a new intent back to Max or start again
            # Reset state and re-process as a greeting/new request
            await redis.delete(state_key)
            return await agent_interact(request, x_webhook_secret, secret)

    # Fallback to welcome CU.A1
    cuA1_text = scripts.get("CU.A1", "Gracias por comunicarse a Maxitransfers...")
    translated = await translate_script_if_needed(cuA1_text, user_text)
    return AgentInteractResponse(
        status="success",
        reply_text=translated,
        derivacion="NA"
    )


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



async def translate_script_if_needed(script_text: str, user_text: str, contact_id: str = "") -> str:
    """
    LNG.01 / LNG.02: Detects user language and translates verbatim script accurately.
    If user_text is in English or non-Spanish, translates script_text to user's language.
    """
    if not script_text or not user_text:
        return script_text
    
    try:
        from .translation_utils import detect_language, translate_text
        lang = await detect_language(user_text)
        if lang and lang != "es":
            logger.info(f"🌐 LNG.01/LNG.02: Translating script to target language '{lang}' for contact '{contact_id}'")
            translated = await translate_text(script_text, target_lang=lang)
            return translated or script_text
    except Exception as err:
        logger.warning(f"Translation error: {err}")
    
    return script_text
