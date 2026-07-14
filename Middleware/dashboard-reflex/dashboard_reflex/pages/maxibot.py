import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.components.styling import (
    GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, BORDER_COLOR, TEXT_MUTED,
    glass_container, status_badge
)
from dashboard_reflex.api.client import api_client
import os
import redis
from datetime import datetime

# Connect to Redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    r_client = redis.from_url(redis_url, decode_responses=True)
except Exception:
    r_client = None

from pydantic import BaseModel

class MaxiSpace(BaseModel):
    space_id: str = ""
    is_authenticated: bool = False
    ttl_minutes: int = 0
    ttl_formatted: str = "N/A"

class GChatInteraction(BaseModel):
    timestamp: str = ""
    space_id: str = ""
    user_text: str = ""
    bot_reply: str = ""
    latency_ms: int = 0
    status: str = "ok"

class MaxiBotState(rx.State):
    spaces: list[MaxiSpace] = []
    interactions: list[GChatInteraction] = []
    use_keycloak: bool = False
    is_loading: bool = False
    
    # Stats
    total_spaces: int = 0
    authenticated_spaces: int = 0
    total_messages: int = 0
    avg_latency: int = 0

    async def load_data(self):
        self.is_loading = True
        
        # 1. Load use_keycloak configuration from API
        mcp_cfg = await api_client.get_mcp_config()
        if mcp_cfg:
            self.use_keycloak = mcp_cfg.get("use_keycloak", False)
            
        # 2. Load spaces from Redis
        space_list = []
        if r_client:
            try:
                active_spaces = r_client.smembers("gchat:active_spaces")
                for s_id in active_spaces:
                    token_key = f"gchat:space_token:{s_id}"
                    exists = r_client.exists(token_key)
                    ttl = 0
                    ttl_str = "Expirado"
                    if exists:
                        ttl_sec = r_client.ttl(token_key)
                        if ttl_sec > 0:
                            ttl = int(ttl_sec / 60)
                            hours = ttl // 60
                            mins = ttl % 60
                            ttl_str = f"{hours}h {mins}m"
                        else:
                            ttl_str = "Persistente"
                    space_list.append(
                        MaxiSpace(
                            space_id=s_id,
                            is_authenticated=exists > 0,
                            ttl_minutes=ttl,
                            ttl_formatted=ttl_str
                        )
                    )
            except Exception as e:
                rx.toast.error(f"Error cargando espacios desde Redis: {str(e)}")
        
        self.spaces = space_list
        self.total_spaces = len(space_list)
        self.authenticated_spaces = len([s for s in space_list if s.is_authenticated])

        # 3. Load interactions from API (telemetry)
        history = await api_client.get_recent_requests(limit=100)
        interaction_list = []
        latency_sum = 0
        
        if history:
            gchat_reqs = [
                r for r in history 
                if r.get("channel", "").lower() in ["google_chat", "google-chat", "gchat"]
            ]
            
            for req in gchat_reqs[:20]:  # Limit to last 20
                latency = req.get("latency_ms", 0)
                latency_sum += latency
                interaction_list.append(
                    GChatInteraction(
                        timestamp=req.get("timestamp", "")[:19],
                        space_id=req.get("trace_id", "")[:8],  # Represent conversation trace reference
                        user_text=req.get("user_text", "N/A"),
                        bot_reply=req.get("mcp_response", "Sin respuesta"),
                        latency_ms=latency,
                        status=req.get("status", "ok")
                    )
                )
            
            self.total_messages = len(gchat_reqs)
            self.avg_latency = int(latency_sum / len(interaction_list)) if interaction_list else 0

        self.interactions = interaction_list
        self.is_loading = False

    async def toggle_keycloak(self, checked: bool):
        self.use_keycloak = checked
        
        # Load full config first to preserve other settings
        mcp_cfg = await api_client.get_mcp_config()
        if not mcp_cfg:
            rx.toast.error("Error al obtener la configuración del MCP.")
            return
            
        payload = {
            "url": mcp_cfg.get("url", ""),
            "timeout": mcp_cfg.get("timeout", 30),
            "max_retries": mcp_cfg.get("max_retries", 3),
            "retry_delay": mcp_cfg.get("retry_delay", 2),
            "mcp_token": mcp_cfg.get("mcp_token", ""),
            "use_keycloak": checked,
            "kc_server_url": mcp_cfg.get("kc_server_url", ""),
            "kc_realm": mcp_cfg.get("kc_realm", ""),
            "kc_client_id": mcp_cfg.get("kc_client_id", ""),
            "kc_client_secret": mcp_cfg.get("kc_client_secret", ""),
            "gemini_api_key": mcp_cfg.get("gemini_api_key", ""),
            "emergency_mode": mcp_cfg.get("emergency_mode", False)
        }
        
        success = await api_client.update_mcp_config(payload)
        if success:
            rx.toast.success(f"Keycloak Auth {'ACTIVADO' if checked else 'DESACTIVADO'} para MaxiBot.")
            # Log audit action
            await api_client.log_audit_action({
                "username": self.router.session.get("username", "admin"),
                "role": self.router.session.get("role", "admin"),
                "action": "CONFIG_CHANGE",
                "details": f"Toggled MaxiBot Keycloak Auth to {checked}"
            })
        else:
            rx.toast.error("Error al guardar la configuración en el API.")
            self.use_keycloak = not checked

    async def revoke_space(self, space_id: str):
        if r_client:
            try:
                token_key = f"gchat:space_token:{space_id}"
                r_client.delete(token_key)
                r_client.srem("gchat:active_spaces", space_id)
                rx.toast.success(f"Acceso revocado para el espacio: {space_id}")
                # Log audit action
                await api_client.log_audit_action({
                    "username": self.router.session.get("username", "admin"),
                    "role": self.router.session.get("role", "admin"),
                    "action": "SECURITY_ACTION",
                    "details": f"Revoked Google Chat space authentication for {space_id}"
                })
                await self.load_data()
            except Exception as e:
                rx.toast.error(f"Error al revocar espacio: {str(e)}")

    async def on_load(self):
        await self.load_data()

