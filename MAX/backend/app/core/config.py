"""
Core configuration settings for MAX application.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "MAX"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # WhatsApp Cloud API
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v18.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = ""
    
    # Chat App
    CHAT_APP_API_URL: str = ""
    CHAT_APP_API_KEY: str = ""
    
    # External Integrations
    TICKETING_API_URL: str = ""
    TICKETING_API_KEY: str = ""
    
    TRANSACTION_API_URL: str = ""
    TRANSACTION_CLIENT_ID: str = ""
    TRANSACTION_CLIENT_SECRET: str = ""
    
    # Storage
    STORAGE_TYPE: str = "cloudflare_r2"
    STORAGE_BUCKET: str = "max-media"
    STORAGE_ACCOUNT_ID: str = ""
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Rate Limiting
    RATE_LIMIT_MESSAGES_PER_MINUTE: int = 20
    RATE_LIMIT_CONVERSATIONS_PER_HOUR: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
