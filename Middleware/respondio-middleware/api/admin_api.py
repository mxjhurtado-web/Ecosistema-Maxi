"""
Admin API for dashboard management.
Provides endpoints for configuration, telemetry, and maintenance.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Header
from typing import List, Optional
from datetime import datetime, timedelta

from .models import (
    SecurityConfig,
    RequestLog,
    ResponseStatus,
    HealthResponse,
    DashboardUser,
    UserRole,
    MCPConfig,
    CacheConfig,
    EmailAlertConfig,
    GoogleChatAlertConfig,
    AuditLogEntry,
    AuditAction,
    AgentConfig,
    GoogleChatNotificationRequest
)
from .config import settings
from .config_manager import config_manager
from .telemetry import telemetry_service
from .mcp_client import mcp_client
import logging

logger = logging.getLogger(__name__)

# Create routers
router = APIRouter(prefix="/admin", tags=["admin"])
public_router = APIRouter(tags=["public"])


# ============================================================
# Authentication Dependency (Basic)
# ============================================================

async def verify_admin_credentials(
    auth_username: str = Query(..., alias="username"),
    auth_password: str = Query(..., alias="password")
) -> DashboardUser:
    """Verify credentials against dynamic user list"""
    users = await config_manager.get_users()
    
    for user in users:
        if user.username == auth_username and user.password == auth_password:
            return user
            
    # Fallback to default if Redis is empty or no match (safety during setup)
    if auth_username == settings.DASHBOARD_USERNAME and auth_password == settings.DASHBOARD_PASSWORD:
        return DashboardUser(
            username=auth_username,
            password=auth_password,
            role=UserRole.ADMIN
        )
        
    raise HTTPException(status_code=401, detail="Invalid credentials")


async def require_admin_role(
    user: DashboardUser = Depends(verify_admin_credentials)
):
    """Ensure user has admin role"""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Permission denied: Admin role required")
    return user


# ============================================================
# Configuration Endpoints
# ============================================================

@router.get("/config/mcp", response_model=MCPConfig)
async def get_mcp_config(
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get current MCP configuration"""
    return await config_manager.get_mcp_config()


@router.put("/config/mcp")
async def update_mcp_config(
    config: MCPConfig,
    admin: DashboardUser = Depends(require_admin_role)
):
    """Update MCP configuration"""
    success = await config_manager.update_mcp_config(config)
    
    if success:
        # Audit log
        await config_manager.log_audit_action(AuditLogEntry(
            username=admin.username,
            role=admin.role,
            action=AuditAction.CONFIG_CHANGE,
            details=f"Updated MCP configuration: {config.url}"
        ))
        
        # Update MCP client with new config
        mcp_client.url = config.url
        mcp_client.timeout = config.timeout
        mcp_client.gemini_api_key = config.gemini_api_key
        mcp_client.emergency_mode = config.emergency_mode
        
        # Update Keycloak Auth
        if config.use_keycloak and config.kc_server_url:
            from .auth import KeycloakAuthService
            mcp_client.kc_auth = KeycloakAuthService(
                server_url=config.kc_server_url,
                realm=config.kc_realm,
                client_id=config.kc_client_id,
                client_secret=config.kc_client_secret
            )
        else:
            mcp_client.kc_auth = None
        
        return {"status": "ok", "message": "MCP config updated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update config")


@router.get("/config/cache", response_model=CacheConfig)
async def get_cache_config(
    _: bool = Depends(verify_admin_credentials)
):
    """Get current cache configuration"""
    return await config_manager.get_cache_config()


@router.put("/config/cache")
async def update_cache_config(
    config: CacheConfig,
    _: bool = Depends(verify_admin_credentials)
):
    """Update cache configuration"""
    success = await config_manager.update_cache_config(config)
    
    if success:
        return {"status": "ok", "message": "Cache config updated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update config")


