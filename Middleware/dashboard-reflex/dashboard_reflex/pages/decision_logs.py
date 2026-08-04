import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.components.styling import (
    GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, BORDER_COLOR, TEXT_MUTED,
    glass_container, status_badge
)
from dashboard_reflex.api.client import api_client
from typing import List, Dict, Any

class DecisionLogsState(rx.State):
    search_query: str = ""
    rule_filter: str = "Todas"
    limit: int = 50
    is_loading: bool = False
    raw_logs: list[dict] = []
    total_count: int = 0

    async def load_data(self):
        self.is_loading = True
        rf = None if self.rule_filter == "Todas" else self.rule_filter
        res = await api_client.get_decision_logs(
            contact_id=self.search_query if self.search_query else None,
            rule_id=rf,
            limit=self.limit
        )
        if isinstance(res, dict):
            self.raw_logs = res.get("logs", [])
            self.total_count = res.get("total", len(self.raw_logs))
        else:
            self.raw_logs = []
            self.total_count = 0
        self.is_loading = False

    async def change_search_query(self, value: str):
        self.search_query = value
        await self.load_data()

    async def change_rule_filter(self, value: str):
        self.rule_filter = value
        await self.load_data()

    @rx.var
    def filtered_logs(self) -> list[dict]:
        filtered = []
        sq = self.search_query.lower().strip()
        for r in self.raw_logs:
            contact = str(r.get("contact_id", "") or "").lower()
            phone = str(r.get("phone", "") or "").lower()
            trace = str(r.get("trace_id", "") or "").lower()
            rule = str(r.get("winning_rule_id", "") or "").lower()
            script = str(r.get("script_code", "") or "").lower()

            if sq and not (sq in contact or sq in phone or sq in trace or sq in rule or sq in script):
                continue

            item = r.copy()
            # Formatting timestamp
            ts = item.get("timestamp", "")
            item["formatted_ts"] = str(ts)[:19].replace("T", " ") if ts else "N/A"
            item["contact_display"] = item.get("contact_id") or item.get("phone") or "Desconocido"
            item["rule_display"] = item.get("winning_rule_id") or "Sin regla"
            item["script_display"] = item.get("script_code") or "Sin script"
            item["current_state_display"] = item.get("current_state") or "INIT"
            item["next_state_display"] = item.get("next_state") or "END"
            item["action_display"] = item.get("next_action") or "CONTINUE"
            
            # Badge colors based on action or state
            action = item["action_display"]
            if "ASSIGN" in action or "HANDOFF" in action:
                item["action_color"] = "amber"
            elif "CSAT" in action or "RESOLVED" in action:
                item["action_color"] = "green"
            elif "FRAUD" in action or "COMPLIANCE" in action:
                item["action_color"] = "ruby"
            else:
                item["action_color"] = "cyan"

            filtered.append(item)
        return filtered

    async def on_load(self):
        await self.load_data()


