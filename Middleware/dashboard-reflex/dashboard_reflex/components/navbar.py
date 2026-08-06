import reflex as rx
from dashboard_reflex.state.app_state import AppState
from dashboard_reflex.components.styling import BORDER_COLOR, ACCENT_BLUE, TEXT_COLOR, TEXT_MUTED

def health_indicator(name: str, status: rx.Var) -> rx.Component:
    """Displays a status indicator with icon and Spanish label."""
    is_ok = (status == "healthy") | (status == "online")
    is_checking = status == "checking"
    
    color = rx.cond(
        is_ok,
        "var(--emerald-9)",
        rx.cond(
            is_checking,
            "var(--sky-9)",
            "var(--ruby-9)"
        )
    )
    
    label_text = rx.cond(
        is_ok,
        "✓ Operativo",
        rx.cond(
            is_checking,
            "⏳ Verificando...",
            "✕ No disponible"
        )
    )

    return rx.hstack(
        rx.box(
            style={
                "width": "8px",
                "height": "8px",
                "border_radius": "50%",
                "background_color": color,
            }
        ),
        rx.text(name, font_size="11px", font_weight="bold", color=TEXT_MUTED),
        rx.text(label_text, font_size="11px", font_weight="bold", color=color),
        spacing="2",
        align="center",
        style={
            "padding": "6px 12px",
            "border_radius": "6px",
            "background_color": rx.color_mode_cond("rgba(0, 0, 0, 0.02)", "rgba(255, 255, 255, 0.03)"),
            "border": f"1px solid {BORDER_COLOR}"
        }
    )

def navbar(page_title: str) -> rx.Component:
    """Topbar with status monitoring controls and alert banner."""
    
    # Translate page titles if needed
    title_translated = rx.cond(
        page_title == "Dashboard KPIs & Analíticas",
        "Panel de KPIs y Analítica",
        page_title
    )
    
    has_issue = (AppState.api_status == "unhealthy") | (AppState.mcp_status == "unhealthy") | (AppState.redis_status == "unhealthy") | AppState.cb_is_open

    return rx.vstack(
        rx.hstack(
            # Page Title
            rx.heading(title_translated, size="6", style={"font_weight": "700", "color": TEXT_COLOR}),
            
            rx.spacer(),
            
            # Health indicators
            rx.hstack(
                health_indicator("API", AppState.api_status),
                health_indicator("MCP", AppState.mcp_status),
                health_indicator("REDIS", AppState.redis_status),
                
                # Circuit Breaker badge
                rx.cond(
                    AppState.cb_is_open,
                    rx.badge("⚠️ CIRCUIT BREAKER: ABIERTO", color_scheme="ruby", variant="solid"),
                    rx.badge("✓ CIRCUIT BREAKER: OK", color_scheme="green", variant="soft")
                ),
                
                # Refresh indicator
                rx.icon_button(
                    rx.icon("refresh-cw", size=15),
                    on_click=AppState.update_health,
                    variant="ghost",
                    style={"cursor": "pointer", "color": ACCENT_BLUE}
                ),
                
                # Theme toggle indicator
                rx.icon_button(
                    rx.color_mode_cond(rx.icon("moon", size=15), rx.icon("sun", size=15)),
                    on_click=rx.toggle_color_mode,
                    variant="ghost",
                    style={"cursor": "pointer", "color": ACCENT_BLUE}
                ),
                
                rx.text(f"Actualizado: {AppState.last_checked}", font_size="10px", color=TEXT_MUTED),
                
                spacing="3",
                align="center"
            ),
            
            style={
                "width": "100%",
                "padding_bottom": "16px",
                "border_bottom": f"1px solid {BORDER_COLOR}",
                "margin_bottom": "16px"
            }
        ),
        
        # System Warning Banner (Shown only when issues are detected)
        rx.cond(
            has_issue,
            rx.callout.root(
                rx.callout.icon(rx.icon("triangle-alert")),
                rx.callout.text("Atención: Uno o más servicios del sistema presentan interrupción o respuesta degradada. Algunas funciones podrían verse afectadas."),
                color_scheme="amber",
                role="alert",
                style={"width": "100%", "margin_bottom": "16px"}
            )
        ),
        width="100%"
    )
