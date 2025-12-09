# hades_1.6_integrado_full_v4_patched_limpio_final_corregido_v3.py
# ------------------------------------------------------------------
# HADES 1.6 — Integrado (FULL v4, Drive patched, Normalización Estricta Final o ya no se que version va jajajaja :) ups)
# • VERIFICACIÓN: Corregida normalización de fechas DD MM YYYY (Pasaporte MX).
# • OCR con Gemini Visión (REST): Analizar actual / Analizar carrusel.
# • EXPORTACIÓN: Salida de OCR forzada a usar fechas normalizadas en la UI.
# ------------------------------------------------------------------

import os, sys, re, io, base64, time, datetime, json, requests, tempfile, unicodedata
try:
    import google.generativeai as genai
except Exception:
    genai = None
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import webbrowser  # Para abrir hipervínculos
# pandas se importará con lazy loading en las funciones que lo usan

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
_MONTHS_ES = {"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,"julio":7,"agosto":8,"septiembre":9,"setiembre":9,"octubre":10,"noviembre":11,"diciembre":12}
_MONTHS_EN = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,"july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
             "jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"aug":8,"sep":9,"sept":9,"oct":10,"nov":11,"dec":12,
             "ene":1, "feb":2, "mar":3, "abr":4, "may":5, "jun":6, "jul":7, "ago":8, "sep":9, "oct":10, "nov":11, "dic":12} # Añadido para 3 letras Español/Inglés
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
_DATE_RE_DMY_H = re.compile(r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b')

# --- Patrones extra: "MES-DD-YYYY" y "DD-MES-YYYY"
_DATE_RE_EN_MON_DD_YYYY_H = re.compile(r'\b([A-Za-z]{3,})[-/](\d{1,2})[-/](\d{2,4})\b', re.IGNORECASE)
_DATE_RE_EN_DD_MON_YYYY_H = re.compile(r'\b(\d{1,2})[-/]([A-Za-z]{3,})[-/](\d{2,4})\b', re.IGNORECASE)

# Patrón para DD MM YYYY (separado por espacios, como el Pasaporte MX)
_DATE_RE_DD_MM_YYYY_SPACE = re.compile(r'\b(\d{1,2})\s+(\d{1,2})\s+(\d{4})\b')

# Patrón para Pasaportes (DD MON / MON YY) - e.g., 30 NOV / NOV 86
_DATE_RE_TXT_PASSPORT = re.compile(r'\b(\d{1,2})\s+([A-Za-z]{3,})\s+/\s+[A-Za-z]{3,}\s+(\d{2,4})\b', re.IGNORECASE)

# 🆕 Patrón para DDMONYYYY (Guatemala DPI)
_DATE_RE_DMMMYYYY = re.compile(r'\b(\d{1,2})([A-Za-z]{3,})(\d{4})\b', re.IGNORECASE)

# Patrón para rangos de año 2022 - 2032 (para INE)
_DATE_RE_YEAR_RANGE = re.compile(r'(\d{4})\s*[-\u2013]\s*(\d{4})')


def _clean_ocr_output(texto: str) -> str:
    """Elimina líneas generadas internamente por HADES que se colaron en el output de Gemini."""
    if not texto:
        return ""
    # Regex para buscar la línea de metadatos internos, incluyendo el patrón: [DOCUMENTO] país: XX — formato detectado: XXXXXX
    cleaned = re.sub(r'\[DOCUMENTO\]\s*país:\s*[A-Z]{2}\s*—\s*formato\s*detectado:\s*.*', '', texto, flags=re.IGNORECASE).strip()
    return cleaned

def _infer_doc_country(texto: str):
    t = (texto or "").lower()
    for cc, cues in _COUNTRY_CUES.items():
        if any(c in t for c in cues):
            return cc
    return None

def _detect_language_bias(texto: str):
    t = (texto or "").lower()
    score_es = sum(1 for m in _MONTHS_ES if m in t)
    score_en = sum(1 for m in _MONTHS_EN if m in t)
    return "ES" if score_es >= score_en and score_es>0 else ("EN" if score_en>0 else None)

def _coerce_year(y: int) -> int:
    if y < 100: return 2000 + y if y < 50 else 1900 + y
    return y


def _normalize_date_to_mdy_ctx(s: str, country_ctx: str|None, lang_ctx: str|None):
    """
    Convierte cualquier formato de fecha reconocido al estándar MM/DD/YYYY.
    Integra todas las reglas de formato.
    """
    if not s:
        return None
    st = s.strip()

    # REGLA: Rango de años (e.g., 2022 - 2032) -> Tomar el año final y pasarlo como solo año para el siguiente filtro
    m_range = _DATE_RE_YEAR_RANGE.search(st)
    if m_range:
        st = m_range.group(2)

    # REGLA: Si sólo incluye año, devuélveme mes 12, día 31 y año correspondiente (YYYY -> 12/31/YYYY)
    if re.fullmatch(r'\b\d{4}\b', st): return f"12/31/{st}"

    # 1. Fecha textual en español (DD de MES de YYYY)
    m = _DATE_RE_TXT_ES.search(st)
    if m:
        da, mon, y = m.groups()
        mo = _MONTHS_ES.get(mon.lower())
        if mo: return f"{int(mo):02d}/{int(da):02d}/{_coerce_year(int(y)):04d}"

    # 2. DDMONYYYY (ej. 24JUN2019)
    m = re.search(r'(\d{1,2})([A-Za-z]{3})(\d{4})', st, re.IGNORECASE)
    if m:
        da, mon, y = m.groups()
        mo_int = _MONTHS_EN.get(mon.lower()[:3])
        if mo_int:
            return f"{mo_int:02d}/{int(da):02d}/{_coerce_year(int(y)):04d}"

    # 3. Pasaporte (DD MES / MES YY)
    m = _DATE_RE_TXT_PASSPORT.search(st)
    if m:
        da, mon, y = m.groups()
        mo = _MONTHS_EN.get(mon.lower())
        if mo: return f"{int(mo):02d}/{int(da):02d}/{_coerce_year(int(y)):04d}"

    # 4. DD MM YYYY (espacios, como en Pasaporte MX)
    m = _DATE_RE_DD_MM_YYYY_SPACE.search(st)
    if m:
        d, m_, y = m.groups()
        try:
            d_int, m_int, y_int = int(d), int(m_), int(y)
            return f"{m_int:02d}/{d_int:02d}/{y_int:04d}"
        except ValueError:
            pass

    # 5. Otros formatos textuales (CORREGIDO)
    for rx in [_DATE_RE_EN_MON_DD_YYYY_H, _DATE_RE_EN_DD_MON_YYYY_H,
               _DATE_RE_TXT_EN_MDY, _DATE_RE_TXT_EN_DMY]:
        m = rx.search(st)
        if m:
            parts = m.groups()
            if len(parts) == 3:
                # REVISIÓN: Identifica el formato por el regex que hizo match
                if rx in (_DATE_RE_TXT_EN_MDY, _DATE_RE_EN_MON_DD_YYYY_H):
                    # Formato: (Mes, Día, Año)
                    mon, da, y = parts[0], parts[1], parts[2]
                else: 
                    # Formato: (Día, Mes, Año)
                    da, mon, y = parts[0], parts[1], parts[2]
    
                mo = _MONTHS_EN.get(mon.lower())
                if mo: return f"{int(mo):02d}/{int(da):02d}/{_coerce_year(int(y)):04d}"

    # 6. ISO y DMY con guiones
    for rx in [_DATE_RE_ISO, _DATE_RE_DMY_H]:
        m = rx.search(st)
        if m:
            parts = list(map(int, m.groups()))
            if rx == _DATE_RE_ISO:
                y, mo, da = parts
            else:
                da, mo, y = parts
            return f"{mo:02d}/{da:02d}/{y:04d}"

    # 7. Ambiguo numérico (d/m/y o m/d/y)
    m = _DATE_RE_NUM_A.search(st)
    if m:
        a, b, y = m.groups()
        a = int(a); b = int(b); y = _coerce_year(int(y))
        prefer_dmy = (country_ctx not in {"US"} or lang_ctx == "ES")
        day, month = None, None
        if a > 12 and b <= 12: day, month = a, b
        elif b > 12 and a <= 12: month, day = a, b
        elif prefer_dmy: day, month = a, b
        else: month, day = a, b
        if day is not None and month is not None:
            return f"{int(month):02d}/{int(day):02d}/{y:04d}"

    return None

def _extract_all_dates(text: str):
    if not text: return []
    hits = []
    # Incluimos un patrón para DDMMMYYYY (como 24JUN2019)
    custom_ddmmyyyy = re.compile(r'\b(\d{1,2})([A-Z]{3})(\d{4})\b', re.IGNORECASE) 

    for rx in (_DATE_RE_TXT_ES, _DATE_RE_TXT_EN, _DATE_RE_TXT_EN_DMY, _DATE_RE_TXT_EN_MDY, _DATE_RE_EN_MON_DD_YYYY_H, _DATE_RE_EN_DD_MON_YYYY_H, _DATE_RE_ISO, _DATE_RE_DMY_H, _DATE_RE_NUM_A, _DATE_RE_DD_MM_YYYY_SPACE, _DATE_RE_TXT_PASSPORT, _DATE_RE_YEAR_RANGE, _DATE_RE_DMMMYYYY, custom_ddmmyyyy):
        for m in rx.finditer(text):
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
    Procesa el texto OCR aplicando las reglas estrictas de normalización de fechas.
    Clasifica las fechas encontradas y aplica la regla de no modificación para USA.
    """
    import datetime as _dt
    doc_pais = _infer_doc_country(texto)
    is_usa_id = (doc_pais == "US")
    lang = _detect_language_bias(texto)

    results: Dict[str, Optional[str]] = {
        "fecha_vigencia_final": None,
        "fecha_expedicion_final": None,
        "fecha_nacimiento_final": None,
        "otras_fechas_normalizadas": "",
        "vigencia_sugerida": None,
        "exp_date_mdy_for_sug": None,
        "nombre": None,
        "tipo_identificacion": None
    }

    vigencia_keywords = ["vencimiento", "vence", "expiración", "expiracion", "vigencia", "valido hasta", "valid thru", "caducidad", "fecha de caducidad", "válido hasta"]
    expedicion_keywords = ["emision", "expedicion", "expedición", "issue", "issued", "fecha de emision", "date of issue", "fecha de expedicion", "emitido", "fecha de emi"]
    nacimiento_keywords = ["fecha de nacimiento", "dob", "date of birth", "nacimient[oa]"]

    all_dates_raw = _extract_all_dates(texto)
    seen_originals = set()
    kv_map: Dict[str, str] = {}

    def process_and_assign_date(original: str, date_type: str):
        nonlocal results
        
        # 1. Verificamos si la fecha original YA está en formato MM/DD/YYYY
        is_already_mdy = False
        if original: # Asegurarse de que 'original' no sea None
            # re.fullmatch comprueba si TODA la cadena coincide con el patrón
            # Patrón: (1-2 dígitos)[/-](1-2 dígitos)[/-](4 dígitos)
            if re.fullmatch(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', original.strip()):
                is_already_mdy = True

        # 2. Aplicamos la nueva regla
        if is_usa_id and is_already_mdy:
            # Es USA y YA está en formato correcto: No la tocamos.
            final_date = original
            norm_mdy_for_sug = original
        else:
            # No es USA, O es USA pero está en un formato incorrecto (ej. "20 Nov 2017"):
            # Intentamos normalizarla.
            final_date = _normalize_date_to_mdy_ctx(original, doc_pais, lang)
            norm_mdy_for_sug = final_date

        # 3. Fallback: Si la normalización falla (devuelve None), usamos el original
        if not final_date:
            final_date = original

        results[f"fecha_{date_type}_final"] = final_date
        
        if date_type == "expedicion" and norm_mdy_for_sug:
            results["exp_date_mdy_for_sug"] = norm_mdy_for_sug
        seen_originals.add(original)
        return final_date

    for line in texto.splitlines():
        ll = line.lower().strip()
        kv_match = re.search(r'([a-záéíóúñ\s]+):\s*(.*)', ll, re.IGNORECASE)
        if kv_match:
            key = kv_match.group(1).strip()
            value = kv_match.group(2).strip()

            # Corrección: nombre principal vs. nombre del padre
            if "nombre" in key and "padre" not in key and not results.get("nombre"):
                results["nombre"] = value

            # Corrección: tipo de identificación
            if "tipo" in key and ("documento" in key or "tarjeta" in key) and not results.get("tipo_identificacion"):
                results["tipo_identificacion"] = value

            all_regexes = (_DATE_RE_NUM_A, _DATE_RE_ISO, _DATE_RE_DMY_H,
                           _DATE_RE_EN_MON_DD_YYYY_H, _DATE_RE_EN_DD_MON_YYYY_H,
                           _DATE_RE_TXT_EN_MDY, _DATE_RE_TXT_EN_DMY, _DATE_RE_TXT_ES,
                           _DATE_RE_DD_MM_YYYY_SPACE, _DATE_RE_TXT_PASSPORT, _DATE_RE_YEAR_RANGE, _DATE_RE_DMMMYYYY)

            original_date_match = None
            for rx in all_regexes:
                dm = rx.search(value)
                if dm:
                    original_date_match = dm.group(0)
                    break

            if original_date_match:
                original = original_date_match
                is_vig = any(k in key for k in vigencia_keywords) and not results["fecha_vigencia_final"]
                is_exp = any(k in key for k in expedicion_keywords) and not results["fecha_expedicion_final"]
                is_nac = any(k in key for k in nacimiento_keywords) and not results["fecha_nacimiento_final"]

                date_type = None
                if is_vig: date_type = "vigencia"
                elif is_exp: date_type = "expedicion"
                elif is_nac: date_type = "nacimiento"

                if date_type:
                    final_date = process_and_assign_date(original, date_type)
                    kv_map[key] = final_date
                else:
                    if not is_usa_id:
                        final_date = _normalize_date_to_mdy_ctx(original, doc_pais, lang)
                        if final_date:
                            kv_map[key] = final_date
                    else:
                        # (CORRECCIÓN): Aplicar lógica de USA aquí también
                        is_already_mdy_other = re.fullmatch(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', original.strip())
                        if is_already_mdy_other:
                            kv_map[key] = original
                        else:
                             final_date = _normalize_date_to_mdy_ctx(original, doc_pais, lang)
                             kv_map[key] = final_date or original


    if not results["fecha_vigencia_final"]:
        vigencia_raw = None
        for line in texto.splitlines():
            if any(k in line.lower() for k in vigencia_keywords):
                range_match = re.search(r'(\d{4})\s*[-\u2013]\s*(\d{4})', line)
                year_match = re.search(r'\b\d{4}\b', line)
                if range_match:
                    vigencia_raw = range_match.group(0)
                elif year_match:
                    vigencia_raw = year_match.group(0)
                if vigencia_raw:
                    y_str_match = re.search(r'\d{4}$', vigencia_raw.strip())
                    y_str = y_str_match.group(0) if y_str_match else None
                    if y_str:
                        sugerida_str_base = _normalize_date_to_mdy_ctx(y_str, doc_pais, lang)
                        if sugerida_str_base:
                            sugerida_str = f"{sugerida_str_base} (Sugerida)"
                            results["vigencia_sugerida"] = sugerida_str
                            results["fecha_vigencia_final"] = sugerida_str
                            break
        if not results["fecha_vigencia_final"]:
            try:
                sugerida_dt = _dt.date.today()
                sugerida_dt = _add_years_safe(sugerida_dt, 5)
                sugerida_str = f"{sugerida_dt.strftime('%m/%d/%Y')} (Sugerida)"
                results["vigencia_sugerida"] = sugerida_str
                results["fecha_vigencia_final"] = sugerida_str
            except ValueError:
                pass

    del results["exp_date_mdy_for_sug"]
    results["kv_map"] = kv_map
    return results

_NAME_HINTS = [
    # Captura el valor después de NOMBRE/NAME/TITULAR/NOMBRES/APELLIDOS
    r"(?:nombre|names|nombres)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s'.-]+?)(?:\s+(APELLIDOS|SURNAME|DIRECCION|CALLE))?$",
    r"(?:apellidos|surname)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s'.-]+?)(?:\s+(NOMBRES|NAMES|FECHA))?$",
    r"(?:nombre|name|titular)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s'.-]+)", # Fallback más simple
]
_DOB_HINTS = [
    r"(?:fecha\s*de\s*nacimiento|f\.\s*de\s*nac\.?|dob|date\s*of\s*birth|nacimient[oa])"
]
_CURP_RE = re.compile(r'\b([A-Z][AEIOUX][A-Z]{2})(\d{2})(\d{2})(\d{2})[HM][A-Z]{5}[0-9A-Z]\d\b', re.IGNORECASE)
_RFC_PER_RE = re.compile(r'\b([A-ZÑ&]{4})(\d{2})(\d{2})(\d{2})[A-Z0-9]{3}\b', re.IGNORECASE)
_SAMPLE_WORDS = ("muestra","sample","specimen","ejemplo","void")

# --- Funciones de extracción de ID ---
def _extract_id_number(texto: str, doc_pais: str | None) -> str | None:
    if not texto: return None
    
    # Normalizamos el texto (espacios internos y saltos de línea para búsqueda de claves)
    t_searchable = texto.upper().replace('\n', ' ')
    t_clean = t_searchable.replace(' ', '').replace('-', '')
    
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
            for rx in (_DATE_RE_NUM_A,_DATE_RE_ISO,_DATE_RE_DMY_H,_DATE_RE_TXT_ES,
                       _DATE_RE_TXT_EN,_DATE_RE_TXT_EN_DMY,_DATE_RE_TXT_EN_MDY,
                       _DATE_RE_EN_MON_DD_YYYY_H,_DATE_RE_EN_DD_MON_YYYY_H, _DATE_RE_TXT_PASSPORT, _DATE_RE_DMMMYYYY):
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
    Analiza la imagen con Gemini Vision para detectar signos de manipulación o falsificación.
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
        
        # Prompt especializado para análisis forense
        prompt = (
            "Analiza esta imagen de identificación oficial y detecta posibles signos de FALSIFICACIÓN o MANIPULACIÓN DIGITAL. "
            "Evalúa específicamente:\n"
            "1. CALIDAD DE IMPRESIÓN: ¿La calidad es consistente o hay áreas borrosas/pixeladas sospechosas?\n"
            "2. FUENTES TIPOGRÁFICAS: ¿Las fuentes son consistentes y profesionales o hay inconsistencias?\n"
            "3. ELEMENTOS DE SEGURIDAD: ¿Se observan hologramas, marcas de agua, microimpresiones u otros elementos de seguridad?\n"
            "4. MANIPULACIÓN DIGITAL: ¿Hay evidencia de edición (bordes irregulares, sombras inconsistentes, clonación)?\n"
            "5. AUTENTICIDAD GENERAL: ¿La identificación parece auténtica o hay señales de alerta?\n\n"
            "Responde SOLO con un análisis breve y directo de cada punto. "
            "Si detectas problemas, menciónalos claramente. Si todo parece correcto, indícalo."
        )
        temp = 0.2  # Baja temperatura para respuestas más deterministas
        
        # Intentar con SDK primero
        visual_analysis = ""
        if genai is not None:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel(GEMINI_MODEL)
                resp = model.generate_content(
                    [{"mime_type": mime, "data": bio.getvalue()}, {"text": prompt}],
                    generation_config={"temperature": temp, "top_p": 0.95, "max_output_tokens": 1024}
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
                    "generationConfig": {"temperature": temp, "topP": 0.95, "maxOutputTokens": 1024}
                }
                headers = {"Content-Type": "application/json"}
                r = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=payload, timeout=60)
                data = r.json()
                visual_analysis = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "") or ""
            except Exception:
                return 0, ["Error al conectar con Gemini Vision para análisis visual."]
        
        # Analizar la respuesta para detectar señales de alerta
        analysis_lower = visual_analysis.lower()
        score_visual = 0
        detalles = []
        
        # Palabras clave que indican problemas
        red_flags = {
            "manipulación": 25,
            "editado": 25,
            "photoshop": 30,
            "inconsistente": 20,
            "sospechoso": 20,
            "irregular": 15,
            "borroso": 10,
            "pixelado": 10,
            "clonación": 30,
            "falso": 35,
            "falsificación": 35,
            "no auténtico": 30,
            "alterado": 25,
        }
        
        for keyword, penalty in red_flags.items():
            if keyword in analysis_lower:
                score_visual += penalty
                detalles.append(f"Análisis visual detectó: '{keyword}'")
        
        # Señales positivas (reducen score)
        if any(word in analysis_lower for word in ["auténtico", "legítimo", "genuino", "correcto", "profesional"]):
            if score_visual == 0:
                detalles.append("Análisis visual: documento parece auténtico.")
        
        # Guardar análisis completo como detalle
        if visual_analysis.strip():
            detalles.append(f"Análisis completo: {visual_analysis[:200]}...")  # Primeros 200 chars
        
        return min(score_visual, 50), detalles  # Cap máximo de 50 puntos por análisis visual
        
    except Exception as e:
        return 0, [f"Error en análisis visual: {str(e)[:100]}"]


def _authenticity_score(texto: str, image_path: str|None):
    """
    Calcula el score de autenticidad combinando análisis de texto y visual.
    Retorna (riesgo, details, emoji_semaforo, color_semaforo)
    
    Niveles de riesgo:
    - 🟢 BAJO (0-20): Verde - Documento parece auténtico
    - 🟡 MEDIO (21-50): Amarillo - Requiere revisión adicional
    - 🔴 ALTO (51+): Rojo - Alta probabilidad de falsificación
    """
    details = []
    score = 0
    low = (texto or "").lower()

    # Usamos la lógica del nuevo procesador para obtener la fecha normalizada
    date_results = _process_all_dates_by_type(texto)
    dob_use = date_results.get("fecha_nacimiento_final")
    
    # 1. Chequeo de Muestra
    if any(w in low for w in _SAMPLE_WORDS if w):
        score += 50; details.append("⚠️ Contiene 'sample/muestra/void'.")

    # 2. Chequeo de Nombre
    nombre = _extract_name(texto)
    if not nombre:
        score += 10; details.append("⚠️ No se detectó nombre.")

    # 3. Chequeo de Fecha de Nacimiento e Inconsistencias
    if dob_use and "Sugerida" not in dob_use:
        age = _age_from_mdy(dob_use)
        if age is not None and (age < 15 or age > 120):
            score += 30; details.append(f"⚠️ Edad implausible ({age} años).")
        
        curp_m = _CURP_RE.search(texto or "")
        if curp_m and _infer_doc_country(texto) == "MX":
            curp = curp_m.group(0)
            curp_dob = _parse_dob_from_curp(curp)
            if curp_dob and curp_dob != dob_use:
                score += 40; details.append("⚠️ CURP no coincide con la fecha de nacimiento.")
        
        rfc_m = _RFC_PER_RE.search(texto or "")
        if rfc_m and _infer_doc_country(texto) == "MX":
            yy,mm,dd = map(int, rfc_m.groups()[1:4])
            y = 2000 + yy if yy < 50 else 1900 + yy
            rfc_dob = f"{mm:02d}/{dd:02d}/{y:04d}"
            if rfc_dob != dob_use:
                score += 20; details.append("⚠️ RFC no coincide con la fecha de nacimiento.")
    else:
        score += 10; details.append("⚠️ No se identificó fecha de nacimiento.")

    # 4. Chequeo de Vigencia
    vig_final = date_results.get("fecha_vigencia_final")
    if not vig_final or "Sugerida" in vig_final:
        score += 10; details.append("⚠️ No se detectó vigencia (usamos sugerida).")
    
    # 5. 🆕 ANÁLISIS VISUAL CON GEMINI (si hay imagen disponible)
    if image_path and os.path.exists(image_path):
        visual_score, visual_details = gemini_vision_auth_check(image_path)
        score += visual_score
        details.extend(visual_details)
    
    # Determinar nivel de riesgo con nuevo sistema de semáforo
    if score <= 20:
        riesgo = "bajo"
        emoji = "🟢"
        color = "green"
    elif score <= 50:
        riesgo = "medio"
        emoji = "🟡"
        color = "yellow"
    else:
        riesgo = "alto"
        emoji = "🔴"
        color = "red"
    
    return riesgo, details, emoji, color


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
GEMINI_MODEL = "gemini-1.5-flash"  # Modelo por defecto

# ===== CONFIGURACIÓN DE IA (Gemini + Claude Backup) =====
CLAUDE_API_KEY = None
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"  # Modelo por defecto
AI_PROVIDER = "gemini"  # "gemini" o "claude"
ENABLE_FALLBACK = True  # Fallback automático si el proveedor principal falla


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
    ## PULIDO: Se modifica el prompt para exigir formato de clave-valor.
    """
    if not GEMINI_API_KEY:
        return "⚠️ Configura GEMINI_API_KEY para usar Visión."
    try:
        from PIL import Image, ImageOps
        # --- Pre-proceso de imagen ---
        im = Image.open(image_path)
        im = ImageOps.exif_transpose(im) # auto-rotación por EXIF
        bio = io.BytesIO()
        im.save(bio, format="PNG") # normalizamos a PNG
        bio.seek(0)
        mime = "image/png"

        # --- Prompt estilo 'clave-valor' ---
        ## PULIDO: NUEVO PROMPT CLAVE-VALOR
        prompt = ("Eres un experto en OCR. Extrae TODO el texto visible de esta imagen de documento oficial. "
                  "Organiza la información como pares CLAVE: VALOR. "
                  "Ejemplo: Nombre: RAMIREZ MARTINEZ MIRIAN, Fecha de Nacimiento: 05/06/1993, Número: 123456789. "
                  "IMPORTANTE: Incluye TODOS los números, series, claves, fechas y texto que veas. "
                  "Mantén la puntuación original. "
                  "Responde SOLO el texto extraído en formato clave-valor en español. "
                  "NO agregues comentarios, introducciones ni explicaciones.")
        temp = 0.3

        # --- SDK preferente ---
        if genai is not None:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel(GEMINI_MODEL)
                resp = model.generate_content(
                    [{"mime_type": mime, "data": bio.getvalue()}, {"text": prompt}],
                    generation_config={"temperature": temp, "top_p": 0.95, "max_output_tokens": 8192}
                )
                txt = getattr(resp, "text", "") or ""
                return _clean_ocr_output(txt.strip() if txt.strip() else "(sin texto)")
            except Exception:
                pass # Si el SDK falla, seguimos con REST

        # --- Fallback REST (mismo prompt/config) ---
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
                "generationConfig": {"temperature": temp, "topP": 0.95, "maxOutputTokens": 8192}
            }
            headers = {"Content-Type": "application/json"}
            r = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=payload, timeout=90)
            data = r.json()
            txt = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "") or ""
            return _clean_ocr_output(txt.strip() if txt.strip() else "(sin texto)")
        except Exception as e2:
            return f"❌ Error en Visión (fallback): {e2}"
    except Exception as e:
        return f"❌ Error en Visión: {e}"


