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
        await AppState.load_dashboard_summary()
        
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
            channels[ch] = channels.get(ch, 0) + 1
        self.channel_distribution = [{"name": ch.title(), "value": val} for ch, val in channels.items()]
        
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
        stat_card("Tasa de Éxito", AppState.success_rate.to(str) + "%", "circle_check", "Objetivo: >95%"),
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
                rx.recharts.line(data_key="total_requests", stroke=ACCENT_BLUE, stroke_width=2),
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
                
                mcp_performances,
                width="100%"
            )
        ),
        
        width="100%",
        spacing="1"
    )
    
    return protected_layout(content, "Dashboard KPIs & Analíticas", "/")
