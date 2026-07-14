import reflex as rx
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.components.styling import BG_COLOR, GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, gradient_heading

def login_page() -> rx.Component:
    """The login page component with premium dark glass theme."""
    return rx.box(
        # Starfield/Neon aura background
        rx.box(
            style={
                "position": "absolute",
                "width": "300px",
                "height": "300px",
                "background_color": ACCENT_BLUE,
                "filter": "blur(150px)",
                "opacity": "0.15",
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
                "opacity": "0.15",
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
                        gradient_heading("ORBIT SYSTEM", size="8"),
                        rx.text(
                            "Integration Middleware Control Panel", 
                            font_size="14px", 
                            color="#8E9BB8", 
                            text_align="center"
                        ),
                        spacing="2",
                        align="center",
                        style={"margin_bottom": "24px"}
                    ),
                    
                    # Form
                    rx.form(
                        rx.vstack(
                            # Input Fields
                            rx.vstack(
                                rx.text("Correo Electrónico", font_size="12px", font_weight="bold", color="#A0AEC0"),
                                rx.input(
                                    name="email",
                                    placeholder="ejemplo@maxillc.com",
                                    type="email",
                                    width="100%",
                                    variant="surface",
                                    style={
                                        "background_color": "rgba(255, 255, 255, 0.03)",
                                        "border": "1px solid rgba(0, 217, 255, 0.15)",
                                        "color": "#FFFFFF",
                                        "border_radius": "8px",
                                        "padding": "10px 14px",
                                    }
                                ),
                                align_items="start",
                                width="100%",
                                spacing="1"
                            ),
                            rx.vstack(
                                rx.text("Contraseña", font_size="12px", font_weight="bold", color="#A0AEC0"),
                                rx.input(
                                    name="password",
                                    placeholder="••••••••",
                                    type="password",
                                    width="100%",
                                    variant="surface",
                                    style={
                                        "background_color": "rgba(255, 255, 255, 0.03)",
                                        "border": "1px solid rgba(0, 217, 255, 0.15)",
                                        "color": "#FFFFFF",
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
                                rx.text(
                                    AuthState.error_message, 
                                    color="var(--ruby-9)", 
                                    font_size="12px", 
                                    font_weight="500",
                                    style={"width": "100%", "text_align": "center"}
                                )
                            ),
                            
                            # Submit button
                            rx.button(
                                "Iniciar Sesión",
                                type="submit",
                                width="100%",
                                style={
                                    "background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)",
                                    "color": "#FFFFFF",
                                    "border_radius": "8px",
                                    "font_weight": "bold",
                                    "padding": "12px 24px",
                                    "cursor": "pointer",
                                    "transition": "transform 0.2s ease, box_shadow 0.2s ease",
                                    "box_shadow": f"0 4px 14px 0 rgba(0, 217, 255, 0.3)",
                                    "&_hover": {
                                        "transform": "translateY(-2px)",
                                        "box_shadow": f"0 6px 20px 0 rgba(0, 217, 255, 0.45)",
                                    }
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
                        "padding": "40px",
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