def claude_vision_extract_text(image_path: str) -> str:
    """
    Extrae texto con Claude 3.5 Sonnet Vision (backup de Gemini)
    """
    if not CLAUDE_API_KEY:
        return "⚠️ Configura CLAUDE_API_KEY para usar Claude."
    
    try:
        from PIL import Image, ImageOps
        import io, base64
        
        # Preparar imagen
        im = Image.open(image_path)
        im = ImageOps.exif_transpose(im)
        bio = io.BytesIO()
        im.save(bio, format="PNG")
        bio.seek(0)
        b64 = base64.b64encode(bio.getvalue()).decode("utf-8")
        
        # Prompt (mismo que Gemini para consistencia)
        prompt = (
            "Eres un experto en OCR. Extrae TODO el texto visible de esta imagen de documento oficial. "
            "Organiza la información como pares CLAVE: VALOR. "
            "Ejemplo: Nombre: RAMIREZ MARTINEZ MIRIAN, Fecha de Nacimiento: 05/06/1993, Número: 123456789. "
            "IMPORTANTE: Incluye TODOS los números, series, claves, fechas y texto que veas. "
            "Mantén la puntuación original. "
            "Responde SOLO el texto extraído en formato clave-valor en español. "
            "NO agregues comentarios, introducciones ni explicaciones."
        )
        
        # Llamada a Claude API
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": CLAUDE_MODEL,
            "max_tokens": 4096,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": b64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        }
        
        r = requests.post(url, headers=headers, json=payload, timeout=90)
        
        # Manejo de errores de cuota y autenticación
        if r.status_code == 429:
            return "❌ CUOTA AGOTADA: Claude ha alcanzado el límite de rate. Espera unos minutos o usa Gemini."
        elif r.status_code == 401:
            return "❌ API KEY INVÁLIDA: Verifica tu Claude API Key en https://console.anthropic.com/"
        elif r.status_code != 200:
            return f"❌ Claude API error: {r.status_code} - {r.text[:100]}"
        
        data = r.json()
        txt = data.get("content", [{}])[0].get("text", "") or ""
        return _clean_ocr_output(txt.strip() if txt.strip() else "(sin texto)")
        
    except Exception as e:
        return f"❌ Error en Claude Vision: {e}"


