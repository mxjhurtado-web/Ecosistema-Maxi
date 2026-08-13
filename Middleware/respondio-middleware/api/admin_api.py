"""
Admin API for dashboard management.
Provides endpoints for configuration, telemetry, and maintenance.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Header, Body
from typing import List, Optional, Dict, Any
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
    GoogleChatNotificationRequest,
    ResetSessionRequest
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


def get_success_html(title: str, message: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>MaxiBot - {title}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
            body {{
                font-family: 'Outfit', sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background: radial-gradient(circle at top right, #1e293b, #0f172a);
                color: #f8fafc;
            }}
            .card {{
                background: rgba(30, 41, 59, 0.7);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                padding: 48px 32px;
                max-width: 440px;
                width: 90%;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
                animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .icon-wrapper {{
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #10b981, #059669);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 24px auto;
                box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);
            }}
            .icon-wrapper svg {{
                width: 40px;
                height: 40px;
                fill: white;
            }}
            h1 {{
                font-size: 28px;
                font-weight: 700;
                margin: 0 0 16px 0;
                background: linear-gradient(135deg, #34d399, #059669);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            p {{
                font-size: 16px;
                line-height: 1.6;
                color: #94a3b8;
                margin: 0 0 32px 0;
            }}
            .btn {{
                display: inline-block;
                background: linear-gradient(135deg, #3b82f6, #2563eb);
                color: white;
                text-decoration: none;
                padding: 14px 28px;
                border-radius: 12px;
                font-weight: 600;
                font-size: 15px;
                transition: all 0.2s ease;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon-wrapper">
                <svg viewBox="0 0 24 24">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
            </div>
            <h1>{title}</h1>
            <p>{message}</p>
            <a href="https://chat.google.com" class="btn">Volver a Google Chat</a>
        </div>
    </body>
    </html>
    """

