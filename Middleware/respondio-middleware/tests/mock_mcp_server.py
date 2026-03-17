"""
Mock MCP Server for Testing - Ecosistema-Maxi OFFICIAL Edition
Integrated with postgresql for full VT-Verifier-Generator flow.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import requests
import re
import uvicorn
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("maxi-bridge")

app = FastAPI(
    title="Maxi Ecosistema Bridge (VT/VER/GEN)",
    description="Bridge implementing OBBA rules and multi-agent flow",
    version="4.0.0"
)

# Configuration from environment
SUPABASE_URI = os.getenv("SUPABASE_URI")

class MCPRequest(BaseModel):
    """Request from middleware"""
    query: str
    context: Optional[dict] = None

class MCPResponse(BaseModel):
    """Response to middleware"""
    response: str
    confidence: float = 0.95

class MaxiDB:
    """Acceso a la base de datos oficial de Maxi en Supabase"""
    
    def __init__(self, uri: str):
        self.uri = uri
    
    def _get_connection(self):
        return psycopg2.connect(self.uri, cursor_factory=RealDictCursor)

    # --- AGENTE VT / STATUS ---
    def query_shipment(self, search_term: str) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Buscamos en Base_completa (o pre_envios si ya migramos)
                    sql = 'SELECT * FROM "Base_completa" WHERE folio::text ILIKE %s OR "Numero_telefonico" ILIKE %s LIMIT 5'
                    pattern = f"%{search_term}%"
                    cur.execute(sql, (pattern, pattern))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error query_shipment: {e}")
            return []

    # --- AGENTE VERIFICADOR ---
    def check_compliance(self, name: str) -> bool:
        """Simulación de Blacklist Compliance"""
        blacklist = ["persona non grata", "estafador", "bad customer"]
        return not any(b in name.lower() for b in blacklist)

    def get_agency_status(self, agency_code: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    sql = 'SELECT * FROM "Agencia_tarifa" WHERE agency_code = %s'
                    cur.execute(sql, (agency_code,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error get_agency_status: {e}")
            return None

    # --- AGENTE GENERADOR ---
    def register_pre_envio(self, data: Dict[str, Any]) -> str:
        """Genera folio MMDDAAAAXX e inserta en Base_completa"""
        try:
            # Generar Folio
            now = datetime.now()
            # Simplificado: usamos los últimos 2 segs para el XX
            folio = f"{now.strftime('%m%d%Y')}{now.strftime('%S')}"
            
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    sql = """
                        INSERT INTO "Base_completa" (folio, "Numero_telefonico", agency_code, status, message_to_user, updated_at)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                    """
                    cur.execute(sql, (
                        folio, 
                        data.get("phone", "Desconocido"), 
                        data.get("agency", "DEFAULT"), 
                        "PENDIENTE_PAGO",
                        "Pre-envío generado. Favor de liquidar en agencia."
                    ))
                    return folio
        except Exception as e:
            logger.error(f"Error register_pre_envio: {e}")
            return "ERROR"

# Inicialización
db = MaxiDB(SUPABASE_URI) if SUPABASE_URI else None

@app.post("/query", response_model=MCPResponse)
async def query(request: MCPRequest):
    query_text = request.query.lower()
    gemini_api_key = request.context.get("gemini_api_key") if request.context else None
    
    if not db:
        return MCPResponse(response="ERROR: Configura SUPABASE_URI en .env", confidence=0.0)

    # 1. REGLA OBBA (Impuesto Federal)
    if any(k in query_text for k in ["enviar", "monto", "cuanto es", "costo"]):
        match_money = re.search(r"\$\s*(\d+)", query_text)
        if match_money:
            amount = float(match_money.group(1))
            if amount >= 15.00:
                tax = amount * 0.01
                total = amount + tax
                return MCPResponse(
                    response=f"📢 **Divulgación OBBA (PETTE_VT):**\nConforme a la ley federal, se aplica un impuesto del 1% (US$ {tax:.2f}). Su total estimado a pagar es US$ {total:.2f}. ¿Desea continuar?"
                )

    # 2. VERIFICACIÓN DE ESTATUS
    match_folio = re.search(r"\b(\d{5,})\b", query_text)
    if match_folio or "estatus" in query_text:
        search = match_folio.group(1) if match_folio else query_text
        results = db.query_shipment(search)
        if results:
            r = results[0]
            return MCPResponse(response=f"🔍 **Estatus (PETTE_STATUS):**\nFolio: {r['folio']}\nEstado: **{r['status']}**\nNota: {r['message_to_user']}")

    # 3. GENERACIÓN (Simulada)
    if "confirmado" in query_text or "si deseo continuar" in query_text:
        # Aquí simularíamos el registro exitoso
        new_folio = db.register_pre_envio({"phone": "Pendiente", "agency": "TEST-01"})
        return MCPResponse(response=f"✅ **¡Éxito! (MAXI_GENERADOR):**\nTu folio es: **{new_folio}**. Preséntalo en tu agencia para pagar.")

    # 4. Gemini Fallback
    if gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            Eres PETTE_VT, el orquestador de Maxi. 
            Regla de ORO: Siempre informa sobre el impuesto OBBA (1%) si el envío es mayor a $15.
            Tablas disponibles: Base_completa, Agencia_tarifa, Cliente_Beneficiario.
            Query: "{request.query}"
            """
            response = model.generate_content(prompt)
            return MCPResponse(response=response.text, confidence=0.99)
        except Exception as e:
            logger.error(f"Gemini error: {e}")

    return MCPResponse(response="Recibido. ¿Podrías darme más detalles o el folio de tu envío?", confidence=0.5)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
