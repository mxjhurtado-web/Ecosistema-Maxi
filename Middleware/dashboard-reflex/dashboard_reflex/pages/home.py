import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.state.app_state import AppState
from dashboard_reflex.components.styling import (
    GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, BORDER_COLOR, TEXT_MUTED,
    glass_container, status_badge
)
from dashboard_reflex.api.client import api_client
import json
import redis
import os
from datetime import datetime

# Redis connection for fallback tracking if required
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    r = redis.from_url(redis_url, decode_responses=True)
except Exception:
    r = None

class HomeState(rx.State):
    time_range: str = "Last 24 Hours"
    hours: int = 24
    stats_data: list[dict] = []
    recent_requests_data: list[dict] = []
    
    # Latency percentiles
    p50: int = 0
    p95: int = 0
    p99: int = 0
    max_latency: int = 0
    
    # Channel distribution
    channel_distribution: list[dict] = []
    
    # Respond categories distribution
    respond_categories: list[dict] = []
    scripts_count: int = 0
    rules_count: int = 0
    handoffs_count: int = 0
    status_count: int = 0
    bill_count: int = 0
    topup_count: int = 0
    csat_count: int = 0
    notify_count: int = 0
    mcp_conversational_count: int = 0
    
    # MCP metrics
    mcp_avg: int = 0
    mcp_min: int = 0
    mcp_max: int = 0
    mcp_uptime: float = 100.0
    
    is_loading: bool = False

    async def change_time_range(self, range_val: str):
        self.time_range = range_val
        hours_map = {
            "Last 24 Hours": 24,
            "Last 7 Days": 168,
            "Last 30 Days": 720
        }
        self.hours = hours_map.get(range_val, 24)
        await self.load_data()

    async def load_data(self):
        self.is_loading = True
        
        # Refresh global summary KPIs in AppState
        app_state = await self.get_state(AppState)
        await app_state.load_dashboard_summary()
        
        # Load hourly stats
        stats = await api_client.get_stats(hours=self.hours)
        self.stats_data = []
        if stats:
            for item in stats:
                hour_str = item.get("hour", "")
                if isinstance(hour_str, str) and "T" in hour_str:
                    parts = hour_str.split("T")
                    date_part = parts[0][5:] # "07-14"
                    time_part = parts[1][:5] # "12:00"
                    display_hour = f"{date_part} {time_part}"
                else:
                    display_hour = str(hour_str)[:16]
                    
                self.stats_data.append({
                    "hour": display_hour,
                    "total_requests": item.get("total_requests", 0),
                    "respond_requests": item.get("respond_requests", 0),
                    "orbit_requests": item.get("orbit_requests", 0),
                    "maxibot_requests": item.get("maxibot_requests", 0),
                    "success_count": item.get("success_count", 0),
                    "error_count": item.get("error_count", 0),
                    "avg_latency_ms": item.get("avg_latency_ms", 0),
                    "p95_latency_ms": item.get("p95_latency_ms", 0)
                })
                
        # Load recent requests
        recent = await api_client.get_recent_requests(limit=1000)
        self.recent_requests_data = recent if recent else []
        
        # Calculate Latency Percentiles
        latencies = [r.get("latency_ms", 0) for r in self.recent_requests_data if r.get("latency_ms")]
        if latencies:
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)
            self.p50 = sorted_latencies[n // 2]
            self.p95 = sorted_latencies[int(n * 0.95)] if n > 1 else sorted_latencies[0]
            self.p99 = sorted_latencies[int(n * 0.99)] if n > 1 else sorted_latencies[0]
            self.max_latency = max(latencies)
        else:
            self.p50, self.p95, self.p99, self.max_latency = 0, 0, 0, 0
            
        # Calculate Channel Distribution
        channels = {}
        for r in self.recent_requests_data:
            ch = r.get("channel", "unknown")
            ch_lower = ch.lower()
            if "maxibot" in ch_lower:
                name = "MaxiBot"
            elif "orbit" in ch_lower:
                name = "Orbit Bot"
            elif "respond" in ch_lower or ch_lower in ["whatsapp", "telegram", "facebook"]:
                name = "Respond.io"
            else:
                name = ch.title()
            channels[name] = channels.get(name, 0) + 1
        self.channel_distribution = [{"name": ch, "value": val} for ch, val in channels.items()]
        
        # Calculate Respond.io Category Distribution
        respond_cats = {
            "MCP Conversacional": 0, 
            "Scripts de Cumplimiento": 0, 
            "Reglas de Negocio": 0, 
            "Derivaciones (Handoffs)": 0,
            "Consulta de Estatus": 0,
            "Pago de Servicios": 0,
            "Consulta de Recargas": 0,
            "Calificación CSAT": 0,
            "Notificaciones Google Chat": 0
        }
        import re
        for r in self.recent_requests_data:
            chan = r.get("channel", "").lower()
            if "respond" in chan or chan in ["whatsapp", "telegram", "facebook", "unknown", "gchat_orbit", "orbit"] or not chan:
                cat = r.get("category")
                
                # Clasificación al vuelo para datos históricos o cargados antes del cambio
                if not cat or cat == "mcp":
                    user_lower = r.get("user_text", "").lower()
                    resp_lower = (r.get("mcp_response") or "").lower()
                    
                    if "[transfer:" in resp_lower:
                        cat = "handoff"
                    elif re.search(r"(sc\.\d+|cu\.\w+|a[2-6]_)", user_lower) or re.search(r"(sc\.\d+|cu\.\w+|a[2-6]_)", resp_lower):
                        cat = "script"
                    elif any(kw in user_lower for kw in ["disputa", "reembolso", "reclamo", "dispute", "refund", "claim", "re-embolso"]) or any(kw in user_lower for kw in ["privacidad", "datos", "borrar", "privacy", "data", "delete"]):
                        cat = "script"
                    elif re.search(r"rne\.\d+", user_lower) or re.search(r"rne\.\d+", resp_lower):
                        cat = "rule"
                    else:
                        cat = "mcp"
                        
                if cat == "script" or cat == "scripts_fetch":
                    respond_cats["Scripts de Cumplimiento"] += 1
                elif cat == "rule" or cat == "rules_fetch":
                    respond_cats["Reglas de Negocio"] += 1
                elif cat == "handoff":
                    respond_cats["Derivaciones (Handoffs)"] += 1
                elif cat == "status_check":
                    respond_cats["Consulta de Estatus"] += 1
                elif cat == "bill_check":
                    respond_cats["Pago de Servicios"] += 1
                elif cat == "topup_check":
                    respond_cats["Consulta de Recargas"] += 1
                elif cat == "csat_log":
                    respond_cats["Calificación CSAT"] += 1
                elif cat == "gchat_notify":
                    respond_cats["Notificaciones Google Chat"] += 1
                else:
                    respond_cats["MCP Conversacional"] += 1
                    
        self.respond_categories = [
            {"name": name, "value": val} 
            for name, val in respond_cats.items() 
            if val > 0 or name == "MCP Conversacional"
        ]
        self.scripts_count = respond_cats["Scripts de Cumplimiento"]
        self.rules_count = respond_cats["Reglas de Negocio"]
        self.handoffs_count = respond_cats["Derivaciones (Handoffs)"]
        self.status_count = respond_cats["Consulta de Estatus"]
        self.bill_count = respond_cats["Pago de Servicios"]
        self.topup_count = respond_cats["Consulta de Recargas"]
        self.csat_count = respond_cats["Calificación CSAT"]
        self.notify_count = respond_cats["Notificaciones Google Chat"]
        self.mcp_conversational_count = respond_cats["MCP Conversacional"]
        
        # Calculate MCP metrics
        mcp_latencies = [
            r.get("mcp_latency_ms", 0) 
            for r in self.recent_requests_data 
            if r.get("mcp_latency_ms") and r.get("mcp_latency_ms") > 0
        ]
        if mcp_latencies:
            self.mcp_avg = int(sum(mcp_latencies) / len(mcp_latencies))
            self.mcp_min = min(mcp_latencies)
            self.mcp_max = max(mcp_latencies)
            
            ok_count = len([r for r in self.recent_requests_data if r.get("status") == "ok"])
            total = len(self.recent_requests_data)
            self.mcp_uptime = (ok_count / total) * 100 if total > 0 else 100.0
        else:
            self.mcp_avg, self.mcp_min, self.mcp_max, self.mcp_uptime = 0, 0, 0, 100.0
            
        self.is_loading = False

    async def on_load(self):
        """Page load trigger."""
        await self.load_data()

def stat_card(title: str, value: rx.Var, icon: str, description: str = "") -> rx.Component:
    """A metric card with modern design aesthetics."""
    return glass_container(
        rx.vstack(
            rx.hstack(
                rx.text(title, font_size="14px", font_weight="bold", color=TEXT_MUTED),
                rx.spacer(),
                rx.icon(icon, size=20, color=ACCENT_BLUE),
                width="100%",
                align_items="center"
            ),
            rx.heading(value, size="7", style={"font_weight": "800", "color": "#FFFFFF", "margin_top": "8px"}),
            rx.text(description, font_size="11px", color=TEXT_MUTED, style={"margin_top": "4px"}),
            spacing="1",
            align_items="start"
        ),
        style={"padding": "20px", "width": "100%"}
    )

def home_page() -> rx.Component:
    """KPIs & Summary dashboard page."""
    
    # 4 metrics cards grid
    metrics_grid = rx.grid(
        stat_card("Total Peticiones", AppState.total_requests.to(str), "activity", "Hoy en producción"),
        stat_card("Consultas por Canal", AppState.channel_counts_str, "git_branch", "Canales: Respond / Orbit / MaxiBot"),
        stat_card("Latencia Promedio", AppState.avg_latency_ms.to(str) + " ms", "clock", "Tiempo de respuesta API"),
        stat_card("Errores Detectados", AppState.error_count.to(str), "triangle_alert", "Hoy en producción"),
        columns="4",
        spacing="4",
        width="100%",
        style={"margin_bottom": "24px"}
    )
    
    # Chart cards
    volume_chart = glass_container(
        rx.vstack(
            rx.heading("Volumen de Peticiones", size="4", style={"margin_bottom": "12px", "color": "#FFFFFF"}),
            rx.recharts.line_chart(
                rx.recharts.line(data_key="respond_requests", name="Respond", stroke=ACCENT_BLUE, stroke_width=2),
                rx.recharts.line(data_key="orbit_requests", name="Orbit Bot", stroke="#48BB78", stroke_width=2),
                rx.recharts.line(data_key="maxibot_requests", name="MaxiBot", stroke=ACCENT_PURPLE, stroke_width=2),
                rx.recharts.x_axis(data_key="hour", stroke="#555", font_size=10),
                rx.recharts.y_axis(stroke="#555", font_size=10),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="rgba(255,255,255,0.05)"),
                rx.recharts.tooltip(content_style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}"}),
                rx.recharts.legend(vertical_align="top", height=36),
                data=HomeState.stats_data,
                width="100%",
                height=300
            ),
            width="100%",
            spacing="2"
        ),
        style={"padding": "20px"}
    )
    
    latency_chart = glass_container(
        rx.vstack(
            rx.heading("Tendencia de Latencia (ms)", size="4", style={"margin_bottom": "12px", "color": "#FFFFFF"}),
            rx.recharts.line_chart(
                rx.recharts.line(data_key="avg_latency_ms", name="Promedio", stroke=ACCENT_BLUE, stroke_width=2),
                rx.recharts.line(data_key="p95_latency_ms", name="P95", stroke=ACCENT_PURPLE, stroke_width=1.5, stroke_dasharray="4 4"),
                rx.recharts.x_axis(data_key="hour", stroke="#555", font_size=10),
                rx.recharts.y_axis(stroke="#555", font_size=10),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="rgba(255,255,255,0.05)"),
                rx.recharts.tooltip(content_style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}"}),
                rx.recharts.legend(vertical_align="top", height=36),
                data=HomeState.stats_data,
                width="100%",
                height=300
            ),
            width="100%",
            spacing="2"
        ),
        style={"padding": "20px"}
    )
    
    success_chart = glass_container(
        rx.vstack(
            rx.heading("Éxito vs Errores", size="4", style={"margin_bottom": "12px", "color": "#FFFFFF"}),
            rx.recharts.area_chart(
                rx.recharts.area(data_key="success_count", stack_id="1", fill="rgba(16, 185, 129, 0.2)", stroke="#10B981", stroke_width=2),
                rx.recharts.area(data_key="error_count", stack_id="1", fill="rgba(239, 68, 68, 0.2)", stroke="#EF4444", stroke_width=1.5),
                rx.recharts.x_axis(data_key="hour", stroke="#555", font_size=10),
                rx.recharts.y_axis(stroke="#555", font_size=10),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="rgba(255,255,255,0.05)"),
                rx.recharts.tooltip(content_style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}"}),
                data=HomeState.stats_data,
                width="100%",
                height=300
            ),
            width="100%",
            spacing="2"
        ),
        style={"padding": "20px"}
    )
    
    channel_chart = glass_container(
        rx.vstack(
            rx.heading("Distribución por Canal", size="4", style={"margin_bottom": "12px", "color": "#FFFFFF"}),
            rx.hstack(
                rx.recharts.pie_chart(
                    rx.recharts.pie(
                        data=HomeState.channel_distribution,
                        data_key="value",
                        name_key="name",
                        cx="50%",
                        cy="50%",
                        outer_radius=70,
                        fill=ACCENT_PURPLE,
                        label=True
                    ),
                    rx.recharts.tooltip(content_style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}"}),
                    width="100%",
                    height=250
                ),
                width="100%",
                align_items="center"
            ),
            width="100%",
            spacing="2"
        ),
        style={"padding": "20px"}
    )
    
    # Respond.io detailed categories chart
    respond_category_chart = glass_container(
        rx.vstack(
            rx.heading("📊 Usabilidad de Respond.io (Scripts / Reglas / MCP / Handoffs)", size="4", style={"margin_bottom": "16px", "color": "#FFFFFF"}),
            rx.grid(
                # Pie Chart
                rx.vstack(
                    rx.recharts.pie_chart(
                        rx.recharts.pie(
                            data=HomeState.respond_categories,
                            data_key="value",
                            name_key="name",
                            cx="50%",
                            cy="50%",
                            outer_radius=75,
                            fill=ACCENT_BLUE,
                            label=True
                        ),
                        rx.recharts.tooltip(content_style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}"}),
                        width="100%",
                        height=220
                    ),
                    width="100%",
                    align_items="center"
                ),
                # Metrics breakdown list
                rx.vstack(
                    rx.text("Detalle de Interacciones (Hoy)", font_size="13px", font_weight="bold", color="#FFFFFF", style={"margin_bottom": "12px"}),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("message-square", color="var(--indigo-9)", size=16),
                            rx.text("MCP Conversacional:", font_size="13px", color=TEXT_MUTED),
                            rx.spacer(),
                            rx.badge(HomeState.mcp_conversational_count.to(str), color_scheme="indigo", variant="solid"),
                            width="100%"
                        ),
                        rx.hstack(
                            rx.icon("file-text", color=ACCENT_BLUE, size=16),
                            rx.text("Scripts de Cumplimiento:", font_size="13px", color=TEXT_MUTED),
                            rx.spacer(),
                            rx.badge(HomeState.scripts_count.to(str), color_scheme="blue", variant="solid"),
                            width="100%"
                        ),
                        rx.hstack(
                            rx.icon("scale", color="var(--amber-9)", size=16),
                            rx.text("Reglas de Negocio:", font_size="13px", color=TEXT_MUTED),
                            rx.spacer(),
                            rx.badge(HomeState.rules_count.to(str), color_scheme="amber", variant="solid"),
                            width="100%"
                        ),
                        rx.hstack(
                            rx.icon("git-pull-request", color="var(--green-9)", size=16),
                            rx.text("Derivaciones (Handoffs):", font_size="13px", color=TEXT_MUTED),
                            rx.spacer(),
                            rx.badge(HomeState.handoffs_count.to(str), color_scheme="green", variant="solid"),
                            width="100%"
                        ),
                        rx.hstack(
                            rx.icon("user-check", color="var(--teal-9)", size=16),
                            rx.text("Consulta de Estatus (API):", font_size="13px", color=TEXT_MUTED),
                            rx.spacer(),
                            rx.badge(HomeState.status_count.to(str), color_scheme="teal", variant="solid"),
                            width="100%"
                        ),
                        rx.hstack(
                            rx.icon("credit-card", color="var(--pink-9)", size=16),
                            rx.text("Pago de Servicios (API):", font_size="13px", color=TEXT_MUTED),
                            rx.spacer(),
                            rx.badge(HomeState.bill_count.to(str), color_scheme="pink", variant="solid"),
                            width="100%"
                        ),
                        rx.hstack(
                            rx.icon("smartphone", color="var(--sky-9)", size=16),
                            rx.text("Consulta de Recargas (API):", font_size="13px", color=TEXT_MUTED),
                            rx.spacer(),
                            rx.badge(HomeState.topup_count.to(str), color_scheme="sky", variant="solid"),
                            width="100%"
                        ),
                        rx.hstack(
                            rx.icon("star", color="var(--yellow-9)", size=16),
                            rx.text("Calificación CSAT (API):", font_size="13px", color=TEXT_MUTED),
                            rx.spacer(),
                            rx.badge(HomeState.csat_count.to(str), color_scheme="yellow", variant="solid"),
                            width="100%"
                        ),
                        rx.hstack(
                            rx.icon("bell", color="var(--purple-9)", size=16),
                            rx.text("Alertas Google Chat:", font_size="13px", color=TEXT_MUTED),
                            rx.spacer(),
                            rx.badge(HomeState.notify_count.to(str), color_scheme="purple", variant="solid"),
                            width="100%"
                        ),
                        spacing="2",
                        width="100%"
                    ),
                    width="100%",
                    align_items="start",
                    justify_content="center",
                    style={"padding_left": "20px"}
                ),
                columns="2",
                width="100%"
            ),
            width="100%"
        ),
        style={"padding": "24px", "margin_top": "24px"}
    )

    # MCP performance metrics grid
    mcp_performances = glass_container(
        rx.vstack(
            rx.heading("⚡ Rendimiento DevOps MCP", size="4", style={"margin_bottom": "16px", "color": "#FFFFFF"}),
            rx.grid(
                rx.vstack(
                    rx.text("Latencia Promedio MCP", font_size="12px", color=TEXT_MUTED),
                    rx.heading(HomeState.mcp_avg.to(str) + " ms", size="5", color="#FFFFFF"),
                    align_items="center"
                ),
                rx.vstack(
                    rx.text("Latencia Mínima MCP", font_size="12px", color=TEXT_MUTED),
                    rx.heading(HomeState.mcp_min.to(str) + " ms", size="5", color="#FFFFFF"),
                    align_items="center"
                ),
                rx.vstack(
                    rx.text("Latencia Máxima MCP", font_size="12px", color=TEXT_MUTED),
                    rx.heading(HomeState.mcp_max.to(str) + " ms", size="5", color="#FFFFFF"),
                    align_items="center"
                ),
                rx.vstack(
                    rx.text("Disponibilidad MCP", font_size="12px", color=TEXT_MUTED),
                    rx.heading(HomeState.mcp_uptime.to(str) + "%", size="5", color=ACCENT_BLUE),
                    align_items="center"
                ),
                columns="4",
                width="100%"
            ),
            width="100%"
        ),
        style={"padding": "24px", "margin_top": "24px"}
    )

    # Main content assembly
    content = rx.vstack(
        # Controls / Filters Header
        rx.hstack(
            rx.select(
                ["Last 24 Hours", "Last 7 Days", "Last 30 Days"],
                value=HomeState.time_range,
                on_change=HomeState.change_time_range,
                style={
                    "background_color": "#0C0F1D",
                    "border": f"1px solid {BORDER_COLOR}",
                    "color": "#FFFFFF",
                    "border_radius": "8px",
                    "padding": "6px 12px",
                    "cursor": "pointer"
                }
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon("refresh_cw", size=14),
                    rx.text("Recargar Datos"),
                    spacing="2"
                ),
                on_click=HomeState.load_data,
                variant="solid",
                style={
                    "background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)",
                    "color": "#FFFFFF",
                    "border_radius": "8px",
                    "font_weight": "bold",
                    "padding": "8px 16px",
                    "cursor": "pointer"
                }
            ),
            width="100%",
            style={"margin_bottom": "20px"}
        ),
        
        # Loader
        rx.cond(
            HomeState.is_loading,
            rx.center(rx.spinner(size="3", color=ACCENT_BLUE), width="100%", height="200px"),
            rx.vstack(
                metrics_grid,
                
                # Charts grid row 1
                rx.grid(
                    volume_chart,
                    latency_chart,
                    columns="2",
                    spacing="4",
                    width="100%",
                    style={"margin_bottom": "24px"}
                ),
                
                # Charts grid row 2
                rx.grid(
                    success_chart,
                    channel_chart,
                    columns="2",
                    spacing="4",
                    width="100%"
                ),
                
                respond_category_chart,
                
                mcp_performances,
                width="100%"
            )
        ),
        
        width="100%",
        spacing="1"
    )
    
    return protected_layout(content, "Dashboard KPIs & Analíticas", "/")