def vision_extract_text_with_fallback(image_path: str) -> tuple[str, str]:
    """
    Extrae texto con fallback automático entre proveedores.
    Retorna: (texto_extraido, proveedor_usado)
    """
    global AI_PROVIDER
    
    # Intentar con el proveedor seleccionado
    if AI_PROVIDER == "gemini":
        try:
            texto = gemini_vision_extract_text(image_path)
            # Si funciona correctamente, retornar
            if not texto.startswith("❌") and not texto.startswith("⚠️"):
                return texto, "Gemini"
            
            # Si hay error y fallback está habilitado, intentar con Claude
            if ENABLE_FALLBACK and CLAUDE_API_KEY:
                print("[HADES] Gemini falló, usando Claude como backup...")
                texto_claude = claude_vision_extract_text(image_path)
                if not texto_claude.startswith("❌") and not texto_claude.startswith("⚠️"):
                    return texto_claude, "Claude (Fallback)"
            
            return texto, "Gemini (con error)"
            
        except Exception as e:
            # Si hay excepción y fallback está habilitado
            if ENABLE_FALLBACK and CLAUDE_API_KEY:
                print(f"[HADES] Excepción en Gemini: {e}, usando Claude como backup...")
                try:
                    return claude_vision_extract_text(image_path), "Claude (Fallback)"
                except:
                    pass
            return f"❌ Error en Gemini: {e}", "Gemini (error)"
    
    elif AI_PROVIDER == "claude":
        try:
            texto = claude_vision_extract_text(image_path)
            # Si funciona correctamente, retornar
            if not texto.startswith("❌") and not texto.startswith("⚠️"):
                return texto, "Claude"
            
            # Si hay error y fallback está habilitado, intentar con Gemini
            if ENABLE_FALLBACK and GEMINI_API_KEY:
                print("[HADES] Claude falló, usando Gemini como backup...")
                texto_gemini = gemini_vision_extract_text(image_path)
                if not texto_gemini.startswith("❌") and not texto_gemini.startswith("⚠️"):
                    return texto_gemini, "Gemini (Fallback)"
            
            return texto, "Claude (con error)"
            
        except Exception as e:
            # Si hay excepción y fallback está habilitado
            if ENABLE_FALLBACK and GEMINI_API_KEY:
                print(f"[HADES] Excepción en Claude: {e}, usando Gemini como backup...")
                try:
                    return gemini_vision_extract_text(image_path), "Gemini (Fallback)"
                except:
                    pass
            return f"❌ Error en Claude: {e}", "Claude (error)"
    
    return "❌ No hay proveedor de IA configurado", "Ninguno"


