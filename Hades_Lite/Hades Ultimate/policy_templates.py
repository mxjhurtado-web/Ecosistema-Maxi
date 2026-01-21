# -*- coding: utf-8 -*-
"""
policy_templates.py
===================
Módulo desacoplado para clasificación de documentos de identidad
según reglas de cumplimiento (Compliance 2025).

NO modifica la lógica existente de hadeslite_2.2.py.
Solo provee clasificación y ajuste de score.
"""

import re
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CONSTANTES - Reglas de Cumplimiento 2025
# ============================================================================

# Estados con "Limitación Federal" en licencias/IDs
LIMITED_FEDERAL_STATES = {
    "COLORADO", "CO",
    "CONNECTICUT", "CT",
    "CALIFORNIA", "CA",
    "DELAWARE", "DE",
    "DISTRICT OF COLUMBIA", "DC", "D.C.",
    "HAWAII", "HI",
    "ILLINOIS", "IL",
    "MARYLAND", "MD",
    "NEVADA", "NV",
    "NEW MEXICO", "NM",
    "UTAH", "UT",
    "VERMONT", "VT",
    "WASHINGTON", "WA"
}

# Keywords que indican limitación federal
FEDERAL_LIMITS_KEYWORDS = [
    "FEDERAL LIMITS APPLY",
    "NOT FOR FEDERAL IDENTIFICATION",
    "NOT FOR FEDERAL USE",
    "FEDERAL PURPOSES",
    "LIMITED PURPOSE"
]

# Documentos NO aceptables (rechazo directo)
REJECT_KEYWORDS = [
    "CURP",
    "FM1", "FM2", "FM3",
    "ACTA DE NACIMIENTO",
    "BIRTH CERTIFICATE",
    "CEDULA PROFESIONAL",
    "LICENCIA INTERNACIONAL",
    "INTERNATIONAL DRIVING PERMIT",
    "VOTER REGISTRATION",
    "SOCIAL SECURITY CARD",
    "TARJETA DE SEGURO SOCIAL"
]

