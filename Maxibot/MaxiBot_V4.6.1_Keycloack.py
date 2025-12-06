from registro import crear_base, registrar_ingreso, registrar_consulta
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import os
import unicodedata
import difflib
import requests
from datetime import datetime
import io, base64, json, re, time

# ====== imports extra para loader avanzado ======
try:
    import PyPDF2
    _PDF_OK = True
except Exception:
    PyPDF2 = None
    _PDF_OK = False

try:
    import docx
    _DOCX_OK = True
except Exception:
    docx = None
    _DOCX_OK = False

try:
    import openpyxl
    _XLSX_OK = True
except Exception:
    openpyxl = None
    _XLSX_OK = False

import zipfile
import struct
# ===============================================

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# === Logo helpers ===
try:
    from PIL import Image, ImageTk  # optional; fallback works without
    _PIL_OK = True
except Exception:
    _PIL_OK = False

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(ASSETS_DIR, "Logo_MaxiBot.png")
_logo_cache = {}

def get_logo(size=48):
    """Load and cache the PNG logo at the requested size."""
    if size in _logo_cache:
        return _logo_cache[size]
    if not os.path.exists(LOGO_PATH):
        _logo_cache[size] = None
        return None
    if _PIL_OK:
        img = Image.open(LOGO_PATH).convert("RGBA").resize((size, size), Image.LANCZOS)
        tkimg = ImageTk.PhotoImage(img)
    else:
        base = tk.PhotoImage(file=LOGO_PATH)
        factor = max(1, int(round(base.width() / size)))  # integer subsample
        tkimg = base.subsample(factor, factor)
    _logo_cache[size] = tkimg
    return tkimg


# ===========================
# 🎨 THEME
# ===========================
COLORS = {
    "app_bg": "#eef2f7",
    "card_bg": "#ffffff",
    "header_grad_start": "#1de58f",
    "header_grad_end": "#06a2ff",
    "accent": "#0b5fff",
    "accent_dark": "#0a3edb",
    "text_primary": "#0f172a",
    "text_secondary": "#475569",
    "chip_bg": "#eaf2ff",
    "chip_ok_bg": "#e8fff2",
    "chip_text": "#0f172a",
    "bot_bubble": "#e8f7e9",
    "user_bubble": "#1b4bff",
    "user_text": "#ffffff",
    "divider": "#e5e7eb"
}
FONT = {
    "title": ("Segoe UI", 16, "bold"),
    "subtitle": ("Segoe UI", 10),
    "chip": ("Segoe UI", 9, "bold"),
    "body": ("Segoe UI", 10),
    "meta": ("Segoe UI", 8),
    "btn": ("Segoe UI", 10, "bold"),
    "btn_small": ("Segoe UI", 9, "bold"),
}

# ===========================
# 🔧 CONFIG
# ===========================
CONVERSATION_FOLDER = "Conversaciones_Maxibot"
CSV_FOLDER = "Registros_Sesiones"

# Google Sheets/Drive IDs
GS_KB_SHEET_ID = "1wrtj7SZ6wB9h1yd_9h613DYNPGjI69_Zj1gLigiUHtE"      # Contenido
GS_AUTH_SHEET_ID = "1Ev3i55QTW1TJQ_KQP01TxEiLmZJVkwVFJ1cn_p9Vlr0"  # Autorizados

# ✅ Carpetas separadas
DRIVE_SESSIONS_FOLDER_ID = "1S7L5VNQRpepQyHQ0MHEYDf59JS-H1YtG"   # Sesiones
DRIVE_NEWRESP_FOLDER_ID  = "1NGP64FcClecTT8Bj2KyPd-z3kZm-7ine"   # Guardados manuales

# ✅ Carpeta de documentos para el Loader (PON AQUÍ EL ID REAL)
#    Si prefieres usar variable de entorno, deja esto vacío y exporta DOCS_FOLDER_ID.
DOCS_FOLDER_ID = os.getenv("DOCS_FOLDER_ID", "1luJOVyYZN2z258plKJGPfjpwIR2zwNWX")

# === Avisos (nuevo) ===
AVISOS_SHEET_ID  = "1ro0vpM8BUhR6RtXgtwKn0jf85pWaqquRT_2Pp7qPuqU"
AVISOS_TAB_NAME  = "Avisos"
AVISOS_POLL_SEC  = 60  # cada 60s revisa nuevos avisos

# Modelo Gemini (solo pruebas / se puede sobrescribir después de login)
GEMINI_API_KEY = ""

usuario_actual = {"correo": None, "nombre": None, "alias": None, "sso": False}

# ===========================
# 🔐 Keycloak (SSO opcional)
# ===========================
try:
    from keycloak_auth import KeycloakAuth  # type: ignore
    import keycloak_config  # type: ignore
    _KEYCLOAK_OK = True
except Exception as e:
    print("Keycloak no disponible:", e)
    KeycloakAuth = None  # type: ignore
    _KEYCLOAK_OK = False

keycloak_auth_instance = None


def autenticar_con_keycloak():
    """
    Inicia sesión con Keycloak usando el wrapper KeycloakAuth.

    Devuelve:
        (ok: bool, mensaje: str)
    """
    global keycloak_auth_instance

    if not _KEYCLOAK_OK or KeycloakAuth is None:
        return False, "Keycloak no está configurado en este equipo."

    try:
        keycloak_auth_instance = KeycloakAuth()
        ok, msg = keycloak_auth_instance.authenticate()
        if not ok:
            keycloak_auth_instance = None
            return False, msg or "No se pudo autenticar con Keycloak."

        correo = (keycloak_auth_instance.get_user_email() or "").strip()
        nombre = (keycloak_auth_instance.get_user_name() or correo or "Usuario").strip()

        if not correo:
            keycloak_auth_instance = None
            return False, "La autenticación SSO no devolvió un correo válido."

        usuario_actual["correo"] = correo
        usuario_actual["nombre"] = nombre
        usuario_actual["sso"] = True

        # Registramos el ingreso como "v4.6.1 (SSO)"
        try:
            registrar_ingreso(correo, nombre, "v4.6.1 (SSO)")
        except Exception as e:
            print("No se pudo registrar ingreso SSO:", e)

        return True, f"Sesión iniciada como {nombre}"
    except Exception as e:
        keycloak_auth_instance = None
        return False, f"Error al autenticar con Keycloak: {e}"


def verificar_autenticacion_keycloak() -> bool:
    """Devuelve True si hay una sesión Keycloak válida."""
    if not keycloak_auth_instance:
        return False
    try:
        return bool(keycloak_auth_instance.is_authenticated())
    except Exception as e:
        print("Error al verificar sesión Keycloak:", e)
        return False


def cerrar_sesion_keycloak():
    """Cierra la sesión SSO y limpia el usuario actual."""
    global keycloak_auth_instance

    try:
        if keycloak_auth_instance:
            try:
                keycloak_auth_instance.logout()
            except Exception as e:
                print("Error al cerrar sesión Keycloak:", e)
    finally:
        keycloak_auth_instance = None
        usuario_actual["correo"] = None
        usuario_actual["nombre"] = None
        usuario_actual["alias"] = None
        usuario_actual["sso"] = False


