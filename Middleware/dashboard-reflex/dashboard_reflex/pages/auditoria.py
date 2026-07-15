import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.components.styling import (
    GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, BORDER_COLOR, TEXT_MUTED,
    glass_container, status_badge
)
from dashboard_reflex.api.client import api_client
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.state.app_state import AppState
import csv
import io

class AuditState(rx.State):
    limit: int = 100
    search_query: str = ""
    raw_logs: list[dict] = []
    is_loading: bool = False

    async def load_data(self):
        self.is_loading = True
        res = await api_client.get_audit_logs(limit=self.limit)
        self.raw_logs = res if res else []
        await self.apply_filters()
        self.is_loading = False

    async def apply_filters(self):
        filtered = []
        for r in self.raw_logs:
            if self.search_query:
                sq = self.search_query.lower()
                username = r.get("username", "").lower()
                action = r.get("action", "").lower()
                details = r.get("details", "").lower()
                if sq not in username and sq not in action and sq not in details:
                    continue
                    
            action_raw = r.get("action", "")
            action_icons = {
                "login": "key",
                "config_change": "settings",
                "user_management": "user",
                "export_data": "download",
                "cache_clear": "trash-2",
                "circuit_reset": "shield",
                "system_maintenance": "wrench"
            }
            icon = action_icons.get(action_raw, "file-text")
            formatted_action = action_raw.replace("_", " ").title()
            
            ts = r.get("timestamp")
            formatted_timestamp = str(ts)[:19] if ts else ""
            
            item = r.copy()
            item["icon"] = icon
            item["formatted_action"] = formatted_action
            item["formatted_timestamp"] = formatted_timestamp
            filtered.append(item)
        self._filtered_logs = filtered

    async def set_limit(self, value: str):
        self.limit = int(value)
        await self.load_data()

    async def change_search_query(self, value: str):
        self.search_query = value
        await self.apply_filters()

    @rx.var
    def filtered_logs(self) -> list[dict]:
        return getattr(self, "_filtered_logs", [])

    @rx.var
    def download_csv_url(self) -> str:
        if not self.filtered_logs:
            return ""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "username", "role", "action", "details", "ip_address"])
        for r in self.filtered_logs:
            writer.writerow([
                r.get("timestamp"), r.get("username"), r.get("role"),
                r.get("action"), r.get("details"), r.get("ip_address")
            ])
        return f"data:text/csv;charset=utf-8,{output.getvalue()}"

    async def on_load(self):
        await self.load_data()

def audit_row(log: dict) -> rx.Component:
    """Renders a single audit log entry as a table row."""
    return rx.table.row(
        rx.table.cell(log.get("formatted_timestamp", "")),
        rx.table.cell(
            rx.hstack(
                rx.icon(log.get("icon", "file-text").to(str), size=14, color=ACCENT_BLUE),
                rx.text(log.get("formatted_action", ""), font_weight="bold"),
                spacing="2",
                align="center"
            )
        ),
        rx.table.cell(log.get("username", "N/A")),
        rx.table.cell(rx.badge(log.get("role", "supervisor").to(str), variant="outline", text_transform="uppercase")),
        rx.table.cell(rx.text(log.get("details", ""), max_width="400px", font_size="13px", color="#FFFFFF")),
        rx.table.cell(log.get("ip_address", "N/A")),
        style={"&_hover": {"background_color": "rgba(255,255,255,0.02)"}}
    )

def auditoria_page() -> rx.Component:
    """The system audit log page."""
    
    # Filter tools
    filter_bar = glass_container(
        rx.hstack(
            rx.vstack(
                rx.text("Mostrar Últimos", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                rx.select(
                    ["50", "100", "200", "500", "1000"],
                    value=AuditState.limit.to(str),
                    on_change=AuditState.set_limit,
                    style={"background_color": "#080B16", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "6px", "padding": "4px"}
                ),
                align_items="start",
                spacing="1"
            ),
            rx.input(
                placeholder="🔍 Filtrar por usuario, acción o detalle...",
                value=AuditState.search_query,
                on_change=AuditState.change_search_query,
                style={
                    "flex": "1",
                    "background_color": "#0C0F1D",
                    "border": f"1px solid {BORDER_COLOR}",
                    "color": "#FFFFFF",
                    "border_radius": "8px",
                    "padding": "8px 16px",
                    "margin_top": "16px"
                }
            ),
            rx.button(
                rx.hstack(
                    rx.icon("refresh-cw", size=14),
                    rx.text("Actualizar"),
                    spacing="2"
                ),
                on_click=AuditState.load_data,
                variant="solid",
                style={
                    "background_color": "rgba(255, 255, 255, 0.05)",
                    "border": f"1px solid {BORDER_COLOR}",
                    "color": "#FFFFFF",
                    "border_radius": "8px",
                    "padding": "8px 16px",
                    "cursor": "pointer",
                    "margin_top": "16px"
                }
            ),
            rx.link(
                rx.button(
                    rx.hstack(
                        rx.icon("download", size=14),
                        rx.text("Descargar CSV"),
                        spacing="2"
                    ),
                    variant="solid",
                    style={
                        "background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)",
                        "color": "#FFFFFF",
                        "border_radius": "8px",
                        "padding": "8px 16px",
                        "cursor": "pointer",
                        "margin_top": "16px"
                    }
                ),
                href=AuditState.download_csv_url,
                is_external=True
            ),
            width="100%",
            spacing="3",
            align_items="end"
        ),
        style={"padding": "16px", "margin_bottom": "20px"}
    )

    # Main content assembly
    content = rx.vstack(
        filter_bar,
        
        # Loader / Table
        rx.cond(
            AuditState.is_loading,
            rx.center(rx.spinner(size="3", color=ACCENT_BLUE), width="100%", height="250px"),
            glass_container(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Fecha"),
                            rx.table.column_header_cell("Acción"),
                            rx.table.column_header_cell("Usuario"),
                            rx.table.column_header_cell("Rol"),
                            rx.table.column_header_cell("Detalles"),
                            rx.table.column_header_cell("Dirección IP")
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            AuditState.filtered_logs,
                            audit_row
                        )
                    ),
                    width="100%"
                ),
                style={"padding": "12px", "width": "100%", "overflow_x": "auto"}
            )
        ),
        width="100%",
        spacing="1"
    )
    
    return protected_layout(content, "Registro de Auditoría", "/auditoria")
