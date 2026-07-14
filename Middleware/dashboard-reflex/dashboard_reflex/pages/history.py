import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.components.styling import (
    GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, BORDER_COLOR, TEXT_MUTED,
    glass_container, status_badge
)
from dashboard_reflex.api.client import api_client
from datetime import datetime, timedelta
import json
import csv
import io

class HistoryState(rx.State):
    limit: int = 100
    status_filter: str = "All"
    search_query: str = ""
    start_date: str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date: str = datetime.now().strftime("%Y-%m-%d")
    
    raw_requests: list[dict] = []
    
    # Selected request for detail view
    selected_request: dict = {}
    show_detail: bool = False
    
    is_loading: bool = False
    
    # Filtered stats
    total_count: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_latency: int = 0

    async def load_data(self):
        self.is_loading = True
        status_param = None if self.status_filter == "All" else self.status_filter
        
        # Load from API
        res = await api_client.get_recent_requests(limit=self.limit, status=status_param)
        self.raw_requests = res if res else []
        await self.apply_filters()
        self.is_loading = False

    async def apply_filters(self):
        # Parse filter dates
        try:
            s_date = datetime.strptime(self.start_date, "%Y-%m-%d").date()
            e_date = datetime.strptime(self.end_date, "%Y-%m-%d").date()
        except Exception:
            s_date = (datetime.now() - timedelta(days=7)).date()
            e_date = datetime.now().date()

        filtered = []
        for r in self.raw_requests:
            # 1. Date Filter
            try:
                ts = r.get("timestamp", "")
                # Format: 'YYYY-MM-DD HH:MM:SS'
                req_date = datetime.strptime(ts.split(" ")[0], "%Y-%m-%d").date()
                if not (s_date <= req_date <= e_date):
                    continue
            except Exception:
                pass
                
            # 2. Search query filter
            if self.search_query:
                sq = self.search_query.lower()
                trace_id = r.get("trace_id", "").lower()
                user_text = r.get("user_text", "").lower()
                mcp_resp = r.get("mcp_response", "").lower()
                if sq not in trace_id and sq not in user_text and sq not in mcp_resp:
                    continue
                    
            filtered.append(r)
            
        # Update metrics
        self.total_count = len(filtered)
        self.success_count = len([r for r in filtered if r.get("status") == "ok"])
        self.error_count = len([r for r in filtered if r.get("status") == "error"])
        self.avg_latency = int(sum(r.get("latency_ms", 0) for r in filtered) / self.total_count) if self.total_count > 0 else 0
        
        self._filtered_requests = filtered

    async def set_limit(self, value: str):
        self.limit = int(value)
        await self.load_data()

    async def set_status_filter(self, value: str):
        self.status_filter = value
        await self.load_data()

    async def change_search_query(self, value: str):
        self.search_query = value
        await self.apply_filters()

    async def change_start_date(self, value: str):
        self.start_date = value
        await self.apply_filters()

    async def change_end_date(self, value: str):
        self.end_date = value
        await self.apply_filters()

    def view_request_detail(self, req: dict):
        self.selected_request = req
        self.show_detail = True

    def close_detail(self):
        self.show_detail = False

    @rx.var
    def filtered_requests(self) -> list[dict]:
        return getattr(self, "_filtered_requests", [])

    @rx.var
    def selected_request_json(self) -> str:
        return json.dumps(self.selected_request, indent=2) if self.selected_request else "{}"

    @rx.var
    def download_csv_url(self) -> str:
        if not self.filtered_requests:
            return ""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["trace_id", "timestamp", "channel", "status", "latency_ms", "mcp_latency_ms", "user_text", "mcp_response"])
        for r in self.filtered_requests:
            writer.writerow([
                r.get("trace_id"), r.get("timestamp"), r.get("channel"), r.get("status"),
                r.get("latency_ms"), r.get("mcp_latency_ms"), r.get("user_text"), r.get("mcp_response")
            ])
        # Return string directly or use data URL
        csv_data = output.getvalue()
        return f"data:text/csv;charset=utf-8,{csv_data}"

    async def on_load(self):
        await self.load_data()

