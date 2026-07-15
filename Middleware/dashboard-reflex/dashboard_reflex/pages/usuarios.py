import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.components.styling import (
    GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, BORDER_COLOR, TEXT_MUTED,
    glass_container
)
from dashboard_reflex.api.client import api_client
from dashboard_reflex.state.auth_state import SUPER_ADMIN_EMAILS, AuthState
import os
import redis
import json

# Connect to Redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    r_client = redis.from_url(redis_url, decode_responses=True)
except Exception:
    r_client = None

from pydantic import BaseModel

class DashboardUserData(BaseModel):
    email: str = ""
    name: str = ""
    role: str = ""
    is_super_admin: bool = False

class UsuariosState(rx.State):
    users: list[DashboardUserData] = []
    
    # Form fields
    new_email: str = ""
    new_name: str = ""
    new_role: str = "supervisor"
    
    is_loading: bool = False

    def set_new_email(self, val: str):
        self.new_email = val.strip().lower()
    def set_new_name(self, val: str):
        self.new_name = val
    def set_new_role(self, val: str):
        self.new_role = val

    async def load_users(self):
        self.is_loading = True
        user_list = []
        emails_seen = set()

        auth_state = await self.get_state(AuthState)
        is_sa = auth_state.role == "super_admin"
        is_admin = auth_state.role == "admin"
        current_email = auth_state.email.strip().lower()

        if r_client:
            try:
                # Scan all orbit:user:* keys
                keys = r_client.keys("orbit:user:*")
                for key in keys:
                    val = r_client.get(key)
                    if val:
                        try:
                            data = json.loads(val)
                            email = data.get("email", "").strip().lower()
                            if not email:
                                continue
                            role = data.get("role", "supervisor")
                            user_is_sa = email in SUPER_ADMIN_EMAILS
                            if user_is_sa:
                                role = "super_admin"
                            
                            # Privacy Filter: Admins can only see supervisors (and themselves)
                            if is_admin and role != "supervisor" and email != current_email:
                                continue
                                
                            user_list.append(
                                DashboardUserData(
                                    email=email,
                                    name=data.get("name", ""),
                                    role=role,
                                    is_super_admin=user_is_sa
                                )
                            )
                            emails_seen.add(email)
                        except Exception:
                            pass
            except Exception as e:
                rx.toast.error(f"Error cargando usuarios: {str(e)}")

        # Ensure super admins are always present in the list, but only if current user is Super Admin
        for sa_email in SUPER_ADMIN_EMAILS:
            if is_admin:
                # Admins shouldn't see other Super Admins
                continue
            if sa_email not in emails_seen:
                name_part = sa_email.split("@")[0].replace(".", " ").title()
                user_list.append(
                    DashboardUserData(
                        email=sa_email,
                        name=name_part,
                        role="super_admin",
                        is_super_admin=True
                    )
                )

        self.users = user_list
        self.is_loading = False

    async def change_user_role(self, email: str, new_role: str):
        if email in SUPER_ADMIN_EMAILS:
            rx.toast.warning("No se puede cambiar el rol de un Super Admin.")
            return

        auth_state = await self.get_state(AuthState)
        if auth_state.role != "super_admin":
            rx.toast.error("Solo los Super Administradores pueden cambiar roles de usuario.")
            return

        if r_client:
            try:
                key = f"orbit:user:{email}"
                val = r_client.get(key)
                name = email.split("@")[0].title()
                if val:
                    data = json.loads(val)
                    name = data.get("name", name)
                
                new_data = {
                    "email": email,
                    "name": name,
                    "role": new_role
                }
                r_client.set(key, json.dumps(new_data))
                rx.toast.success(f"Rol de {email} cambiado a {new_role}.")
                # Log audit action
                await api_client.log_audit_action({
                    "username": auth_state.username or "admin",
                    "role": auth_state.role or "admin",
                    "action": "CONFIG_CHANGE",
                    "details": f"Changed role of user {email} to {new_role}"
                })
                await self.load_users()
            except Exception as e:
                rx.toast.error(f"Error al cambiar rol: {str(e)}")

    async def delete_user(self, email: str):
        if email in SUPER_ADMIN_EMAILS:
            rx.toast.error("No se puede eliminar a un Super Admin.")
            return

        if r_client:
            try:
                key = f"orbit:user:{email}"
                r_client.delete(key)
                rx.toast.success(f"Usuario {email} eliminado.")
                # Log audit action
                auth_state = await self.get_state(AuthState)
                await api_client.log_audit_action({
                    "username": auth_state.username or "admin",
                    "role": auth_state.role or "admin",
                    "action": "CONFIG_CHANGE",
                    "details": f"Deleted dashboard access for user {email}"
                })
                await self.load_users()
            except Exception as e:
                rx.toast.error(f"Error al eliminar usuario: {str(e)}")

    async def add_user(self):
        if not self.new_email or not self.new_name:
            rx.toast.error("Por favor, llene todos los campos.")
            return

        if self.new_email in SUPER_ADMIN_EMAILS:
            rx.toast.warning("El correo especificado ya es un Super Admin configurado.")
            return

        auth_state = await self.get_state(AuthState)
        role_to_set = self.new_role
        if auth_state.role == "admin":
            # Admins can only register supervisors
            role_to_set = "supervisor"

        if r_client:
            try:
                key = f"orbit:user:{self.new_email}"
                user_data = {
                    "email": self.new_email,
                    "name": self.new_name,
                    "role": role_to_set
                }
                r_client.set(key, json.dumps(user_data))
                rx.toast.success(f"Usuario {self.new_email} registrado exitosamente.")
                
                # Log audit action
                auth_state = await self.get_state(AuthState)
                await api_client.log_audit_action({
                    "username": auth_state.username or "admin",
                    "role": auth_state.role or "admin",
                    "action": "CONFIG_CHANGE",
                    "details": f"Registered new user {self.new_email} with role {role_to_set}"
                })

                # Clear fields
                self.new_email = ""
                self.new_name = ""
                self.new_role = "supervisor"
                
                await self.load_users()
            except Exception as e:
                rx.toast.error(f"Error al registrar usuario: {str(e)}")

    async def on_load(self):
        await self.load_users()

