# hades_1.6_integrado_full_v4_patched_limpio_final_corregido_v3.py
# ------------------------------------------------------------------
# HADES 1.6 — Integrado (FULL v4, Drive patched, Normalización Estricta Final o ya no se que version va jajajaja :) ups)
# • VERIFICACIÓN: Corregida normalización de fechas DD MM YYYY (Pasaporte MX).
# • OCR con Gemini Visión (REST): Analizar actual / Analizar carrusel.
# • EXPORTACIÓN: Salida de OCR forzada a usar fechas normalizadas en la UI.
# ------------------------------------------------------------------

import os, sys, re, io, base64, time, datetime, json, requests, tempfile, unicodedata
import threading
import queue
import gc
try:
    import google.generativeai as genai
except Exception:
    genai = None
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import webbrowser  # Para abrir hipervínculos
# pandas se importará con lazy loading en las funciones que lo usan

# ===== POLICY TEMPLATES (Compliance 2025) =====
try:
    from policy_templates import classify_document, policy_score_adjustment
    _POLICY_TEMPLATES_OK = True
except Exception as e:
    print(f"[HADES] Advertencia: No se pudo cargar policy_templates: {e}")
    _POLICY_TEMPLATES_OK = False
    classify_document = None
    policy_score_adjustment = None

# ===== KEYCLOAK SSO =====
_KEYCLOAK_OK = False
keycloak_auth_instance = None
try:
    from keycloak_auth import KeycloakAuth
    _KEYCLOAK_OK = True
except Exception:
    _KEYCLOAK_OK = False
    KeycloakAuth = None

# ==============================================================================
# ===== INICIO: BLOQUE DE TKINTER Y DND (CORRECCIÓN NameError) =====
# ==============================================================================

# --- Tk / UI ---
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, Toplevel, Label, Button, Frame, ttk
from PIL import Image, ImageTk, ImageGrab, Image as PILImage
from difflib import SequenceMatcher

_DND_OK = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    _DND_OK = True
except Exception:
    _DND_OK = False

# ==============================================================================
# ===== FIN: BLOQUE DE TKINTER Y DND =====
# ==============================================================================


# ====== HADES: Detección de país / normalización de fechas / vigencia ======
# Diccionario expandido con nombres completos y abreviados de meses en español
_MONTHS_ES = {
    # Nombres completos
    "enero":1, "febrero":2, "marzo":3, "abril":4, "mayo":5, "junio":6,
    "julio":7, "agosto":8, "septiembre":9, "setiembre":9, "octubre":10, "noviembre":11, "diciembre":12,
    # Abreviaciones de 3 letras
    "ene":1, "feb":2, "mar":3, "abr":4, "may":5, "jun":6,
    "jul":7, "ago":8, "sep":9, "oct":10, "nov":11, "dic":12
}
_MONTHS_EN = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,"july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
             "jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"aug":8,"sep":9,"sept":9,"oct":10,"nov":11,"dec":12,
             "ene":1, "feb":2, "mar":3, "abr":4, "may":5, "jun":6, "jul":7, "ago":8, "sep":9, "oct":10, "nov":11, "dic":12} # Añadido para 3 letras Español/Inglés


# --- Normalización robusta de meses (multi-idioma / sin acentos) ---
def _strip_accents(s: str) -> str:
    """Elimina acentos/diacríticos manteniendo letras latinas (útil para meses en múltiples idiomas)."""
    if not s:
        return ""
    try:
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    except Exception:
        return s

def _norm_month_token(mon: str) -> str:
    """Normaliza el token de mes: minúsculas, sin acentos y solo letras."""
    if not mon:
        return ""
    mon = _strip_accents(mon).lower().strip()
    mon = re.sub(r'[^a-z]', '', mon)
    return mon

# Meses adicionales (FR/PT/DE/IT/NL) + romanos (I-XII)
_MONTHS_FR = {
    "janvier": 1, "janv": 1, "jan": 1,
    "fevrier": 2, "fevr": 2, "fev": 2,
    "mars": 3, "mar": 3,
    "avril": 4, "avr": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7, "juil": 7,
    "aout": 8,
    "septembre": 9, "sept": 9,
    "octobre": 10, "oct": 10,
    "novembre": 11, "nov": 11,
    "decembre": 12, "dec": 12,
}
_MONTHS_PT = {
    "janeiro": 1, "jan": 1,
    "fevereiro": 2, "fev": 2,
    "marco": 3, "mar": 3,
    "abril": 4, "abr": 4,
    "maio": 5, "mai": 5,
    "junho": 6, "jun": 6,
    "julho": 7, "jul": 7,
    "agosto": 8, "ago": 8,
    "setembro": 9, "set": 9,
    "outubro": 10, "out": 10,
    "novembro": 11, "nov": 11,
    "dezembro": 12, "dez": 12,
}
_MONTHS_DE = {
    "januar": 1, "jan": 1,
    "februar": 2, "feb": 2,
    "marz": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mai": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "dezember": 12, "dez": 12,
}
_MONTHS_IT = {
    "gennaio": 1, "gen": 1,
    "febbraio": 2, "feb": 2,
    "marzo": 3, "mar": 3,
    "aprile": 4, "apr": 4,
    "maggio": 5, "mag": 5,
    "giugno": 6, "giu": 6,
    "luglio": 7, "lug": 7,
    "agosto": 8, "ago": 8,
    "settembre": 9, "set": 9,
    "ottobre": 10, "ott": 10,
    "novembre": 11, "nov": 11,
    "dicembre": 12, "dic": 12,
}
_MONTHS_NL = {
    "januari": 1, "jan": 1,
    "februari": 2, "feb": 2,
    "maart": 3, "mrt": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mei": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "augustus": 8, "aug": 8,
    "september": 9, "sep": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}
_MONTHS_ROMAN = {
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6,
    "vii": 7, "viii": 8, "ix": 9, "x": 10, "xi": 11, "xii": 12,
}

# Diccionario unificado
_MONTHS_ALL: Dict[str, int] = {}
for _d in (_MONTHS_ES, _MONTHS_EN, _MONTHS_FR, _MONTHS_PT, _MONTHS_DE, _MONTHS_IT, _MONTHS_NL, _MONTHS_ROMAN):
    for _k, _v in _d.items():
        _MONTHS_ALL[_norm_month_token(_k)] = int(_v)

_COUNTRY_CUES = {
    # ****************** LISTA COMPLETA  ******************
    # MEJORA DE PRIORIDAD (GT y PH subidos)
    "GT": ["guatemala", "guatemalteca", "republica de guatemala", "identificacion consular", "documento personal de identificación", "pasaporte guatemala", "país emisor: gtm", "registro nacional de las personas"],
    "PH": ["pasaporte", "republic of the philippines", "republika ng pilipinas", "código de país: phl", "filipino"], # Filipinas
    "MX": ["ine","instituto nacional electoral","credencial para votar","clave de elector","curp","rfc","licencia de conducir", "pasaporte", "matrícula consular", "estados unidos mexicanos", "clave del país de expedición: mex"],
    "HN": ["registro nacional de las personas", "pasaporte", "honduras"],
    "CO": ["cédula de ciudadanía", "cedula de ciudadania", "pasaporte", "republica de colombia"],
    "PE": ["dni", "documento nacional de identidad", "pasaporte", "peru", "república del perú"],
    "NI": ["consejo supremo electoral", "pasaporte", "nicaragua"],
    "SV": ["documento único de identidad", "dui", "pasaporte", "el salvador"],
    "EC": ["cédula de ciudadanía", "pasaporte", "ecuador"],
    "DO": ["república dominicana", "pasaporte"],
    "VE": ["matrícula consular", "venezuela"],
    "US": ["united states","usa","state of","driver license","dl class","id card","department of motor vehicles","dmv","ssn","uscis","passport of the united states"],
    "ES": ["dni","nif","número de soporte","ministerio del interior","reino de españa","pasaporte español"],
    "AR": ["dni","registro nacional de las personas","república argentina","republica argentina"],
    "BR": ["cpf", "rg", "carteira de identidade", "carteira nacional de habilitação", "cnh", "registro geral", "documento de identidade", "passaporte", "república federativa do brasil"],
    "CL": ["rut", "rol único tributario", "cédula de identidad", "pasaporte", "república de chile"],
    "PY": ["cédula de identidad civil", "pasaporte", "república del paraguay"],
    "UY": ["cédula de identidad", "documento de identidad", "pasaporte", "república oriental del uruguay"],
    "BO": ["cédula de identidad", "pasaporte", "estado plurinacional de bolivia"],
    "CR": ["cédula de identidad", "documento de identidad", "pasaporte", "república de costa rica"],
    "PA": ["cédula de identidad personal", "pasaporte", "república de panamá"],
    "CU": ["carné de identidad", "pasaporte", "república de cuba"],
    "HT": ["carte d'identité nationale", "pasaporte", "république d'haïti"],
    "JM": ["national id", "electoral id", "passport", "jamaica"],
    "TT": ["national id card", "passport", "trinidad and tobago"],
    "PK": ["cnic", "computerized national identity card", "national identity card", "passport","tarjeta de identidad nacional", "pakistan"],
    "IL": ["teudat zehut", "תעודת זהות", "israeli id", "passport", "state of israel", "מדינת ישראל"],
    "VN": ["căn cước công dân",  # Tarjeta de identificación ciudadana (CCCD)
           "chứng minh nhân dân",  # Documento de identidad anterior (CMND)
           "giấy chứng minh nhân dân",
           "giấy tờ tùy thân",
           "hộ chiếu",  # Pasaporte
           "social insurance book", "republic of vietnam", "vietnam"],
}

_DATE_RE_TXT_ES = re.compile(r'\b(\d{1,2})\s*(?:de\s*)?([A-Za-záéíóúÁÉÍÓÚñÑ]+)\s*(?:de\s*)?(\d{2,4})\b', re.IGNORECASE)

