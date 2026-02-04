"""
Módulo de detección y procesamiento de fechas para Hades Web.

CAMBIO PRINCIPAL vs Hades Ultimate:
- Preserva el formato original del OCR (no reformatea)
- Solo interpreta internamente para validaciones
"""

import re
from datetime import datetime, date
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class DateType(Enum):
    """Tipo de fecha detectada"""
    BIRTH = "birth"
    ISSUE = "issue"
    EXPIRATION = "expiration"
    UNKNOWN = "unknown"


class DateFormat(Enum):
    """Formato de fecha detectado"""
    MM_DD_YYYY = "MM/DD/YYYY"
    DD_MM_YYYY = "DD/MM/YYYY"
    YYYY_MM_DD = "YYYY-MM-DD"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


@dataclass
class DateInfo:
    """
    Información completa de una fecha detectada.
    
    REGLA CLAVE: 'original' NUNCA se modifica.
    'display' siempre es igual a 'original'.
    'parsed' se usa solo para validaciones internas.
    """
    # Datos principales
    original: str                    # Exactamente como aparece en OCR
    display: str                     # Lo que se muestra al usuario (= original)
    parsed: Optional[datetime]       # Para validaciones internas
    
    # Metadata
    date_type: DateType
    format_detected: DateFormat
    confidence: float                # 0.0 - 1.0
    
    # Contexto
    country_hint: Optional[str]
    
    # Validaciones
    is_valid: bool
    is_ambiguous: bool
    warnings: List[str]
    
    # Vigencia (si aplica)
    is_expired: Optional[bool] = None
    days_until_expiry: Optional[int] = None


# Diccionarios de meses (copiados de Hades Ultimate)
_MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12
}

_MONTHS_EN = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12
}

