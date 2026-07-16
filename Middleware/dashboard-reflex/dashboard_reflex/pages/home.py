import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.state.app_state import AppState
from dashboard_reflex.components.styling import (
    GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, BORDER_COLOR, TEXT_MUTED, TEXT_COLOR,
    glass_container, status_badge
)
from dashboard_reflex.api.client import api_client
import json
import redis
import os
from datetime import datetime, timedelta

# Redis connection for fallback tracking if required
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    r = redis.from_url(redis_url, decode_responses=True)
except Exception:
    r = None

class HomeState(rx.State):
    start_date: str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date: str = datetime.now().strftime("%Y-%m-%d")
    stats_data: list[dict] = []
    recent_requests_data: list[dict] = []
    
    # Rango seleccionado KPIs
    total_requests_range: int = 0
    channel_counts_str_range: str = "R: 0 | O: 0 | M: 0"
    avg_latency_range: int = 0
    error_count_range: int = 0
    
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

    def set_start_date(self, val: str):
        self.start_date = val

    def set_end_date(self, val: str):
        self.end_date = val

    async def load_data(self):
        self.is_loading = True
        
        # Refresh global summary KPIs in AppState
        app_state = await self.get_state(AppState)
        await app_state.load_dashboard_summary()
        
        # Determine query hours
        query_hours = 168  # 7 days default
        parsed_start = None
        parsed_end = None
        
        if self.start_date and self.end_date:
            try:
                parsed_start = datetime.strptime(self.start_date, "%Y-%m-%d")
                parsed_end = datetime.strptime(self.end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                
                # Calculate hours between start_date and now
                now = datetime.now()
                diff = now - parsed_start
                query_hours = max(24, int(diff.total_seconds() / 3600) + 24)
            except Exception as e:
                print(f"Error parsing dates: {e}")
                
        # Load hourly stats
        stats = await api_client.get_stats(hours=query_hours)
        self.stats_data = []
        if stats:
            for item in stats:
                hour_str = item.get("hour", "")
                
                # Filter records by date range
                if parsed_start and parsed_end:
                    try:
                        record_dt = datetime.fromisoformat(hour_str)
                        if not (parsed_start <= record_dt <= parsed_end):
                            continue
                    except Exception:
                        pass
                
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
                
        # Sum from stats_data for custom range KPIs
        total_reqs = sum(item["total_requests"] for item in self.stats_data)
        total_errors = sum(item["error_count"] for item in self.stats_data)
        r_sum = sum(item["respond_requests"] for item in self.stats_data)
        o_sum = sum(item["orbit_requests"] for item in self.stats_data)
        m_sum = sum(item["maxibot_requests"] for item in self.stats_data)
        
        latencies = [item["avg_latency_ms"] for item in self.stats_data if item["total_requests"] > 0]
        avg_lat = int(sum(latencies) / len(latencies)) if latencies else 0
        
        self.total_requests_range = total_reqs
        self.error_count_range = total_errors
        self.channel_counts_str_range = f"R: {r_sum} | O: {o_sum} | M: {m_sum}"
        self.avg_latency_range = avg_lat

        # Load recent requests
        limit_to_fetch = min(1000, max(100, query_hours * 10))
        recent = await api_client.get_recent_requests(limit=limit_to_fetch)
        filtered_recent = []
        if recent:
            for r in recent:
                ts_str = r.get("timestamp", "")
                if parsed_start and parsed_end:
                    try:
                        if "." in ts_str:
                            ts_str_clean = ts_str.split(".")[0]
                        else:
                            ts_str_clean = ts_str
                        ts_str_clean = ts_str_clean.replace(" ", "T")
                        record_dt = datetime.fromisoformat(ts_str_clean)
                        if not (parsed_start <= record_dt <= parsed_end):
                            continue
                    except Exception:
                        pass
                filtered_recent.append(r)
                
        self.recent_requests_data = filtered_recent
        
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
        
        channel_colors = {
            "MaxiBot": "var(--purple-9)",
            "Orbit Bot": "var(--green-9)",
            "Respond.io": "var(--blue-9)"
        }
        self.channel_distribution = [
            {"name": ch, "value": val, "color": channel_colors.get(ch, "var(--indigo-9)")} 
            for ch, val in channels.items()
        ]
        
        # Calculate Respond.io Category Distribution
        respond_cats = {
            "MCP Conversacional": 0, 
            "Scripts de Cumplimiento": 0, 
            "Reglas de Negocio": 0, 
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
                    
        category_colors = {
            "MCP Conversacional": "var(--indigo-9)", 
            "Scripts de Cumplimiento": "var(--blue-9)", 
            "Reglas de Negocio": "var(--amber-9)", 
            "Consulta de Estatus": "var(--teal-9)",
            "Pago de Servicios": "var(--pink-9)",
            "Consulta de Recargas": "var(--sky-9)",
            "Calificación CSAT": "var(--yellow-9)",
            "Notificaciones Google Chat": "var(--purple-9)"
        }
        self.respond_categories = [
            {"name": name, "value": val, "color": category_colors.get(name, "var(--blue-9)")} 
            for name, val in respond_cats.items() 
            if val > 0 or name == "MCP Conversacional"
        ]
        self.scripts_count = respond_cats["Scripts de Cumplimiento"]
        self.rules_count = respond_cats["Reglas de Negocio"]
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
            rx.heading(value, size="7", style={"font_weight": "800", "color": TEXT_COLOR, "margin_top": "8px"}),
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
        stat_card("Total Peticiones", HomeState.total_requests_range.to(str), "activity", "En el rango seleccionado"),
        stat_card("Consultas por Canal", HomeState.channel_counts_str_range, "git_branch", "Canales: Respond / Orbit / MaxiBot"),
        stat_card("Latencia Promedio", HomeState.avg_latency_range.to(str) + " ms", "clock", "Promedio en el rango"),
        stat_card("Errores Detectados", HomeState.error_count_range.to(str), "triangle_alert", "En el rango seleccionado"),
        columns="4",
        spacing="4",
        width="100%",
        style={"margin_bottom": "24px"}
    )
    
    # Chart cards
    volume_chart = glass_container(
        rx.vstack(
            rx.heading("Volumen de Peticiones", size="4", style={"margin_bottom": "12px", "color": TEXT_COLOR}),
            rx.recharts.line_chart(
                rx.recharts.line(data_key="respond_requests", name="Respond", stroke=ACCENT_BLUE, stroke_width=2),
                rx.recharts.line(data_key="orbit_requests", name="Orbit Bot", stroke="#48BB78", stroke_width=2),
                rx.recharts.line(data_key="maxibot_requests", name="MaxiBot", stroke=ACCENT_PURPLE, stroke_width=2),
                rx.recharts.x_axis(data_key="hour", stroke="#555", font_size=10),
                rx.recharts.y_axis(stroke="#555", font_size=10),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="rgba(255,255,255,0.05)"),
                rx.recharts.tooltip(content_style=rx.color_mode_cond({"backgroundColor": "#FFFFFF", "border": "1px solid rgba(0,0,0,0.1)", "color": "#1A202C"}, {"backgroundColor": "#0C0F1D", "border": "1px solid rgba(0, 217, 255, 0.15)", "color": "#FFFFFF"})),
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
            rx.heading("Tendencia de Latencia (ms)", size="4", style={"margin_bottom": "12px", "color": TEXT_COLOR}),
            rx.recharts.line_chart(
                rx.recharts.line(data_key="avg_latency_ms", name="Promedio", stroke=ACCENT_BLUE, stroke_width=2),
                rx.recharts.line(data_key="p95_latency_ms", name="P95", stroke=ACCENT_PURPLE, stroke_width=1.5, stroke_dasharray="4 4"),
                rx.recharts.x_axis(data_key="hour", stroke="#555", font_size=10),
                rx.recharts.y_axis(stroke="#555", font_size=10),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="rgba(255,255,255,0.05)"),
                rx.recharts.tooltip(content_style=rx.color_mode_cond({"backgroundColor": "#FFFFFF", "border": "1px solid rgba(0,0,0,0.1)", "color": "#1A202C"}, {"backgroundColor": "#0C0F1D", "border": "1px solid rgba(0, 217, 255, 0.15)", "color": "#FFFFFF"})),
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
            rx.heading("Éxito vs Errores", size="4", style={"margin_bottom": "12px", "color": TEXT_COLOR}),
            rx.recharts.area_chart(
                rx.recharts.area(data_key="success_count", stack_id="1", fill="rgba(16, 185, 129, 0.2)", stroke="#10B981", stroke_width=2),
                rx.recharts.area(data_key="error_count", stack_id="1", fill="rgba(239, 68, 68, 0.2)", stroke="#EF4444", stroke_width=1.5),
                rx.recharts.x_axis(data_key="hour", stroke="#555", font_size=10),
                rx.recharts.y_axis(stroke="#555", font_size=10),
                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="rgba(255,255,255,0.05)"),
                rx.recharts.tooltip(content_style=rx.color_mode_cond({"backgroundColor": "#FFFFFF", "border": "1px solid rgba(0,0,0,0.1)", "color": "#1A202C"}, {"backgroundColor": "#0C0F1D", "border": "1px solid rgba(0, 217, 255, 0.15)", "color": "#FFFFFF"})),
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
            rx.heading("Distribución por Canal", size="4", style={"margin_bottom": "12px", "color": TEXT_COLOR}),
            rx.hstack(
                rx.recharts.pie_chart(
                    rx.recharts.pie(
                        rx.foreach(
                            HomeState.channel_distribution,
                            lambda item: rx.recharts.cell(fill=item["color"])
                        ),
                        data=HomeState.channel_distribution,
                        data_key="value",
                        name_key="name",
                        cx="50%",
                        cy="50%",
                        outer_radius=70,
                        label=True
                    ),
                    rx.recharts.tooltip(content_style=rx.color_mode_cond({"backgroundColor": "#FFFFFF", "border": "1px solid rgba(0,0,0,0.1)", "color": "#1A202C"}, {"backgroundColor": "#0C0F1D", "border": "1px solid rgba(0, 217, 255, 0.15)", "color": "#FFFFFF"})),
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
            rx.heading("📊 Usabilidad de Respond.io (Scripts / Reglas / MCP / Alertas)", size="4", style={"margin_bottom": "16px", "color": TEXT_COLOR}),
            rx.grid(
                # Pie Chart
                rx.vstack(
                    rx.recharts.pie_chart(
                        rx.recharts.pie(
                            rx.foreach(
                                HomeState.respond_categories,
                                lambda item: rx.recharts.cell(fill=item["color"])
                            ),
                            data=HomeState.respond_categories,
                            data_key="value",
                            name_key="name",
                            cx="50%",
                            cy="50%",
                            outer_radius=75,
                            label=True
                        ),
                        rx.recharts.tooltip(content_style=rx.color_mode_cond({"backgroundColor": "#FFFFFF", "border": "1px solid rgba(0,0,0,0.1)", "color": "#1A202C"}, {"backgroundColor": "#0C0F1D", "border": "1px solid rgba(0, 217, 255, 0.15)", "color": "#FFFFFF"})),
                        width="100%",
                        height=220
                    ),
                    width="100%",
                    align_items="center"
                ),
                # Metrics breakdown list
                rx.vstack(
                    rx.hstack(
                        rx.text("Detalle de Interacciones (Rango Seleccionado)", font_size="13px", font_weight="bold", color=TEXT_COLOR),
                        rx.spacer(),
                        rx.dialog.root(
                            rx.dialog.trigger(
                                rx.button(
                                    rx.icon("help-circle", size=14),
                                    rx.text("Guía", font_size="11px"),
                                    variant="soft",
                                    color_scheme="indigo",
                                    style={"cursor": "pointer", "padding": "4px 8px", "height": "22px", "border_radius": "6px"}
                                )
                            ),
                            rx.dialog.content(
                                rx.dialog.title("📖 Guía de Conceptos de Usabilidad"),
                                rx.dialog.description(
                                    "A continuación se describe qué mide y cuándo se registra cada una de las métricas de interacción:"
                                ),
                                rx.vstack(
                                    rx.vstack(
                                        rx.hstack(rx.icon("message-square", size=14, color="var(--indigo-9)"), rx.text("1. MCP Conversacional", font_weight="bold"), spacing="2"),
                                        rx.text("• Qué es: Consultas que hace el motor de Inteligencia Artificial interno de Orbit para verificar el funcionamiento de los sistemas.", font_size="12px", color=TEXT_MUTED),
                                        rx.text("• Cuándo se registra: Cada vez que se realiza una prueba general para verificar el funcionamiento del sistema.", font_size="12px", color=TEXT_MUTED),
                                        align_items="start",
                                        width="100%",
                                    ),
                                    rx.divider(),
                                    rx.vstack(
                                        rx.hstack(rx.icon("file-text", size=14, color=ACCENT_BLUE), rx.text("2. Scripts de Cumplimiento", font_weight="bold"), spacing="2"),
                                        rx.text("• Qué es: Consultas de los guiones y respuestas predefinidas que el bot utiliza para seguir el protocolo de cumplimiento.", font_size="12px", color=TEXT_MUTED),
                                        rx.text("• Cuándo se registra: Cada vez que el sistema de Respond.io hace una petición HTTP GET para leer el contenido de la hoja de Google Sheets de Scripts (18VE3tdVt4E-eNrf0dD4zlk1aLV2nfv9_ncdUvLPaNic) para actualizar sus respuestas estructuradas.", font_size="12px", color=TEXT_MUTED),
                                        align_items="start",
                                        width="100%",
                                    ),
                                    rx.divider(),
                                    rx.vstack(
                                        rx.hstack(rx.icon("scale", size=14, color="var(--amber-9)"), rx.text("3. Reglas de Negocio", font_weight="bold"), spacing="2"),
                                        rx.text("• Qué es: Consultas de las reglas lógicas que rigen el comportamiento automatizado del bot.", font_size="12px", color=TEXT_MUTED),
                                        rx.text("• Cuándo se registra: Cada vez que Respond.io hace una petición para consultar la hoja de Google Sheets de Reglas (1eFm3L_ALVr78wTDBB2bsg7Wq6DT9ZoGzIX9tKLN9nGw) y saber cómo debe enrutar una conversación o qué condición validar.", font_size="12px", color=TEXT_MUTED),
                                        align_items="start",
                                        width="100%",
                                    ),
                                    rx.divider(),
                                    rx.vstack(
                                        rx.hstack(rx.icon("user-check", size=14, color="var(--teal-9)"), rx.text("4. Consulta de Estatus (API)", font_weight="bold"), spacing="2"),
                                        rx.text("• Qué es: Peticiones automáticas para revisar el estado de un envío o pedido.", font_size="12px", color=TEXT_MUTED),
                                        rx.text("• Cuándo se registra: Cada vez que un cliente pregunta por el estado de su trámite en el flujo de WhatsApp, y Respond.io hace una llamada al endpoint del Middleware (/api/v1/status/check) para obtener el estatus en tiempo real desde la base de datos de Orbit.", font_size="12px", color=TEXT_MUTED),
                                        align_items="start",
                                        width="100%",
                                    ),
                                    rx.divider(),
                                    rx.vstack(
                                        rx.hstack(rx.icon("credit-card", size=14, color="var(--pink-9)"), rx.text("5. Pago de Servicios (API)", font_weight="bold"), spacing="2"),
                                        rx.text("• Qué es: Consultas o validaciones relacionadas con el pago de facturas (luz, agua, teléfono, etc.).", font_size="12px", color=TEXT_MUTED),
                                        rx.text("• Cuándo se registra: Cada vez que un usuario interactúa con la opción de pago de servicios en WhatsApp y el sistema consulta el Middleware (/api/v1/bill/check) para verificar los montos o convenios de las facturas.", font_size="12px", color=TEXT_MUTED),
                                        align_items="start",
                                        width="100%",
                                    ),
                                    rx.divider(),
                                    rx.vstack(
                                        rx.hstack(rx.icon("smartphone", size=14, color="var(--sky-9)"), rx.text("6. Consulta de Recargas (API)", font_weight="bold"), spacing="2"),
                                        rx.text("• Qué es: Consultas sobre el estado o procesamiento de recargas de tiempo aire/celular.", font_size="12px", color=TEXT_MUTED),
                                        rx.text("• Cuándo se registra: Cada vez que se solicita una recarga telefónica en el chat y Respond.io consulta al Middleware (/api/v1/topup/check) para procesar o verificar la recarga.", font_size="12px", color=TEXT_MUTED),
                                        align_items="start",
                                        width="100%",
                                    ),
                                    rx.divider(),
                                    rx.vstack(
                                        rx.hstack(rx.icon("star", size=14, color="var(--yellow-9)"), rx.text("7. Calificación CSAT (API)", font_weight="bold"), spacing="2"),
                                        rx.text("• Qué es: Registro de encuestas de satisfacción del cliente al finalizar la atención.", font_size="12px", color=TEXT_MUTED),
                                        rx.text("• Cuándo se registra: Cada vez que el chat termina, se le envía la pregunta de satisfacción al cliente (ej. del 1 al 5) y su respuesta se guarda en base de datos mediante el endpoint /api/v1/csat/log.", font_size="12px", color=TEXT_MUTED),
                                        align_items="start",
                                        width="100%",
                                    ),
                                    rx.divider(),
                                    rx.vstack(
                                        rx.hstack(rx.icon("bell", size=14, color="var(--purple-9)"), rx.text("8. Alertas Google Chat", font_weight="bold"), spacing="2"),
                                        rx.text("• Qué es: Mensajes de notificación enviados por el Agente Comunicador del ecosistema hacia los canales internos de tu equipo.", font_size="12px", color=TEXT_MUTED),
                                        rx.text("• Cuándo se registra: Cada vez que ocurre un evento importante (ej. alerta de fraude, reporte de operaciones, aviso de soporte) y la plataforma envía un mensaje formateado a tus espacios de Google Chat.", font_size="12px", color=TEXT_MUTED),
                                        align_items="start",
                                        width="100%",
                                    ),
                                    spacing="3",
                                    style={"max_height": "320px", "overflow_y": "auto", "margin_top": "16px", "margin_bottom": "16px", "padding_right": "10px"}
                                ),
                                rx.dialog.close(
                                    rx.button("Entendido", color_scheme="indigo", style={"cursor": "pointer"})
                                ),
                                style={
                                    "background_color": "#0C0F1D",
                                    "border": f"1px solid {BORDER_COLOR}",
                                    "max_width": "550px",
                                    "color": "#FFFFFF"
                                }
                            )
                        ),
                        width="100%",
                        align_items="center",
                        style={"margin_bottom": "12px"}
                    ),
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
            rx.heading("⚡ Rendimiento DevOps MCP", size="4", style={"margin_bottom": "16px", "color": TEXT_COLOR}),
            rx.grid(
                rx.vstack(
                    rx.text("Latencia Promedio MCP", font_size="12px", color=TEXT_MUTED),
                    rx.heading(HomeState.mcp_avg.to(str) + " ms", size="5", color=TEXT_COLOR),
                    align_items="center"
                ),
                rx.vstack(
                    rx.text("Latencia Mínima MCP", font_size="12px", color=TEXT_MUTED),
                    rx.heading(HomeState.mcp_min.to(str) + " ms", size="5", color=TEXT_COLOR),
                    align_items="center"
                ),
                rx.vstack(
                    rx.text("Latencia Máxima MCP", font_size="12px", color=TEXT_MUTED),
                    rx.heading(HomeState.mcp_max.to(str) + " ms", size="5", color=TEXT_COLOR),
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
            rx.hstack(
                rx.text("Desde", color=TEXT_MUTED, font_size="12px", align_self="center"),
                rx.input(
                    type="date",
                    value=HomeState.start_date,
                    on_change=HomeState.set_start_date,
                    style={
                        "background_color": rx.color_mode_cond("#FFFFFF", "#0C0F1D"),
                        "border": f"1px solid {BORDER_COLOR}",
                        "color": TEXT_COLOR,
                        "border_radius": "8px",
                        "padding": "4px 8px"
                    }
                ),
                rx.text("Hasta", color=TEXT_MUTED, font_size="12px", align_self="center"),
                rx.input(
                    type="date",
                    value=HomeState.end_date,
                    on_change=HomeState.set_end_date,
                    style={
                        "background_color": rx.color_mode_cond("#FFFFFF", "#0C0F1D"),
                        "border": f"1px solid {BORDER_COLOR}",
                        "color": TEXT_COLOR,
                        "border_radius": "8px",
                        "padding": "4px 8px"
                    }
                ),
                rx.button(
                    "Filtrar",
                    on_click=HomeState.load_data,
                    variant="soft",
                    color_scheme="indigo",
                    style={"cursor": "pointer"}
                ),
                spacing="2",
                align_items="center"
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon("refresh-cw", size=14),
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
