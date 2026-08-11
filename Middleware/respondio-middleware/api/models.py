"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import re

def determine_request_category(user_text: str, mcp_response: str) -> str:
    """Clasifica una consulta en: handoff, script, rule, mcp"""
    user_lower = (user_text or "").lower()
    resp_lower = (mcp_response or "").lower()
    
    # 1. Handoff (Derivación)
    if "[transfer:" in resp_lower:
        return "handoff"
        
    # 2. Scripts (Compliance/Scripts como SC.xxx o A2-A6)
    script_pattern = r"(sc\.\d+|cu\.\w+|a[2-6]_)"
    if re.search(script_pattern, user_lower) or re.search(script_pattern, resp_lower):
        return "script"
    
    dispute_keywords = ["disputa", "reembolso", "reclamo", "dispute", "refund", "claim", "re-embolso"]
    privacy_keywords = ["privacidad", "datos", "borrar", "privacy", "data", "delete"]
    if any(kw in user_lower for kw in dispute_keywords) or any(kw in user_lower for kw in privacy_keywords):
        return "script"
        
    # 3. Rules (Reglas de negocio)
    rule_pattern = r"rne\.\d+"
    if re.search(rule_pattern, user_lower) or re.search(rule_pattern, resp_lower):
        return "rule"
        
    # 4. Default: Standard MCP query
    return "mcp"


class ResponseStatus(str, Enum):
    """Status de la respuesta"""
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


class UserRole(str, Enum):
    """Roles de usuario para el dashboard"""
    ADMIN = "admin"
    SUPERVISOR = "supervisor"


class MediaItem(BaseModel):
    """Objeto para manejar archivos multimedia (Base64 o URL)"""
    mime_type: str = Field(..., description="MIME type del archivo (e.g. image/png, audio/mpeg)")
    data: Optional[str] = Field(None, description="Contenido en formato Base64")
    url: Optional[str] = Field(None, description="URL directa del archivo (Respond.io compatible)")
    file_name: Optional[str] = Field(None, description="Nombre original del archivo")


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
    user_text: str = Field(..., min_length=1, description="Texto del usuario")
    media: Optional[List[MediaItem]] = Field(default_factory=list, description="Archivos multimedia adjuntos")
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
    derivacion: Optional[str] = Field("NA", description="Departamento al que se deriva")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "reply_text": "¡Hola! ¿En qué puedo ayudarte hoy?",
                "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                "latency_ms": 1234,
                "derivacion": "NA"
            }
        }


# ============================================================
# Request hacia MCP
# ============================================================

class MCPRequest(BaseModel):
    """Request hacia el MCP"""
    query: str = Field(..., description="Query del usuario")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contexto adicional")
    media: Optional[List[MediaItem]] = Field(default_factory=list, description="Multimedia para procesar")

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
    confidence: Optional[float] = Field(0.95, description="Confianza de la respuesta")

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
    category: Optional[str] = "mcp"

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
    emergency_mode: bool = Field(default=False, description="Usa Gemini directo si el MCP está offline")
    # Keycloak Auth (for Service Account)
    use_keycloak: bool = Field(default=False, description="Usar Keycloak para autenticación")
    kc_server_url: Optional[str] = Field(None, description="Keycloak Server URL")
    kc_realm: Optional[str] = Field(None, description="Keycloak Realm")
    kc_client_id: Optional[str] = Field(None, description="Keycloak Client ID")
    kc_client_secret: Optional[str] = Field(None, description="Keycloak Client Secret")


class AgentConfig(BaseModel):
    """Configuración de un agente dinámico"""
    name: str = Field(..., description="Nombre único del agente")
    system_prompt: str = Field(..., description="Instrucciones para el LLM")
    readonly: bool = Field(default=False, description="Modo solo lectura (bloquea escrituras)")
    mcp_url: Optional[str] = Field(None, description="URL del MCP específico para este agente")
    is_orchestrator: bool = Field(default=False, description="Si es un agente orquestador/clasificador")
    specific_rules: Dict[str, Any] = Field(default_factory=dict, description="Reglas específicas estructuradas en JSON")
    knowledge_sources: List[str] = Field(default_factory=list, description="Fuentes de conocimiento (IDs de documentos/RAG)")
    web_search_enabled: bool = Field(default=False, description="Activa la capacidad de búsqueda en internet")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "asistente_ventas",
                "system_prompt": "Eres un asistente de ventas profesional...",
                "readonly": False,
                "mcp_url": "http://localhost:8080/query",
                "is_orchestrator": False,
                "specific_rules": {
                    "do": ["Ser amable", "Usar emojis"],
                    "dont": ["Mencionar precios"],
                    "internet_policy": "solo_si_necesario"
                },
                "knowledge_sources": ["doc_123", "sheet_456"],
                "web_search_enabled": True
            }
        }


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


