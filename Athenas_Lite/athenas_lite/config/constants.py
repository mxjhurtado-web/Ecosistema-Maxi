import os
import sys

# Project root calculation:
# If frozen (EXE), we want the folder where the EXE lives (to find 'rubricas' next to it).
# If script, we go up from config -> athenas_lite -> Root.

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PALETTE = {"bg": "#fceff1", "brand": "#e91e63", "brand_dark": "#c2185b"}

DEPT_OPTIONS_FIXED = [
    "Administración de agencias",
    "Agent Oversight",
    "BSA Monitoring",
    "Capacitación",
    "Cheques",
    "Cobranza",
    "Cumplimiento",
    "Prevención de fraudes",
    "Servicio al cliente",
    "Soporte técnico",
    "Ventas internas (Ajustes)",
    "Ventas Internas (Bienvenida)",
    "Ventas telefónicas",
]

LOCAL_RUBRICS_DIR = os.path.join(BASE_DIR, "rubricas")
EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")