# === Service Account embebida (base64) ===
SA_JSON_B64 = ("ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAibWF4aWJvdC00NzI0MjMiLAogICJwcml2YXRlX2tleV9pZCI6ICJmOTFkMGRjYWM2ODA4NTYyY2IxOTRlOWM0NmU5ZDM2MGY1ZTNjNTczIiwKICAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUURIN0IrZ0JnTU9ScElmXG50ejJQSWRieXpoUnduSitVcitZN05JT1FsRGpNMWgweEl3dUIrNHZ6M2w4M1J1dWJ5VEQvbUQ1NklDckJONkg2XG50RkNDcTErbytsMWl0T1lHYkNVajdCcnBZM3ZnbHJmUVJFcUdnV1EzT2lxdGR6bHE3b3RhZk11K1d6bVlKODVQXG5QNnl1SUVJbnUyVXFEYW5WV3ZrL2Q1WnlaRkF3UG9IRDVIMldKcGlwblNhTW1HcXhDRG5RWTAxVDAwUWRiaStIXG42NlFscXdCQURFajZXWHhCNm1BdXZIdXRJTG4vaWRsYWpZRU4zVDd3OTJ1Q2JPNVk1dlFuUlI1TGViS1paaE5hXG5ZbTlPanp3TE9SekFPVG9rWCswWXZxUGFhTXplV2lncWY5RDJMZ3NMbE1sZnpBNXpxQkhEV0szaTJGMngvYWNXXG5jVkJIRzI2N0FnTUJBQUVDZ2dFQUNndWVSeThtSmloN25TWmE3SDg1eXJkNkpYSnBQbEpjVWl0QVZScHRoRFZhXG5BQ2NQby9kY3YrTXppNVovcmpNOHlBc0JVS2VmSGxoS1JrdWJKQVd5Wjg0MHRRbjc2T1MwTlFyZkMwMFpZMTZQXG5XK0tpa0FHZVpId0N1dmFicHZqWGZiTjVsVllHSGRRYU5MY3hXUXA3NkgwdEJ5RHFvTExTaFZMZjkxMTgvZjkvXG5RVGlIMk1pMkZNS3crVS93ckVsbmV0SFIrSE1vV2Fia2picGx4cEZQRDNMTkpWU0oybHkwUzBzb2praDV0WEZ5XG5ubDJXVUJPd1FTVmNmQzhvVHNwQXM3SUpXRzZVYldBc2dkZHlWZUU1VDRkZGFoa0JDSEhYQVFBUVYzYjJFTGM2XG54USs5WVFxS2VJNmNTMW5OeHNRUjBlK1V3OG1zT3V1MElSS3Mva2hmQVFLQmdRRHlzUGVGaFJUZ01kd1NsS2dCXG5vVHlnTUxtd3JVUGhzMXJ6d1g1eEVaUWtSRmVjb2F4M0U3WDJFTnRpR1AyRm9oU0R4VVd4TFE3czMyaFFOU0RpXG5tbmh1NWs4SVk1Nmt2VGxjbzlMeDV5TEF5UHEyTFNQWDUrYmowZXkzdEZkVXFaT0dqWlRrV0R3NUh4QlBRMHIyXG5BbFFKT01RUURMRHFPQnFXWUd4YksydHdPd0tCZ1FEUzRyNDkybk92TGhMaHYyMm0yUTlVa3BRcis4RC9udXQ5XG45ajJwSzFQQ1dRRmJhSHRVWit3NFhPUk1pczVqM3ZaTkg3aDd0Z3hvM0FhTGhGMS8wSlJYaTlpS2V2SmpKU0JjXG5zREI2SFE5cFBmNUU0SHNPOE9zejBDNjMzYXNMUFNZakIwNFdUWkVtQ0J2dFoxeGtXZHpQdG1VajZSYThSZUkwXG56TkFDeXpLVGdRS0JnQmZ3enlvVHU4QjJDckNtaTRCRnFKWmcyQ0NPcHhDZndjd2ovVllvRnNZUkc5ZHV0M1d6XG5zeEtJRFN3N0xOOCs0dWt3ejdRdnJyWTlQNndSNGFHWS9XSnJROGFmRlNwSkpGeDRLTG9HUkE1aWhTRHRpUWltXG5ic2R3a1BwNlJ0Y3FOMHhoc1J0cGZOOWhxaGszbVRCMWdGYThpOUxOZmJKTlFJb3ZEdUZiZ2lpN0FvR0FPdGdZXG5PNHdzUVpKNnBGRlZHSHh5NGFkdy93RGxycTQ2aWRCZkRraFB1K2c0RDdpTXlWV2lQV3YyTEVHREs2ejRUemJ0XG50Rjl0QVFsOExnd0dSdmI5blp3aEZTc1BYWWpyaWRHRUJWNzhnT0pTaEFlYmJ1VGN6SDFudTloM3ROQWdSeC92XG5zeHQ3eC8vMVF2NVhjb3o4cDF6K3hkRnhqYUYyYUVOS082MVZkSUVDZ1lFQXovMTRCVnZDQ2MzRGg0elBFOXlBXG4weEp0ZDhzNUw2YUdnT3h5RzRZR3VuKzZ0QTBKOWZvUWV4cHd2azFpWGlOYXZvWTNWN3haRUNSSm1ua2l4TEEzXG53bWZ3YzZFTkVWWjg0b2Y0VU42SVRSdCtHRytGZThTaE05STBFVHpFYWlTcmQvT0VxQ1VQZVlNelNQQVNIakRCXG5PdW1LWHlkU2N5NWhlNUdpNm9rc2MyWT1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsCiAgImNsaWVudF9lbWFpbCI6ICJtYXhpYm90LXNhQG1heGlib3QtNDcyNDIzLmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAiY2xpZW50X2lkIjogIjExNjkyMDExNDg3MTgwMTYxMTEzOSIsCiAgImF1dGhfdXJpIjogImh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9hdXRoIiwKICAidG9rZW5fdXJpIjogImh0dHBzOi8vb2F1dGgyLmdvb2dsZWFwaXMuY29tL3Rva2VuIiwKICAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsCiAgImNsaWVudF94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL3JvYm90L3YxL21ldGFkYXRhL3g1MDkvbWF4aWJvdC1zYSU0MG1heGlib3QtNDcyNDIzLmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIgp9Cg==")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def _load_sa_info():
    b64 = (SA_JSON_B64 or "").strip()
    if not b64:
        raise RuntimeError("SA embebida vacía.")
    try:
        b64_clean = "".join(b64.split())
        b64_clean += "=" * (-len(b64_clean) % 4)  # padding seguro
        data = base64.b64decode(b64_clean.encode("utf-8"))
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Credenciales embebidas inválidas: {e}")

def _creds():
    info = _load_sa_info()
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

def _sheets_service():
    return build("sheets","v4",credentials=_creds(), cache_discovery=False)

def _drive_service():
    return build("drive","v3",credentials=_creds(), cache_discovery=False)

def _sheet_titles(sheet_id: str):
    svc = _sheets_service()
    meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
    return [s["properties"]["title"] for s in meta.get("sheets", [])]

def _get_rows(sheet_id: str, title: str):
    svc = _sheets_service()
    rng = "'" + title + "'!A:Z"
    res = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range=rng).execute()
    return res.get("values", [])

def _rows_to_mapping(rows, col_q="pregunta", col_a="respuesta"):
    if not rows: return {}
    header = [str(h).strip().lower() for h in rows[0]]
    try:
        i_p = header.index(col_q); i_r = header.index(col_a)
    except ValueError:
        return {}
    out = {}
    for row in rows[1:]:
        if i_p < len(row) and i_r < len(row):
            p = str(row[i_p]).strip(); r = str(row[i_r]).strip()
            if p and r: out[p] = r
    return out

def _append_row(sheet_id: str, title: str, values: list[list]):
    svc = _sheets_service()
    rng = "'" + title + "'!A:Z"
    body = {"values": values}
    svc.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=rng,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

def cargar_todas_las_respuestas():
    # Lee todas las pestañas del Sheet de Contenido con columnas Pregunta/Respuesta
    respuestas_por_hoja = {}
    try:
        for title in _sheet_titles(GS_KB_SHEET_ID):
            m = _rows_to_mapping(_get_rows(GS_KB_SHEET_ID, title))
            if m:
                respuestas_por_hoja[title] = m
    except Exception as e:
        try:
            messagebox.showerror("Error", f"No pude leer el Sheet de contenido: {e}")
        except Exception:
            print("No pude leer el Sheet de contenido:", e)
    return respuestas_por_hoja

def verificar_correo_online(correo):
    try:
        for title in _sheet_titles(GS_AUTH_SHEET_ID):
            rows = _get_rows(GS_AUTH_SHEET_ID, title)
            if not rows:
                continue
            header = [str(h).strip().lower() for h in rows[0]]
            if "correo" in header:
                i_c = header.index("correo")
                i_n = header.index("nombre") if "nombre" in header else None
                for r in rows[1:]:
                    if i_c < len(r) and str(r[i_c]).strip().lower() == str(correo).strip().lower():
                        nombre = str(r[i_n]).strip() if (i_n is not None and i_n < len(r)) else correo
                        return True, nombre
    except Exception as e:
        print("Error al validar correo:", e)
    return False, None

# ===========================
# 🔎 Gemini (KB + Web)
# ===========================
def buscar_con_gemini(prompt: str):
    """
    Llama a Gemini usando la API Key actual.
    Si no hay API Key configurada, avisa de forma clara.
    """
    if not GEMINI_API_KEY:
        return ("No hay API Key configurada para el modelo. "
                "Por favor, vuelve a iniciar sesión e ingresa una API Key.")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=payload, timeout=30)
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"No se pudo obtener respuesta de Gemini: {e}"



def _normalize_for_match(text):
    text = text or ""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(text.split())

def _token_jaccard(a, b):
    aa = set(_normalize_for_match(a).split())
    bb = set(_normalize_for_match(b).split())
    if not aa or not bb: return 0.0
    inter = len(aa & bb); union = len(aa | bb)
    return inter / union

def _substring_score(a, b):
    an = _normalize_for_match(a); bn = _normalize_for_match(b)
    if an and an in bn:
        return min(len(an)/max(len(bn),1), 1.0)
    if bn and bn in an:
        return min(len(bn)/max(len(an),1), 1.0)
    return 0.0

def _difflib_ratio(a, b):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, _normalize_for_match(a), _normalize_for_match(b)).ratio()

def _composite_score(user_q, kb_q):
    w_dl, w_jac, w_sub = 0.55, 0.35, 0.10
    return (w_dl * _difflib_ratio(user_q, kb_q)
            + w_jac * _token_jaccard(user_q, kb_q)
            + w_sub * _substring_score(user_q, kb_q))

def _kb_collect_entries(respuestas_por_hoja):
    entries = []
    idx = 1
    for hoja, base in (respuestas_por_hoja or {}).items():
        for q, a in base.items():
            entries.append({"id": f"K{idx}", "hoja": hoja, "pregunta": str(q), "respuesta": str(a)})
            idx += 1
    return entries

def _preselect_candidates(user_q, entries, top_k=15):
    scored = []
    for e in entries:
        s = _composite_score(user_q, e["pregunta"])
        scored.append((s, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:max(1, top_k)]]

