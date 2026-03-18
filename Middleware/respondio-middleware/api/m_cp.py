"""
Servidor MCP para Maxi - Agente de Estatus de Envíos
Usa Supabase REST API (HTTPS/443) para compatibilidad con Render free tier.
Puerto 5432 (psycopg2) está bloqueado en Render free - usamos httpx en su lugar.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import logging
import re
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Maxi-Estatus-MCP", version="2.0.0")

# Supabase REST API
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tzlomvpugmrpdfatscxe.supabase.co")
SUPABASE_ANON_KEY = os.getenv(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6bG9tdnB1Z21ycGRmYXRzY3hlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3NjI3MjcsImV4cCI6MjA4OTMzODcyN30.aH-p2YbLa8LPlnMVsZMlELsxFWwSSLZMA_LPpRz5DU8"
)

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json"
}


# ── Modelos ───────────────────────────────────────────────────────────────────

class MCPRequest(BaseModel):
    query: str
    context: Optional[dict] = None
    media: Optional[list] = []


class MCPResponse(BaseModel):
    response: str
    status: str = "ok"
    error_detail: Optional[str] = None


# ── Lógica de Negocio ─────────────────────────────────────────────────────────

async def consultar_supabase(codigo: str, telefono: Optional[str] = None):
    """Consulta Supabase via REST API (HTTPS). Evita el bloqueo de puerto 5432."""
    codigo_clean = codigo.strip().upper()
    logger.info(f"🔍 Consultando REST API para código: '{codigo_clean}'")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{SUPABASE_URL}/rest/v1/Base_completa"
            params = {
                "Codigo_de_envio": f"ilike.{codigo_clean}",
                "select": "*",
                "limit": "1"
            }
            response = await client.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            data = response.json()

        if not data:
            logger.warning(f"❌ Código no encontrado: {codigo_clean}")
            return {"error": "not_found"}

        resultado = data[0]

        # Verificación opcional de teléfono
        if telefono:
            val_tel = re.sub(r'\D', '', str(resultado.get("Numero_telefonico", "")))
            tel_clean = re.sub(r'\D', '', telefono)
            if tel_clean and val_tel and tel_clean not in val_tel and val_tel not in tel_clean:
                logger.warning(f"⚠️ Teléfono no coincide para {codigo_clean}")
                return {"error": "auth_failed"}

        logger.info(f"✅ Registro encontrado: {codigo_clean}")
        return {"error": None, "data": resultado}

    except httpx.HTTPStatusError as e:
        msg = f"Supabase HTTP {e.response.status_code}: {e.response.text[:200]}"
        logger.error(msg)
        return {"error": "connection_error", "detail": msg}
    except Exception as e:
        msg = f"Error REST Supabase: {str(e)}"
        logger.error(msg)
        return {"error": "connection_error", "detail": msg}


def extraer_codigo(texto: str) -> Optional[str]:
    """Extrae código de envío alfanumérico del texto."""
    patrones = [
        r'\b[A-Z]{2}\d{9,}\b',   # CE17016886149
        r'\b[A-Z0-9]{10,}\b',    # Genérico largo
    ]
    for patron in patrones:
        m = re.search(patron, texto.upper())
        if m:
            return m.group()
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "online", "service": "Maxi-Estatus-MCP", "version": "2.0.0", "mode": "REST API"}


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    """Health check que verifica la conexión REST a Supabase."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            url = f"{SUPABASE_URL}/rest/v1/Base_completa"
            r = await client.get(url, headers=HEADERS, params={"select": "Codigo_de_envio", "limit": "1"})
            r.raise_for_status()
        return {"status": "healthy", "db": "Supabase REST OK"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@app.post("/query", response_model=MCPResponse)
async def query(request: MCPRequest):
    """Recibe consulta del usuario, extrae el código y consulta Supabase."""
    logger.info(f"📥 Query: {request.query[:100]}")

    codigo = extraer_codigo(request.query)
    ctx = request.context or {}
    phone = ctx.get("phone") or ctx.get("contact_id")

    if not codigo:
        return MCPResponse(
            response="Por favor proporciona tu código de envío (ejemplo: CE17016886149).",
            status="ok"
        )

    res = await consultar_supabase(codigo, telefono=phone)

    if res["error"] == "connection_error":
        return MCPResponse(
            response="⚠️ Tengo problemas temporales para consultar el estatus. Intenta de nuevo en un momento.",
            status="error",
            error_detail=res.get("detail")
        )

    if res["error"] == "auth_failed":
        return MCPResponse(
            response="❌ El teléfono no coincide con nuestros registros. Por seguridad no puedo mostrar el estatus.",
            status="ok"
        )

    if res["error"] == "not_found":
        return MCPResponse(
            response=f"❌ No encontré ningún envío con el código **{codigo}**. Verifica tu recibo.",
            status="ok"
        )

    # Éxito
    fila = res["data"]
    estatus = str(fila.get("status", "PENDIENTE")).upper()
    mensaje = fila.get("message_to_user") or "Tu envío está siendo procesado."
    cliente = fila.get("Nombre_Cliente", "Cliente")

    return MCPResponse(
        response=(
            f"Hola {cliente}, aquí tienes el estatus de tu envío **{codigo}**:\n\n"
            f"📍 **ESTADO**: {estatus}\n"
            f"📝 **NOTA**: {mensaje}\n\n"
            "¿Hay algo más en lo que pueda ayudarte?"
        ),
        status="ok"
    )
