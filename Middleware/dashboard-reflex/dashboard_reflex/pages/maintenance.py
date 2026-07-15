import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.components.styling import (
    GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, BORDER_COLOR, TEXT_MUTED,
    glass_container, status_badge
)
from dashboard_reflex.api.client import api_client
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.state.app_state import AppState

class MaintenanceState(rx.State):
    is_loading: bool = False
    is_testing: bool = False
    
    test_query: str = "Hola, ¿cómo estás?"
    test_result: str = ""
    test_latency: int = 0
    test_success: bool = False
    
    # Circuit Breaker Status
    cb_enabled: bool = False
    cb_is_open: bool = False
    cb_failures: int = 0
    cb_threshold: int = 5
    
    # Knowledge Base / FAQs
    faq_list: list[dict] = []
    knowledge_links: list[dict] = []
    public_knowledge_url: str = ""

    def set_test_query(self, val: str):
        self.test_query = val

    async def load_data(self):
        self.is_loading = True
        self.public_knowledge_url = f"{api_client.base_url}/knowledge"
        
        # 1. Update global health in AppState
        app_state = await self.get_state(AppState)
        await app_state.update_health()
        
        # 2. Fetch Circuit Breaker
        cb = await api_client.get_circuit_breaker_status()
        if cb:
            self.cb_enabled = cb.get("enabled", True)
            self.cb_is_open = cb.get("is_open", False)
            self.cb_failures = cb.get("failure_count", 0)
            self.cb_threshold = cb.get("failure_threshold", 5)
            
        # 3. Fetch Knowledge Base FAQs
        kb = await api_client.get_knowledge()
        if kb:
            self.faq_list = kb.get("faq", [])
            self.knowledge_links = []
            raw_links = kb.get("links", [])
            for link in raw_links:
                url = link.get("url", "")
                if url.startswith("/"):
                    url = f"{api_client.base_url}{url}"
                self.knowledge_links.append({
                    "name": link.get("name", "Link"),
                    "url": url
                })
        else:
            self.faq_list = []
            self.knowledge_links = []
            
        self.is_loading = False

    async def run_mcp_test(self):
        if not self.test_query:
            rx.toast.error("Por favor escriba una consulta para probar.")
            return
            
        self.is_testing = True
        res = await api_client.test_mcp(self.test_query)
        if res and res.get("status") == "ok":
            self.test_success = True
            self.test_latency = res.get("latency_ms", 0)
            self.test_result = res.get("mcp_response", "Sin respuesta.")
            rx.toast.success("✅ Prueba de conexión MCP exitosa!")
        else:
            self.test_success = False
            self.test_latency = 0
            self.test_result = res.get("error", "Error desconocido o tiempo de espera agotado.") if res else "No hubo respuesta del servidor."
            rx.toast.error("❌ La prueba de conexión MCP falló.")
        self.is_testing = False

    async def reload_configuration(self):
        rx.toast.info("Recargando configuración...")
        try:
            res = await api_client._request("POST", "/admin/maintenance/reload-config")
            if res:
                rx.toast.success("✅ Configuración recargada correctamente!")
                await self.load_data()
            else:
                rx.toast.error("❌ Falló la recarga de configuración.")
        except Exception:
            rx.toast.error("❌ Error de red al recargar configuración.")

    async def reset_circuit_breaker_action(self):
        success = await api_client.reset_circuit_breaker()
        if success:
            rx.toast.success("✅ Circuit Breaker restablecido con éxito!")
            await self.load_data()
        else:
            rx.toast.error("❌ Falló el restablecimiento del Circuit Breaker.")

    async def clear_cache_maint(self):
        success = await api_client.clear_cache()
        if success:
            rx.toast.success("✅ Caché vaciada correctamente!")
        else:
            rx.toast.error("❌ Falló el vaciado de caché.")

    async def on_load(self):
        await self.load_data()