def space_row(space: MaxiSpace) -> rx.Component:
    """Renders a single row in the authenticated spaces table."""
    status_color = rx.cond(space.is_authenticated, "green", "ruby")
    status_label = rx.cond(space.is_authenticated, "🟢 Conectado (SSO)", "🔴 Requiere Auth")
    
    return rx.table.row(
        rx.table.cell(space.space_id, font_family="Courier New", font_size="13px"),
        rx.table.cell(rx.badge(status_label, color_scheme=status_color)),
        rx.table.cell(space.ttl_formatted, font_size="13px"),
        rx.table.cell(
            rx.button(
                "Revocar",
                size="1",
                color_scheme="ruby",
                variant="soft",
                on_click=lambda: MaxiBotState.revoke_space(space.space_id),
                style={"cursor": "pointer"}
            )
        )
    )

def interaction_row(intr: GChatInteraction) -> rx.Component:
    """Renders a recent interaction row."""
    status_color = rx.cond(intr.status == "ok", "green", "ruby")
    
    return rx.table.row(
        rx.table.cell(intr.timestamp, font_size="12px"),
        rx.table.cell(intr.space_id, font_family="Courier New", font_size="12px"),
        rx.table.cell(intr.user_text, max_width="200px", is_truncated=True, font_size="13px"),
        rx.table.cell(intr.bot_reply, max_width="300px", is_truncated=True, font_size="13px"),
        rx.table.cell(intr.latency_ms.to(str) + "ms", font_size="12px"),
        rx.table.cell(rx.badge(intr.status, color_scheme=status_color))
    )

