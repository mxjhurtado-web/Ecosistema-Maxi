# -*- coding: utf-8 -*-
"""
hades_engine.py
===============
Motor analítico de HADES portado a la nube.
Realiza OCR estructurado y análisis forense visual avanzado de identificaciones
de 12+ países utilizando un único llamado REST de alta velocidad a Gemini Vision.

NO tiene dependencias de Tkinter ni de entorno gráfico.
Diseñado para alta velocidad, robustez y estabilidad en Render (Linux).
"""

import os
import re
import io
import json
import base64
import logging
import datetime
from typing import Dict, List, Optional, Tuple
import httpx

from .config_manager import config_manager
from .policy_templates import classify_document, policy_score_adjustment

logger = logging.getLogger(__name__)

# Diccionarios de meses de HADES
_MONTHS_ES = {
    "enero":1, "febrero":2, "marzo":3, "abril":4, "mayo":5, "junio":6,
    "julio":7, "agosto":8, "septiembre":9, "setiembre":9, "octubre":10, "noviembre":11, "diciembre":12,
    "ene":1, "feb":2, "mar":3, "abr":4, "may":5, "jun":6,
    "jul":7, "ago":8, "sep":9, "oct":10, "nov":11, "dic":12
}

_MONTHS_EN = {
    "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,"july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
    "jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"aug":8,"sep":9,"sept":9,"oct":10,"nov":11,"dec":12,
    "ene":1, "feb":2, "mar":3, "abr":4, "may":5, "jun":6, "jul":7, "ago":8, "sep":9, "oct":10, "nov":11, "dic":12
}

# Cues de países originales de HADES
_COUNTRY_CUES = {
    "GT": ["guatemala", "guatemalteca", "republica de guatemala", "identificacion consular", "documento personal de identificación", "pasaporte guatemala", "país emisor: gtm", "registro nacional de las personas"],
    "PH": ["pasaporte", "republic of the philippines", "republika ng pilipinas", "código de país: phl", "filipino"],
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
    "IL": ["teudat zehut", "תעודת זהות", "israeli id", "passport", "state of israel", "מדינת israel"],
    "VN": ["căn cước công dân", "chứng minh nhân dân", "giấy chứng minh nhân dân", "giấy tờ tùy thân", "hộ chiếu", "social insurance book", "republic of vietnam", "vietnam"],
}

