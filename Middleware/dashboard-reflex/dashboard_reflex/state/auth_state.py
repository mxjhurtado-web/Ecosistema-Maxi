import reflex as rx
import redis
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    r = redis.from_url(redis_url, decode_responses=True)
except Exception:
    r = None

SUPER_ADMIN_EMAILS = [
    email.strip().lower() 
    for email in os.getenv("SUPER_ADMIN_EMAILS", "mxjhurtado@maxillc.com,mxmramirez@maxillc.com").split(",")
]
DEFAULT_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "orbit2026")

class AuthState(rx.State):
    """Global authentication state for Orbit Dashboard."""
    email: str = rx.LocalStorage("")
    username: str = rx.LocalStorage("")
    role: str = rx.LocalStorage("")
    is_authenticated: bool = rx.LocalStorage(False)
    error_message: str = ""

    def login(self, form_data: dict):
        """Handle temporary username/password authentication."""
        email_input = form_data.get("email", "").strip().lower()
        password_input = form_data.get("password", "")

        self.error_message = ""

        if not email_input or not password_input:
            self.error_message = "Por favor llene todos los campos."
            return

        # Check password (either custom in Redis/env or default)
        expected_password = DEFAULT_PASSWORD
        user_role = "supervisor"  # Default role for new users

        # If it's a hardcoded super admin
        if email_input in SUPER_ADMIN_EMAILS:
            user_role = "super_admin"
        else:
            # Check Redis for custom user configuration/role
            if r:
                try:
                    user_data = r.get(f"orbit:user:{email_input}")
                    if user_data:
                        data = json.loads(user_data)
                        user_role = data.get("role", "supervisor")
                except Exception as e:
                    print(f"Redis error: {e}")

        if password_input != expected_password:
            self.error_message = "Credenciales incorrectas."
            return

        # Success
        self.email = email_input
        # Derive name from email
        name_part = email_input.split("@")[0]
        self.username = name_part.replace(".", " ").title()
        self.role = user_role
        self.is_authenticated = True
        
        # Save to Redis if connection is alive to track users
        if r:
            try:
                r.set(
                    f"orbit:user:{email_input}", 
                    json.dumps({
                        "email": email_input,
                        "name": self.username,
                        "role": self.role
                    })
                )
            except Exception as e:
                print(f"Redis save error: {e}")

        # Redirect to main page
        return rx.redirect("/")

    def logout(self):
        """Clear user session and redirect to login."""
        self.email = ""
        self.username = ""
        self.role = ""
        self.is_authenticated = False
        self.error_message = ""
        return rx.redirect("/login")

    def check_auth(self):
        """Check if authenticated; if not, redirect to login."""
        if not self.is_authenticated:
            return rx.redirect("/login")

    def check_admin(self):
        """Check if authenticated and is admin/super_admin; if not, redirect accordingly."""
        if not self.is_authenticated:
            return rx.redirect("/login")
        if not self.is_admin_or_higher:
            return rx.redirect("/")

    @rx.var
    def is_super_admin(self) -> bool:
        return self.role == "super_admin"

    @rx.var
    def is_admin_or_higher(self) -> bool:
        return self.role in ["admin", "super_admin"]

    def set_session(self, email: str, name: str, role: str):
        """Set user session from external authentication like Keycloak."""
        self.email = email
        self.username = name
        self.role = role
        self.is_authenticated = True

    def sso_redirect(self):
        """Redirect browser to Keycloak login portal."""
        kc_url = os.getenv("KC_SERVER_URL", "https://sso.maxilabs.net/auth")
        realm = os.getenv("KC_REALM", "zeusDev")
        client_id = os.getenv("KC_CLIENT_ID", "maxi-business-ai")
        redirect_uri = os.getenv("KC_REDIRECT_URI", "https://orbit-dashboard-ewov.onrender.com/callback")
        
        url = f"{kc_url.rstrip('/')}/realms/{realm}/protocol/openid-connect/auth"
        params = f"?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=openid%20email%20profile"
        return rx.redirect(url + params)