def maxibot_page() -> rx.Component:
    """The MaxiBot Dedicated control panel page."""
    
    # Stats row
    stats = rx.grid(
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Espacios Registrados", font_size="12px", color=TEXT_MUTED),
                    rx.heading(MaxiBotState.total_spaces.to(str), size="6", color="#FFFFFF"),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("layers", color=ACCENT_BLUE, size=24),
                width="100%"
            ),
            style={"padding": "18px"}
        ),
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Espacios Autenticados (SSO)", font_size="12px", color=TEXT_MUTED),
                    rx.heading(MaxiBotState.authenticated_spaces.to(str), size="6", color="var(--green-9)"),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("shield-check", color="var(--green-9)", size=24),
                width="100%"
            ),
            style={"padding": "18px"}
        ),
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Mensajes en Google Chat", font_size="12px", color=TEXT_MUTED),
                    rx.heading(MaxiBotState.total_messages.to(str), size="6", color=ACCENT_PURPLE),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("message-square-code", color=ACCENT_PURPLE, size=24),
                width="100%"
            ),
            style={"padding": "18px"}
        ),
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Latencia Promedio Chat", font_size="12px", color=TEXT_MUTED),
                    rx.heading(MaxiBotState.avg_latency.to(str) + " ms", size="6", color="#FFFFFF"),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("zap", color="#FFD700", size=24),
                width="100%"
            ),
            style={"padding": "18px"}
        ),
        columns="4",
        spacing="4",
        width="100%",
        style={"margin_bottom": "24px"}
    )

    # 🔒 SSO Control Banner and Switch
    sso_control = glass_container(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.heading("🔑 Autenticación SSO Keycloak (MaxiBot)", size="4", color="#FFFFFF"),
                    rx.text("Controla si el bot requiere autenticación institucional en los espacios de Google Chat.", font_size="13px", color=TEXT_MUTED),
                    align_items="start",
                    spacing="1"
                ),
                rx.spacer(),
                rx.hstack(
                    rx.switch(checked=MaxiBotState.use_keycloak, on_change=MaxiBotState.toggle_keycloak),
                    rx.text(rx.cond(MaxiBotState.use_keycloak, "REQUERIDO (Estricto)", "DESACTIVADO (Prueba)"), font_size="14px", font_weight="bold", color=rx.cond(MaxiBotState.use_keycloak, "var(--green-9)", "var(--amber-9)")),
                    spacing="3",
                    align_items="center"
                ),
                width="100%",
                align_items="center"
            ),
            
            # Warning banner when Keycloak SSO is False
            rx.cond(
                ~MaxiBotState.use_keycloak,
                rx.box(
                    rx.hstack(
                        rx.icon("triangle_alert", color="var(--amber-9)", size=20),
                        rx.vstack(
                            rx.text("⚠️ Advertencia: Control de Acceso Desactivado", font_weight="bold", font_size="14px", color="var(--amber-9)"),
                            rx.text("El bot responderá libremente en todos los espacios sin verificar credenciales de Keycloak. Use este modo solo para desarrollo o pruebas controladas.", font_size="12px", color="#FFFFFF"),
                            align_items="start",
                            spacing="0"
                        ),
                        spacing="3",
                        align_items="start"
                    ),
                    style={
                        "padding": "12px 16px",
                        "background_color": "rgba(245, 158, 11, 0.08)",
                        "border_left": "4px solid var(--amber-9)",
                        "border_radius": "6px",
                        "margin_top": "16px",
                        "width": "100%"
                    }
                )
            ),
            width="100%"
        ),
        style={"padding": "20px", "margin_bottom": "24px"}
    )

    # 🏢 Table of Authenticated Spaces
    spaces_table = glass_container(
        rx.vstack(
            rx.hstack(
                rx.heading("🏢 Espacios de Trabajo Activos", size="3", color="#FFFFFF"),
                rx.spacer(),
                rx.button(
                    rx.hstack(rx.icon("refresh_cw", size=12), rx.text("Refrescar"), spacing="2"),
                    on_click=MaxiBotState.load_data,
                    size="1",
                    variant="soft",
                    style={"cursor": "pointer"}
                ),
                width="100%",
                align_items="center",
                style={"margin_bottom": "12px"}
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Space ID"),
                        rx.table.column_header_cell("Estatus"),
                        rx.table.column_header_cell("Expiración Token (12h)"),
                        rx.table.column_header_cell("Acciones")
                    )
                ),
                rx.table.body(
                    rx.cond(
                        MaxiBotState.spaces.length() == 0,
                        rx.table.row(
                            rx.table.cell("No hay espacios activos en Redis", colspan=4, style={"text_align": "center", "color": TEXT_MUTED})
                        ),
                        rx.foreach(
                            MaxiBotState.spaces,
                            space_row
                        )
                    )
                ),
                variant="surface",
                style={"width": "100%"}
            ),
            width="100%"
        ),
        style={"padding": "20px", "margin_bottom": "24px"}
    )

    # 💬 Recent interactions in GChat
    interactions_table = glass_container(
        rx.vstack(
            rx.heading("💬 Conversaciones Recientes en Google Chat", size="3", color="#FFFFFF", style={"margin_bottom": "12px"}),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Fecha/Hora"),
                        rx.table.column_header_cell("Trace ID"),
                        rx.table.column_header_cell("Mensaje Usuario"),
                        rx.table.column_header_cell("Respuesta Bot (MCP)"),
                        rx.table.column_header_cell("Latencia"),
                        rx.table.column_header_cell("Estatus")
                    )
                ),
                rx.table.body(
                    rx.cond(
                        MaxiBotState.interactions.length() == 0,
                        rx.table.row(
                            rx.table.cell("No se encontraron solicitudes de Google Chat recientemente", colspan=6, style={"text_align": "center", "color": TEXT_MUTED})
                        ),
                        rx.foreach(
                            MaxiBotState.interactions,
                            interaction_row
                        )
                    )
                ),
                variant="surface",
                style={"width": "100%"}
            ),
            width="100%"
        ),
        style={"padding": "20px"}
    )

    content = rx.vstack(
        stats,
        sso_control,
        spaces_table,
        interactions_table,
        width="100%",
        spacing="1"
    )

    return protected_layout(content, "MaxiBot Control Panel", "/maxibot")
