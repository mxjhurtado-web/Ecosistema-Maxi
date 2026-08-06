import reflex as rx
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.components.styling import BG_COLOR, GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, gradient_heading

def login_page() -> rx.Component:
    """The login page component with refined enterprise theme."""
    return rx.box(
        # Starfield/Neon aura background
        rx.box(
            style={
                "position": "absolute",
                "width": "300px",
                "height": "300px",
                "background_color": ACCENT_BLUE,
                "filter": "blur(150px)",
                "opacity": "0.12",
                "top": "20%",
                "left": "30%",
                "z_index": "0"
            }
        ),
        rx.box(
            style={
                "position": "absolute",
                "width": "300px",
                "height": "300px",
                "background_color": ACCENT_PURPLE,
                "filter": "blur(150px)",
                "opacity": "0.12",
                "bottom": "20%",
                "right": "30%",
                "z_index": "0"
            }
        ),
        
        # Center container
        rx.center(
            rx.vstack(
                # Glass card
                rx.vstack(
                    # Header
                    rx.vstack(
                        rx.icon("orbit", size=48, color=ACCENT_BLUE),
                        gradient_heading("SISTEMA ORBIT", size="8"),
                        rx.text(
                            "Panel de Control de Middleware e Integraciones", 
                            font_size="13px", 
                            color=rx.color_mode_cond("#64748B", "#94A3B8"), 
                            text_align="center"
                        ),
                        rx.badge("Orbit v1.4 · Producción", color_scheme="cyan", variant="soft", size="2"),
                        spacing="2",
                        align="center",
                        style={"margin_bottom": "20px"}
                    ),
                    
                    # SSO Button (Highlighted as Recommended Access Option)
                    rx.button(
                        rx.hstack(
                            rx.icon("key-round", size=18),
                            rx.text("Iniciar Sesión con SSO Keycloak"),
                            spacing="2"
                        ),
                        type="button",
                        on_click=AuthState.sso_redirect,
                        width="100%",
                        style={
                            "background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)",
                            "color": "#FFFFFF",
                            "border_radius": "8px",
                            "font_weight": "bold",
                            "padding": "12px 24px",
                            "cursor": "pointer",
                            "transition": "transform 0.2s ease, box_shadow 0.2s ease",
                            "box_shadow": "0 4px 14px 0 rgba(56, 189, 248, 0.35)",
                            "&_hover": {
                                "transform": "translateY(-2px)",
                                "box_shadow": "0 6px 20px 0 rgba(56, 189, 248, 0.5)",
                            }
                        }
                    ),
                    
                    # Divider
                    rx.hstack(
                        rx.divider(style={"border_color": rx.color_mode_cond("#E2E8F0", "rgba(255, 255, 255, 0.1)"), "flex_grow": "1"}),
                        rx.text("o acceso local con correo", font_size="11px", color=rx.color_mode_cond("#64748B", "#94A3B8"), style={"padding": "0 8px"}),
                        rx.divider(style={"border_color": rx.color_mode_cond("#E2E8F0", "rgba(255, 255, 255, 0.1)"), "flex_grow": "1"}),
                        width="100%",
                        align_items="center",
                        style={"margin": "14px 0 10px 0"}
                    ),

                    # Form
                    rx.form(
                        rx.vstack(
                            # Input Fields
                            rx.vstack(
                                rx.text("Correo Electrónico", font_size="12px", font_weight="bold", color=rx.color_mode_cond("#475569", "#94A3B8")),
                                rx.input(
                                    name="email",
                                    placeholder="usuario@empresa.com",
                                    type="email",
                                    width="100%",
                                    variant="surface",
                                    style={
                                        "background_color": rx.color_mode_cond("#FFFFFF", "rgba(255, 255, 255, 0.03)"),
                                        "border": rx.color_mode_cond("1px solid #CBD5E1", "1px solid rgba(56, 189, 248, 0.2)"),
                                        "color": rx.color_mode_cond("#0F172A", "#FFFFFF"),
                                        "border_radius": "8px",
                                        "padding": "10px 14px",
                                    }
                                ),
                                align_items="start",
                                width="100%",
                                spacing="1"
                            ),
                            rx.vstack(
                                rx.text("Contraseña", font_size="12px", font_weight="bold", color=rx.color_mode_cond("#475569", "#94A3B8")),
                                rx.input(
                                    name="password",
                                    placeholder="••••••••",
                                    type="password",
                                    width="100%",
                                    variant="surface",
                                    style={
                                        "background_color": rx.color_mode_cond("#FFFFFF", "rgba(255, 255, 255, 0.03)"),
                                        "border": rx.color_mode_cond("1px solid #CBD5E1", "1px solid rgba(56, 189, 248, 0.2)"),
                                        "color": rx.color_mode_cond("#0F172A", "#FFFFFF"),
                                        "border_radius": "8px",
                                        "padding": "10px 14px",
                                    }
                                ),
                                align_items="start",
                                width="100%",
                                spacing="1"
                            ),
                            
                            # Error message display
                            rx.cond(
                                AuthState.error_message != "",
                                rx.callout.root(
                                    rx.callout.icon(rx.icon("triangle-alert")),
                                    rx.callout.text(AuthState.error_message),
                                    color_scheme="ruby",
                                    role="alert",
                                    style={"width": "100%"}
                                )
                            ),
                            # Submit button
                            rx.button(
                                "Ingresar con credenciales locales",
                                type="submit",
                                width="100%",
                                variant="soft",
                                color_scheme="cyan",
                                style={
                                    "border_radius": "8px",
                                    "font_weight": "bold",
                                    "padding": "10px 24px",
                                    "cursor": "pointer"
                                }
                            ),
                            spacing="4",
                            width="100%"
                        ),
                        on_submit=AuthState.login,
                        width="100%"
                    ),
                    style={
                        **GLASS_EFFECT,
                        "padding": "36px",
                        "width": "420px",
                    }
                ),
                align="center",
                width="100%"
            ),
            height="100vh",
            width="100vw",
            z_index="10"
        ),
        style={
            "background_color": BG_COLOR,
            "width": "100vw",
            "height": "100vh",
            "position": "relative",
            "overflow": "hidden"
        }
    )