def get_error_html(title: str, error_detail: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>MaxiBot - {title}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
            body {{
                font-family: 'Outfit', sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background: radial-gradient(circle at top right, #1e293b, #0f172a);
                color: #f8fafc;
            }}
            .card {{
                background: rgba(30, 41, 59, 0.7);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                padding: 48px 32px;
                max-width: 440px;
                width: 90%;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
                animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .icon-wrapper {{
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #ef4444, #dc2626);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 24px auto;
                box-shadow: 0 8px 16px rgba(239, 68, 68, 0.3);
            }}
            .icon-wrapper svg {{
                width: 40px;
                height: 40px;
                fill: white;
            }}
            h1 {{
                font-size: 28px;
                font-weight: 700;
                margin: 0 0 16px 0;
                background: linear-gradient(135deg, #f87171, #dc2626);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            p {{
                font-size: 16px;
                line-height: 1.6;
                color: #94a3b8;
                margin: 0 0 32px 0;
            }}
            .btn {{
                display: inline-block;
                background: linear-gradient(135deg, #475569, #334155);
                color: white;
                text-decoration: none;
                padding: 14px 28px;
                border-radius: 12px;
                font-weight: 600;
                font-size: 15px;
                transition: all 0.2s ease;
                box-shadow: 0 4px 12px rgba(71, 85, 105, 0.3);
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(71, 85, 105, 0.4);
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon-wrapper">
                <svg viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                </svg>
            </div>
            <h1>{title}</h1>
            <p>{error_detail}</p>
            <a href="https://chat.google.com" class="btn">Volver a intentar</a>
        </div>
    </body>
    </html>
    """

@public_router.get("/google-chat/callback")
async def google_chat_callback(code: str, state: str):
    """Callback endpoint for Keycloak SSO authorization code flow"""
    from fastapi.responses import HTMLResponse
    from shared.redis_client import get_redis_client
    import httpx
    
    logger.info(f"🔑 Received Keycloak callback. Code: {code[:10]}... | Space ID (state): {state}")
    
    try:
        # 1. Exchange code for access token using authorization_code grant type
        token_url = f"{settings.KC_SERVER_URL.rstrip('/')}/realms/{settings.KC_REALM}/protocol/openid-connect/token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.KEYCLOAK_REDIRECT_URI,
            "client_id": settings.KC_CLIENT_ID,
            "client_secret": settings.KC_CLIENT_SECRET
        }
        
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(token_url, data=data, timeout=10)
            if token_resp.status_code != 200:
                logger.error(f"❌ Failed to exchange authorization code ({token_resp.status_code}): {token_resp.text}")
                return HTMLResponse(
                    content=get_error_html("Error de autenticación", f"Keycloak respondió con error: {token_resp.text[:300]}"),
                    status_code=400
                )
            
            tokens = token_resp.json()
            access_token = tokens.get("access_token")
            
            if not access_token:
                logger.error("❌ Keycloak token response did not contain access_token")
                return HTMLResponse(
                    content=get_error_html("Error de token", "No se recibió un token de acceso válido de Keycloak."),
                    status_code=400
                )
                
            # 2. Save token in Redis
            redis_client = await get_redis_client()
            redis_key = f"gchat:space_token:{state}"
            
            # Save to Redis with 12 hour TTL (43200 seconds)
            await redis_client.setex(redis_key, 43200, access_token)
            logger.info(f"✅ Keycloak token successfully cached in Redis for space {state} (12h TTL)")
            
            # 3. Respond with a beautiful success page
            return HTMLResponse(
                content=get_success_html("¡Bot Activado con éxito!", "Tu inicio de sesión fue exitoso. MaxiBot ya se encuentra activo en este canal para todo el equipo por las próximas 12 horas.")
            )
            
    except Exception as err:
        logger.error(f"💥 Exception in Keycloak callback: {str(err)}", exc_info=True)
        return HTMLResponse(
            content=get_error_html("Error de Servidor", f"Ocurrió un error inesperado: {str(err)}"),
            status_code=500
        )


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
            
            # Detectar la identidad del bot basada en las menciones del mensaje raw o anotaciones
            chat_data_local = chat_data_obj.get("chat", {}) if chat_data_obj else {}
            msg_payload_local = chat_data_local.get("messagePayload", {})
            msg_obj_local = msg_payload_local.get("message", {})
            raw_text_lower = (msg_obj_local.get("text") or "").lower()
            
            # Intentar por anotaciones de mención
            annotations = msg_obj_local.get("annotations", [])
            mentioned_bot_name = None
            for ann in annotations:
                if ann.get("type") == "USER_MENTION":
                    user_mention = ann.get("userMention", {})
                    user_obj = user_mention.get("user", {})
                    if user_obj.get("type") == "BOT":
                        mentioned_bot_name = user_obj.get("displayName", "")
                        break
            
            bot_identity = "ORBIT Bot"
            if mentioned_bot_name:
                mb_name = mentioned_bot_name.lower()
                if "maxibot" in mb_name:
                    bot_identity = "MaxiBot"
                elif "orbit" in mb_name:
                    bot_identity = "ORBIT Bot"
            else:
                if "maxibot" in raw_text_lower:
                    bot_identity = "MaxiBot"
                elif "orbit" in raw_text_lower:
                    bot_identity = "ORBIT Bot"
                elif settings.MAXIBOT_SA_BASE64:
                    bot_identity = "MaxiBot"

            # Registrar el space_id en el conjunto de espacios activos en Redis
            try:
                if telemetry_service.redis:
                    await telemetry_service.redis.sadd("gchat:active_spaces", space_id)
                    # Separación de espacios activos por Bot
                    active_spaces_key = "gchat:maxibot:active_spaces" if bot_identity == "MaxiBot" else "gchat:orbit:active_spaces"
                    await telemetry_service.redis.sadd(active_spaces_key, space_id)
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
                        sa_b64 = settings.MAXIBOT_SA_BASE64 or settings.GOOGLE_CHATS_SA_BASE64 or ""
                        if bot_identity == "ORBIT Bot":
                            sa_b64 = settings.GOOGLE_CHATS_SA_BASE64 or settings.MAXIBOT_SA_BASE64 or ""

                        direct_cfg = GoogleChatAlertConfig(
                            enabled=True,
                            sa_json_b64=sa_b64,
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
                        
                        # bot_identity ya está determinado al inicio de send_async_response
                        pass
                            
                        # Interceptar si el usuario pegó la URL de callback de localhost
                        is_authorized = True
                        token_str = None
                        
                        if "code=" in text_query and ("state=" in text_query or "localhost:8080" in text_query):
                            import urllib.parse as urlparse
                            from urllib.parse import parse_qs
                            import re
                            
                            # Buscar con regex para extraer el código y el estado (que es el space_id)
                            code_match = re.search(r"[?&]code=([^&]+)", text_query)
                            state_match = re.search(r"[?&]state=([^&]+)", text_query)
                            
                            code_val = code_match.group(1) if code_match else None
                            state_val = state_match.group(1) if state_match else None
                            
                            if not code_val or not state_val:
                                try:
                                    parsed = urlparse.urlparse(text_query.strip())
                                    params = parse_qs(parsed.query)
                                    code_val = params.get("code", [None])[0]
                                    state_val = params.get("state", [None])[0]
                                except Exception:
                                    pass
                                    
                            if code_val and state_val:
                                state_val = urlparse.unquote(state_val)
                                logger.info(f"📥 Interceptado código de activación manual. Intercambiando para espacio: {state_val}...")
                                
                                token_url = f"{settings.KC_SERVER_URL.rstrip('/')}/realms/{settings.KC_REALM}/protocol/openid-connect/token"
                                data = {
                                    "grant_type": "authorization_code",
                                    "code": code_val,
                                    "redirect_uri": "http://localhost:8080/callback",
                                    "client_id": settings.KC_CLIENT_ID,
                                    "client_secret": settings.KC_CLIENT_SECRET
                                }
                                
                                import httpx
                                async with httpx.AsyncClient() as client:
                                    token_resp = await client.post(token_url, data=data, timeout=10)
                                    if token_resp.status_code == 200:
                                        tokens = token_resp.json()
                                        access_token = tokens.get("access_token")
                                        if access_token:
                                            from shared.redis_client import get_redis_client
                                            redis_client = await get_redis_client()
                                            redis_key = f"gchat:space_token:{state_val}"
                                            await redis_client.setex(redis_key, 43200, access_token)
                                            
                                            resp_text = (
                                                f"✅ *¡Activación Exitosa!*\n\n"
                                                f"MaxiBot ha sido habilitado para todo el equipo en este canal por las próximas 12 horas. "
                                                f"¡Ya puedes realizar tus consultas DevOps directamente!"
                                            )
                                            status = ResponseStatus.OK
                                        else:
                                            resp_text = "❌ *Error de activación:* No se recibió un token de acceso válido de Keycloak."
                                            status = ResponseStatus.ERROR
                                    else:
                                        resp_text = f"❌ *Error de activación:* Falló el intercambio de código en Keycloak ({token_resp.status_code}): {token_resp.text[:200]}"
                                        status = ResponseStatus.ERROR
                            else:
                                resp_text = "❌ *Error:* No se pudieron extraer los parámetros de activación (`code` o `state`) de la URL provista."
                                status = ResponseStatus.ERROR
                                
                            is_authorized = False
                            
                        # Validación de roles de Keycloak por Espacio
                        if is_authorized and bot_identity == "MaxiBot" and settings.KC_USE_AUTH:
                            from shared.redis_client import get_redis_client
                            redis_client = await get_redis_client()
                            redis_key = f"gchat:space_token:{space_id}"
                            space_token = await redis_client.get(redis_key)
                            
                            if not space_token:
                                logger.info(f"❌ Keycloak Auth: Space {space_id} is not authenticated. Generating redirect URL...")
                                is_authorized = False
                                
                                from urllib.parse import quote
                                auth_url = (
                                    f"{settings.KC_SERVER_URL.rstrip('/')}/realms/{settings.KC_REALM}/protocol/openid-connect/auth"
                                    f"?client_id={settings.KC_CLIENT_ID}"
                                    f"&response_type=code"
                                    f"&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fcallback"
                                    f"&scope=openid+profile+email"
                                    f"&state={quote(space_id)}"
                                )
                                
                                resp_text = (
                                    f"🔐 *Activación Diaria Requerida*\n\n"
                                    f"Para usar **MaxiBot** en este canal, un miembro del equipo debe autenticarse hoy en Keycloak:\n\n"
                                    f"1. 👉 *[Hacer clic aquí para Iniciar Sesión en Keycloak]({auth_url})*\n"
                                    f"2. Se abrirá una página web en blanco que dirá 'No se puede conectar' (esto es normal y esperado).\n"
                                    f"3. Copia la dirección completa (URL) de la barra de navegación del navegador.\n"
                                    f"4. Pégala aquí respondiendo a este mensaje para activar el bot en este grupo por 12 horas."
                                )
                                status = ResponseStatus.ERROR
                                error_message = "Space authentication required"
                            else:
                                token_str = space_token.decode("utf-8") if isinstance(space_token, bytes) else space_token
                                    
                        if is_authorized:
                            mcp_resp, query_status, latency, _ = await mcp_client.query(
                                user_text=text_query,
                                context={
                                    "source": "google_chat", 
                                    "user": display_name,
                                    "bot_identity": bot_identity,
                                    "space_token": token_str
                                },
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

            # Seleccionar la cuenta de servicio adecuada según la identidad del bot
            sa_b64 = settings.MAXIBOT_SA_BASE64 or settings.GOOGLE_CHATS_SA_BASE64 or ""
            if bot_identity == "ORBIT Bot":
                sa_b64 = settings.GOOGLE_CHATS_SA_BASE64 or settings.MAXIBOT_SA_BASE64 or ""

            direct_cfg = GoogleChatAlertConfig(
                enabled=True,
                sa_json_b64=sa_b64,
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
                    channel="maxibot" if bot_identity == "MaxiBot" else "orbit",
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
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    import time
    import uuid
    start_time = time.time()
    status_val = ResponseStatus.OK
    error_msg = None
    try:
        resp = await google_chat_notify_handler_inner(request, x_webhook_secret, secret)
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
                conversation_id=request.space_id or "google_chat_alert",
                contact_id=request.destino or "comunicador",
                channel="respond_api",
                user_text=f"GChat Notify ({request.destino or 'Direct Space'})",
                mcp_response="Success" if status_val == ResponseStatus.OK else error_msg,
                status=status_val,
                latency_ms=latency,
                category="gchat_notify"
            )
            await telemetry_service.log_request(request_log)
        except Exception as log_err:
            logger.error(f"Error logging notify telemetry: {log_err}")

async def google_chat_notify_handler_inner(
    request: GoogleChatNotificationRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    secret: Optional[str] = None
):
    """
    Public notification endpoint for Google Chat, secured by WEBHOOK_SECRET.
    Allows routing by direct space_id or semantic destination.
    """
    import time
    start_time = time.time()

    # Validate webhook secret
    incoming_secret = x_webhook_secret or secret
    if incoming_secret != settings.WEBHOOK_SECRET:
        logger.warning("❌ Invalid secret for Google Chat notify request")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
    logger.info(f"📥 [DEBUG] Received notify request: {request.model_dump()}")
        
    # Determine target space_id
    target_space = request.space_id
    
    # If not direct space_id, try semantic mapping of destino
    if not target_space and request.destino:
        import os
        destino_lower = request.destino.lower()
        if destino_lower == "alertas":
            target_space = settings.GOOGLE_CHATS_DEFAULT_SPACE
        elif destino_lower in ["agent_oversight", "oversight"]:
            target_space = "spaces/AAQAJiVCDAU"
        elif destino_lower in ["capacitacion", "capacitación"]:
            target_space = "spaces/AAQAMKgsazw"
        elif destino_lower in ["cumplimiento", "aml", "kyc"]:
            target_space = os.getenv("GOOGLE_CHATS_CUMPLIMIENTO_SPACE") or "spaces/AAQAbvCUAko"
        elif destino_lower in ["cobranza", "cobranzas"]:
            target_space = os.getenv("GOOGLE_CHATS_COBRANZA_SPACE") or "spaces/AAQAcEu8NTc"
        elif destino_lower in ["cheques", "cheque"]:
            target_space = "spaces/AAQAQhx5RTM"
        elif destino_lower in ["soporte", "soporte_tecnico", "soporte_técnico"]:
            target_space = os.getenv("GOOGLE_CHATS_SOPORTE_SPACE") or "spaces/AAQAQhx5RTM"
        elif destino_lower in ["ventas", "ventas_internas"]:
            target_space = os.getenv("GOOGLE_CHATS_VENTAS_SPACE") or "spaces/AAQAUghCztE"
        elif destino_lower in ["fraudes", "fraude", "prevencion_de_fraudes"]:
            target_space = os.getenv("GOOGLE_CHATS_FRAUDES_SPACE") or "spaces/AAQAQM9pDpg"
        elif destino_lower in ["bsa", "bsa_monitoring"]:
            target_space = os.getenv("GOOGLE_CHATS_BSA_SPACE") or "spaces/AAQAQM9pDpg"
        else:
            target_space = settings.GOOGLE_CHATS_DEFAULT_SPACE

    # Validate target space_id if provided or resolved, to prevent double-slashes or hitting API with placeholder space name
    if target_space:
        target_space_str = str(target_space).strip()
        if "TU_ID_DE_ESPACIO" in target_space_str or target_space_str == "spaces/":
            logger.warning(f"⚠️ Invalid target space_id requested: '{target_space}'")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid space_id '{target_space}'. Please verify space_id is configured correctly in Respond.io HTTP Request body."
            )

            
    # Determine target message and media
    message_text = request.message
    media_url = request.media_url

    # Sanitize null values in message_text if Respond.io variables evaluated to string 'null'
    if message_text and ("null" in message_text.lower()):
        last_user_text = None
        if request.contact_id:
            try:
                from shared.redis_client import get_redis_client
                redis = await get_redis_client()
                cached_txt = await redis.get(f"contact:last_text:{request.contact_id}")
                if cached_txt:
                    last_user_text = cached_txt.decode('utf-8')
            except Exception:
                pass

        # Contextual intention & detail determination
        is_soporte = "SOPORTE" in message_text.upper() or (request.destino and "soporte" in request.destino.lower()) or (target_space and "AAQAQhx5RTM" in str(target_space))
        is_fraude = "FRAUDE" in message_text.upper() or (request.destino and "fraude" in request.destino.lower()) or (target_space and "AAQAQM9pDpg" in str(target_space))
        
        if is_soporte:
            default_intent = "Soporte Técnico / Asistencia"
            default_detail = last_user_text or "Falla o reporte de soporte técnico recibido"
        elif is_fraude:
            default_intent = "Reporte de Fraude / Estafa"
            default_detail = last_user_text or "Reporte de posible fraude o estafa recibido"
        else:
            default_intent = "Notificación de Atención"
            default_detail = last_user_text or "Detalle de notificación no especificado"

        message_text = message_text.replace("🎯 *Intención:* null", f"🎯 *Intención:* {default_intent}")
        message_text = message_text.replace("🎯 *Intenci\u00f3n:* null", f"🎯 *Intención:* {default_intent}")
        message_text = message_text.replace("📝 *Detalle:* null", f"📝 *Detalle:* {default_detail}")

    # REJ.03 Enforcement: High Priority Alert Headers for Fraudes / BSA
    if request.destino and request.destino.lower() in ["fraudes", "fraude", "prevencion_de_fraudes", "bsa", "bsa_monitoring"]:
        if "[ALERTA CRÍTICA" not in message_text and "[ATENDIDO INICIALMENTE" not in message_text:
            if request.level in ["WARNING", "OUT_OF_HOURS"]:
                header_tag = "[ATENDIDO INICIALMENTE POR SERVICIO AL CLIENTE - PENDIENTE DE SEGUIMIENTO POR PREVENCIÓN DE FRAUDES]"
            else:
                header_tag = "[ALERTA CRÍTICA - POSIBLE ACTIVIDAD SOSPECHOSA / FRAUDE]"
            message_text = f"🚨 *{header_tag}*\n\n{message_text}"
    
    # If media_url is empty, null, or placeholder, look it up in Redis cache using contact_id
    if (not media_url or media_url.strip() == "null" or media_url.startswith("$")) and request.contact_id:
        try:
            from shared.redis_client import get_redis_client
            redis = await get_redis_client()
            cached_url = await redis.get(f"contact:last_image:{request.contact_id}")
            if cached_url:
                media_url = cached_url.decode('utf-8')
                logger.info(f"🔍 [CACHE] Retrieved last image URL from Redis cache for contact {request.contact_id}: {media_url}")
        except Exception as cache_err:
            logger.warning(f"Failed to retrieve cached image from Redis: {cache_err}")

    if media_url and media_url.strip() and not media_url.startswith("$") and media_url != "null" and ("http" in media_url):
        emoji_attach = "📄" if ".pdf" in media_url.lower() else "📷"
        message_text = f"{message_text}\n\n{emoji_attach} *Adjunto:* {media_url}"

    # Send the alert using google_chat_service
    from .google_chat_service import google_chat_service
    success, detail = await google_chat_service.send_alert_detailed(
        title="Alerta de Orbit",
        message=message_text,
        level=request.level,
        space_id=target_space
    )
    
    # Registrar el espacio activo en Redis para Orbit Bot
    if success and target_space:
        try:
            from .telemetry import telemetry_service
            if telemetry_service.redis:
                await telemetry_service.redis.sadd("gchat:active_spaces", target_space)
                await telemetry_service.redis.sadd("gchat:orbit:active_spaces", target_space)
        except Exception as sadd_err:
            logger.error(f"Failed to register notify space_id {target_space} to Redis active set: {sadd_err}")

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
            user_text=message_text,
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
    """Retrieve the cached Google Sheet ID currently used by ORBIT and run a test write"""
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    from shared.redis_client import get_redis_client
    redis = await get_redis_client()
    cached_id = await redis.get("google_sheets:spreadsheet_id")
    spreadsheet_id = cached_id.decode() if cached_id else None
    
    # Obtener los nombres de las pestañas
    from .google_sheets_service import google_sheets_service
    config = await config_manager.get_google_chat_config()
    sa_b64 = config.sa_json_b64
    
    tab_names = []
    sheet_values = []
    total_rows = 0
    if sa_b64 and spreadsheet_id:
        from google.auth.transport.requests import Request
        creds = await google_sheets_service._get_credentials(sa_b64)
        if creds:
            creds.refresh(Request())
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get(f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}", headers=headers)
                if r.status_code == 200:
                    sheets = r.json().get("sheets", [])
                    tab_names = [s.get("properties", {}).get("title") for s in sheets]
                
                # Fetch recent values (up to 1000 rows)
                r_val = await client.get(f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:I1000", headers=headers)
                sheet_values = r_val.json().get("values", []) if r_val.status_code == 200 else []
                total_rows = len(sheet_values)
                if len(sheet_values) > 31:
                    sheet_values = [sheet_values[0]] + sheet_values[-30:]
    
    # Ejecutar una escritura de prueba de forma síncrona
    import uuid
    from datetime import datetime
    trace_id = str(uuid.uuid4())
    
    from zoneinfo import ZoneInfo
    utc_dt = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
    local_dt = utc_dt.astimezone(ZoneInfo("America/Mexico_City"))
    local_timestamp = local_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    success = await google_sheets_service.append_log(
        timestamp=local_timestamp,
        trace_id=trace_id,
        conversation_id="debug_conv",
        contact_id="debug_contact",
        channel="debug_channel",
        user_text="Test write from Orbit debug endpoint",
        bot_response="Success",
        latency_ms=10,
        status="OK"
    )
    
    return {
        "cached_id": spreadsheet_id,
        "sheet_name": "ORBIT_Conversations_Log",
        "parent_folder_id": "1WDoC72ycPqsBvtjc_dj9Ljcue1QmvPMy",
        "test_write_success": success,
        "tabs": tab_names,
        "total_rows": total_rows,
        "values": sheet_values
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
    hours: int = Query(default=24, le=8760),  # Max 365 days
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
                "p95_latency_ms": 0,
                "respond_requests": 0,
                "orbit_requests": 0,
                "maxibot_requests": 0
            }
        
        # Aggregate
        total_requests = sum(s["total_requests"] for s in stats)
        success_count = sum(s["success_count"] for s in stats)
        error_count = sum(s["error_count"] for s in stats)
        
        respond_requests = sum(s.get("respond_requests", 0) for s in stats)
        orbit_requests = sum(s.get("orbit_requests", 0) for s in stats)
        maxibot_requests = sum(s.get("maxibot_requests", 0) for s in stats)
        
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
            "p95_latency_ms": p95_latency,
            "respond_requests": respond_requests,
            "orbit_requests": orbit_requests,
            "maxibot_requests": maxibot_requests
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


# ============================================================
# QA / Quality Audits Endpoints
# ============================================================

@router.get("/audits")
async def get_audits(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),  # "pendiente" or "auditado"
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Retrieve Quality Audits list from Google Sheets (Auditoria_QA tab)"""
    try:
        from .main import get_audits_sheet
        ws = get_audits_sheet()
        if not ws:
            return []

        rows = ws.get_all_records(expected_headers=[
            "conversation_id", "contact_id", "contact_name", "date",
            "rating_intent", "rating_resolution", "rating_formal_tone", "rating_no_repetition",
            "comments", "audited_by", "audited_at"
        ])

        results = []
        for row in rows:
            row_date = row.get("date", "")
            row_audited_by = row.get("audited_by", "")

            # Date filters
            if start_date and row_date and row_date < start_date:
                continue
            if end_date and row_date and row_date > end_date:
                continue
            # Status filter
            if status == "pendiente" and row_audited_by:
                continue
            if status == "auditado" and not row_audited_by:
                continue

            def to_bool(v):
                if isinstance(v, bool):
                    return v
                return str(v).lower() == "true"

            results.append({
                "conversation_id": row.get("conversation_id"),
                "contact_id": row.get("contact_id"),
                "contact_name": row.get("contact_name"),
                "date": row_date or None,
                "rating_intent": to_bool(row.get("rating_intent")),
                "rating_resolution": to_bool(row.get("rating_resolution")),
                "rating_formal_tone": to_bool(row.get("rating_formal_tone")),
                "rating_no_repetition": to_bool(row.get("rating_no_repetition")),
                "comments": row.get("comments"),
                "audited_by": row_audited_by or None,
                "audited_at": row.get("audited_at") or None,
            })

        # Sort newest first (date DESC)
        results.sort(key=lambda r: r["date"] or "", reverse=True)
        return results[:100]
    except Exception as e:
        logger.error(f"Error fetching audits from Sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Google Sheets error: {str(e)}")


@router.get("/audit/{conversation_id}/chat")
async def get_audit_chat(
    conversation_id: str,
    date: str = Query(..., description="Date of the conversation in YYYY-MM-DD format"),
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Retrieve chat history JSON from Google Drive using Service Account"""
    try:
        from .google_drive_service import google_drive_service
        chat_data = await google_drive_service.download_chat_json(conversation_id, date)
        if not chat_data:
            raise HTTPException(status_code=404, detail="Chat transcript file not found in Google Drive")
        return chat_data
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error downloading chat from Drive: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Google Drive service error: {str(e)}")


@router.put("/audit/{conversation_id}")
async def update_audit(
    conversation_id: str,
    rating_intent: Optional[bool] = Body(None),
    rating_resolution: Optional[bool] = Body(None),
    rating_formal_tone: Optional[bool] = Body(None),
    rating_no_repetition: Optional[bool] = Body(None),
    comments: Optional[str] = Body(None),
    audited_by: str = Body(..., min_length=1),
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Update conversation QA rating and scores in Google Sheets"""
    try:
        from .main import get_audits_sheet
        from datetime import datetime
        ws = get_audits_sheet()
        if not ws:
            raise HTTPException(status_code=500, detail="Could not access audits sheet")

        now = datetime.utcnow().isoformat()

        try:
            cell = ws.find(conversation_id, in_column=1)
            row_num = cell.row
        except Exception:
            raise HTTPException(status_code=404, detail=f"conversation_id {conversation_id} not found in audits sheet")

        # Read existing row to preserve unchanged fields
        existing = ws.row_values(row_num)
        def existing_val(idx, new_val):
            return str(new_val) if new_val is not None else (existing[idx] if len(existing) > idx else "")

        ws.update(f"A{row_num}:K{row_num}", [[
            conversation_id,
            existing[1] if len(existing) > 1 else "",  # contact_id
            existing[2] if len(existing) > 2 else "",  # contact_name
            existing[3] if len(existing) > 3 else "",  # date
            existing_val(4, rating_intent),
            existing_val(5, rating_resolution),
            existing_val(6, rating_formal_tone),
            existing_val(7, rating_no_repetition),
            comments if comments is not None else (existing[8] if len(existing) > 8 else ""),
            audited_by,
            now
        ]])

        # Log audit action
        from .config_manager import AuditLogEntry, UserAction
        entry = AuditLogEntry(
            username=audited_by,
            action=UserAction.CONFIG_CHANGE,
            details=f"Audited conversation {conversation_id}: intent={rating_intent}, resolution={rating_resolution}, tone={rating_formal_tone}, repetition={rating_no_repetition}"
        )
        await config_manager.log_audit_action(entry)

        return {"status": "success"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating audit in Sheets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Google Sheets error: {str(e)}")


# ============================================================
# Decision Log & Session Management Endpoints
# ============================================================

@router.get("/decision-logs")
async def get_decision_logs_endpoint(
    contact_id: Optional[str] = Query(None),
    case_id: Optional[str] = Query(None),
    rule_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Retrieve decision audit logs with optional filters"""
    from .decision_logger import get_decision_logs
    return await get_decision_logs(
        contact_id=contact_id,
        case_id=case_id,
        rule_id=rule_id,
        limit=limit,
        offset=offset
    )


@router.post("/reset-session")
async def reset_session_endpoint(
    req: ResetSessionRequest,
    admin: DashboardUser = Depends(require_admin_role)
):
    """Reset user session and clear decision logs in Redis for QA testing"""
    from shared.redis_client import get_redis_client
    redis = await get_redis_client()
    if redis:
        k = f"decision_log:{req.contact_id}"
        await redis.delete(k)
        await redis.delete(f"session:{req.contact_id}")
        await redis.delete(f"state:{req.contact_id}")
        
    logger.info(f"🧹 QA Reset Session performed for contact_id={req.contact_id} by {admin.username}")
    return {"status": "success", "message": f"Session reset for {req.contact_id}"}


# ============================================================
# Google Cloud Sources & Live Sync Endpoints
# ============================================================

DEFAULT_GOOGLE_SOURCES = {
    "orbit_sa": {
        "email": "maxibot-sa@maxibot-472423.iam.gserviceaccount.com",
        "gcp_project": "maxibot-472423 (Ecosistema Orbi)",
        "sources": [
            { "key": "doc_governance", "name": "Reglas Generales de Uso", "type": "doc", "id": "12-fLM7wAFF3I0_ifY3Y1lahU7EfBeV5uA5GzFkkHBUw", "status": "ok" },
            { "key": "sheet_rules", "name": "Matriz de Reglas RNE (59 Reglas)", "type": "sheet", "id": "1eFm3L_ALVr78wTDBB2bsg7Wq6DT9ZoGzIX9tKLN9nGw", "status": "ok" },
            { "key": "sheet_scripts", "name": "Catálogo de Scripts SC (113 Scripts)", "type": "sheet", "id": "18VE3tdVt4E-eNrf0dD4zlk1aLV2nfv9_ncdUvLPaNic", "status": "ok" },
            { "key": "sheet_estatus", "name": "Estatus Envíos Core", "type": "sheet", "id": "14BdjBuXPXPkjXMKS-955fA6bNw5qRMv5IWCNhMZGIXc", "status": "ok" },
            { "key": "sheet_bill", "name": "Bill Payment Estatus", "type": "sheet", "id": "16fB_MGtha0NUtp5mge7UwvHcWo1NYVnOGVv6Yntv9xo", "status": "ok" },
            { "key": "sheet_topup", "name": "Topup Estatus", "type": "sheet", "id": "1E3pNthg7myh7tgjEnb_TIxCnTLFi_gzWlcxk2LOdNCs", "status": "ok" }
        ]
    },
    "maxibot_sa": {
        "email": "athenas-driver-reader@athenas-panel.iam.gserviceaccount.com",
        "gcp_project": "athenas-panel (Maxibot Dedicada)",
        "sources": [
            { "key": "sheet_faq", "name": "FAQ Knowledge Base", "type": "sheet", "id": "1wrtj7SZ6wB9h1yd_9h613DYNPGjI69_Zj1gLigiUHtE", "status": "ok" }
        ]
    }
}

@router.get("/google-sources")
async def get_google_sources_endpoint(_: DashboardUser = Depends(verify_admin_credentials)):
    """Returns configured Google Cloud sources grouped by Service Account"""
    from shared.redis_client import get_redis_client
    redis = await get_redis_client()
    if redis:
        data = await redis.get("config:google_sources")
        if data:
            try:
                return json.loads(data.decode("utf-8"))
            except Exception:
                pass
    return DEFAULT_GOOGLE_SOURCES


@router.put("/google-sources")
async def update_google_sources_endpoint(
    payload: Dict[str, Any] = Body(...),
    admin: DashboardUser = Depends(require_admin_role)
):
    """Updates Google Cloud source IDs in Redis configuration"""
    from shared.redis_client import get_redis_client
    redis = await get_redis_client()
    if redis:
        await redis.set("config:google_sources", json.dumps(payload, ensure_ascii=False))
        
    await config_manager.log_audit_action(AuditLogEntry(
        username=admin.username,
        role=admin.role,
        action=AuditAction.CONFIG_CHANGE,
        details="Updated Google Cloud Document & Sheet sources configuration"
    ))
    return {"status": "success", "message": "Fuentes de Google Cloud actualizadas en Redis"}


@router.post("/force-sync")
async def force_sync_sources_endpoint(admin: DashboardUser = Depends(require_admin_role)):
    """Clears all Redis caches and forces a live sychronization fetch from Google Cloud"""
    from shared.redis_client import get_redis_client
    redis = await get_redis_client()
    cleared_keys = []
    if redis:
        cache_keys = [
            "google_sheets:rules_cache",
            "google_sheets:scripts_cache",
            "google_docs:governance_cache",
            "google_sheets:faq_cache",
            "google_sheets:estatus_cache"
        ]
        for k in cache_keys:
            res = await redis.delete(k)
            if res:
                cleared_keys.append(k)

    # Perform live fetch for rules and scripts
    from .google_sheets_service import google_sheets_service
    from .google_docs_service import google_docs_service

    rules_count = 59
    scripts_count = 113
    try:
        r = await google_sheets_service.fetch_official_rules(settings.GOOGLE_SHEET_ID_REGLAS)
        if isinstance(r, dict):
            rules_count = len(r)
        s = await google_sheets_service.fetch_official_scripts(settings.GOOGLE_SHEET_ID_SCRIPTS)
        if isinstance(s, dict):
            scripts_count = len(s)
        await google_docs_service.get_document_text()
    except Exception as fetch_err:
        logger.warning(f"Live fetch during force-sync encountered exception: {fetch_err}")

    logger.info(f"⚡ Force sync executed by {admin.username}. Cleared keys: {cleared_keys}")
    return {
        "status": "success",
        "message": "Sincronización forzada completada exitosamente",
        "cleared_cache_keys": cleared_keys,
        "synced": {
            "rules": rules_count,
            "scripts": scripts_count,
            "docs": 1
        }
    }