def request_row(req: dict) -> rx.Component:
    """Renders a single request as a table row."""
    status_val = req.get("status", "error")
    icon_map = {
        "whatsapp": "phone",
        "google_chat": "message-square",
        "google-chat": "message-square",
        "telegram": "send",
        "default": "message-circle"
    }
    channel_icon = rx.cond(
        req.get("channel", "default") == "whatsapp",
        "phone",
        rx.cond(
            (req.get("channel", "default") == "google_chat") | (req.get("channel", "default") == "google-chat"),
            "message-square",
            rx.cond(
                req.get("channel", "default") == "telegram",
                "send",
                "message-circle"
            )
        )
    )
    
    return rx.table.row(
        rx.table.cell(status_badge(req.get("status", "error"))),
        rx.table.cell(req.get("timestamp", "N/A")),
        rx.table.cell(
            rx.hstack(
                rx.icon(channel_icon, size=14, color=ACCENT_BLUE),
                rx.text(req.get("channel", "unknown").to(str).upper(), font_size="12px", font_weight="bold"),
                spacing="2",
                align="center"
            )
        ),
        rx.table.cell(req.get("latency_ms", 0).to(str) + " ms"),
        rx.table.cell(rx.text(req.get("user_text", ""), max_width="350px", is_truncated=True, font_size="13px")),
        rx.table.cell(
            rx.button(
                "Ver Detalle",
                on_click=lambda: HistoryState.view_request_detail(req),
                size="1",
                variant="soft",
                style={"cursor": "pointer"}
            )
        ),
        style={"&_hover": {"background_color": "rgba(255,255,255,0.02)"}}
    )