def _gemini_select_from_candidates(user_q, candidates):
    try:
        if not candidates:
            return None
        lines = []
        lines.append("Eres un motor de búsqueda. Elige el ID de la pregunta del KB que MEJOR responde a la consulta del usuario.")
        lines.append("Si ninguna coincide claramente, responde SOLO con: NONE")
        lines.append("Responde ÚNICAMENTE con el ID exacto (ej. K3) o NONE. No agregues texto adicional.")
        lines.append("Consulta del usuario:")
        lines.append(user_q.strip())
        lines.append("Candidatos:")
        for e in candidates:
            q = e["pregunta"].strip().replace("\n", " ")
            if len(q) > 300: q = q[:300] + "…"
            lines.append(f"- {e['id']}: {q}")
        prompt = "\n".join(lines)

        ans = buscar_con_gemini(prompt).strip()
        ids = {e["id"].upper(): e for e in candidates}
        ans_first = ans.splitlines()[0].strip().upper()
        if ans_first in ids:
            return ids[ans_first]
        m = re.search(r"\b(K\d+)\b", ans, flags=re.IGNORECASE)
        if m and m.group(1).upper() in ids:
            return ids[m.group(1).upper()]
        if "NONE" in ans_first:
            return None
        # fallback: si Gemini no siguió instrucción, toma top-1 local
        return candidates[0]
    except Exception:
        return candidates[0] if candidates else None

def buscar_en_excel_completo(pregunta_usuario, respuestas_por_hoja):
    """
    Usa Gemini para seleccionar la mejor pregunta del KB (sobre un shortlist local).
    Si encuentra match, devuelve la RESPUESTA EXACTA del KB.
    Si no, deja que la UI pregunte si se busca en la web.
    """
    entries = _kb_collect_entries(respuestas_por_hoja)
    if not entries:
        return None, None, None, pregunta_usuario, None

    shortlist = _preselect_candidates(pregunta_usuario, entries, top_k=15)
    elegido = _gemini_select_from_candidates(pregunta_usuario, shortlist)

    if elegido is not None:
        # Respetar la respuesta del Excel al máximo → devolver tal cual
        return elegido["respuesta"], "excel", elegido["hoja"], None, None

    return None, None, None, pregunta_usuario, None

# === Flujo principal: primero KB; si no, Docs → MCP → Web ===
def buscar_respuesta(pregunta_usuario, respuestas_por_hoja):
    respuesta, origen, hoja, pregunta_web, respuesta_web = buscar_en_excel_completo(pregunta_usuario, respuestas_por_hoja)
    if respuesta:
        return respuesta, "excel", hoja, None, None  # RESPETO ESTRICTO
    else:
        return None, "no_encontrada", None, pregunta_usuario, None

def reformular_con_gemini(texto):
    prompt = f"Reescribe esta respuesta de forma clara y cálida SIN agregar nueva info ni cambiar el sentido:\n\n{texto}"
    return buscar_con_gemini(prompt)

def guardar_en_hoja_aprendida(pregunta, respuesta):
    hoja = "Aprendido_2025"
    try:
        _append_row(GS_KB_SHEET_ID, hoja, [[pregunta, respuesta, datetime.now().isoformat(sep=' ', timespec='seconds')]])
    except Exception as e:
        print(f"Error al guardar en hoja '{hoja}':", e)

def guardar_conversacion(nombre, pregunta, respuesta):
    if not os.path.exists(CONVERSATION_FOLDER):
        os.makedirs(CONVERSATION_FOLDER)
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archivo = os.path.join(CONVERSATION_FOLDER, f"{nombre}_{fecha}.txt")
    with open(archivo, "w", encoding="utf-8") as f:
        f.write(f"{nombre}: {pregunta}\nMaxiBot: {respuesta}\n")

def asegurar_carpeta_csv():
    if not os.path.exists(CSV_FOLDER):
        os.makedirs(CSV_FOLDER)

def guardar_csv_sesion():
    if not registro_sesion:
        return
    nombre = usuario_actual.get("alias") or "usuario"
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sesion_{nombre}_{fecha}.csv"
    df = pd.DataFrame(registro_sesion)
    try:
        svc = _drive_service()
        csv_bytes = df.to_csv(index=False, encoding="utf-8").encode("utf-8")
        media = MediaIoBaseUpload(io.BytesIO(csv_bytes), mimetype="text/csv", resumable=False)
        meta = {"name": filename, "mimeType": "text/csv", "parents": [DRIVE_SESSIONS_FOLDER_ID]}
        f = svc.files().create(body=meta, media_body=media, supportsAllDrives=True, fields="id, webViewLink").execute()
        print(f"✅ Sesión subida a Drive: {f.get('webViewLink')}")
    except Exception as e:
        print(f"⚠️ No pude subir a Drive ({e}). Guardando local…")
        asegurar_carpeta_csv()
        archivo = os.path.join(CSV_FOLDER, filename)
        df.to_csv(archivo, index=False, encoding="utf-8")
        print(f"💾 Registro de sesión guardado en: {archivo}")

def cerrar_app():
    try:
        guardar_csv_sesion()
    finally:
        app.destroy()

# ===========================
# 🛡️ Anti-alucinación (para Web)
# ===========================
ANTI_HALLUCINATION_NOTE = (
    "\nReglas:"
    "\n- Devuelve solo hechos con fuente (URL real y verificable)."
    "\n- Si no encuentras evidencia sólida o URLs confiables, responde: 'No encontré evidencia suficiente'."
    "\n- No inventes nombres, cifras o enlaces."
)

# ==========================
# 🔌 MCP (Model Context Protocol) – opcional
# ==========================
from urllib.parse import urljoin
import requests as _req_mcp

MCP_ENABLED = True
MCP_ENDPOINT = os.getenv("MCP_ENDPOINT", "http://127.0.0.1:5000").strip().rstrip("/")

class MCPTool:
    """
    Cliente MCP con implementación genérica HTTP/SDK.
    Prioridad:
      1) SDK (si existe el paquete 'mcp' y soporta client.tools['search'].call)
      2) HTTP REST (POST a {endpoint}/tools/search con JSON {"q": query, "limit": top_k})
    Autorización opcional:
      - MCP_API_KEY en header "Authorization: Bearer <MCP_API_KEY>"
    Respuesta esperada (HTTP):
      {"results":[{"title":"...","snippet":"...","url":"...","score":0.9}, ...]}
    """
    def __init__(self, endpoint: str = MCP_ENDPOINT, *, api_key: str | None = None, timeout: int = 20):
        self.endpoint = (endpoint or "").strip().rstrip("/")
        self.timeout = timeout
        self.api_key = api_key or os.getenv("MCP_API_KEY") or ""

        # SDK opcional
        try:
            import mcp  # type: ignore
            self._mcp = mcp
        except Exception:
            self._mcp = None

    def available(self) -> bool:
        # Disponible si hay SDK con endpoint definido o si hay endpoint HTTP listo.
        return bool(self.endpoint)

    def _http_post(self, path: str, payload: dict):
        if not self.endpoint:
            return None, {"error": "No endpoint"}
        url = urljoin(self.endpoint + "/", path.lstrip("/"))
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            r = _req_mcp.post(url, json=payload, headers=headers, timeout=self.timeout)
            try:
                data = r.json()
            except Exception:
                data = {"error": f"HTTP {r.status_code} sin JSON", "text": r.text[:500]}
            return r.status_code, data
        except Exception as e:
            return None, {"error": f"HTTP error: {e}"}

    def search(self, query: str, top_k: int = 3):
        if not self.available():
            return []
        # 1) SDK (si lo usas más adelante)
        if self._mcp:
            try:
                # client = self._mcp.Client(self.endpoint, api_key=self.api_key or None)
                # results = client.tools["search"].call({"q": query, "limit": top_k})
                # return [{"title": r.get("title","MCP"), "content": r.get("snippet") or r.get("content",""),
                #          "url": r.get("url",""), "score": float(r.get("score", 1.0))} for r in results]
                pass
            except Exception:
                pass
        # 2) HTTP REST
        status, data = self._http_post("/tools/search", {"q": query, "limit": int(top_k)})
        if status and 200 <= status < 300 and isinstance(data, dict):
            items = data.get("results") or data.get("data") or []
            out = []
            for r in items:
                out.append({
                    "title": r.get("title") or "MCP",
                    "content": r.get("snippet") or r.get("content") or "",
                    "url": r.get("url") or "",
                    "score": float(r.get("score", 1.0)) if isinstance(r.get("score", 1.0), (int, float, str)) else 1.0
                })
            return out
        return []

mcp_tool = MCPTool()