@router.get("/config/security", response_model=SecurityConfig)
async def get_security_config(
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get current security configuration"""
    return await config_manager.get_security_config()


@router.put("/config/security")
async def update_security_config(
    config: SecurityConfig,
    _: bool = Depends(verify_admin_credentials)
):
    """Update security configuration"""
    success = await config_manager.update_security_config(config)
    
    if success:
        return {"status": "ok", "message": "Security config updated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update config")


@router.get("/config/email", response_model=EmailAlertConfig)
async def get_email_config(_: DashboardUser = Depends(verify_admin_credentials)):
    """Get current email alert configuration"""
    return await config_manager.get_email_config()


@router.put("/config/email")
async def update_email_config(
    config: EmailAlertConfig,
    user: DashboardUser = Depends(require_admin_role)
):
    """Update email alert configuration"""
    success = await config_manager.update_email_config(config)
    
    if success:
        # Update email service instance settings if needed
        from .email_service import email_service
        email_service.enabled = config.enabled
        email_service.host = config.smtp_server
        email_service.port = config.smtp_port
        email_service.user = config.smtp_user
        email_service.password = config.smtp_password
        email_service.recipient = config.recipient_email
        
        # Audit log
        await config_manager.log_audit_action(AuditLogEntry(
            username=user.username,
            role=user.role,
            action=AuditAction.CONFIG_CHANGE,
            details="Updated email alerting configuration"
        ))
        
        return {"status": "ok", "message": "Email config updated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update config")


# ============================================================
# Google Chat Configuration Endpoints
# ============================================================

@router.get("/config/google-chat", response_model=GoogleChatAlertConfig)
async def get_google_chat_config(
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get current Google Chat configuration"""
    return await config_manager.get_google_chat_config()


@router.put("/config/google-chat")
async def update_google_chat_config(
    config: GoogleChatAlertConfig,
    user: DashboardUser = Depends(require_admin_role)
):
    """Update Google Chat configuration"""
    success = await config_manager.update_google_chat_config(config)
    
    if success:
        # Audit log
        await config_manager.log_audit_action(AuditLogEntry(
            username=user.username,
            role=user.role,
            action=AuditAction.CONFIG_CHANGE,
            details="Updated Google Chat alerting configuration"
        ))
        
        return {"status": "ok", "message": "Google Chat config updated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update config")


@router.post("/maintenance/test-google-chat")
async def test_google_chat(
    message: str = Query(default="Test alert from ORBIT Dashboard"),
    space_id: Optional[str] = Query(None),
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Test Google Chat connection"""
    from .google_chat_service import google_chat_service
    success = await google_chat_service.send_alert("Prueba de Conexión", message, level="SUCCESS", space_id=space_id)
    
    if success:
        return {"status": "ok", "message": "Test message sent to Google Chat"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test message to Google Chat")


# ============================================================
# Google Chat Interactive Event Handler (Public)
# ============================================================

@public_router.post("/google-chat/event")
async def google_chat_event_handler(request: Request):
    """
    Handles interactive events from Google Chat (Workspace Add-on format)
    """
    import json
    
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    
    try:
        data = json.loads(body_str) if body_str else {}
    except Exception as e:
        logger.error(f"❌ Error parsing JSON: {e}")
        return {"text": "Error parsing request"}

    # Detectar el tipo de evento en el nuevo formato
    # El mensaje suele estar en chat -> messagePayload -> message
    chat_data = data.get("chat", {})
    message_payload = chat_data.get("messagePayload", {})
    message = message_payload.get("message", {})
    
    # Usuario
    user = chat_data.get("user", {})
    user_name = user.get("displayName", "Usuario")
    
    # Texto (usamos argumentText para evitar la mención @Bot) - MANTENEMOS EL CASO ORIGINAL para URLs y códigos sensibles
    text = (message.get("argumentText") or message.get("text") or "").strip()
    
    # Limpieza defensiva de menciones del bot de manera insensible a mayúsculas/minúsculas
    import re
    text = re.sub(r'(?i)@orbit\s*middleware\s*bot', '', text).strip()
    text = re.sub(r'(?i)@orbit_middleware_bot', '', text).strip()
    
    logger.info(f"📥 Message from {user_name}: {text}")

    # Si no hay texto pero hay un evento de interacción
    if not text and not chat_data:
        return {}

    # Todos los comandos (básicos y complejos) se procesan asíncronamente en el background task
    import asyncio

    # VÍA DE ESCAPE: Enviar mensaje asíncronamente y responder 200 OK de inmediato
    async def send_async_response(chat_data_obj, text_query, display_name):
        try:
            from .google_chat_service import google_chat_service
            from .models import GoogleChatAlertConfig, ResponseStatus, RequestLog
            from .config import settings
            from .telemetry import telemetry_service
            import uuid
            import time
            from datetime import datetime
            
            trace_id = f"gchat-{uuid.uuid4()}"
            start_time = time.time()
            status = ResponseStatus.OK
            mcp_latency_ms = None
            error_message = None
            
            # Función para buscar el space_id recursivamente
            def find_space_id(obj):
                if isinstance(obj, str) and obj.startswith("spaces/"):
                    return obj
                if isinstance(obj, dict):
                    for v in obj.values():
                        res = find_space_id(v)
                        if res: return res
                if isinstance(obj, list):
                    for item in obj:
                        res = find_space_id(item)
                        if res: return res
                return None

            space_id = find_space_id(chat_data_obj)
            
            if not space_id:
                logger.warning("⚠️ No se encontró el ID del espacio en la tarea de fondo.")
                return
                
            logger.info(f"🎯 ESPACIO ENCONTRADO: {space_id}")
            
            # Registrar el space_id en el conjunto de espacios activos en Redis
            try:
                if telemetry_service.redis:
                    await telemetry_service.redis.sadd("gchat:active_spaces", space_id)
            except Exception as sadd_err:
                logger.error(f"Failed to register space_id {space_id} to Redis active set: {sadd_err}")

            # Generar respuesta de forma asíncrona en el Background
            resp_text = ""
            text_query_lower = text_query.lower()
            if text_query_lower in ["estado", "status", "reporte", "health"]:
                resp_text = f"📊 *Estado de ORBIT*\n- API: 🟢 Activa\n- Redis: 🟢 Conectado\n- MCP: 🟢 Saludable\n\nHola *{display_name}*, el sistema opera con normalidad."
            
            else:
                # 1. DETECTAR SI ES UN ANUNCIO MULTI-ESPACIO
                text_stripped = text_query.strip()
                import re
                ann_match = re.match(r'(?i)(anuncio|anunciar)\s*:\s*(.*)', text_stripped)
                if not ann_match:
                    ann_match = re.match(r'(?i)(anuncio|anunciar)\s+(.*)', text_stripped)
                    
                if ann_match:
                    announcement_msg = ann_match.group(2).strip()
                    if announcement_msg:
                        logger.info(f"📢 ANUNCIO DETECTADO: '{announcement_msg}' emitido por {display_name}")
                        
                        spaces_to_announce = {space_id}
                        if settings.GOOGLE_CHATS_DEFAULT_SPACE:
                            spaces_to_announce.add(settings.GOOGLE_CHATS_DEFAULT_SPACE)
                            
                        try:
                            if telemetry_service.redis:
                                stored_spaces = await telemetry_service.redis.smembers("gchat:active_spaces")
                                if stored_spaces:
                                    for s in stored_spaces:
                                        s_str = s.decode() if isinstance(s, bytes) else str(s)
                                        if s_str.startswith("spaces/"):
                                            spaces_to_announce.add(s_str)
                        except Exception as redis_err:
                            logger.error(f"Error fetching active spaces from Redis: {redis_err}")
                            
                        announcement_text = (
                            f"📢 *ANUNCIO OFICIAL DE ORBIT* 📢\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"{announcement_msg}\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"_Emitido por: *{display_name}* desde {space_id}_"
                        )
                        
                        success_count = 0
                        failed_count = 0
                        direct_cfg = GoogleChatAlertConfig(
                            enabled=True,
                            sa_json_b64=settings.GOOGLE_CHATS_SA_BASE64 or "",
                            default_space_id=space_id
                        )
                        
                        for dest_space in spaces_to_announce:
                            try:
                                logger.info(f"Posting announcement to space: {dest_space}")
                                await google_chat_service.send_message(
                                    text=announcement_text,
                                    space_id=dest_space,
                                    config_override=direct_cfg
                                )
                                success_count += 1
                            except Exception as post_err:
                                logger.error(f"Failed to post announcement to {dest_space}: {post_err}")
                                failed_count += 1
                                
                        resp_text = (
                            f"📢 *¡Anuncio difundido con éxito!*\n"
                            f"Se ha enviado el anuncio a `{success_count}` espacio(s) activo(s) de Google Chat.\n"
                            f"❌ Fallidos: `{failed_count}`\n\n"
                            f"*Mensaje enviado:*\n{announcement_msg}"
                        )

                # Si no fue un anuncio, procesar adjuntos y consultas de forma normal
                if not resp_text:
                    # DETECTAR Y PARSEAR ARCHIVOS ADJUNTOS EN GOOGLE CHAT
                    def find_attachments(obj):
                        if isinstance(obj, dict):
                            if "attachment" in obj:
                                return obj["attachment"]
                            for v in obj.values():
                                res = find_attachments(v)
                                if res: return res
                        if isinstance(obj, list):
                            for item in obj:
                                res = find_attachments(item)
                                if res: return res
                        return None

                attachments = find_attachments(chat_data_obj)
                if attachments and len(attachments) > 0:
                    attachment = attachments[0]
                    content_name = attachment.get("contentName", "archivo")
                    mime_type = attachment.get("contentType", "").lower()
                    resource_name = attachment.get("attachmentDataRef", {}).get("resourceName")
                    
                    if resource_name:
                        logger.info(f"📎 File attachment found in chat: '{content_name}' ({mime_type}) | resourceName: {resource_name}")
                        try:
                            from .config_manager import config_manager
                            config = await config_manager.get_google_chat_config()
                            sa_b64 = config.sa_json_b64
                            
                            from .google_chat_service import google_chat_service
                            creds = await google_chat_service._get_credentials(sa_b64)
                            if creds:
                                from google.auth.transport.requests import Request
                                creds.refresh(Request())
                                
                                # Descargar binario usando Google Chat API
                                download_url = f"https://chat.googleapis.com/v1/media/{resource_name}?alt=media"
                                headers = {
                                    "Authorization": f"Bearer {creds.token}"
                                }
                                
                                logger.info(f"📥 Descargando archivo adjunto de Google Chat: {download_url}")
                                import httpx
                                async with httpx.AsyncClient() as client:
                                    attachment_resp = await client.get(download_url, headers=headers, timeout=30)
                                    if attachment_resp.status_code == 200:
                                        content_bytes = attachment_resp.content
                                        logger.info(f"✅ ¡Descarga de {len(content_bytes)} bytes exitosa!")
                                        
                                        # Parsear según el tipo de archivo
                                        extracted_text = ""
                                        is_image = "image" in mime_type or any(content_name.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"])
                                        
                                        if is_image:
                                            logger.info(f"📸 Procesando imagen adjunta en Google Chat usando HadesEngine...")
                                            try:
                                                from .hades_engine import hades_engine
                                                hades_report = await hades_engine.analyze_document_image(content_bytes, mime_type)
                                                if hades_report.get("success"):
                                                    score = hades_report["score"]
                                                    riesgo = hades_report["riesgo"]
                                                    emoji = hades_report["emoji"]
                                                    data = hades_report["data"]
                                                    forensic = hades_report["forensic_details"]
                                                    details_user = hades_report["details_user"]
                                                    
                                                    resp_text = (
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
                                                        resp_text += f"🚨 *MANIPULACIÓN DIGITAL:* Se detectó posible fotomontaje o edición digital.\n"
                                                    
                                                    scores = forensic.get("scores", {})
                                                    resp_text += (
                                                        f"- 🛡️ Elementos de Seguridad: `{scores.get('security_elements', 0)}/10`\n"
                                                        f"- 🖨️ Calidad de Impresión: `{scores.get('printing_quality', 0)}/10`\n"
                                                        f"- 💻 Manipulación Digital: `{scores.get('digital_manipulation', 0)}/10`\n"
                                                        f"- 🔤 Tipografía: `{scores.get('typography', 0)}/10`\n"
                                                        f"- 📸 Fotografía: `{scores.get('photography', 0)}/10`\n"
                                                    )
                                                    
                                                    if forensic.get("evidences"):
                                                        resp_text += "\n*Evidencias Encontradas:*\n"
                                                        for ev in forensic["evidences"][:3]:
                                                            resp_text += f"• _{ev}_\n"
                                                    
                                                    if details_user:
                                                        resp_text += "\n*Observaciones de Operación:*\n"
                                                        for obs in details_user:
                                                            resp_text += f"⚠️ _{obs}_\n"
                                                            
                                                    resp_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n_Análisis completado en {hades_report.get('latency_sec', 0):.2f}s_"
                                                else:
                                                    resp_text = f"❌ *Error en HadesEngine:* {hades_report.get('error')}"
                                            except Exception as he_err:
                                                logger.error(f"Error executing HadesEngine on image: {he_err}")
                                                resp_text = f"❌ *Error al procesar la imagen con HadesEngine:* {str(he_err)}"
                                        
                                        elif "pdf" in mime_type or content_name.endswith(".pdf"):
                                            logger.info(f"🛠️ Parseando archivo PDF adjunto usando pypdf...")
                                            import io
                                            from pypdf import PdfReader
                                            reader = PdfReader(io.BytesIO(content_bytes))
                                            text_pages = []
                                            for idx, page in enumerate(reader.pages):
                                                page_text = page.extract_text()
                                                if page_text:
                                                    text_pages.append(f"--- [PÁGINA {idx+1}] ---\n{page_text}")
                                            extracted_text = "\n\n".join(text_pages)
                                        else:
                                            extracted_text = content_bytes.decode('utf-8', errors='ignore')
                                            
                                        if not is_image:
                                            if extracted_text:
                                                logger.info(f"✅ Se extrajeron {len(extracted_text)} caracteres del archivo adjunto.")
                                                text_query = f"[CONTENIDO DEL ARCHIVO ADJUNTO '{content_name}':]\n{extracted_text}\n\n[Instrucción/Pregunta del usuario:]\n{text_query}"
                                            else:
                                                logger.warning(f"⚠️ El archivo adjunto '{content_name}' está vacío o no tiene texto extraíble.")
                                    else:
                                        logger.error(f"❌ Error al descargar archivo adjunto ({attachment_resp.status_code}): {attachment_resp.text}")
                        except Exception as attach_err:
                            logger.error(f"❌ Error procesando archivo adjunto de Google Chat: {attach_err}")
 
                # CONSULTA AL MCP DE FORMA ASÍNCRONA
                if not resp_text:
                    logger.info(f"🧠 Consultando MCP en segundo plano para: {text_query[:100]}...")
                    try:
                        from .mcp_client import mcp_client
                        
                        mcp_resp, query_status, latency, _ = await mcp_client.query(
                            user_text=text_query,
                            context={"source": "google_chat", "user": display_name},
                            agent_name=None
                        )
                        
                        status = query_status
                        mcp_latency_ms = latency
                        
                        if status == ResponseStatus.OK:
                            resp_text = f"{mcp_resp}\n\n_🕒 Latencia: {latency}ms_"
                        else:
                            resp_text = f"⚠️ *Error del MCP*\n{mcp_resp}"
                            error_message = "MCP error"
                    except Exception as e:
                        logger.error(f"❌ Error al consultar MCP desde Google Chat: {e}")
                        resp_text = f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}"
                        status = ResponseStatus.ERROR
                        error_message = str(e)

            # Usamos la configuración directa importada localmente
            direct_cfg = GoogleChatAlertConfig(
                enabled=True,
                sa_json_b64=settings.GOOGLE_CHATS_SA_BASE64 or "",
                default_space_id=space_id
            )
            
            logger.info(f"📤 Enviando mensaje asíncrono (Background)...")
            await google_chat_service.send_message(
                text=resp_text,
                space_id=space_id,
                config_override=direct_cfg
            )
            
            # Registrar telemetría y Google Sheets
            try:
                latency_ms = int((time.time() - start_time) * 1000)
                request_log = RequestLog(
                    trace_id=trace_id,
                    timestamp=datetime.utcnow(),
                    conversation_id=space_id,
                    contact_id=display_name,
                    channel="google_chat",
                    user_text=text_query,
                    mcp_response=resp_text,
                    status=status,
                    latency_ms=latency_ms,
                    mcp_latency_ms=mcp_latency_ms,
                    error_message=error_message,
                    retry_count=0
                )
                await telemetry_service.log_request(request_log)
                logger.info(f"📊 Google Chat message logged to Sheets telemetry successfully.")
            except Exception as log_err:
                logger.error(f"❌ Failed to write Google Chat message telemetry: {log_err}")
                
        except Exception as err:
            logger.error(f"❌ Error en Background Task de Google Chat: {err}")

    # Disparar la tarea de fondo de inmediato
    import asyncio
    asyncio.create_task(send_async_response(data, text, user_name))

    return {}


@public_router.post("/google-chat/notify")
async def google_chat_notify_handler(
    request: GoogleChatNotificationRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
):
    """
    Public notification endpoint for Google Chat, secured by WEBHOOK_SECRET.
    Allows routing by direct space_id or semantic destination.
    """
    import time
    start_time = time.time()

    # Validate webhook secret
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        logger.warning("❌ Invalid secret for Google Chat notify request")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
    # Determine target space_id
    target_space = request.space_id
    
    # If not direct space_id, try semantic mapping of destino
    if not target_space and request.destino:
        import os
        destino_lower = request.destino.lower()
        if destino_lower == "alertas":
            target_space = settings.GOOGLE_CHATS_DEFAULT_SPACE
        elif destino_lower == "soporte":
            target_space = os.getenv("GOOGLE_CHATS_SOPORTE_SPACE") or settings.GOOGLE_CHATS_DEFAULT_SPACE
        elif destino_lower == "ventas":
            target_space = os.getenv("GOOGLE_CHATS_VENTAS_SPACE") or settings.GOOGLE_CHATS_DEFAULT_SPACE
        else:
            target_space = settings.GOOGLE_CHATS_DEFAULT_SPACE

            
    # Send the alert using google_chat_service
    from .google_chat_service import google_chat_service
    success, detail = await google_chat_service.send_alert_detailed(
        title="Alerta de Orbit",
        message=request.message,
        level=request.level,
        space_id=target_space
    )
    
    # Registrar telemetría y Google Sheets
    try:
        import uuid
        from .telemetry import telemetry_service
        from .models import RequestLog, ResponseStatus
        
        trace_id = str(uuid.uuid4())
        latency_ms = int((time.time() - start_time) * 1000)
        
        request_log = RequestLog(
            trace_id=trace_id,
            timestamp=datetime.utcnow(),
            conversation_id=target_space or "unknown",
            contact_id="RespondIO_Agent",
            channel="respond_notificacion",
            user_text=request.message,
            mcp_response="Notification sent successfully" if success else f"Failed: {detail}",
            status=ResponseStatus.OK if success else ResponseStatus.ERROR,
            latency_ms=latency_ms,
            mcp_latency_ms=0,
            error_message=None if success else detail,
            retry_count=0
        )
        await telemetry_service.log_request(request_log)
        logger.info(f"📊 Google Chat notification logged to telemetry successfully.")
    except Exception as log_err:
        logger.error(f"❌ Failed to write notify telemetry: {log_err}")
    
    if success:
        return {"status": "ok", "message": "Notification sent to Google Chat"}
    else:
        logger.error(f"Failed to send notification: {detail}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification to Google Chat: {detail}")


@public_router.get("/debug/sheets")
async def debug_sheets(x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")):
    """Retrieve the cached Google Sheet ID currently used by ORBIT"""
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    from shared.redis_client import get_redis_client
    redis = await get_redis_client()
    cached_id = await redis.get("google_sheets:spreadsheet_id")
    return {
        "cached_id": cached_id.decode() if cached_id else None,
        "sheet_name": "ORBIT_Conversations_Log",
        "parent_folder_id": "1WDoC72ycPqsBvtjc_dj9Ljcue1QmvPMy"
    }























# ============================================================
# User Management Endpoints
# ============================================================

@router.get("/users", response_model=List[DashboardUser])
async def get_dashboard_users(
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get all dashboard users"""
    return await config_manager.get_users()


@router.post("/users")
async def add_dashboard_user(
    new_user: DashboardUser,
    admin: DashboardUser = Depends(require_admin_role)
):
    """Add or update a dashboard user with limit checks"""
    existing_users = await config_manager.get_users()
    
    # Check if we are updating or creating
    is_update = any(u.username == new_user.username for u in existing_users)
    
    if not is_update:
        # Enforce limits: Max 3 of each role
        admins = [u for u in existing_users if u.role == UserRole.ADMIN]
        supervisors = [u for u in existing_users if u.role == UserRole.SUPERVISOR]
        
        if new_user.role == UserRole.ADMIN and len(admins) >= 3:
            raise HTTPException(status_code=400, detail="Limit reached: Maximum 3 administrators allowed")
        
        if new_user.role == UserRole.SUPERVISOR and len(supervisors) >= 3:
            raise HTTPException(status_code=400, detail="Limit reached: Maximum 3 supervisors allowed")
            
    success = await config_manager.add_user(new_user)
    
    if success:
        # Audit log
        await config_manager.log_audit_action(AuditLogEntry(
            username=admin.username,
            role=admin.role,
            action=AuditAction.USER_MANAGEMENT,
            details=f"{'Updated' if is_update else 'Created'} user: {new_user.username} as {new_user.role}"
        ))
        return {"status": "ok", "message": f"User {new_user.username} {'updated' if is_update else 'created'}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save user")


@router.delete("/users/{username}")
async def delete_dashboard_user(
    username: str,
    admin: DashboardUser = Depends(require_admin_role)
):
    """Delete a dashboard user"""
    success = await config_manager.delete_user(username)
    
    if success:
        # Audit log
        await config_manager.log_audit_action(AuditLogEntry(
            username=admin.username,
            role=admin.role,
            action=AuditAction.USER_MANAGEMENT,
            details=f"Deleted user: {username}"
        ))
        return {"status": "ok", "message": f"User {username} deleted"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot delete user {username}")


# ============================================================
# Agent Management Endpoints
# ============================================================

@router.get("/agents", response_model=List[AgentConfig])
async def get_agents(
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get all dynamic agents"""
    return await config_manager.get_agents()


@router.post("/agents")
async def add_agent(
    agent: AgentConfig,
    admin: DashboardUser = Depends(require_admin_role)
):
    """Add or update an agent"""
    success = await config_manager.update_agent(agent)
    
    if success:
        # Audit log
        await config_manager.log_audit_action(AuditLogEntry(
            username=admin.username,
            role=admin.role,
            action=AuditAction.CONFIG_CHANGE,
            details=f"Updated agent: {agent.name} (Orchestrator: {agent.is_orchestrator})"
        ))
        return {"status": "ok", "message": f"Agent {agent.name} updated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save agent")


@router.delete("/agents/{name}")
async def delete_agent(
    name: str,
    admin: DashboardUser = Depends(require_admin_role)
):
    """Delete an agent"""
    # Don't allow deleting all agents if possible? 
    # For now, just delete.
    success = await config_manager.delete_agent(name)
    
    if success:
        # Audit log
        await config_manager.log_audit_action(AuditLogEntry(
            username=admin.username,
            role=admin.role,
            action=AuditAction.CONFIG_CHANGE,
            details=f"Deleted agent: {name}"
        ))
        return {"status": "ok", "message": f"Agent {name} deleted"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to delete agent {name}")


# ============================================================
# Audit Log Endpoints
# ============================================================

@router.get("/audit/logs", response_model=List[AuditLogEntry])
async def get_audit_logs(
    limit: int = 100,
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get recent audit logs"""
    return await config_manager.get_audit_logs(limit)


@router.post("/audit/log")
async def log_audit_generic(
    action: AuditAction,
    details: str,
    user: DashboardUser = Depends(verify_admin_credentials)
):
    """Log a generic audit action from the frontend"""
    entry = AuditLogEntry(
        username=user.username,
        role=user.role,
        action=action,
        details=details
    )
    await config_manager.log_audit_action(entry)
    return {"status": "ok"}


# ============================================================
# Telemetry Endpoints
# ============================================================

@router.get("/telemetry/requests", response_model=List[RequestLog])
async def get_recent_requests(
    limit: int = Query(default=100, le=1000),
    status: Optional[ResponseStatus] = None,
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get recent requests"""
    return await telemetry_service.get_recent_requests(limit, status)


@router.get("/telemetry/request/{trace_id}", response_model=RequestLog)
async def get_request_by_trace_id(
    trace_id: str,
    _: bool = Depends(verify_admin_credentials)
):
    """Get a specific request by trace ID"""
    request_log = await telemetry_service.get_request_by_trace_id(trace_id)
    
    if not request_log:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return request_log


@router.get("/telemetry/stats")
async def get_stats(
    hours: int = Query(default=24, le=168),  # Max 7 days
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get hourly statistics"""
    return await telemetry_service.get_hourly_stats(hours)


@router.get("/telemetry/summary")
async def get_summary(
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get summary statistics for today"""
    try:
        # Get today's stats
        stats = await telemetry_service.get_hourly_stats(24)
        
        if not stats:
            return {
                "total_requests": 0,
                "success_count": 0,
                "error_count": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0,
                "p95_latency_ms": 0
            }
        
        # Aggregate
        total_requests = sum(s["total_requests"] for s in stats)
        success_count = sum(s["success_count"] for s in stats)
        error_count = sum(s["error_count"] for s in stats)
        
        # Calculate averages
        total_latency = sum(s["avg_latency_ms"] * s["total_requests"] for s in stats)
        avg_latency = int(total_latency / total_requests) if total_requests > 0 else 0
        
        # Get max P95
        p95_latency = max((s["p95_latency_ms"] for s in stats), default=0)
        
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "total_requests": total_requests,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": round(success_rate, 2),
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency
        }
    
    except Exception as e:
        logger.error(f"Failed to get summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get summary")


# ============================================================
# Maintenance Endpoints
# ============================================================

@router.post("/maintenance/reload-config")
async def reload_config(
    user: DashboardUser = Depends(require_admin_role)
):
    """Reload configuration from Redis"""
    success = await config_manager.reload_config()
    
    if success:
        await config_manager.log_audit_action(AuditLogEntry(
            username=user.username,
            role=user.role,
            action=AuditAction.SYSTEM_MAINTENANCE,
            details="Reloaded system configuration from Redis"
        ))
        return {"status": "ok", "message": "Configuration reloaded"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reload config")


@router.post("/maintenance/clear-cache")
async def clear_cache(
    user: DashboardUser = Depends(require_admin_role)
):
    """Clear all cached data"""
    success = await config_manager.clear_cache()
    
    if success:
        await config_manager.log_audit_action(AuditLogEntry(
            username=user.username,
            role=user.role,
            action=AuditAction.CACHE_CLEAR,
            details="Cleared all system cache"
        ))
        return {"status": "ok", "message": "Cache cleared"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/maintenance/health", response_model=HealthResponse)
async def health_check_detailed(
    _: bool = Depends(verify_admin_credentials)
):
    """Detailed health check"""
    
    # Check MCP
    mcp_healthy = await mcp_client.health_check()
    mcp_status = "healthy" if mcp_healthy else "unhealthy"
    
    # Check Redis
    redis_status = "healthy" if telemetry_service.enabled else "disabled"
    
    # Overall status
    overall_status = "healthy" if mcp_healthy else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.API_VERSION,
        mcp_status=mcp_status,
        redis_status=redis_status
    )


@router.post("/maintenance/test-mcp")
async def test_mcp_connection(
    query: str = Query(default="Test query"),
    _: bool = Depends(verify_admin_credentials)
):
    """Test MCP connection with a query"""
    try:
        import time
        start_time = time.time()
        
        response, status, latency_ms, retry_count = await mcp_client.query(
            user_text=query,
            context={"test": True}
        )
        
        return {
            "status": "ok",
            "mcp_response": response,
            "response_status": status,
            "latency_ms": latency_ms,
            "retry_count": retry_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"MCP test failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/maintenance/system-info")
async def get_system_info(
    _: bool = Depends(verify_admin_credentials)
):
    """Get system information"""
    try:
        import psutil
        import os
        
        # Get process info
        process = psutil.Process(os.getpid())
        
        # Memory info
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # CPU info
        cpu_percent = process.cpu_percent(interval=0.1)
        
        # Uptime
        create_time = datetime.fromtimestamp(process.create_time())
        uptime = datetime.utcnow() - create_time
        
        return {
            "memory_mb": round(memory_mb, 2),
            "cpu_percent": round(cpu_percent, 2),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime).split('.')[0],
            "version": settings.API_VERSION,
            "python_version": os.sys.version.split()[0]
        }
    
    except ImportError:
        # psutil not available
        return {
            "memory_mb": 0,
            "cpu_percent": 0,
            "uptime_seconds": 0,
            "uptime_human": "N/A",
            "version": settings.API_VERSION,
            "python_version": "N/A",
            "note": "Install psutil for detailed system info"
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system info")


# ============================================================
# Circuit Breaker Info
# ============================================================

@router.get("/maintenance/circuit-breaker")
async def get_circuit_breaker_status(
    _: bool = Depends(verify_admin_credentials)
):
    """Get circuit breaker status"""
    return {
        "enabled": settings.CIRCUIT_BREAKER_ENABLED,
        "is_open": mcp_client.circuit_open,
        "failure_count": mcp_client.failure_count,
        "failure_threshold": settings.CIRCUIT_FAILURE_THRESHOLD,
        "timeout_seconds": settings.CIRCUIT_TIMEOUT
    }


@router.post("/maintenance/circuit-breaker/reset")
async def reset_circuit_breaker(
    user: DashboardUser = Depends(require_admin_role)
):
    """Reset circuit breaker"""
    mcp_client.circuit_open = False
    mcp_client.failure_count = 0
    
    # Audit log
    await config_manager.log_audit_action(AuditLogEntry(
        username=user.username,
        role=user.role,
        action=AuditAction.CIRCUIT_RESET,
        details="Manually reset system circuit breaker"
    ))
    
    logger.info(f"Circuit breaker manually reset by {user.username}")
    
    return {
        "status": "ok",
        "message": "Circuit breaker reset"
    }
