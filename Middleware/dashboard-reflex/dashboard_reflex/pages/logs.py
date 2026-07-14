import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.components.styling import (
    GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, BORDER_COLOR, TEXT_MUTED,
    glass_container, status_badge
)
from dashboard_reflex.api.client import api_client
import asyncio
from datetime import datetime

class LogsState(rx.State):
    raw_logs: list[dict] = []
    log_level: str = "All"
    auto_refresh: bool = False
    refresh_interval: int = 5
    is_loading: bool = False
    
    # Counts
    errors_count: int = 0
    warnings_count: int = 0
    info_count: int = 0

    async def load_data(self):
        self.is_loading = True
        res = await api_client.get_recent_requests(limit=100)
        self.raw_logs = res if res else []
        self.calculate_metrics()
        self.is_loading = False

    def calculate_metrics(self):
        self.errors_count = len([r for r in self.raw_logs if r.get("status") == "error"])
        self.warnings_count = len([r for r in self.raw_logs if r.get("status") == "degraded"])
        self.info_count = len([r for r in self.raw_logs if r.get("status") == "ok"])

    @rx.var
    def filtered_logs(self) -> list[dict]:
        filtered = []
        for r in self.raw_logs:
            status = r.get("status", "ok")
            if status == "error":
                level = "ERROR"
            elif status == "degraded":
                level = "WARNING"
            else:
                level = "INFO"
                
            if self.log_level != "All" and level != self.log_level:
                continue
                
            # Pre-format fields
            item = r.copy()
            item["level"] = level
            item["color"] = "ruby" if level == "ERROR" else ("amber" if level == "WARNING" else "green")
            item["icon"] = "circle_alert" if level == "ERROR" else ("triangle_alert" if level == "WARNING" else "info")
            item["timestamp_short"] = r.get("timestamp", "")[:19]
            item["trace_id_short"] = r.get("trace_id", "")[:8]
            filtered.append(item)
        return filtered

    async def run_refresh_loop(self):
        while self.auto_refresh:
            await self.load_data()
            yield
            await asyncio.sleep(self.refresh_interval)

    async def toggle_auto_refresh(self, checked: bool):
        self.auto_refresh = checked
        if checked:
            return LogsState.run_refresh_loop

    def set_log_level(self, level: str):
        self.log_level = level

    def set_refresh_interval(self, val: list[int]):
        if val:
            self.refresh_interval = int(val[0])

    @rx.var
    def download_logs_url(self) -> str:
        if not self.raw_logs:
            return ""
        log_text = ""
        for r in self.raw_logs:
            status = r.get("status", "ok")
            level = "ERROR" if status == "error" else ("WARNING" if status == "degraded" else "INFO")
            log_text += f"[{r.get('timestamp')}] {level} - Trace: {r.get('trace_id')} - Latency: {r.get('latency_ms', 0)}ms - {r.get('user_text', 'N/A')}\n"
        return f"data:text/plain;charset=utf-8,{log_text}"

    async def on_load(self):
        await self.load_data()

def log_row(log: dict) -> rx.Component:
    """Renders a single log entry row formatted like a terminal log line."""
    is_error = log["level"] == "ERROR"
    text_color = rx.cond(is_error, "#FFA0A0", rx.cond(log["level"] == "WARNING", "#FFE0A0", "#E0FFE0"))
    bg_color = rx.cond(is_error, "rgba(239, 68, 68, 0.05)", rx.cond(log["level"] == "WARNING", "rgba(245, 158, 11, 0.05)", "rgba(16, 185, 129, 0.05)"))
    
    return rx.box(
        rx.hstack(
            rx.text("[", log.get("timestamp_short", ""), "]", color=TEXT_MUTED, font_size="12px", font_family="Courier New"),
            rx.badge(log.get("level", "INFO"), color_scheme=log.get("color", "gray"), size="1"),
            rx.text("Trace: ", log.get("trace_id_short", ""), "...", color=TEXT_MUTED, font_size="12px", font_family="Courier New"),
            rx.text("Canal: ", log.get("channel", "N/A"), color=TEXT_MUTED, font_size="12px", font_family="Courier New"),
            rx.text(log.get("latency_ms", 0).to(str), " ms", color=TEXT_MUTED, font_size="12px", font_family="Courier New"),
            rx.spacer(),
            rx.text(
                rx.cond(
                    is_error,
                    log.get("error_message", "Error desconocido"),
                    log.get("user_text", "")
                ),
                color=text_color,
                font_size="13px",
                font_family="Courier New",
                max_width="450px",
                is_truncated=True
            ),
            width="100%",
            spacing="3",
            align_items="center"
        ),
        style={
            "padding": "8px 12px",
            "border_bottom": f"1px solid {BORDER_COLOR}",
            "background_color": bg_color,
            "width": "100%"
        }
    )

