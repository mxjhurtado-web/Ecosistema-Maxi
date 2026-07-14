import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.components.styling import (
    GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, BORDER_COLOR, TEXT_MUTED,
    glass_container
)
from dashboard_reflex.api.client import api_client
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.state.app_state import AppState
import httpx
import os
from datetime import datetime

from pydantic import BaseModel

class MessageMetadata(BaseModel):
    status: str = ""
    latency_ms: int = 0
    trace_id: str = ""
    retry_count: int = 0

class ChatMessage(BaseModel):
    role: str = ""
    content: str = ""
    timestamp: str = ""
    time: str = ""
    metadata: MessageMetadata = MessageMetadata()

class ChatState(rx.State):
    messages: list[ChatMessage] = []
    input_text: str = ""
    channel: str = "whatsapp"
    selected_agent: str = "Auto (Orchestrator)"
    agent_options: list[str] = ["Auto (Orchestrator)"]
    is_sending: bool = False

    def set_input_text(self, val: str):
        self.input_text = val
    def set_selected_agent(self, val: str):
        self.selected_agent = val
    def set_channel(self, val: str):
        self.channel = val

    async def load_agents(self):
        res = await api_client.get_agents()
        self.agent_options = ["Auto (Orchestrator)"]
        if res:
            self.agent_options.extend([a.get("name", "") for a in res])

    async def send_message(self):
        if not self.input_text.strip():
            return
            
        self.is_sending = True
        user_msg = self.input_text.strip()
        self.input_text = ""
        
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        time_only = now.strftime("%H:%M:%S")
        
        self.messages.append(
            ChatMessage(
                role="user",
                content=user_msg,
                timestamp=timestamp,
                time=time_only,
                metadata=MessageMetadata(status="", latency_ms=0, trace_id="", retry_count=0)
            )
        )
        
        # Call API Webhook
        api_url = os.getenv("ORBIT_API_URL", "http://localhost:8000").rstrip('/')
        webhook_secret = os.getenv("WEBHOOK_SECRET", "your-super-secret-webhook-key-change-me")
        
        agent_name = None if self.selected_agent == "Auto (Orchestrator)" else self.selected_agent
        
        payload = {
            "conversation_id": f"chat_test_{datetime.now().timestamp()}",
            "contact_id": "dashboard_user",
            "channel": self.channel,
            "user_text": user_msg,
            "media": [],
            "metadata": {
                "source": "dashboard_chat",
                "agent_name": agent_name
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{api_url}/webhook",
                    headers={"X-Webhook-Secret": webhook_secret, "Content-Type": "application/json"},
                    json=payload
                )
                
                resp_time = datetime.now().strftime("%H:%M:%S")
                if response.status_code == 200:
                    result = response.json()
                    self.messages.append(
                        ChatMessage(
                            role="assistant",
                            content=result.get("reply_text", "Sin respuesta."),
                            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            time=resp_time,
                            metadata=MessageMetadata(
                                status=result.get("status", ""),
                                latency_ms=result.get("latency_ms", 0),
                                retry_count=result.get("retry_count", 0),
                                trace_id=result.get("trace_id", "")
                            )
                        )
                    )
                else:
                    self.messages.append(
                        ChatMessage(
                            role="assistant",
                            content=f"⚠️ Error del Servidor API (HTTP {response.status_code})",
                            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            time=resp_time,
                            metadata=MessageMetadata(status="error", latency_ms=0, trace_id="", retry_count=0)
                        )
                    )
        except Exception as e:
            resp_time = datetime.now().strftime("%H:%M:%S")
            self.messages.append(
                ChatMessage(
                    role="assistant",
                    content=f"❌ Error de red: {str(e)}",
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    time=resp_time,
                    metadata=MessageMetadata(status="error", latency_ms=0, trace_id="", retry_count=0)
                )
            )
            
        self.is_sending = False

    def clear_chat(self):
        self.messages = []
        rx.toast.info("Historial de chat borrado.")

    async def quick_test(self, text: str):
        self.input_text = text
        await self.send_message()

    def handle_key_down(self, key: str):
        if key == "Enter":
            return ChatState.send_message

    @rx.var
    def download_history_url(self) -> str:
        if not self.messages:
            return ""
        chat_text = ""
        for m in self.messages:
            role = "Tú" if m.role == "user" else "DevOps MCP"
            chat_text += f"[{m.timestamp}] {role}: {m.content}\n\n"
        return f"data:text/plain;charset=utf-8,{chat_text}"

    @rx.var
    def total_sent(self) -> int:
        return len([m for m in self.messages if m.role == "user"])

    @rx.var
    def total_received(self) -> int:
        return len([m for m in self.messages if m.role == "assistant"])

    async def on_load(self):
        await self.load_agents()

def chat_bubble(msg: ChatMessage) -> rx.Component:
    """Renders a single message bubble (user or assistant)."""
    is_user_cond = msg.role == "user"
    border_color = rx.cond(is_user_cond, ACCENT_BLUE, ACCENT_PURPLE)
    bg_color = rx.cond(is_user_cond, "rgba(0, 217, 255, 0.04)", "rgba(124, 58, 237, 0.04)")
    alignment = rx.cond(is_user_cond, "end", "start")
    bubble_title = rx.cond(is_user_cond, "Tú", "DevOps MCP")
    
    return rx.hstack(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text(bubble_title, font_weight="bold", font_size="13px", color=border_color),
                    rx.spacer(),
                    rx.text(msg.time, font_size="10px", color=TEXT_MUTED),
                    width="100%"
                ),
                rx.text(msg.content, font_size="14px", color="#FFFFFF"),
                
                # Show API metrics if assistant message contains them
                rx.cond(
                    msg.metadata.status != "",
                    rx.vstack(
                        rx.divider(style={"border_color": BORDER_COLOR, "margin": "8px 0"}),
                        rx.hstack(
                            rx.text("Latencia: ", msg.metadata.latency_ms.to(str), "ms", font_size="10px", color=TEXT_MUTED),
                            rx.text("ID: ", msg.metadata.trace_id, font_size="10px", color=TEXT_MUTED, max_width="100px", is_truncated=True),
                            spacing="3"
                        ),
                        width="100%",
                        align_items="start"
                    )
                ),
                align_items="start",
                spacing="2"
            ),
            style={
                **GLASS_EFFECT,
                "padding": "12px 16px",
                "max_width": "550px",
                "width": "100%",
                "background_color": bg_color,
                "border_left_style": "solid",
                "border_left_width": "4px",
                "border_left_color": border_color
            }
        ),
        width="100%",
        justify_content=alignment
    )

