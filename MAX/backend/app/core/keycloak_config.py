"""
Keycloak configuration for MAX.
Uses the same Keycloak instance as Maxibot.
"""
from pydantic_settings import BaseSettings


class KeycloakSettings(BaseSettings):
    """Keycloak configuration settings."""
    
    # Keycloak server
    KEYCLOAK_URL: str = "http://localhost:8081"
    KEYCLOAK_REALM: str = "maxibot"
    KEYCLOAK_CLIENT_ID: str = "maxibot-client"
    KEYCLOAK_CLIENT_SECRET: str = "maxibot-secret-123"
    
    # Endpoints (auto-generated)
    @property
    def auth_endpoint(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/auth"
    
    @property
    def token_endpoint(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/token"
    
    @property
    def userinfo_endpoint(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
    
    @property
    def logout_endpoint(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/logout"
    
    @property
    def jwks_uri(self) -> str:
        """JSON Web Key Set URI for token validation."""
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/certs"
    
    # Token validation
    KEYCLOAK_VERIFY_SIGNATURE: bool = True
    KEYCLOAK_VERIFY_AUD: bool = False  # Audience verification
    
    class Config:
        env_file = ".env"
        case_sensitive = True


keycloak_settings = KeycloakSettings()
