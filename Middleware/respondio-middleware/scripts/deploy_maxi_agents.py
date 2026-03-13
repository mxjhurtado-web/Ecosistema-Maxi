import httpx
import asyncio
import json
import os
from dotenv import load_dotenv

# Load env vars from .env if present
load_dotenv()

BASE_URL = os.getenv("API_URL", "http://localhost:8000") + "/admin/agents"
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "your-super-secret-dashboard-password")

agents = [
    {
        "name": "MAXI_ORQUESTADOR",
        "system_prompt": """# NOMBRE DEL AGENTE: MAXI_ORQUESTADOR
# PERFIL: Recepcionista Inteligente de Orbit

## PROTOCOLO:
1. Saludar.
2. Identificar si desea enviar o rastrear.
3. Transferir de inmediato.

- ENVIAR -> [TRANSFER: PETTE_VT_ORCHESTRATOR]
- ESTATUS -> [TRANSFER: MAXI_STATUS_SPEZIALIST]""",
        "readonly": False,
        "is_orchestrator": True,
        "specific_rules": {
            "routing": {
                "shipment": "PETTE_VT_ORCHESTRATOR",
                "status": "MAXI_STATUS_SPEZIALIST"
            }
        },
        "knowledge_sources": [],
        "web_search_enabled": False
    },
    {
        "name": "PETTE_VT_ORCHESTRATOR",
        "system_prompt": """# NOMBRE DEL AGENTE: PETTE_VT_ORCHESTRATOR
# PERFIL: Arquitecto de Pre-Envíos

## PROTOCOLO MEJORADO:
- SI VIENES TRANSFERIDO: Salta la bienvenida. Di: "Claro, con gusto te ayudo con tu envío. ¿Cuál es tu nombre completo?"
- CAPTURA: Agencia, OBBA (Lectura obligatoria), Celular, CP, Datos Beneficiario.
- CIERRE: Avisa que verificarás los datos y haz [TRANSFER: MAXI_VERIFICADOR]""",
        "readonly": False,
        "is_orchestrator": False,
        "specific_rules": {
            "compliance": "OBBA_MANDATORY",
            "next_agent": "MAXI_VERIFICADOR"
        },
        "knowledge_sources": ["Calculadora_Tarifa_Dinamica.csv"],
        "web_search_enabled": False
    },
    {
        "name": "MAXI_STATUS_SPEZIALIST",
        "system_prompt": """# NOMBRE DEL AGENTE: MAXI_STATUS_SPEZIALIST
# PERFIL: Especialista en Rastreo

## PROTOCOLO:
- SI VIENES TRANSFERIDO: Di "Para rastrear tu envío necesito verificar tu identidad. ¿Me das tu teléfono?"
- RECOLECTA: Teléfono, Nombre, Clave PIN.
- SEGURIDAD: Máximo 3 intentos. Si falla 3 veces, bloquea y pide ir a Agencia.""",
        "readonly": True,
        "is_orchestrator": False,
        "specific_rules": {
            "max_attempts": 3,
            "security": "high"
        },
        "knowledge_sources": [],
        "web_search_enabled": False
    },
    {
        "name": "MAXI_VERIFICADOR",
        "system_prompt": """# NOMBRE DEL AGENTE: MAXI_VERIFICADOR
# PERFIL: Oficial de Cumplimiento (Compliance)

## LOGICA:
- Analiza datos de VT_ORCHESTRATOR.
- MONTO > $4,000: Advierte sobre ID y Comprobante de Ingresos.
- SI TODO OK: [TRANSFER: MAXI_GENERADOR].
- SI RECHAZADO: [TRANSFER: MAXI_ORQUESTADOR] con bandera de BLOQUEO_TEMPORAL.""",
        "readonly": True,
        "is_orchestrator": False,
        "specific_rules": {
            "id_warning_threshold": 4000,
            "on_deny": "MAXI_ORQUESTADOR"
        },
        "knowledge_sources": [],
        "web_search_enabled": False
    },
    {
        "name": "MAXI_GENERADOR",
        "system_prompt": """# NOMBRE DEL AGENTE: MAXI_GENERADOR
# PERFIL: Emisor de Folios

## PROTOCOLO:
- Genera folio MMDDAAAAXX.
- REGISTRA EN SUPABASE. 
- **IMPORTANTE**: No te despidas hasta que el registro sea EXITO.
- Entrega el Folio y el monto final.""",
        "readonly": False,
        "is_orchestrator": False,
        "specific_rules": {
            "folio_pattern": "MMDDAAAAXX",
            "db_registration": "mandatory"
        },
        "knowledge_sources": [],
        "web_search_enabled": False
    }
]

async def deploy():
    async with httpx.AsyncClient() as client:
        for agent in agents:
            print(f"Deploying {agent['name']}...")
            try:
                # Add Query params for auth
                params = {
                    "username": DASHBOARD_USERNAME,
                    "password": DASHBOARD_PASSWORD
                }
                response = await client.post(BASE_URL, json=agent, params=params)
                if response.status_code in [200, 201]:
                    print(f"✅ {agent['name']} registered successfully.")
                else:
                    print(f"❌ Error in {agent['name']}: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"💥 Failed to connect to API: {str(e)}")

if __name__ == "__main__":
    asyncio.run(deploy())