# Reglas de documentos válidos por país
DOC_RULES: List[Dict] = [
    # ========== ESTADOS UNIDOS ==========
    {
        "country": "US",
        "type": "DRIVER_LICENSE",
        "patterns": [
            r"\bDRIVER'?S?\s+LICENSE\b",
            r"\bDL\s+CLASS\b",
            r"\bOPERATOR\s+LICENSE\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "US",
        "type": "STATE_ID",
        "patterns": [
            r"\bIDENTIFICATION\s+CARD\b",
            r"\bSTATE\s+ID\b",
            r"\bID\s+CARD\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "US",
        "type": "US_PASSPORT",
        "patterns": [
            r"\bUNITED\s+STATES\s+OF\s+AMERICA\b",
            r"\bPASSPORT\b.*\bUSA\b",
            r"\bU\.?S\.?\s+PASSPORT\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "US",
        "type": "PASSPORT_CARD",
        "patterns": [
            r"\bPASSPORT\s+CARD\b",
            r"\bU\.?S\.?\s+PASSPORT\s+CARD\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "US",
        "type": "MILITARY_ID",
        "patterns": [
            r"\bDEPARTMENT\s+OF\s+DEFENSE\b",
            r"\bMILITARY\s+ID\b",
            r"\bARMED\s+FORCES\b",
            r"\bDOD\s+ID\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "US",
        "type": "EAD_I766",
        "patterns": [
            r"\bI-766\b",
            r"\bEMPLOYMENT\s+AUTHORIZATION\b",
            r"\bEAD\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "US",
        "type": "GREEN_CARD",
        "patterns": [
            r"\bPERMANENT\s+RESIDENT\s+CARD\b",
            r"\bGREEN\s+CARD\b",
            r"\bI-551\b"
        ],
        "acceptance": "ACCEPTED"
    },
    
    # ========== MÉXICO ==========
    {
        "country": "MX",
        "type": "INE",
        "patterns": [
            r"\bINE\b",
            r"\bCREDENCIAL\s+PARA\s+VOTAR\b",
            r"\bINSTITUTO\s+NACIONAL\s+ELECTORAL\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "MX",
        "type": "MATRICULA_CONSULAR",
        "patterns": [
            r"\bMATRICULA\s+CONSULAR\b",
            r"\bCONSULADO\s+DE\s+MEXICO\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "MX",
        "type": "PASSPORT",
        "patterns": [
            r"\bPASAPORTE\b.*\bMEXICO\b",
            r"\bMEXICAN\s+PASSPORT\b"
        ],
        "acceptance": "ACCEPTED"
    },
    
    # ========== GUATEMALA ==========
    {
        "country": "GT",
        "type": "DPI",
        "patterns": [
            r"\bDPI\b",
            r"\bDOCUMENTO\s+PERSONAL\s+DE\s+IDENTIFICACION\b",
            r"\bREGISTRO\s+NACIONAL\s+DE\s+LAS\s+PERSONAS\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "GT",
        "type": "PASSPORT",
        "patterns": [
            r"\bPASAPORTE\b.*\bGUATEMALA\b",
            r"\bREPUBLICA\s+DE\s+GUATEMALA\b"
        ],
        "acceptance": "ACCEPTED"
    },
    
    # ========== EL SALVADOR ==========
    {
        "country": "SV",
        "type": "DUI",
        "patterns": [
            r"\bDUI\b",
            r"\bDOCUMENTO\s+UNICO\s+DE\s+IDENTIDAD\b",
            r"\bREGISTRO\s+NACIONAL\s+DE\s+LAS\s+PERSONAS\s+NATURALES\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "SV",
        "type": "PASSPORT",
        "patterns": [
            r"\bPASAPORTE\b.*\bEL\s+SALVADOR\b",
            r"\bREPUBLICA\s+DE\s+EL\s+SALVADOR\b"
        ],
        "acceptance": "ACCEPTED"
    },
    
    # ========== HONDURAS ==========
    {
        "country": "HN",
        "type": "RNP",
        "patterns": [
            r"\bRNP\b",
            r"\bREGISTRO\s+NACIONAL\s+DE\s+LAS\s+PERSONAS\b",
            r"\bTARJETA\s+DE\s+IDENTIDAD\b.*\bHONDURAS\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "HN",
        "type": "PASSPORT",
        "patterns": [
            r"\bPASAPORTE\b.*\bHONDURAS\b",
            r"\bREPUBLICA\s+DE\s+HONDURAS\b"
        ],
        "acceptance": "ACCEPTED"
    },
    
    # ========== COLOMBIA ==========
    {
        "country": "CO",
        "type": "CEDULA",
        "patterns": [
            r"\bCEDULA\s+DE\s+CIUDADANIA\b",
            r"\bREGISTRADURIA\s+NACIONAL\b",
            r"\bREPUBLICA\s+DE\s+COLOMBIA\b"
        ],
        "acceptance": "ACCEPTED"
    },
    {
        "country": "CO",
        "type": "PASSPORT",
        "patterns": [
            r"\bPASAPORTE\b.*\bCOLOMBIA\b"
        ],
        "acceptance": "ACCEPTED"
    }
]


# ============================================================================
# HELPERS PRIVADOS
# ============================================================================

def _normalize_text(text: str) -> str:
    """Normaliza texto para matching: uppercase, colapsar espacios."""
    if not text:
        return ""
    # Uppercase
    normalized = text.upper()
    # Colapsar múltiples espacios/saltos de línea en uno solo
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()


def _match_rule(text: str, rule: Dict) -> bool:
    """
    Verifica si el texto coincide con algún patrón de la regla.
    
    Args:
        text: Texto normalizado
        rule: Dict con 'patterns' (list de regex strings)
    
    Returns:
        True si al menos un patrón coincide
    """
    patterns = rule.get("patterns", [])
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _check_federal_limits(text: str, state_detected: Optional[str] = None) -> bool:
    """
    Verifica si el documento tiene limitación federal.
    
    Args:
        text: Texto normalizado del OCR
        state_detected: Estado detectado (opcional)
    
    Returns:
        True si tiene limitación federal
    """
    # 1. Buscar keywords de limitación federal
    for keyword in FEDERAL_LIMITS_KEYWORDS:
        if keyword in text:
            return True
    
    # 2. Si se detectó un estado con limitación federal
    if state_detected:
        state_upper = state_detected.upper()
        if state_upper in LIMITED_FEDERAL_STATES:
            return True
    
    # 3. Buscar estados con limitación en el texto
    for state in LIMITED_FEDERAL_STATES:
        # Buscar como palabra completa
        if re.search(rf'\b{re.escape(state)}\b', text):
            return True
    
    return False


def _check_rejection(text: str) -> Tuple[bool, Optional[str]]:
    """
    Verifica si el documento debe ser rechazado directamente.
    
    Args:
        text: Texto normalizado del OCR
    
    Returns:
        (is_rejected, reason)
    """
    for keyword in REJECT_KEYWORDS:
        if keyword in text:
            return True, f"Documento no aceptable: {keyword}"
    return False, None


def _detect_state(text: str) -> Optional[str]:
    """
    Intenta detectar el estado en documentos US.
    
    Returns:
        Código del estado (ej: "CA", "NY") o None
    """
    # Buscar patrones comunes de estado
    # Ej: "STATE OF CALIFORNIA", "CALIFORNIA", "CA"
    for state in LIMITED_FEDERAL_STATES:
        if re.search(rf'\b{re.escape(state)}\b', text):
            # Retornar el código de 2 letras si es posible
            if len(state) == 2:
                return state
            # Si es nombre completo, buscar el código
            for code in LIMITED_FEDERAL_STATES:
                if len(code) == 2 and code in text:
                    return code
    return None


def _check_expiration(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verifica si el documento está expirado.
    
    Args:
        text: Texto normalizado del OCR
    
    Returns:
        (is_expired, expiration_date, reason)
    """
    import datetime
    
    # Keywords de vigencia/expiración
    expiration_keywords = [
        r"VENCIMIENTO[:\s]+",
        r"VENCE[:\s]+",
        r"EXPIRACI[OÓ]N[:\s]+",
        r"VIGENCIA[:\s]+",
        r"VALID\s+THRU[:\s]+",
        r"EXPIRES[:\s]+",
        r"EXPIRY[:\s]+",
        r"CADUCIDAD[:\s]+"
    ]
    
    # Patrones de fecha
    date_patterns = [
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b',  # MM/DD/YYYY o DD/MM/YYYY
        r'\b(\d{1,2})\s+([A-Z]{3})\s+(\d{2,4})\b',    # DD MON YYYY
        r'\b([A-Z]{3})[/-](\d{1,2})[/-](\d{2,4})\b',  # MON-DD-YYYY
    ]
    
    # Buscar fecha de expiración
    for keyword in expiration_keywords:
        keyword_match = re.search(keyword, text, re.IGNORECASE)
        if keyword_match:
            # Buscar fecha después del keyword
            text_after = text[keyword_match.end():keyword_match.end()+50]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, text_after, re.IGNORECASE)
                if date_match:
                    try:
                        # Intentar parsear la fecha
                        groups = date_match.groups()
                        
                        # Determinar formato
                        if len(groups) == 3:
                            if groups[1].isdigit():  # MM/DD/YYYY o DD/MM/YYYY
                                # Asumir MM/DD/YYYY para USA, DD/MM/YYYY para otros
                                # Por simplicidad, intentar ambos
                                try:
                                    month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                                    if year < 100:
                                        year = 2000 + year if year < 50 else 1900 + year
                                    exp_date = datetime.date(year, month, day)
                                except ValueError:
                                    # Intentar invertido
                                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                                    if year < 100:
                                        year = 2000 + year if year < 50 else 1900 + year
                                    exp_date = datetime.date(year, month, day)
                            else:  # Formato con mes textual
                                # Mapeo de meses
                                months = {
                                    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                                    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12,
                                    'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'MAY': 5, 'JUN': 6,
                                    'JUL': 7, 'AGO': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DIC': 12
                                }
                                
                                if pattern == date_patterns[1]:  # DD MON YYYY
                                    day, mon, year = int(groups[0]), groups[1].upper(), int(groups[2])
                                else:  # MON-DD-YYYY
                                    mon, day, year = groups[0].upper(), int(groups[1]), int(groups[2])
                                
                                month = months.get(mon)
                                if not month:
                                    continue
                                    
                                if year < 100:
                                    year = 2000 + year if year < 50 else 1900 + year
                                exp_date = datetime.date(year, month, day)
                            
                            # Comparar con fecha actual
                            today = datetime.date.today()
                            if exp_date < today:
                                exp_str = exp_date.strftime("%m/%d/%Y")
                                return True, exp_str, f"Documento expirado el {exp_str}"
                            else:
                                exp_str = exp_date.strftime("%m/%d/%Y")
                                return False, exp_str, f"Documento válido hasta {exp_str}"
                                
                    except (ValueError, IndexError):
                        continue
    
    return False, None, "No se pudo determinar fecha de expiración"


# ============================================================================
# API PÚBLICA
# ============================================================================

def classify_document(
    ocr_text_front: str,
    ocr_text_back: Optional[str] = None
) -> Dict[str, any]:
    """
    Clasifica un documento según reglas de cumplimiento.
    
    Args:
        ocr_text_front: Texto OCR del frente del documento
        ocr_text_back: Texto OCR del reverso (opcional)
    
    Returns:
        Dict con:
        - doc_country: "US|MX|GT|SV|HN|CO|UNKNOWN"
        - doc_type: "INE|DPI|DUI|RNP|DRIVER_LICENSE|..."
        - acceptance: "ACCEPTED|ACCEPTED_LIMITED|REJECTED|REVIEW"
        - policy_reason: Texto explicativo
        - policy_evidence: Lista de patrones/keywords encontrados
    """
    # Resultado por defecto
    result = {
        "doc_country": "UNKNOWN",
        "doc_type": "UNKNOWN",
        "acceptance": "REVIEW",
        "policy_reason": "No se pudo clasificar el documento",
        "policy_evidence": []
    }
    
    # Validar entrada
    if not ocr_text_front or not ocr_text_front.strip():
        result["policy_reason"] = "OCR vacío; revisión manual requerida"
        return result
    
    # Normalizar textos
    text_front = _normalize_text(ocr_text_front)
    text_combined = text_front
    
    if ocr_text_back:
        text_back = _normalize_text(ocr_text_back)
        text_combined = f"{text_front} {text_back}"
    
    # 1. VERIFICAR RECHAZO DIRECTO
    is_rejected, reject_reason = _check_rejection(text_combined)
    if is_rejected:
        result["acceptance"] = "REJECTED"
        result["policy_reason"] = reject_reason
        result["policy_evidence"] = [reject_reason]
        return result
    
    # 2. INTENTAR CLASIFICAR POR REGLAS
    matched_rule = None
    for rule in DOC_RULES:
        if _match_rule(text_combined, rule):
            matched_rule = rule
            break
    
    if not matched_rule:
        # No se encontró coincidencia
        result["policy_reason"] = "Documento no reconocido; revisión recomendada"
        return result
    
    # 3. DOCUMENTO RECONOCIDO
    result["doc_country"] = matched_rule["country"]
    result["doc_type"] = matched_rule["type"]
    result["acceptance"] = matched_rule["acceptance"]
    result["policy_evidence"] = matched_rule["patterns"]
    
    # 🆕 3.5. VERIFICAR EXPIRACIÓN
    is_expired, exp_date, exp_reason = _check_expiration(text_combined)
    result["is_expired"] = is_expired
    result["expiration_date"] = exp_date
    result["expiration_reason"] = exp_reason
    
    # Si el documento está expirado, marcarlo como REJECTED
    if is_expired:
        result["acceptance"] = "REJECTED"
        result["policy_reason"] = f"Documento EXPIRADO - {exp_reason}"
        return result
    
    # 4. VERIFICAR LIMITACIÓN FEDERAL (solo para US)
    if matched_rule["country"] == "US":
        state_detected = _detect_state(text_combined)
        has_federal_limits = _check_federal_limits(text_combined, state_detected)
        
        if has_federal_limits:
            result["acceptance"] = "ACCEPTED_LIMITED"
            result["policy_reason"] = f"Documento aceptable con limitación federal ({matched_rule['type']})"
            if state_detected:
                result["policy_reason"] += f" - Estado: {state_detected}"
            # Agregar info de vigencia si está disponible
            if exp_date:
                result["policy_reason"] += f" - {exp_reason}"
        else:
            result["policy_reason"] = f"Documento aceptable ({matched_rule['type']})"
            if exp_date:
                result["policy_reason"] += f" - {exp_reason}"
    else:
        result["policy_reason"] = f"Documento aceptable ({matched_rule['country']} - {matched_rule['type']})"
        if exp_date:
            result["policy_reason"] += f" - {exp_reason}"
    
    return result


def policy_score_adjustment(acceptance: str) -> Tuple[int, str]:
    """
    Calcula el ajuste de score según la clasificación de cumplimiento.
    
    Args:
        acceptance: "ACCEPTED|ACCEPTED_LIMITED|REJECTED|REVIEW"
    
    Returns:
        (score_adjustment, reason)
        - REJECTED: +35 puntos (alto riesgo)
        - ACCEPTED_LIMITED: +10 puntos (validación física recomendada)
        - REVIEW: +8 puntos (no clasificado)
        - ACCEPTED: 0 puntos (sin ajuste)
    """
    adjustments = {
        "REJECTED": (35, "Documento NO aceptable según Cumplimiento"),
        "ACCEPTED_LIMITED": (10, "Documento aceptable con limitación; validación física recomendada"),
        "REVIEW": (8, "No se pudo clasificar; revisión recomendada"),
        "ACCEPTED": (0, "Documento aceptable")
    }
    
    return adjustments.get(acceptance, (8, "Estado de aceptación desconocido"))


# ============================================================================
# DEMO / TESTING
# ============================================================================

def _demo():
    """Función de demostración con casos de prueba."""
    print("=" * 80)
    print("DEMO: Policy Templates - Clasificación de Documentos")
    print("=" * 80)
    
    # Caso 1: INE México
    print("\n[TEST 1] INE México")
    ocr_ine = """
    INSTITUTO NACIONAL ELECTORAL
    CREDENCIAL PARA VOTAR
    NOMBRE: JUAN PEREZ GARCIA
    CLAVE DE ELECTOR: PRGJ850101HDFRNN09
    """
    result = classify_document(ocr_ine)
    print(f"País: {result['doc_country']}")
    print(f"Tipo: {result['doc_type']}")
    print(f"Aceptación: {result['acceptance']}")
    print(f"Razón: {result['policy_reason']}")
    adj, reason = policy_score_adjustment(result['acceptance'])
    print(f"Ajuste de score: +{adj} ({reason})")
    
    # Caso 2: Driver License con limitación federal
    print("\n[TEST 2] Driver License California con limitación federal")
    ocr_dl_limited = """
    STATE OF CALIFORNIA
    DRIVER LICENSE
    FEDERAL LIMITS APPLY
    NAME: JOHN DOE
    DL CLASS: C
    """
    result = classify_document(ocr_dl_limited)
    print(f"País: {result['doc_country']}")
    print(f"Tipo: {result['doc_type']}")
    print(f"Aceptación: {result['acceptance']}")
    print(f"Razón: {result['policy_reason']}")
    adj, reason = policy_score_adjustment(result['acceptance'])
    print(f"Ajuste de score: +{adj} ({reason})")
    
    # Caso 3: CURP (rechazado)
    print("\n[TEST 3] CURP (documento no aceptable)")
    ocr_curp = """
    CURP: PRGJ850101HDFRNN09
    NOMBRE: JUAN PEREZ GARCIA
    """
    result = classify_document(ocr_curp)
    print(f"País: {result['doc_country']}")
    print(f"Tipo: {result['doc_type']}")
    print(f"Aceptación: {result['acceptance']}")
    print(f"Razón: {result['policy_reason']}")
    adj, reason = policy_score_adjustment(result['acceptance'])
    print(f"Ajuste de score: +{adj} ({reason})")
    
    # Caso 4: DPI Guatemala
    print("\n[TEST 4] DPI Guatemala")
    ocr_dpi = """
    REPUBLICA DE GUATEMALA
    REGISTRO NACIONAL DE LAS PERSONAS
    DOCUMENTO PERSONAL DE IDENTIFICACION
    DPI: 1234567890123
    """
    result = classify_document(ocr_dpi)
    print(f"País: {result['doc_country']}")
    print(f"Tipo: {result['doc_type']}")
    print(f"Aceptación: {result['acceptance']}")
    print(f"Razón: {result['policy_reason']}")
    adj, reason = policy_score_adjustment(result['acceptance'])
    print(f"Ajuste de score: +{adj} ({reason})")
    
    print("\n" + "=" * 80)
    print("✅ Demo completado")
    print("=" * 80)


if __name__ == "__main__":
    _demo()
