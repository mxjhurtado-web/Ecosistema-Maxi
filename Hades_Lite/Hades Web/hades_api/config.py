"""
Configuración de la aplicación Hades API.

Variables de entorno y configuración general.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # App
    APP_NAME: str = "Hades API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Keycloak
    KEYCLOAK_SERVER_URL: str
    KEYCLOAK_REALM: str
    KEYCLOAK_CLIENT_ID: str
    KEYCLOAK_CLIENT_SECRET: str
    
    # Gemini (opcional - se puede configurar desde UI)
    GEMINI_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Google Drive (opcional en .env, se puede usar st.secrets)
    GOOGLE_SA_JSON_B64: Optional[str] = None
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = "1eexrVXQYRZLk9hnJwLVYJp5PkYnjx2bt"
    
    # Async Processing (Toggle)
    ASYNC_PROCESSING: bool = False  # True = Celery, False = Sync
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