# ===========================
# 📄 DocsTool (Loader simple con Drive API) + loader avanzado
# ===========================
class DocsTool:
    """
    Lista archivos desde una carpeta de Drive y ofrece búsqueda simple.
    Usa la SA embebida y el mismo `_drive_service()` del KB.
    """
    def __init__(self, drive_folder_id: str = None):
        # 1) carpeta fija de config, 2) parámetro explícito, 3) variable de entorno
        self.drive_folder_id = drive_folder_id or DOCS_FOLDER_ID or os.getenv("DOCS_FOLDER_ID", "")
        self.index = []  # {"title","content","summary","url","score"}

    def add_document(self, title: str, content: str, url: str = ""):
        """Permite al loader recursivo añadir documentos al índice."""
        self.index.append({
            "title": title or "Documento",
            "content": content or "",
            "summary": content or "",
            "url": url or "",
            "score": 1.0,
        })

    def refresh(self, max_files: int = 50):
        """
        Refresca el índice usando el loader recursivo avanzado.
        Si no hay DOCS_FOLDER_ID, hace un listado plano como fallback.
        """
        try:
            svc = _drive_service()
            self.index = []

            # Si tenemos carpeta definida, usamos el loader recursivo “pro”
            if self.drive_folder_id:
                n = load_drive_folder_to_docs_tool(
                    svc,
                    folder_id=self.drive_folder_id,
                    docs_tool=self,
                    max_chars_per_doc=20000,
                )
                return n

            # Fallback: listado simple en todo el Drive (no recomendado pero sirve de respaldo)
            q = "trashed = false"
            res = svc.files().list(
                q=q,
                pageSize=max_files,
                fields="files(id,name,mimeType,webViewLink,description)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()
            files = res.get("files", [])
            for f in files:
                content = f.get("description") or f.get("name","")
                self.index.append({
                    "title": f.get("name","Documento"),
                    "content": content,
                    "summary": content,
                    "url": f.get("webViewLink",""),
                    "score": 1.0
                })
            return len(self.index)
        except Exception as e:
            print("DocsTool.refresh error:", e)
            return 0

    @staticmethod
    def _normalize(s: str) -> str:
        import re, unicodedata
        s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode().lower()
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _score(self, q: str, t: str) -> float:
        qn = self._normalize(q); tn = self._normalize(t)
        if not tn: return 0.0
        score = 0.0
        if qn in tn: score += 0.7
        qset = set(qn.split()); tset = set(tn.split())
        if qset:
            score += min(len(qset & tset) / len(qset), 1.0) * 0.3
        return score

    def search(self, query: str, top_k: int = 3):
        if not self.index:
            try:
                self.refresh()
            except Exception:
                return []
        scored = [(self._score(query, it.get("content","") or it.get("title","")), it) for it in self.index]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:max(1, top_k)]]

docs_tool = DocsTool()

# ==========================
# 📥 Loader recursivo (Docs/PDF/DOCX/TXT/XLSX/CSV/Sheets/PBIX/EXE)
# ==========================
_EXE_MAX_BYTES = 4 * 1024 * 1024
_STRINGS_MIN = 6

def _drive_list_children_recursive(svc, folder_id: str):
    stack = [folder_id]
    while stack:
        fid = stack.pop()
        q = f"'{fid}' in parents and trashed=false"
        res = svc.files().list(
            q=q,
            fields="files(id,name,mimeType,parents), nextPageToken",
            pageSize=1000,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        for f in res.get("files", []):
            if f["mimeType"] == "application/vnd.google-apps.folder":
                stack.append(f["id"])
            else:
                yield f, fid

def _export_google_doc_to_text(svc, file_id: str, max_chars: int = 20000) -> str:
    data = svc.files().export_media(fileId=file_id, mimeType='text/plain').execute()
    if isinstance(data, (bytes, bytearray)):
        return data.decode("utf-8", "ignore")[:max_chars]
    return str(data)[:max_chars]

def _download_bytes(svc, file_id: str) -> bytes:
    from googleapiclient.http import MediaIoBaseDownload
    req = svc.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    return buf.getvalue()

def _parse_pdf(data: bytes, max_chars: int = 20000) -> str:
    if not _PDF_OK or not data: return ""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(data))
        texts = []
        for page in reader.pages:
            try: texts.append(page.extract_text() or "")
            except Exception: pass
        return "\n".join(texts)[:max_chars]
    except Exception:
        return ""

def _parse_docx(data: bytes, max_chars: int = 20000) -> str:
    if not _DOCX_OK or not data: return ""
    try:
        d = docx.Document(io.BytesIO(data))
        texts = [p.text or "" for p in d.paragraphs]
        return "\n".join(texts)[:max_chars]
    except Exception:
        return ""

def _parse_txt(data: bytes, max_chars: int = 20000) -> str:
    try: return data.decode("utf-8","ignore")[:max_chars]
    except Exception: return ""

def _parse_xlsx(data: bytes, max_chars: int = 20000) -> str:
    if not _XLSX_OK or not data: return ""
    try:
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        out = []
        for ws in wb.worksheets[:5]:
            out.append(f"[Hoja] {ws.title}")
            for r_i, row in enumerate(ws.iter_rows(values_only=True)):
                if r_i >= 100: break
                vals = [str(x) if x is not None else "" for x in row]
                line = " | ".join(vals).strip()
                if line: out.append(line)
        return "\n".join(out)[:max_chars]
    except Exception:
        return ""

def _parse_csv(data: bytes, max_chars: int = 20000) -> str:
    if not data: return ""
    try: s = data.decode("utf-8", "ignore")
    except Exception:
        try: s = data.decode("latin-1", "ignore")
        except Exception: return ""
    return "\n".join(s.splitlines()[:200])[:max_chars]

def _parse_pbix_basic(data: bytes, max_chars: int = 20000) -> str:
    if not data: return ""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            cand = [n for n in z.namelist() if "Report" in n and n.lower().endswith(("layout","layout.json","report.json"))]
            if not cand:
                names = "\n".join(z.namelist()[:30])
                return f"[PBIX] No hallé Layout/Report JSON. Contenido:\n{names}"[:max_chars]
            with z.open(cand[0]) as f:
                raw = f.read()
            try:
                js = json.loads(raw.decode("utf-8","ignore"))
            except Exception:
                return f"[PBIX] Layout no es JSON legible ({cand[0]})."
            out = ["[PBIX] Extracto de Layout:"]
            def _walk(obj):
                if isinstance(obj, dict):
                    for k in ("name","displayName","title","text","pageName","visualType"):
                        v = obj.get(k)
                        if isinstance(v, str) and 2 <= len(v) <= 200:
                            out.append(f"{k}: {v}")
                    for v in obj.values(): _walk(v)
                elif isinstance(obj, list):
                    for v in obj: _walk(v)
            _walk(js)
            return "\n".join(out)[:max_chars]
    except Exception as e:
        return f"[PBIX] No se pudo leer: {e}"[:max_chars]

def _extract_strings(data: bytes, min_len: int = _STRINGS_MIN, max_chars: int = 20000) -> str:
    if not data: return ""
    data = data[:_EXE_MAX_BYTES]
    ascii_re = re.compile(rb"[ -~]{%d,}" % min_len)
    utf8_re  = re.compile(rb"(?:[\x09\x0A\x0D\x20-\x7E]|[\xC2-\xF4][\x80-\xBF]+){%d,}" % min_len)
    parts = []
    for m in ascii_re.finditer(data):
        parts.append(m.group().decode("utf-8","ignore"))
    for m in utf8_re.finditer(data):
        parts.append(m.group().decode("utf-8","ignore"))
    return "\n".join(parts)[:max_chars]

def _parse_exe_safe(data: bytes, max_chars: int = 20000) -> str:
    if not data: return ""
    meta = []
    try:
        if data[:2] == b'MZ':
            pe_off = struct.unpack_from("<I", data, 0x3C)[0]
            if data[pe_off:pe_off+4] == b'PE\x00\x00':
                ts = struct.unpack_from("<I", data, pe_off + 8)[0]
                meta.append(f"PE Timestamp (epoch): {ts}")
    except Exception:
        pass
    strings = _extract_strings(data, max_chars=max_chars)
    prefix = "[EXE Metadata]\n" + "\n".join(meta) + "\n\n" if meta else ""
    return (prefix + strings)[:max_chars]

def load_drive_folder_to_docs_tool(svc, folder_id: str, docs_tool: DocsTool, max_chars_per_doc: int = 20000) -> int:
    """Loader recursivo opcional."""
    count = 0
    for f, parent in _drive_list_children_recursive(svc, folder_id):
        fid = f["id"]; name = f.get("name",""); mime = f.get("mimeType","")
        url = f"https://drive.google.com/file/d/{fid}/view"
        text = ""
        try:
            if mime == 'application/vnd.google-apps.document':
                text = _export_google_doc_to_text(svc, fid, max_chars=max_chars_per_doc)
            else:
                data = _download_bytes(svc, fid)
                if not data: continue
                name_l = name.lower()
                if mime == "application/pdf" or name_l.endswith(".pdf"):
                    text = _parse_pdf(data, max_chars=max_chars_per_doc)
                elif name_l.endswith(".docx"):
                    text = _parse_docx(data, max_chars=max_chars_per_doc)
                elif name_l.endswith(".txt") or mime.startswith("text/"):
                    text = _parse_txt(data, max_chars=max_chars_per_doc)
                elif name_l.endswith(".xlsx"):
                    text = _parse_xlsx(data, max_chars=max_chars_per_doc)
                elif name_l.endswith(".csv"):
                    text = _parse_csv(data, max_chars=max_chars_per_doc)
                elif name_l.endswith(".pbix"):
                    text = _parse_pbix_basic(data, max_chars=max_chars_per_doc)
                elif name_l.endswith(".exe") or mime in ("application/x-msdownload","application/vnd.microsoft.portable-executable"):
                    text = _parse_exe_safe(data, max_chars=max_chars_per_doc)
                elif mime == "application/vnd.google-apps.spreadsheet":
                    try:
                        data_csv = svc.files().export_media(fileId=fid, mimeType="text/csv").execute()
                        text = _parse_csv(data_csv, max_chars=max_chars_per_doc)
                    except Exception:
                        text = ""
                else:
                    text = ""
            if text:
                docs_tool.add_document(title=name, content=text, url=url); count += 1
        except Exception:
            pass
    return count