class GoogleChatAlertConfig(BaseModel):
    """Configuración de alertas por Google Chat"""
    enabled: bool = Field(default=False, description="Habilitar alertas por Google Chat")
    sa_json_b64: str = Field(default="", description="Service Account JSON en Base64")
    default_space_id: str = Field(default="", description="ID del espacio por defecto (spaces/XXXX)")
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


class GoogleChatNotificationRequest(BaseModel):
    """Request for Google Chat notification"""
    message: str = Field(..., description="El mensaje a enviar a Google Chat")
    level: str = Field(default="INFO", description="Nivel del mensaje (INFO, ERROR, WARNING, SUCCESS)")
    destino: Optional[str] = Field(None, description="Destino mapeado (alertas, soporte, ventas)")
    space_id: Optional[str] = Field(None, description="ID del espacio (spaces/XXXX) para envío directo")
    media_url: Optional[str] = Field(None, description="URL de la imagen/archivo adjunto a incluir")
    contact_id: Optional[str] = Field(None, description="ID del contacto de Respond.io para emparejar caché")


class StatusCheckRequest(BaseModel):
    """Request structure for status routing check"""
    contact_id: str = Field(..., description="ID del contacto en Respond.io")
    user_text: str = Field(..., description="Mensaje del usuario")
    contact_name: Optional[str] = Field(None, description="Nombre del contacto")
    contact_phone: Optional[str] = Field(None, description="Teléfono del contacto")
    nombre_remitente: Optional[str] = Field(None, description="Nombre del remitente ingresado")
    nombre_beneficiario: Optional[str] = Field(None, description="Nombre del beneficiario ingresado")
    codigo_envio: Optional[str] = Field(None, description="Código de envío si ya está extraído")
    perfil: Optional[str] = Field(default="CLIENTE", description="Perfil del usuario (CLIENTE, BENEFICIARIO, AGENTE)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata adicional")


class StatusCheckResponse(BaseModel):
    """Response structure for status routing check"""
    status: str = Field(..., description="Estatus del procesamiento ('success' o 'error')")
    reply_text: str = Field(..., description="Mensaje de respuesta para el usuario")
    derivacion: str = Field(..., description="Departamento al que se deriva el contacto")
    validation_success: bool = Field(..., description="Si el código de envío y los nombres fueron validados")
    transaction_status: Optional[str] = Field(None, description="Estatus original de la transacción en la base de datos")
    client_profile: Optional[str] = Field(None, description="Perfil final determinado para el usuario")


class BillCheckRequest(BaseModel):
    """Request structure for bill check"""
    contact_id: str = Field(..., description="ID del contacto en Respond.io")
    user_text: str = Field(..., description="Mensaje del usuario")
    contact_name: Optional[str] = Field(None, description="Nombre del contacto")
    tracking_number: Optional[str] = Field(None, description="Tracking number del bill payment")
    biller: Optional[str] = Field(None, description="Nombre del biller")
    nombre_completo_customer: Optional[str] = Field(None, description="Nombre completo del customer")
    perfil: Optional[str] = Field(default="CLIENTE", description="Perfil del usuario (CLIENTE, BENEFICIARIO, AGENTE)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata adicional")


class BillCheckResponse(BaseModel):
    """Response structure for bill check"""
    status: str = Field(..., description="Estatus del procesamiento ('success' o 'error')")
    reply_text: str = Field(..., description="Mensaje de respuesta para el usuario")
    derivacion: str = Field(..., description="Departamento al que se deriva el contacto")
    validation_success: bool = Field(..., description="Si la validación fue exitosa")
    transaction_status: Optional[str] = Field(None, description="Estatus original de la transacción en la base de datos")
    client_profile: Optional[str] = Field(None, description="Perfil final determinado para el usuario")


class CSATLogRequest(BaseModel):
    """Request structure for CSAT logging"""
    contact_id: str = Field(..., description="ID del contacto en Respond.io")
    contact_name: str = Field(..., description="Nombre del contacto")
    rating: int = Field(..., description="Calificación de la encuesta (1 al 5)")
    comment: Optional[str] = Field(None, description="Comentario o feedback del cliente")
    assigned_agent: Optional[str] = Field(None, description="Nombre del agente previo que atendió")


class CSATLogResponse(BaseModel):
    """Response structure for CSAT logging"""
    status: str = Field(..., description="Estado de la operación ('success' o 'error')")
    message: str = Field(..., description="Mensaje explicativo")


class TopupCheckRequest(BaseModel):
    """Request structure for mobile top-up check"""
    contact_id: str = Field(..., description="ID del contacto en Respond.io")
    user_text: str = Field(..., description="Mensaje del usuario")
    contact_name: Optional[str] = Field(None, description="Nombre del contacto")
    transaction_id: Optional[str] = Field(None, description="ID de transacción / Folio de recarga")
    customer_number: Optional[str] = Field(None, description="Número telefónico del cliente")
    cellular_number: Optional[str] = Field(None, description="Número telefónico destino de recarga")
    perfil: Optional[str] = Field(default="CLIENTE", description="Perfil del usuario (CLIENTE, BENEFICIARIO, AGENTE)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata adicional")


