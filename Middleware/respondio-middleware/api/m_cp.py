"""
Servidor MCP para Maxi - Agente de Estatus de Envíos
Expone un endpoint /query compatible con el Orbit mcp_client.py
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
import re
from dotenv import load_dotenv

# Cargar variables de entorno local si existen
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Maxi-Estatus-MCP", version="1.1.0")

# Configuración Supabase via variable de entorno
DB_URI = os.getenv(
    "SUPABASE_URI",
    "postgresql://postgres:PruebaBoot2025.*@db.tzlomvpugmrpdfatscxe.supabase.co:5432/postgres"
)


# ── Modelos Pydantic ──────────────────────────────────────────────────────────

class MCPRequest(BaseModel):
    query: str
    context: Optional[dict] = None
    media: Optional[list] = []


class MCPResponse(BaseModel):
    response: str
    status: str = "ok"
    error_detail: Optional[str] = None


# ── Utilidades ────────────────────────────────────────────────────────────────

def consultar_supabase(codigo: str, telefono: Optional[str] = None, nombre: Optional[str] = None):
    """
    Busca un envío por Codigo_de_envio en Supabase y opcionalmente verifica identidad.
    """
    conn = None
    try:
        conn = psycopg2.connect(DB_URI, connect_timeout=10)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        codigo_clean = codigo.strip().upper()
        logger.info(f"🔍 Consultando DB para código: '{codigo_clean}'")
        
        # Búsqueda por código (case insensitive y sin espacios)
        query = 'SELECT * FROM "Base_completa" WHERE TRIM(UPPER("Codigo_de_envio")) = %s'
        cursor.execute(query, (codigo_clean,))
        resultado = cursor.fetchone()
        
        if not resultado:
            logger.warning(f"❌ Código no encontrado: {codigo_clean}")
            return {"error": "not_found", "detail": f"Código {codigo_clean} no existe en la tabla Base_completa."}

        # Verificación de Identidad (si se proporcionan datos en el contexto)
        if telefono:
            val_tel = str(resultado.get("Numero_telefonico", "")).strip()
            # Limpieza básica para comparar números
            tel_clean = re.sub(r'\D', '', telefono)
            val_tel_clean = re.sub(r'\D', '', val_tel)
            
            if tel_clean and val_tel_clean and tel_clean not in val_tel_clean and val_tel_clean not in tel_clean:
                logger.warning(f"⚠️ Validación de teléfono fallida para {codigo_clean}")
                return {"error": "auth_failed", "detail": "El teléfono no coincide con el registro."}

        if nombre:
            val_nom = str(resultado.get("Nombre_Cliente", "")).strip().upper()
            nom_query = nombre.strip().upper()
            if nom_query not in val_nom and val_nom not in nom_query:
                logger.warning(f"⚠️ Validación de nombre fallida para {codigo_clean}")
                # No bloqueamos por nombre parcial, pero registramos
                pass

        logger.info(f"✅ Registro validado con éxito: {codigo_clean}")
        cursor.close()
        return {"error": None, "data": resultado}

    except Exception as e:
        error_msg = f"Error de conexión Supabase: {str(e)}"
        logger.error(error_msg)
        return {"error": "connection_error", "detail": error_msg}
    finally:
        if conn:
            conn.close()


def extraer_codigo(texto: str) -> Optional[str]:
    """Extrae códigos alfanuméricos como CE17016886149."""
    # Prioridad a formatos conocidos de Maxi
    patrones = [
        r'\b[A-Z]{2}\d{9,}\b',  # Ej: CE17016886149
        r'\b[A-Z0-9]{10,}\b',   # Genérico largo
    ]
    for patron in patrones:
        match = re.search(patron, texto.upper())
        if match:
            return match.group()
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "online", "service": "Maxi-Estatus-MCP", "db_configured": bool(DB_URI)}


@app.get("/health")
async def health():
    # Intento de conexión rápida para healthcheck real
    try:
        conn = psycopg2.connect(DB_URI, connect_timeout=3)
        conn.close()
        return {"status": "healthy", "db": "connected"}
    except Exception as e:
        return {"status": "degraded", "db_error": str(e)}


@app.post("/query", response_model=MCPResponse)
async def query(request: MCPRequest):
    """
    Recibe consulta, extrae código y valida contra Supabase.
    Soporta contexto con phone/name para mayor seguridad.
    """
    logger.info(f"📥 Query: {request.query[:100]}")

    # 1. Extraer código
    codigo = extraer_codigo(request.query)
    
    # 2. Obtener datos extra del contexto (Respond.io pass data)
    ctx = request.context or {}
    phone = ctx.get("phone") or ctx.get("contact_id") # A veces el contact_id es el phone
    name = ctx.get("name") or ctx.get("first_name")

    if not codigo:
        return MCPResponse(
            response="Por favor, proporciona tu código de envío de 11 o más caracteres (ejemplo: CE17016886149).",
            status="ok"
        )

    # 3. Consultar DB
    res = consultar_supabase(codigo, telefono=phone, nombre=name)

    # 4. Procesar Resultado
    if res["error"] == "connection_error":
        return MCPResponse(
            response="⚠️ Lo siento, tengo problemas temporales para conectar con la base de datos de estatus.",
            status="error",
            error_detail=res["detail"]
        )
    
    if res["error"] == "auth_failed":
        return MCPResponse(
            response="❌ La clave de envío es válida, pero el número de teléfono no coincide con nuestros registros. Por seguridad, no puedo mostrar el estatus.",
            status="ok"
        )

    if res["error"] == "not_found":
        return MCPResponse(
            response=f"❌ No encontré ningún envío con el código **{codigo}**. Por favor, verifica tu recibo.",
            status="ok",
            error_detail=res["detail"]
        )

    # 5. Éxito
    fila = res["data"]
    estatus = fila.get('status', 'PENDIENTE').upper()
    mensaje_personalizado = fila.get('message_to_user') or "Tu envío está siendo procesado."
    cliente = fila.get('Nombre_Cliente', 'Cliente')

    respuesta = (
        f"Hola {cliente}, aquí tienes el estatus de tu envío **{codigo}**:\n\n"
        f"📍 **ESTADO**: {estatus}\n"
        f"📝 **NOTA**: {mensaje_personalizado}\n\n"
        "¿Hay algo más en lo que pueda ayudarte?"
    )

    return MCPResponse(response=respuesta, status="ok")