def logs_page() -> rx.Component:
    """Live logs viewer page."""
    
    # 📊 Metrics
    metrics = rx.grid(
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Errores (ERROR)", font_size="12px", color=TEXT_MUTED),
                    rx.heading(LogsState.errors_count.to(str), size="6", color="var(--ruby-9)"),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("circle_alert", color="var(--ruby-9)", size=20),
                width="100%"
            ),
            style={"padding": "16px"}
        ),
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Advertencias (WARNING)", font_size="12px", color=TEXT_MUTED),
                    rx.heading(LogsState.warnings_count.to(str), size="6", color="var(--amber-9)"),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("triangle_alert", color="var(--amber-9)", size=20),
                width="100%"
            ),
            style={"padding": "16px"}
        ),
        glass_container(
            rx.hstack(
                rx.vstack(
                    rx.text("Información (INFO)", font_size="12px", color=TEXT_MUTED),
                    rx.heading(LogsState.info_count.to(str), size="6", color="var(--green-9)"),
                    align_items="start"
                ),
                rx.spacer(),
                rx.icon("info", color="var(--green-9)", size=20),
                width="100%"
            ),
            style={"padding": "16px"}
        ),
        columns="3",
        spacing="4",
        width="100%",
        style={"margin_bottom": "20px"}
    )

    # 🎛️ Control Panel
    controls = glass_container(
        rx.hstack(
            rx.vstack(
                rx.text("Filtrar por Nivel", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                rx.select(
                    ["All", "ERROR", "WARNING", "INFO"],
                    value=LogsState.log_level,
                    on_change=LogsState.set_log_level,
                    style={"background_color": "#080B16", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "6px", "padding": "4px"}
                ),
                align_items="start",
                spacing="1"
            ),
            rx.hstack(
                rx.switch(checked=LogsState.auto_refresh, on_change=LogsState.toggle_auto_refresh),
                rx.text("Auto-refrescar", font_size="13px", font_weight="bold"),
                spacing="3",
                align_items="center",
                style={"margin_top": "16px"}
            ),
            rx.vstack(
                rx.hstack(
                    rx.text("Intervalo: ", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                    rx.text(LogsState.refresh_interval.to(str) + "s", font_size="11px", font_weight="bold", color=ACCENT_BLUE)
                ),
                rx.slider(
                    min=2,
                    max=30,
                    value=[LogsState.refresh_interval],
                    on_value_commit=LogsState.set_refresh_interval,
                    disabled=~LogsState.auto_refresh,
                    style={"width": "120px"}
                ),
                align_items="start",
                spacing="1"
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(rx.icon("refresh_cw", size=14), rx.text("Actualizar"), spacing="2"),
                on_click=LogsState.load_data,
                variant="solid",
                style={"background_color": "rgba(255, 255, 255, 0.05)", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "cursor": "pointer", "margin_top": "16px"}
            ),
            rx.link(
                rx.button(
                    rx.hstack(rx.icon("download", size=14), rx.text("Descargar logs"), spacing="2"),
                    variant="solid",
                    style={"background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)", "color": "#FFFFFF", "cursor": "pointer", "margin_top": "16px"}
                ),
                href=LogsState.download_logs_url,
                is_external=True
            ),
            width="100%",
            spacing="4",
            align_items="end"
        ),
        style={"padding": "16px", "margin_bottom": "20px"}
    )

    # 📋 Logs console feed
    logs_feed = glass_container(
        rx.vstack(
            rx.cond(
                LogsState.is_loading,
                rx.center(rx.spinner(size="3"), width="100%", height="250px"),
                rx.vstack(
                    rx.foreach(
                        LogsState.filtered_logs,
                        log_row
                    ),
                    width="100%",
                    spacing="0"
                )
            ),
            width="100%"
        ),
        style={
            "padding": "0",
            "border": f"1px solid {BORDER_COLOR}",
            "border_radius": "8px",
            "background_color": "#05070D",
            "overflow": "hidden",
            "max_height": "500px",
            "overflow_y": "auto",
            "width": "100%"
        }
    )

    # Note
    note_box = rx.box(
        rx.text("📝 Nota: Este panel muestra las solicitudes recientes formateadas como líneas de log para simplificar el monitoreo del middleware. Para consultar logs completos de sistema, use 'docker logs respondio_api' en el servidor.", font_size="11px", color=TEXT_MUTED),
        style={"padding": "12px", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px", "background_color": "rgba(255,255,255,0.01)", "margin_top": "16px"}
    )

    content = rx.vstack(
        metrics,
        controls,
        logs_feed,
        note_box,
        width="100%",
        spacing="1"
    )

    return protected_layout(content, "Visor de Logs en Vivo", "/logs")
