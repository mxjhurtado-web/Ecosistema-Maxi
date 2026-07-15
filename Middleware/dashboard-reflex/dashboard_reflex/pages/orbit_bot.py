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
from pydantic import BaseModel

# Connect to Redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    r_client = redis.from_url(redis_url, decode_responses=True)
except Exception:
    r_client = None

class OrbitSpace(BaseModel):
    space_id: str = ""
    is_active: bool = True

class OrbitInteraction(BaseModel):
    timestamp: str = ""
    space_id: str = ""
    user_text: str = ""
    bot_reply: str = ""
    latency_ms: int = 0
    status: str = "ok"

class OrbitBotState(rx.State):
    spaces: list[OrbitSpace] = []
    interactions: list[OrbitInteraction] = []
    is_loading: bool = False
    
    # Stats
    total_spaces: int = 0
    total_messages: int = 0
    avg_latency: int = 0

    async def load_data(self):
        self.is_loading = True
            
        # 1. Load spaces from Redis
        space_list = []
        if r_client:
            try:
                active_spaces = r_client.smembers("gchat:orbit:active_spaces")
                for s_id in active_spaces:
                    space_list.append(
                        OrbitSpace(
                            space_id=s_id,
                            is_active=True
                        )
                    )
            except Exception as e:
                rx.toast.error(f"Error cargando espacios desde Redis: {str(e)}")
        
        self.spaces = space_list
        self.total_spaces = len(space_list)

        # 2. Load interactions from API (telemetry)
        history = await api_client.get_recent_requests(limit=100)
        interaction_list = []
        latency_sum = 0
        
        if history:
            gchat_reqs = [
                r for r in history 
                if r.get("channel", "").lower() == "orbit"
            ]
            
            for req in gchat_reqs[:20]:  # Limit to last 20
                latency_val = req.get("latency_ms", 0)
                latency_sum += latency_val
                
                # Format timestamp
                ts_str = req.get("timestamp", "")
                if ts_str and "T" in ts_str:
                    try:
                        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass
                
                interaction_list.append(
                    OrbitInteraction(
                        timestamp=ts_str,
                        space_id=req.get("conversation_id", ""),
                        user_text=req.get("user_text", ""),
                        bot_reply=req.get("mcp_response", "") or "",
                        latency_ms=latency_val,
                        status=req.get("status", "ok")
                    )
                )
            
            self.total_messages = len(gchat_reqs)
            self.avg_latency = int(latency_sum / len(interaction_list)) if interaction_list else 0

        self.interactions = interaction_list
        self.is_loading = False

    async def revoke_space(self, space_id: str):
        if r_client:
            try:
                r_client.srem("gchat:orbit:active_spaces", space_id)
                rx.toast.success(f"Espacio removido: {space_id}")
                # Log audit action
                await api_client.log_audit_action({
                    "username": self.router.session.get("username", "admin"),
                    "role": self.router.session.get("role", "admin"),
                    "action": "SECURITY_ACTION",
                    "details": f"Removed Orbit Bot space {space_id}"
                })
                await self.load_data()
            except Exception as e:
                rx.toast.error(f"Error al remover espacio: {str(e)}")

    async def on_load(self):
        await self.load_data()

def space_row(space: OrbitSpace) -> rx.Component:
    """Renders a single row in the spaces table."""
    return rx.table.row(
        rx.table.cell(space.space_id, font_family="Courier New", font_size="13px"),
        rx.table.cell(rx.badge("🟢 Activo", color_scheme="green")),
        rx.table.cell(
            rx.button(
                "Remover",
                size="1",
                color_scheme="ruby",
                variant="soft",
                on_click=lambda: OrbitBotState.revoke_space(space.space_id),
                style={"cursor": "pointer"}
            )
        )
    )

def interaction_row(intr: OrbitInteraction) -> rx.Component:
    """Renders a recent interaction row."""
    status_color = rx.cond(intr.status == "ok", "green", "ruby")
    
    return rx.table.row(
        rx.table.cell(intr.timestamp, font_size="12px"),
        rx.table.cell(intr.space_id, font_family="Courier New", font_size="12px"),
        rx.table.cell(intr.user_text, max_width="250px", is_truncated=True, font_size="13px"),
        rx.table.cell(intr.bot_reply, max_width="350px", is_truncated=True, font_size="13px"),
        rx.table.cell(intr.latency_ms.to(str) + "ms", font_size="12px"),
        rx.table.cell(rx.badge(intr.status, color_scheme=status_color))
    )

def orbit_page() -> rx.Component:
    """The Orbit Bot dedicated panel page."""
    
    # Stats row
    stats = rx.grid(
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Espacios Activos", font_size="12px", color=TEXT_MUTED),
                    rx.heading(OrbitBotState.total_spaces.to(str), size="6", color="#FFFFFF"),
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
                    rx.text("Mensajes Procesados", font_size="12px", color=TEXT_MUTED),
                    rx.heading(OrbitBotState.total_messages.to(str), size="6", color=ACCENT_PURPLE),
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
                    rx.text("Latencia Promedio", font_size="12px", color=TEXT_MUTED),
                    rx.heading(OrbitBotState.avg_latency.to(str) + " ms", size="6", color="#FFFFFF"),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("zap", color="#FFD700", size=24),
                width="100%"
            ),
            style={"padding": "18px"}
        ),
        columns="3",
        spacing="4",
        width="100%",
        style={"margin_bottom": "24px"}
    )

    # 🏢 Table of Workspaces
    spaces_table = glass_container(
        rx.vstack(
            rx.hstack(
                rx.heading("🏢 Canales de Google Chat Registrados", size="3", color="#FFFFFF"),
                rx.spacer(),
                rx.button(
                    rx.hstack(rx.icon("refresh_cw", size=12), rx.text("Refrescar"), spacing="2"),
                    on_click=OrbitBotState.load_data,
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
                        rx.table.column_header_cell("Acciones")
                    )
                ),
                rx.table.body(
                    rx.cond(
                        OrbitBotState.spaces.length() == 0,
                        rx.table.row(
                            rx.table.cell("No hay canales activos en Redis", colspan=3, style={"text_align": "center", "color": TEXT_MUTED})
                        ),
                        rx.foreach(
                            OrbitBotState.spaces,
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
            rx.heading("💬 Conversaciones Recientes (Orbit Bot)", size="3", color="#FFFFFF", style={"margin_bottom": "12px"}),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Fecha/Hora"),
                        rx.table.column_header_cell("Space ID"),
                        rx.table.column_header_cell("Mensaje Usuario"),
                        rx.table.column_header_cell("Respuesta Bot"),
                        rx.table.column_header_cell("Latencia"),
                        rx.table.column_header_cell("Estatus")
                    )
                ),
                rx.table.body(
                    rx.cond(
                        OrbitBotState.interactions.length() == 0,
                        rx.table.row(
                            rx.table.cell("No se encontraron solicitudes de Orbit Bot recientemente", colspan=6, style={"text_align": "center", "color": TEXT_MUTED})
                        ),
                        rx.foreach(
                            OrbitBotState.interactions,
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
        spaces_table,
        interactions_table,
        width="100%",
        spacing="1"
    )

    return protected_layout(content, "Orbit Bot Control Panel", "/orbit")