# ====== Modales con tema (oscuro morado) ======
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
metricas=[] # [{archivo, api, tipo, duracion_s, usuario, feedback}]
FEEDBACK_RATING=None
API_USADA="gemini-vision"

def registrar_changelog(evento: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs("./logs", exist_ok=True)
    with open("./logs/changelog.txt", "a", encoding="utf-8") as log:
        log.write(f"[{ts}] {evento}\n")

def _guardar_resultado(nombre: str, texto: str, tipo: str, duracion_s: float,
                         datos_esenciales: dict = None, riesgo: str = "", detalles: list = None):
    """Guarda resultados y métricas de forma consolidada."""
    # Inicialización
    r = next((res for res in resultados if res['archivo'] == nombre), None)
    if not r:
        r = {'archivo': nombre, 'texto': texto, 'tipo': tipo, 'duracion_s': duracion_s}
        resultados.append(r)
    else:
        r.update({'texto': texto, 'tipo': tipo, 'duracion_s': duracion_s})

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
        
    except Exception as e:
        print(f"[HADES] Error al calcular metadata de resultado: {e}")

    # métricas (usuario = correo)
    m = next((met for met in metricas if met['archivo'] == nombre), None)
    if not m:
        m = {'archivo': nombre, 'api': API_USADA, 'tipo': tipo, 'duracion_s': duracion_s, 'usuario': usuario_actual.get('correo') or "", 'feedback': FEEDBACK_RATING or ""}
        metricas.append(m)
    else:
        m.update({'api': API_USADA, 'tipo': tipo, 'duracion_s': duracion_s, 'usuario': usuario_actual.get('correo') or "", 'feedback': FEEDBACK_RATING or ""})
        
    registrar_changelog(f"Resultado guardado: {nombre} ({len(texto)} chars, {duracion_s:.2f}s, riesgo={riesgo})")


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
    """Gestor unificado de API Keys para Gemini y Claude con hipervínculos"""
    global GEMINI_API_KEY, CLAUDE_API_KEY
    
    if not usuario_actual["correo"]:
        messagebox.showinfo("API Keys", "Primero verifica tu correo (se hace al iniciar).")
        return
    
    # Crear ventana
    win = tk.Toplevel(root)
    win.title("Configurar API Keys")
    win.configure(bg=COLOR_CARD)
    win.transient(root)
    win.grab_set()
    win.geometry("500x350")
    
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
    
    # ===== CLAUDE API KEY =====
    tk.Label(main_frame, text="Claude API Key (Anthropic):", bg=COLOR_CARD, fg=COLOR_TEXT,
             font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", pady=(0, 5))
    
    claude_entry = tk.Entry(main_frame, bg="#1f1440", fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
                           highlightbackground=ACCENT_2, relief="flat", width=45, show="*")
    claude_entry.grid(row=4, column=0, sticky="ew", pady=(0, 5))
    if CLAUDE_API_KEY:
        claude_entry.insert(0, CLAUDE_API_KEY)
    
    # Hipervínculo Claude
    link_claude = tk.Label(main_frame, text="🔗 Obtener Claude API Key", bg=COLOR_CARD,
                          fg=COLOR_BLUE, cursor="hand2", font=("Segoe UI", 9, "underline"))
    link_claude.grid(row=5, column=0, sticky="w", pady=(0, 20))
    link_claude.bind("<Button-1>", lambda e: webbrowser.open("https://console.anthropic.com/"))
    
    main_frame.grid_columnconfigure(0, weight=1)
    
    # Botones
    btn_frame = tk.Frame(win, bg=COLOR_CARD)
    btn_frame.pack(pady=(0, 16))
    
    def guardar():
        global GEMINI_API_KEY, CLAUDE_API_KEY
        gemini_key = gemini_entry.get().strip()
        claude_key = claude_entry.get().strip()
        
        if gemini_key:
            GEMINI_API_KEY = gemini_key
        if claude_key:
            CLAUDE_API_KEY = claude_key
        
        keys_configuradas = []
        if GEMINI_API_KEY:
            keys_configuradas.append("Gemini")
        if CLAUDE_API_KEY:
            keys_configuradas.append("Claude")
        
        if keys_configuradas:
            status.config(text=f"✅ API Keys: {', '.join(keys_configuradas)}")
        else:
            status.config(text="⚠️ No se configuraron API Keys")
        
        win.destroy()
    
    tk.Button(btn_frame, text="💾 Guardar", command=guardar, bg=COLOR_PURPLE, fg="white",
             relief="flat", padx=20, pady=10, width=12).pack(side="left", padx=5)
    tk.Button(btn_frame, text="❌ Cancelar", command=win.destroy, bg=COLOR_BTN, fg="white",
             relief="flat", padx=20, pady=10, width=12).pack(side="left", padx=5)
    
    # Centrar ventana
    root.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width()//2 - 250)
    y = root.winfo_rooty() + (root.winfo_height()//2 - 175)
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
btn_modelo = tk.Button(bar, text="🤖 Seleccionar Modelo", bg=COLOR_BLUE, fg="white", relief="flat", padx=10, pady=8,
                      command=seleccionar_modelo); btn_modelo.pack(side="left", padx=(0,8), pady=8)
btn_proveedor = tk.Button(bar, text="🔷 Proveedor IA", bg=COLOR_BLUE, fg="white", relief="flat", padx=10, pady=8,
                         command=seleccionar_proveedor); btn_proveedor.pack(side="left", padx=(0,8), pady=8)
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
btn_analizar = tk.Button(footer, text="🔍 Analizar actual", bg=COLOR_PURPLE, fg=COLOR_TEXT, relief="flat", padx=12, pady=10,
                         command=lambda: analizar_actual()); btn_analizar.pack(side="left", padx=8, pady=10)
btn_carrusel = tk.Button(footer, text="🎯 Analizar carrusel", bg=COLOR_PURPLE, fg="white", relief="flat", padx=12, pady=10,
                         command=lambda: analizar_carrusel()); btn_carrusel.pack(side="left", padx=8, pady=10)
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
    - Sustituye fechas clave por sus versiones normalizadas/finales.
    - Resalta en color los campos considerados ESENCIALES directamente en el panel.
    """
    
    # --- INICIO DE CAMBIOS: Helper de limpieza ---
    
    def _clean_key_for_matching(key_text: str) -> str:
        """
        Limpia una clave para la comparación:
        1. Minúsculas
        2. Sin acentos
        3. Sin puntuación (.,:;_-)
        4. Espacios normalizados
        """
        if not key_text:
            return ""
        # 1. Minúsculas
        s = key_text.lower()
        # 2. Sin acentos (requiere 'import unicodedata' al inicio de tu script)
        try:
            s = ''.join(c for c in unicodedata.normalize('NFD', s)
                        if unicodedata.category(c) != 'Mn')
        except Exception:
            pass # Fallback si unicodedata falla o no está importado
        # 3. Sin puntuación (reemplaza con espacio)
        s = re.sub(r'[.,:;_\-]+', ' ', s)
        # 4. Espacios normalizados
        s = re.sub(r'\s+', ' ', s).strip()
        return s
    
    # --- FIN DE CAMBIOS ---


    # Mapeo de claves que necesitan reemplazo de valor normalizado
    key_mapping: Dict[str, Optional[str]] = {}
    
    # (Punto 2 - Arreglo "Lugar de nacimiento")
    for key_prefix in ["fecha de nacimiento", "dob", "date of birth", r"^nacimient[oa]$"]:
        key_mapping[key_prefix] = results.get("fecha_nacimiento_final")
    for key_prefix in ["emision", "expedicion", "expedición", "issue", "issued", "...a de emision", "fecha de expedicion", "emitido", "fecha de emi"]:
        key_mapping[key_prefix] = results.get("fecha_expedicion_final")
    for key_prefix in ["vencimiento", "vence", "expiración", "expiracion", "vigencia", "valido hasta", "valid thru", "caducidad", "fecha de caducidad", "válido hasta"]:
        key_mapping[key_prefix] = results.get("fecha_vigencia_final")

    # (Punto 4 - Keywords)

    essential_keywords_clean = {
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
        "vigencia", "vence", "valido hasta", "valid thru", "fecha de vencimiento",
    }
 
    # Configuración de estilos para el resaltado
    try:
        ocr_text.tag_config("essential_value", font=("Segoe UI", 10, "bold"), foreground=COLOR_GREEN)
    except Exception:
        # Si el widget aún no está inicializado, ignoramos
        pass

    for line in t.splitlines():
        if ":" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                original_value = parts[1].strip()

                normalized_date = None
                key_lower = key.lower() # Mantenemos esta para el key_mapping

                # ¿Hay fecha normalizada asociada a esta clave?
                for key_prefix, processed_date in key_mapping.items():
                    # (Usamos la 'key_lower' original para que el regex [oa] funcione)
                    if re.search(key_prefix, key_lower):
                        normalized_date = processed_date
                        break

                # Valor que se va a mostrar (fecha normalizada o valor OCR original)
                if normalized_date:
                    value_to_show = (normalized_date or "").strip()
                else:
                    value_to_show = original_value.strip()

                # ¿Es un campo esencial?
                # 1. Limpiamos la clave de esta línea
                key_clean = _clean_key_for_matching(key)
                
                # 2. Comparamos (usando 'any' para match de subcadenas)
                #    Esto permite que "nombre" en la lista, coincida con "nombre completo" en el OCR
                is_essential = any(kw in key_clean for kw in essential_keywords_clean)
                
                tag = "essential_value" if is_essential else "value_bold"
                
                ocr_text.insert("end", f"{key}: ")
                ocr_text.insert("end", f"{value_to_show}\n", tag)
            else:
                ocr_text.insert("end", line + "\n")
        else:
            ocr_text.insert("end", line + "\n")

def analizar_actual():
    global idx
    if not rutas:
        messagebox.showinfo("HADES", "No hay imágenes cargadas."); return
    if idx < 0:
        idx = 0
    p = rutas[idx]
    t0 = time.time()
    _hide_logo_bg()
    
    # 1. OCR y Normalización con fallback automático
    texto, proveedor = vision_extract_text_with_fallback(p)
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
    riesgo, detalles, emoji_semaforo, color_semaforo = _authenticity_score(texto, p)
    dt = round(time.time() - t0, 2)

    # 3. Guardar resultados
    # Usamos el texto original para que el exportador trabaje con el output de Gemini
    _guardar_resultado(Path(p).name, texto, "actual", dt, datos_esenciales, riesgo, detalles)
    
    # 4. Mostrar en el panel
    ocr_text.delete("1.0", "end") # Limpiamos antes de mostrar
        
    # Bloque de Resultado 1/1 (Formato de carrusel)
    nombre_archivo = Path(p).name
    ocr_text.insert("end", f"\nRESULTADO 1/1 — {nombre_archivo}\n", "header")
    ocr_text.tag_config("header", font=("Segoe UI", 12, "bold"), foreground=ACCENT_2)
    
    # Mostrar proveedor usado
    ocr_text.insert("end", f"Analizado con: {proveedor}\n", "provider_tag")
    ocr_text.tag_config("provider_tag", foreground=COLOR_MUTED, font=("Segoe UI", 9, "italic"))
    
    # Mostrar semáforo de autenticidad
    ocr_text.insert("end", f"\n{emoji_semaforo} Autenticidad: {riesgo.upper()}\n", "risk_tag")
    if color_semaforo == "green":
        ocr_text.tag_config("risk_tag", foreground=COLOR_GREEN, font=("Segoe UI", 11, "bold"))
    elif color_semaforo == "yellow":
        ocr_text.tag_config("risk_tag", foreground="#FFD700", font=("Segoe UI", 11, "bold"))
    else:
        ocr_text.tag_config("risk_tag", foreground=COLOR_RED, font=("Segoe UI", 11, "bold"))
    if detalles:
        ocr_text.insert("end", f"Detalles: {'; '.join(detalles)}\n", "body_header")
    
    # Se imprime solo la línea de país limpia
    ocr_text.insert("end", f"\nTexto Completo (OCR original):\n", "body_header")
    ocr_text.tag_config("body_header", font=("Segoe UI", 10, "bold"), foreground=COLOR_TEXT)
    
    # (Punto 3 - Arreglo [DOCUMENTO])
    #if doc_pais:
        #ocr_text.insert("end", f"país: {doc_pais}\n", "essential_value")
    
    # Mostrar el texto OCR, sustituyendo las fechas por las procesadas (LLAMADA A LA FUNCIÓN CORREGIDA)
    ocr_text.tag_config("value_bold", font=("Segoe UI", 10, "bold"), foreground=COLOR_TEXT)
    texto_listo = texto.replace('\\n', '\n')
    _format_ocr_text_with_normalized_dates(texto_listo, date_results)
    
    ocr_text.see("end")
    root.update_idletasks() # Forzar el despliegue
    
    root.after(1000, _popup_feedback_then_export_drive)

def analizar_carrusel():
    """Analiza TODAS las imágenes y muestra cada resultado en el panel conforme avanza."""
    if not rutas:
        messagebox.showinfo("HADES", "No hay imágenes cargadas."); return

    total = len(rutas)
    _hide_logo_bg()
    ocr_text.delete("1.0", "end") # Limpiamos el panel
    
    # Configurar negrita para carrusel
    ocr_text.tag_config("value_bold", font=("Segoe UI", 10, "bold"), foreground=COLOR_TEXT)
    ocr_text.tag_config("header", font=("Segoe UI", 12, "bold"), foreground=ACCENT_2)
    ocr_text.tag_config("essential_header", font=("Segoe UI", 12, "bold"), foreground=ACCENT_2) # Tag para DATOS ESENCIALES
    ocr_text.tag_config("risk_tag", foreground=COLOR_GREEN, font=("Segoe UI", 10, "bold")) # Por defecto verde

    for i, p in enumerate(rutas, start=1):
        t0 = time.time()
        try:
            # 1. OCR y Normalización con fallback automático
            texto, proveedor = vision_extract_text_with_fallback(p)
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

            riesgo, detalles, emoji_semaforo, color_semaforo = _authenticity_score(texto, p)
            dt = round(time.time() - t0, 2)

            # 3. Guardar resultados
            _guardar_resultado(Path(p).name, texto, "carrusel", dt, datos_esenciales, riesgo, detalles)

            # 4. Mostrar en el panel (SOLO OCR y autenticidad)
            nombre_archivo = Path(p).name
            doc_pais_actual = _infer_doc_country(texto) # Re-obtener el país por si las claves de GTM/PHL funcionan mejor ahora
            
            # Mostrar encabezado de resultado
            ocr_text.insert("end", f"\n\nRESULTADO {i}/{total} — {nombre_archivo}\n", "header")
            
            # Mostrar proveedor usado
            ocr_text.insert("end", f"Analizado con: {proveedor}\n", "provider_tag")
            ocr_text.tag_config("provider_tag", foreground=COLOR_MUTED, font=("Segoe UI", 9, "italic"))
            
            # Mostrar semáforo de autenticidad
            ocr_text.insert("end", f"\n{emoji_semaforo} Autenticidad: {riesgo.upper()}\n", "risk_tag")
            if color_semaforo == "green":
                ocr_text.tag_config("risk_tag", foreground=COLOR_GREEN, font=("Segoe UI", 11, "bold"))
            elif color_semaforo == "yellow":
                ocr_text.tag_config("risk_tag", foreground="#FFD700", font=("Segoe UI", 11, "bold"))
            else:
                ocr_text.tag_config("risk_tag", foreground=COLOR_RED, font=("Segoe UI", 11, "bold"))
            if detalles:
                ocr_text.insert("end", f"Detalles: {'; '.join(detalles)}\n", "body_header")

            # (Punto 3 - Arreglo [DOCUMENTO])
            #if doc_pais_actual:
                #ocr_text.insert("end", f"país: {doc_pais_actual}\n", "essential_value")

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
    root.after(1000, _popup_feedback_then_export_drive)

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

        try:
            # === 1) OCR de frente y reverso (por separado) con fallback ===
            texto_frente, proveedor_frente = vision_extract_text_with_fallback(frente)
            texto_reverso, proveedor_reverso = vision_extract_text_with_fallback(reverso)

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

            riesgo, detalles, emoji_semaforo, color_semaforo = _authenticity_score(texto_total, frente)
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
            
            # Mostrar semáforo de autenticidad
            ocr_text.insert("end", f"\n{emoji_semaforo} Autenticidad: {riesgo.upper()}\n", "risk_tag")
            if color_semaforo == "green":
                ocr_text.tag_config("risk_tag", foreground=COLOR_GREEN, font=("Segoe UI", 11, "bold"))
            elif color_semaforo == "yellow":
                ocr_text.tag_config("risk_tag", foreground="#FFD700", font=("Segoe UI", 11, "bold"))
            else:
                ocr_text.tag_config("risk_tag", foreground=COLOR_RED, font=("Segoe UI", 11, "bold"))
            if detalles:
                ocr_text.insert("end", f"Detalles: {'; '.join(detalles)}\n", "body_header")

            # País (una sola vez por ID)
            #if doc_pais:
                #ocr_text.insert("end", f"país: {doc_pais}\n", "essential_value")

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
    root.after(1000, _popup_feedback_then_export_drive)

def _popup_feedback_then_export_drive():
    # Modal morado con 👍/👎 que BLOQUEA hasta seleccionar
    win = Toplevel(root)
    win.title("Califica el análisis")
    win.configure(bg=COLOR_CARD)
    win.transient(root)
    win.grab_set()
    Label(win, text="¿Te gustó el análisis?", bg=COLOR_CARD, fg=COLOR_TEXT).pack(pady=(14, 4))

    btns = Frame(win, bg=COLOR_CARD)
    btns.pack(pady=10)

    def choose(v):
        global FEEDBACK_RATING, metricas
        FEEDBACK_RATING = v
        for m in metricas:
            m['feedback'] = FEEDBACK_RATING or ""
        win.destroy()
        _export_drive_only()

    Button(btns, text="👍 Me gustó", command=lambda: choose('up'), bg=COLOR_PURPLE, fg="white", relief="flat", padx=16, pady=10).pack(side="left", padx=8)
    Button(btns, text="👎 No me gustó", command=lambda: choose('down'), bg=COLOR_BTN, fg="white", relief="flat", padx=16, pady=10).pack(side="left", padx=8)

    # Centrar y bloquear
    root.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width()//2 - win.winfo_width()//2)
    y = root.winfo_rooty() + (root.winfo_height()//2 - win.winfo_height()//2)
    try:
        win.geometry(f"+{x}+{y}")
    except Exception:
        pass
    root.wait_window(win)

def _export_drive_only():
    # Modal morado con 👍/👎 que BLOQUEA hasta seleccionar
    win = Toplevel(root)
    win.title("Califica el análisis")
    win.configure(bg=COLOR_CARD)
    win.transient(root)
    win.grab_set()
    Label(win, text="¿Te gustó el análisis?", bg=COLOR_CARD, fg=COLOR_TEXT).pack(pady=(14, 4))

    btns = Frame(win, bg=COLOR_CARD)
    btns.pack(pady=10)

    def choose(v):
        global FEEDBACK_RATING, metricas
        FEEDBACK_RATING = v
        for m in metricas:
            m['feedback'] = FEEDBACK_RATING or ""
        win.destroy()
        _export_drive_only()

    Button(btns, text="👍 Me gustó", command=lambda: choose('up'), bg=COLOR_PURPLE, fg="white", relief="flat", padx=16, pady=10).pack(side="left", padx=8)
    Button(btns, text="👎 No me gustó", command=lambda: choose('down'), bg=COLOR_BTN, fg="white", relief="flat", padx=16, pady=10).pack(side="left", padx=8)

    # Centrar y bloquear
    root.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width()//2 - win.winfo_width()//2)
    y = root.winfo_rooty() + (root.winfo_height()//2 - win.winfo_height()//2)
    try:
        win.geometry(f"+{x}+{y}")
    except Exception:
        pass
    root.wait_window(win)

def _export_drive_only():
    import pandas as pd  # Lazy import
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    resumen_df = pd.DataFrame(resultados)
    if resumen_df.empty:
        print("[HADES] No hay resultados para exportar a Drive.")
        return

    metricas_df = pd.DataFrame(metricas).copy()
    if metricas_df.empty:
        metricas_df = pd.DataFrame(columns=['archivo','api','tipo','duracion_s','usuario','feedback'])

    combinado_df = resumen_df.merge(metricas_df, on='archivo', how='left', suffixes=('', '_m'))
    preferred_order = ['archivo','texto','duracion_s','tipo','doc_pais','formato_fecha_detectado','fecha_expedicion_final','vigencia_final','fecha_nacimiento_final','otras_fechas_final','fechas_mdy','incluye_vigencia','vigencia_mdy','vigencia_sugerida_mdy','autenticidad_riesgo','autenticidad_detalles','api','usuario','feedback']
    final_cols = [c for c in preferred_order if c in combinado_df.columns] + [c for c in combinado_df.columns if c not in preferred_order]
    combinado_df = combinado_df[final_cols]

    tmp_dir = tempfile.gettempdir()
    drive_tmp_csv = os.path.join(tmp_dir, f"HADES_OCR_{ts}.csv")
    combinado_df.to_csv(drive_tmp_csv, index=False, encoding="utf-8-sig")

    remote_name = f"HADES_OCR_{ts}.csv"
    info_msgs = []
    ok, info = _subir_a_drive(drive_tmp_csv, remote_name, "text/csv"); info_msgs.append(info)
    if ok:
        # Se extrae el ID de la respuesta para el log
        file_id = info.split('id=')[-1].split(')')[0]
        print(f"[HADES] CSV subido a Drive (id={file_id})")
    else:
        print("[HADES] No se pudo subir a Drive: " + " | ".join(info_msgs))


def _do_export(destino_carpeta_local: str):
    import pandas as pd  # Lazy import
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(destino_carpeta_local, exist_ok=True)
    csv_path = os.path.join(destino_carpeta_local, f"HADES_OCR_{ts}.csv")
    txt_path = os.path.join(destino_carpeta_local, f"HADES_OCR_{ts}.txt")

    resumen_df = pd.DataFrame(resultados)
    if resumen_df.empty:
        messagebox.showinfo("Exportación", "No hay resultados para exportar localmente."); return

    # Usar las nuevas columnas finales para exportar los datos procesados
    cols = [c for c in ['archivo','texto','duracion_s','tipo','doc_pais','formato_fecha_detectado','fecha_expedicion_final','vigencia_final','fecha_nacimiento_final','otras_fechas_final'] if c in resumen_df.columns]
    out_df = resumen_df[cols].copy() if cols else resumen_df.copy()
    out_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    with open(txt_path, 'w', encoding='utf-8') as f:
        for _, row in out_df.iterrows():
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
    rutas.clear(); resultados.clear(); metricas.clear()
    global FEEDBACK_RATING; FEEDBACK_RATING=None
    ocr_text.delete("1.0", "end")
    _show_logo_bg() # Vuelve a mostrar el logo
    status.config(text="Se limpió el estado.")



# ========= VERIFICACIÓN DE INICIO CON KEYCLOAK =========
def _verificar_inicio():
    """Verifica usuario con Keycloak SSO"""
    if not _KEYCLOAK_OK:
        messagebox.showerror(
            "Keycloak no disponible",
            "El sistema de autenticación SSO no está configurado.\n"
            "Contacta al administrador del sistema."
        )
        return False
    
    # Intentar autenticación con Keycloak
    ok, msg = autenticar_con_keycloak()
    
    if ok:
        messagebox.showinfo(
            "Autenticación Exitosa",
            f"Bienvenido, {usuario_actual['nombre']}\n"
            f"Correo: {usuario_actual['correo']}"
        )
        return True
    else:
        messagebox.showerror(
            "Error de Autenticación",
            f"No se pudo iniciar sesión:\n{msg}"
        )
        return False


# ========= INICIO (Optimizado con verificación diferida) =========
def _init_app():
    """Inicializa la app después de verificar usuario"""
    if _verificar_inicio():
        root.bind_all("<Control-v>", lambda e: pegar_imagen_clipboard())
        _set_mode_ocr()
    else:
        root.destroy()

# Mostrar UI primero, luego verificar (arranque más rápido)
root.after(100, _init_app)  # Verificar después de 100ms
root.mainloop()