# ===========================
# 🛎️ AVISOS (Sheet dedicado)
# ===========================
_last_aviso_ts = None
_avisos_cache = []

def _read_avisos():
    try:
        rows = _get_rows(AVISOS_SHEET_ID, AVISOS_TAB_NAME)
        if not rows or len(rows) < 2:
            return []
        header = [str(h).strip().lower() for h in rows[0]]
        it = header.index("titulo") if "titulo" in header else None
        im = header.index("mensaje") if "mensaje" in header else None
        its = header.index("timestamp") if "timestamp" in header else None
        out = []
        for r in rows[1:]:
            tit = r[it].strip() if (it is not None and it < len(r)) else ""
            msg = r[im].strip() if (im is not None and im < len(r)) else ""
            ts  = r[its].strip() if (its is not None and its < len(r)) else ""
            if tit or msg:
                out.append({"titulo": tit, "mensaje": msg, "ts": ts})
        return out
    except Exception as e:
        print("Avisos error:", e)
        return []

def _notify_popup(title, message):
    try:
        tw = tk.Toplevel(app)
        tw.overrideredirect(True)
        tw.configure(bg="#333")
        tw.attributes("-topmost", True)
        x = app.winfo_rootx() + app.winfo_width() - 320
        y = app.winfo_rooty() + 40
        tw.geometry(f"300x90+{int(x)}+{int(y)}")

        tk.Label(tw, text=title or "Aviso", bg="#333", fg="#fff",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        tk.Label(tw, text=message or "", bg="#333", fg="#fff",
                 font=("Segoe UI", 9), wraplength=280,
                 justify="left").pack(anchor="w", padx=10)
        app.after(5500, tw.destroy)
    except Exception as e:
        print("Popup aviso error:", e)

def _avisos_poller():
    global _last_aviso_ts, _avisos_cache
    try:
        avisos = _read_avisos()

        def _key(a):
            try:
                return datetime.fromisoformat(a.get("ts") or "1970-01-01T00:00:00")
            except Exception:
                return datetime.min

        avisos.sort(key=_key)

        if _last_aviso_ts is None:
            # Primera vez: solo cacheamos, no spameamos popups antiguos
            _avisos_cache = avisos
            if avisos:
                _last_aviso_ts = _key(avisos[-1])
        else:
            for a in avisos:
                ts = _key(a)
                if ts > _last_aviso_ts:
                    # Popup siempre
                    _notify_popup(a.get("titulo", "Aviso"), a.get("mensaje", ""))

                    # Solo mandamos al chat si ya existe el área de chat
                    if "chat_inner" in globals():
                        try:
                            add_message(
                                "MaxiBot",
                                f"🔔 {a.get('titulo','Aviso')}\n{a.get('mensaje','')}",
                                kind="bot"
                            )
                        except Exception as e:
                            print("No se pudo agregar aviso al chat:", e)

                    _avisos_cache.append(a)
                    _last_aviso_ts = ts
    except Exception as e:
        print("Poller avisos:", e)
    finally:
        try:
            app.after(AVISOS_POLL_SEC * 1000, _avisos_poller)
        except Exception:
            pass


def mostrar_avisos_ui():
    win = tk.Toplevel(app)
    win.title("Avisos")
    win.configure(bg=COLORS["card_bg"])
    win.geometry("520x420")

    tk.Label(win, text="Avisos", font=("Segoe UI", 12, "bold"),
             bg=COLORS["card_bg"], fg=COLORS["text_primary"]).pack(
        anchor="w", padx=12, pady=(12, 8)
    )

    frame = tk.Frame(win, bg=COLORS["card_bg"])
    frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    canvas = tk.Canvas(frame, bg=COLORS["card_bg"], highlightthickness=0)
    vscroll = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=COLORS["card_bg"])

    inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _cfg(e):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(inner_id, width=canvas.winfo_width())

    inner.bind("<Configure>", _cfg)
    canvas.configure(yscrollcommand=vscroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    vscroll.pack(side="right", fill="y")

    items = sorted(_avisos_cache, key=lambda a: a.get("ts", ""), reverse=True)
    if not items:
        tk.Label(inner, text="No hay avisos.",
                 font=FONT["body"], bg=COLORS["card_bg"],
                 fg=COLORS["text_secondary"]).pack(anchor="w", pady=8)
        return

    for a in items:
        card = tk.Frame(inner, bg="#fffdf5",
                        highlightthickness=1,
                        highlightbackground="#f0e0b5")
        card.pack(fill="x", pady=6)
        tk.Label(card, text=a.get("titulo","(Sin título)"),
                 font=("Segoe UI", 10, "bold"),
                 bg="#fffdf5", fg=COLORS["text_primary"]).pack(
            anchor="w", padx=10, pady=(8, 2)
        )
        tk.Label(card, text=a.get("mensaje","(Sin mensaje)"),
                 font=FONT["body"], bg="#fffdf5",
                 fg=COLORS["text_primary"],
                 wraplength=460, justify="left").pack(
            anchor="w", padx=10, pady=(0, 8)
        )
        ts = a.get("ts") or ""
        if ts:
            tk.Label(card, text=ts, font=FONT["meta"],
                     bg="#fffdf5", fg=COLORS["text_secondary"]).pack(
                anchor="w", padx=10, pady=(0, 8)
            )

# ===========================
# 🖼️  UI HELPERS
# ===========================
def ensure_scroll_to_bottom():
    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)

