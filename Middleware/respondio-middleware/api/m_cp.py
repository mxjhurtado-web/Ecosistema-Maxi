"""
Servidor MCP para Maxi - Agente de Estatus de Envíos
Expone un endpoint /query compatible con el Orbit mcp_client.py
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Maxi-Estatus-MCP", version="1.0.0")

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


# ── Utilidades ────────────────────────────────────────────────────────────────

def consultar_supabase(codigo: str):
    """Busca un envío por Codigo_de_envio en Supabase."""
    conn = None
    try:
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = 'SELECT * FROM "Base_completa" WHERE "Codigo_de_envio" = %s'
        cursor.execute(query, (codigo.strip(),))
        resultado = cursor.fetchone()
        cursor.close()
        return resultado
    except Exception as e:
        logger.error(f"Error al conectar con Supabase: {e}")
        return None
    finally:
        if conn:
            conn.close()


def extraer_codigo(texto: str) -> Optional[str]:
    """
    Intenta extraer el código de envío del texto del usuario.
    Los códigos suelen ser alfanuméricos de 10+ caracteres.
    """
    import re
    # Busca patrones comunes: letras seguidas de números o viceversa (ej: CE17016886149)
    patrones = [
        r'\b[A-Z]{2}\d{9,}\b',        # CE17016886149
        r'\b[A-Z0-9]{8,}\b',           # Genérico alfanumérico
    ]
    for patron in patrones:
        match = re.search(patron, texto.upper())
        if match:
            return match.group()
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "online", "service": "Maxi-Estatus-MCP"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/query", response_model=MCPResponse)
async def query(request: MCPRequest):
    """
    Endpoint principal. Recibe la consulta del usuario,
    extrae el código de envío, consulta Supabase y devuelve el resultado.
    """
    logger.info(f"Query recibido: {request.query[:100]}")

    # 1. Extraer código de envío del mensaje
    codigo = extraer_codigo(request.query)

    if not codigo:
        return MCPResponse(
            response=(
                "No pude encontrar un código de envío en tu mensaje. "
                "Por favor proporciona el código de envío (ej: CE17016886149)."
            ),
            status="ok"
        )

    # 2. Consultar Supabase
    fila = consultar_supabase(codigo)

    # 3. Construir respuesta
    if fila:
        estatus = fila.get('status', 'No disponible')
        cliente = fila.get('Nombre_Cliente', 'N/A')
        mensaje = fila.get('message_to_user', 'Sin mensajes adicionales.')

        respuesta = (
            f"✅ Registro encontrado para el código **{codigo}**:\n"
            f"- **Cliente**: {cliente}\n"
            f"- **Estatus**: {estatus}\n"
            f"- **Nota**: {mensaje}"
        )
    else:
        respuesta = (
            f"❌ No se encontró el código de envío **{codigo}** en nuestra base de datos. "
            f"Por favor verifica que el código sea correcto."
        )

    return MCPResponse(response=respuesta, status="ok")