def chat_page() -> rx.Component:
    """The interactive test chat interface page."""
    
    # Settings sidebar panel (rendered as a glass container inside the page layout)
    chat_settings_panel = glass_container(
        rx.vstack(
            rx.heading("💬 Opciones de Simulación", size="3", color="#FFFFFF"),
            
            # Agent selector
            rx.text("Agente Activo", font_size="11px", font_weight="bold", color=TEXT_MUTED),
            rx.select(
                ChatState.agent_options,
                value=ChatState.selected_agent,
                on_change=ChatState.set_selected_agent,
                style={"width": "100%", "background_color": "#080B16", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "6px", "padding": "4px"}
            ),
            
            # Channel selector
            rx.text("Canal Simulado", font_size="11px", font_weight="bold", color=TEXT_MUTED, style={"margin_top": "12px"}),
            rx.select(
                ["whatsapp", "telegram", "messenger", "webchat"],
                value=ChatState.channel,
                on_change=ChatState.set_channel,
                style={"width": "100%", "background_color": "#080B16", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "6px", "padding": "4px"}
            ),
            
            rx.divider(style={"border_color": BORDER_COLOR, "margin": "16px 0"}),
            
            # Stats
            rx.heading("📊 Estadísticas", size="2", color="#FFFFFF"),
            rx.hstack(rx.text("Enviados:", font_size="12px", color=TEXT_MUTED), rx.spacer(), rx.text(ChatState.total_sent.to(str), font_size="12px", font_weight="bold"), width="100%"),
            rx.hstack(rx.text("Respuestas:", font_size="12px", color=TEXT_MUTED), rx.spacer(), rx.text(ChatState.total_received.to(str), font_size="12px", font_weight="bold"), width="100%"),
            
            rx.divider(style={"border_color": BORDER_COLOR, "margin": "16px 0"}),
            
            # Actions
            rx.button(
                "🗑️ Limpiar Chat",
                on_click=ChatState.clear_chat,
                color_scheme="ruby",
                variant="soft",
                style={"cursor": "pointer", "width": "100%"}
            ),
            
            rx.link(
                rx.button(
                    rx.hstack(rx.icon("download", size=14), rx.text("Descargar Chat"), spacing="2"),
                    variant="solid",
                    style={
                        "background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)",
                        "color": "#FFFFFF",
                        "cursor": "pointer",
                        "width": "100%",
                        "margin_top": "8px"
                    }
                ),
                href=ChatState.download_history_url,
                is_external=True,
                style={"width": "100%"}
            ),
            
            align_items="start",
            spacing="3"
        ),
        style={"padding": "20px", "width": "260px"}
    )
    
    # Test shortcuts
    shortcuts = rx.hstack(
        rx.button("👋 Saludo", on_click=lambda: ChatState.quick_test("hola"), size="1", variant="soft", style={"cursor": "pointer"}),
        rx.button("📰 Noticias", on_click=lambda: ChatState.quick_test("noticias de tecnologia"), size="1", variant="soft", style={"cursor": "pointer"}),
        rx.button("❓ Ayuda", on_click=lambda: ChatState.quick_test("ayuda"), size="1", variant="soft", style={"cursor": "pointer"}),
        spacing="2",
        style={"margin_bottom": "12px"}
    )
    
    # Chat feed
    chat_feed = rx.vstack(
        # Welcome message if empty
        rx.cond(
            ChatState.messages.length() == 0,
            rx.center(
                rx.vstack(
                    rx.icon("message-square", size=32, color=TEXT_MUTED),
                    rx.text("Inicie una conversación de prueba con DevOps MCP", color=TEXT_MUTED, font_size="13px"),
                    spacing="2",
                    align="center"
                ),
                width="100%",
                height="300px"
            ),
            rx.vstack(
                rx.foreach(
                    ChatState.messages,
                    chat_bubble
                ),
                width="100%",
                spacing="3"
            )
        ),
        style={
            "height": "400px",
            "overflow_y": "auto",
            "padding": "16px",
            "background_color": "rgba(0,0,0,0.1)",
            "border_radius": "12px",
            "border": f"1px solid {BORDER_COLOR}",
            "width": "100%",
            "margin_bottom": "16px"
        }
    )
    
    # Input box
    input_box = rx.hstack(
        rx.input(
            placeholder="Escribe un mensaje de prueba...",
            value=ChatState.input_text,
            on_change=ChatState.set_input_text,
            on_key_down=ChatState.handle_key_down,
            style={
                "flex": "1",
                "background_color": "#0C0F1D",
                "border": f"1px solid {BORDER_COLOR}",
                "color": "#FFFFFF",
                "border_radius": "8px",
                "padding": "8px 16px"
            }
        ),
        rx.button(
            rx.cond(
                ChatState.is_sending,
                rx.spinner(size="2"),
                rx.icon("send", size=16)
            ),
            on_click=ChatState.send_message,
            disabled=ChatState.is_sending,
            style={
                "background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)",
                "color": "#FFFFFF",
                "border_radius": "8px",
                "padding": "8px 16px",
                "cursor": "pointer"
            }
        ),
        width="100%",
        spacing="3"
    )

    # Assemble page layout
    content = rx.hstack(
        rx.vstack(
            shortcuts,
            chat_feed,
            input_box,
            width="100%",
            align_items="start"
        ),
        chat_settings_panel,
        width="100%",
        spacing="4",
        align_items="start"
    )

    return protected_layout(content, "Chat de Prueba con MCP", "/chat")