# -- Patrones textuales y numéricos
_DATE_RE_TXT_EN_DMY = re.compile(r'\b(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{2,4})\b', re.IGNORECASE)
_DATE_RE_TXT_EN_MDY = re.compile(r'\b([A-Za-z]{3,})\s+(\d{1,2})\s+(\d{2,4})\b', re.IGNORECASE)
_DATE_RE_TXT_EN = re.compile(r'\b([A-Za-z]+)\s+(\d{1,2}),\s*(\d{2,4})\b', re.IGNORECASE)
_DATE_RE_NUM_A = re.compile(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b')
_DATE_RE_ISO = re.compile(r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b')
_DATE_RE_DMY_H = re.compile(r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b')  # 🆕 FASE 4: Cambiado a 2-4 dígitos

# --- Patrones extra: "MES-DD-YYYY" y "DD-MES-YYYY"
_DATE_RE_EN_MON_DD_YYYY_H = re.compile(r'\b([A-Za-z]{3,})[-/](\d{1,2})[-/](\d{2,4})\b', re.IGNORECASE)
_DATE_RE_EN_DD_MON_YYYY_H = re.compile(r'\b(\d{1,2})[-/]([A-Za-z]{3,})[-/](\d{2,4})\b', re.IGNORECASE)

# Patrón para DD MM YYYY (separado por espacios, como el Pasaporte MX)
_DATE_RE_DD_MM_YYYY_SPACE = re.compile(r'\b(\d{1,2})\s+(\d{1,2})\s+(\d{2,4})\b')  # 🆕 FASE 4: Cambiado a 2-4 dígitos

# Patrón para Pasaportes (DD MON / MON YY) - e.g., 30 NOV / NOV 86
_DATE_RE_TXT_PASSPORT = re.compile(r'\b(\d{1,2})\s*([A-Za-z]{3,})\s*/\s*(?:[A-Za-z]{3,}\s*)?(\d{2,4})\b', re.IGNORECASE)

# 🆕 Patrón para Pasaportes con slashes entre todos los tokens (DD/MON/MON/YYYY)
_DATE_RE_TXT_PASSPORT_SLASH4 = re.compile(r'\b(\d{1,2})/([A-Za-z]{3,})/(?:([A-Za-z]{3,})/)?(\d{2,4})\b', re.IGNORECASE)

# 🆕 Patrón para DDMONYYYY (Guatemala DPI)
_DATE_RE_DMMMYYYY = re.compile(r'\b(\d{1,2})([A-Za-z]{3,})(\d{4})\b', re.IGNORECASE)

# 🆕 Patrón para DD MON/MES YYYY (Honduras, Matrículas Consulares) - e.g., "14 ENE 1975", "14 JAN 1975"
_DATE_RE_DD_MON_YYYY = re.compile(r'\b(\d{1,2})\s+([A-Z]{3})[/\s]+(\d{4})\b', re.IGNORECASE)

# Patrón para rangos de año 2022 - 2032 (para INE)
_DATE_RE_YEAR_RANGE = re.compile(r'(\d{4})\s*[-\u2013]\s*(\d{4})')

# 🆕 Patrón para año solo (Matrículas Consulares - fecha de vencimiento)
_DATE_RE_YEAR_ONLY = re.compile(r'\b(20\d{2})\b')  # Solo años 2000-2099

# 🆕 FASE 1: Nuevos patrones para mejorar detección de fechas
# Patrón para MM/YYYY (ej. 03/2027 - Venezuela)
_DATE_RE_MM_YYYY = re.compile(r'(?<!\d[\/-])\b(\d{1,2})[\/-](\d{4})\b')

# Patrón para DD.MM.YYYY (ej. 30.10.2000, 18.10.2030 - Costa Rica)
_DATE_RE_DD_MM_YYYY_DOT = re.compile(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b')

# Patrón mejorado para fechas textuales en español con guiones (ej. 31-ago-2027, 15 agosto 1994)
_DATE_RE_TXT_ES_FULL = re.compile(r'\b(\d{1,2})[-\s]+([a-záéíóúñ]+)[-\s]+(\d{2,4})\b', re.IGNORECASE)


def _clean_ocr_output(texto: str) -> str:
    """Elimina líneas generadas internamente por HADES que se colaron en el output de Gemini."""
    if not texto:
        return ""
    # Regex para buscar la línea de metadatos internos, incluyendo el patrón: [DOCUMENTO] país: XX — formato detectado: XXXXXX
    cleaned = re.sub(r'\[DOCUMENTO\]\s*país:\s*[A-Z]{2}\s*—\s*formato\s*detectado:\s*.*', '', texto, flags=re.IGNORECASE).strip()
    return cleaned


# ====== Traducción de etiquetas de campos al español ======
# Mapeo inglés → español para etiquetas de campos de documentos de identidad.
# Se aplica al texto OCR cuando Gemini devuelve campos en otro idioma.
_ID_LABEL_TRANSLATIONS: dict = {
    # --- Identificación personal ---
    "surname"                   : "Apellido",
    "last name"                 : "Apellido",
    "last names"                : "Apellidos",
    "first name"                : "Nombre",
    "first names"               : "Nombres",
    "given name"                : "Nombre",
    "given names"               : "Nombres",
    "middle name"               : "Segundo Nombre",
    "full name"                 : "Nombre Completo",
    "name"                      : "Nombre",
    "names"                     : "Nombres",
    "father's surname"          : "Apellido Paterno",
    "father surname"            : "Apellido Paterno",
    "mother's surname"          : "Apellido Materno",
    "mother surname"            : "Apellido Materno",
    # --- Fechas ---
    "date of birth"             : "Fecha de Nacimiento",
    "birth date"                : "Fecha de Nacimiento",
    "dob"                       : "Fecha de Nacimiento",
    "date of issue"             : "Fecha de Expedición",
    "issue date"                : "Fecha de Expedición",
    "issued"                    : "Fecha de Expedición",
    "date of expiry"            : "Fecha de Vencimiento",
    "date of expiration"        : "Fecha de Vencimiento",
    "expiry date"               : "Fecha de Vencimiento",
    "expiration date"           : "Fecha de Vencimiento",
    "expiry"                    : "Vencimiento",
    "expiration"                : "Vencimiento",
    "expires"                   : "Vence",
    "valid thru"                : "Válido Hasta",
    "valid through"             : "Válido Hasta",
    "valid until"               : "Válido Hasta",
    "validity"                  : "Vigencia",
    # --- Tipo de documento ---
    "document type"             : "Tipo de Documento",
    "type of document"          : "Tipo de Documento",
    "document class"            : "Clase de Documento",
    "class"                     : "Clase",
    "dl class"                  : "Clase de Licencia",
    "id type"                   : "Tipo de ID",
    "card type"                 : "Tipo de Tarjeta",
    # --- Número de documento ---
    "document number"           : "Número de Documento",
    "document no"               : "Número de Documento",
    "id number"                 : "Número de Identificación",
    "id no"                     : "Número de Identificación",
    "passport number"           : "Número de Pasaporte",
    "passport no"               : "Número de Pasaporte",
    "passport no."              : "Número de Pasaporte",
    "license number"            : "Número de Licencia",
    "licence number"            : "Número de Licencia",
    "license no"                : "Número de Licencia",
    "licence no"                : "Número de Licencia",
    "driver license number"     : "Número de Licencia",
    "driver's license number"   : "Número de Licencia",
    "serial number"             : "Número de Serie",
    "serie"                     : "Serie",
    "folio"                     : "Folio",
    "control number"            : "Número de Control",
    # --- Tipo de documento (nombre) ---
    "passport"                  : "Pasaporte",
    "driver license"            : "Licencia de Conducir",
    "driver's license"          : "Licencia de Conducir",
    "driving license"           : "Licencia de Conducir",
    "driving licence"           : "Licencia de Conducir",
    "identity card"             : "Cédula de Identidad",
    "national identity card"    : "Cédula de Identidad Nacional",
    "national id"               : "Identificación Nacional",
    "permanent resident card"   : "Tarjeta de Residente Permanente",
    "residence permit"          : "Permiso de Residencia",
    "resident card"             : "Tarjeta de Residente",
    # --- País / Nacionalidad ---
    "country"                   : "País",
    "issuing country"           : "País Emisor",
    "issuing state"             : "Estado Emisor",
    "issuing authority"         : "Autoridad Emisora",
    "nationality"               : "Nacionalidad",
    "citizenship"               : "Ciudadanía",
    "place of birth"            : "Lugar de Nacimiento",
    "country of birth"          : "País de Nacimiento",
    # --- Datos físicos ---
    "sex"                       : "Sexo",
    "gender"                    : "Género",
    "height"                    : "Estatura",
    "weight"                    : "Peso",
    "eye color"                 : "Color de Ojos",
    "eye colour"                : "Color de Ojos",
    "hair color"                : "Color de Cabello",
    "hair colour"               : "Color de Cabello",
    # --- Dirección ---
    "address"                   : "Dirección",
    "street"                    : "Calle",
    "city"                      : "Ciudad",
    "state"                     : "Estado",
    "zip code"                  : "Código Postal",
    "postal code"               : "Código Postal",
    # --- Otros campos comunes ---
    "restrictions"              : "Restricciones",
    "endorsements"              : "Endosos",
    "organ donor"               : "Donador de Órganos",
    "veteran"                   : "Veterano",
    "signature"                 : "Firma",
    "mrz"                       : "MRZ",
    "machine readable zone"     : "Zona de Lectura Mecánica",
    "notes"                     : "Notas",
    "observations"              : "Observaciones",
    "remarks"                   : "Observaciones",
    "personal number"           : "Número Personal",
    "social security number"    : "Número de Seguro Social",
    "ssn"                       : "Número de Seguro Social",
    "tax id"                    : "Número Fiscal",
    "tax identification"        : "Identificación Fiscal",
}

# Compilamos un regex de reemplazo (case-insensitive) para eficiencia.
# Solo reemplaza la CLAVE de la línea (antes del primer ":"), no el valor.
_ID_LABEL_TRANS_RE = re.compile(
    r'^(' + '|'.join(re.escape(k) for k in sorted(_ID_LABEL_TRANSLATIONS, key=len, reverse=True)) + r')\s*:',
    re.IGNORECASE | re.MULTILINE
)


def _translate_field_labels_to_spanish(texto: str) -> str:
    """
    Traduce las etiquetas/claves de campos de documentos de identidad al español.

    - Solo actúa sobre la parte IZQUIERDA del separador ":" en cada línea.
    - Preserva el valor original sin modificarlo.
    - Si la etiqueta ya estaba en español, la deja intacta.
    """
    if not texto:
        return texto

    def _replace(m: re.Match) -> str:
        original_key = m.group(1)
        translated   = _ID_LABEL_TRANSLATIONS.get(
            original_key.lower(),
            _ID_LABEL_TRANSLATIONS.get(original_key, original_key)
        )
        return f"{translated}:"

    return _ID_LABEL_TRANS_RE.sub(_replace, texto)


# --- Heurística robusta para inferir país del documento ---
# Nota: muchas palabras como "pasaporte"/"passport" aparecen en TODOS los países, así que
# se tratan como señales de baja confianza para evitar falsos positivos.
_GENERIC_COUNTRY_CUES = {
    "pasaporte", "passport",
    "dni", "cedula", "cédula", "identidad", "id card",
    "documento", "tarjeta",
    "licencia de conducir", "driver license", "driver's license",
}

def _iso3_to_iso2(code: str) -> Optional[str]:
    """Convierte ISO-3166 alpha-3 -> alpha-2 cuando sea posible.

    - Si ya viene en 2 letras, lo devuelve.
    - Si no se puede convertir, devuelve None.
    """
    if not code:
        return None
    c = str(code).strip().upper()
    if len(c) == 2 and c.isalpha():
        return c
    if len(c) != 3 or not c.isalpha():
        return None

    # Intento con pycountry (si está instalado)
    try:
        import pycountry  # type: ignore
        country = pycountry.countries.get(alpha_3=c)
        if country and getattr(country, "alpha_2", None):
            return country.alpha_2
    except Exception:
        pass

    # Fallback mínimo
    fallback = {
        "USA": "US",
        "MEX": "MX",
        "VEN": "VE",
        "PRY": "PY",
        "GTM": "GT",
        "PHL": "PH",
        "COL": "CO",
        "PER": "PE",
        "ECU": "EC",
        "BRA": "BR",
        "ARG": "AR",
        "ESP": "ES",
        "FRA": "FR",
        "DEU": "DE",
        "ITA": "IT",
        "GBR": "GB",
        "CAN": "CA",
        "CHN": "CN",
        "JPN": "JP",
        "KOR": "KR",
        "IND": "IN",
        "AUS": "AU",
    }
    return fallback.get(c)

def _infer_doc_country(texto: str):
    """Intenta inferir el país emisor del documento (ISO-2) usando múltiples señales.

    Prioridad:
      1) MRZ de pasaporte (P<XXX)
      2) Campos explícitos tipo "País Emisor: XXX" / "Issuing State: XXX"
      3) Score por _COUNTRY_CUES (ponderado; evita que "pasaporte" domine)
      4) Campo débil "País: XX" como último recurso
    """
    raw = (texto or "")
    if not raw.strip():
        return None

    # 1) MRZ de pasaporte: P<XXX
    m = re.search(r"\bP<([A-Z]{3})", raw, re.IGNORECASE)
    if m:
        iso3 = m.group(1).upper()
        iso2 = _iso3_to_iso2(iso3)
        if iso2:
            return iso2

    # Normalizamos texto para búsquedas (sin acentos)
    t_norm = _strip_accents(raw)

    # 2) Campo explícito de país emisor (alta confianza)
    m = re.search(
        r"(?:pa[ií]s\s*(?:emisor|de\s*emisi[oó]n)|issuing\s*(?:state|country)|country\s*code)\s*[:\-]\s*([A-Z]{2,3})\b",
        t_norm,
        re.IGNORECASE,
    )
    if m:
        code = m.group(1).upper()
        iso2 = _iso3_to_iso2(code)
        if iso2:
            return iso2

    # 4) Campo débil: "País: XX"
    weak_country = None
    m = re.search(r"\bpa[ií]s\s*[:\-]\s*([A-Z]{2,3})\b", t_norm, re.IGNORECASE)
    if m:
        code = m.group(1).upper()
        weak_country = _iso3_to_iso2(code) or weak_country

    # 3) Score por cues (ponderado)
    t_low = _strip_accents(raw).lower()
    best_cc = None
    best_score = 0.0

    for cc, cues in _COUNTRY_CUES.items():
        score = 0.0
        for cue in cues:
            cue_n = _strip_accents(cue).lower()
            if not cue_n:
                continue
            if cue_n in t_low:
                if cue_n in _GENERIC_COUNTRY_CUES:
                    score += 0.2
                else:
                    score += min(3.0, 0.5 + (len(cue_n) / 12.0))
        if score > best_score:
            best_score = score
            best_cc = cc

    # Umbral mínimo para evitar falsos positivos (ej. solo "pasaporte")
    if best_cc and best_score >= 0.6:
        return best_cc

    return weak_country
def _detect_language_bias(texto: str):
    t = (texto or "").lower()
    score_es = sum(1 for m in _MONTHS_ES if m in t)
    score_en = sum(1 for m in _MONTHS_EN if m in t)
    return "ES" if score_es >= score_en and score_es>0 else ("EN" if score_en>0 else None)

def _coerce_year(y) -> Optional[int]:
    """Convierte un año (int o str) a formato YYYY.

    - Si viene en 2 dígitos: 00-49 -> 2000-2049, 50-99 -> 1950-1999.
    - Si no es convertible a número, devuelve None.

    Nota: muchas regex devuelven los grupos como *strings*, por eso esta función
    debe ser tolerante.
    """
    if y is None:
        return None
    try:
        yi = int(str(y).strip())
    except Exception:
        return None
    if yi < 0:
        return None
    if yi < 100:
        return 2000 + yi if yi < 50 else 1900 + yi
    return yi


def _normalize_date_to_mdy_ctx(s: str, country_ctx: Optional[str], lang_ctx: Optional[str]) -> Optional[str]:
    """
    Convierte una fecha (potencialmente en múltiples formatos) a MM/DD/YYYY.
    Reglas clave:
      - Si solo viene un AÑO (YYYY) -> 12/31/YYYY
      - Soporta DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, YYYY-MM-DD, formatos con mes en texto (multi-idioma),
        y fechas con espacios (ej. "05 / 06 / 2020").
      - Para formatos numéricos ambiguos (05/06/2020) se decide por heurística (país/idioma).
    """
    if not s:
        return None

    st0 = str(s).strip()
    if not st0:
        return None

    # Normalizar separadores raros y espacios alrededor de separadores
    st0 = st0.replace("／", "/").replace("–", "-").replace("—", "-").replace("−", "-").replace("‐", "-")
    st0 = re.sub(r"\s+", " ", st0).strip()
    st0 = re.sub(r"\s*([/\-\.])\s*", r"\1", st0)

    # Trabajamos sin acentos para soportar meses FR/PT/DE/IT/NL, etc.
    st = _strip_accents(st0)

    # 0) Si viene un rango de años, tomamos el año final (ej. 2020-2029 -> 2029)
    m_range = _DATE_RE_YEAR_RANGE.search(st)
    if m_range:
        st = m_range.group(2)

    # 1) Solo año (YYYY) -> 12/31/YYYY
    if re.fullmatch(r"\d{4}", st):
        try:
            y = int(st)
            if 1900 <= y <= 2099:
                return f"12/31/{y:04d}"
        except ValueError:
            pass

    # 2) Solo mes/año (MM/YYYY o MM-YYYY) -> MM/31/YYYY (día 31 fijo por requerimiento)
    m = _DATE_RE_MM_YYYY.fullmatch(st)
    if m:
        mm, yyyy = m.groups()
        try:
            mi = int(mm)
            yi = int(yyyy)
            if 1 <= mi <= 12 and 1900 <= yi <= 2099:
                return f"{mi:02d}/31/{yi:04d}"
        except Exception:
            pass

    # 3) DD.MM.YYYY -> MM/DD/YYYY
    m = _DATE_RE_DD_MM_YYYY_DOT.search(st)
    if m:
        da, mo, y = m.groups()
        y_int = _coerce_year(y)
        if y_int:
            try:
                di = int(da)
                mi = int(mo)
                if 1 <= mi <= 12 and 1 <= di <= 31:
                    return f"{mi:02d}/{di:02d}/{y_int:04d}"
            except ValueError:
                pass

    # 4) Pasaporte: DD MON / MON YY  (ej. "30 NOV / NOV 86" o "30NOV/NOV86")
    m = _DATE_RE_TXT_PASSPORT.search(st)
    if m:
        da, mon, y = m.groups()
        mo = _MONTHS_ALL.get(_norm_month_token(mon))
        y_int = _coerce_year(y)
        if mo and y_int:
            try:
                di = int(da)
                if 1 <= di <= 31:
                    return f"{mo:02d}/{di:02d}/{y_int:04d}"
            except ValueError:
                pass

    
    # 4b) Pasaporte con slashes entre todos los tokens: DD/MON/MON/YYYY (ej. 18/Sep/Sep/1999)
    m = _DATE_RE_TXT_PASSPORT_SLASH4.search(st)
    if m:
        da, mon1, mon2, y = m.groups()
        mon_pick = mon1
        mo = _MONTHS_ALL.get(_norm_month_token(mon_pick)) or (_MONTHS_ALL.get(_norm_month_token(mon2)) if mon2 else None)
        y_int = _coerce_year(y)
        if mo and y_int:
            try:
                di = int(da)
                if 1 <= di <= 31:
                    return f"{mo:02d}/{di:02d}/{y_int:04d}"
            except ValueError:
                pass

# 5) Si hay letras y '/', muchas veces es texto tipo "15/AGO/2020"
    st_text = st
    if "/" in st and re.search(r"[A-Za-z]", st):
        st_text = st.replace("/", " ")

    # 6) 31-ago-2027 / 31 ago 2027 (mes en texto)
    m = _DATE_RE_TXT_ES_FULL.search(st_text)
    if m:
        da, mon, y = m.groups()
        mo = _MONTHS_ALL.get(_norm_month_token(mon))
        y_int = _coerce_year(y)
        if mo and y_int:
            try:
                di = int(da)
                if 1 <= di <= 31:
                    return f"{mo:02d}/{di:02d}/{y_int:04d}"
            except ValueError:
                pass

    # 7) DD de MES de YYYY / DDMESYYYY / DD MES YYYY (ES/varios)
    m = _DATE_RE_TXT_ES.search(st_text)
    if m:
        da, mon, y = m.groups()
        mo = _MONTHS_ALL.get(_norm_month_token(mon))
        y_int = _coerce_year(y)
        if mo and y_int:
            try:
                di = int(da)
                if 1 <= di <= 31:
                    return f"{mo:02d}/{di:02d}/{y_int:04d}"
            except ValueError:
                pass

    # 8) DD MON YYYY (3+ letras) / DD MON/YYYY (capturado por st_text)
    m = _DATE_RE_DD_MON_YYYY.search(st_text)
    if m:
        da, mon, y = m.groups()
        mo = _MONTHS_ALL.get(_norm_month_token(mon))
        y_int = _coerce_year(y)
        if mo and y_int:
            try:
                di = int(da)
                if 1 <= di <= 31:
                    return f"{mo:02d}/{di:02d}/{y_int:04d}"
            except ValueError:
                pass

    # 9) Mes en texto con formato inglés "Mon 15, 2020" o "15 Mon 2020"
    for rx, is_mdy in ((_DATE_RE_TXT_EN_MDY, True), (_DATE_RE_TXT_EN_DMY, False), (_DATE_RE_TXT_EN, True),
                       (_DATE_RE_EN_MON_DD_YYYY_H, True), (_DATE_RE_EN_DD_MON_YYYY_H, False)):
        m = rx.search(st)
        if not m:
            continue

        g = m.groups()
        # Variantes: (mon, day, year) o (day, mon, year)
        if len(g) != 3:
            continue
        if is_mdy:
            mon, da, y = g
        else:
            da, mon, y = g

        mo = _MONTHS_ALL.get(_norm_month_token(mon))
        y_int = _coerce_year(y)
        if mo and y_int:
            try:
                di = int(da)
                if 1 <= di <= 31:
                    return f"{mo:02d}/{di:02d}/{y_int:04d}"
            except ValueError:
                pass

    # 10) ISO YYYY-MM-DD -> MM/DD/YYYY
    m = _DATE_RE_ISO.search(st)
    if m:
        y, mo, da = m.groups()
        y_int = _coerce_year(y)
        if y_int:
            try:
                mi = int(mo)
                di = int(da)
                if 1 <= mi <= 12 and 1 <= di <= 31:
                    return f"{mi:02d}/{di:02d}/{y_int:04d}"
            except ValueError:
                pass

    # 11) DD-MM-YYYY (o con /) -> MM/DD/YYYY
    m = _DATE_RE_DMY_H.search(st)
    if m:
        da, mo, y = m.groups()
        y_int = _coerce_year(y)
        if y_int:
            try:
                di = int(da)
                mi = int(mo)
                if 1 <= mi <= 12 and 1 <= di <= 31:
                    return f"{mi:02d}/{di:02d}/{y_int:04d}"
            except ValueError:
                pass

    # 12) Numérico general: A/B/YYYY donde puede ser MDY o DMY
    m = _DATE_RE_NUM_A.search(st)
    if m:
        a, b, y = m.groups()
        y_int = _coerce_year(y)
        if y_int:
            try:
                ai = int(a)
                bi = int(b)
            except ValueError:
                ai = bi = None

            if ai is not None and bi is not None:
                # Unambiguous
                if ai > 12 and bi <= 12:
                    # DMY
                    day, month = ai, bi
                elif bi > 12 and ai <= 12:
                    # MDY
                    month, day = ai, bi
                else:
                    # Ambiguo: decide por contexto (US -> MDY, ES/otros -> DMY por defecto)
                    prefer_dmy = (country_ctx not in {"US"} or lang_ctx == "ES")
                    if prefer_dmy:
                        day, month = ai, bi
                    else:
                        month, day = ai, bi

                if 1 <= month <= 12 and 1 <= day <= 31:
                    return f"{month:02d}/{day:02d}/{y_int:04d}"

    return None

def _extract_all_dates(text: str):
    """
    Extrae TODAS las fechas detectables del texto.
    Importante: antes de aplicar regex, normaliza separadores para capturar casos con espacios:
      "05 / 06 / 2020" -> "05/06/2020"
    """
    if not text:
        return []
    t = str(text)
    t = t.replace("／", "/").replace("–", "-").replace("—", "-").replace("−", "-").replace("‐", "-")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s*([/\-\.])\s*", r"\1", t)
    t = _strip_accents(t)

    hits = []
    # Incluimos un patrón para DDMMMYYYY (como 24JUN2019) y también DDMMMMYY/AAAA
    custom_ddmmyyyy = re.compile(r'\b(\d{1,2})([A-Z]{3,})(\d{2,4})\b', re.IGNORECASE)

    for rx in (
        _DATE_RE_TXT_ES, _DATE_RE_TXT_ES_FULL,
        _DATE_RE_TXT_EN, _DATE_RE_TXT_EN_DMY, _DATE_RE_TXT_EN_MDY,
        _DATE_RE_EN_MON_DD_YYYY_H, _DATE_RE_EN_DD_MON_YYYY_H,
        _DATE_RE_ISO, _DATE_RE_DMY_H, _DATE_RE_DD_MM_YYYY_DOT, _DATE_RE_NUM_A,
        _DATE_RE_DD_MM_YYYY_SPACE, _DATE_RE_TXT_PASSPORT, _DATE_RE_TXT_PASSPORT_SLASH4,
        _DATE_RE_YEAR_RANGE, _DATE_RE_MM_YYYY, _DATE_RE_DMMMYYYY,
        _DATE_RE_DD_MON_YYYY,
        custom_ddmmyyyy,
    ):
        for m in rx.finditer(t):
            hits.append((m.group(0), m.start()))

    hits.sort(key=lambda x: x[1])
    return [h[0] for h in hits]

def _normalize_all_dates_with_pairs(text: str):
    """Mantenida solo por retrocompatibilidad en el exportador/diagnóstico."""
    if not text: return text, [], None, None
    doc_pais = _infer_doc_country(text)
    lang = _detect_language_bias(text)
    
    originals = _extract_all_dates(text)
    pairs = []
    for d in originals:
        norm = _normalize_date_to_mdy_ctx(d, doc_pais, lang)
        if norm and (d, norm) not in pairs:
            pairs.append((d, norm))
    
    return text, pairs, doc_pais, "MIXTO/UNKNOWN"


def _add_years_safe(d, years):
    try:
        return d.replace(year=d.year + years)
    except Exception:
        if d.month == 2 and d.day == 29:
            return d.replace(month=2, day=28, year=d.year + years)
        import datetime as _dt; return d + _dt.timedelta(days=365*years)
    
def _process_all_dates_by_type(texto: str) -> Dict[str, Optional[str]]:
    """
    Procesa el texto OCR aplicando reglas estrictas de normalización.

    ✅ Fix principal: ahora detecta fechas con espacios alrededor de separadores
       (ej. "05 / 06 / 2020") y las normaliza.

    Reglas ESPECIALES para vigencia/caducidad/expiración "incompletas":
      1) Solo AÑO (YYYY) -> 12/31/YYYY   (NO sugerida)
      2) Solo MES/AÑO (MM/YYYY) -> MM/31/YYYY  (NO sugerida; día 31 fijo por requerimiento)
      3) Si no hay día/mes/año -> hoy + 5 años (Sugerida)

    Para el resto de fechas:
      - Se intenta convertir a MM/DD/YYYY desde formatos comunes.
      - Regla USA: si YA viene en MM/DD/YYYY, se muestra tal cual (solo compactamos espacios).
    """
    import datetime as _dt

    doc_pais = _infer_doc_country(texto)
    is_usa_id = (doc_pais in ("US", "USA"))
    lang = _detect_language_bias(texto)

    results: Dict[str, Optional[str]] = {
        "doc_pais": doc_pais,
        "fecha_vigencia_final": None,
        "fecha_expedicion_final": None,
        "fecha_nacimiento_final": None,
        "otras_fechas_normalizadas": "",
        "vigencia_sugerida": None,
        "exp_date_mdy_for_sug": None,
        "nombre": None,
        "tipo_identificacion": None,
    }

    vigencia_keywords = [
        "vencimiento", "vence", "expiración", "expiracion", "vigencia",
        "valido hasta", "válido hasta", "valid thru", "valid through", "valid until",
        "caducidad", "fecha de caducidad",
        "expires", "expire", "expiry", "expiration", "date of expiry", "date of expiration",
    ]
    expedicion_keywords = [
        "emision", "expedicion", "expedición", "issue", "issued",
        "fecha de emision", "date of issue", "fecha de expedicion", "emitido", "fecha de emi",
    ]
    nacimiento_keywords = ["fecha de nacimiento", "dob", "date of birth", "nacimient[oa]"]

    seen_originals = set()
    kv_map: Dict[str, str] = {}

    def _compact_seps(x: str) -> str:
        """Compacta separadores (quita espacios alrededor) y normaliza unicode/díacriticos."""
        if not x:
            return ""
        x = str(x)
        x = x.replace("／", "/").replace("–", "-").replace("—", "-").replace("−", "-").replace("‐", "-")
        x = re.sub(r"\s+", " ", x).strip()
        x = re.sub(r"\s*([/\-\.])\s*", r"\1", x)
        x = _strip_accents(x)
        return x

    def _is_american_numeric_date(val: str) -> bool:
        """Detecta fechas numéricas estilo USA: MM/DD/YY(YY) o MM-DD-YY(YY).

        Importante: aquí NO reinterpretamos DD/MM. Solo validamos rangos básicos
        para poder *preservar* el formato original en documentos de USA.
        """
        if not val:
            return False
        v = _compact_seps(val)
        m = re.fullmatch(r"(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2,4})", v)
        if not m:
            return False
        try:
            mm = int(m.group(1))
            dd = int(m.group(2))
            return 1 <= mm <= 12 and 1 <= dd <= 31
        except Exception:
            return False


    def _vigencia_normalizada(original: str) -> Tuple[Optional[str], bool]:
        """
        Aplica SOLO las reglas especiales de vigencia/caducidad/expiración incompleta.
        Devuelve (fecha_final, es_sugerida).
        """
        o = _compact_seps(original)
        if not o:
            return None, False

        # Regla USA: si ya viene como fecha numérica americana (MM/DD/YY o MM/DD/YYYY),
        # NO se formaliza (solo compactamos espacios). Esto evita cambiar 02/04/30 -> 02/04/2030.
        if is_usa_id and _is_american_numeric_date(o):
            return o, False

        # 1) Rango de años -> usar año final (NO sugerida)
        rm = _DATE_RE_YEAR_RANGE.search(o)
        if rm:
            y_str = rm.group(2)
            base = _normalize_date_to_mdy_ctx(y_str, doc_pais, lang)
            return base, False

        # 2) Solo año -> 12/31/YYYY (NO sugerida)
        if re.fullmatch(r"\d{4}", o):
            base = _normalize_date_to_mdy_ctx(o, doc_pais, lang)
            return base, False

        # 3) Solo mes/año -> MM/31/YYYY (NO sugerida)
        mm_yyyy = _DATE_RE_MM_YYYY.fullmatch(o)
        if mm_yyyy:
            mm, yyyy = mm_yyyy.groups()
            try:
                mi = int(mm)
                yi = int(yyyy)
                if 1 <= mi <= 12 and 1900 <= yi <= 2099:
                    return f"{mi:02d}/31/{yi:04d}", False
            except Exception:
                pass

        # 4) Fecha completa u otros formatos -> normalización normal
        base = _normalize_date_to_mdy_ctx(o, doc_pais, lang)
        return base, False

    def process_and_assign_date(original: str, date_type: str) -> str:
        nonlocal results

        original = original or ""
        original_c = _compact_seps(original)

        # Detecta si ya viene como fecha numérica estilo USA (MM/DD/YY o MM/DD/YYYY).
        # Esto se usa para PRESERVAR el formato original en documentos de USA.
        is_us_numeric = _is_american_numeric_date(original_c)

        if date_type == "vigencia":
            base, is_sug = _vigencia_normalizada(original_c)
            final_date = base or original_c or original

            if is_sug and "Sugerida" not in final_date:
                final_date = f"{final_date} (Sugerida)"
                results["vigencia_sugerida"] = final_date

            results["fecha_vigencia_final"] = final_date
            seen_originals.add(original)
            return final_date

        # Para el resto de tipos:
        if is_usa_id and is_us_numeric:
            # USA y ya está en formato americano: no se modifica (solo compactamos espacios)
            final_date = original_c
        else:
            final_date = _normalize_date_to_mdy_ctx(original_c or original, doc_pais, lang) or (original_c or original)

        results[f"fecha_{date_type}_final"] = final_date

        if date_type == "expedicion":
            # Guarda por si se usa para lógica adicional
            results["exp_date_mdy_for_sug"] = final_date

        seen_originals.add(original)
        return final_date

    # --- 1) Scan de pares clave: valor ---
    for line in texto.splitlines():
        ll = line.lower().strip()
        kv_match = re.search(r'([a-záéíóúñ\s]+):\s*(.*)', ll, re.IGNORECASE)
        if not kv_match:
            continue

        key = kv_match.group(1).strip()
        value = kv_match.group(2).strip()

        # Nombre / tipo (sin cambiar)
        if "nombre" in key and "padre" not in key and not results.get("nombre"):
            results["nombre"] = value
        if "tipo" in key and ("documento" in key or "tarjeta" in key) and not results.get("tipo_identificacion"):
            results["tipo_identificacion"] = value

        # Compactamos el value para que los regex encuentren "05 / 06 / 2020"
        value_norm = _compact_seps(value)

        all_regexes = (
            _DATE_RE_NUM_A, _DATE_RE_ISO, _DATE_RE_DMY_H, _DATE_RE_DD_MM_YYYY_DOT,
            _DATE_RE_EN_MON_DD_YYYY_H, _DATE_RE_EN_DD_MON_YYYY_H,
            _DATE_RE_TXT_EN_MDY, _DATE_RE_TXT_EN_DMY, _DATE_RE_TXT_ES, _DATE_RE_TXT_ES_FULL,
            _DATE_RE_DD_MM_YYYY_SPACE, _DATE_RE_TXT_PASSPORT, _DATE_RE_TXT_PASSPORT_SLASH4, _DATE_RE_YEAR_RANGE,
            _DATE_RE_MM_YYYY, _DATE_RE_DMMMYYYY, _DATE_RE_DD_MON_YYYY,
        )

        original_date_match = None
        for rx in all_regexes:
            dm = rx.search(value_norm)
            if dm:
                original_date_match = dm.group(0)
                break

        if not original_date_match:
            continue

        original = original_date_match

        is_vig = any(k in key for k in vigencia_keywords) and not results["fecha_vigencia_final"]
        is_exp = any(k in key for k in expedicion_keywords) and not results["fecha_expedicion_final"]
        is_nac = any(re.search(k, key) for k in nacimiento_keywords) and not results["fecha_nacimiento_final"]

        date_type = None
        if is_vig:
            date_type = "vigencia"
        elif is_exp:
            date_type = "expedicion"
        elif is_nac:
            date_type = "nacimiento"

        if date_type:
            final_date = process_and_assign_date(original, date_type)
            kv_map[key] = final_date
        else:
            # Otras fechas: normaliza (excepto regla USA si ya es fecha numérica americana)
            original_c = _compact_seps(original)
            if is_usa_id and _is_american_numeric_date(original_c or original):
                kv_map[key] = original_c or original
            else:
                norm = _normalize_date_to_mdy_ctx(original_c or original, doc_pais, lang)
                kv_map[key] = norm or (original_c or original)

    # --- 2) Fallback: vigencia si no se encontró en pares clave:valor ---
    if not results["fecha_vigencia_final"]:
        for line in texto.splitlines():
            ll = line.lower()
            if not any(k in ll for k in vigencia_keywords):
                continue

            candidates = _extract_all_dates(line)
            chosen = None

            # Prioridad A: fechas completas (con día)
            for cand in candidates:
                cand_str = _compact_seps(cand or "")
                if not cand_str:
                    continue
                if _DATE_RE_YEAR_RANGE.search(cand_str):
                    continue
                if re.fullmatch(r"\d{4}", cand_str):
                    continue
                if _DATE_RE_MM_YYYY.fullmatch(cand_str):
                    continue  # se maneja en prioridad B

                base = _normalize_date_to_mdy_ctx(cand_str, doc_pais, lang)
                if base:
                    chosen = base
                    break

            # Prioridad B: MM/YYYY -> MM/31/YYYY (día 31 fijo)
            if not chosen:
                for cand in candidates:
                    cand_str = _compact_seps(cand or "")
                    if _DATE_RE_MM_YYYY.fullmatch(cand_str):
                        try:
                            mm, yyyy = _DATE_RE_MM_YYYY.fullmatch(cand_str).groups()
                            mi = int(mm)
                            yi = int(yyyy)
                            if 1 <= mi <= 12 and 1900 <= yi <= 2099:
                                chosen = f"{mi:02d}/31/{yi:04d}"
                                break
                        except Exception:
                            pass

            # Prioridad C: rango de años o solo año -> 12/31/YYYY (NO sugerida)
            if not chosen:
                range_match = _DATE_RE_YEAR_RANGE.search(_strip_accents(line))
                year_match = re.search(r"\b(19\d{2}|20\d{2})\b", _strip_accents(line))
                if range_match:
                    y_str = range_match.group(2)
                    chosen = _normalize_date_to_mdy_ctx(y_str, doc_pais, lang)
                elif year_match:
                    y_str = year_match.group(1)
                    chosen = _normalize_date_to_mdy_ctx(y_str, doc_pais, lang)

            if chosen:
                results["fecha_vigencia_final"] = chosen
                break

        # Intento final: si NO se encontró nada, sugerir hoy + 5 años (Sugerida)
        if not results["fecha_vigencia_final"]:
            try:
                sugerida_dt = _dt.date.today()
                sugerida_dt = _add_years_safe(sugerida_dt, 5)
                sugerida_str = f"{sugerida_dt.strftime('%m/%d/%Y')} (Sugerida)"
                results["vigencia_sugerida"] = sugerida_str
                results["fecha_vigencia_final"] = sugerida_str
            except Exception:
                pass

    # --- 3) Pasada global: convierte TODAS las fechas numéricas DD/MM/AAAA → MM/DD/AAAA ---
    # Solo aplica a documentos NO-USA. Los documentos USA ya vienen en MM/DD/YYYY.
    # Se construye un mapa {original: convertida} que el renderizador usa para sustituir
    # en todo el texto visible, incluyendo líneas sin separador ":" y valores libres.
    date_substitution_map: Dict[str, str] = {}

    # Regex para capturar fechas numéricas con separador / - .
    # Captura: DD/MM/YYYY, D/M/YYYY, DD-MM-YYYY, DD.MM.YYYY y variantes con año 2 dígitos.
    _RE_NUMERIC_DATE_GLOBAL = re.compile(
        r'\b(\d{1,2})([\\/\-\.])(\d{1,2})\2(\d{2,4})\b'
    )

    if not is_usa_id:
        for m_dt in _RE_NUMERIC_DATE_GLOBAL.finditer(texto):
            original_raw = m_dt.group(0)
            sep          = m_dt.group(2)
            part1        = int(m_dt.group(1))   # podría ser DD
            part2        = int(m_dt.group(3))   # podría ser MM
            year_raw     = m_dt.group(4)

            # Saltar si ya fue procesada o si es ambigua y ambas partes son ≤ 12
            # Regla: si part1 > 12 → definitivamente DD (día). Caso contrario asumimos DD/MM
            # (convención global no-USA).
            if part1 > 31 or part2 > 12:
                continue   # valores imposibles, no es fecha válida
            if part1 < 1 or part2 < 1:
                continue

            year_int = _coerce_year(year_raw)
            if not year_int:
                continue

            # Decidimos: part1 = día, part2 = mes (formato DD/MM/YYYY)
            dd = part1
            mm = part2

            # Solo convertir si el resultado difiere del original
            converted = f"{mm:02d}/{dd:02d}/{year_int:04d}"
            original_normalizado = f"{dd:02d}{sep}{mm:02d}{sep}{year_raw}"

            # Evitar "convertir" lo que ya está en MM/DD (sería igual en forma)
            # Si dd > 12 es inequívoco: el primer número ES día → hay que invertir
            # Si dd <= 12 también invertimos (convención no-USA = DD primero)
            if converted != original_raw:
                date_substitution_map[original_raw] = converted

    # Incluir también en kv_map para que _format_ocr_text llegue a ellas por clave
    # (en líneas con formato "Clave: DD/MM/YYYY" que no hayan sido detectadas antes)
    for orig_date, conv_date in date_substitution_map.items():
        # Solo agregar si la fecha original aparece como valor en alguna línea no procesada
        for line in texto.splitlines():
            if ":" in line and orig_date in line:
                parts = line.split(":", 1)
                key_raw = parts[0].strip().lower()
                # Si la clave aún no está en kv_map, agregamos la conversión
                from unicodedata import normalize as _unorm
                key_clean_local = re.sub(r'\s+', ' ', re.sub(r'[.,:;_\-]+', ' ',
                    ''.join(c for c in _unorm('NFD', key_raw)
                             if _unorm('NFC', c) == c or True
                    ).lower())).strip()
                if key_clean_local not in kv_map:
                    kv_map[key_clean_local] = conv_date

    results["date_substitution_map"] = date_substitution_map

    # Limpieza + extra
    try:
        del results["exp_date_mdy_for_sug"]
    except Exception:
        pass

    results["kv_map"] = kv_map
    return results

# ------------------------------------------------------------------------------
# Patrones auxiliares (evita NameError y permite extracción de nombre/DOB/MX)
# ------------------------------------------------------------------------------

_NAME_HINTS = [
    # Captura el valor después de NOMBRE/NAME/TITULAR/NOMBRES/APELLIDOS
    r"(?:nombre|names|nombres)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s'.-]+?)(?:\s+(APELLIDOS|SURNAME|DIRECCION|CALLE))?$",
    r"(?:apellidos|surname)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s'.-]+?)(?:\s+(NOMBRES|NAMES|FECHA))?$",
    r"(?:nombre|name|titular)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s'.-]+)",  # Fallback más simple
]

_DOB_HINTS = [
    r"(?:fecha\s*de\s*nacimiento|f\.\s*de\s*nac\.?|dob|date\s*of\s*birth|nacimient[oa])"
]

# México (compatibilidad): CURP y RFC
_CURP_RE = re.compile(r"\b([A-Z][AEIOUX][A-Z]{2})(\d{2})(\d{2})(\d{2})[HM][A-Z]{5}[0-9A-Z]\d\b", re.IGNORECASE)
_RFC_PER_RE = re.compile(r"\b([A-ZÑ&]{4})(\d{2})(\d{2})(\d{2})[A-Z0-9]{3}\b", re.IGNORECASE)

# Palabras típicas de documento de muestra
_SAMPLE_WORDS = ("muestra", "sample", "specimen", "ejemplo", "void")

def _extract_id_number(texto: str, doc_pais: str | None) -> str | None:
    if not texto: return None
    
    # Normalizamos el texto (espacios internos y saltos de línea para búsqueda de claves)
    t_searchable = texto.upper().replace('\n', ' ')
    t_clean = t_searchable.replace(' ', '').replace('-', '')
    
    # 🆕 FASE 3: Detección específica por país (antes de keywords genéricos)
    
    # Colombia: NUIP (10 dígitos)
    if doc_pais == "CO":
        # Buscar "NUIP" o "NÚMERO ÚNICO DE IDENTIFICACIÓN PERSONAL" seguido de 10 dígitos
        nuip_match = re.search(r'(?:NUIP|NUMERO\s*UNICO|IDENTIFICACION\s*PERSONAL)[:\s-]*(\d{10})\b', t_searchable)
        if nuip_match:
            return nuip_match.group(1)
        # Fallback: buscar cualquier secuencia de 10 dígitos
        nuip_fallback = re.search(r'\b(\d{10})\b', t_clean)
        if nuip_fallback:
            return nuip_fallback.group(1)
    
    # Ecuador: NUI/Cédula (10 dígitos)
    if doc_pais == "EC":
        # Buscar "NUI" o "CÉDULA" seguido de 10 dígitos
        nui_match = re.search(r'(?:NUI|CEDULA|IDENTIFICACION)[:\s-]*(\d{10})\b', t_searchable)
        if nui_match:
            return nui_match.group(1)
        # Fallback: buscar cualquier secuencia de 10 dígitos
        nui_fallback = re.search(r'\b(\d{10})\b', t_clean)
        if nui_fallback:
            return nui_fallback.group(1)
    
    # Bolivia: Cédula de Identidad (7-8 dígitos + extensión opcional)
    if doc_pais == "BO":
        # Buscar "CÉDULA" o "CI" seguido de 7-8 dígitos
        bo_match = re.search(r'(?:CEDULA|CI|IDENTIDAD)[:\s-]*(\d{7,8}(?:-?\d{1,2})?)\b', t_searchable)
        if bo_match:
            return bo_match.group(1).replace('-', '')
        # Fallback: buscar secuencia de 7-8 dígitos
        bo_fallback = re.search(r'\b(\d{7,8})\b', t_clean)
        if bo_fallback:
            return bo_fallback.group(1)
    
    # Brasil: CPF (11 dígitos) o RG (7-9 dígitos)
    if doc_pais == "BR":
        # Buscar CPF (formato: XXX.XXX.XXX-XX o 11 dígitos)
        cpf_match = re.search(r'(?:CPF)[:\s-]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})\b', t_searchable)
        if cpf_match:
            return cpf_match.group(1).replace('.', '').replace('-', '')
        # Buscar RG
        rg_match = re.search(r'(?:RG|REGISTRO\s*GERAL)[:\s-]*(\d{7,9})\b', t_searchable)
        if rg_match:
            return rg_match.group(1)
        # Fallback: buscar 11 dígitos (CPF) o 7-9 dígitos (RG)
        br_fallback = re.search(r'\b(\d{11})\b', t_clean)
        if br_fallback:
            return br_fallback.group(1)
        br_rg_fallback = re.search(r'\b(\d{7,9})\b', t_clean)
        if br_rg_fallback:
            return br_rg_fallback.group(1)
    
    # Prioridad 1: Claves específicas de identificación
    keywords_num = [
        "PASAPORTE N.", "NÚMERO DE PASAPORTE", "PASSPORT NO", "NÚMERO DE PASAPORTE", 
        "NÚMERO DE LICENCIA", "NO. LICENCIA", "NÚMERO DE SERIE",
        "NÚMERO DE MATRÍCULA", "MATRÍCULA CONSULAR",
        "CÓDIGO ÚNICO DE IDENTIFICACIÓN", "CUI", # DPI Guatemala
        "DNI", "DPI", "ID NUMBER", "CLAVE DE ELECTOR", 
        "NÚMERO DE IDENTIFICACIÓN", "NÚMERO"
    ]
    
    for kw in keywords_num:
        # Buscamos la clave, permitiendo ":", "-" o un espacio como separador, seguido de [A-Z0-9\-]
        # Nota: El regex ahora busca el valor y lo trata como RAW STRING.
        line_match = re.search(f"{kw.replace(' ', ' ?')}\\s*[:\\-]?\\s*([A-Z0-9\\-]+)", t_searchable)
        
        if line_match:
            val = line_match.group(1).strip()
            clean_val = val.replace(' ', '').replace('-', '')

            # Caso específico DPI/CUI (Guatemala): Buscamos 13 dígitos
            if kw in ["CÓDIGO ÚNICO DE IDENTIFICACIÓN", "CUI"] and re.match(r'^\d{13}$', clean_val):
                return clean_val

            # Caso General: Validamos longitud y limpiamos sufijos de texto indeseados (como 'NOMBRE')
            if clean_val and len(clean_val) >= 8:
                # Intento de limpieza de texto colado (ej. 'NOMBRE', 'APELLIDO')
                clean_val_final = re.sub(r'[A-ZÑ]+$', '', clean_val) 
                if len(clean_val_final) >= 8:
                    return clean_val_final

    # Prioridad 2: Claves reguladas (CURP, RFC)
    if doc_pais == "MX":
        curp_match = _CURP_RE.search(t_clean)
        if curp_match: return curp_match.group(0)
        rfc_match = _RFC_PER_RE.search(t_clean)
        if rfc_match: return rfc_match.group(0)

    # Fallback: Capturar el Número de Control del documento (Licencia de Conducir, etc.)
    match_long_num = re.search(r'\b([A-Z0-9]{8,25})\b', t_clean)
    if match_long_num:
        return match_long_num.group(1) if not match_long_num.group(1).isdigit() or len(match_long_num.group(1)) > 8 else None

    return None

def _extract_id_type(texto: str, doc_pais: str | None) -> str | None:
    if not doc_pais: return None
    t = texto.lower()
    
    # 1. Por País y tipo específico (prioridad alta)
    if doc_pais == "MX":
        if any(kw in t for kw in ["credencial para votar", "ine"]): return "Credencial INE (MX)"
        if "matrícula consular" in t: return "Matrícula Consular (MX)"
        if "pasaporte" in t and "mex" in t: return "Pasaporte (MX)"
    if doc_pais == "GT":
        if "documento personal de identificación" in t or "dpi" in t: return "DPI (GT)"
        if "identificacion consular" in t: return "Identificación Consular (GT)"
        if "pasaporte" in t: return "Pasaporte (GT)"
    if doc_pais == "PH":
        return "Pasaporte (PH)"
    if doc_pais == "US":
        if any(kw in t for kw in ["driver license", "licencia de conducir"]): return "Licencia de Conducir (US)"
    
    # 2. Por palabras clave genéricas (si no se resolvió antes)
    if "pasaporte" in t or "passport" in t: return "Pasaporte"
    if "licencia de conducir" in t or "driver license" in t: return "Licencia de Conducir"
    
    return None
# --- Fin funciones de extracción de ID ---

def _extract_name(texto: str) -> str | None:
    if not texto: return None
    t = texto.upper()
    
    # Diccionario para almacenar los nombres y apellidos encontrados
    name_parts = {"apellidos": None, "nombres": None, "segundo_apellido": None}
    
    # 1. Intento: Capturar Nombres y Apellidos en pares CLAVE: VALOR
    for line in t.splitlines():
        # Captura Apellidos/Surname
        match_apellido = re.search(r'(?:APELLIDOS|SURNAME|APELLIDO)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s\.\-]+)', line)
        if match_apellido:
            name_parts["apellidos"] = match_apellido.group(1).strip()
            
        # Captura Nombres/Given Names/Nombre Completo
        match_nombre = re.search(r'(?:NOMBRES|NAME|GIVEN NAME|NOMBRE|NOMBRE COMPLETO)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s\.\-]+)', line)
        if match_nombre:
            # Si se encuentra 'Nombre Completo', lo priorizamos, pero si ya tenemos apellidos, solo usamos el nombre
            val = match_nombre.group(1).strip()
            
            # Si el valor capturado de 'NOMBRE' contiene espacios y parece ser el nombre completo
            if "COMPLETO" in line and len(val.split()) > 2:
                return " ".join(val.split()).title() # Retorna inmediatamente el nombre completo

            # Lógica estándar de nombres/apellidos
            if val not in ["DELA CRUZ", "DE", "LA", "DEL"]: # Exclusión por caso 9
                name_parts["nombres"] = val
        
        # Captura Segundo Apellido (caso 9)
        match_segundo = re.search(r'(?:SEGUNDO APELLIDO|SEGUNDOAPELLIDO)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s\.\-]+)', line)
        if match_segundo:
            name_parts["segundo_apellido"] = match_segundo.group(1).strip()


    # 2. Combinación de los resultados capturados
    apellidos = name_parts["apellidos"]
    nombres = name_parts["nombres"]
    segundo = name_parts["segundo_apellido"]

    full_name = []
    
    # Orden Preferente: Apellidos (1 o 2) + Nombres
    # Juntar todos los apellidos
    apellidos_full = [apellidos] if apellidos else []
    if segundo and segundo != apellidos: # No repetir si el OCR lo confunde
        apellidos_full.append(segundo)
    
    # Unir apellidos y nombres
    final_name_parts = [" ".join(apellidos_full).strip()] if apellidos_full else []
    if nombres:
        final_name_parts.append(nombres)
    
    final_name = " ".join(final_name_parts).strip()

    if final_name:
        # Post-limpieza y validación (debe tener al menos dos palabras)
        clean_name = re.sub(r'\s+', ' ', final_name).strip()
        if len(clean_name.split()) >= 2 and not any(ch.isdigit() for ch in clean_name):
            # Corregir la mayúsculas/minúsculas de los prefijos como DE, LA, Y
            title_cased = clean_name.title()
            for p in ["De ", "La ", "Los ", "Las ", "Y "]:
                title_cased = title_cased.replace(p, p.lower())
            return title_cased

    # Intento 3: Usar regex genérico (mantenido del código anterior)
    for rx in _NAME_HINTS:
        for line in t.splitlines():
            m = re.search(rx, line, flags=re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                if len(m.groups()) > 1 and m.group(2) is not None:
                    cand = cand.replace(m.group(2), '').strip()
                if len(cand.split()) >= 2 and not any(ch.isdigit() for ch in cand):
                    keywords_to_remove = ["DOMICILIO", "DIRECCION", "ADDRESS", "CALLE", "CASA"]
                    for kw in keywords_to_remove:
                        if cand.endswith(kw):
                            cand = cand[:-len(kw)].strip()
                    # Corregir la mayúsculas/minúsculas de los prefijos como DE, LA, Y
                    title_cased = " ".join(cand.split()).title()
                    for p in ["De ", "La ", "Los ", "Las ", "Y "]:
                        title_cased = title_cased.replace(p, p.lower())
                    return title_cased

    return None

def _find_first_date_after_keyword(texto: str, hints: list[str]) -> tuple[str|None, str|None]:
    """Devuelve (original_encontrada, sugerida_MDY) cerca de palabras clave."""
    if not texto: return None, None
    span = 120
    for kw in hints:
        for m in re.finditer(kw, texto, flags=re.IGNORECASE):
            window = texto[m.end(): m.end()+span]
            # 🆕 FASE 1: Agregamos los nuevos patrones
            for rx in (_DATE_RE_NUM_A,_DATE_RE_ISO,_DATE_RE_DMY_H,_DATE_RE_DD_MM_YYYY_DOT,
                       _DATE_RE_TXT_ES,_DATE_RE_TXT_ES_FULL,_DATE_RE_TXT_EN,_DATE_RE_TXT_EN_DMY,_DATE_RE_TXT_EN_MDY,
                       _DATE_RE_EN_MON_DD_YYYY_H,_DATE_RE_EN_DD_MON_YYYY_H, _DATE_RE_TXT_PASSPORT, 
                       _DATE_RE_MM_YYYY, _DATE_RE_DMMMYYYY):
                mm = rx.search(window)
                if mm:
                    original = mm.group(0).strip()
                    sugerida = _normalize_date_to_mdy_ctx(original, _infer_doc_country(texto), _detect_language_bias(texto))
                    if sugerida:
                        return original, sugerida
    return None, None
    
def _extract_dob(texto: str) -> tuple[str|None, str|None]:
    return _find_first_date_after_keyword(texto, _DOB_HINTS)

def _parse_dob_from_curp(curp: str):
    m = _CURP_RE.search(curp or "")
    if not m: return None
    yy, mm, dd = map(int, m.groups()[1:4])
    y = 2000 + yy if yy < 50 else 1900 + yy
    try:
        import datetime as _dt
        _dt.date(y, mm, dd)
        return f"{int(mm):02d}/{int(dd):02d}/{y:04d}"
    except Exception:
        return None

def _age_from_mdy(mdy: str):
    try:
        import datetime as _dt
        m,d,y = map(int, mdy.split("/"))
        dob = _dt.date(y,m,d); today = _dt.date.today()
        return (today - dob).days // 365
    except Exception:
        return None

def gemini_vision_auth_check(image_path: str) -> tuple[int, list[str]]:
    """
    Análisis forense avanzado con Gemini Vision para detectar falsificación.
    Retorna (score_adicional, detalles_visuales)
    """
    if not GEMINI_API_KEY or not image_path:
        return 0, []
    
    try:
        from PIL import Image, ImageOps
        import io, base64
        
        # Cargar y preparar imagen
        im = Image.open(image_path)
        im = ImageOps.exif_transpose(im)
        bio = io.BytesIO()
        im.save(bio, format="PNG")
        bio.seek(0)
        mime = "image/png"
        
        # Prompt forense avanzado
        prompt = (
            "Actúa como un experto forense en documentos de identidad. Analiza esta imagen con técnicas forenses profesionales.\n\n"
            "ANÁLISIS FORENSE REQUERIDO:\n"
            "1. ELEMENTOS DE SEGURIDAD:\n"
            "   - Hologramas, marcas de agua, microimpresiones\n"
            "   - Tintas especiales, guilloches (patrones de líneas)\n"
            "   - Elementos táctiles (relieve, textura)\n\n"
            "2. ANÁLISIS DE IMPRESIÓN:\n"
            "   - Calidad de impresión (offset profesional vs casera)\n"
            "   - Resolución y nitidez de texto/imágenes\n"
            "   - Alineación de capas (registro de color)\n"
            "   - Bordes de texto (limpios vs borrosos)\n\n"
            "3. DETECCIÓN DE MANIPULACIÓN DIGITAL:\n"
            "   - Clonación de áreas (stamp/clone tool)\n"
            "   - Bordes irregulares en foto o texto\n"
            "   - Inconsistencias de iluminación/sombras\n"
            "   - Artefactos de compresión JPEG sospechosos\n"
            "   - Transiciones de color no naturales\n\n"
            "4. TIPOGRAFÍA Y LAYOUT:\n"
            "   - Fuentes oficiales vs genéricas (Arial, Times)\n"
            "   - Espaciado y kerning profesional\n"
            "   - Alineación y márgenes estándar\n\n"
            "5. FOTOGRAFÍA:\n"
            "   - Calidad profesional vs casera\n"
            "   - Fondo uniforme y apropiado\n"
            "   - Iluminación frontal consistente\n"
            "   - Proporciones faciales correctas\n\n"
            "INSTRUCCIONES:\n"
            "- Evalúa cada categoría con score de 0-10 (10=muy sospechoso, 0=auténtico)\n"
            "- Menciona evidencia específica para scores >5\n"
            "- Sé directo y técnico, sin ambigüedades\n"
            "- Si detectas manipulación, especifica el tipo exacto"
        )
        temp = 0.1  # Temperatura muy baja para análisis determinista
        
        # Intentar con SDK primero
        visual_analysis = ""
        if genai is not None:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel(GEMINI_MODEL)
                resp = model.generate_content(
                    [{"mime_type": mime, "data": bio.getvalue()}, {"text": prompt}],
                    generation_config={"temperature": temp, "top_p": 0.9, "max_output_tokens": 2048},
                    request_options={"timeout": GEMINI_TIMEOUT_LONG}  # Timeout más largo para análisis forense
                )
                visual_analysis = getattr(resp, "text", "") or ""
            except Exception:
                pass  # Fallback a REST
        
        # Fallback REST
        if not visual_analysis:
            try:
                b64 = base64.b64encode(bio.getvalue()).decode("utf-8")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
                payload = {
                    "contents": [{
                        "parts": [
                            {"inline_data": {"mime_type": mime, "data": b64}},
                            {"text": prompt}
                        ]
                    }],
                    "generationConfig": {"temperature": temp, "topP": 0.9, "maxOutputTokens": 2048}
                }
                headers = {"Content-Type": "application/json"}
                r = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=payload, 
                                 timeout=GEMINI_TIMEOUT_LONG)  # Timeout más largo para análisis forense
                data = r.json()
                visual_analysis = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "") or ""
            except requests.Timeout:
                return 0, ["Timeout en análisis forense visual"]
            except requests.ConnectionError:
                return 0, ["Sin conexión para análisis forense"]
            except Exception:
                return 0, ["Error en análisis forense visual"]
        
        # Análisis forense mejorado con más keywords
        analysis_lower = visual_analysis.lower()
        score_visual = 0
        detalles_internos = []  # Detalles técnicos (no se muestran al usuario)
        
        # Red flags expandidos con pesos ajustados
        red_flags = {
            # Manipulación digital (peso alto)
            "manipulación": 30,
            "manipulacion": 30,
            "editado": 30,
            "photoshop": 40,
            "clonación": 40,
            "clonacion": 40,
            "alterado": 30,
            "retocado": 25,
            
            # Falsificación directa (peso muy alto)
            "falso": 45,
            "falsificación": 45,
            "falsificacion": 45,
            "no auténtico": 40,
            "fraudulento": 45,
            
            # Inconsistencias (peso medio-alto)
            "inconsistente": 25,
            "sospechoso": 25,
            "irregular": 20,
            "anómalo": 25,
            "anomalo": 25,
            
            # Calidad (peso medio)
            "borroso": 15,
            "pixelado": 15,
            "baja calidad": 20,
            "amateur": 20,
            "casera": 25,
            
            # Elementos faltantes (peso alto)
            "sin holograma": 35,
            "falta marca de agua": 35,
            "ausencia de": 30,
            "no se observa": 25,
            
            # Tipografía (peso medio)
            "fuente genérica": 20,
            "fuente generica": 20,
            "arial": 15,
            "times new roman": 15,
            
            # Bordes y transiciones (peso medio-alto)
            "bordes irregulares": 30,
            "transición abrupta": 25,
            "transicion abrupta": 25,
            "recorte sospechoso": 30,
        }
        
        for keyword, penalty in red_flags.items():
            if keyword in analysis_lower:
                score_visual += penalty
                detalles_internos.append(f"Forense: '{keyword}' (+{penalty})")
        
        # Señales positivas (bonificación)
        positive_signals = ["auténtico", "autentico", "legítimo", "legitimo", "genuino", "profesional", "oficial"]
        if any(word in analysis_lower for word in positive_signals):
            if score_visual == 0:
                detalles_internos.append("Forense: Documento aparenta autenticidad")
            else:
                # Reducir score si hay señales positivas mezcladas
                score_visual = max(0, score_visual - 10)
                detalles_internos.append("Forense: Señales mixtas detectadas (-10)")
        
        # Guardar análisis completo en detalles internos (para logs)
        if visual_analysis.strip():
            detalles_internos.append(f"Análisis completo: {visual_analysis[:300]}")
        
        return min(score_visual, 50), detalles_internos  # Cap reducido a 50 para evitar falsos positivos
        
    except Exception as e:
        return 0, [f"Error en análisis forense: {str(e)[:100]}"]


def _authenticity_score(texto: str, image_path: str|None):
    """
    Calcula el score de autenticidad combinando análisis de texto y visual forense.
    Retorna (riesgo, details_user, emoji_semaforo, color_semaforo)
    
    Niveles de riesgo (umbrales más estrictos):
    - 🟢 BAJO (0-15): Verde - Documento aparenta ser auténtico
    - 🟡 MEDIO (16-40): Amarillo - Requiere verificación adicional
    - 🔴 ALTO (41+): Rojo - Alta probabilidad de falsificación
    """
    details_internal = []  # Detalles técnicos (para logs)
    details_user = []      # Mensajes para el usuario (genéricos)
    score = 0
    low = (texto or "").lower()

    # Usamos la lógica del nuevo procesador para obtener la fecha normalizada
    date_results = _process_all_dates_by_type(texto)
    dob_use = date_results.get("fecha_nacimiento_final")
    doc_pais = _infer_doc_country(texto)
    
    # 1. Chequeo de Muestra/Plantilla (crítico)
    if any(w in low for w in _SAMPLE_WORDS if w):
        score += 60
        details_internal.append("⚠️ CRÍTICO: Contiene 'sample/muestra/void'")
        details_user.append("Documento de muestra detectado")

    # 2. Chequeo de Nombre
    nombre = _extract_name(texto)
    if not nombre:
        score += 15
        details_internal.append("⚠️ No se detectó nombre válido")
        details_user.append("Información incompleta")

    # 3. Chequeo de Fecha de Nacimiento e Inconsistencias
    if dob_use and "Sugerida" not in dob_use:
        age = _age_from_mdy(dob_use)
        if age is not None and (age < 15 or age > 120):
            score += 35
            details_internal.append(f"⚠️ Edad implausible: {age} años")
            details_user.append("Inconsistencia en datos personales")
        
        # Validación CURP (México) - mejorada
        curp_m = _CURP_RE.search(texto or "")
        if curp_m and doc_pais == "MX":
            curp = curp_m.group(0)
            curp_dob = _parse_dob_from_curp(curp)
            if curp_dob and curp_dob != dob_use:
                score += 45
                details_internal.append(f"⚠️ CURP no coincide: CURP={curp_dob} vs DOB={dob_use}")
                details_user.append("Inconsistencia en identificadores oficiales")
        
        # Validación RFC (México) - mejorada
        rfc_m = _RFC_PER_RE.search(texto or "")
        if rfc_m and doc_pais == "MX":
            yy, mm, dd = map(int, rfc_m.groups()[1:4])
            y = 2000 + yy if yy < 50 else 1900 + yy
            rfc_dob = f"{mm:02d}/{dd:02d}/{y:04d}"
            if rfc_dob != dob_use:
                score += 25
                details_internal.append(f"⚠️ RFC no coincide: RFC={rfc_dob} vs DOB={dob_use}")
                details_user.append("Inconsistencia en datos fiscales")
    else:
        score += 8  # Reducido de 12 a 8
        details_internal.append("⚠️ No se identificó fecha de nacimiento")
        details_user.append("Información incompleta")

    # 4. Chequeo de Vigencia (penalización reducida para evitar falsos positivos)
    vig_final = date_results.get("fecha_vigencia_final")
    if not vig_final or "Sugerida" in vig_final:
        score += 8  # Reducido de 12 a 8
        details_internal.append("⚠️ No se detectó vigencia válida")
        # No agregar a details_user (no es crítico para el usuario)
    
    # 5. Validación de Número de ID (penalización reducida)
    num_id = _extract_id_number(texto, doc_pais)
    if not num_id:
        score += 6  # Reducido de 10 a 6
        details_internal.append("⚠️ No se detectó número de identificación")
        details_user.append("Información incompleta")
    elif num_id in ["123456789", "000000000", "111111111", "999999999"]:
        score += 40
        details_internal.append(f"⚠️ Número de ID sospechoso: {num_id}")
        details_user.append("Patrón de identificación no válido")
    
    # 6. 🆕 ANÁLISIS VISUAL FORENSE (siempre activo, peso mínimo)
    # ESTRATEGIA: Analizar TODOS los documentos pero con peso muy reducido
    # Esto mantiene detección de fraudes sin causar falsos positivos
    
    if image_path and os.path.exists(image_path):
        visual_score, visual_details_internal = gemini_vision_auth_check(image_path)
        
        # Peso optimizado para detección: máximo 20 puntos
        # Balance: suficiente para detectar fraudes, controlado para limitar falsos positivos
        visual_score_aplicado = min(visual_score, 20)
        score += visual_score_aplicado
        
        if visual_score > 0:
            details_internal.append(f"Análisis visual: {visual_score} pts (aplicados: {visual_score_aplicado} pts)")
            details_internal.extend(visual_details_internal[:1])
        
        # Mensaje genérico solo si el análisis visual detecta problemas muy serios
        if visual_score > 40:
            details_user.append("Análisis visual detectó anomalías significativas")
        elif visual_score > 25:
            details_user.append("Análisis visual requiere verificación")
    
    # NOTA: Análisis visual SIEMPRE activo pero con peso reducido
    # Esto balancea detección (mantiene capacidad de detectar fraudes)
    # vs falsos positivos (peso bajo no marca documentos reales)
    
    # 7. Validación de consistencia interna adicional
    # Verificar que el nombre no sea obviamente falso
    if nombre:
        nombre_lower = nombre.lower()
        fake_patterns = ["test", "prueba", "ejemplo", "sample", "xxxx", "aaaa"]
        if any(pattern in nombre_lower for pattern in fake_patterns):
            score += 35
            details_internal.append(f"⚠️ Nombre sospechoso: {nombre}")
            details_user.append("Datos personales no válidos")
    
    # Determinar nivel de riesgo (optimizado para detección)
    if score <= 16:  # Umbral para BAJO
        riesgo = "bajo"
        emoji = "🟢"
        color = "green"
        # Mensaje genérico positivo
        if not details_user:
            details_user = ["Documento aparenta ser auténtico"]
    elif score <= 40:  # Umbral para MEDIO
        riesgo = "medio"
        emoji = "🟡"
        color = "yellow"
        # Mensaje genérico de precaución + disclaimer
        if not details_user:
            details_user = ["Requiere verificación adicional"]
        details_user.append("⚠️ Se recomienda validación física del documento")
    else:  # 41+
        riesgo = "alto"
        emoji = "🔴"
        color = "red"
        # Mensaje genérico de alerta + disclaimer fuerte
        if not details_user:
            details_user = ["Se detectaron inconsistencias significativas"]
        details_user.append("⚠️ VALIDACIÓN FÍSICA OBLIGATORIA - No confiar solo en análisis digital")
    
    # Guardar detalles internos en logs (para auditoría)
    if details_internal:
        registrar_changelog(f"Análisis forense - Score: {score} - {' | '.join(details_internal[:3])}")
    
    return riesgo, details_user, emoji, color


# ===== AUTENTICACIÓN CON KEYCLOAK SSO =====

def autenticar_con_keycloak():
    """
    Inicia sesión con Keycloak usando el wrapper KeycloakAuth.
    Retorna: (ok: bool, mensaje: str)
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
    except Exception:
        return False


def cerrar_sesion_keycloak():
    """Cierra la sesión SSO y limpia el usuario actual."""
    global keycloak_auth_instance

    try:
        if keycloak_auth_instance:
            try:
                keycloak_auth_instance.logout()
            except Exception as e:
                print(f"Error al cerrar sesión Keycloak: {e}")
    finally:
        keycloak_auth_instance = None
        usuario_actual["correo"] = None
        usuario_actual["nombre"] = None
        usuario_actual["sso"] = False


# --- Tk / UI ---
# (Las importaciones ya se hicieron al inicio)

# ===== ESTILO =====
APP_TITLE = "HADES 1.8 — Integrado"
COLOR_BG = "#0f0b1a"; COLOR_PANEL = "#1a1330"; COLOR_CARD = "#221b3f"
COLOR_TEXT = "#EAE6FF"; COLOR_MUTED = "#C7B8FF"
ACCENT = "#7C3AED"; ACCENT_2 = "#A78BFA"; COLOR_BTN = "#2E2357"; COLOR_PRIMARY = ACCENT
COLOR_GREEN = "forest green"
COLOR_PURPLE = "purple3"
COLOR_BLUE = "DodgerBlue"
COLOR_RED = "firebrick1"

# ===== CONFIG MANUAL =====
GS_KB_SHEET_ID = "1wrtj7SZ6wB9h1yd_9h613DYNPGjI69_Zj1gLigiUHtE" # KB (pregunta/respuesta por pestaña)
GS_AUTH_SHEET_ID = "1Ev3i55QTW1TJQ_KQP01TxEiLmZJVkwVFJ1cn_p9Vlr0" # Autorizados (correo/nombre)
SA_JSON_B64 = "ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAibWF4aWJvdC00NzI0MjMiLAogICJwcml2YXRlX2tleV9pZCI6ICJmOTFkMGRjYWM2ODA4NTYyY2IxOTRlOWM0NmU5ZDM2MGY1ZTNjNTczIiwKICAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUURIN0IrZ0JnTU9ScElmXG50ejJQSWRieXpoUnduSitVcitZN05JT1FsRGpNMWgweEl3dUIrNHZ6M2w4M1J1dWJ5VEQvbUQ1NklDckJONkg2XG50RkNDcTErbytsMWl0T1lHYkNVajdCcnBZM3ZnbHJmUVJFcUdnV1EzT2lxdGR6bHE3b3RhZk11K1d6bVlKODVQXG5QNnl1SUVJbnUyVXFEYW5WV3ZrL2Q1WnlaRkF3UG9IRDVIMldKcGlwblNhTW1HcXhDRG5RWTAxVDAwUWRiaStIXG42NlFscXdCQURFajZXWHhCNm1BdXZIdXRJTG4vaWRsYWpZRU4zVDd3OTJ1Q2JPNVk1dlFuUlI1TGViS1paaE5hXG5ZbTlPanp3TE9SekFPVG9rWCswWXZxUGFhTXplV2lncWY5RDJMZ3NMbE1sZnpBNXpxQkhEV0szaTJGMngvYWNXXG5jVkJIRzI2N0FnTUJBQUVDZ2dFQUNndWVSeThtSmloN25TWmE3SDg1eXJkNkpYSnBQbEpjVWl0QVZScHRoRFZhXG5BQ2NQby9kY3YrTXppNVovcmpNOHlBc0JVS2VmSGxoS1JrdWJKQVd5Wjg0MHRRbjc2T1MwTlFyZkMwMFpZMTZQXG5XK0tpa0FHZVpId0N1dmFicHZqWGZiTjVsVllHSGRRYU5MY3hXUXA3NkgwdEJ5RHFvTExTaFZMZjkxMTgvZjkvXG5RVGlIMk1pMkZNS3crVS93ckVsbmV0SFIrSE1vV2Fia2picGx4cEZQRDNMTkpWU0oybHkwUzBzb2praDV0WEZ5XG5ubDJXVUJPd1FTVmNmQzhvVHNwQXM3SUpXRzZVYldBc2dkZHlWZUU1VDRkZGFoa0JDSEhYQVFBUVYzYjJFTGM2XG54USs5WVFxS2VJNmNTMW5OeHNRUjBlK1V3OG1zT3V1MElSS3Mva2hmQVFLQmdRRHlzUGVGaFJUZ01kd1NsS2dCXG5vVHlnTUxtd3JVUGhzMXJ6d1g1eEVaUWtSRmVjb2F4M0U3WDJFTnRpR1AyRm9oU0R4VVd4TFE3czMyaFFOU0RpXG5tbmh1NWs4SVk1Nmt2VGxjbzlMeDV5TEF5UHEyTFNQWDUrYmowZXkzdEZkVXFaT0dqWlRrV0R3NUh4QlBRMHIyXG5BbFFKT01RUURMRHFPQnFXWUd4YksydHdPd0tCZ1FEUzRyNDkybk92TGhMaHYyMm0yUTlVa3BRcis4RC9udXQ5XG45ajJwSzFQQ1dRRmJhSHRVWit3NFhPUk1pczVqM3ZaTkg3aDd0Z3hvM0FhTGhGMS8wSlJYaTlpS2V2SmpKU0JjXG5zREI2SFE5cFBmNUU0SHNPOE9zejBDNjMzYXNMUFNZakIwNFdUWkVtQ0J2dFoxeGtXZHpQdG1VajZSYThSZUkwXG56TkFDeXpLVGdRS0JnQmZ3enlvVHU4QjJDckNtaTRCRnFKWmcyQ0NPcHhDZndjd2ovVllvRnNZUkc5ZHV0M1d6XG5zeEtJRFN3N0xOOCs0dWt3ejdRdnJyWTlQNndSNGFHWS9XSnJROGFmRlNwSkpGeDRLTG9HUkE1aWhTRHRpUWltXG5ic2R3a1BwNlJ0Y3FOMHhoc1J0cGZOOWhxaGszbVRCMWdGYThpOUxOZmJKTlFJb3ZEdUZiZ2lpN0FvR0FPdGdZXG5PNHdzUVpKNnBGRlZHSHh5NGFkdy93RGxycTQ2aWRCZkRraFB1K2c0RDdpTXlWV2lQV3YyTEVHREs2ejRUemJ0XG50Rjl0QVFsOExnd0dSdmI5blp3aEZTc1BYWWpyaWRHRUJWNzhnT0pTaEFlYmJ1VGN6SDFudTloM3ROQWdSeC92XG5zeHQ3eC8vMVF2NVhjb3o4cDF6K3hkRnhqYUYyYUVOS082MVZkSUVDZ1lFQXovMTRCVnZDQ2MzRGg0elBFOXlBXG4weEp0ZDhzNUw2YUdnT3h5RzRZR3VuKzZ0QTBKOWZvUWV4cHd2azFpWGlOYXZvWTNWN3haRUNSSm1ua2l4TEEzXG53bWZ3YzZFTkVWWjg0b2Y0VU42SVRSdCtHRytGZThTaE05STBFVHpFYWlTcmQvT0VxQ1VQZVlNelNQQVNIakRCXG5PdW1LWHlkU2N5NWhlNUdpNm9rc2MyWT1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsCiAgImNsaWVudF9lbWFpbCI6ICJtYXhpYm90LXNhQG1heGlib3QtNDcyNDIzLmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAiY2xpZW50X2lkIjogIjExNjkyMDExNDg3MTgwMTYxMTEzOSIsCiAgImF1dGhfdXJpIjogImh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9hdXRoIiwKICAidG9rZW5fdXJpIjogImh0dHBzOi8vb2F1dGgyLmdvb2dsZWFwaXMuY29tL3Rva2VuIiwKICAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92MS9jZXJ0cyIsCiAgImNsaWVudF94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL3JvYm90L3YxL21ldGFkYXRhL3g1MDkvbWF4aWJvdC1zYSU0MG1heGlib3QtNDcyNDIzLmlhbS5nc2VydmljZWFjY291bnQuY29tIiwKICAidW5pdmVyc2VfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIgp9Cg=="

# JSON de cuenta de servicio en BASE64
DRIVE_FOLDER_ID = "1eexrVXQYRZLk9hnJwLVYJp5PkYnjx2bt" # Carpeta destino (URL .../folders/<ID>)
GEMINI_API_KEY = None # se solicita desde botón

# ===== USUARIO ACTUAL (Keycloak SSO) =====
usuario_actual = {"correo": None, "nombre": None, "sso": False}

# ===== MODELO GEMINI SELECCIONADO =====
GEMINI_MODEL = "gemini-2.5-flash"  # Modelo fijo (el que funcionaba antes)

# ===== CONFIGURACIÓN DE IA (Solo Gemini) =====
# Claude ha sido removido - solo usamos Gemini


# ===== CONFIG LOGIN (OAuth) =====
USE_OAUTH_LOGIN = False
OAUTH_CLIENT_JSON_B64 = "PEGA_AQUI_BASE64_DEL_CLIENT_SECRET_JSON"
ENTERPRISE_DOMAIN = "maxillc.com"
SCOPES_SHEETS = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ===== GOOGLE API =====
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    _GOOGLE_OK = True
except Exception as e:
    _GOOGLE_OK = False
    print("[HADES] Google API no disponible:", e)


usuario_actual = {"correo": None, "nombre": None}
respuestas_por_hoja = {}

# ===== Helpers Google =====
def _load_sa_info():
    if not SA_JSON_B64 or "PEGA_AQUI" in SA_JSON_B64:
        raise RuntimeError("Falta SA_JSON_B64 (CONFIG MANUAL).")
    try:
        # 1. Limpieza extrema: Eliminar espacios en blanco y caracteres no-Base64
        b64c_raw = SA_JSON_B64.strip()
        # Solo permite caracteres alfanuméricos, +, /, y =
        b64c = re.sub(r'[^A-Za-z0-9+/=]', '', b64c_raw)
        
        # 2. Asegurar el padding correcto para Base64 (corrige el error "cannot be 1 more...")
        missing_padding = len(b64c) % 4
        if missing_padding != 0:
            b64c += '=' * (4 - missing_padding)
        
        # 3. Decodificación
        data = base64.b64decode(b64c.encode("utf-8"))
        return json.loads(data.decode("utf-8"))
    except (base64.binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
        # 🚨 DIAGNÓSTICO: Imprimir la cadena Base64 que intentó usar.
        print("\n" + "="*80)
        print("🚨 ERROR CRÍTICO DE CARGA DE CREDENCIALES (BASE64 INVÁLIDO) 🚨")
        print(f"Error específico: {e}")
        print(f"Longitud de la cadena limpia: {len(b64c)}")
        print("CADENA BASE64 QUE INTENTÓ CARGAR (revise si está completa):")
        print(b64c)
        print("="*80 + "\n")
        
        # Lanzar error de aplicación con el detalle
        raise RuntimeError(
            f"SA_JSON_B64 es un Base64/JSON inválido. "
            f"Verifique la consola para ver la cadena que intentó cargar. Detalle: {e}"
        )


def _creds_sa(scopes):
    try:
        from google.oauth2 import service_account  # Lazy import
        info = _load_sa_info()
        return service_account.Credentials.from_service_account_info(info, scopes=scopes)
    except ImportError:
        raise RuntimeError("Google API no disponible (instala google-auth)")

def _creds(scopes):
    return _creds_sa(scopes)

def _sheets_service():
    if not _GOOGLE_OK:
        raise RuntimeError("Google API no disponible")
    try:
        from googleapiclient.discovery import build  # Lazy import
        return build("sheets", "v4", credentials=_creds(SCOPES_SHEETS), cache_discovery=False)
    except ImportError:
        raise RuntimeError("Google API no disponible (instala google-api-python-client)")
    except RuntimeError as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Error al inicializar Sheets API: {e}")


def _drive_service(scopes):
    if not _GOOGLE_OK:
        raise RuntimeError("Google API no disponible")
    try:
        from googleapiclient.discovery import build  # Lazy import
        from googleapiclient.http import MediaFileUpload  # Lazy import
        return build("drive", "v3", credentials=_creds(scopes), cache_discovery=False)
    except ImportError:
        raise RuntimeError("Google API no disponible (instala google-api-python-client)")
    except RuntimeError as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Error al inicializar Drive API: {e}")

def _sheet_titles(sheet_id: str):
    try:
        svc = _sheets_service()
        meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
        return [s["properties"]["title"] for s in meta.get("sheets", [])]
    except RuntimeError as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Error al leer títulos de Sheet: {e}")


def _get_rows(sheet_id: str, title: str):
    try:
        svc = _sheets_service()
        rng = f"'{title}'!A:Z"
        res = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range=rng).execute()
        return res.get("values", [])
    except RuntimeError as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Error al leer filas del Sheet: {e}")


# ===== Verificación=====
def verificar_correo_online(correo: str):
    try:
        sheet_titles = _sheet_titles(GS_AUTH_SHEET_ID)
        
        if not sheet_titles:
            messagebox.showwarning("Configuración Incompleta", "El Google Sheet de autorizados está vacío o mal configurado.")
            return False, None
            
        for title in sheet_titles:
            rows = _get_rows(GS_AUTH_SHEET_ID, title)
            if not rows: continue
            
            # Limpiar y normalizar la cabecera antes de buscar 'correo'
            header_raw = rows[0]
            header = [str(h).strip().lower() for h in header_raw]
            
            try:
                i_c = header.index("correo")
                i_n = header.index("nombre") if "nombre" in header else None
            except ValueError:
                # Si la columna 'correo' no se encuentra en esta hoja, pasa a la siguiente.
                continue

            # Normalizar el correo de entrada para la búsqueda
            correo_buscado = correo.strip().lower()

            for r in rows[1:]:
                # Normalizar el correo de la hoja para la comparación
                if i_c < len(r):
                    correo_en_hoja = str(r[i_c]).strip().lower()
                    
                    if correo_en_hoja == correo_buscado:
                        nombre = str(r[i_n]).strip() if (i_n is not None and i_n < len(r) and r[i_n]) else correo
                        return True, nombre
        
        # Si termina el bucle sin encontrar el correo
        return False, None
        
    except RuntimeError as e:
        # Captura errores del Service Account (Base64/Permisos)
        messagebox.showerror("Error de Conexión",
            f"No se pudo acceder a la lista de autorizados (Sheets API). \n"
            f"Verifica el permiso del Service Account y la clave Base64. Detalle: {e}")
        return False, None
    except Exception as e:
        # Captura otros errores de API o conexión.
        messagebox.showerror("Error de Conexión", f"Error inesperado de conexión a Sheets: {e}")
        return False, None


# ====== OCR con Gemini Visión (REST) ======

def gemini_vision_extract_text(image_path: str) -> str:
    """
    Extrae texto con Gemini Visión.

    - Fuerza salida en formato CLAVE: VALOR (OCR estructurado).
    - Si la salida parece "alucinación" (ej. resolución de un problema matemático),
      reintenta con un prompt más estricto y temperatura 0.
    """
    if not GEMINI_API_KEY:
        return "⚠️ Configura GEMINI_API_KEY para usar Visión."

    from PIL import Image, ImageOps

    im = None
    try:
        # --- Pre-proceso de imagen ---
        im = Image.open(image_path)
        im = ImageOps.exif_transpose(im)  # auto-rotación por EXIF
        bio = io.BytesIO()
        im.save(bio, format="PNG")  # normalizamos a PNG
        bio.seek(0)
        mime = "image/png"

        def _looks_like_document_ocr(t: str) -> bool:
            """Heurística rápida para detectar salidas no relacionadas (p.ej. matemáticas)."""
            if not t:
                return False
            tt = t.strip()
            if len(tt) < 20:
                return False

            low = tt.lower()
            colon_lines = sum(1 for ln in tt.splitlines() if ":" in ln)
            has_mrz = ("p<" in low) or ("mrz" in low)

            # Palabras típicas de documentos (inglés Y español, ya que la traducción se aplica antes)
            has_doc_words = any(
                w in low
                for w in [
                    # --- Inglés (originales) ---
                    "pasaporte", "passport",
                    "identific", "id", "licencia", "driver",
                    "residen", "resident",
                    "cédula", "cedula", "dni",
                    "nombre", "surname", "given name",
                    "fecha", "date of birth", "dob",
                    "expir", "expiry", "expires", "emisión", "emision", "issue",
                    # --- Español (tras traducción) ---
                    "apellido",                 # surname → Apellido
                    "vence", "vencimiento",     # expires/expiry → Vence/Vencimiento
                    "vigencia", "caducidad",    # validity/expiration
                    "expedicion", "expedición", # issue → Expedición
                    "nacimiento",               # date of birth → Nacimiento
                    "conducir",                 # driver → Conducir
                    "identificacion",           # identification
                    "numero de",                # number of
                ]
            )

            # Frases típicas de soluciones matemáticas / contenido ajeno
            bad_phrases = [
                "to solve this problem",
                "we need to find",
                "minimum value",
                "constrained optimization",
                "expand the expression",
                "now substitute",
                "f(x)",
                "x + y",
                "x^",
                "y^",
            ]
            if any(p in low for p in bad_phrases) and not has_mrz and not has_doc_words:
                return False

            # Señales fuertes de que sí es OCR del documento
            if has_mrz:
                return True
            if colon_lines >= 2:
                return True
            if has_doc_words and len(tt) > 60:
                return True

            return False

        def _run_once(prompt: str, temp: float) -> str:
            """Ejecuta 1 intento (SDK preferente; REST fallback)."""
            # --- SDK preferente ---
            if genai is not None:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel(GEMINI_MODEL)
                    resp = model.generate_content(
                        [{"mime_type": mime, "data": bio.getvalue()}, {"text": prompt}],
                        generation_config={"temperature": temp, "top_p": 0.95, "max_output_tokens": 4096},
                        request_options={"timeout": GEMINI_TIMEOUT_SHORT},
                    )
                    texto = getattr(resp, "text", "") or ""
                    if texto.strip():
                        return texto
                except Exception:
                    pass  # fallback a REST

            # --- Fallback REST ---
            b64 = base64.b64encode(bio.getvalue()).decode("utf-8")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"inline_data": {"mime_type": mime, "data": b64}},
                            {"text": prompt},
                        ]
                    }
                ],
                "generationConfig": {"temperature": temp, "topP": 0.95, "maxOutputTokens": 4096},
            }
            headers = {"Content-Type": "application/json"}
            r = requests.post(
                f"{url}?key={GEMINI_API_KEY}",
                headers=headers,
                json=payload,
                timeout=GEMINI_TIMEOUT_SHORT,
            )
            data = r.json()
            texto = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                or ""
            )
            return texto

        # --- Prompts (2 intentos) ---
        prompt_base = (
            "Eres un experto en OCR. Extrae TODO el texto visible de esta imagen de documento oficial. "
            "Organiza la información como pares CLAVE: VALOR. "
            "Ejemplo: Nombre: RAMIREZ MARTINEZ MIRIAN, Fecha de Nacimiento: 05/06/1993, Número: 123456789. "
            "IMPORTANTE: Incluye TODOS los números, series, claves, fechas y texto que veas. "
            "Mantén la puntuación original. "
            "Responde SOLO el texto extraído en formato clave-valor en español. "
            "NO agregues comentarios, introducciones ni explicaciones."
        )

        prompt_strict = (
            "Eres un motor de OCR para documentos. "
            "Devuelve ÚNICAMENTE líneas en formato CLAVE: VALOR (una por línea). "
            "PROHIBIDO: resolver problemas, explicar, inventar datos, o escribir contenido que NO esté en el documento. "
            "Si un campo no es legible, escribe ILEGIBLE como valor. "
            "Incluye también las líneas MRZ si existen. "
            "Salida SOLO en español."
        )

        attempts = [
            (prompt_base, 0.3),
            (prompt_strict, 0.0),
        ]

        last_text = ""
        for prompt, temp in attempts:
            texto = _run_once(prompt, temp)
            texto = _clean_ocr_output(texto)
            texto = _translate_field_labels_to_spanish(texto)  # 🌐 Traducir etiquetas al español
            if texto.strip():
                last_text = texto
            if _looks_like_document_ocr(texto):
                return texto

        # Si ambos intentos fallan, evita mostrar basura (ej. matemáticas)
        if last_text and _looks_like_document_ocr(last_text):
            return last_text

        return (
            "⚠️ OCR: no se pudo extraer contenido válido del documento. "
            "Intenta con una imagen más nítida (más cerca, sin reflejos, recortada)."
        )

    except requests.Timeout:
        return "⚠️ Timeout: Gemini tardó demasiado. Intenta con una imagen más pequeña."
    except requests.ConnectionError:
        return "⚠️ Sin conexión a internet. Verifica tu red."
    except Exception as e:
        try:
            registrar_changelog(f"ERROR en gemini_vision_extract_text: {str(e)[:200]}")
        except Exception:
            pass
        return f"⚠️ Error al extraer texto: {str(e)[:120]}"
    finally:
        try:
            if im is not None:
                im.close()
        except Exception:
            pass
        gc.collect()

def themed_askstring(title: str, prompt: str, initialvalue: str = "", parent=None, **kwargs):
    import tkinter as tk
    from tkinter import Toplevel
    top = Toplevel(parent if parent is not None else root)
    top.title(title)
    top.configure(bg=COLOR_CARD)
    top.transient(root)
    top.grab_set()
    # contenedor
    frm = tk.Frame(top, bg=COLOR_CARD)
    frm.pack(padx=16, pady=14)
    # etiqueta
    lbl = tk.Label(frm, text=prompt, bg=COLOR_CARD, fg=COLOR_TEXT)
    lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))
    # entrada
    ent = tk.Entry(frm, bg="#1f1440", fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
                   highlightbackground=ACCENT_2, relief="flat", width=42, **kwargs) # Permite pasar 'show'
    ent.insert(0, initialvalue or "")
    ent.grid(row=1, column=0, columnspan=2, sticky="ew")
    frm.grid_columnconfigure(0, weight=1)

    # botones
    def close_ok():
        nonlocal_val[0] = ent.get().strip()
        top.destroy()
    def close_cancel():
        nonlocal_val[0] = None
        top.destroy()

    nonlocal_val = [None]
    btn_ok = tk.Button(frm, text="OK", command=close_ok, bg=COLOR_PURPLE, fg="white", relief="flat", padx=16, pady=10)
    btn_cancel = tk.Button(frm, text="Cancel", command=close_cancel, bg="#38304f", fg=COLOR_TEXT, relief="flat", padx=16, pady=10)
    btn_ok.grid(row=2, column=0, sticky="e", pady=(10,0), padx=(0,6))
    btn_cancel.grid(row=2, column=1, sticky="w", pady=(10,0))

    # centrar
    top.update_idletasks()
    anchor = parent if parent is not None else root
    x = anchor.winfo_rootx() + (anchor.winfo_width()//2 - top.winfo_width()//2)
    y = anchor.winfo_rooty() + (anchor.winfo_height()//2 - top.winfo_height()//2)
    top.geometry(f"+{x}+{y}")
    top.wait_window(top)
    return nonlocal_val[0]
# ====== Estado / resultados / métricas (Función de guardado mejorada) ======
rutas=[]; idx=-1; rot=0
resultados=[] # [{archivo, texto, duracion_s, tipo, doc_pais, ...}]
API_USADA="gemini-vision"

# ====== Threading y Estabilidad ======
current_operation = None
cancel_requested = False

# Timeouts optimizados (más cortos para evitar bloqueos)
GEMINI_TIMEOUT_SHORT = 30   # Para OCR básico
GEMINI_TIMEOUT_LONG = 45    # Para análisis forense
DRIVE_TIMEOUT = 20          # Para upload a Drive

class ThreadedOperation:
    """Ejecuta operaciones pesadas en thread separado para no bloquear UI"""
    def __init__(self):
        self.thread = None
        self.result_queue = queue.Queue()
        self.cancel_flag = threading.Event()
    
    def run(self, func, *args, **kwargs):
        """Ejecuta función en thread separado"""
        def wrapper():
            try:
                result = func(*args, **kwargs)
                self.result_queue.put(('success', result))
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                self.result_queue.put(('error', str(e), error_detail))
        
        self.thread = threading.Thread(target=wrapper, daemon=True)
        self.thread.start()
    
    def cancel(self):
        """Marca operación para cancelar"""
        self.cancel_flag.set()
    
    def is_cancelled(self):
        """Verifica si se solicitó cancelación"""
        return self.cancel_flag.is_set()
    
    def is_done(self):
        """Verifica si terminó"""
        return self.thread is None or not self.thread.is_alive()
    
    def get_result(self, timeout=0.1):
        """Obtiene resultado si está listo"""
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None

def registrar_changelog(evento: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs("./logs", exist_ok=True)
    with open("./logs/changelog.txt", "a", encoding="utf-8") as log:
        log.write(f"[{ts}] {evento}\n")

def _guardar_resultado(nombre: str, texto: str, tipo: str, duracion_s: float,
                         datos_esenciales: dict = None, riesgo: str = "", detalles: list = None, policy_data: dict = None):
    """Guarda resultados y métricas de forma consolidada."""
    # Inicialización
    r = next((res for res in resultados if res['archivo'] == nombre), None)
    if not r:
        r = {'archivo': nombre, 'texto': texto, 'tipo': tipo, 'duracion_s': duracion_s}
        resultados.append(r)
    else:
        r.update({'texto': texto, 'tipo': tipo, 'duracion_s': duracion_s})

    # 🆕 Agregar el correo del usuario autenticado
    usuario_correo = "Sin autenticar"
    if keycloak_auth_instance and keycloak_auth_instance.is_authenticated():
        usuario_correo = keycloak_auth_instance.get_user_email() or "Sin correo"
    r['usuario_correo'] = usuario_correo

    # Campos extra (País, Fechas, Vigencia)
    try:
        date_results = _process_all_dates_by_type(texto)
        
        doc = _infer_doc_country(texto)
        # Aquí usamos el texto original del OCR
        _, pairs, _, fmt = _normalize_all_dates_with_pairs(texto)
        
        # Asignación de fechas procesadas
        r['doc_pais'] = doc or ''
        r['formato_fecha_detectado'] = fmt or ''
        
        # Nuevos campos de fechas (usados para el exportador)
        r['fecha_expedicion_final'] = date_results.get('fecha_expedicion_final') or ''
        r['fecha_nacimiento_final'] = date_results.get('fecha_nacimiento_final') or ''
        r['vigencia_final'] = date_results.get('fecha_vigencia_final') or ''
        r['otras_fechas_final'] = date_results.get('otras_fechas_normalizadas') or ''
        
        # Compatibilidad con campos antiguos del exportador
        fechas_mdy = f"Vig: {r['vigencia_final']} | Exp: {r['fecha_expedicion_final']} | Nac: {r['fecha_nacimiento_final']}"
        r['fechas_mdy'] = fechas_mdy
        r['incluye_vigencia'] = 'sí' if 'Sugerida' not in r['vigencia_final'] else 'no (sugerida)'
        r['vigencia_mdy'] = r['vigencia_final'].replace(' (Sugerida)', '') if 'Sugerida' in r['vigencia_final'] else r['vigencia_final']
        r['vigencia_sugerida_mdy'] = date_results.get('vigencia_sugerida') or ''

        # Autenticidad
        r['autenticidad_riesgo'] = riesgo
        r['autenticidad_detalles'] = ' | '.join(detalles or [])
        r['todas_las_fechas_sugeridas_mdy'] = fechas_mdy
        
        # 🆕 Policy Templates (Compliance 2025)
        if policy_data:
            r['policy_doc_country'] = policy_data.get('doc_country', '')
            r['policy_doc_type'] = policy_data.get('doc_type', '')
            r['policy_acceptance'] = policy_data.get('acceptance', '')
            r['policy_reason'] = policy_data.get('policy_reason', '')
            r['policy_evidence'] = '|'.join(policy_data.get('policy_evidence', []))
            r['policy_is_expired'] = 'Sí' if policy_data.get('is_expired', False) else 'No'
            r['policy_expiration_date'] = policy_data.get('expiration_date', '')
            r['policy_expiration_reason'] = policy_data.get('expiration_reason', '')
        else:
            r['policy_doc_country'] = ''
            r['policy_doc_type'] = ''
            r['policy_acceptance'] = ''
            r['policy_reason'] = ''
            r['policy_evidence'] = ''
            r['policy_is_expired'] = ''
            r['policy_expiration_date'] = ''
            r['policy_expiration_reason'] = ''
        
    except Exception as e:
        print(f"[HADES] Error al calcular metadata de resultado: {e}")

    # Registro de changelog
    registrar_changelog(f"Resultado guardado: {nombre} ({len(texto)} chars, {duracion_s:.2f}s, riesgo={riesgo}, usuario={usuario_correo})")


# ====== Drive upload (PATCHED) ======
def _validate_folder(service, folder_id: str):
    """
    Valida que el ID sea una CARPETA o un ACCESO DIRECTO a carpeta.
    Si es acceso directo, devuelve el ID del destino real.
    """
    try:
        meta = service.files().get(
            fileId=folder_id,
            fields="id,name,mimeType,shortcutDetails",
            supportsAllDrives=True
        ).execute()

        mt = meta.get("mimeType", "")
        if mt == "application/vnd.google-apps.folder":
            return True, {"id": meta["id"]}

        if mt == "application/vnd.google-apps.shortcut":
            target = meta.get("shortcutDetails", {}).get("targetId")
            if target:
                tmeta = service.files().get(
                    fileId=target,
                    fields="id,mimeType",
                    supportsAllDrives=True
                ).execute()
                if tmeta.get("mimeType") == "application/vnd.google-apps.folder":
                    return True, {"id": target}
            return False, "El acceso directo no apunta a una carpeta."

        return False, f"El ID no es carpeta (mimeType={mt})."
    except Exception as e:
        return False, f"No se pudo leer la carpeta (¿ID o permisos?): {e}"

def _subir_a_drive(ruta_archivo: str, nombre_remoto: str, mimetype: str):
    if "PEGA_AQUI" in DRIVE_FOLDER_ID or not DRIVE_FOLDER_ID:
        return False, "Configura DRIVE_FOLDER_ID en el código."

    last_err = "sin detalle"
    for scopes in (["https://www.googleapis.com/auth/drive.file"],
                   ["https://www.googleapis.com/auth/drive"]):
        try:
            service = _drive_service(scopes)
            ok, meta = _validate_folder(service, DRIVE_FOLDER_ID)
            if not ok:
                raise RuntimeError(str(meta))

            folder_real_id = meta["id"]
            file_metadata = {"name": nombre_remoto, "parents": [folder_real_id]}
            media = MediaFileUpload(ruta_archivo, mimetype=mimetype, resumable=False)
            created = service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, parents",
                supportsAllDrives=True
            ).execute()
            registrar_changelog(f"Drive: subido {nombre_remoto} ({created.get('id')}) a {folder_real_id}")
            return True, f"Subido a Drive (id={created.get('id')})."
        except Exception as e:
            last_err = str(e)
            continue

    # Diagnóstico de cuenta de servicio para ayudar a compartir la carpeta correcta
    try:
        sa = _load_sa_info()
        svc_mail = sa.get("client_email", "(sin client_email)")
    except Exception:
        svc_mail = "(no se pudo leer SA_JSON_B64)"

    return False, (
        "No se pudo subir a Drive.\n"
        f"• Cuenta de servicio: {svc_mail}\n"
        f"• Carpeta ID: {DRIVE_FOLDER_ID}\n"
        "• Verifica que esa carpeta esté compartida con la cuenta de servicio (Editor/Content Manager)\n"
        "• Si es un acceso directo, el parche ya resuelve el destino.\n"
        f"Detalle último intento: {last_err}"
    )




# ==========================================================
# =================== UI (Tkinter  =======================
# ==========================================================

# Definición de resource_path (necesaria para PyInstaller y archivos estáticos)
def resource_path(relative_path):
    """Obtiene la ruta absoluta, compatible con PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# Root: si hay tkinterdnd2, usamos su Tk para drag&drop nativo
if _DND_OK:
    root = TkinterDnD.Tk()
else:
    root = tk.Tk()
root.title(APP_TITLE); root.geometry("1120x740"); root.configure(bg=COLOR_BG)

# Ocultar ventana principal hasta que termine la autenticación
root.withdraw()

# ===== ESTILO TTK =====

style = ttk.Style(root)
style.theme_use('clam') 

# configuración de el estilo base 'Vertical.TScrollbar'
style.configure("Vertical.TScrollbar",
    troughcolor=COLOR_CARD,       # Color del canal (el fondo por donde corre)
    background=COLOR_BTN,         # Color del botón de la barra
    bordercolor=COLOR_GREEN,       # Color del borde
    arrowcolor=COLOR_GREEN         # Color de las flechas
)

# estilo para la "barra" (thumb) 
style.map("Vertical.TScrollbar",
    background=[
        ('!active', COLOR_BTN),     # Barra en estado normal
        ('active', ACCENT)          # Barra al pasar el mouse (morado brillante)
    ],
    troughcolor=[
        ('!active', COLOR_CARD),    # Canal en estado normal
        ('active', COLOR_CARD)      # Canal al pasar el mouse
    ]
)

try:
    root.iconbitmap(resource_path("Hades_ico.ico"))
except Exception:
    pass # Permite que se ejecute si no encuentra el icono

# Verificar acceso al iniciar (bloqueante)
def _verificar_inicio():
    # Flujo anterior (lista de correos en Sheets)
    for _ in range(3):
        correo = themed_askstring("Verificación", "Ingresa tu CORREO autorizado:", parent=root)
        if not correo:
            if messagebox.askyesno("Salir", "¿Deseas salir de HADES?"):
                root.destroy(); return False
            else:
                continue
        ok, nombre = verificar_correo_online(correo)
        if ok:
            usuario_actual["correo"]=correo; usuario_actual["nombre"]=nombre
            messagebox.showinfo("Verificado", "Acceso concedido.\nCorreo: {}".format(correo))
            return True
        else:
            messagebox.showerror("Acceso denegado", "Este correo no está autorizado.")
    root.destroy(); return False


# Header con imagen flama
header = tk.Frame(root, bg=COLOR_BG)
header.pack(fill="x", pady=(6, 0))

try:
    flama_img = Image.open(resource_path("flama2.png")) # ← Ruta dinámica
    flama_img = flama_img.resize((32, 32), Image.LANCZOS)
    flama_tk = ImageTk.PhotoImage(flama_img)
    flama_label = tk.Label(header, image=flama_tk, bg=COLOR_BG)
    flama_label.image = flama_tk # ← Previene que se borre por el recolector
    flama_label.pack(side="left", padx=(12, 6))
except Exception as e:
    # print(f"[HADES] No se pudo cargar flama2.png: {e}")
    pass

tk.Label(header, text="HADES: El Guardián de tu Información", bg=COLOR_BG, fg=COLOR_MUTED,
         font=("Segoe UI", 16, "bold")).pack(side="left", padx=6)

# Barra superior
bar = tk.Frame(root, bg=COLOR_PANEL); bar.pack(fill="x", pady=(6,0))

def configurar_api_keys():
    """Gestor de API Key para Gemini con hipervínculo"""
    global GEMINI_API_KEY
    
    if not usuario_actual["correo"]:
        messagebox.showinfo("API Keys", "Primero verifica tu correo (se hace al iniciar).")
        return
    
    # Crear ventana
    win = tk.Toplevel(root)
    win.title("Configurar API Key")
    win.configure(bg=COLOR_CARD)
    win.transient(root)
    win.grab_set()
    win.geometry("500x250")
    
    # Título
    tk.Label(win, text="🔑 Configuración de API Keys", bg=COLOR_CARD, fg=COLOR_TEXT,
             font=("Segoe UI", 13, "bold")).pack(pady=(16, 10))
    
    # Frame principal
    main_frame = tk.Frame(win, bg=COLOR_CARD)
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    # ===== GEMINI API KEY =====
    tk.Label(main_frame, text="Gemini API Key (Google):", bg=COLOR_CARD, fg=COLOR_TEXT,
             font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
    
    gemini_entry = tk.Entry(main_frame, bg="#1f1440", fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
                           highlightbackground=ACCENT_2, relief="flat", width=45, show="*")
    gemini_entry.grid(row=1, column=0, sticky="ew", pady=(0, 5))
    if GEMINI_API_KEY:
        gemini_entry.insert(0, GEMINI_API_KEY)
    
    # Hipervínculo Gemini
    link_gemini = tk.Label(main_frame, text="🔗 Obtener Gemini API Key", bg=COLOR_CARD, 
                          fg=COLOR_BLUE, cursor="hand2", font=("Segoe UI", 9, "underline"))
    link_gemini.grid(row=2, column=0, sticky="w", pady=(0, 15))
    link_gemini.bind("<Button-1>", lambda e: webbrowser.open("https://aistudio.google.com/app/apikey"))
    
    main_frame.grid_columnconfigure(0, weight=1)
    
    # Botones
    btn_frame = tk.Frame(win, bg=COLOR_CARD)
    btn_frame.pack(pady=(0, 16))
    
    def guardar():
        global GEMINI_API_KEY
        gemini_key = gemini_entry.get().strip()
        
        if gemini_key:
            GEMINI_API_KEY = gemini_key
            status.config(text="✅ API Key configurada: Gemini")
        else:
            status.config(text="⚠️ No se configuró API Key")
        
        win.destroy()
    
    tk.Button(btn_frame, text="💾 Guardar", command=guardar, bg=COLOR_PURPLE, fg="white",
             relief="flat", padx=20, pady=10, width=12).pack(side="left", padx=5)
    tk.Button(btn_frame, text="❌ Cancelar", command=win.destroy, bg=COLOR_BTN, fg="white",
             relief="flat", padx=20, pady=10, width=12).pack(side="left", padx=5)
    
    # Centrar ventana
    root.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width()//2 - 250)
    y = root.winfo_rooty() + (root.winfo_height()//2 - 125)
    try:
        win.geometry(f"+{x}+{y}")
    except:
        pass

def seleccionar_modelo():
    """Muestra un menú para seleccionar el modelo de Gemini"""
    global GEMINI_MODEL
    
    # Crear ventana de selección
    win = tk.Toplevel(root)
    win.title("Seleccionar Modelo Gemini")
    win.configure(bg=COLOR_CARD)
    win.transient(root)
    win.grab_set()
    
    tk.Label(win, text="Selecciona el modelo de Gemini:", bg=COLOR_CARD, fg=COLOR_TEXT, 
          font=("Segoe UI", 11, "bold")).pack(pady=(14, 10))
    
    # Modelos disponibles
    modelos = {
        "Gemini 2.0 Flash (Experimental)": "gemini-2.0-flash-exp",
        "Gemini 1.5 Flash (Recomendado)": "gemini-1.5-flash",
        "Gemini 1.5 Pro": "gemini-1.5-pro",
        "Gemini 1.0 Pro Vision": "gemini-1.0-pro-vision"
    }
    
    def elegir(nombre_modelo, id_modelo):
        global GEMINI_MODEL
        GEMINI_MODEL = id_modelo
        status.config(text=f"✅ Modelo: {nombre_modelo}")
        win.destroy()
    
    # Botones para cada modelo
    for nombre, id_modelo in modelos.items():
        color_btn = COLOR_PURPLE if id_modelo == GEMINI_MODEL else COLOR_BTN
        btn = tk.Button(win, text=nombre, command=lambda n=nombre, i=id_modelo: elegir(n, i),
                    bg=color_btn, fg="white", relief="flat", padx=20, pady=12, width=30)
        btn.pack(pady=4, padx=20)
    
    # Centrar ventana
    root.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width()//2 - 200)
    y = root.winfo_rooty() + (root.winfo_height()//2 - 150)
    try:
        win.geometry(f"+{x}+{y}")
    except Exception:
        pass

def seleccionar_proveedor():
    """Selector de proveedor de IA (Gemini / Claude)"""
    global AI_PROVIDER
    
    win = tk.Toplevel(root)
    win.title("Seleccionar Proveedor de IA")
    win.configure(bg=COLOR_CARD)
    win.transient(root)
    win.grab_set()
    
    tk.Label(win, text="¿Qué proveedor de IA quieres usar?", bg=COLOR_CARD, fg=COLOR_TEXT,
             font=("Segoe UI", 11, "bold")).pack(pady=(14, 10))
    
    tk.Label(win, text="(El otro se usará como backup automático)", bg=COLOR_CARD, fg=COLOR_MUTED,
             font=("Segoe UI", 9)).pack(pady=(0, 10))
    
    def elegir(proveedor):
        global AI_PROVIDER
        AI_PROVIDER = proveedor
        status.config(text=f"✅ Proveedor: {proveedor.upper()}")
        win.destroy()
    
    # Botones
    btn_gemini = tk.Button(win, text="🔷 Gemini (Google)", 
                          command=lambda: elegir("gemini"),
                          bg=COLOR_PURPLE if AI_PROVIDER == "gemini" else COLOR_BTN,
                          fg="white", relief="flat", padx=20, pady=12, width=25)
    btn_gemini.pack(pady=4, padx=20)
    
    btn_claude = tk.Button(win, text="🟣 Claude (Anthropic)", 
                          command=lambda: elegir("claude"),
                          bg=COLOR_PURPLE if AI_PROVIDER == "claude" else COLOR_BTN,
                          fg="white", relief="flat", padx=20, pady=12, width=25)
    btn_claude.pack(pady=4, padx=20)
    
    # Centrar
    root.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width()//2 - 150)
    y = root.winfo_rooty() + (root.winfo_height()//2 - 100)
    try:
        win.geometry(f"+{x}+{y}")
    except:
        pass

btn_cargar = tk.Button(bar, text="Cargar imágenes", bg=COLOR_GREEN, fg="white", relief="flat", padx=10, pady=8,
                       command=lambda: cargar_imagenes()); btn_cargar.pack(side="left", padx=8, pady=8)
btn_preview = tk.Button(bar, text="Previsualización", bg=COLOR_PURPLE, fg="white", relief="flat", padx=10, pady=8,
                        command=lambda: abrir_previsualizacion()); btn_preview.pack(side="left", padx=(0,8), pady=8)

btn_api = tk.Button(bar, text="🔑 Configurar API Keys", bg=COLOR_PURPLE, fg=COLOR_TEXT, relief="flat", padx=10, pady=8,
                    command=configurar_api_keys); btn_api.pack(side="left", padx=(0,8), pady=8)
btn_pegar = tk.Button(bar, text="Pegar imagen (Ctrl+V)", bg=COLOR_GREEN, fg=COLOR_TEXT, relief="flat", padx=10, pady=8,
                      command=lambda: pegar_imagen_clipboard()); btn_pegar.pack(side="left", padx=(0,8), pady=8)

# Layout principal (solo panel derecho + vistas)
main = tk.Frame(root, bg=COLOR_BG); main.pack(fill="both", expand=True)
right = tk.Frame(main, bg=COLOR_CARD); right.pack(side="left", fill="both", expand=True)

# Título + status (status ahora bajo el título, a la derecha)
title_row = tk.Frame(right, bg=COLOR_CARD); title_row.pack(fill="x", pady=(10,0))
tk.Label(title_row, text="Resultado OCR", bg=COLOR_CARD, fg=COLOR_TEXT, font=("Segoe UI", 12, "bold")).pack(side="left", padx=12)
status = tk.Label(title_row, text="Arrastra y suelta imágenes aquí, o usa Cargar / Ctrl+V.", bg=COLOR_CARD, fg=COLOR_MUTED)
status.pack(side="right", padx=12)

# --- Contenedor de vistas (solo OCR) ---
view_wrap = tk.Frame(right, bg=COLOR_CARD); view_wrap.pack(fill="both", expand=True)

# OCR view (con scrollbar)
ocr_container = tk.Frame(view_wrap, bg=COLOR_CARD)

# 1. Crear el Scrollbar TTK (tematizado)
ocr_scrollbar = ttk.Scrollbar(ocr_container, orient="vertical")

# 2. Crear el widget Text y conectarlo al scrollbar (yscrollcommand)
ocr_text = tk.Text(ocr_container, bg="#0f172a", fg=COLOR_TEXT, insertbackground=COLOR_TEXT, 
                   wrap="word", highlightbackground=COLOR_PURPLE, 
                   highlightcolor=COLOR_PURPLE, highlightthickness=2,
                   yscrollcommand=ocr_scrollbar.set) 

# 3. Configurar el Scrollbar para que controle al texto (command)
ocr_scrollbar.config(command=ocr_text.yview)

# 4. Empaquetar (Scrollbar a la derecha, Texto a la izquierda)
ocr_scrollbar.pack(side="right", fill="y", padx=(0, 12), pady=(12, 12))
ocr_text.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(12, 12))

_set_mode_ocr = lambda: (_clear_view(), ocr_container.pack(fill="both", expand=True)) # Definición limpia# ====== Logo de fondo en panel OCR ======
_BG_LOGO_LABEL = None
_BG_LOGO_IMG = None
def _show_logo_bg():
    import os, tkinter as tk
    from PIL import Image, ImageTk
    global _BG_LOGO_LABEL, _BG_LOGO_IMG
    try:
        # PULIDO: Usar resource_path para PyInstaller
        logo_path = resource_path("Logo_Hades.png")
        if not os.path.exists(logo_path):
            return
        img = Image.open(logo_path)
        base_w = 380
        w, h = img.size
        if w > base_w:
            ratio = base_w / float(w)
            img = img.resize((int(w*ratio), int(h*ratio)))
        _BG_LOGO_IMG = ImageTk.PhotoImage(img)
        if _BG_LOGO_LABEL is None:
            _BG_LOGO_LABEL = tk.Label(ocr_container, image=_BG_LOGO_IMG, bg=COLOR_CARD)
        else:
            _BG_LOGO_LABEL.configure(image=_BG_LOGO_IMG, bg=COLOR_CARD)
        _BG_LOGO_LABEL.place(relx=0.5, rely=0.5, anchor="center")
        _BG_LOGO_LABEL.lift()
    except Exception:
        pass
def _hide_logo_bg():
    global _BG_LOGO_LABEL
    try:
        if _BG_LOGO_LABEL is not None:
            _BG_LOGO_LABEL.place_forget()
    except Exception:
        pass


_show_logo_bg()

# --- Pie de página con botones (abajo de todo) ---
footer = tk.Frame(root, bg=COLOR_PANEL); footer.pack(fill="x")
btn_analizar = tk.Button(footer, text="🔍 Analizar", bg=COLOR_PURPLE, fg="white", relief="flat", padx=12, pady=10,
                         command=lambda: analizar_carrusel()); btn_analizar.pack(side="left", padx=8, pady=10)
btn_ident = tk.Button(footer, text="🪪 Analizar identificación", bg=COLOR_PURPLE, fg=COLOR_TEXT, relief="flat", padx=12, pady=10,
                        command=lambda: analizar_identificacion()); btn_ident.pack(side="left", padx=8, pady=10)
btn_export = tk.Button(footer, text="💾 Exportar", bg=COLOR_GREEN, fg=COLOR_TEXT, relief="flat", padx=12, pady=10,
                       command=lambda: exportar_resultados()); btn_export.pack(side="left", padx=8, pady=10)
btn_borrar = tk.Button(footer, text="🧹 Borrar", bg=COLOR_RED, fg="white", relief="flat", padx=12, pady=10,
                       command=lambda: borrar_todo()); btn_borrar.pack(side="left", padx=8, pady=10)

# ========= TOGGLE VIEW =========
def _clear_view():
    for w in view_wrap.winfo_children(): w.pack_forget()


# ========= IMÁGENES =========
def _add_images(file_list):
    added=0
    for f in file_list:
        p=Path(f)
        if p.exists() and p.suffix.lower() in {".png",".jpg",".jpeg",".bmp",".tif",".tiff",".webp"}:
            rutas.append(str(p)); added+=1
    if added:
        global idx
        if idx == -1: idx = 0
        status.config(text=f"Se agregaron {added} imagen(es). Total: {len(rutas)}")

def cargar_imagenes():
    files = filedialog.askopenfilenames(title="Selecciona imágenes", filetypes=[("Imágenes", ".png .jpg .jpeg .bmp .tif .tiff .webp")])
    if files: _add_images(files)

def pegar_imagen_clipboard():
    try:
        data = ImageGrab.grabclipboard()
        if hasattr(data, "save"):
            bio=io.BytesIO(); data.save(bio, format="PNG")
            # PULIDO: Se movió la creación de temporales a la carpeta local para facilitar el acceso en análisis
            temp=Path(os.getcwd())/f"clipboard_{int(time.time())}.png"
            with open(temp, "wb") as f: f.write(bio.getvalue())
            _add_images([str(temp)])
        elif isinstance(data, list): _add_images(data)
        else: messagebox.showinfo("Portapapeles", "No hay imagen en el portapapeles.")
    except Exception as e:
        messagebox.showwarning("Portapapeles", f"No se pudo leer el portapapeles: {e}")

# --- Drag & Drop (usa tkinterdnd2 si está instalado) ---
def _parse_dnd_paths(raw: str):
    # Windows: {C:\con espacios\img 1.png} {C:\otra.png}
    paths, buf, in_brace = [], "", False
    for ch in raw:
        if ch == "{": in_brace = True; buf = ""; continue
        if ch == "}": in_brace = False; paths.append(buf); buf = ""; continue
        if ch == " " and not in_brace:
            if buf: paths.append(buf); buf = ""
        else:
            buf += ch
    if buf: paths.append(buf)
    return paths

def _handle_drop(event):
    _add_images(_parse_dnd_paths(event.data))

if _DND_OK:
    ocr_container.drop_target_register(DND_FILES)
    ocr_container.dnd_bind("<<Drop>>", _handle_drop)


# ========= PREVISUALIZACIÓN =========
preview_win=None; preview_canvas=None; preview_imgtk=None; rot=0; idx=-1
def abrir_previsualizacion():
    global preview_win
    if not rutas: messagebox.showinfo("Previsualización", "Primero agrega imágenes."); return
    if preview_win and tk.Toplevel.winfo_exists(preview_win): preview_win.lift(); return
    _build_preview_modal()
def _build_preview_modal():
    global preview_win, preview_canvas, idx, rot
    preview_win = tk.Toplevel(root); preview_win.title("Previsualización"); preview_win.configure(bg=COLOR_PANEL); preview_win.geometry("780x560")
    top = tk.Frame(preview_win, bg=COLOR_PANEL); top.pack(fill="x")
    tk.Label(top, text="Navega y rota tus imágenes", bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side="left", padx=12, pady=8)
    tk.Button(top, text="⟵ Atrás", bg=COLOR_BTN, fg=COLOR_TEXT, relief="flat", padx=10, command=lambda: mover(-1)).pack(side="right", padx=4, pady=8)
    tk.Button(top, text="Siguiente ⟶", bg=COLOR_BTN, fg=COLOR_TEXT, relief="flat", padx=10, command=lambda: mover(1)).pack(side="right", padx=4, pady=8)
    tk.Button(top, text="↻ Rotar", bg=COLOR_PURPLE, fg="black", relief="flat", padx=10, command=rotar_actual).pack(side="right", padx=12)
    wrap = tk.Frame(preview_win, bg=COLOR_PANEL); wrap.pack(fill="both", expand=True, padx=12, pady=12)
    preview_canvas = tk.Canvas(wrap, bg="#0f172a", highlightthickness=0); preview_canvas.pack(fill="both", expand=True)
    preview_canvas.bind("<Configure>", lambda e: mostrar_imagen_en_canvas(preview_canvas))
    if idx < 0 and rutas: idx = 0; rot = 0
    mostrar_imagen_en_canvas(preview_canvas)
def mover(delta):
    global idx, rot
    if not rutas: return
    idx = (idx + delta) % len(rutas); rot = 0
    if preview_canvas: mostrar_imagen_en_canvas(preview_canvas)
def rotar_actual():
    global rot
    rot = (rot + 90) % 360
    if preview_canvas: mostrar_imagen_en_canvas(preview_canvas)
def mostrar_imagen_en_canvas(canvas):
    global preview_imgtk
    if not rutas or idx < 0: return
    try:
        im = PILImage.open(rutas[idx]).convert("RGBA")
        if rot: im = im.rotate(rot, expand=True)
        cw = canvas.winfo_width() or 1; ch = canvas.winfo_height() or 1
        im_ratio = im.width / im.height; canvas_ratio = cw / ch
        if im_ratio > canvas_ratio: new_w=cw; new_h=int(cw/im_ratio)
        else: new_h=ch; new_w=int(ch*im_ratio)
        im = im.resize((max(1,new_w), max(1,new_h)), PILImage.LANCZOS)
        preview_imgtk = ImageTk.PhotoImage(im)
        canvas.delete("all")
        canvas.create_image(cw//2, ch//2, image=preview_imgtk, anchor="center")
        canvas.create_text(8, ch-8, anchor="sw", text=f"{idx+1}/{len(rutas)} — {Path(rutas[idx]).name}", fill="#9ca3af")
    except Exception as e:
        canvas.delete("all"); canvas.create_text(10, 10, anchor="nw", text=f"No se pudo cargar la imagen: {e}", fill="#ef4444")


# FUNCIÓN CORREGIDA Y SACADA DE AMBOS ANALIZAR_* PARA USO COMPARTIDO
def _format_ocr_text_with_normalized_dates(t: str, results: Dict[str, Optional[str]]):
    """Formatea el texto OCR en el widget de texto.
    - Sustituye fechas por sus versiones normalizadas/finales (incluye pares clave:valor detectados).
    - Resalta en VERDE los campos considerados ESENCIALES directamente en el panel.
    """

    def _clean_key_for_matching(key_text: str) -> str:
        """
        Limpia una clave para comparación:
        1) minúsculas
        2) sin acentos
        3) sin puntuación (.,:;_-)
        4) espacios normalizados
        """
        if not key_text:
            return ""
        s = key_text.lower()
        try:
            s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        except Exception:
            pass
        s = re.sub(r'[.,:;_\-]+', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    # --- 1) Mapeo "por prefijos" (DOB / Emisión / Expiración) ---
    key_mapping: Dict[str, Optional[str]] = {}

    for key_prefix in ["fecha de nacimiento", "dob", "date of birth", r"^nacimient[oa]$"]:
        key_mapping[key_prefix] = results.get("fecha_nacimiento_final")
    for key_prefix in ["emision", "expedicion", "expedición", "issue", "issued", "fecha de emision", "fecha de expedicion", "emitido", "fecha de emi", "date of issue"]:
        key_mapping[key_prefix] = results.get("fecha_expedicion_final")
    for key_prefix in [
        "vencimiento", "vence", "expiración", "expiracion", "vigencia",
        "valido hasta", "válido hasta", "valid thru", "valid through", "valid until",
        "caducidad", "fecha de caducidad",
        "expires", "expire", "expiry", "expiration", "date of expiry", "date of expiration",
        "fecha de vencimiento", "fecha de expiracion", "fecha de expiración",
    ]:
        key_mapping[key_prefix] = results.get("fecha_vigencia_final")

    # --- 2) Mapeo exacto (kv_map) para normalizar cualquier par clave:valor con fecha detectada ---
    kv_map_raw = results.get("kv_map") or {}
    kv_map_clean: Dict[str, str] = {}
    try:
        for k, v in kv_map_raw.items():
            if not k or not v:
                continue
            kv_map_clean[_clean_key_for_matching(k)] = str(v)
    except Exception:
        kv_map_clean = {}

    # --- 2b) Mapa de sustitución directa de fechas numéricas (DD/MM/YYYY → MM/DD/YYYY) ---
    date_sub_map: Dict[str, str] = results.get("date_substitution_map") or {}

    inferred_country = (results.get("doc_pais") or "").strip()

    # --- 3) Campos esenciales (se resaltan en verde) ---
    essential_keywords_clean = {
        # País
        "pais", "country", "nationality", "nacionalidad",
        # Nombre y apellidos
        "nombre", "nombres", "apellido", "apellidos", "apellido paterno", "apellido materno", "segundo apellido",
        # Fecha de Nacimiento
        "fecha de nacimiento", "dob", "date of birth",
        # Tipo de Identificacion
        "tipo de documento", "tipo de identificacion", "tipo", "clase", "dl class",
        # Numero de Identificacion
        "numero de identificacion", "numero de id", "numero de documento", "documento personal de identificacion",
        "numero de pasaporte", "pasaporte", "pasaporte no", "passport no",
        "clave de elector", "cui", "dpi", "id number",
        "license number", "numero de licencia", "no licencia",
        "numero de matricula", "matricula consular",
        # Fecha de Expiracion
        "fecha de expiracion", "expiracion", "fecha de caducidad", "caducidad",
        "vigencia", "vence", "valido hasta", "valid thru", "valid through", "valid until", "fecha de vencimiento",
        "expires", "expire", "expiry", "expiration", "date of expiry", "date of expiration",
    }

    # Configuración de estilos para el resaltado
    try:
        ocr_text.tag_config("essential_value", font=("Segoe UI", 10, "bold"), foreground=COLOR_GREEN)
    except Exception:
        pass

    def _apply_date_subs(text_fragment: str) -> str:
        """Sustituye fechas DD/MM/YYYY → MM/DD/YYYY en un fragmento usando date_sub_map."""
        if not date_sub_map or not text_fragment:
            return text_fragment
        result = text_fragment
        for orig, conv in sorted(date_sub_map.items(), key=lambda x: -len(x[0])):
            result = result.replace(orig, conv)
        return result

    for line in (t or "").splitlines():
        if ":" not in line:
            # Línea sin ':' → aplicar sustitución directa de fechas
            ocr_text.insert("end", _apply_date_subs(line) + "\n")
            continue

        parts = line.split(":", 1)
        if len(parts) != 2:
            ocr_text.insert("end", line + "\n")
            continue

        key = parts[0].strip()
        original_value = parts[1].strip()

        key_lower = key.lower()
        key_clean = _clean_key_for_matching(key)

        normalized_value = None

        # 1) Preferimos el mapeo exacto por clave (kv_map) si existe
        if key_clean in kv_map_clean:
            normalized_value = (kv_map_clean.get(key_clean) or "").strip()

        # 2) Si no hay exact match, usamos el mapeo por prefijo (DOB/EXP/ISSUE)
        if not normalized_value:
            for key_prefix, processed_date in key_mapping.items():
                # mantenemos key_lower para que el regex ^nacimient[oa]$ funcione
                if re.search(key_prefix, key_lower):
                    normalized_value = (processed_date or "").strip()
                    break

        # 3) Fallback: sustitución directa de fechas en el valor si no se resolvió por clave
        if normalized_value:
            value_to_show = normalized_value
        else:
            value_to_show = _apply_date_subs(original_value)

        # Si el OCR/LLM se equivoca en "País: XX", preferimos el país inferido por HADES.
        if inferred_country and key_clean in ("pais", "country"):
            value_to_show = inferred_country

        # ¿Es un campo esencial?
        is_essential = any(kw in key_clean for kw in essential_keywords_clean)
        tag = "essential_value" if is_essential else "value_bold"

        ocr_text.insert("end", f"{key}: ")
        ocr_text.insert("end", f"{value_to_show}\n", tag)

def analizar_actual():
    global idx
    if not rutas:
        messagebox.showinfo("HADES", "No hay imágenes cargadas."); return
    if idx < 0:
        idx = 0
    p = rutas[idx]
    t0 = time.time()
    _hide_logo_bg()
    
    # Mostrar mensaje de procesamiento
    ocr_text.delete("1.0", "end")
    ocr_text.insert("end", "⏳ Procesando imagen con Gemini Vision...\n", "processing")
    ocr_text.tag_config("processing", font=("Segoe UI", 11, "italic"), foreground=ACCENT)
    root.update()  # Actualizar UI inmediatamente
    
    # 1. OCR y Normalización (solo Gemini)
    texto = gemini_vision_extract_text(p)
    
    # Actualizar progreso
    ocr_text.insert("end", "✓ OCR completado\n⏳ Analizando autenticidad...\n", "processing")
    root.update()  # Mantener UI responsiva
    # Se mantiene la normalización para extraer metadatos de riesgo y exportación
    texto_normalizado_diag, _pairs, doc_pais, fmt = _normalize_all_dates_with_pairs(texto)
    
    # 2. Extracción de datos esenciales y autenticidad
    date_results = _process_all_dates_by_type(texto)
    vigencia_final = date_results.get("fecha_vigencia_final")
    nombre_completo = _extract_name(texto)
    tipo_id = _extract_id_type(texto, doc_pais)
    num_id = _extract_id_number(texto, doc_pais)
    
    datos_esenciales = {
        "nombre": nombre_completo,
        "fecha_nacimiento_original": _extract_dob(texto)[0],
        "fecha_nacimiento_sugerida_mdy": date_results.get("fecha_nacimiento_final"),
        "vigencia_original": texto,
        "vigencia_sugerida_mdy": vigencia_final,
    }
    # NOTA: Se pasa el texto original a _authenticity_score para que use la detección de país
    riesgo, detalles, emoji, color = _authenticity_score(texto, p)
    
    # 🆕 Policy Templates (Compliance 2025)
    policy_data = None
    if _POLICY_TEMPLATES_OK and classify_document:
        policy_data = classify_document(texto)
        # Ajustar score con policy
        policy_adj, policy_adj_reason = policy_score_adjustment(policy_data['acceptance'])
        # Agregar ajuste a detalles
        if policy_adj > 0:
            detalles.append(policy_adj_reason)
    
    dt = round(time.time() - t0, 2)

    # 3. Guardar resultados
    # Usamos el texto original para que el exportador trabaje con el output de Gemini
    _guardar_resultado(Path(p).name, texto, "actual", dt, datos_esenciales, riesgo, detalles, policy_data)
    
    # 4. Mostrar en el panel
    ocr_text.delete("1.0", "end") # Limpiamos antes de mostrar
        
    # Bloque de Resultado 1/1 (Formato de carrusel)
    nombre_archivo = Path(p).name
    ocr_text.insert("end", f"\nRESULTADO 1/1 — {nombre_archivo}\n", "header")
    ocr_text.tag_config("header", font=("Segoe UI", 12, "bold"), foreground=ACCENT_2)
    
    # Mostrar proveedor usado (siempre Gemini ahora)
    ocr_text.insert("end", f"Analizado con: Gemini\n", "provider_tag")
    ocr_text.tag_config("provider_tag", foreground=COLOR_MUTED, font=("Segoe UI", 9, "italic"))
    
    # Mostrar semáforo de autenticidad
    ocr_text.insert("end", f"\n{emoji} Riesgo de falsificación: {riesgo.upper()}\n", "risk_tag")
    if color == "green":
        ocr_text.tag_config("risk_tag", foreground=COLOR_GREEN, font=("Segoe UI", 11, "bold"))
    elif color == "yellow":
        ocr_text.tag_config("risk_tag", foreground="#FFD700", font=("Segoe UI", 11, "bold"))
    else:
        ocr_text.tag_config("risk_tag", foreground=COLOR_RED, font=("Segoe UI", 11, "bold"))
    # Mostrar solo mensajes genéricos al usuario
    if detalles:
        ocr_text.insert("end", f"{'; '.join(detalles)}\n", "body_header")
    
    # Se imprime solo la línea de país limpia
    ocr_text.insert("end", f"\nTexto Completo (OCR original):\n", "body_header")
    ocr_text.tag_config("body_header", font=("Segoe UI", 10, "bold"), foreground=COLOR_TEXT)
    
    # País (una sola vez por ID)
    if doc_pais:
        ocr_text.insert("end", f"País: {doc_pais}\n", "essential_value")
    
    # Mostrar el texto OCR, sustituyendo las fechas por las procesadas (LLAMADA A LA FUNCIÓN CORREGIDA)
    ocr_text.tag_config("value_bold", font=("Segoe UI", 10, "bold"), foreground=COLOR_TEXT)
    texto_listo = texto.replace('\\n', '\n')
    _format_ocr_text_with_normalized_dates(texto_listo, date_results)
    
    ocr_text.see("end")
    root.update_idletasks() # Forzar el despliegue
    
    # Exportar directamente a Drive sin pedir feedback
    root.after(0, safe_export_drive)

def analizar_carrusel():
    """Analiza TODAS las imágenes y muestra cada resultado en el panel conforme avanza."""
    if not rutas:
        messagebox.showinfo("HADES", "No hay imágenes cargadas."); return

    total = len(rutas)
    _hide_logo_bg()
    ocr_text.delete("1.0", "end")
    
    # Mostrar mensaje inicial
    ocr_text.insert("end", f"⏳ Procesando {total} imágenes...\n\n", "processing")
    ocr_text.tag_config("processing", font=("Segoe UI", 11, "bold"), foreground=ACCENT)
    root.update()  # Actualizar UI # Limpiamos el panel
    
    # Configurar negrita para carrusel
    ocr_text.tag_config("value_bold", font=("Segoe UI", 10, "bold"), foreground=COLOR_TEXT)
    ocr_text.tag_config("header", font=("Segoe UI", 12, "bold"), foreground=ACCENT_2)
    ocr_text.tag_config("essential_header", font=("Segoe UI", 12, "bold"), foreground=ACCENT_2) # Tag para DATOS ESENCIALES
    ocr_text.tag_config("risk_tag", foreground=COLOR_GREEN, font=("Segoe UI", 10, "bold")) # Por defecto verde

    for i in range(total):
        p = rutas[i]
        t0 = time.time()
        
        # Actualizar progreso
        ocr_text.insert("end", f"\n[{i+1}/{total}] Procesando {Path(p).name}...\n", "progress")
        ocr_text.tag_config("progress", font=("Segoe UI", 10, "italic"), foreground=COLOR_MUTED)
        ocr_text.see("end")
        root.update()  # Mantener UI responsiva
        
        try:
            # 1. OCR y Normalización (solo Gemini)
            texto = gemini_vision_extract_text(p)
            texto_normalizado_diag, _pairs, doc_pais, fmt = _normalize_all_dates_with_pairs(texto)
            
            # 2. Extracción de datos esenciales y autenticidad (solo para registro)
            date_results = _process_all_dates_by_type(texto)
            vigencia_final = date_results.get("fecha_vigencia_final")
            expedicion_final = date_results.get("fecha_expedicion_final")
            nacimiento_final = date_results.get("fecha_nacimiento_final")
            
            nombre_completo = _extract_name(texto)
            tipo_id = _extract_id_type(texto, doc_pais)
            num_id = _extract_id_number(texto, doc_pais)
            
            datos_esenciales = {
                "nombre": nombre_completo,
                "fecha_nacimiento_original": _extract_dob(texto)[0],
                "fecha_nacimiento_sugerida_mdy": nacimiento_final,
                "vigencia_original": texto,
                "vigencia_sugerida_mdy": vigencia_final,
            }

            riesgo, detalles, emoji, color = _authenticity_score(texto, p)
            dt = round(time.time() - t0, 2)

            # 3. Guardar resultados
            _guardar_resultado(Path(p).name, texto, "carrusel", dt, datos_esenciales, riesgo, detalles)

            # 4. Mostrar en el panel (SOLO OCR y autenticidad)
            nombre_archivo = Path(p).name
            doc_pais_actual = _infer_doc_country(texto) # Re-obtener el país por si las claves de GTM/PHL funcionan mejor ahora
            
            # Mostrar encabezado de resultado
            ocr_text.insert("end", f"\n\nRESULTADO {i+1}/{total} — {nombre_archivo}\n", "header")
            
            # Mostrar proveedor usado (siempre Gemini ahora)
            ocr_text.insert("end", f"Analizado con: Gemini\n", "provider_tag")
            ocr_text.tag_config("provider_tag", foreground=COLOR_MUTED, font=("Segoe UI", 9, "italic"))
            
            # Mostrar semáforo de autenticidad (tag único por resultado)
            risk_tag = f"risk_tag_{i}"
            ocr_text.insert("end", f"\n{emoji} Riesgo de falsificación: {riesgo.upper()}\n", risk_tag)
            if color == "green":
                ocr_text.tag_config(risk_tag, foreground=COLOR_GREEN, font=("Segoe UI", 11, "bold"))
            elif color == "yellow":
                ocr_text.tag_config(risk_tag, foreground="#FFD700", font=("Segoe UI", 11, "bold"))
            else:
                ocr_text.tag_config(risk_tag, foreground=COLOR_RED, font=("Segoe UI", 11, "bold"))
            # Mostrar solo mensajes genéricos al usuario
            if detalles:
                ocr_text.insert("end", f"{'; '.join(detalles)}\n", "body_header")

            # País (una sola vez por ID)
            if doc_pais_actual:
                ocr_text.insert("end", f"País: {doc_pais_actual}\n", "essential_value")

            # Mostrar texto OCR con negritas en valores
            texto_listo = texto.replace('\\n', '\n')
            _format_ocr_text_with_normalized_dates(texto_listo, date_results)
            
            ocr_text.see("end")
            root.update_idletasks()
            
        except Exception as e:
            err_msg = f"❌ Error en Visión o procesamiento de {Path(p).name}: {e}"
            ocr_text.insert("end", f"\n\n===== {i}/{total} — {Path(p).name} =====\n{err_msg}\n")
            root.update_idletasks()
            continue

    # Un solo feedback al finalizar todo el carrusel (y export a Drive)
    # Exportar directamente a Drive sin pedir feedback
    root.after(0, safe_export_drive)

def analizar_identificacion():
    """
    Analiza identificaciones que tienen frente y reverso.
    Toma las imágenes cargadas en pares (1-2, 3-4, ...) y muestra en el panel:
      • Parte frontal (Imagen 1)
      • Parte reversa (Imagen 2)
    con el texto de cada lado por separado.
    Además, sigue guardando un solo resultado combinado para exportar.
    """
    if not rutas:
        messagebox.showinfo("HADES", "No hay imágenes cargadas.")
        return

    if len(rutas) < 2:
        messagebox.showinfo(
            "HADES",
            "Para este modo carga al menos FRENTE y REVERSO de la identificación (2 imágenes).",
        )
        return

    _hide_logo_bg()
    ocr_text.delete("1.0", "end")

    total_ids = len(rutas) // 2  # cada par = 1 identificación
    
    # Mostrar mensaje inicial
    ocr_text.insert("end", f"⏳ Procesando {total_ids} identificaciones (frente + reverso)...\n\n", "processing")
    ocr_text.tag_config("processing", font=("Segoe UI", 11, "bold"), foreground=ACCENT)
    root.update()  # Actualizar UI

    # Tags de formato
    ocr_text.tag_config("value_bold", font=("Segoe UI", 10, "bold"), foreground=COLOR_TEXT)
    ocr_text.tag_config("header", font=("Segoe UI", 12, "bold"), foreground=ACCENT_2)
    ocr_text.tag_config("body_header", font=("Segoe UI", 10, "bold"), foreground=COLOR_TEXT)
    ocr_text.tag_config("essential_value", font=("Segoe UI", 10, "bold"), foreground=COLOR_GREEN)

    idx_doc = 0
    for i in range(0, len(rutas) - 1, 2):
        frente = rutas[i]
        reverso = rutas[i + 1]
        idx_doc += 1
        t0 = time.time()
        
        # Actualizar progreso
        ocr_text.insert("end", f"\n[{idx_doc}/{total_ids}] Procesando {Path(frente).name} + {Path(reverso).name}...\n", "progress")
        ocr_text.tag_config("progress", font=("Segoe UI", 10, "italic"), foreground=COLOR_MUTED)
        ocr_text.see("end")
        root.update()  # Mantener UI responsiva

        try:
            # === 1) OCR de frente y reverso (por separado) solo con Gemini ===
            texto_frente = gemini_vision_extract_text(frente)
            texto_reverso = gemini_vision_extract_text(reverso)

            # Texto combinado (lo que se guarda / exporta)
            texto_total = texto_frente + "\n" + texto_reverso

            # === 2) Normalización / metadata usando el texto combinado ===
            _, _pairs, doc_pais, fmt = _normalize_all_dates_with_pairs(texto_total)
            date_results = _process_all_dates_by_type(texto_total)
            vigencia_final = date_results.get("fecha_vigencia_final")
            nacimiento_final = date_results.get("fecha_nacimiento_final")
            nombre_completo = _extract_name(texto_total)
            tipo_id = _extract_id_type(texto_total, doc_pais)
            num_id = _extract_id_number(texto_total, doc_pais)

            datos_esenciales = {
                "nombre": nombre_completo,
                "fecha_nacimiento_original": _extract_dob(texto_total)[0],
                "fecha_nacimiento_sugerida_mdy": nacimiento_final,
                "vigencia_original": texto_total,
                "vigencia_sugerida_mdy": vigencia_final,
            }

            riesgo, detalles, emoji, color = _authenticity_score(texto_total, frente)
            dt = round(time.time() - t0, 2)

            # Nombre lógico para exportar (frente + reverso)
            nombre_logico = f"{Path(frente).name} + {Path(reverso).name}"
            _guardar_resultado(
                nombre_logico,
                texto_total,
                "identificacion",
                dt,
                datos_esenciales,
                riesgo,
                detalles,
            )

            # ===== 3) MOSTRAR EN PANEL =====

            # Encabezado general del ID
            header_line = (
                f"\n\nRESULTADO ID {idx_doc}/{total_ids} — "
                f"{Path(frente).name} + {Path(reverso).name} ({dt:.2f}s)\n"
            )
            ocr_text.insert("end", header_line, "header")
            
            # Mostrar semáforo de autenticidad (tag único por ID)
            risk_tag = f"risk_tag_id_{idx_doc}"
            ocr_text.insert("end", f"\n{emoji} Riesgo de falsificación: {riesgo.upper()}\n", risk_tag)
            if color == "green":
                ocr_text.tag_config(risk_tag, foreground=COLOR_GREEN, font=("Segoe UI", 11, "bold"))
            elif color == "yellow":
                ocr_text.tag_config(risk_tag, foreground="#FFD700", font=("Segoe UI", 11, "bold"))
            else:
                ocr_text.tag_config(risk_tag, foreground=COLOR_RED, font=("Segoe UI", 11, "bold"))
            # Mostrar solo mensajes genéricos al usuario
            if detalles:
                ocr_text.insert("end", f"{'; '.join(detalles)}\n", "body_header")

            # País (una sola vez por ID)
            if doc_pais:
                ocr_text.insert("end", f"País: {doc_pais}\n", "essential_value")

            # --- TEXTO FRONTAL ---
            ocr_text.insert(
                "end",
                f"\nParte frontal (Imagen 1 — {Path(frente).name}):\n",
                "body_header",
            )
            texto_frente_listo = texto_frente.replace("\\n", "\n")
            _format_ocr_text_with_normalized_dates(texto_frente_listo, date_results)

            # --- TEXTO REVERSO ---
            ocr_text.insert(
                "end",
                f"\nParte reversa (Imagen 2 — {Path(reverso).name}):\n",
                "body_header",
            )
            texto_reverso_listo = texto_reverso.replace("\\n", "\n")
            _format_ocr_text_with_normalized_dates(texto_reverso_listo, date_results)

            ocr_text.see("end")
            root.update_idletasks()

        except Exception as e:
            err_msg = (
                f"❌ Error en Visión o procesamiento de "
                f"{Path(frente).name} / {Path(reverso).name}: {e}"
            )
            ocr_text.insert("end", f"\n\n{err_msg}\n")
            root.update_idletasks()
            continue

    # Feedback + export a Drive al final
    # Exportar directamente a Drive sin pedir feedback
    root.after(0, safe_export_drive)

# Función de exportación directa a Drive (sin feedback)
def _export_drive_only():
    """Exporta resultados a Drive automáticamente en segundo plano."""
    import pandas as pd  # Lazy import
    import traceback
    
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    resumen_df = pd.DataFrame(resultados)
    if resumen_df.empty:
        print("[HADES] No hay resultados para exportar a Drive.")
        return

    # El correo ya está en los resultados (agregado en _guardar_resultado)
    # Columnas preferidas para el CSV (🆕 agregadas columnas de policy y expiración)
    preferred_order = ['usuario_correo','archivo','texto','duracion_s','tipo','doc_pais','formato_fecha_detectado',
                      'fecha_expedicion_final','vigencia_final','fecha_nacimiento_final','otras_fechas_final',
                      'fechas_mdy','incluye_vigencia','vigencia_mdy','vigencia_sugerida_mdy',
                      'autenticidad_riesgo','autenticidad_detalles',
                      'policy_doc_country','policy_doc_type','policy_acceptance','policy_reason','policy_evidence',
                      'policy_is_expired','policy_expiration_date','policy_expiration_reason']
    final_cols = [c for c in preferred_order if c in resumen_df.columns] + [c for c in resumen_df.columns if c not in preferred_order]
    resumen_df = resumen_df[final_cols]

    tmp_dir = tempfile.gettempdir()
    drive_tmp_csv = os.path.join(tmp_dir, f"HADES_OCR_{ts}.csv")
    
    try:
        # Crear CSV
        resumen_df.to_csv(drive_tmp_csv, index=False, encoding="utf-8-sig")
        
        # Validar que el CSV existe y no está vacío
        if not os.path.exists(drive_tmp_csv):
            error_msg = f"Error: El archivo CSV no se creó correctamente: {drive_tmp_csv}"
            print(f"[HADES] {error_msg}")
            messagebox.showerror("Error de Exportación", error_msg)
            return
        
        if os.path.getsize(drive_tmp_csv) == 0:
            error_msg = f"Error: El archivo CSV está vacío: {drive_tmp_csv}"
            print(f"[HADES] {error_msg}")
            messagebox.showerror("Error de Exportación", error_msg)
            return
        
        print(f"[HADES] CSV creado exitosamente: {drive_tmp_csv} ({os.path.getsize(drive_tmp_csv)} bytes)")
        
        # Subir a Drive
        remote_name = f"HADES_OCR_{ts}.csv"
        info_msgs = []
        ok, info = _subir_a_drive(drive_tmp_csv, remote_name, "text/csv")
        info_msgs.append(info)
        
        if ok:
            # Se extrae el ID de la respuesta para el log
            file_id = info.split('id=')[-1].split(')')[0]
            success_msg = f"CSV subido a Drive exitosamente (id={file_id})"
            print(f"[HADES] {success_msg}")
            registrar_changelog(f"Drive upload exitoso: {remote_name}")
            # Mostrar confirmación en status bar
            status.config(text=f"✅ Enviado a Drive: {len(resumen_df)} registros")
        else:
            error_msg = "No se pudo subir a Drive:\n" + " | ".join(info_msgs)
            print(f"[HADES] {error_msg}")
            registrar_changelog(f"Drive upload falló: {info}")
            # Mostrar error al usuario
            messagebox.showerror(
                "Error de Google Drive",
                f"No se pudo subir el archivo a Google Drive.\n\n{info}\n\nVerifica:\n"
                f"• Conexión a internet\n"
                f"• Permisos de la cuenta de servicio\n"
                f"• ID de carpeta: {DRIVE_FOLDER_ID}"
            )
    
    except Exception as e:
        error_detail = f"Error inesperado al exportar a Drive: {str(e)}"
        print(f"[HADES] {error_detail}")
        print(f"[HADES] Traceback:\n{traceback.format_exc()}")
        registrar_changelog(f"Drive upload error: {error_detail}")
        # Mostrar error al usuario
        messagebox.showerror(
            "Error de Exportación",
            f"Error al exportar a Drive:\n\n{str(e)}\n\nRevisa los logs para más detalles."
        )


def safe_export_drive():
    """
    Wrapper seguro para _export_drive_only que garantiza:
    1. Ejecución en el hilo principal de Tkinter
    2. Manejo de excepciones visible al usuario
    3. Validación de estado antes de exportar
    """
    try:
        # Verificar que tenemos resultados
        if not resultados:
            print("[HADES] No hay resultados para exportar (lista vacía)")
            return
        
        # Verificar que estamos en el hilo principal
        import threading
        if threading.current_thread() != threading.main_thread():
            print("[HADES] ADVERTENCIA: safe_export_drive llamado desde thread secundario")
            # Re-agendar en el hilo principal
            root.after(0, safe_export_drive)
            return
        
        print(f"[HADES] Iniciando exportación segura a Drive ({len(resultados)} resultados)")
        _export_drive_only()
        
    except Exception as e:
        import traceback
        error_msg = f"Error crítico en safe_export_drive: {str(e)}"
        print(f"[HADES] {error_msg}")
        print(f"[HADES] Traceback:\n{traceback.format_exc()}")
        registrar_changelog(f"safe_export_drive error: {error_msg}")
        
        # Mostrar error al usuario
        try:
            messagebox.showerror(
                "Error Crítico de Exportación",
                f"Error al intentar exportar a Drive:\n\n{str(e)}\n\n"
                f"El análisis se completó pero no se pudo subir a Drive.\n"
                f"Revisa los logs para más detalles."
            )
        except:
            # Si incluso el messagebox falla, al menos lo tenemos en logs
            print("[HADES] No se pudo mostrar messagebox de error")



def _do_export(destino_carpeta_local: str):
    import pandas as pd  # Lazy import
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(destino_carpeta_local, exist_ok=True)
    csv_path = os.path.join(destino_carpeta_local, f"HADES_OCR_{ts}.csv")
    txt_path = os.path.join(destino_carpeta_local, f"HADES_OCR_{ts}.txt")

    resumen_df = pd.DataFrame(resultados)
    if resumen_df.empty:
        messagebox.showinfo("Exportación", "No hay resultados para exportar localmente."); return

    # 🆕 Obtener el correo del usuario autenticado
    usuario_correo = "Sin autenticar"
    if keycloak_auth_instance and keycloak_auth_instance.is_authenticated():
        usuario_correo = keycloak_auth_instance.get_user_email() or "Sin correo"
    
    # Agregar el correo del usuario a todas las filas
    resumen_df['usuario_correo'] = usuario_correo

    # Usar las nuevas columnas finales para exportar los datos procesados
    # 🆕 Agregada 'usuario_correo' a las columnas exportadas
    cols = [c for c in ['usuario_correo','archivo','texto','duracion_s','tipo','doc_pais','formato_fecha_detectado','fecha_expedicion_final','vigencia_final','fecha_nacimiento_final','otras_fechas_final'] if c in resumen_df.columns]
    out_df = resumen_df[cols].copy() if cols else resumen_df.copy()
    out_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    with open(txt_path, 'w', encoding='utf-8') as f:
        for _, row in out_df.iterrows():
            f.write(f"Usuario: {row.get('usuario_correo','')}\n")
            f.write(f"Archivo: {row.get('archivo','')}\n")
            f.write(f"Duración (s): {row.get('duracion_s','')}\n")
            f.write(f"Tipo: {row.get('tipo','')}\n")
            f.write(f"País: {row.get('doc_pais','')}\n")
            f.write(f"Formato fecha detectado: {row.get('formato_fecha_detectado','')}\n")
            f.write(f"Fecha Expedición: {row.get('fecha_expedicion_final','')}\n")
            f.write(f"Vigencia: {row.get('vigencia_final','')}\n")
            f.write(f"Fecha Nacimiento: {row.get('fecha_nacimiento_final','')}\n")
            f.write(f"Otras Fechas: {row.get('otras_fechas_final','')}\n")
            f.write("Texto OCR original:\n")
            f.write(str(row.get('texto','')).strip() + "\n")
            f.write("-"*40 + "\n")
            f.write("-" * 60 + "\n")

    messagebox.showinfo("Exportación", f"Se guardaron archivos locales:\n• {os.path.basename(csv_path)}\n• {os.path.basename(txt_path)}")

def exportar_resultados():
    if not resultados:
        messagebox.showinfo("Exportar", "No hay resultados para exportar."); return
    carpeta = filedialog.askdirectory(title="Selecciona carpeta destino para exportar")
    if not carpeta:
        status.config(text="ℹ️ Exportación cancelada."); return
    _do_export(carpeta)

def borrar_todo():
    rutas.clear(); resultados.clear()
    ocr_text.delete("1.0", "end")
    _show_logo_bg() # Vuelve a mostrar el logo
    status.config(text="Se limpió el estado.")


# ========= PANTALLA DE BIENVENIDA CON AUTENTICACIÓN MANUAL =========
def mostrar_pantalla_bienvenida():
    """Muestra pantalla de bienvenida con botón de autenticación manual"""
    welcome = tk.Toplevel(root)
    welcome.title("HADES - Bienvenida")
    welcome.configure(bg=COLOR_BG)
    welcome.geometry("500x600")
    welcome.resizable(False, False)
    
    # Centrar ventana
    welcome.update_idletasks()
    x = (welcome.winfo_screenwidth() // 2) - (250)
    y = (welcome.winfo_screenheight() // 2) - (300)
    welcome.geometry(f"500x600+{x}+{y}")
    
    # Configurar ventana (permitir minimizar para autenticación)
    welcome.lift()
    welcome.focus_force()
    
    # Frame principal
    main_frame = tk.Frame(welcome, bg=COLOR_BG)
    main_frame.pack(expand=True, fill="both", padx=40, pady=40)
    
    # Logo de HADES (si existe)
    try:
        logo_path = Path(__file__).parent / "Logo_Hades.png"
        if logo_path.exists():
            logo_img = Image.open(logo_path)
            # Redimensionar logo
            logo_img.thumbnail((250, 250), Image.Resampling.LANCZOS)
            logo_tk = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(main_frame, image=logo_tk, bg=COLOR_BG)
            logo_label.image = logo_tk  # Mantener referencia
            logo_label.pack(pady=(0, 20))
    except Exception:
        pass  # Si no hay logo, continuar sin él
    
    # Título
    tk.Label(
        main_frame,
        text="HADES",
        font=("Segoe UI", 32, "bold"),
        fg=ACCENT,
        bg=COLOR_BG
    ).pack()
    
    tk.Label(
        main_frame,
        text="El Guardián de tu Información",
        font=("Segoe UI", 13),
        fg=COLOR_MUTED,
        bg=COLOR_BG
    ).pack(pady=(5, 20))  # Reducido de 40 a 20 para que quepa el botón
    
    # Mensaje de estado (inicialmente vacío)
    status_label = tk.Label(
        main_frame,
        text="",
        font=("Segoe UI", 10),
        fg=COLOR_TEXT,
        bg=COLOR_BG
    )
    status_label.pack(pady=10)
    
    # Botón de autenticación
    def iniciar_autenticacion():
        # Deshabilitar botón
        btn_auth.config(state="disabled", bg=COLOR_PANEL)
        status_label.config(text="Espere un momento...", fg=COLOR_MUTED)
        welcome.update()
        
        # Pequeña pausa para que se vea el mensaje
        welcome.after(500, lambda: _ejecutar_autenticacion_manual(welcome, status_label))
    
    btn_auth = tk.Button(
        main_frame,
        text="🔐 Iniciar Sesión con Keycloak",
        command=iniciar_autenticacion,
        bg=COLOR_PURPLE,
        fg="white",
        font=("Segoe UI", 12, "bold"),
        relief="flat",
        padx=30,
        pady=15,
        cursor="hand2"
    )
    btn_auth.pack(pady=20)
    
    # Hover effect
    def on_enter(e):
        if btn_auth['state'] != 'disabled':
            btn_auth.config(bg=ACCENT)
    
    def on_leave(e):
        if btn_auth['state'] != 'disabled':
            btn_auth.config(bg=COLOR_PURPLE)
    
    btn_auth.bind("<Enter>", on_enter)
    btn_auth.bind("<Leave>", on_leave)
    
    # Versión
    tk.Label(
        main_frame,
        text="Versión 2.2",
        font=("Segoe UI", 9),
        fg=COLOR_MUTED,
        bg=COLOR_BG
    ).pack(side="bottom", pady=(20, 0))
    
    # Forzar actualización para que se muestren todos los widgets
    welcome.update_idletasks()
    welcome.update()
    
    # Esperar a que se cierre la ventana
    welcome.wait_window()

def _ejecutar_autenticacion_manual(welcome, status_label):
    """Ejecuta la autenticación de Keycloak desde la pantalla de bienvenida"""
    if not _KEYCLOAK_OK:
        welcome.destroy()
        messagebox.showerror(
            "Keycloak no disponible",
            "El sistema de autenticación SSO no está configurado.\n"
            "Contacta al administrador del sistema."
        )
        root.destroy()
        return
    
    # Actualizar mensaje
    status_label.config(text="Redirigiendo a Keycloak...", fg=ACCENT)
    welcome.update()
    
    # Intentar autenticación con Keycloak
    ok, msg = autenticar_con_keycloak()
    
    if ok:
        # Autenticación exitosa
        status_label.config(text=f"✅ Bienvenido, {usuario_actual['nombre']}", fg=COLOR_GREEN)
        welcome.update()
        welcome.after(1500, welcome.destroy)  # Cerrar después de 1.5 segundos
    else:
        # Autenticación fallida
        welcome.destroy()
        messagebox.showerror(
            "Error de Autenticación",
            f"No se pudo iniciar sesión:\n{msg}"
        )
        root.destroy()


# ========= VERIFICACIÓN DE INICIO CON KEYCLOAK =========
def _verificar_inicio():
    """Verifica usuario con Keycloak SSO"""
    # Esta función ahora solo verifica si ya hay sesión
    # La autenticación real se hace en mostrar_pantalla_bienvenida()
    return verificar_autenticacion_keycloak()


# ========= INICIO (Optimizado con verificación diferida) =========
def _init_app():
    """Inicializa la app después de verificar usuario"""
    # Mostrar pantalla de bienvenida con botón de autenticación
    mostrar_pantalla_bienvenida()
    
    # Verificar si la autenticación fue exitosa
    if _verificar_inicio():
        # Mostrar ventana principal solo después de autenticación exitosa
        root.deiconify()
        root.bind_all("<Control-v>", lambda e: pegar_imagen_clipboard())
        _set_mode_ocr()
    else:
        root.destroy()

# Mostrar UI primero, luego verificar (arranque más rápido)
root.after(100, _init_app)  # Verificar después de 100ms
root.mainloop()