def draw_horizontal_gradient(canvas, x1, y1, x2, y2, color1, color2, steps=120):
    r1, g1, b1 = canvas.winfo_rgb(color1)  # 0..65535
    r2, g2, b2 = canvas.winfo_rgb(color2)

    r_ratio = (r2 - r1) / steps
    g_ratio = (g2 - g1) / steps
    b_ratio = (b2 - b1) / steps

    width = max((x2 - x1) / steps, 1)

    for i in range(steps):
        nr16 = int(r1 + (r_ratio * i))
        ng16 = int(g1 + (g_ratio * i))
        nb16 = int(b1 + (b_ratio * i))

        nr = max(0, min(255, nr16 // 256))
        ng = max(0, min(255, ng16 // 256))
        nb = max(0, min(255, nb16 // 256))

        color = f'#{nr:02x}{ng:02x}{nb:02x}'
        canvas.create_rectangle(
            x1 + i * width, y1, x1 + (i + 1) * width, y2,
            outline="", fill=color
        )

def make_chip_label(text, bg, fg=COLORS["chip_text"]):
    return tk.Label(text=text, font=FONT["chip"], bg=bg, fg=fg, padx=8, pady=2)

def sanitize_text(txt: str) -> str:
    return (txt or "").replace("\\n", "\n").strip()

def rounded_rect(c, x1, y1, x2, y2, r, fill):
    c.create_arc(x1, y1, x1 + 2*r, y1 + 2*r, start=90, extent=90,
                 style="pieslice", outline="", fill=fill)
    c.create_arc(x2 - 2*r, y1, x2, y1 + 2*r, start=0, extent=90,
                 style="pieslice", outline="", fill=fill)
    c.create_arc(x2 - 2*r, y2 - 2*r, x2, y2, start=270, extent=90,
                 style="pieslice", outline="", fill=fill)
    c.create_arc(x1, y2 - 2*r, x1 + 2*r, y2, start=180, extent=90,
                 style="pieslice", outline="", fill=fill)
    c.create_rectangle(x1 + r - 1, y1, x2 - r + 1, y2, outline="", fill=fill)
    c.create_rectangle(x1, y1 + r - 1, x2, y2 - r + 1, outline="", fill=fill)

def create_bubble(parent, text, is_user=False):
    wrap = max(int(app.winfo_width() * 0.55), 360)
    pad_x, pad_y, r = 14, 10, 18
    fill = COLORS["user_bubble"] if is_user else COLORS["bot_bubble"]
    fg = COLORS["user_text"] if is_user else COLORS["text_primary"]

    c = tk.Canvas(parent, bg=COLORS["card_bg"], bd=0, highlightthickness=0)
    t = c.create_text(
        pad_x, pad_y,
        text=sanitize_text(text), font=FONT["body"], fill=fg,
        width=wrap, anchor="nw", justify="left"
    )
    c.update_idletasks()
    x1, y1, x2, y2 = c.bbox(t)
    width = x2 - x1 + pad_x*2
    height = y2 - y1 + pad_y*2
    shadow_offset = 3
    shadow_color = "#d0d7e2"
    c.config(width=width + shadow_offset, height=height + shadow_offset)
    rounded_rect(c, shadow_offset, shadow_offset,
                 width + shadow_offset, height + shadow_offset,
                 r, shadow_color)
    rounded_rect(c, 0, 0, width, height, r, fill)
    c.tag_raise(t)
    return c, width + shadow_offset, height + shadow_offset

# ===========================
# 💾 MEMORIA DE CHAT (30 min)
# ===========================
chat_memory = []
_LAST_TOUCH_TS = time.time()
MEMORY_TTL_SEC = 30 * 60  # 30 minutos

def _touch_activity():
    global _LAST_TOUCH_TS
    _LAST_TOUCH_TS = time.time()

def borrar_memoria(auto: bool = False):
    """Limpia la memoria ligera de conversación."""
    global chat_memory
    chat_memory.clear()
    if not auto:
        add_message(
            "MaxiBot",
            "He borrado la memoria temporal de esta sesión. "
            "A partir de ahora comenzamos un nuevo contexto. 🙂",
            kind="bot"
        )

def _idle_watcher():
    """Revisa cada minuto si han pasado 30 min sin actividad para limpiar memoria."""
    try:
        now = time.time()
        if chat_memory and (now - _LAST_TOUCH_TS >= MEMORY_TTL_SEC):
            borrar_memoria(auto=True)
        app.after(60_000, _idle_watcher)
    except Exception:
        pass

# ===========================
# CHAT helpers (usa memoria)
# ===========================
def add_message(who, text, kind="bot"):
    is_user = (kind == "user")
    row = tk.Frame(chat_inner, bg=COLORS["card_bg"])
    row.pack(fill="x", pady=(8, 0), padx=8)

    bubble_parent = tk.Frame(row, bg=COLORS["card_bg"])
    meta_parent = tk.Frame(row, bg=COLORS["card_bg"])

    bubble_parent.pack(anchor="e" if is_user else "w", padx=6)
    meta_parent.pack(anchor="e" if is_user else "w", padx=12, pady=(4, 10))

    c, w, h = create_bubble(bubble_parent, text, is_user=is_user)
    c.pack(anchor="e" if is_user else "w")

    meta = tk.Label(
        meta_parent,
        text=f"{who}  •  {datetime.now().strftime('%H:%M')}",
        font=FONT["meta"], fg=COLORS["text_secondary"],
        bg=COLORS["card_bg"]
    )
    meta.pack(anchor="e" if is_user else "w")

    role = "user" if is_user else "bot"
    chat_memory.append((role, text))
    _touch_activity()

    ensure_scroll_to_bottom()
    return row, meta_parent

def _crear_botones_feedback(parent, idx):
    wrap = tk.Frame(parent, bg=COLORS["card_bg"])
    wrap.pack(anchor="w", pady=(2, 0))

    estado_actual = registro_sesion[idx].get("feedback", "neutral")

    def marcar(valor):
        registro_sesion[idx]["feedback"] = valor
        btn_up.config(font=FONT["btn_small"] if registro_sesion[idx]["feedback"] != "positiva" else ("Segoe UI", 9, "bold"))
        btn_down.config(font=FONT["btn_small"] if registro_sesion[idx]["feedback"] != "negativa" else ("Segoe UI", 9, "bold"))

    btn_up = tk.Button(
        wrap, text="👍", command=lambda: marcar("positiva"),
        bg=COLORS["card_bg"], fg=COLORS["text_primary"],
        relief="flat", bd=0, padx=6, pady=2, font=FONT["btn_small"]
    )
    btn_down = tk.Button(
        wrap, text="👎", command=lambda: marcar("negativa"),
        bg=COLORS["card_bg"], fg=COLORS["text_primary"],
        relief="flat", bd=0, padx=6, pady=2, font=FONT["btn_small"]
    )
    btn_up.pack(side="left")
    btn_down.pack(side="left", padx=(6, 0))

    if estado_actual == "positiva":
        btn_up.config(font=("Segoe UI", 9, "bold"))
    elif estado_actual == "negativa":
        btn_down.config(font=("Segoe UI", 9, "bold"))

# ===========================
# PANTALLAS
# ===========================
def header_card(root, show_chips=True):
    card = tk.Frame(
        root, bg=COLORS["card_bg"],
        highlightthickness=1, highlightbackground=COLORS["divider"]
    )
    card.pack(fill="x", padx=20, pady=(16, 8))

    header_h = 90
    canvas = tk.Canvas(
        card, height=header_h, bg=COLORS["card_bg"],
        bd=0, highlightthickness=0
    )
    canvas.pack(fill="x")
    card.update_idletasks()

    w = max(canvas.winfo_width(), root.winfo_width() - 40, 640)
    draw_horizontal_gradient(
        canvas, 0, 0, w, header_h,
        COLORS["header_grad_start"], COLORS["header_grad_end"]
    )

    pad_left = 20
    logo_size = 56
    gap = 16
    y_logo = max(0, (header_h - logo_size) // 2)
    x_text = pad_left + logo_size + gap

    logo = get_logo(size=logo_size)
    if logo:
        canvas.create_image(pad_left, y_logo, image=logo, anchor="nw")
        if not hasattr(canvas, "_img_refs"):
            canvas._img_refs = []
        canvas._img_refs.append(logo)

    canvas.create_text(
        x_text, y_logo + 6, text="MaxiBot",
        font=FONT["title"], fill="#ffffff", anchor="nw"
    )
    canvas.create_text(
        x_text, y_logo + 36, text="Asistente cálido y modular",
        font=FONT["subtitle"], fill="#e6f4ff", anchor="nw"
    )

    if show_chips:
        chip_texts = [
            ("En línea", COLORS["chip_ok_bg"]),
            ("Modelo v4.6.1", COLORS["chip_bg"]),
            ("Tiempo de respuesta < 2s", COLORS["chip_bg"])
        ]
        spacing = 8
        x = w - 20
        y = 18
        for txt, bg in reversed(chip_texts):
            lbl = make_chip_label(txt, bg)
            lbl.update_idletasks()
            ww = lbl.winfo_reqwidth()
            canvas.create_window(x, y, window=lbl, anchor="ne")
            x -= (ww + spacing)
    return card

def limpiar_pantalla():
    for widget in app.winfo_children():
        widget.destroy()

def mostrar_verificacion():
    limpiar_pantalla()
    header_card(app)

    body = tk.Frame(app, bg=COLORS["app_bg"])
    body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    form = tk.Frame(
        body, bg=COLORS["card_bg"], padx=20, pady=20,
        highlightthickness=1, highlightbackground=COLORS["divider"]
    )
    form.pack(anchor="n", fill="x")

    # ===========================
    # 1) SSO con Keycloak (si está disponible)
    # ===========================
    if _KEYCLOAK_OK:
        tk.Label(
            form,
            text="Inicia sesión con tu cuenta corporativa:",
            font=FONT["body"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_primary"]
        ).pack(pady=(4, 6), anchor="w")

        def _sso_login():
            ok, msg = autenticar_con_keycloak()
            if ok:
                messagebox.showinfo("SSO", msg or "Autenticación correcta.")
                nombre = (
                    usuario_actual.get("nombre")
                    or usuario_actual.get("correo")
                    or "Invitado"
                )
                # Igual que el flujo normal: después del login → Alias → API Key
                mostrar_alias(nombre)
            else:
                messagebox.showerror("SSO", msg or "No se pudo iniciar sesión con SSO.")

        tk.Button(
            form,
            text="Iniciar sesión con SSO (Keycloak)",
            command=_sso_login,
            bg=COLORS["accent"], fg="#fff",
            activebackground=COLORS["accent_dark"],
            activeforeground="#fff",
            relief="flat", bd=0, padx=16, pady=10,
            font=FONT["btn"]
        ).pack(pady=(0, 10), anchor="w")

        tk.Label(
            form,
            text="— o usa tu correo autorizado —",
            font=FONT["meta"],
            bg=COLORS["card_bg"],
            fg=COLORS["text_secondary"]
        ).pack(pady=(0, 10), anchor="w")

    # ===========================
    # 2) Verificación clásica por correo (Sheet)
    # ===========================
    tk.Label(
        form,
        text="Ingresa tu correo registrado:",
        font=FONT["body"],
        bg=COLORS["card_bg"],
        fg=COLORS["text_primary"]
    ).pack(pady=(0, 8), anchor="w")

    entrada_correo = tk.Entry(
        form, font=FONT["body"], width=40, bd=0,
        highlightthickness=1, highlightbackground=COLORS["divider"],
        relief="flat"
    )
    entrada_correo.pack(pady=(0, 10), anchor="w")

    def verificar():
        correo = entrada_correo.get().strip()
        if not correo:
            messagebox.showwarning("Correo requerido", "Por favor, ingresa tu correo.")
            return

        valido, nombre = verificar_correo_online(correo)
        if valido:
            usuario_actual["correo"] = correo
            usuario_actual["nombre"] = nombre
            usuario_actual["sso"] = False
            registrar_ingreso(correo, nombre, "v4.6.1")
            mostrar_alias(nombre)
        else:
            messagebox.showerror(
                "Acceso denegado",
                "Este correo no está autorizado para usar MaxiBot."
            )

    tk.Button(
        form,
        text="Verificar",
        command=verificar,
        bg=COLORS["accent"],
        fg="#fff",
        activebackground=COLORS["accent_dark"],
        activeforeground="#fff",
        relief="flat", bd=0, padx=16, pady=10,
        font=FONT["btn"]
    ).pack(pady=6, anchor="w")



def mostrar_alias(nombre_real):
    limpiar_pantalla()
    header_card(app)

    body = tk.Frame(app, bg=COLORS["app_bg"])
    body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    form = tk.Frame(
        body, bg=COLORS["card_bg"], padx=20, pady=20,
        highlightthickness=1, highlightbackground=COLORS["divider"]
    )
    form.pack(anchor="n", fill="x")

    tk.Label(
        form,
        text=f"¡Hola, {nombre_real}! ¿Cómo quieres que te llame MaxiBot?",
        font=FONT["body"], bg=COLORS["card_bg"],
        fg=COLORS["text_primary"]
    ).pack(pady=(4, 8), anchor="w")

    entrada_alias = tk.Entry(
        form, font=FONT["body"], width=40, bd=0,
        highlightthickness=1, highlightbackground=COLORS["divider"],
        relief="flat"
    )
    entrada_alias.pack(pady=(0, 10), anchor="w")

    def guardar_alias():
        alias = entrada_alias.get().strip()
        if not alias:
            messagebox.showwarning("Alias requerido", "Por favor, ingresa cómo quieres que te llame.")
            return
        usuario_actual["alias"] = alias
        # 👉 Después del alias, pasamos a pedir la API Key
        mostrar_api_key()

    tk.Button(
        form, text="Continuar", command=guardar_alias,
        bg=COLORS["accent"], fg="#fff",
        activebackground=COLORS["accent_dark"],
        activeforeground="#fff",
        relief="flat", bd=0, padx=16, pady=10,
        font=FONT["btn"]
    ).pack(pady=6, anchor="w")

def mostrar_api_key():
    """
    Pantalla para solicitar la API Key (por ejemplo de Gemini).
    La API Key se guarda en la variable global GEMINI_API_KEY.
    """
    limpiar_pantalla()
    header_card(app)

    body = tk.Frame(app, bg=COLORS["app_bg"])
    body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    card = tk.Frame(
        body, bg=COLORS["card_bg"], padx=20, pady=20,
        highlightthickness=1, highlightbackground=COLORS["divider"]
    )
    card.pack(anchor="n", fill="x")

    tk.Label(
        card,
        text="Ingresa tu API Key para que MaxiBot pueda responder:",
        font=("Segoe UI", 11, "bold"),
        bg=COLORS["card_bg"],
        fg=COLORS["text_primary"]
    ).pack(pady=(4, 6), anchor="w")

    tk.Label(
        card,
        text="Solo se usará en esta sesión. Si la dejas vacía, MaxiBot no podrá llamar al modelo.",
        font=FONT["meta"],
        bg=COLORS["card_bg"],
        fg=COLORS["text_secondary"]
    ).pack(pady=(0, 10), anchor="w")

    entrada_key = tk.Entry(
        card, font=FONT["body"], width=50, bd=0,
        highlightthickness=1, highlightbackground=COLORS["divider"],
        relief="flat", show="*"
    )
    entrada_key.pack(pady=(0, 10), anchor="w")

    # Si ya hubiera una API Key definida (por pruebas), puedes precargarla (opcional):
    # if GEMINI_API_KEY:
    #     entrada_key.insert(0, GEMINI_API_KEY)

    def guardar_api_key():
        global GEMINI_API_KEY
        key = entrada_key.get().strip()
        if not key:
            messagebox.showwarning(
                "API Key requerida",
                "Por favor, ingresa una API Key válida para continuar."
            )
            return

        GEMINI_API_KEY = key
        # Opcional: log a consola para saber que se seteo:
        print("✅ API Key establecida para esta sesión.")
        mostrar_bienvenida()

    tk.Button(
        card, text="Continuar", command=guardar_api_key,
        bg=COLORS["accent"], fg="#fff",
        activebackground=COLORS["accent_dark"],
        activeforeground="#fff",
        relief="flat", bd=0, padx=16, pady=10,
        font=FONT["btn"]
    ).pack(pady=6, anchor="w")


def mostrar_bienvenida():
    limpiar_pantalla()
    header_card(app)

    body = tk.Frame(app, bg=COLORS["app_bg"])
    body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    card = tk.Frame(
        body, bg=COLORS["card_bg"], padx=20, pady=20,
        highlightthickness=1, highlightbackground=COLORS["divider"]
    )
    card.pack(fill="x")

    alias = usuario_actual["alias"]
    tk.Label(
        card,
        text=f"¡Perfecto, {alias}! MaxiBot está listo para acompañarte en tu jornada.",
        font=("Segoe UI", 12, "bold"),
        bg=COLORS["card_bg"], fg=COLORS["text_primary"]
    ).pack(pady=6, anchor="w")
    tk.Button(
        card, text="Ir al chat", command=mostrar_chat,
        bg=COLORS["accent"], fg="#fff",
        activebackground=COLORS["accent_dark"],
        activeforeground="#fff",
        relief="flat", bd=0, padx=16, pady=10,
        font=FONT["btn"]
    ).pack(pady=(10, 0), anchor="w")

# ===========================
# CHAT (Rounded bubbles + Scroll)
# ===========================
historial = []
registro_sesion = []

def responder():
    pregunta = entrada_pregunta.get().strip()
    if not pregunta:
        return
    alias = usuario_actual["alias"] or "Usuario"
    add_message(alias, pregunta, kind="user")

    respuesta, origen, hoja, pregunta_web, _ = buscar_respuesta(pregunta, respuestas_por_hoja)

    if origen == "excel":
        registrar_consulta(usuario_actual["correo"], "excel", pregunta)
        row, meta_parent = add_message("MaxiBot", respuesta, kind="bot")
        entrada_pregunta.delete(0, tk.END)

        registro_sesion.append({
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "usuario": usuario_actual["alias"],
            "correo": usuario_actual["correo"],
            "pregunta": pregunta,
            "respuesta": respuesta,
            "origen": "excel",
            "hoja": hoja,
            "feedback": "neutral",
        })
        idx = len(registro_sesion) - 1
        _crear_botones_feedback(meta_parent, idx)
        guardar_conversacion(alias, pregunta, respuesta)

    elif origen == "no_encontrada":
        registrar_consulta(usuario_actual["correo"], "no_encontrada", pregunta)

        # DOCS (Loader) primero
        try:
            doc_hits = docs_tool.search(pregunta, top_k=3)
        except Exception:
            doc_hits = []
        if doc_hits:
            best = max(doc_hits, key=lambda h: float(h.get("score", 0.0)))
            snippet = (best.get("summary") or best.get("content") or "").strip() or "No encontré un pasaje claro en Documentos."
            rowd, metad = add_message("MaxiBot", snippet, kind="bot")
            registro_sesion.append({
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "usuario": usuario_actual["alias"],
                "correo": usuario_actual["correo"],
                "pregunta": pregunta,
                "respuesta": snippet,
                "origen": "DOCS",
                "hoja": None,
                "feedback": "neutral",
            })
            _crear_botones_feedback(metad, len(registro_sesion)-1)
            entrada_pregunta.delete(0, tk.END)
            return

        # MCP después
        if MCP_ENABLED and mcp_tool and mcp_tool.available():
            mcp_hits = mcp_tool.search(pregunta, top_k=3)
            if mcp_hits:
                best = max(mcp_hits, key=lambda h: float(h.get("score", 0.0)))
                snippet = (best.get("content") or "").strip() or "No encontré un pasaje claro en MCP."
                refs = ""
                if best.get("url"):
                    refs = f"\n\nFuente: {best.get('title','MCP')} — {best.get('url')}"
                rowm, metam = add_message("MaxiBot", (snippet + refs).strip(), kind="bot")
                registro_sesion.append({
                    "timestamp": datetime.now().isoformat(timespec='seconds'),
                    "usuario": usuario_actual["alias"],
                    "correo": usuario_actual["correo"],
                    "pregunta": pregunta,
                    "respuesta": (snippet + refs).strip(),
                    "origen": "MCP",
                    "hoja": None,
                    "feedback": "neutral",
                })
                _crear_botones_feedback(metam, len(registro_sesion)-1)
                entrada_pregunta.delete(0, tk.END)
                return

        # WEB (confirmación)
        info = ("No encontré esa respuesta en mi base de conocimiento.\n"
                "¿Quieres que busque en la web?")
        row, meta_parent = add_message("MaxiBot", info, kind="bot")

        ctrls = tk.Frame(meta_parent, bg=COLORS["card_bg"])
        ctrls.pack(anchor="w", pady=(2, 0))

        def _buscar_web():
            prompt = (
                "Resume en 5-7 líneas lo más relevante que encontrarías en la web "
                "sobre la consulta. Incluye 2-4 referencias con título y URL "
                "(si no tienes URLs, usa 'N/A').\n"
                f"Consulta: {pregunta}" + ANTI_HALLUCINATION_NOTE
            )
            respuesta_web = buscar_con_gemini(prompt)
            registrar_consulta(usuario_actual["correo"], "web", pregunta)
            row2, meta2 = add_message("MaxiBot", respuesta_web, kind="bot")
            guardar_en_hoja_aprendida(pregunta, respuesta_web)
            registro_sesion.append({
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "usuario": usuario_actual["alias"],
                "correo": usuario_actual["correo"],
                "pregunta": pregunta,
                "respuesta": respuesta_web,
                "origen": "WEB",
                "hoja": None,
                "feedback": "neutral",
            })
            idx2 = len(registro_sesion) - 1
            _crear_botones_feedback(meta2, idx2)
            guardar_conversacion(alias, pregunta, respuesta_web)
            for w in ctrls.winfo_children():
                w.destroy()

        def _no_buscar():
            for w in ctrls.winfo_children():
                w.destroy()

        tk.Button(
            ctrls, text="Buscar en la web", command=_buscar_web,
            bg=COLORS["accent"], fg="#fff", relief="flat", bd=0,
            padx=10, pady=6, font=FONT["btn_small"]
        ).pack(side="left")
        tk.Button(
            ctrls, text="No, gracias", command=_no_buscar,
            bg="#f1f5f9", fg=COLORS["text_primary"], relief="flat", bd=0,
            padx=10, pady=6, font=FONT["btn_small"]
        ).pack(side="left", padx=(8, 0))

        entrada_pregunta.delete(0, tk.END)

def mostrar_chat():
    global chat_canvas, chat_inner, chat_inner_id, entrada_pregunta
    limpiar_pantalla()
    header_card(app)

    body = tk.Frame(app, bg=COLORS["app_bg"])
    body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    card_shadow = tk.Frame(body, bg="#d0d7e2")
    card_shadow.pack(fill="both", expand=True)
    chat_card = tk.Frame(
        card_shadow, bg=COLORS["card_bg"],
        highlightthickness=1, highlightbackground=COLORS["divider"]
    )
    chat_card.pack(fill="both", expand=True, padx=2, pady=2)

    title_bar = tk.Frame(chat_card, bg=COLORS["card_bg"])
    title_bar.pack(fill="x", padx=16, pady=(12, 0))
    tk.Label(
        title_bar, text="Chat", font=("Segoe UI", 11, "bold"),
        bg=COLORS["card_bg"], fg=COLORS["text_primary"]
    ).pack(side="left")

    holder = tk.Frame(chat_card, bg=COLORS["card_bg"])
    holder.pack(fill="both", expand=True, padx=12, pady=12)

    chat_canvas_local = tk.Canvas(
        holder, bg=COLORS["card_bg"], highlightthickness=0
    )
    vscroll = tk.Scrollbar(holder, orient="vertical", command=chat_canvas_local.yview)
    chat_canvas_local.configure(yscrollcommand=vscroll.set)

    vscroll.pack(side="right", fill="y")
    chat_canvas_local.pack(side="left", fill="both", expand=True)

    chat_canvas = chat_canvas_local
    chat_inner = tk.Frame(chat_canvas, bg=COLORS["card_bg"])
    chat_inner_id = chat_canvas.create_window((0, 0), window=chat_inner, anchor="nw")

    def _on_frame_config(event):
        chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
        chat_canvas.itemconfig(chat_inner_id, width=chat_canvas.winfo_width())

    chat_inner.bind("<Configure>", _on_frame_config)

    add_message("MaxiBot", "¡Hola! ¿En qué puedo ayudarte hoy?", kind="bot")

    input_bar = tk.Frame(chat_card, bg=COLORS["card_bg"])
    input_bar.pack(fill="x", padx=12, pady=(0, 12))

    entrada_pregunta = tk.Entry(
        input_bar, font=FONT["body"], relief="flat",
        highlightthickness=1, highlightbackground=COLORS["divider"]
    )
    entrada_pregunta.pack(side="left", padx=(0, 8), ipady=8, fill="x", expand=True)
    entrada_pregunta.bind("<Return>", lambda e: responder())

    tk.Button(
        input_bar, text="Responder", command=responder,
        bg=COLORS["accent"], fg="#fff",
        activebackground=COLORS["accent_dark"],
        activeforeground="#fff",
        relief="flat", bd=0, padx=16, pady=10,
        font=FONT["btn"]
    ).pack(side="left")

    btn_row = tk.Frame(chat_card, bg=COLORS["card_bg"])
    btn_row.pack(fill="x", padx=12, pady=(0, 12))

    tk.Button(
        btn_row, text="Actualizar base", command=actualizar_base,
        bg="#e6f2ff", fg=COLORS["text_primary"],
        relief="flat", bd=0, padx=12, pady=6,
        font=FONT["btn_small"]
    ).pack(side="left", padx=(0, 8))

    tk.Button(
        btn_row, text="Borrar memoria", command=lambda: borrar_memoria(auto=False),
        bg="#ffecec", fg=COLORS["text_primary"],
        relief="flat", bd=0, padx=12, pady=6,
        font=FONT["btn_small"]
    ).pack(side="left", padx=(0, 8))

    tk.Button(
        btn_row, text="Avisos", command=mostrar_avisos_ui,
        bg="#fff4d6", fg=COLORS["text_primary"],
        relief="flat", bd=0, padx=12, pady=6,
        font=FONT["btn_small"]
    ).pack(side="left", padx=(0, 8))

    tk.Button(
        btn_row, text="Cargar carpeta (Loader)",
        command=lambda: cargar_loader(),
        bg="#e9e9ff", fg=COLORS["text_primary"],
        relief="flat", bd=0, padx=12, pady=6,
        font=FONT["btn_small"]
    ).pack(side="left", padx=(0, 8))

    def _logout():
        # Si vienes de SSO, cerramos también en Keycloak
        if usuario_actual.get("sso"):
            cerrar_sesion_keycloak()
        else:
            usuario_actual["correo"] = None
            usuario_actual["nombre"] = None
            usuario_actual["alias"] = None
            usuario_actual["sso"] = False

        borrar_memoria(auto=True)
        mostrar_verificacion()

    tk.Button(
        btn_row, text="Cerrar sesión",
        command=_logout,
        bg="#ffe4e6", fg=COLORS["text_primary"],
        relief="flat", bd=0, padx=12, pady=6,
        font=FONT["btn_small"]
    ).pack(side="right", padx=(8, 0))


def cargar_loader():
    """Refresca el índice del Loader (DocsTool) manualmente."""
    try:
        n = docs_tool.refresh()
        messagebox.showinfo("Loader", f"Índice actualizado ({n} documentos).")
    except Exception as e:
        messagebox.showerror("Loader", f"No se pudo refrescar el índice: {e}")

def actualizar_base():
    global respuestas_por_hoja
    respuestas_por_hoja = cargar_todas_las_respuestas()
    try:
        docs_tool.refresh()
    except Exception as e:
        print("Aviso: no se pudo refrescar DocsTool:", e)
    messagebox.showinfo("Actualizado", "La base de datos se ha actualizado correctamente.")
    mostrar_chat()

def guardar_manual():
    win = tk.Toplevel(app)
    win.title("Guardar respuesta")
    win.configure(bg=COLORS["card_bg"])

    tk.Label(
        win, text="Pregunta:", font=FONT["body"],
        bg=COLORS["card_bg"], fg=COLORS["text_primary"]
    ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
    ent_q = tk.Entry(win, font=FONT["body"], width=60)
    ent_q.grid(row=0, column=1, padx=10, pady=(10, 4))

    tk.Label(
        win, text="Respuesta:", font=FONT["body"],
        bg=COLORS["card_bg"], fg=COLORS["text_primary"]
    ).grid(row=1, column=0, sticky="nw", padx=10, pady=(4, 10))
    txt_a = tk.Text(win, font=FONT["body"], width=60, height=8)
    txt_a.grid(row=1, column=1, padx=10, pady=(4, 10))

    if registro_sesion:
        ent_q.insert(0, registro_sesion[-1].get("pregunta", ""))
        txt_a.insert("1.0", registro_sesion[-1].get("respuesta", ""))

    def _guardar():
        pregunta = ent_q.get().strip()
        respuesta = txt_a.get("1.0", "end").strip()
        if not pregunta or not respuesta:
            messagebox.showwarning("Campos requeridos", "Ingresa pregunta y respuesta.")
            return
        try:
            df = pd.DataFrame([{
                "pregunta": pregunta,
                "respuesta": respuesta,
                "correo": usuario_actual.get("correo"),
                "alias": usuario_actual.get("alias"),
            }])
            filename = f"guardado_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_bytes = df.to_csv(index=False, encoding="utf-8").encode("utf-8")
            svc = _drive_service()
            media = MediaIoBaseUpload(io.BytesIO(csv_bytes), mimetype="text/csv", resumable=False)
            meta = {"name": filename, "mimeType": "text/csv", "parents": [DRIVE_NEWRESP_FOLDER_ID]}
            f = svc.files().create(
                body=meta, media_body=media,
                supportsAllDrives=True, fields="id, webViewLink"
            ).execute()
            messagebox.showinfo("Listo", "Se guardó y subió el CSV correctamente.")
            win.destroy()
        except Exception as e:
            asegurar_carpeta_csv()
            archivo = os.path.join(
                CSV_FOLDER,
                f"guardado_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            df.to_csv(archivo, index=False, encoding="utf-8")
            messagebox.showwarning(
                "Aviso",
                f"No se pudo subir a Drive ({e}). Se guardó local en:\n{archivo}"
            )

    tk.Button(
        win, text="Guardar", command=_guardar,
        bg=COLORS["accent"], fg="#fff", relief="flat", bd=0,
        padx=12, pady=8, font=FONT["btn"]
    ).grid(row=2, column=1, sticky="e", padx=10, pady=(0, 10))

# ===========================
# 🚀 APP INIT
# ===========================
respuestas_por_hoja = cargar_todas_las_respuestas()
crear_base()
historial = []
registro_sesion = []

app = tk.Tk()
app.title("MaxiBot v4.6.1 – Asistente cálido y modular")
app.geometry("880x640")
app.configure(bg=COLORS["app_bg"])
app.protocol("WM_DELETE_WINDOW", lambda: cerrar_app())

_touch_activity()
app.after(60_000, _idle_watcher)
app.after(AVISOS_POLL_SEC * 1000, _avisos_poller)

mostrar_verificacion()
app.mainloop()
