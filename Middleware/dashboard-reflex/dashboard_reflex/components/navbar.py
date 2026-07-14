import reflex as rx
from dashboard_reflex.state.app_state import AppState
from dashboard_reflex.components.styling import BORDER_COLOR, ACCENT_BLUE

def health_indicator(name: str, status: rx.Var) -> rx.Component:
    """Displays a tiny status dot with a label."""
    color = rx.cond(
        (status == "healthy") | (status == "online"),
        "var(--emerald-9)",
        rx.cond(
            status == "checking",
            "var(--sky-9)",
            "var(--ruby-9)"
        )
    )
    bg_glow = rx.cond(
        (status == "healthy") | (status == "online"),
        "0 0 8px var(--emerald-7)",
        rx.cond(
            status == "checking",
            "0 0 8px var(--sky-7)",
            "0 0 8px var(--ruby-7)"
        )
    )
    return rx.hstack(
        rx.box(
            style={
                "width": "8px",
                "height": "8px",
                "border_radius": "50%",
                "background_color": color,
                "box_shadow": bg_glow
            }
        ),
        rx.text(name, font_size="11px", font_weight="bold", color="#A0AEC0"),
        rx.text(status, font_size="11px", font_weight="bold", color="#FFFFFF"),
        spacing="2",
        align="center",
        style={
            "padding": "6px 12px",
            "border_radius": "6px",
            "background_color": "rgba(255, 255, 255, 0.03)",
            "border": f"1px solid {BORDER_COLOR}"
        }
    )

def navbar(page_title: str) -> rx.Component:
    """Topbar with status monitoring controls."""
    return rx.hstack(
        # Page Title
        rx.heading(page_title, size="6", style={"font_weight": "700", "color": "#FFFFFF"}),
        
        rx.spacer(),
        
        # Health indicators
        rx.hstack(
            health_indicator("API", AppState.api_status),
            health_indicator("MCP", AppState.mcp_status),
            health_indicator("REDIS", AppState.redis_status),
            
            # Circuit Breaker badge
            rx.cond(
                AppState.cb_is_open,
                rx.badge("CIRCUIT BREAKER: OPEN", color_scheme="ruby", variant="solid"),
                rx.badge("CIRCUIT BREAKER: OK", color_scheme="green", variant="soft")
            ),
            
            # Refresh indicator
            rx.icon_button(
                rx.icon("refresh_cw", size=15),
                on_click=AppState.update_health,
                variant="ghost",
                style={"cursor": "pointer", "color": ACCENT_BLUE}
            ),
            
            rx.text(f"Actualizado: {AppState.last_checked}", font_size="10px", color="#A0AEC0"),
            
            spacing="3",
            align="center"
        ),
        
        style={
            "width": "100%",
            "padding_bottom": "20px",
            "border_bottom": f"1px solid {BORDER_COLOR}",
            "margin_bottom": "30px"
        }
    )
