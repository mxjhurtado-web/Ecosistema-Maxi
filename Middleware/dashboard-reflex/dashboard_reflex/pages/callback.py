import reflex as rx
from dashboard_reflex.state.auth_state import AuthState, SUPER_ADMIN_EMAILS, r as r_client
from dashboard_reflex.components.styling import BG_COLOR, GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, TEXT_MUTED
import httpx
import os
import json
from jose import jwt

class CallbackState(rx.State):
    is_authenticating: bool = True
    error_message: str = ""

    async def handle_callback(self):
        # 1. Get code from URL query parameters
        code = self.router.page.params.get("code")
        if not code:
            self.error_message = "No se recibió código de autorización de Keycloak en los parámetros."
            self.is_authenticating = False
            return

        # 2. Exchange code for access/identity token
        kc_url = os.getenv("KC_SERVER_URL", "https://sso.maxilabs.net/auth")
        realm = os.getenv("KC_REALM", "zeusDev")
        client_id = os.getenv("KC_CLIENT_ID", "maxi-business-ai")
        client_secret = os.getenv("KC_CLIENT_SECRET", "mOLonfMkGYnhq3M4CSnzY4p7fFakNciu")
        redirect_uri = os.getenv("KC_REDIRECT_URI", "https://orbit-dashboard-ewov.onrender.com/callback")

        token_url = f"{kc_url.rstrip('/')}/realms/{realm}/protocol/openid-connect/token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(token_url, data=data, timeout=15)
                if resp.status_code != 200:
                    self.error_message = f"Error al intercambiar código (HTTP {resp.status_code}): {resp.text[:300]}"
                    self.is_authenticating = False
                    return
                
                tokens = resp.json()
                # Try to use id_token, fallback to access_token
                id_token = tokens.get("id_token") or tokens.get("access_token")
                if not id_token:
                    self.error_message = "El token de inicio de sesión recibido no es válido."
                    self.is_authenticating = False
                    return

                # Decode claims to extract user information
                claims = jwt.get_unverified_claims(id_token)
                email = claims.get("email", "").strip().lower()
                name = claims.get("name", "").strip() or claims.get("preferred_username", "").strip()

                if not email:
                    self.error_message = "No se pudo extraer una dirección de correo válida del token SSO."
                    self.is_authenticating = False
                    return

                # 3. Determine permissions & sync with Redis
                role = "supervisor"
                is_sa = email in SUPER_ADMIN_EMAILS
                if is_sa:
                    role = "super_admin"
                else:
                    if r_client:
                        try:
                            user_data = r_client.get(f"orbit:user:{email}")
                            if user_data:
                                data_parsed = json.loads(user_data)
                                role = data_parsed.get("role", "supervisor")
                            else:
                                # New registration gets supervisor by default
                                new_user = {
                                    "email": email,
                                    "name": name or email.split("@")[0].title(),
                                    "role": "supervisor"
                                }
                                r_client.set(f"orbit:user:{email}", json.dumps(new_user))
                        except Exception as redis_err:
                            print(f"Redis check error: {redis_err}")

                # 4. Set session in AuthState
                username_derived = name or email.split("@")[0].replace(".", " ").title()
                
                # Settle session variables
                return [
                    AuthState.set_session(email, username_derived, role),
                    rx.redirect("/")
                ]

        except Exception as e:
            self.error_message = f"Excepción interna de conexión: {str(e)}"
            self.is_authenticating = False

def callback_page() -> rx.Component:
    """Renders the SSO callback loading and status page."""
    return rx.box(
        rx.center(
            rx.vstack(
                rx.cond(
                    CallbackState.is_authenticating,
                    rx.vstack(
                        rx.spinner(size="3", color=ACCENT_BLUE),
                        rx.text("Procesando credenciales SSO...", font_size="16px", font_weight="bold"),
                        rx.text("Estableciendo conexión segura con Keycloak", font_size="12px", color=TEXT_MUTED),
                        spacing="3",
                        align="center"
                    ),
                    rx.vstack(
                        rx.icon("circle_alert", size=48, color="var(--ruby-9)"),
                        rx.text("Fallo de Autenticación SSO", font_size="18px", font_weight="bold", color="var(--ruby-9)"),
                        rx.text(CallbackState.error_message, font_size="13px", color="#FFFFFF", text_align="center", max_width="400px"),
                        rx.link(
                            rx.button("Volver al Login", variant="solid", style={"background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)", "color": "#FFFFFF", "cursor": "pointer"}),
                            href="/login"
                        ),
                        spacing="4",
                        align="center"
                    )
                ),
                style={
                    **GLASS_EFFECT,
                    "padding": "40px",
                    "width": "460px",
                    "border_radius": "12px"
                }
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
