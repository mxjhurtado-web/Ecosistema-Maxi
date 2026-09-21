
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Service Account embebida por B64 (para Sheets/Drive en exports, NO para rúbricas)
SA_JSON_B64 = os.environ.get("ATHENAS_SA_JSON_B64", "").strip()

# Carpeta de Drive solo para exportar CSV (opcional)
DRIVE_EXPORT_FOLDER_ID = os.environ.get("DRIVE_EXPORT_FOLDER_ID", "18I2zDaj_sQbQvBiRyySdwuT2UYRNzaBt").strip()

# Sheet para autorización por correo (A: correo, B: nombre)
GS_AUTH_SHEET_ID = os.environ.get("GS_AUTH_SHEET_ID", "1Ev3i55QTW1TJQ_KQP01TxEiLmZJVkwVFJ1cn_p9Vlr0").strip()

# API key opcional de Gemini (si no, la pide UI)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
