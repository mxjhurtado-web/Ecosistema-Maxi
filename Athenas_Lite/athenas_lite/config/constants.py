import os

# Project root calculation: .../athenas_lite/config/constants.py -> up 3 levels?
# No, structure is:
# Root
#   athenas_lite/
#     config/
#       constants.py
#   rubricas/
# So we need to go up from config (parent) -> athenas_lite (parent) -> Root

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
