import reflex as rx
from dashboard_reflex.pages.login import login_page
from dashboard_reflex.pages.home import home_page
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.state.app_state import AppState

# Styles for whole app
app_style = {
    "font_family": "Inter, sans-serif",
}

app = rx.App(style=app_style)

# Register pages with authentication guards and health checks
app.add_page(
    home_page,
    route="/",
    on_load=[AuthState.check_auth, AppState.on_load],
    title="Orbit Dashboard | KPIs"
)

app.add_page(
    login_page,
    route="/login",
    title="Orbit Dashboard | Iniciar Sesión"
)
