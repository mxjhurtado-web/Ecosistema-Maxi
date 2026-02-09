"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    """Status de la respuesta"""
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


class UserRole(str, Enum):
    """Roles de usuario para el dashboard"""
    ADMIN = "admin"
    SUPERVISOR = "supervisor"


class AuditAction(str, Enum):
    """Acciones auditables en el dashboard"""
    LOGIN = "login"
    CONFIG_CHANGE = "config_change"
    USER_MANAGEMENT = "user_management"
    EXPORT_DATA = "export_data"
    CACHE_CLEAR = "cache_clear"
    CIRCUIT_RESET = "circuit_reset"
    SYSTEM_MAINTENANCE = "system_maintenance"


class DashboardUser(BaseModel):
    """Usuario del dashboard"""
    username: str
    password: str # Encriptado en producción, texto plano para MVP/Redis simple
    role: UserRole
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLogEntry(BaseModel):
    """Entrada en el registro de auditoría"""
    username: str
    role: UserRole
    action: AuditAction
    details: str
    ip_address: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Request desde Respond.io
# ============================================================

class RespondioRequest(BaseModel):
    """Request desde Respond.io"""
    conversation_id: str = Field(..., description="ID de la conversación")
    contact_id: str = Field(..., description="ID del contacto")
    channel: str = Field(..., description="Canal (whatsapp, telegram, etc)")
    user_text: str = Field(..., description="Texto del usuario")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata adicional")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_abc123",
                "contact_id": "contact_xyz789",
                "channel": "whatsapp",
                "user_text": "Hola, necesito ayuda",
                "metadata": {
                    "language": "es",
                    "country": "MX"
                }
            }
        }


# ============================================================
# Response hacia Respond.io
# ============================================================

class RespondioResponse(BaseModel):
    """Response hacia Respond.io"""
    status: ResponseStatus = Field(..., description="Estado de la respuesta")
    reply_text: str = Field(..., description="Texto de respuesta")
    trace_id: str = Field(..., description="ID de trazabilidad")
    latency_ms: int = Field(..., description="Latencia en milisegundos")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "reply_text": "¡Hola! ¿En qué puedo ayudarte hoy?",
                "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                "latency_ms": 1234
            }
        }


# ============================================================
# Request hacia MCP
# ============================================================

class MCPRequest(BaseModel):
    """Request hacia el MCP"""
    query: str = Field(..., description="Query del usuario")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contexto adicional")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Hola, necesito ayuda",
                "context": {
                    "conversation_id": "conv_abc123",
                    "channel": "whatsapp"
                }
            }
        }


# ============================================================
# Response desde MCP
# ============================================================

class MCPResponse(BaseModel):
    """Response desde el MCP"""
    response: str = Field(..., description="Respuesta del MCP")
    confidence: Optional[float] = Field(None, description="Confianza de la respuesta")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "¡Hola! ¿En qué puedo ayudarte hoy?",
                "confidence": 0.95
            }
        }


# ============================================================
# Telemetría
# ============================================================

class RequestLog(BaseModel):
    """Log de un request procesado"""
    trace_id: str
    timestamp: datetime
    conversation_id: str
    contact_id: str
    channel: str
    user_text: str
    mcp_response: Optional[str] = None
    status: ResponseStatus
    latency_ms: int
    mcp_latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2026-02-04T14:30:00Z",
                "conversation_id": "conv_abc123",
                "contact_id": "contact_xyz789",
                "channel": "whatsapp",
                "user_text": "Hola",
                "mcp_response": "¡Hola! ¿En qué puedo ayudarte?",
                "status": "ok",
                "latency_ms": 1234,
                "mcp_latency_ms": 890,
                "error_message": None,
                "retry_count": 0
            }
        }


# ============================================================
# Configuración
# ============================================================

class MCPConfig(BaseModel):
    """Configuración del MCP"""
    url: str = Field(default="http://localhost:8080/query", description="URL del MCP")
    timeout: int = Field(default=5, description="Timeout en segundos")
    max_retries: int = Field(default=3, description="Número máximo de reintentos")
    retry_delay: int = Field(default=1, description="Delay entre reintentos (segundos)")
    mcp_token: Optional[str] = Field(None, description="Token de autenticación manual")
    gemini_api_key: Optional[str] = Field(None, description="Gemini API Key")
    # Keycloak Auth (for Service Account)
    use_keycloak: bool = Field(default=False, description="Usar Keycloak para autenticación")
    kc_server_url: Optional[str] = Field(None, description="Keycloak Server URL")
    kc_realm: Optional[str] = Field(None, description="Keycloak Realm")
    kc_client_id: Optional[str] = Field(None, description="Keycloak Client ID")
    kc_client_secret: Optional[str] = Field(None, description="Keycloak Client Secret")


class CacheConfig(BaseModel):
    """Configuración del cache"""
    enabled: bool = Field(default=True, description="Cache habilitado")
    ttl: int = Field(default=300, description="TTL en segundos")
    max_size: int = Field(default=1000, description="Tamaño máximo del cache")


class SecurityConfig(BaseModel):
    """Configuración de seguridad"""
    webhook_secret: str = Field(..., description="Secret para validar webhooks")
    rate_limit: int = Field(default=100, description="Rate limit (req/min)")


class EmailAlertConfig(BaseModel):
    """Configuración de alertas por correo"""
    enabled: bool = Field(default=False, description="Habilitar alertas por correo")
    smtp_server: str = Field(default="smtp.gmail.com", description="Servidor SMTP")
    smtp_port: int = Field(default=587, description="Puerto SMTP")
    smtp_user: str = Field(default="", description="Usuario SMTP")
    smtp_password: str = Field(default="", description="Contraseña SMTP")
    recipient_email: str = Field(default="", description="Email destinatario de alertas")
    alert_on_mcp_error: bool = Field(default=True, description="Alertar en error de MCP")
    alert_on_circuit_breaker: bool = Field(default=True, description="Alertar en apertura de Circuit Breaker")


# ============================================================
# Health Check
# ============================================================

class HealthResponse(BaseModel):
    """Response del health check"""
    status: str = Field(..., description="Estado del servicio")
    timestamp: datetime = Field(..., description="Timestamp del check")
    version: str = Field(default="1.0.0", description="Versión del servicio")
    mcp_status: Optional[str] = Field(None, description="Estado del MCP")
    redis_status: Optional[str] = Field(None, description="Estado de Redis")