def user_row(user: DashboardUserData) -> rx.Component:
    """Renders a single row in the user management table."""
    return rx.table.row(
        rx.table.cell(user.email, font_family="Courier New", font_size="13px"),
        rx.table.cell(user.name, font_size="13px"),
        rx.table.cell(
            rx.cond(
                user.is_super_admin,
                rx.badge("SUPER ADMIN", color_scheme="purple"),
                rx.cond(
                    AuthState.role == "super_admin",
                    rx.select(
                        ["supervisor", "admin"],
                        value=user.role,
                        on_change=lambda val: UsuariosState.change_user_role(user.email, val),
                        style={"background_color": rx.color_mode_cond("#FFFFFF", "#080B16"), "border": f"1px solid {BORDER_COLOR}", "color": rx.color_mode_cond("#1A202C", "#FFFFFF"), "border_radius": "6px", "padding": "2px"}
                    ),
                    rx.badge(user.role.upper(), color_scheme="blue", variant="outline")
                )
            )
        ),
        rx.table.cell(
            rx.cond(
                user.is_super_admin,
                rx.text("Protegido", color=TEXT_MUTED, font_size="12px"),
                rx.button(
                    "Eliminar",
                    size="1",
                    color_scheme="ruby",
                    variant="soft",
                    on_click=lambda: UsuariosState.delete_user(user.email),
                    style={"cursor": "pointer"}
                )
            )
        )
    )

