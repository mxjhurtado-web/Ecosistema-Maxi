import reflex as rx
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.components.styling import BORDER_COLOR, SIDEBAR_STYLE, ACCENT_BLUE, TEXT_MUTED, TEXT_COLOR

def sidebar_link(title: str, icon: str, url: str, active: bool = False) -> rx.Component:
    """A sidebar navigation link."""
    link_color = ACCENT_BLUE if active else TEXT_COLOR
    bg_color = "rgba(0, 217, 255, 0.08)" if active else "transparent"
    border_left = f"3px solid {ACCENT_BLUE}" if active else "3px solid transparent"
    
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=18, color=link_color),
            rx.text(title, font_size="14px", font_weight="500", color=link_color),
            spacing="3",
            align="center",
            style={
                "padding": "12px 16px",
                "border_radius": "8px",
                "background_color": bg_color,
                "border_left": border_left,
                "transition": "all 0.2s ease-in-out",
                "width": "100%",
                "cursor": "pointer",
                "&_hover": {
                    "background_color": rx.color_mode_cond("rgba(0, 0, 0, 0.04)", "rgba(255, 255, 255, 0.04)"),
                }
            }
        ),
        href=url,
        style={"text_decoration": "none", "width": "100%"}
    )

def sidebar(current_page: str) -> rx.Component:
    """The main sidebar component."""
    
    # Section 1: Monitoreo (Visible to everyone)
    monitoring_items = [
        ("Resumen", "layout-dashboard", "/"),
        ("Historial", "history", "/history"),
        ("Calidad", "square-check", "/calidad"),
    ]
    
    # Section 2: Operación (Admin/Super Admin)
    operations_items = [
        ("Logs en Vivo", "file-text", "/logs"),
        ("Decisiones FSM", "git-branch", "/decision-logs"),
        ("Chat MCP", "message-square", "/chat"),
    ]

    # Section 3: Administración (Admin/Super Admin)
    admin_items = [
        ("Configuración", "settings", "/config"),
        ("Mantenimiento", "wrench", "/maintenance"),
        ("Auditoría", "shield-alert", "/auditoria"),
        ("Usuarios", "users", "/usuarios"),
        ("MaxiBot Panel", "bot", "/maxibot"),
        ("Orbit Bot Panel", "activity", "/orbit"),
    ]
    
    role_display = rx.cond(
        AuthState.role == "SUPER_ADMIN",
        "Superadministrador",
        rx.cond(
            AuthState.role == "ADMIN",
            "Administrador",
            "Analista"
        )
    )

    return rx.box(
        rx.vstack(
            # Logo header
            rx.hstack(
                rx.icon("orbit", size=28, color=ACCENT_BLUE),
                rx.text("ORBIT", font_size="22px", font_weight="900", letter_spacing="1px", color=TEXT_COLOR),
                spacing="2",
                align="center",
                style={"margin_bottom": "24px", "width": "100%", "justify_content": "center"}
            ),
            
            # Nav links container
            rx.vstack(
                # Section 1 Header & Links: MONITOREO
                rx.text("MONITOREO", font_size="10px", font_weight="bold", color=TEXT_MUTED, style={"padding_left": "12px", "letter_spacing": "1.5px"}),
                *[sidebar_link(title, icon, url, current_page == url) for title, icon, url in monitoring_items],
                
                # Section 2 & 3: Admin / Super Admin options
                rx.cond(
                    AuthState.is_admin_or_higher,
                    rx.vstack(
                        rx.divider(style={"border_color": BORDER_COLOR, "margin": "12px 0 8px 0"}),
                        rx.text("OPERACIÓN", font_size="10px", font_weight="bold", color=TEXT_MUTED, style={"padding_left": "12px", "letter_spacing": "1.5px"}),
                        *[sidebar_link(title, icon, url, current_page == url) for title, icon, url in operations_items],
                        
                        rx.divider(style={"border_color": BORDER_COLOR, "margin": "12px 0 8px 0"}),
                        rx.text("ADMINISTRACIÓN", font_size="10px", font_weight="bold", color=TEXT_MUTED, style={"padding_left": "12px", "letter_spacing": "1.5px"}),
                        *[sidebar_link(title, icon, url, current_page == url) for title, icon, url in admin_items],
                        width="100%",
                        spacing="1"
                    )
                ),
                width="100%",
                spacing="1",
                align_items="start",
                style={"overflow_y": "auto", "flex": "1"}
            ),
            
            # Sidebar Footer / User Info
            rx.vstack(
                rx.divider(style={"border_color": BORDER_COLOR, "margin_bottom": "12px"}),
                rx.hstack(
                    rx.vstack(
                        rx.text(AuthState.username, font_size="13px", font_weight="bold", color=TEXT_COLOR),
                        rx.text(role_display, font_size="11px", font_weight="bold", color=ACCENT_BLUE),
                        spacing="0",
                        align_items="start"
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("log-out", size=16),
                        on_click=AuthState.logout,
                        color_scheme="ruby",
                        variant="soft",
                        style={"cursor": "pointer"}
                    ),
                    width="100%",
                    align_items="center"
                ),
                width="100%"
            ),
            height="100%",
            spacing="0",
            align_items="stretch"
        ),
        style=SIDEBAR_STYLE
    )
