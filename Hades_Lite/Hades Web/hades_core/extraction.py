"""
Módulo de extracción de datos de documentos.

Extrae nombres, números de ID y tipos de documento.
Migrado de Hades Ultimate.
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass


# Regex patterns para IDs específicos
_CURP_RE = re.compile(
    r'\b([A-Z][AEIOUX][A-Z]{2})(\d{2})(\d{2})(\d{2})[HM][A-Z]{5}[0-9A-Z]\d\b',
    re.IGNORECASE
)
_RFC_PER_RE = re.compile(
    r'\b([A-ZÑ&]{4})(\d{2})(\d{2})(\d{2})[A-Z0-9]{3}\b',
    re.IGNORECASE
)

# Regex patterns para nombres
_NAME_HINTS = [
    r'(?:NOMBRE|NAME|GIVEN\s*NAME)[:\s-]+([A-ZÁÉÍÓÚÑ\s\.]+?)(?:\n|APELLIDO|SURNAME|FECHA|DATE|SEXO)',
    r'(?:APELLIDO|SURNAME)[:\s-]+([A-ZÁÉÍÓÚÑ\s\.]+?)(?:\n|NOMBRE|NAME|FECHA|DATE)',
]


@dataclass
class ExtractedData:
    """Datos extraídos de un documento"""
    name: Optional[str] = None
    id_number: Optional[str] = None
    id_type: Optional[str] = None
    confidence: float = 0.0


def extract_name(text: str) -> Optional[str]:
    """
    Extrae el nombre completo del documento.
    
    Maneja múltiples formatos:
    - APELLIDOS + NOMBRES
    - NOMBRE COMPLETO
    - SURNAME + GIVEN NAME
    
    Args:
        text: Texto OCR del documento
        
    Returns:
        Nombre completo en formato Title Case, o None si no se encuentra
    """
    if not text:
        return None
    
    t = text.upper()
    
    # Diccionario para almacenar partes del nombre
    name_parts = {
        "apellidos": None,
        "nombres": None,
        "segundo_apellido": None
    }
    
    # 1. Intentar capturar nombres y apellidos en pares CLAVE: VALOR
    for line in t.splitlines():
        # Captura Apellidos/Surname
        match_apellido = re.search(
            r'(?:APELLIDOS|SURNAME|APELLIDO)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s\.\-]+)',
            line
        )
        if match_apellido:
            name_parts["apellidos"] = match_apellido.group(1).strip()
        
        # Captura Nombres/Given Names/Nombre Completo
        match_nombre = re.search(
            r'(?:NOMBRES|NAME|GIVEN NAME|NOMBRE|NOMBRE COMPLETO)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s\.\-]+)',
            line
        )
        if match_nombre:
            val = match_nombre.group(1).strip()
            
            # Si es "Nombre Completo", retornar inmediatamente
            if "COMPLETO" in line and len(val.split()) > 2:
                return " ".join(val.split()).title()
            
            # Lógica estándar
            if val not in ["DELA CRUZ", "DE", "LA", "DEL"]:
                name_parts["nombres"] = val
        
        # Captura Segundo Apellido
        match_segundo = re.search(
            r'(?:SEGUNDO APELLIDO|SEGUNDOAPELLIDO)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s\.\-]+)',
            line
        )
        if match_segundo:
            name_parts["segundo_apellido"] = match_segundo.group(1).strip()
    
    # 2. Combinar resultados capturados
    apellidos = name_parts["apellidos"]
    nombres = name_parts["nombres"]
    segundo = name_parts["segundo_apellido"]
    
    # Orden: Apellidos (1 o 2) + Nombres
    apellidos_full = [apellidos] if apellidos else []
    if segundo and segundo != apellidos:
        apellidos_full.append(segundo)
    
    # Unir apellidos y nombres
    final_name_parts = [" ".join(apellidos_full).strip()] if apellidos_full else []
    if nombres:
        final_name_parts.append(nombres)
    
    final_name = " ".join(final_name_parts).strip()
    
    if final_name:
        # Post-limpieza y validación
        clean_name = re.sub(r'\s+', ' ', final_name).strip()
        if len(clean_name.split()) >= 2 and not any(ch.isdigit() for ch in clean_name):
            # Title case con prefijos en minúscula
            title_cased = clean_name.title()
            for p in ["De ", "La ", "Los ", "Las ", "Y "]:
                title_cased = title_cased.replace(p, p.lower())
            return title_cased
    
    # 3. Intento con regex genérico
    for rx in _NAME_HINTS:
        for line in t.splitlines():
            m = re.search(rx, line, flags=re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                if len(m.groups()) > 1 and m.group(2) is not None:
                    cand = cand.replace(m.group(2), '').strip()
                if len(cand.split()) >= 2 and not any(ch.isdigit() for ch in cand):
                    # Limpiar keywords
                    keywords_to_remove = ["DOMICILIO", "DIRECCION", "ADDRESS", "CALLE", "CASA"]
                    for kw in keywords_to_remove:
                        if cand.endswith(kw):
                            cand = cand[:-len(kw)].strip()
                    
                    # Title case
                    title_cased = " ".join(cand.split()).title()
                    for p in ["De ", "La ", "Los ", "Las ", "Y "]:
                        title_cased = title_cased.replace(p, p.lower())
                    return title_cased
    
    return None


def extract_id_number(text: str, country: Optional[str] = None) -> Optional[str]:
    """
    Extrae el número de identificación del documento.
    
    Soporta múltiples formatos por país:
    - MX: CURP, RFC, Clave de Elector
    - GT: CUI/DPI (13 dígitos)
    - US: Driver License Number
    - CO: NUIP (10 dígitos)
    - EC: Cédula (10 dígitos)
    - BR: CPF (11 dígitos), RG
    - BO: CI (7-8 dígitos)
    
    Args:
        text: Texto OCR del documento
        country: Código de país (opcional, mejora la precisión)
        
    Returns:
        Número de ID extraído, o None si no se encuentra
    """
    if not text:
        return None
    
    # Normalizar texto
    t_searchable = text.upper().replace('\n', ' ')
    t_clean = t_searchable.replace(' ', '').replace('-', '')
    
    # Detección específica por país
    
    # Colombia: NUIP (10 dígitos)
    if country == "CO":
        nuip_match = re.search(
            r'(?:NUIP|NUMERO\s*UNICO|IDENTIFICACION\s*PERSONAL)[:\s-]*(\d{10})\b',
            t_searchable
        )
        if nuip_match:
            return nuip_match.group(1)
        nuip_fallback = re.search(r'\b(\d{10})\b', t_clean)
        if nuip_fallback:
            return nuip_fallback.group(1)
    
    # Ecuador: Cédula (10 dígitos)
    if country == "EC":
        nui_match = re.search(
            r'(?:NUI|CEDULA|IDENTIFICACION)[:\s-]*(\d{10})\b',
            t_searchable
        )
        if nui_match:
            return nui_match.group(1)
        nui_fallback = re.search(r'\b(\d{10})\b', t_clean)
        if nui_fallback:
            return nui_fallback.group(1)
    
    # Bolivia: CI (7-8 dígitos)
    if country == "BO":
        bo_match = re.search(
            r'(?:CEDULA|CI|IDENTIDAD)[:\s-]*(\d{7,8}(?:-?\d{1,2})?)\b',
            t_searchable
        )
        if bo_match:
            return bo_match.group(1).replace('-', '')
        bo_fallback = re.search(r'\b(\d{7,8})\b', t_clean)
        if bo_fallback:
            return bo_fallback.group(1)
    
    # Brasil: CPF (11 dígitos) o RG
    if country == "BR":
        cpf_match = re.search(
            r'(?:CPF)[:\s-]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})\b',
            t_searchable
        )
        if cpf_match:
            return cpf_match.group(1).replace('.', '').replace('-', '')
        rg_match = re.search(
            r'(?:RG|REGISTRO\s*GERAL)[:\s-]*(\d{7,9})\b',
            t_searchable
        )
        if rg_match:
            return rg_match.group(1)
        br_fallback = re.search(r'\b(\d{11})\b', t_clean)
        if br_fallback:
            return br_fallback.group(1)
    
    # Keywords genéricos de identificación
    keywords_num = [
        "PASAPORTE N.", "NÚMERO DE PASAPORTE", "PASSPORT NO",
        "NÚMERO DE LICENCIA", "NO. LICENCIA", "NÚMERO DE SERIE",
        "NÚMERO DE MATRÍCULA", "MATRÍCULA CONSULAR",
        "CÓDIGO ÚNICO DE IDENTIFICACIÓN", "CUI",
        "DNI", "DPI", "ID NUMBER", "CLAVE DE ELECTOR",
        "NÚMERO DE IDENTIFICACIÓN", "NÚMERO"
    ]
    
    for kw in keywords_num:
        line_match = re.search(
            f"{kw.replace(' ', ' ?')}\\s*[:\\-]?\\s*([A-Z0-9\\-]+)",
            t_searchable
        )
        
        if line_match:
            val = line_match.group(1).strip()
            clean_val = val.replace(' ', '').replace('-', '')
            
            # DPI/CUI Guatemala (13 dígitos)
            if kw in ["CÓDIGO ÚNICO DE IDENTIFICACIÓN", "CUI"] and re.match(r'^\d{13}$', clean_val):
                return clean_val
            
            # Validar longitud
            if clean_val and len(clean_val) >= 8:
                clean_val_final = re.sub(r'[A-ZÑ]+$', '', clean_val)
                if len(clean_val_final) >= 8:
                    return clean_val_final
    
    # México: CURP, RFC
    if country == "MX":
        curp_match = _CURP_RE.search(t_clean)
        if curp_match:
            return curp_match.group(0)
        rfc_match = _RFC_PER_RE.search(t_clean)
        if rfc_match:
            return rfc_match.group(0)
    
    # Fallback: número largo alfanumérico
    match_long_num = re.search(r'\b([A-Z0-9]{8,25})\b', t_clean)
    if match_long_num:
        num = match_long_num.group(1)
        if not num.isdigit() or len(num) > 8:
            return num
    
    return None


def extract_id_type(text: str, country: Optional[str] = None) -> Optional[str]:
    """
    Extrae el tipo de documento de identificación.
    
    Args:
        text: Texto OCR del documento
        country: Código de país (opcional)
        
    Returns:
        Tipo de documento (ej: "Credencial INE (MX)", "Pasaporte (GT)")
    """
    if not country:
        return None
    
    t = text.lower()
    
    # Por país y tipo específico
    if country == "MX":
        if any(kw in t for kw in ["credencial para votar", "ine"]):
            return "Credencial INE (MX)"
        if "matrícula consular" in t:
            return "Matrícula Consular (MX)"
        if "pasaporte" in t and "mex" in t:
            return "Pasaporte (MX)"
    
    if country == "GT":
        if "documento personal de identificación" in t or "dpi" in t:
            return "DPI (GT)"
        if "identificacion consular" in t:
            return "Identificación Consular (GT)"
        if "pasaporte" in t:
            return "Pasaporte (GT)"
    
    if country == "PH":
        return "Pasaporte (PH)"
    
    if country == "US":
        if any(kw in t for kw in ["driver license", "licencia de conducir"]):
            return "Licencia de Conducir (US)"
    
    # Keywords genéricos
    if "pasaporte" in t or "passport" in t:
        return "Pasaporte"
    if "licencia de conducir" in t or "driver license" in t:
        return "Licencia de Conducir"
    
    return None


def extract_all_data(text: str, country: Optional[str] = None) -> ExtractedData:
    """
    Extrae todos los datos del documento.
    
    Args:
        text: Texto OCR del documento
        country: Código de país (opcional)
        
    Returns:
        ExtractedData con nombre, ID y tipo de documento
    """
    name = extract_name(text)
    id_number = extract_id_number(text, country)
    id_type = extract_id_type(text, country)
    
    # Calcular confianza
    confidence = 0.0
    if name:
        confidence += 0.4
    if id_number:
        confidence += 0.4
    if id_type:
        confidence += 0.2
    
    return ExtractedData(
        name=name,
        id_number=id_number,
        id_type=id_type,
        confidence=confidence
    )
