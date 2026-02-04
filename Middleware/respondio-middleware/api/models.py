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
    gemini_api_key: Optional[str] = Field(None, description="Gemini API Key")


class CacheConfig(BaseModel):
    """Configuración del cache"""
    enabled: bool = Field(default=True, description="Cache habilitado")
    ttl: int = Field(default=300, description="TTL en segundos")
    max_size: int = Field(default=1000, description="Tamaño máximo del cache")


class SecurityConfig(BaseModel):
    """Configuración de seguridad"""
    webhook_secret: str = Field(..., description="Secret para validar webhooks")
    rate_limit: int = Field(default=100, description="Rate limit (req/min)")


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