def decision_card(log: dict) -> rx.Component:
    """Renders a single decision audit card with full state transition details."""
    return rx.box(
        rx.vstack(
            # Card Header
            rx.hstack(
                rx.hstack(
                    rx.icon("brain", size=18, color=ACCENT_BLUE),
                    rx.text(
                        f"Contacto: {log.get('contact_display', '')}",
                        font_weight="bold",
                        font_size="15px"
                    ),
                    spacing="2",
                    align="center"
                ),
                rx.spacer(),
                rx.badge(
                    f"Regla: {log.get('rule_display', '')}",
                    color_scheme="purple",
                    variant="solid",
                    radius="full"
                ),
                rx.badge(
                    f"Script: {log.get('script_display', '')}",
                    color_scheme="cyan",
                    variant="soft",
                    radius="full"
                ),
                rx.badge(
                    log.get("action_display", "CONTINUE"),
                    color_scheme=log.get("action_color", "cyan"),
                    variant="surface",
                    radius="full"
                ),
                width="100%",
                align="center",
                margin_bottom="10px"
            ),
            
            # Main Details Grid
            rx.grid(
                # Column 1: FSM State Transition
                rx.vstack(
                    rx.text("TRANSICIÓN FSM", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                    rx.hstack(
                        rx.badge(log.get("current_state_display", "INIT"), color_scheme="gray", variant="outline"),
                        rx.icon("arrow-right", size=14, color=ACCENT_BLUE),
                        rx.badge(log.get("next_state_display", "NEXT"), color_scheme="blue", variant="solid"),
                        align="center",
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.text("Trace ID:", font_size="11px", color=TEXT_MUTED),
                        rx.code(log.get("trace_id", "N/A"), font_size="11px"),
                        spacing="1"
                    ),
                    align_items="start",
                    spacing="1"
                ),

                # Column 2: Inputs Capturados
                rx.vstack(
                    rx.text("MENSAJE / ENTRADA", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                    rx.text(
                        log.get("inputs", {}).get("user_text") or "Sin texto adjunto",
                        font_size="13px",
                        style={"max_height": "50px", "overflow_y": "auto"}
                    ),
                    rx.hstack(
                        rx.cond(
                            log.get("inputs", {}).get("is_fresh", False),
                            rx.badge("Frescura OK", color_scheme="green", variant="soft"),
                            rx.badge("Sin comprobante", color_scheme="gray", variant="soft")
                        ),
                        rx.cond(
                            log.get("inputs", {}).get("perfil"),
                            rx.badge(f"Perfil: {log.get('inputs', {}).get('perfil')}", color_scheme="cyan", variant="soft"),
                            rx.fragment()
                        ),
                        spacing="1"
                    ),
                    align_items="start",
                    spacing="1"
                ),

                # Column 3: Script Entregado Literal
                rx.vstack(
                    rx.text("RESPUESTA ENTREGADA", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                    rx.text(
                        log.get("script_text") or "Sin texto registrado",
                        font_size="12px",
                        color=TEXT_MUTED,
                        style={"max_height": "50px", "overflow_y": "auto"}
                    ),
                    align_items="start",
                    spacing="1"
                ),

                columns="3",
                spacing="4",
                width="100%",
                style={"background": "rgba(255,255,255,0.02)", "padding": "12px", "border_radius": "8px"}
            ),

            # Card Footer Meta
            rx.hstack(
                rx.text(f"🕒 {log.get('formatted_ts', '')}", font_size="11px", color=TEXT_MUTED),
                rx.spacer(),
                rx.cond(
                    log.get("destination_team"),
                    rx.badge(f"Derivado a: {log.get('destination_team')}", color_scheme="orange", variant="solid"),
                    rx.fragment()
                ),
                rx.cond(
                    log.get("csat_eligible", False),
                    rx.badge("CSAT Elegible", color_scheme="green", variant="outline"),
                    rx.fragment()
                ),
                rx.cond(
                    log.get("close_allowed", False),
                    rx.badge("Permite Cierre", color_scheme="blue", variant="outline"),
                    rx.fragment()
                ),
                width="100%",
                align="center",
                margin_top="8px"
            ),

            spacing="2",
            align_items="stretch"
        ),
        style={
            **GLASS_EFFECT,
            "padding": "16px",
            "border_radius": "12px",
            "border": f"1px solid {BORDER_COLOR}",
            "margin_bottom": "12px",
            "width": "100%"
        }
    )


def decision_logs_page() -> rx.Component:
    """Main Decision Logs audit page component."""
    content = rx.vstack(
        # Page Title Header
        rx.hstack(
            rx.vstack(
                rx.heading("🧠 Auditoría de Toma de Decisiones FSM", size="6", font_weight="800"),
                rx.text("Registro determinístico y trazabilidad turno a turno de la Máquina de Estados de Orbit", color=TEXT_MUTED, font_size="14px"),
                spacing="1"
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon("refresh-cw", size=16),
                    rx.text("Actualizar Logs"),
                    spacing="2",
                    align="center"
                ),
                on_click=DecisionLogsState.load_data,
                color_scheme="cyan",
                variant="solid",
                is_loading=DecisionLogsState.is_loading
            ),
            width="100%",
            align="center",
            margin_bottom="20px"
        ),

        # Filter & Control Bar
        rx.box(
            rx.hstack(
                rx.input(
                    placeholder="🔍 Buscar por teléfono, Contact ID, Trace ID...",
                    value=DecisionLogsState.search_query,
                    on_change=DecisionLogsState.change_search_query,
                    width="350px",
                    size="2"
                ),
                rx.select(
                    ["Todas", "RNE.26", "RNE.28", "RNE.29", "RNE.30", "SC.019", "SC.003", "SC.011_COMPLIANCE"],
                    value=DecisionLogsState.rule_filter,
                    on_change=DecisionLogsState.change_rule_filter,
                    size="2"
                ),
                rx.spacer(),
                rx.badge(
                    f"Total: {DecisionLogsState.total_count} decisiones",
                    color_scheme="purple",
                    variant="surface"
                ),
                width="100%",
                align="center",
                spacing="3"
            ),
            style={
                **GLASS_EFFECT,
                "padding": "12px 16px",
                "border_radius": "10px",
                "margin_bottom": "20px",
                "width": "100%"
            }
        ),

        # Decision Cards Container
        rx.cond(
            DecisionLogsState.is_loading,
            rx.center(
                rx.spinner(size="3", color=ACCENT_BLUE),
                height="200px",
                width="100%"
            ),
            rx.cond(
                DecisionLogsState.total_count > 0,
                rx.vstack(
                    rx.foreach(
                        DecisionLogsState.filtered_logs,
                        decision_card
                    ),
                    width="100%",
                    spacing="2"
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("inbox", size=40, color=TEXT_MUTED),
                        rx.text("No se encontraron registros de decisiones FSM", color=TEXT_MUTED, font_size="15px"),
                        align="center",
                        spacing="2"
                    ),
                    height="200px",
                    width="100%"
                )
            )
        ),

        width="100%",
        spacing="4"
    )
    
    return protected_layout(content, current_page="/decision-logs")