# Patrones Regex de Fechas de HADES
_DATE_RE_TXT_ES = re.compile(r'\b(\d{1,2})\s*(?:de\s*)?([A-Za-záéíóúÁÉÍÓÚñÑ]+)\s*(?:de\s*)?(\d{2,4})\b', re.IGNORECASE)
_DATE_RE_TXT_EN_DMY = re.compile(r'\b(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{2,4})\b', re.IGNORECASE)
_DATE_RE_TXT_EN_MDY = re.compile(r'\b([A-Za-z]{3,})\s+(\d{1,2})\s+(\d{2,4})\b', re.IGNORECASE)
_DATE_RE_TXT_EN = re.compile(r'\b([A-Za-z]+)\s+(\d{1,2}),\s*(\d{2,4})\b', re.IGNORECASE)
_DATE_RE_NUM_A = re.compile(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b')
_DATE_RE_ISO = re.compile(r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b')
_DATE_RE_DMY_H = re.compile(r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b')
_DATE_RE_EN_MON_DD_YYYY_H = re.compile(r'\b([A-Za-z]{3,})[-/](\d{1,2})[-/](\d{2,4})\b', re.IGNORECASE)
_DATE_RE_EN_DD_MON_YYYY_H = re.compile(r'\b(\d{1,2})[-/]([A-Za-z]{3,})[-/](\d{2,4})\b', re.IGNORECASE)
_DATE_RE_DD_MM_YYYY_SPACE = re.compile(r'\b(\d{1,2})\s+(\d{1,2})\s+(\d{2,4})\b')
_DATE_RE_TXT_PASSPORT = re.compile(r'\b(\d{1,2})\s+([A-Za-z]{3,})\s+/\s+[A-Za-z]{3,}\s+(\d{2,4})\b', re.IGNORECASE)
_DATE_RE_DMMMYYYY = re.compile(r'\b(\d{1,2})([A-Za-z]{3})(\d{4})\b', re.IGNORECASE)
_DATE_RE_DD_MON_YYYY = re.compile(r'\b(\d{1,2})\s+([A-Z]{3})[/\s]+(\d{4})\b', re.IGNORECASE)
_DATE_RE_YEAR_RANGE = re.compile(r'(\d{4})\s*[-\u2013]\s*(\d{4})')
_DATE_RE_YEAR_ONLY = re.compile(r'\b(20\d{2})\b')
_DATE_RE_MM_YYYY = re.compile(r'\b(\d{1,2})/(\d{4})\b')
_DATE_RE_DD_MM_YYYY_DOT = re.compile(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b')
_DATE_RE_TXT_ES_FULL = re.compile(r'\b(\d{1,2})[-\s]+([a-záéíóúñ]+)[-\s]+(\d{2,4})\b', re.IGNORECASE)

# Reglas de ID y consistencia
_CURP_RE = re.compile(r'\b([A-Z][AEIOUX][A-Z]{2})(\d{2})(\d{2})(\d{2})[HM][A-Z]{5}[0-9A-Z]\d\b', re.IGNORECASE)
_RFC_PER_RE = re.compile(r'\b([A-ZÑ&]{4})(\d{2})(\d{2})(\d{2})[A-Z0-9]{3}\b', re.IGNORECASE)
_SAMPLE_WORDS = ("muestra", "sample", "specimen", "ejemplo", "void")
_NAME_HINTS = [
    r"(?:nombre|names|nombres)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s'.-]+?)(?:\s+(APELLIDOS|SURNAME|DIRECCION|CALLE))?$",
    r"(?:apellidos|surname)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s'.-]+?)(?:\s+(NOMBRES|NAMES|FECHA))?$",
    r"(?:nombre|name|titular)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s'.-]+)",
]
_DOB_HINTS = [
    r"(?:fecha\s*de\s*nacimiento|f\.\s*de\s*nac\.?|dob|date\s*of\s*birth|nacimient[oa])"
]


# ============================================================================
# FUNCIONES DE PROCESAMIENTO CORE (IDENTICAS A HADES)
# ============================================================================

def _clean_ocr_output(texto: str) -> str:
    if not texto: return ""
    return re.sub(r'\[DOCUMENTO\]\s*país:\s*[A-Z]{2}\s*—\s*formato\s*detectado:\s*.*', '', texto, flags=re.IGNORECASE).strip()

def _infer_doc_country(texto: str) -> Optional[str]:
    t = (texto or "").lower()
    for cc, cues in _COUNTRY_CUES.items():
        if any(c in t for c in cues):
            return cc
    return None

def _detect_language_bias(texto: str) -> Optional[str]:
    t = (texto or "").lower()
    score_es = sum(1 for m in _MONTHS_ES if m in t)
    score_en = sum(1 for m in _MONTHS_EN if m in t)
    return "ES" if score_es >= score_en and score_es > 0 else ("EN" if score_en > 0 else None)

def _coerce_year(y: int) -> int:
    if y < 100: return 2000 + y if y < 50 else 1900 + y
    return y

def _normalize_date_to_mdy_ctx(s: str, country_ctx: Optional[str], lang_ctx: Optional[str]) -> Optional[str]:
    if not s: return None
    st = s.strip()

    m_range = _DATE_RE_YEAR_RANGE.search(st)
    if m_range: st = m_range.group(2)

    if re.fullmatch(r'\b\d{4}\b', st): return f"12/31/{st}"

    m = _DATE_RE_MM_YYYY.search(st)
    if m:
        mm, y = m.groups()
        mm_int = int(mm)
        if 1 <= mm_int <= 12:
            return f"{mm_int:02d}/01/{int(y):04d}"

    m = _DATE_RE_DD_MM_YYYY_DOT.search(st)
    if m:
        d, mm, y = m.groups()
        try:
            d_int, mm_int, y_int = int(d), int(mm), int(y)
            if 1 <= d_int <= 31 and 1 <= mm_int <= 12:
                return f"{mm_int:02d}/{d_int:02d}/{y_int:04d}"
        except ValueError: pass

    m = _DATE_RE_TXT_ES_FULL.search(st)
    if m:
        da, mon, y = m.groups()
        mo = _MONTHS_ES.get(mon.lower())
        if mo: return f"{int(mo):02d}/{int(da):02d}/{_coerce_year(int(y)):04d}"

    m = _DATE_RE_TXT_ES.search(st)
    if m:
        da, mon, y = m.groups()
        mo = _MONTHS_ES.get(mon.lower())
        if mo: return f"{int(mo):02d}/{int(da):02d}/{_coerce_year(int(y)):04d}"

    m = re.search(r'(\d{1,2})([A-Za-z]{3})(\d{4})', st, re.IGNORECASE)
    if m:
        da, mon, y = m.groups()
        mo_int = _MONTHS_EN.get(mon.lower()[:3])
        if mo_int: return f"{mo_int:02d}/{int(da):02d}/{_coerce_year(int(y)):04d}"

    m = _DATE_RE_TXT_PASSPORT.search(st)
    if m:
        da, mon, y = m.groups()
        mo = _MONTHS_EN.get(mon.lower())
        if mo: return f"{int(mo):02d}/{int(da):02d}/{_coerce_year(int(y)):04d}"

    m = _DATE_RE_DD_MM_YYYY_SPACE.search(st)
    if m:
        d, m_, y = m.groups()
        try:
            d_int, m_int, y_int = int(d), int(m_), int(y)
            return f"{m_int:02d}/{d_int:02d}/{_coerce_year(y_int):04d}"
        except ValueError: pass

    m = _DATE_RE_DD_MON_YYYY.search(st)
    if m:
        da, mon, y = m.groups()
        mo = _MONTHS_ES.get(mon.lower()) or _MONTHS_EN.get(mon.lower())
        if mo: return f"{int(mo):02d}/{int(da):02d}/{_coerce_year(int(y)):04d}"

    for rx in [_DATE_RE_EN_MON_DD_YYYY_H, _DATE_RE_EN_DD_MON_YYYY_H, _DATE_RE_TXT_EN_MDY, _DATE_RE_TXT_EN_DMY]:
        m = rx.search(st)
        if m:
            parts = m.groups()
            if len(parts) == 3:
                if rx in (_DATE_RE_TXT_EN_MDY, _DATE_RE_EN_MON_DD_YYYY_H):
                    mon, da, y = parts[0], parts[1], parts[2]
                else:
                    da, mon, y = parts[0], parts[1], parts[2]
                mo = _MONTHS_EN.get(mon.lower())
                if mo: return f"{int(mo):02d}/{int(da):02d}/{_coerce_year(int(y)):04d}"

    for rx in [_DATE_RE_ISO, _DATE_RE_DMY_H]:
        m = rx.search(st)
        if m:
            parts = list(map(int, m.groups()))
            y = _coerce_year(parts[0] if rx == _DATE_RE_ISO else parts[2])
            mo = parts[1]
            da = parts[2] if rx == _DATE_RE_ISO else parts[0]
            return f"{mo:02d}/{da:02d}/{y:04d}"

    m = _DATE_RE_NUM_A.search(st)
    if m:
        a, b, y = m.groups()
        a, b, y = int(a), int(b), _coerce_year(int(y))
        prefer_dmy = (country_ctx not in {"US"} or lang_ctx == "ES")
        day, month = None, None
        if a > 12 and b <= 12: day, month = a, b
        elif b > 12 and a <= 12: month, day = a, b
        elif prefer_dmy: day, month = a, b
        else: month, day = a, b
        if day is not None and month is not None:
            return f"{int(month):02d}/{int(day):02d}/{y:04d}"

    return None

def _extract_all_dates(text: str) -> List[str]:
    if not text: return []
    hits = []
    custom_ddmmyyyy = re.compile(r'\b(\d{1,2})([A-Z]{3})(\d{4})\b', re.IGNORECASE)
    for rx in (_DATE_RE_TXT_ES, _DATE_RE_TXT_ES_FULL, _DATE_RE_TXT_EN, _DATE_RE_TXT_EN_DMY, _DATE_RE_TXT_EN_MDY, 
               _DATE_RE_EN_MON_DD_YYYY_H, _DATE_RE_EN_DD_MON_YYYY_H, _DATE_RE_ISO, _DATE_RE_DMY_H, 
               _DATE_RE_DD_MM_YYYY_DOT, _DATE_RE_NUM_A, _DATE_RE_DD_MM_YYYY_SPACE, _DATE_RE_TXT_PASSPORT, 
               _DATE_RE_YEAR_RANGE, _DATE_RE_MM_YYYY, _DATE_RE_DMMMYYYY, custom_ddmmyyyy):
        for m in rx.finditer(text):
            hits.append((m.group(0), m.start()))
    hits.sort(key=lambda x: x[1])
    return [h[0] for h in hits]

def _add_years_safe(d: datetime.date, years: int) -> datetime.date:
    try:
        return d.replace(year=d.year + years)
    except Exception:
        if d.month == 2 and d.day == 29:
            return d.replace(month=2, day=28, year=d.year + years)
        return d + datetime.timedelta(days=365*years)

def _process_all_dates_by_type(texto: str) -> Dict[str, Optional[str]]:
    doc_pais = _infer_doc_country(texto)
    is_usa_id = (doc_pais == "US")
    lang = _detect_language_bias(texto)

    results: Dict[str, any] = {
        "fecha_vigencia_final": None,
        "fecha_expedicion_final": None,
        "fecha_nacimiento_final": None,
        "otras_fechas_normalizadas": "",
        "vigencia_sugerida": None,
        "nombre": None,
        "tipo_identificacion": None,
        "kv_map": {}
    }

    vigencia_keywords = ["vencimiento", "vence", "expiración", "expiracion", "vigencia", "valido hasta", "valid thru", "caducidad", "fecha de caducidad", "válido hasta"]
    expedicion_keywords = ["emision", "expedicion", "expedición", "issue", "issued", "fecha de emision", "date of issue", "fecha de expedicion", "emitido", "fecha de emi"]
    nacimiento_keywords = ["fecha de nacimiento", "dob", "date of birth", "nacimient[oa]"]

    seen_originals = set()
    kv_map = {}

    def process_and_assign_date(original: str, date_type: str):
        is_already_mdy = False
        if original:
            if re.fullmatch(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', original.strip()):
                is_already_mdy = True

        if is_usa_id and is_already_mdy:
            final_date = original
        else:
            final_date = _normalize_date_to_mdy_ctx(original, doc_pais, lang)

        if not final_date:
            final_date = original

        results[f"fecha_{date_type}_final"] = final_date
        seen_originals.add(original)
        return final_date

    for line in texto.splitlines():
        ll = line.lower().strip()
        kv_match = re.search(r'([a-záéíóúñ\s]+):\s*(.*)', ll, re.IGNORECASE)
        if kv_match:
            key = kv_match.group(1).strip()
            value = kv_match.group(2).strip()

            if "nombre" in key and "padre" not in key and not results.get("nombre"):
                results["nombre"] = value.strip().upper()

            if "tipo" in key and ("documento" in key or "tarjeta" in key) and not results.get("tipo_identificacion"):
                results["tipo_identificacion"] = value.strip().upper()

            all_regexes = (_DATE_RE_NUM_A, _DATE_RE_ISO, _DATE_RE_DMY_H, _DATE_RE_DD_MM_YYYY_DOT,
                           _DATE_RE_EN_MON_DD_YYYY_H, _DATE_RE_EN_DD_MON_YYYY_H,
                           _DATE_RE_TXT_EN_MDY, _DATE_RE_TXT_EN_DMY, _DATE_RE_TXT_ES, _DATE_RE_TXT_ES_FULL,
                           _DATE_RE_DD_MM_YYYY_SPACE, _DATE_RE_TXT_PASSPORT, _DATE_RE_YEAR_RANGE, 
                           _DATE_RE_MM_YYYY, _DATE_RE_DMMMYYYY, _DATE_RE_DD_MON_YYYY)

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
                        if final_date: kv_map[key] = final_date
                    else:
                        is_already_mdy_other = re.fullmatch(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', original.strip())
                        if is_already_mdy_other:
                            kv_map[key] = original
                        else:
                            final_date = _normalize_date_to_mdy_ctx(original, doc_pais, lang)
                            kv_map[key] = final_date or original

    # Buscar sugerencias de vigencia si falta
    if not results["fecha_vigencia_final"]:
        vigencia_raw = None
        for line in texto.splitlines():
            if any(k in line.lower() for k in vigencia_keywords):
                range_match = re.search(r'(\d{4})\s*[-\u2013]\s*(\d{4})', line)
                year_match = re.search(r'\b\d{4}\b', line)
                if range_match: vigencia_raw = range_match.group(0)
                elif year_match: vigencia_raw = year_match.group(0)
                
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
            sugerida_dt = datetime.date.today()
            sugerida_dt = _add_years_safe(sugerida_dt, 5)
            sugerida_str = f"{sugerida_dt.strftime('%m/%d/%Y')} (Sugerida)"
            results["vigencia_sugerida"] = sugerida_str
            results["fecha_vigencia_final"] = sugerida_str

    results["kv_map"] = kv_map
    return results

def _extract_id_number(texto: str, doc_pais: Optional[str]) -> Optional[str]:
    if not texto: return None
    t_searchable = texto.upper().replace('\n', ' ')
    t_clean = t_searchable.replace(' ', '').replace('-', '')

    if doc_pais == "CO":
        nuip_match = re.search(r'(?:NUIP|NUMERO\s*UNICO|IDENTIFICACION\s*PERSONAL)[:\s-]*(\d{10})\b', t_searchable)
        if nuip_match: return nuip_match.group(1)
        nuip_fallback = re.search(r'\b(\d{10})\b', t_clean)
        if nuip_fallback: return nuip_fallback.group(1)

    if doc_pais == "EC":
        nui_match = re.search(r'(?:NUI|CEDULA|IDENTIFICACION)[:\s-]*(\d{10})\b', t_searchable)
        if nui_match: return nui_match.group(1)
        nui_fallback = re.search(r'\b(\d{10})\b', t_clean)
        if nui_fallback: return nui_fallback.group(1)

    if doc_pais == "BO":
        bo_match = re.search(r'(?:CEDULA|CI|IDENTIDAD)[:\s-]*(\d{7,8}(?:-?\d{1,2})?)\b', t_searchable)
        if bo_match: return bo_match.group(1).replace('-', '')
        bo_fallback = re.search(r'\b(\d{7,8})\b', t_clean)
        if bo_fallback: return bo_fallback.group(1)

    if doc_pais == "BR":
        cpf_match = re.search(r'(?:CPF)[:\s-]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})\b', t_searchable)
        if cpf_match: return cpf_match.group(1).replace('.', '').replace('-', '')
        rg_match = re.search(r'(?:RG|REGISTRO\s*GERAL)[:\s-]*(\d{7,9})\b', t_searchable)
        if rg_match: return rg_match.group(1)
        br_fallback = re.search(r'\b(\d{11})\b', t_clean)
        if br_fallback: return br_fallback.group(1)

    keywords_num = [
        "PASAPORTE N.", "NÚMERO DE PASAPORTE", "PASSPORT NO", "NÚMERO DE PASAPORTE", 
        "NÚMERO DE LICENCIA", "NO. LICENCIA", "NÚMERO DE SERIE",
        "NÚMERO DE MATRÍCULA", "MATRÍCULA CONSULAR",
        "CÓDIGO ÚNICO DE IDENTIFICACIÓN", "CUI",
        "DNI", "DPI", "ID NUMBER", "CLAVE DE ELECTOR", 
        "NÚMERO DE IDENTIFICACIÓN", "NÚMERO"
    ]

    for kw in keywords_num:
        line_match = re.search(f"{kw.replace(' ', ' ?')}\\s*[:\\-]?\\s*([A-Z0-9\\-]+)", t_searchable)
        if line_match:
            val = line_match.group(1).strip()
            clean_val = val.replace(' ', '').replace('-', '')
            if kw in ["CÓDIGO ÚNICO DE IDENTIFICACIÓN", "CUI"] and re.match(r'^\d{13}$', clean_val):
                return clean_val
            if clean_val and len(clean_val) >= 8:
                clean_val_final = re.sub(r'[A-ZÑ]+$', '', clean_val)
                if len(clean_val_final) >= 8: return clean_val_final

    if doc_pais == "MX":
        curp_match = _CURP_RE.search(t_clean)
        if curp_match: return curp_match.group(0)
        rfc_match = _RFC_PER_RE.search(t_clean)
        if rfc_match: return rfc_match.group(0)

    match_long_num = re.search(r'\b([A-Z0-9]{8,25})\b', t_clean)
    if match_long_num:
        val = match_long_num.group(1)
        if not val.isdigit() or len(val) > 8: return val

    return None

def _extract_id_type(texto: str, doc_pais: Optional[str]) -> Optional[str]:
    if not doc_pais: return None
    t = texto.lower()
    if doc_pais == "MX":
        if any(kw in t for kw in ["credencial para votar", "ine"]): return "Credencial INE (MX)"
        if "matrícula consular" in t: return "Matrícula Consular (MX)"
        if "pasaporte" in t and "mex" in t: return "Pasaporte (MX)"
    if doc_pais == "GT":
        if "documento personal de identificación" in t or "dpi" in t: return "DPI (GT)"
        if "identificacion consular" in t: return "Identificación Consular (GT)"
        if "pasaporte" in t: return "Pasaporte (GT)"
    if doc_pais == "PH": return "Pasaporte (PH)"
    if doc_pais == "US":
        if any(kw in t for kw in ["driver license", "licencia de conducir"]): return "Licencia de Conducir (US)"
    if "pasaporte" in t or "passport" in t: return "Pasaporte"
    if "licencia de conducir" in t or "driver license" in t: return "Licencia de Conducir"
    return None

def _extract_name(texto: str) -> Optional[str]:
    if not texto: return None
    t = texto.upper()
    name_parts = {"apellidos": None, "nombres": None, "segundo_apellido": None}

    for line in t.splitlines():
        match_apellido = re.search(r'(?:APELLIDOS|SURNAME|APELLIDO)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s\.\-]+)', line)
        if match_apellido:
            name_parts["apellidos"] = match_apellido.group(1).strip()
            
        match_nombre = re.search(r'(?:NOMBRES|NAME|GIVEN NAME|NOMBRE|NOMBRE COMPLETO)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s\.\-]+)', line)
        if match_nombre:
            val = match_nombre.group(1).strip()
            if "COMPLETO" in line and len(val.split()) > 2:
                return " ".join(val.split()).title()
            if val not in ["DELA CRUZ", "DE", "LA", "DEL"]:
                name_parts["nombres"] = val
        
        match_segundo = re.search(r'(?:SEGUNDO APELLIDO|SEGUNDOAPELLIDO)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s\.\-]+)', line)
        if match_segundo:
            name_parts["segundo_apellido"] = match_segundo.group(1).strip()

    apellidos = name_parts["apellidos"]
    nombres = name_parts["nombres"]
    segundo = name_parts["segundo_apellido"]

    apellidos_full = [apellidos] if apellidos else []
    if segundo and segundo != apellidos:
        apellidos_full.append(segundo)
    
    final_name_parts = [" ".join(apellidos_full).strip()] if apellidos_full else []
    if nombres: final_name_parts.append(nombres)
    
    final_name = " ".join(final_name_parts).strip()
    if final_name:
        clean_name = re.sub(r'\s+', ' ', final_name).strip()
        if len(clean_name.split()) >= 2 and not any(ch.isdigit() for ch in clean_name):
            title_cased = clean_name.title()
            for p in ["De ", "La ", "Los ", "Las ", "Y "]:
                title_cased = title_cased.replace(p, p.lower())
            return title_cased

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
                        if cand.endswith(kw): cand = cand[:-len(kw)].strip()
                    title_cased = " ".join(cand.split()).title()
                    for p in ["De ", "La ", "Los ", "Las ", "Y "]:
                        title_cased = title_cased.replace(p, p.lower())
                    return title_cased
    return None

def _age_from_mdy(mdy: str) -> Optional[int]:
    try:
        m, d, y = map(int, mdy.split("/"))
        dob = datetime.date(y, m, d)
        today = datetime.date.today()
        return (today - dob).days // 365
    except Exception: return None

def _parse_dob_from_curp(curp: str) -> Optional[str]:
    m = _CURP_RE.search(curp or "")
    if not m: return None
    yy, mm, dd = map(int, m.groups()[1:4])
    y = 2000 + yy if yy < 50 else 1900 + yy
    try:
        datetime.date(y, mm, dd)
        return f"{mm:02d}/{dd:02d}/{y:04d}"
    except Exception: return None


def _safe_parse_gemini_json(raw_text: str) -> dict:
    """
    Parsea de forma robusta la respuesta JSON de Gemini.
    - Quita bloques de código markdown (```json ... ```) si los hay.
    - Usa strict=False para tolerar caracteres de control y saltos de línea literales en strings.
    """
    if not raw_text:
        raise ValueError("El texto de respuesta de Gemini está vacío.")

    text_to_parse = raw_text.strip()

    # 1. Quitar bloques de código Markdown
    if text_to_parse.startswith("```"):
        text_to_parse = re.sub(r"^```(?:json)?\s*\n", "", text_to_parse)
        text_to_parse = re.sub(r"\n\s*```$", "", text_to_parse)
        text_to_parse = text_to_parse.strip()

    # 2. Parseo con strict=False (tolera newlines literales en strings)
    return json.loads(text_to_parse, strict=False)



# ============================================================================
# MOTOR GEMINI VISION + FORENSE UNIFICADO EN LA NUBE
# ============================================================================

class HadesEngine:
    """
    Motor forense unificado de HADES portado a la nube.
    Ejecuta OCR y análisis forense visual en una única llamada REST ultra-rápida.
    """

    def __init__(self):
        pass

    async def analyze_document_image(self, image_bytes: bytes, mime_type: str = "image/png") -> Dict[str, any]:
        """
        Analiza una imagen de identificación:
        1. Llama a Gemini Vision para extraer OCR y hacer análisis forense visual en un solo paso.
        2. Ejecuta lógica de puntuación y compliance.
        3. Retorna un reporte estructurado de riesgo forense.
        """
        logger.info("⏳ Iniciando análisis forense en la nube con HadesEngine...")
        start_time = datetime.datetime.now()

        # 1. Obtener API key dinámica
        config = await config_manager.get_mcp_config()
        api_key = config.gemini_api_key
        if not api_key:
            logger.error("❌ Gemini API Key no configurada en ORBIT.")
            return {
                "success": False,
                "error": "Gemini API Key no configurada en la plataforma."
            }

        # 2. Base64 de la imagen
        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        # 3. Prompt unificado: OCR + Forense (JSON estructurado con esquema)
        prompt = (
            "Actúa como un perito forense experto en documentos de identidad y oficial de cumplimiento corporativo.\n"
            "Analiza esta imagen y extrae la información solicitada en formato JSON exacto respetando la estructura del esquema.\n\n"
            "INSTRUCCIONES DE EXTRACCIÓN DE DATOS Y ANÁLISIS FORENSE:\n"
            "1. OCR TEXTUAL: Extrae de forma literal todo el texto visible del documento (nombres, fechas, firmas, códigos).\n"
            "2. EXTRAE EL PAÍS: Identifica el país emisor del documento y retorna su código de dos letras (ej: US, MX, GT, CO, PE).\n"
            "3. EXTRAE EL TIPO DE DOCUMENTO: Identifica si es una Licencia de Conducir, Tarjeta de Identificación, Pasaporte, Credencial para Votar, etc.\n"
            "4. EXTRAE EL NOMBRE: Identifica el nombre completo del titular tal como aparece en el documento (sin prefijos como 'Nombre:').\n"
            "5. EXTRAE EL NÚMERO DE ID: Identifica el número de documento de forma limpia (ej: D04774185).\n"
            "6. EXTRAE LAS FECHAS: Identifica la fecha de nacimiento (birth_date), fecha de vencimiento (expiration_date) y fecha de emisión (issue_date), formateándolas estrictamente como MM/DD/YYYY. Si una fecha no está presente, es ilegible o está en blanco en el documento, retorna una cadena vacía \"\".\n"
            "7. ELEMENTOS DE SEGURIDAD (0-10): Evalúa la presencia/consistencia de hologramas, guilloches, marcas de agua, relieves (10=sospechoso/ausente, 0=perfecto).\n"
            "8. CALIDAD DE IMPRESIÓN (0-10): Evalúa nitidez de los bordes del texto, registro de color y microimpresión (10=impresión casera/inconsistente, 0=oficial/offset).\n"
            "9. MANIPULACIÓN DIGITAL (0-10): Busca señales de clonación de píxeles, recortes alrededor de la foto/firma, artefactos extraños o bordes ásperos (10=evidencia de Photoshop, 0=consistente).\n"
            "10. TIPOGRAFÍA (0-10): Busca si las fuentes del texto coinciden con las tipografías oficiales o si son genéricas (ej. Arial) y si tienen espaciado irregular (10=sospechoso, 0=oficial).\n"
            "11. FOTOGRAFÍA (0-10): Evalúa si el fondo de la foto es uniforme, si las proporciones faciales son naturales y consistentes con la iluminación del documento (10=sospechoso, 0=profesional).\n\n"
            "Debes responder ÚNICAMENTE con un objeto JSON válido que cumpla con el esquema requerido."
        )

        # Definir el esquema JSON estructurado para Gemini
        schema = {
            "type": "OBJECT",
            "properties": {
                "extracted_ocr": {
                    "type": "STRING",
                    "description": "Texto completo literal extraído del documento."
                },
                "document_country": {
                    "type": "STRING",
                    "description": "Código de país de dos letras (ej: US, MX, GT, CO, PE) del documento o vacío si no se identifica."
                },
                "document_type": {
                    "type": "STRING",
                    "description": "Tipo de documento (ej: Licencia de Conducir, Tarjeta de Identificación, Pasaporte, Credencial para Votar)."
                },
                "extracted_name": {
                    "type": "STRING",
                    "description": "Nombre completo del titular tal como aparece en el documento o vacío si no se identifica."
                },
                "id_number": {
                    "type": "STRING",
                    "description": "Número de identificación, número de licencia o número de documento o vacío si no se identifica."
                },
                "expiration_date": {
                    "type": "STRING",
                    "description": "Fecha de vencimiento en formato MM/DD/YYYY o vacío si no tiene o está en blanco."
                },
                "birth_date": {
                    "type": "STRING",
                    "description": "Fecha de nacimiento en formato MM/DD/YYYY o vacío si no tiene."
                },
                "issue_date": {
                    "type": "STRING",
                    "description": "Fecha de emisión en formato MM/DD/YYYY o vacío si no tiene."
                },
                "forensic_analysis_summary": {
                    "type": "STRING",
                    "description": "Resumen técnico detallado del análisis forense visual."
                },
                "photoshop_detected": {
                    "type": "BOOLEAN",
                    "description": "Indica si hay sospecha o evidencia clara de manipulación digital."
                },
                "scores": {
                    "type": "OBJECT",
                    "properties": {
                        "security_elements": {"type": "INTEGER", "description": "Puntuación de 0 a 10 (10 sospechoso/ausente, 0 perfecto)."},
                        "printing_quality": {"type": "INTEGER", "description": "Puntuación de 0 a 10 (10 sospechoso, 0 perfecto)."},
                        "digital_manipulation": {"type": "INTEGER", "description": "Puntuación de 0 a 10 (10 sospechoso, 0 perfecto)."},
                        "typography": {"type": "INTEGER", "description": "Puntuación de 0 a 10 (10 sospechoso, 0 perfecto)."},
                        "photography": {"type": "INTEGER", "description": "Puntuación de 0 a 10 (10 sospechoso, 0 perfecto)."}
                    },
                    "required": ["security_elements", "printing_quality", "digital_manipulation", "typography", "photography"]
                },
                "evidences": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Detalles o anomalías específicas detectadas en el documento."
                }
            },
            "required": [
                "extracted_ocr",
                "document_country",
                "document_type",
                "extracted_name",
                "id_number",
                "expiration_date",
                "birth_date",
                "issue_date",
                "forensic_analysis_summary",
                "photoshop_detected",
                "scores",
                "evidences"
            ]
        }

        # 4. Llamada HTTP REST asíncrona a Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": b64_image
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.9,
                "responseMimeType": "application/json",
                "responseSchema": schema,
                "maxOutputTokens": 2048
            }
        }

        try:
            logger.info("📡 Enviando imagen a la API REST de Gemini...")
            async with httpx.AsyncClient() as client:
                r = await client.post(url, headers=headers, json=payload, timeout=60)
                
                if r.status_code != 200:
                    logger.error(f"❌ Error en API de Gemini ({r.status_code}): {r.text}")
                    return {
                        "success": False,
                        "error": f"Error del servicio visual de Gemini: {r.status_code}"
                    }
                
                response_json = r.json()
                raw_text = response_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                
                # Parsear el JSON retornado por Gemini de forma robusta (manejo de saltos de línea y Markdown)
                gemini_data = _safe_parse_gemini_json(raw_text)
                
                ocr_text = gemini_data.get("extracted_ocr", "")
                forensic_summary = gemini_data.get("forensic_analysis_summary", "")
                photoshop_detected = gemini_data.get("photoshop_detected", False)
                scores = gemini_data.get("scores", {})
                evidences = gemini_data.get("evidences", [])
                
                logger.info("✅ OCR y Análisis forense visual extraídos con éxito.")

                # ============================================================
                # CÁLCULO DE SCORE DE AUTENTICIDAD (ALINEADO A HADES LITE 2.2)
                # ============================================================
                score = 0
                details_internal = []
                details_user = []
                low_ocr = ocr_text.lower()
                
                # Usar el país extraído directamente por Gemini con fallback a inferencia
                doc_pais = gemini_data.get("document_country") or _infer_doc_country(ocr_text)
                if doc_pais:
                    doc_pais = doc_pais.strip().upper()

                # 1. Chequeo de Muestra/Plantilla (crítico)
                if any(w in low_ocr for w in _SAMPLE_WORDS if w):
                    score += 60
                    details_internal.append("⚠️ CRÍTICO: Contiene 'sample/muestra/void'")
                    details_user.append("Documento de muestra detectado")

                # 2. Extracción de Fechas e Identificación (motor HADES)
                date_results = _process_all_dates_by_type(ocr_text)
                
                # Usar extracción directa de Gemini si está disponible, con fallback a regex clásicos de HADES
                dob_use = gemini_data.get("birth_date") or date_results.get("fecha_nacimiento_final")
                if dob_use:
                    dob_use = dob_use.strip()
                    
                vig_final = gemini_data.get("expiration_date") or date_results.get("fecha_vigencia_final")
                if vig_final:
                    vig_final = vig_final.strip()
                    
                extracted_name = gemini_data.get("extracted_name") or date_results.get("nombre") or _extract_name(ocr_text)
                if extracted_name:
                    extracted_name = extracted_name.strip()
                    
                extracted_id = gemini_data.get("id_number") or _extract_id_number(ocr_text, doc_pais)
                if extracted_id:
                    extracted_id = extracted_id.strip()
                    
                extracted_type = gemini_data.get("document_type") or date_results.get("tipo_identificacion") or _extract_id_type(ocr_text, doc_pais)
                if extracted_type:
                    extracted_type = extracted_type.strip()

                # 3. Penalización por Nombre ausente
                if not extracted_name:
                    score += 15
                    details_internal.append("⚠️ No se detectó nombre válido")
                    details_user.append("Información incompleta")
                
                # 4. Penalización por edad implausible
                if dob_use and "Sugerida" not in dob_use:
                    age = _age_from_mdy(dob_use)
                    if age is not None and (age < 15 or age > 120):
                        score += 35
                        details_internal.append(f"⚠️ Edad implausible: {age} años")
                        details_user.append("Inconsistencia en datos personales")
                    
                    # Validación CURP (México)
                    curp_m = _CURP_RE.search(ocr_text)
                    if curp_m and doc_pais == "MX":
                        curp = curp_m.group(0)
                        curp_dob = _parse_dob_from_curp(curp)
                        if curp_dob and curp_dob != dob_use:
                            score += 45
                            details_internal.append(f"⚠️ CURP no coincide: CURP={curp_dob} vs DOB={dob_use}")
                            details_user.append("Inconsistencia en identificadores oficiales")
                    
                    # Validación RFC (México)
                    rfc_m = _RFC_PER_RE.search(ocr_text)
                    if rfc_m and doc_pais == "MX":
                        yy, mm, dd = map(int, rfc_m.groups()[1:4])
                        y = 2000 + yy if yy < 50 else 1900 + yy
                        rfc_dob = f"{mm:02d}/{dd:02d}/{y:04d}"
                        if rfc_dob != dob_use:
                            score += 25
                            details_internal.append(f"⚠️ RFC no coincide: RFC={rfc_dob} vs DOB={dob_use}")
                            details_user.append("Inconsistencia en datos fiscales")
                else:
                    score += 8
                    details_internal.append("⚠️ No se identificó fecha de nacimiento")
                    details_user.append("Información incompleta")

                # 5. Penalización por Vigencia ausente
                if not vig_final or "Sugerida" in vig_final:
                    score += 8
                    details_internal.append("⚠️ No se detectó vigencia válida")
                
                # 6. Penalización por ID ausente o falso
                if not extracted_id:
                    score += 6
                    details_internal.append("⚠️ No se detectó número de identificación")
                    details_user.append("Información incompleta")
                elif extracted_id in ["123456789", "000000000", "111111111", "999999999"]:
                    score += 40
                    details_internal.append(f"⚠️ Número de ID sospechoso: {extracted_id}")
                    details_user.append("Patrón de identificación no válido")

                # 7. Penalización por nombre sospechoso
                if extracted_name:
                    name_lower = extracted_name.lower()
                    fake_patterns = ["test", "prueba", "ejemplo", "sample", "xxxx", "aaaa"]
                    if any(pattern in name_lower for pattern in fake_patterns):
                        score += 35
                        details_internal.append(f"⚠️ Nombre sospechoso: {extracted_name}")
                        details_user.append("Datos personales no válidos")

                # 8. INTEGRAR SCORES VISUALES DE GEMINI (Peso máximo de 20 puntos)
                visual_score = 0
                
                # Photoshop penalty
                if photoshop_detected:
                    visual_score += 30
                    details_internal.append("🚨 Photoshop detectado por análisis de píxeles visuales")
                
                # Sumar penalizaciones de categorías
                manipulation_points = scores.get("digital_manipulation", 0)
                security_points = scores.get("security_elements", 0)
                quality_points = scores.get("printing_quality", 0)
                
                if manipulation_points > 5: visual_score += 15
                if security_points > 6: visual_score += 10
                if quality_points > 7: visual_score += 5

                # Aplicar tope a la influencia visual para evitar falsos positivos
                visual_score_aplicado = min(visual_score, 20)
                score += visual_score_aplicado
                
                if visual_score > 0:
                    details_internal.append(f"Visual: {visual_score} pts (aplicados: {visual_score_aplicado} pts)")
                    if evidences:
                        details_internal.extend([f"Forense: {e}" for e in evidences[:2]])

                # 9. CLASIFICACIÓN DE COMPLIANCE (Policy Templates 2025)
                compliance_result = classify_document(ocr_text, known_expiration_date=gemini_data.get("expiration_date"))
                acceptance = compliance_result.get("acceptance", "REVIEW")
                policy_reason = compliance_result.get("policy_reason", "")
                
                # Ajuste de score por compliance
                policy_adj, policy_adj_reason = policy_score_adjustment(acceptance)
                score += policy_adj
                if policy_adj > 0:
                    details_internal.append(f"Compliance: {policy_adj_reason} (+{policy_adj} pts)")
                    details_user.append(policy_reason)

                # 10. DEFINIR RIESGO Y SEMÁFORO FINAL (UMBRALES ESTRICTOS HADES)
                if score <= 16:
                    riesgo = "BAJO RIESGO"
                    color = "green"
                    emoji = "🟢"
                    if not details_user:
                        details_user = ["El documento cumple los parámetros de autenticidad."]
                elif score <= 40:
                    riesgo = "RIESGO MEDIO"
                    color = "yellow"
                    emoji = "🟡"
                    if not details_user:
                        details_user = ["Requiere verificación manual adicional."]
                else:
                    riesgo = "ALTO RIESGO"
                    color = "red"
                    emoji = "🔴"
                    if not details_user:
                        details_user = ["Alta sospecha de inconsistencia o adulteración."]

                latency = (datetime.datetime.now() - start_time).total_seconds()
                logger.info(f"🏁 Análisis completado en {latency:.2f}s | Score: {score} | Riesgo: {riesgo}")

                return {
                    "success": True,
                    "score": min(score, 100),
                    "riesgo": riesgo,
                    "color": color,
                    "emoji": emoji,
                    "data": {
                        "pais": doc_pais or "NO IDENTIFICADO",
                        "tipo": extracted_type or "DESCONOCIDO",
                        "nombre": extracted_name or "NO DETECTADO",
                        "id": extracted_id or "NO DETECTADO",
                        "expiracion": vig_final or "NO DETECTADA",
                        "nacimiento": dob_use or "NO DETECTADO",
                        "compliance_status": acceptance,
                        "compliance_reason": policy_reason
                    },
                    "forensic_details": {
                        "summary": forensic_summary,
                        "photoshop_detected": photoshop_detected,
                        "evidences": evidences,
                        "scores": scores
                    },
                    "details_internal": details_internal,
                    "details_user": list(set(details_user)),
                    "latency_sec": latency
                }

        except Exception as e:
            logger.exception("❌ Error procesando el documento en HadesEngine:")
            return {
                "success": False,
                "error": f"Error interno en HadesEngine: {str(e)}"
            }

# Instancia singleton del motor
hades_engine = HadesEngine()