class TopupCheckResponse(BaseModel):
    """Response structure for mobile top-up check"""
    status: str = Field(..., description="Estatus del procesamiento ('success' o 'error')")
    reply_text: str = Field(..., description="Mensaje de respuesta para el usuario")
    derivacion: str = Field(..., description="Departamento al que se deriva el contacto")
    validation_success: bool = Field(..., description="Si la validación fue exitosa")
    transaction_status: Optional[str] = Field(None, description="Estatus original de la transacción en la base de datos")
    client_profile: Optional[str] = Field(None, description="Perfil final determinado para el usuario")


class AgentInteractRequest(BaseModel):
    """Request structure for the unified cascade agent assistant"""
    agent_name: str = Field(..., description="Nombre del agente en cascada (ej. Max, VerificadorEstatus)")
    contact_id: str = Field(..., description="ID del contacto en Respond.io")
    conversation_id: Optional[str] = Field(None, description="ID de la conversación en Respond.io")
    user_text: str = Field(..., description="Mensaje del usuario")
    media_url: Optional[str] = Field(None, description="URL de imagen u otro archivo multimedia adjunto")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata adicional")


class AgentInteractResponse(BaseModel):
    """Response structure for the unified cascade agent assistant"""
    status: str = Field(..., description="Estado de la respuesta ('success' o 'error')")
    reply_text: str = Field(..., description="Texto final para responder verbatim al usuario")
    derivacion: str = Field(..., description="Nombre de agente o equipo al cual derivar, o 'NA'")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata o variables adicionales del estado")


# ============================================================
# Decision Logging & QA Session Reset Models
# ============================================================

class DecisionLogEntry(BaseModel):
    """Entrada en el registro de toma de decisiones por conversación (Orbit FSM)"""
    trace_id: str = Field(..., description="Folio único de trazabilidad de la decisión")
    contact_id: str = Field(..., description="ID del contacto o teléfono en Respond.io")
    case_id: Optional[str] = Field(None, description="ID del caso/sesión activa")
    active_agent: Optional[str] = Field("Max", description="Nombre del agente en cascada activo (ej. VerificadorEstatus)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora de la decisión")
    profile: Optional[str] = Field("CLIENTE", description="Perfil determinado (CLIENTE, BENEFICIARIO, AGENTE)")
    user_input: Optional[str] = Field(None, description="Mensaje o comando enviado por el usuario")
    ocr_extracted: Optional[Dict[str, Any]] = Field(None, description="Campos extraídos por visión/OCR si aplica")
    winning_rule_id: Optional[str] = Field(None, description="ID de la regla de negocio ganadora (ej. RNE.26)")
    script_code: Optional[str] = Field(None, description="Código del script asignado (ej. SC.019)")
    script_text: Optional[str] = Field(None, description="Texto literal devuelto para comunicar al usuario")
    language_code: Optional[str] = Field("es", description="Idioma del script ('es' o 'en')")
    current_state: Optional[str] = Field(None, description="Estado FSM inicial del turno")
    next_state: Optional[str] = Field(None, description="Estado FSM siguiente")
    next_action: Optional[str] = Field("NONE", description="Acción técnica siguiente (OFFER_ADDITIONAL_HELP, ASSIGN_TO_TEAM, etc.)")
    destination_team: Optional[str] = Field(None, description="Equipo/Agente de destino en caso de handoff")
    virtual_queue: Optional[str] = Field("Cola B", description="Cola virtual de asignación: 'Cola A' (Alta Prioridad - Riesgo/Fraude) o 'Cola B' (Prioridad Estándar)")
    csat_eligible: Optional[bool] = Field(False, description="Si la interacción califica para encuesta CSAT")
    close_allowed: Optional[bool] = Field(False, description="Si se permite el cierre técnico de la conversación")
    audit_meta: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata técnica (versiones, flags de frescura, etc.)")


class ResetSessionRequest(BaseModel):
    """Request para limpiar la sesión en Redis para QA o usuario"""
    contact_id: str = Field(..., description="ID de contacto o teléfono a resetear")
    reason: Optional[str] = Field("QA Manual Reset", description="Motivo del reset")


class ResetSessionResponse(BaseModel):
    """Response del reset de sesión"""
    status: str = Field(..., description="Estado del reset ('success' o 'error')")
    contact_id: str = Field(..., description="ID de contacto reseteado")
    cleared_keys: List[str] = Field(default_factory=list, description="Lista de claves de Redis eliminadas")
    message: str = Field(..., description="Mensaje informativo")





