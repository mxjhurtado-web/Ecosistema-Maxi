import reflex as rx
from dashboard_reflex.pages.login import login_page
from dashboard_reflex.pages.home import home_page
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.state.app_state import AppState
from dashboard_reflex.pages.history import history_page
from dashboard_reflex.pages.history import HistoryState
from dashboard_reflex.pages.config import config_page
from dashboard_reflex.pages.config import ConfigState
from dashboard_reflex.pages.maintenance import maintenance_page
from dashboard_reflex.pages.maintenance import MaintenanceState
from dashboard_reflex.pages.auditoria import auditoria_page
from dashboard_reflex.pages.auditoria import AuditState
from dashboard_reflex.pages.chat import chat_page
from dashboard_reflex.pages.chat import ChatState
from dashboard_reflex.pages.logs import logs_page
from dashboard_reflex.pages.logs import LogsState
from dashboard_reflex.pages.maxibot import maxibot_page
from dashboard_reflex.pages.maxibot import MaxiBotState
from dashboard_reflex.pages.orbit_bot import orbit_page
from dashboard_reflex.pages.orbit_bot import OrbitBotState
from dashboard_reflex.pages.usuarios import usuarios_page
from dashboard_reflex.pages.usuarios import UsuariosState
from dashboard_reflex.pages.callback import callback_page
from dashboard_reflex.pages.callback import CallbackState
from dashboard_reflex.pages.calidad import calidad_page, CalidadState


# Styles for whole app
app_style = {
    "font_family": "Inter, sans-serif",
}

app = rx.App(style=app_style, admin_dash=False, stylesheets=["styles.css"])

# Register pages with authentication guards and health checks
app.add_page(
    home_page,
    route="/",
    on_load=[AuthState.check_auth, AppState.on_load],
    title="Orbit Dashboard | KPIs"
)

app.add_page(
    history_page,
    route="/history",
    on_load=[AuthState.check_auth, HistoryState.on_load, AppState.on_load],
    title="Orbit Dashboard | Historial"
)

app.add_page(
    calidad_page,
    route="/calidad",
    on_load=[AuthState.check_auth, CalidadState.on_load, AppState.on_load],
    title="Orbit Dashboard | Calidad"
)

app.add_page(
    config_page,
    route="/config",
    on_load=[AuthState.check_admin, ConfigState.on_load, AppState.on_load],
    title="Orbit Dashboard | Configuración"
)

app.add_page(
    maintenance_page,
    route="/maintenance",
    on_load=[AuthState.check_admin, MaintenanceState.on_load, AppState.on_load],
    title="Orbit Dashboard | Mantenimiento"
)

app.add_page(
    auditoria_page,
    route="/auditoria",
    on_load=[AuthState.check_admin, AuditState.on_load, AppState.on_load],
    title="Orbit Dashboard | Auditoría"
)

app.add_page(
    chat_page,
    route="/chat",
    on_load=[AuthState.check_admin, ChatState.on_load, AppState.on_load],
    title="Orbit Dashboard | Chat MCP"
)

app.add_page(
    logs_page,
    route="/logs",
    on_load=[AuthState.check_admin, LogsState.on_load, AppState.on_load],
    title="Orbit Dashboard | Logs en Vivo"
)

app.add_page(
    maxibot_page,
    route="/maxibot",
    on_load=[AuthState.check_admin, MaxiBotState.on_load, AppState.on_load],
    title="Orbit Dashboard | MaxiBot Panel"
)

app.add_page(
    orbit_page,
    route="/orbit",
    on_load=[AuthState.check_admin, OrbitBotState.on_load, AppState.on_load],
    title="Orbit Dashboard | Orbit Bot Panel"
)

app.add_page(
    usuarios_page,
    route="/usuarios",
    on_load=[AuthState.check_admin, UsuariosState.on_load, AppState.on_load],
    title="Orbit Dashboard | Usuarios"
)

app.add_page(
    callback_page,
    route="/callback",
    on_load=[CallbackState.handle_callback],
    title="Orbit Dashboard | Autenticando SSO..."
)

app.add_page(
    login_page,
    route="/login",
    title="Orbit Dashboard | Iniciar Sesión"
)
