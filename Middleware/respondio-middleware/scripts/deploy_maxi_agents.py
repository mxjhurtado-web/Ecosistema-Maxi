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

def get_agent_content(agent_dir, filename):
    try:
        # Resolve path relative to Ecosistema-Maxi root
        # Script is in Middleware/respondio-middleware/scripts/
        # Agentes IA is in Ecosistema-Maxi/Agentes IA
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        path = os.path.join(root_dir, "Agentes IA", agent_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Could not read {filename} from {agent_dir}: {e}")
        return None

# Load dynamic content from .md files
orquestador_prompt = get_agent_content("Agente Orquestador", "config_agente_orquestador.md")
vt_prompt = get_agent_content("Agente VT", "config_agente_vt.md")
status_prompt = get_agent_content("Agente Estatus", "config_agente_status.md")
verificador_prompt = get_agent_content("Agente Verificador", "config_agente_verificador.md")
generador_prompt = get_agent_content("Agente Generador", "config_agente_generador.md")
derivacion_fraudes_prompt = get_agent_content("Agente Derivacion Fraudes", "config_derivacion_fraudes.md")
derivacion_bsa_prompt = get_agent_content("Agente Derivacion BSA", "config_derivacion_bsa.md")
comunicador_prompt = get_agent_content("Agente Comunicador", "config_agente_comunicador.md")




agents = [
    {
        "name": "MAXI_ORQUESTADOR",
        "system_prompt": orquestador_prompt or "Error loading prompt",
        "readonly": False,
        "is_orchestrator": True,
        "specific_rules": {
            "routing": {
                "shipment": "PATH_SOPORTE_ENVIO",
                "status": "PATH_ESTATUS_ENVIO",
                "new_order": "PATH_REALIZAR_ENVIO",
                "billing": "PATH_PAGO_BILL",
                "history": "PATH_HISTORIAL"
            },
            "hours": {
                "weekdays": "09:00-21:00",
                "weekends": "09:00-19:00"
            }
        },
        "knowledge_sources": [],
        "web_search_enabled": False
    },
    {
        "name": "PETTE_VT_ORCHESTRATOR",
        "system_prompt": vt_prompt or "Error loading prompt",
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
        "system_prompt": status_prompt or "Error loading prompt",
        "readonly": False,
        "is_orchestrator": False,
        "specific_rules": {
            "max_attempts": 3,
            "security": "high",
            "ocr_enabled": True
        },
        "knowledge_sources": [],
        "web_search_enabled": False
    },
    {
        "name": "MAXI_VERIFICADOR",
        "system_prompt": verificador_prompt or "Error loading prompt",
        "readonly": False,
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
        "system_prompt": generador_prompt or "Error loading prompt",
        "readonly": False,
        "is_orchestrator": False,
        "specific_rules": {
            "folio_pattern": "MMDDAAAAXX",
            "db_registration": "mandatory"
        },
        "knowledge_sources": [],
        "web_search_enabled": False
    },
    {
        "name": "MAXI_DERIVACION_FRAUDES",
        "system_prompt": derivacion_fraudes_prompt or "Error loading prompt",
        "readonly": False,
        "is_orchestrator": False,
        "specific_rules": {
            "department": "Prevención de Fraudes",
            "hours": {
                "monday_to_sunday": "08:00-23:00"
            }
        },
        "knowledge_sources": [],
        "web_search_enabled": False
    },
    {
        "name": "MAXI_DERIVACION_BSA",
        "system_prompt": derivacion_bsa_prompt or "Error loading prompt",
        "readonly": False,
        "is_orchestrator": False,
        "specific_rules": {
            "department": "BSA Monitoring",
            "hours": {
                "monday_to_friday": "08:00-19:00",
                "saturday": "08:00-18:00"
            }
        },
        "knowledge_sources": [],
        "web_search_enabled": False
    },
    {
        "name": "MAXI_COMUNICADOR",
        "system_prompt": comunicador_prompt or "Error loading prompt",
        "readonly": False,
        "is_orchestrator": False,
        "specific_rules": {
            "department": "Soporte Interno / Departamentos",
            "actions": [
                "Notificar_Agent_Oversight",
                "Notificar_Capacitacion",
                "Notificar_Cumplimiento",
                "Notificar_Cobranza",
                "Notificar_Cheques",
                "Notificar_Soporte_Tecnico",
                "Notificar_Ventas_Internas"
            ]
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
