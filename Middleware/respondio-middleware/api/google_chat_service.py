"""
Service for sending notifications to Google Chat spaces.
"""

import base64
import json
import logging
import httpx
from typing import Optional
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from .config_manager import config_manager
from .models import GoogleChatAlertConfig

logger = logging.getLogger(__name__)


class GoogleChatService:
    """Service to send messages to Google Chat using a Service Account"""
    
    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/chat.messages.create",
            "https://www.googleapis.com/auth/chat.bot",
            "https://www.googleapis.com/auth/gmail.send"
        ]
        self._credentials_cache = {}

    async def _get_credentials(self, sa_b64: str):
        """Decode SA and load credentials"""
        try:
            sa_json = base64.b64decode(sa_b64).decode('utf-8')
            sa_info = json.loads(sa_json)
            return service_account.Credentials.from_service_account_info(
                sa_info, scopes=self.scopes
            )
        except Exception as e:
            logger.error(f"Failed to load Google Chat Service Account: {str(e)}")
            return None

    async def send_message(self, text: str, space_id: Optional[str] = None, config_override: Optional[GoogleChatAlertConfig] = None) -> bool:
        """
        Send a message to a Google Chat space.
        """
        if config_override:
            config = config_override
        else:
            config = await config_manager.get_google_chat_config()

        if not config.enabled and not config_override:
            logger.debug("Google Chat alerts are disabled")
            return False

        sa_b64 = config.sa_json_b64
        target_space = space_id or config.default_space_id

        if not sa_b64 or not target_space:
            logger.warning("Google Chat configuration incomplete (SA or Space missing)")
            return False

        # Space ID normalization (must start with spaces/)
        if not target_space.startswith("spaces/"):
            target_space = f"spaces/{target_space}"

        try:
            creds = self._credentials_cache.get(sa_b64)
            if not creds:
                logger.info(f"🔑 Cargando credenciales por primera vez para el espacio: {target_space}")
                creds = await self._get_credentials(sa_b64)
                if creds:
                    self._credentials_cache[sa_b64] = creds
            
            if not creds:
                logger.error("❌ No se pudieron obtener las credenciales de la Service Account")
                return False
            
            # Refresh token solo si no es válido
            if not creds.valid:
                logger.info("🔄 Refrescando token de Google Auth...")
                creds.refresh(Request())
                logger.info("🎟️ Token refrescado con éxito")

            url = f"https://chat.googleapis.com/v1/{target_space}/messages"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            
            payload = {"text": text}

            logger.info(f"🚀 Disparando POST a Google Chat API: {url}")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"❌ Error API Google Chat ({response.status_code}): {response.text}")
                    return False
                    
                logger.info(f"✅ ¡Mensaje enviado con éxito a {target_space}!")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Google Chat API error ({e.response.status_code}): {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"💥 Failed to send Google Chat message: {str(e)}")
            return False

    async def send_alert(self, title: str, message: str, level: str = "INFO", space_id: Optional[str] = None, sa_b64_override: Optional[str] = None) -> bool:
        """Helper to send a formatted alert message (returns bool status)"""
        ok, _ = await self.send_alert_detailed(title, message, level, space_id, sa_b64_override)
        return ok

    async def send_alert_detailed(
        self, 
        title: str, 
        message: str, 
        level: str = "INFO", 
        space_id: Optional[str] = None,
        sa_b64_override: Optional[str] = None
    ) -> tuple[bool, str]:
        """Send a formatted alert message and return detailed result status"""
        icon = "ℹ️"
        if level == "ERROR": icon = "🚨"
        elif level == "WARNING": icon = "⚠️"
        elif level == "SUCCESS": icon = "✅"
        
        formatted_text = f"{icon} *{title}*\n{message}"
        
        config = await config_manager.get_google_chat_config()
        
        sa_b64 = sa_b64_override or config.sa_json_b64
        target_space = space_id or config.default_space_id

        if not sa_b64:
            return False, "Google Chat configuration incomplete: Service Account JSON (sa_json_b64) is missing or empty"
            
        if not target_space:
            return False, "Google Chat configuration incomplete: Space ID is missing or empty"

        # Space ID normalization (must start with spaces/)
        if not target_space.startswith("spaces/"):
            target_space = f"spaces/{target_space}"

        # If sa_b64 credentials exist, allow alert execution
        if not config.enabled and not space_id and not sa_b64_override and not sa_b64:
            return False, "Google Chat alerts are globally disabled (enabled = False) and no Service Account credentials exist"

        try:
            # Decode and load credentials
            creds = await self._get_credentials(sa_b64)
            if not creds:
                return False, "Failed to decode or parse Service Account credentials"
            
            # Refresh token
            creds.refresh(Request())

            url = f"https://chat.googleapis.com/v1/{target_space}/messages"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            
            payload = {"text": formatted_text}

            logger.info(f"🚀 Disparando POST a Google Chat API: {url}")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    error_msg = f"Google Chat API returned status {response.status_code}: {response.text}"
                    logger.error(f"❌ {error_msg}")
                    return False, error_msg
                    
                logger.info(f"✅ ¡Mensaje enviado con éxito a {target_space}!")
                return True, "Message sent successfully"

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP status error: {e.response.status_code} - {e.response.text}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected exception: {str(e)}"
            logger.error(f"💥 {error_msg}")
            return False, error_msg


    async def send_unified_notification(
        self,
        dept_key: str,
        contact_id: str,
        user_text: str,
        nombre_usuario: Optional[str] = None,
        perfil_nlu: Optional[str] = None,
        codigo_envio: Optional[str] = None,
        numero_agencia: Optional[str] = None,
        telefono_contacto: Optional[str] = None,
        media_url: Optional[str] = None,
        space_id: Optional[str] = None,
        custom_summary: Optional[str] = None,
        is_out_of_hours: bool = False,
        turn_tag: Optional[str] = None,
        template_type: Optional[str] = None,
        status_transaccion: Optional[str] = None,
        status_retencion: Optional[str] = None,
        alerta_tipo: Optional[str] = None
    ) -> bool:
        """
        Generates and dispatches a structured Google Chat alert card compliant with the official
        specification (Plantilla 1, Plantilla 2, Plantilla 3, and Servicio al Cliente).
        """
        from datetime import datetime
        from zoneinfo import ZoneInfo
        import re
        from .config import settings

        timestamp_ct = datetime.now(ZoneInfo("America/Chicago")).strftime("%d/%m/%Y %H:%M:%S CT")
        dept_upper = dept_key.upper().strip()
        
        # Auto-detect template type if not explicitly set
        if not template_type:
            if dept_upper in ["FRAUDES", "FRAUDE", "BSA", "BSA_MONITORING"]:
                template_type = "plantilla_1"
            elif dept_upper in ["OVERSIGHT", "AGENT_OVERSIGHT", "VENTAS", "VENTAS_INTERNAS", "COBRANZA", "CAPACITACION", "CAPACITACIÓN", "CHEQUES", "SOPORTE_TECNICO", "TECNICO", "SOPORTE TÉCNICO", "SOPORTE TECNICO"]:
                template_type = "plantilla_2"
            elif dept_upper in ["CUMPLIMIENTO", "FRAUDE_ESPECIAL", "REVISION_RIESGO", "RETENIDO"]:
                template_type = "plantilla_3"
            elif dept_upper in ["SERVICIO_CLIENTE", "SERVICIO_AL_CLIENTE", "CS", "SOPORTE_HUMANO"]:
                template_type = "asignacion_cs"
            else:
                template_type = "plantilla_1"

        # Determine header and default space by template and department
        simultaneous_cs_dispatch = False
        
        if template_type == "plantilla_1":
            if dept_upper in ["FRAUDES", "FRAUDE"]:
                header = "⚠️ [ALERTA CRÍTICA - POSIBLE FRAUDE O ESTAFA - ATENCIÓN SERVICIO AL CLIENTE]" if is_out_of_hours else "🚨 [ALERTA CRÍTICA - POSIBLE FRAUDE O ESTAFA]"
                default_space = settings.GOOGLE_CHATS_FRAUDES_SPACE
                if is_out_of_hours:
                    simultaneous_cs_dispatch = True
            else:  # BSA / BSA_MONITORING
                header = "⚠️ [ALERTA CRÍTICA - POSIBLE ACTIVIDAD SOSPECHOSA - ATENCIÓN SERVICIO AL CLIENTE]" if is_out_of_hours else "🚨 [ALERTA CRÍTICA - POSIBLE ACTIVIDAD SOSPECHOSA]"
                default_space = settings.GOOGLE_CHATS_BSA_SPACE
                if is_out_of_hours:
                    simultaneous_cs_dispatch = True

        elif template_type == "plantilla_2":
            if dept_upper in ["OVERSIGHT", "AGENT_OVERSIGHT"]:
                header = "↪️ [DERIVACIÓN AGENT OVERSIGHT]"
                default_space = settings.GOOGLE_CHATS_OVERSIGHT_SPACE
            elif dept_upper in ["VENTAS", "VENTAS_INTERNAS"]:
                header = "↪️ [DERIVACIÓN VENTAS INTERNAS]"
                default_space = settings.GOOGLE_CHATS_VENTAS_SPACE
            elif dept_upper in ["COBRANZA"]:
                header = "↪️ [DERIVACIÓN COBRANZA]"
                default_space = settings.GOOGLE_CHATS_COBRANZA_SPACE
            elif dept_upper in ["CAPACITACION", "CAPACITACIÓN"]:
                header = "↪️ [DERIVACIÓN CAPACITACIÓN]"
                default_space = settings.GOOGLE_CHATS_CAPACITACION_SPACE
            elif dept_upper in ["CHEQUES"]:
                header = "↪️ [DERIVACIÓN CHEQUES]"
                default_space = settings.GOOGLE_CHATS_CHEQUES_SPACE
            elif dept_upper in ["SOPORTE_TECNICO", "TECNICO", "SOPORTE TÉCNICO", "SOPORTE TECNICO"]:
                header = "↪️ [DERIVACIÓN SOPORTE TÉCNICO]"
                default_space = settings.GOOGLE_CHATS_SOPORTE_SPACE
            else:
                header = f"↪️ [DERIVACIÓN {dept_upper}]"
                default_space = settings.GOOGLE_CHATS_DEFAULT_SPACE or settings.GOOGLE_CHATS_BSA_SPACE

        elif template_type == "plantilla_3":
            if dept_upper in ["FRAUDE_ESPECIAL", "REVISION_RIESGO", "VALIDATE_HOLD"]:
                header = "🔏 [TRANSACCIÓN EN REVISIÓN POR PREVENCIÓN DE FRAUDE]"
                default_space = settings.GOOGLE_CHATS_FRAUDES_SPACE
            else:
                header = "🚧 [DERIVACIÓN TRANSACCIÓN RETENIDA CUMPLIMIENTO]"
                default_space = settings.GOOGLE_CHATS_CUMPLIMIENTO_SPACE

        else:  # asignacion_cs
            if alerta_tipo == "input_no_procesable":
                header = "🚨 [ALERTA POR INPUT NO PROCESABLE]"
            elif alerta_tipo == "intencion_no_identificada":
                header = "⚠️ [ALERTA POR INTENCIÓN NO IDENTIFICADA]"
            elif alerta_tipo == "seguridad_incorrecta":
                header = "⚠️ [ALERTA POR DATOS DE VALIDACIÓN DE SEGURIDAD INCORRECTOS]"
            else:
                header = "👤 [ASIGNACIÓN A SERVICIO AL CLIENTE]"
            default_space = settings.GOOGLE_CHATS_SERVICIO_CLIENTE_SPACE or settings.GOOGLE_CHATS_CS_HIGH_PRIORITY_SPACE or settings.GOOGLE_CHATS_DEFAULT_SPACE or "spaces/AAQA3WL2JIk"

        # Perfil detection
        if not perfil_nlu:
            user_lower = user_text.lower()
            if any(k in user_lower for k in ["agencia", "sucursal", "ctr", "irs", "hermes", "balance", "agente"]):
                perfil_nlu = "Agente"
            elif any(k in user_lower for k in ["beneficiario", "recibo el dinero", "cobrar"]):
                perfil_nlu = "Beneficiario"
            elif any(k in user_lower for k in ["remitente", "hice el envío", "hice el envio", "mandé", "mande"]):
                perfil_nlu = "Remitente"
            else:
                perfil_nlu = "Cliente"

        clave_str = codigo_envio or "No proporcionada"
        agencia_str = numero_agencia if numero_agencia else "No proporcionado"
        nombre_str = nombre_usuario or "No proporcionado"
        contacto_str = telefono_contacto or contact_id
        
        motivo_raw = custom_summary or user_text or ""
        motivo_clean = re.sub(r'(?i)(?:\.?mensaje_notificacion|\$agent\.mensaje_notificacion|\$resumen_solicitud|\$resumen|\$intencion|null)', '', motivo_raw).strip()
        if not motivo_clean or len(motivo_clean) < 3:
            motivo_clean = "Reporte registrado de atención prioritaria."
        motivo_str = motivo_clean
        adjunto_str = media_url if media_url else "[Sin archivos adjuntos]"

        # Build card content according to official Template
        if template_type == "plantilla_2":
            # Plantilla 2: No includes Clave de la transacción
            formatted_card = (
                f"*{header}*\n"
                f"─────────────────────────────────────────\n"
                f"• *Horario de consulta:* {timestamp_ct}\n"
                f"• *ID de conversación:* `{contact_id}`\n"
                f"• *Perfil del usuario:* {perfil_nlu}\n"
                f"• *Nombre del usuario:* {nombre_str}\n"
                f"• *Contacto:* {contacto_str}\n"
                f"• *Número de agencia:* {agencia_str}\n"
                f"• *Motivo de consulta:* {motivo_str}\n"
                f"• *Archivos adjuntos del caso:* {adjunto_str}\n"
                f"• *Link de la conversación (en desarrollo):* No disponible\n"
                f"─────────────────────────────────────────"
            )
        elif template_type == "plantilla_3":
            # Plantilla 3: Transacciones Retenidas (includes Status de transacción and Status de retención)
            status_tx_str = status_transaccion or "Verify Hold"
            status_ret_str = status_retencion or "Retenido por revisión"
            formatted_card = (
                f"*{header}*\n"
                f"─────────────────────────────────────────\n"
                f"• *Horario de consulta:* {timestamp_ct}\n"
                f"• *ID de conversación:* `{contact_id}`\n"
                f"• *Perfil del usuario:* {perfil_nlu}\n"
                f"• *Nombre del usuario:* {nombre_str}\n"
                f"• *Contacto:* {contacto_str}\n"
                f"• *Clave de la transacción:* `{clave_str}`\n"
                f"• *Status de transacción:* {status_tx_str}\n"
                f"• *Status de la retención:* {status_ret_str}\n"
                f"• *Motivo de consulta:* {motivo_str}\n"
                f"• *Archivos adjuntos del caso:* {adjunto_str}\n"
                f"• *Link de la conversación (en desarrollo):* No disponible\n"
                f"─────────────────────────────────────────"
            )
        else:
            # Plantilla 1 (Prioridad Alta) and Asignación CS: Standard 10 fields
            formatted_card = (
                f"*{header}*\n"
                f"─────────────────────────────────────────\n"
                f"• *Horario de consulta:* {timestamp_ct}\n"
                f"• *ID de conversación:* `{contact_id}`\n"
                f"• *Perfil del usuario:* {perfil_nlu}\n"
                f"• *Nombre del usuario:* {nombre_str}\n"
                f"• *Contacto:* {contacto_str}\n"
                f"• *Clave de la transacción:* `{clave_str}`\n"
                f"• *Número de agencia:* {agencia_str}\n"
                f"• *Motivo de consulta:* {motivo_str}\n"
                f"• *Archivos adjuntos del caso:* {adjunto_str}\n"
                f"• *Link de la conversación (en desarrollo):* No disponible\n"
                f"─────────────────────────────────────────"
            )

        target_space = space_id or default_space
        
        # Debounce / Deduplication: Avoid duplicate cards within the same turn
        turn_key_suffix = f":{turn_tag}" if turn_tag else ""
        if contact_id and not contact_id.startswith("sim_test"):
            try:
                from shared.redis_client import get_redis_client
                redis = await get_redis_client()
                dedup_key = f"gchat:dedup:{contact_id}:{target_space}{turn_key_suffix}"
                already_sent = await redis.get(dedup_key)
                if already_sent:
                    logger.info(f"⏭️ [DEDUP] Suppressing duplicate Google Chat alert card for contact {contact_id} in {target_space}{turn_key_suffix} (debounced 30s)")
                    return True
                await redis.set(dedup_key, "1", ex=30)
            except Exception as dedup_err:
                logger.warning(f"Redis dedup check error: {dedup_err}")

        # Fire Primary Google Chat Notification
        chat_success = await self.send_message(formatted_card, space_id=target_space)
        
        # Dual Dispatch: If out of hours for Fraudes/BSA, dispatch simultaneously to CS High Priority Space
        if simultaneous_cs_dispatch:
            cs_space = (
                settings.GOOGLE_CHATS_CS_HIGH_PRIORITY_SPACE or 
                settings.GOOGLE_CHATS_SERVICIO_CLIENTE_SPACE or 
                settings.GOOGLE_CHATS_DEFAULT_SPACE
            )
            if cs_space and cs_space != target_space:
                try:
                    logger.info(f"🚨 [DUAL DISPATCH] Firing simultaneous alert to CS High Priority Space: {cs_space}")
                    await self.send_message(formatted_card, space_id=cs_space)
                except Exception as dual_err:
                    logger.warning(f"⚠️ Dual dispatch to CS space warning: {dual_err}")

        # Dual Dispatch: Fire Email Notification via Gmail API asynchronously
        try:
            from .email_service import email_service
            import asyncio
            asyncio.create_task(email_service.send_gmail_notification(
                subject=header,
                body_text=formatted_card
            ))
        except Exception as mail_err:
            logger.warning(f"⚠️ Non-blocking email dispatch warning: {mail_err}")

        return chat_success


# Singleton instance
google_chat_service = GoogleChatService()


