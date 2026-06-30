"""
Configuration management using environment variables and Redis.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_VERSION: str = "1.0.0"
    
    # MCP Settings
    MCP_URL: str = "http://localhost:8080/query"
    MCP_TIMEOUT: int = 5
    MCP_MAX_RETRIES: int = 3
    MCP_RETRY_DELAY: int = 1
    MCP_TOKEN: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # Keycloak Settings
    KC_SERVER_URL: Optional[str] = None
    KC_REALM: Optional[str] = None
    KC_CLIENT_ID: Optional[str] = None
    KC_CLIENT_SECRET: Optional[str] = None
    KC_USE_AUTH: bool = False
    
    # Security
    WEBHOOK_SECRET: str = "change-me-in-production"
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Google Sheets Integration
    GOOGLE_SHEET_ID_REGLAS: str = "1eFm3L_ALVr78wTDBB2bsg7Wq6DT9ZoGzIX9tKLN9nGw"
    GOOGLE_SHEET_ID_SCRIPTS: str = "18VE3tdVt4E-eNrf0dD4zlk1aLV2nfv9_ncdUvLPaNic"
    GOOGLE_SHEET_ID_ESTATUS: Optional[str] = "14BdjBuXPXPkjXMKS-955fA6bNw5qRMv5IWCNhMZGIXc"
    GOOGLE_SHEET_ID_BILL_ESTATUS: Optional[str] = "16fB_MGtha0NUtp5mge7UwvHcWo1NYVnOGVv6Yntv9xo"
    GOOGLE_SHEET_ID_TOPUP_ESTATUS: Optional[str] = "1E3pNthg7myh7tgjEnb_TIxCnTLFi_gzWlcxk2LOdNCs"
    
    
    # Supabase (PostgreSQL)
    SUPABASE_URI: Optional[str] = "postgresql://postgres:PruebaBoot2025.*@db.tzlomvpugmrpdfatscxe.supabase.co:5432/postgres"
    
    # Redis
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Cache
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 300
    CACHE_MAX_SIZE: int = 1000
    
    # Circuit Breaker
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_FAILURE_THRESHOLD: int = 5
    CIRCUIT_TIMEOUT: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    # Dashboard
    DASHBOARD_USERNAME: str = "admin"
    DASHBOARD_PASSWORD: str = "change-me-in-production"
    
    # SMTP / Alerts
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    ALERT_EMAIL_RECIPIENT: Optional[str] = None
    
    # Google Chat Settings
    GOOGLE_CHATS_SA_BASE64: Optional[str] = None
    GOOGLE_CHATS_DEFAULT_SPACE: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Singleton instance
settings = get_settings()