def history_page() -> rx.Component:
    """The request history page."""
    
    # Metrics cards
    metrics_row = rx.grid(
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Total Mostradas", font_size="12px", color=TEXT_MUTED),
                    rx.heading(HistoryState.total_count.to(str), size="6", color="#FFFFFF"),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("activity", color=ACCENT_BLUE),
                width="100%",
                align_items="center"
            ),
            style={"padding": "16px"}
        ),
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Completadas OK", font_size="12px", color=TEXT_MUTED),
                    rx.heading(HistoryState.success_count.to(str), size="6", color="var(--emerald-9)"),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("circle_check", color="var(--emerald-9)"),
                width="100%",
                align_items="center"
            ),
            style={"padding": "16px"}
        ),
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Errores", font_size="12px", color=TEXT_MUTED),
                    rx.heading(HistoryState.error_count.to(str), size="6", color="var(--ruby-9)"),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("triangle_alert", color="var(--ruby-9)"),
                width="100%",
                align_items="center"
            ),
            style={"padding": "16px"}
        ),
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Latencia Promedio", font_size="12px", color=TEXT_MUTED),
                    rx.heading(HistoryState.avg_latency.to(str) + " ms", size="6", color=ACCENT_PURPLE),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("clock", color=ACCENT_PURPLE),
                width="100%",
                align_items="center"
            ),
            style={"padding": "16px"}
        ),
        columns="4",
        spacing="4",
        width="100%",
        style={"margin_bottom": "24px"}
    )
    
    # Detail Modal
    detail_modal = rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.text("Detalle de Petición", font_weight="bold"),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon_button(rx.icon("x", size=16), variant="ghost", on_click=HistoryState.close_detail, style={"cursor": "pointer"})
                    ),
                    width="100%"
                )
            ),
            rx.divider(style={"margin_bottom": "16px", "border_color": BORDER_COLOR}),
            
            rx.grid(
                rx.vstack(
                    rx.text("Metadatos", font_weight="bold", font_size="14px", color=ACCENT_BLUE),
                    rx.text("Trace ID: " + HistoryState.selected_request["trace_id"].to(str), font_size="12px"),
                    rx.text("Conversation: " + HistoryState.selected_request["conversation_id"].to(str), font_size="12px"),
                    rx.text("Contact: " + HistoryState.selected_request["contact_id"].to(str), font_size="12px"),
                    rx.text("Canal: " + HistoryState.selected_request["channel"].to(str).upper(), font_size="12px"),
                    rx.text("Timestamp: " + HistoryState.selected_request["timestamp"].to(str), font_size="12px"),
                    rx.text("Latencia Total: " + HistoryState.selected_request["latency_ms"].to(str) + " ms", font_size="12px"),
                    rx.text("Latencia MCP: " + HistoryState.selected_request["mcp_latency_ms"].to(str) + " ms", font_size="12px"),
                    align_items="start",
                    spacing="2"
                ),
                rx.vstack(
                    rx.text("Consulta de Usuario", font_weight="bold", font_size="14px", color=ACCENT_BLUE),
                    rx.box(
                        rx.text(HistoryState.selected_request["user_text"].to(str), font_size="13px"),
                        style={"padding": "12px", "background_color": "rgba(255,255,255,0.03)", "border_radius": "8px", "width": "100%"}
                    ),
                    rx.text("Respuesta / Error", font_weight="bold", font_size="14px", color=ACCENT_BLUE, style={"margin_top": "12px"}),
                    rx.box(
                        rx.text(
                            rx.cond(
                                HistoryState.selected_request["mcp_response"],
                                HistoryState.selected_request["mcp_response"].to(str),
                                HistoryState.selected_request["error_message"].to(str)
                            ),
                            font_size="13px"
                        ),
                        style={"padding": "12px", "background_color": "rgba(255,255,255,0.03)", "border_radius": "8px", "width": "100%"}
                    ),
                    align_items="start",
                    spacing="2"
                ),
                columns="2",
                spacing="4",
                width="100%"
            ),
            
            rx.vstack(
                rx.text("JSON Completo", font_weight="bold", font_size="14px", color=ACCENT_BLUE, style={"margin_top": "16px"}),
                rx.code_block(
                    HistoryState.selected_request_json,
                    language="json",
                    style={"width": "100%", "max_height": "200px", "overflow_y": "auto", "font_size": "11px"}
                ),
                width="100%",
                align_items="start"
            ),
            style={
                "background_color": "#0C0F1D",
                "border": f"1px solid {BORDER_COLOR}",
                "color": "#FFFFFF",
                "max_width": "750px",
                "padding": "24px",
                "border_radius": "16px"
            }
        ),
        open=HistoryState.show_detail
    )

    # Filter Bar
    filter_bar = glass_container(
        rx.grid(
            rx.vstack(
                rx.text("Cantidad", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                rx.select(
                    ["50", "100", "200", "500", "1000"],
                    value=HistoryState.limit.to(str),
                    on_change=HistoryState.set_limit,
                    style={"width": "100%", "background_color": "#080B16", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "6px", "padding": "4px"}
                ),
                align_items="start",
                spacing="1"
            ),
            rx.vstack(
                rx.text("Estatus", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                rx.select(
                    ["All", "ok", "degraded", "error"],
                    value=HistoryState.status_filter,
                    on_change=HistoryState.set_status_filter,
                    style={"width": "100%", "background_color": "#080B16", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "6px", "padding": "4px"}
                ),
                align_items="start",
                spacing="1"
            ),
            rx.vstack(
                rx.text("Desde", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                rx.input(
                    type="date",
                    value=HistoryState.start_date,
                    on_change=HistoryState.change_start_date,
                    style={"width": "100%", "background_color": "#080B16", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "6px", "padding": "4px 8px"}
                ),
                align_items="start",
                spacing="1"
            ),
            rx.vstack(
                rx.text("Hasta", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                rx.input(
                    type="date",
                    value=HistoryState.end_date,
                    on_change=HistoryState.change_end_date,
                    style={"width": "100%", "background_color": "#080B16", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "6px", "padding": "4px 8px"}
                ),
                align_items="start",
                spacing="1"
            ),
            columns="4",
            spacing="4",
            width="100%"
        ),
        style={"padding": "16px", "margin_bottom": "20px"}
    )
    
    # Search and export tools
    actions_bar = rx.hstack(
        rx.input(
            placeholder="🔍 Buscar por Trace ID, consulta o respuesta...",
            value=HistoryState.search_query,
            on_change=HistoryState.change_search_query,
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
            rx.hstack(
                rx.icon("refresh_cw", size=14),
                rx.text("Actualizar"),
                spacing="2"
            ),
            on_click=HistoryState.load_data,
            variant="solid",
            style={
                "background_color": "rgba(255, 255, 255, 0.05)",
                "border": f"1px solid {BORDER_COLOR}",
                "color": "#FFFFFF",
                "border_radius": "8px",
                "padding": "8px 16px",
                "cursor": "pointer"
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
                    "cursor": "pointer"
                }
            ),
            href=HistoryState.download_csv_url,
            is_external=True
        ),
        width="100%",
        spacing="3",
        style={"margin_bottom": "20px"}
    )

    # Main content assembly
    content = rx.vstack(
        metrics_row,
        filter_bar,
        actions_bar,
        
        # Loader / Table
        rx.cond(
            HistoryState.is_loading,
            rx.center(rx.spinner(size="3", color=ACCENT_BLUE), width="100%", height="200px"),
            glass_container(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Estatus"),
                            rx.table.column_header_cell("Fecha"),
                            rx.table.column_header_cell("Canal"),
                            rx.table.column_header_cell("Latencia"),
                            rx.table.column_header_cell("Texto de Consulta"),
                            rx.table.column_header_cell("Acción")
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            HistoryState.filtered_requests,
                            request_row
                        )
                    ),
                    width="100%"
                ),
                style={"padding": "12px", "width": "100%", "overflow_x": "auto"}
            )
        ),
        
        detail_modal,
        width="100%",
        spacing="1"
    )
    
    return protected_layout(content, "Historial de Peticiones", "/history")