def usuarios_page() -> rx.Component:
    """The User Management control panel page."""
    
    # Register new user panel
    add_user_panel = glass_container(
        rx.vstack(
            rx.heading("➕ Registrar Nuevo Usuario", size="3", color=TEXT_COLOR, style={"margin_bottom": "12px"}),
            rx.grid(
                rx.vstack(
                    rx.text("Correo Electrónico", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                    rx.input(
                        placeholder="ejemplo@maxillc.com",
                        value=UsuariosState.new_email,
                        on_change=UsuariosState.set_new_email,
                        style={"background_color": rx.color_mode_cond("#FFFFFF", "#080B16"), "border": f"1px solid {BORDER_COLOR}", "color": TEXT_COLOR, "border_radius": "6px", "width": "100%"}
                    ),
                    align_items="start",
                    width="100%"
                ),
                rx.vstack(
                    rx.text("Nombre Completo", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                    rx.input(
                        placeholder="Juan Perez",
                        value=UsuariosState.new_name,
                        on_change=UsuariosState.set_new_name,
                        style={"background_color": rx.color_mode_cond("#FFFFFF", "#080B16"), "border": f"1px solid {BORDER_COLOR}", "color": TEXT_COLOR, "border_radius": "6px", "width": "100%"}
                    ),
                    align_items="start",
                    width="100%"
                ),
                rx.vstack(
                    rx.text("Rol Inicial", font_size="11px", font_weight="bold", color=TEXT_MUTED),
                    rx.cond(
                        AuthState.role == "super_admin",
                        rx.select(
                            ["supervisor", "admin"],
                            value=UsuariosState.new_role,
                            on_change=UsuariosState.set_new_role,
                            style={"background_color": rx.color_mode_cond("#FFFFFF", "#080B16"), "border": f"1px solid {BORDER_COLOR}", "color": TEXT_COLOR, "border_radius": "6px", "padding": "4px", "width": "100%"}
                        ),
                        rx.input(
                            value="supervisor",
                            disabled=True,
                            style={"background_color": rx.color_mode_cond("#E2E8F0", "#1A202C"), "border": f"1px solid {BORDER_COLOR}", "color": TEXT_MUTED, "border_radius": "6px", "width": "100%"}
                        )
                    ),
                    align_items="start",
                    width="100%"
                ),
                columns="3",
                spacing="4",
                width="100%"
            ),
            rx.button(
                "Registrar Usuario",
                on_click=UsuariosState.add_user,
                variant="solid",
                style={
                    "background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)",
                    "color": "#FFFFFF",
                    "cursor": "pointer",
                    "margin_top": "16px",
                    "align_self": "end"
                }
            ),
            width="100%"
        ),
        style={"padding": "20px", "margin_bottom": "24px"}
    )

    # User List Panel
    users_list_panel = glass_container(
        rx.vstack(
            rx.hstack(
                rx.heading("👥 Usuarios con Acceso al Dashboard", size="3", color=TEXT_COLOR),
                rx.spacer(),
                rx.button(
                    rx.hstack(rx.icon("refresh-cw", size=12), rx.text("Recargar"), spacing="2"),
                    on_click=UsuariosState.load_users,
                    size="1",
                    variant="soft",
                    style={"cursor": "pointer"}
                ),
                width="100%",
                align_items="center",
                style={"margin_bottom": "12px"}
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Correo Electrónico"),
                        rx.table.column_header_cell("Nombre"),
                        rx.table.column_header_cell("Rol / Permisos"),
                        rx.table.column_header_cell("Acciones")
                    )
                ),
                rx.table.body(
                    rx.cond(
                        UsuariosState.is_loading,
                        rx.table.row(
                            rx.table.cell(rx.center(rx.spinner(size="2")), colspan=4)
                        ),
                        rx.foreach(
                            UsuariosState.users,
                            user_row
                        )
                    )
                ),
                variant="surface",
                style={"width": "100%"}
            ),
            width="100%"
        ),
        style={"padding": "20px"}
    )

    content = rx.vstack(
        add_user_panel,
        users_list_panel,
        width="100%",
        spacing="1"
    )

    return protected_layout(content, "Administración de Usuarios", "/usuarios")