def faq_item(faq: dict) -> rx.Component:
    """Renders a single FAQ question and answer inside an accordion."""
    return rx.accordion.item(
        header=rx.hstack(
            rx.icon("circle_help", size=16, color=ACCENT_BLUE),
            rx.text(faq.get("question", ""), font_weight="bold", font_size="14px"),
            spacing="2"
        ),
        content=rx.text(faq.get("answer", ""), font_size="13px", color="#A0AEC0", style={"padding": "12px 16px"}),
        value=faq.get("question", "")
    )

def kb_link_button(link: dict) -> rx.Component:
    """Renders a button that links to external knowledge documentation."""
    return rx.link(
        rx.button(
            rx.hstack(
                rx.icon("external-link", size=14),
                rx.text(link.get("name", "Documento")),
                spacing="2"
            ),
            variant="solid",
            style={
                "background_color": "rgba(255,255,255,0.05)",
                "border": f"1px solid {BORDER_COLOR}",
                "color": "#FFFFFF",
                "cursor": "pointer",
                "width": "100%"
            }
        ),
        href=link.get("url", "#"),
        is_external=True,
        style={"width": "100%"}
    )

def maintenance_page() -> rx.Component:
    """System maintenance and diagnostics page."""
    
    # Tab 1: Diagnostics and Test Connection Form
    diagnostics_panel = rx.vstack(
        rx.heading("🏥 Salud del Sistema & Diagnóstico", size="4", color="#FFFFFF", style={"margin_bottom": "16px"}),
        
        # Grid of current statuses
        rx.grid(
            glass_container(
                rx.vstack(
                    rx.text("Servidor Middleware API", font_size="12px", color=TEXT_MUTED),
                    status_badge(AppState.api_status),
                    align_items="center"
                ),
                style={"padding": "16px"}
            ),
            glass_container(
                rx.vstack(
                    rx.text("Servidor DevOps MCP", font_size="12px", color=TEXT_MUTED),
                    status_badge(AppState.mcp_status),
                    align_items="center"
                ),
                style={"padding": "16px"}
            ),
            glass_container(
                rx.vstack(
                    rx.text("Caché y Almacenamiento Redis", font_size="12px", color=TEXT_MUTED),
                    status_badge(AppState.redis_status),
                    align_items="center"
                ),
                style={"padding": "16px"}
            ),
            columns="3",
            spacing="4",
            width="100%",
            style={"margin_bottom": "24px"}
        ),
        
        rx.divider(style={"border_color": BORDER_COLOR}),
        
        # Test MCP Form
        rx.vstack(
            rx.heading("🧪 Prueba Manual DevOps MCP", size="3", color="#FFFFFF", style={"margin_top": "16px"}),
            rx.text("Consulta de prueba para enviar al MCP", font_size="12px", color=TEXT_MUTED),
            rx.text_area(
                value=MaintenanceState.test_query,
                on_change=MaintenanceState.set_test_query,
                width="100%",
                style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "8px", "height": "80px"}
            ),
            rx.button(
                rx.cond(
                    MaintenanceState.is_testing,
                    rx.spinner(size="2"),
                    rx.hstack(rx.icon("play", size=14), rx.text("Enviar Consulta de Prueba"), spacing="2")
                ),
                on_click=MaintenanceState.run_mcp_test,
                disabled=MaintenanceState.is_testing,
                style={"background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)", "color": "#FFFFFF", "cursor": "pointer", "margin_top": "8px"}
            ),
            
            # Test Result display box
            rx.cond(
                MaintenanceState.test_result != "",
                glass_container(
                    rx.vstack(
                        rx.hstack(
                            rx.text("Resultado de Prueba", font_weight="bold", font_size="13px", color=ACCENT_BLUE),
                            rx.spacer(),
                            rx.badge(
                                rx.cond(MaintenanceState.test_success, "Éxito", "Falló"),
                                color_scheme=rx.cond(MaintenanceState.test_success, "green", "ruby")
                            ),
                            rx.badge(MaintenanceState.test_latency.to(str) + " ms", color_scheme="gray"),
                            width="100%",
                            align_items="center"
                        ),
                        rx.box(
                            rx.text(MaintenanceState.test_result, font_size="13px"),
                            style={"padding": "12px", "background_color": "rgba(0,0,0,0.2)", "border_radius": "8px", "width": "100%"}
                        ),
                        width="100%",
                        spacing="2"
                    ),
                    style={"padding": "16px", "width": "100%", "margin_top": "16px", "border_color": rx.cond(MaintenanceState.test_success, "rgba(16, 185, 129, 0.3)", "rgba(239, 68, 68, 0.3)")}
                )
            ),
            
            width="100%",
            align_items="start"
        ),
        width="100%"
    )

    # Tab 2: System Controls (Reload, Cache, Circuit Breaker)
    controls_panel = rx.vstack(
        rx.heading("⚙️ Controles de Operaciones", size="4", color="#FFFFFF", style={"margin_bottom": "16px"}),
        
        # Quick Actions
        rx.grid(
            glass_container(
                rx.vstack(
                    rx.heading("Recargar Sistema", size="3", color="#FFFFFF"),
                    rx.text("Recarga las configuraciones del API desde la base de datos sin necesidad de reiniciar el servicio.", font_size="11px", color=TEXT_MUTED),
                    rx.button(
                        "Recargar Configuración",
                        on_click=MaintenanceState.reload_configuration,
                        style={"background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)", "color": "#FFFFFF", "cursor": "pointer", "width": "100%", "margin_top": "10px"}
                    ),
                    spacing="2",
                    align_items="start"
                ),
                style={"padding": "20px"}
            ),
            glass_container(
                rx.vstack(
                    rx.heading("Caché y Memoria", size="3", color="#FFFFFF"),
                    rx.text("Limpia la memoria caché de las consultas respondio-mcp de forma manual y fuerza peticiones frescas.", font_size="11px", color=TEXT_MUTED),
                    rx.button(
                        "Vaciar Caché",
                        on_click=MaintenanceState.clear_cache_maint,
                        variant="outline",
                        style={"cursor": "pointer", "border_color": BORDER_COLOR, "color": "#FFFFFF", "width": "100%", "margin_top": "10px"}
                    ),
                    spacing="2",
                    align_items="start"
                ),
                style={"padding": "20px"}
            ),
            columns="2",
            spacing="4",
            width="100%",
            style={"margin_bottom": "24px"}
        ),
        
        rx.divider(style={"border_color": BORDER_COLOR}),
        
        # Circuit Breaker Status
        rx.vstack(
            rx.heading("🔌 Control del Circuit Breaker (Fusible de Seguridad)", size="3", color="#FFFFFF", style={"margin_top": "16px"}),
            rx.text("El circuit breaker desconecta el MCP si detecta múltiples fallas consecutivas para evitar sobrecarga.", font_size="12px", color=TEXT_MUTED),
            
            glass_container(
                rx.grid(
                    rx.vstack(
                        rx.text("Habilitado", font_size="11px", color=TEXT_MUTED),
                        rx.text(rx.cond(MaintenanceState.cb_enabled, "SÍ", "NO"), font_size="16px", font_weight="bold", color="#FFFFFF")
                    ),
                    rx.vstack(
                        rx.text("Estado del Fusible", font_size="11px", color=TEXT_MUTED),
                        rx.text(rx.cond(MaintenanceState.cb_is_open, "ABIERTO 🔴 (Alerta)", "CERRADO 🟢 (Operando)"), font_size="16px", font_weight="bold")
                    ),
                    rx.vstack(
                        rx.text("Peticiones Fallidas", font_size="11px", color=TEXT_MUTED),
                        rx.text(MaintenanceState.cb_failures.to(str) + " / " + MaintenanceState.cb_threshold.to(str), font_size="16px", font_weight="bold", color="#FFFFFF")
                    ),
                    columns="3",
                    width="100%"
                ),
                style={"padding": "16px", "width": "100%"}
            ),
            
            rx.cond(
                MaintenanceState.cb_is_open,
                rx.button(
                    "Restablecer Fusible (Circuit Breaker)",
                    on_click=MaintenanceState.reset_circuit_breaker_action,
                    color_scheme="green",
                    style={"cursor": "pointer", "margin_top": "12px"}
                )
            ),
            
            width="100%",
            align_items="start",
            spacing="3"
        ),
        width="100%"
    )

    # Tab 3: Knowledge Base (FAQ & links)
    kb_panel = rx.vstack(
        rx.heading("📚 Base de Conocimientos & FAQ", size="4", color="#FFFFFF", style={"margin_bottom": "16px"}),
        rx.text("Acceso a dudas comunes y ligas de integración.", font_size="12px", color=TEXT_MUTED),
        
        glass_container(
            rx.vstack(
                rx.text("Enlace Público del FAQ de la API (JSON)", font_weight="bold", font_size="13px", color=ACCENT_BLUE),
                rx.text("Utilice esta URL en sus webhooks o plataformas de chat externas para descargar el FAQ actual:", font_size="11px", color=TEXT_MUTED),
                rx.code_block(
                    MaintenanceState.public_knowledge_url,
                    style={"width": "100%", "font_size": "11px", "background_color": "#080B16", "border": f"1px solid {BORDER_COLOR}"}
                ),
                width="100%",
                align_items="start",
                spacing="1"
            ),
            style={"padding": "16px", "width": "100%", "margin_bottom": "20px"}
        ),
        
        rx.grid(
            # FAQs list Accordion
            rx.vstack(
                rx.text("Preguntas Frecuentes", font_weight="bold", font_size="14px", color="#FFFFFF"),
                rx.cond(
                    MaintenanceState.faq_list.length() > 0,
                    rx.accordion.root(
                        rx.foreach(
                            MaintenanceState.faq_list,
                            faq_item
                        ),
                        collapsible=True,
                        width="100%",
                        style={"border": f"1px solid {BORDER_COLOR}", "border_radius": "8px", "overflow": "hidden"}
                    ),
                    rx.text("No hay preguntas configuradas en el FAQ actualmente.")
                ),
                width="100%",
                align_items="start"
            ),
            
            # Resource links list
            rx.vstack(
                rx.text("Ligas e Integraciones Útiles", font_weight="bold", font_size="14px", color="#FFFFFF"),
                rx.cond(
                    MaintenanceState.knowledge_links.length() > 0,
                    rx.grid(
                        rx.foreach(
                            MaintenanceState.knowledge_links,
                            kb_link_button
                        ),
                        columns="1",
                        spacing="2",
                        width="100%"
                    ),
                    rx.text("No hay ligas configuradas actualmente.")
                ),
                width="100%",
                align_items="start"
            ),
            columns="2",
            spacing="4",
            width="100%"
        ),
        
        width="100%"
    )

    # Assemble tabs using Radix
    tabs_section = rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("🚀 Diagnósticos", value="diag", style={"cursor": "pointer"}),
            rx.tabs.trigger("⚙️ Controles del Sistema", value="ctrl", style={"cursor": "pointer"}),
            rx.tabs.trigger("📚 Base de Conocimientos", value="kb", style={"cursor": "pointer"}),
        ),
        rx.tabs.content(
            glass_container(diagnostics_panel, style={"padding": "24px", "margin_top": "16px"}),
            value="diag"
        ),
        rx.tabs.content(
            glass_container(controls_panel, style={"padding": "24px", "margin_top": "16px"}),
            value="ctrl"
        ),
        rx.tabs.content(
            glass_container(kb_panel, style={"padding": "24px", "margin_top": "16px"}),
            value="kb"
        ),
        default_value="diag",
        width="100%"
    )

    # Main content assembly
    content = rx.vstack(
        rx.cond(
            MaintenanceState.is_loading,
            rx.center(rx.spinner(size="3", color=ACCENT_BLUE), width="100%", height="250px"),
            tabs_section
        ),
        width="100%"
    )

    return protected_layout(content, "Mantenimiento del Sistema", "/maintenance")
