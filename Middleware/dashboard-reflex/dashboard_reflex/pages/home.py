import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.state.app_state import AppState

def home_page() -> rx.Component:
    """KPIs & Summary dashboard page (index)."""
    content = rx.vstack(
        rx.heading("Resumen de KPIs", size="6"),
        rx.text("Bienvenido al control panel de Orbit Middleware. Los componentes se cargarán pronto."),
        spacing="4"
    )
    return protected_layout(content, "Dashboard KPIs", "/")
