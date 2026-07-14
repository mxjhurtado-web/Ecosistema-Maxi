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

    @rx.var
    def is_super_admin(self) -> bool:
        return self.role == "super_admin"

    @rx.var
    def is_admin_or_higher(self) -> bool:
        return self.role in ["admin", "super_admin"]