# Patrones regex (copiados de Hades Ultimate)
_DATE_RE_NUM_A = re.compile(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b')
_DATE_RE_ISO = re.compile(r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b')
_DATE_RE_DMY_H = re.compile(r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b')
_DATE_RE_DD_MM_YYYY_DOT = re.compile(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b')
_DATE_RE_DD_MM_YYYY_SPACE = re.compile(r'\b(\d{1,2})\s+(\d{1,2})\s+(\d{2,4})\b')
_DATE_RE_TXT_ES = re.compile(r'\b(\d{1,2})\s*(?:de\s*)?([A-Za-záéíóúÁÉÍÓÚñÑ]+)\s*(?:de\s*)?(\d{2,4})\b', re.IGNORECASE)
_DATE_RE_TXT_EN_DMY = re.compile(r'\b(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{2,4})\b', re.IGNORECASE)
_DATE_RE_TXT_EN_MDY = re.compile(r'\b([A-Za-z]{3,})\s+(\d{1,2})\s+(\d{2,4})\b', re.IGNORECASE)


def _coerce_year(y: int) -> int:
    """Convierte años de 2 dígitos a 4 dígitos"""
    if y < 100:
        return 2000 + y if y < 50 else 1900 + y
    return y


def detect_date_format(date_str: str, country_hint: Optional[str] = None) -> Tuple[DateFormat, float]:
    """
    Detecta el formato de una fecha SIN reformatearla.
    
    Returns:
        (formato_detectado, confianza)
    
    Reglas:
    1. Si día > 12 → formato claro
    2. Si ambos ≤ 12 → usar country_hint
    3. Si no hay hint → AMBIGUOUS
    """
    # Normalizar separadores
    normalized = date_str.replace('-', '/').replace('.', '/')
    parts = normalized.split('/')
    
    if len(parts) != 3:
        return DateFormat.UNKNOWN, 0.0
    
    try:
        p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return DateFormat.UNKNOWN, 0.0
    
    # Caso 1: Primera parte > 12 → DD/MM/YYYY
    if p1 > 12 and p2 <= 12:
        return DateFormat.DD_MM_YYYY, 1.0
    
    # Caso 2: Segunda parte > 12 → MM/DD/YYYY
    if p2 > 12 and p1 <= 12:
        return DateFormat.MM_DD_YYYY, 1.0
    
    # Caso 3: Ambos ≤ 12 → usar contexto de país
    if p1 <= 12 and p2 <= 12:
        if country_hint == "US":
            return DateFormat.MM_DD_YYYY, 0.7
        elif country_hint in ["MX", "AR", "CO", "CL", "PE", "EC", "BO", "BR"]:
            return DateFormat.DD_MM_YYYY, 0.7
        else:
            return DateFormat.AMBIGUOUS, 0.0
    
    return DateFormat.UNKNOWN, 0.0


def parse_date(date_str: str, format_hint: DateFormat) -> Optional[datetime]:
    """
    Parsea una fecha a datetime SOLO para validaciones internas.
    NO modifica el string original.
    """
    # Normalizar separadores
    normalized = date_str.replace('-', '/').replace('.', '/')
    parts = normalized.split('/')
    
    if len(parts) != 3:
        return None
    
    try:
        p1, p2, p3 = int(parts[0]), int(parts[1]), _coerce_year(int(parts[2]))
    except ValueError:
        return None
    
    # Interpretar según formato detectado
    if format_hint == DateFormat.MM_DD_YYYY:
        month, day, year = p1, p2, p3
    elif format_hint == DateFormat.DD_MM_YYYY:
        day, month, year = p1, p2, p3
    elif format_hint == DateFormat.YYYY_MM_DD:
        year, month, day = p1, p2, p3
    else:
        return None  # Formato desconocido o ambiguo
    
    try:
        return datetime(year, month, day)
    except ValueError:
        return None  # Fecha inválida


def analyze_date(
    date_str: str,
    country_hint: Optional[str] = None,
    date_type: DateType = DateType.UNKNOWN
) -> DateInfo:
    """
    Analiza una fecha SIN reformatearla.
    
    REGLA CLAVE:
    - original = date_str (sin cambios)
    - display = date_str (sin cambios)
    - parsed = datetime (solo para validaciones)
    """
    warnings = []
    
    # Detectar formato
    format_detected, confidence = detect_date_format(date_str, country_hint)
    
    # Verificar si es ambigua
    is_ambiguous = (format_detected == DateFormat.AMBIGUOUS)
    if is_ambiguous:
        warnings.append(f"Fecha ambigua: {date_str}. No se puede determinar formato con certeza.")
    
    # Parsear para validaciones internas
    parsed = parse_date(date_str, format_detected) if not is_ambiguous else None
    
    # Validar
    is_valid = parsed is not None
    
    # Calcular vigencia si es fecha de expiración
    is_expired = None
    days_until_expiry = None
    if parsed and date_type == DateType.EXPIRATION:
        today = date.today()
        expiry_date = parsed.date()
        is_expired = expiry_date < today
        days_until_expiry = (expiry_date - today).days
    
    return DateInfo(
        original=date_str,           # ← SIN CAMBIOS
        display=date_str,             # ← SIN CAMBIOS (igual al original)
        parsed=parsed,
        date_type=date_type,
        format_detected=format_detected,
        confidence=confidence,
        country_hint=country_hint,
        is_valid=is_valid,
        is_ambiguous=is_ambiguous,
        warnings=warnings,
        is_expired=is_expired,
        days_until_expiry=days_until_expiry
    )


def extract_dates_from_text(text: str, country_hint: Optional[str] = None) -> List[DateInfo]:
    """
    Extrae todas las fechas de un texto OCR.
    
    Returns:
        Lista de DateInfo con fechas preservadas (sin reformatear)
    """
    dates = []
    
    # Buscar patrones numéricos
    for pattern in [_DATE_RE_NUM_A, _DATE_RE_ISO, _DATE_RE_DMY_H, 
                    _DATE_RE_DD_MM_YYYY_DOT, _DATE_RE_DD_MM_YYYY_SPACE]:
        for match in pattern.finditer(text):
            date_str = match.group(0)
            date_info = analyze_date(date_str, country_hint)
            dates.append(date_info)
    
    # Buscar patrones textuales
    for pattern in [_DATE_RE_TXT_ES, _DATE_RE_TXT_EN_DMY, _DATE_RE_TXT_EN_MDY]:
        for match in pattern.finditer(text):
            date_str = match.group(0)
            # Para fechas textuales, el formato es claro
            date_info = analyze_date(date_str, country_hint)
            dates.append(date_info)
    
    return dates


def process_dates_by_type(text: str, country_hint: Optional[str] = None) -> Dict[str, Optional[DateInfo]]:
    """
    Procesa fechas clasificándolas por tipo (nacimiento, expedición, vencimiento).
    
    CAMBIO vs Hades Ultimate:
    - Retorna DateInfo en lugar de strings reformateados
    - Preserva el formato original del OCR
    """
    keywords_expiration = ["vencimiento", "vence", "expiración", "expiracion", "vigencia", 
                          "valid thru", "expires", "expiration"]
    keywords_issue = ["emision", "expedicion", "issue", "issued", "fecha de emision"]
    keywords_birth = ["fecha de nacimiento", "dob", "date of birth", "nacimiento"]
    
    result = {
        "birth": None,
        "issue": None,
        "expiration": None
    }
    
    # Extraer todas las fechas
    all_dates = extract_dates_from_text(text, country_hint)
    
    # Clasificar por contexto
    for line in text.splitlines():
        line_lower = line.lower()
        
        # Buscar fechas en esta línea
        line_dates = extract_dates_from_text(line, country_hint)
        
        for date_info in line_dates:
            # Clasificar según keywords
            if any(kw in line_lower for kw in keywords_expiration) and not result["expiration"]:
                date_info.date_type = DateType.EXPIRATION
                result["expiration"] = date_info
            elif any(kw in line_lower for kw in keywords_issue) and not result["issue"]:
                date_info.date_type = DateType.ISSUE
                result["issue"] = date_info
            elif any(kw in line_lower for kw in keywords_birth) and not result["birth"]:
                date_info.date_type = DateType.BIRTH
                result["birth"] = date_info
    
    return result
