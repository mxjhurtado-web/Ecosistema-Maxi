"""
Módulo de detección de país para documentos.

Copiado de Hades Ultimate sin cambios.
"""

from typing import Optional

# Diccionario de pistas por país (copiado de Hades Ultimate)
COUNTRY_CUES = {
    "GT": ["guatemala", "guatemalteca", "republica de guatemala", "identificacion consular", 
           "documento personal de identificación", "pasaporte guatemala", "país emisor: gtm", 
           "registro nacional de las personas"],
    "PH": ["pasaporte", "republic of the philippines", "republika ng pilipinas", 
           "código de país: phl", "filipino"],
    "MX": ["ine", "instituto nacional electoral", "credencial para votar", "clave de elector", 
           "curp", "rfc", "licencia de conducir", "pasaporte", "matrícula consular", 
           "estados unidos mexicanos", "clave del país de expedición: mex"],
    "HN": ["registro nacional de las personas", "pasaporte", "honduras"],
    "CO": ["cédula de ciudadanía", "cedula de ciudadania", "pasaporte", "republica de colombia"],
    "PE": ["dni", "documento nacional de identidad", "pasaporte", "peru", "república del perú"],
    "NI": ["consejo supremo electoral", "pasaporte", "nicaragua"],
    "SV": ["documento único de identidad", "dui", "pasaporte", "el salvador"],
    "EC": ["cédula de ciudadanía", "pasaporte", "ecuador"],
    "DO": ["república dominicana", "pasaporte"],
    "VE": ["matrícula consular", "venezuela"],
    "US": ["united states", "usa", "state of", "driver license", "dl class", "id card", 
           "department of motor vehicles", "dmv", "ssn", "uscis", "passport of the united states"],
    "ES": ["dni", "nif", "número de soporte", "ministerio del interior", "reino de españa", 
           "pasaporte español"],
    "AR": ["dni", "registro nacional de las personas", "república argentina", "republica argentina"],
    "BR": ["cpf", "rg", "carteira de identidade", "carteira nacional de habilitação", "cnh", 
           "registro geral", "documento de identidade", "passaporte", "república federativa do brasil"],
    "CL": ["rut", "rol único tributario", "cédula de identidad", "pasaporte", "república de chile"],
    "PY": ["cédula de identidad civil", "pasaporte", "república del paraguay"],
    "UY": ["cédula de identidad", "documento de identidad", "pasaporte", 
           "república oriental del uruguay"],
    "BO": ["cédula de identidad", "pasaporte", "estado plurinacional de bolivia"],
    "CR": ["cédula de identidad", "documento de identidad", "pasaporte", "república de costa rica"],
    "PA": ["cédula de identidad personal", "pasaporte", "república de panamá"],
    "CU": ["carné de identidad", "pasaporte", "república de cuba"],
    "HT": ["carte d'identité nationale", "pasaporte", "république d'haïti"],
    "JM": ["national id", "electoral id", "passport", "jamaica"],
    "TT": ["national id card", "passport", "trinidad and tobago"],
    "PK": ["cnic", "computerized national identity card", "national identity card", "passport",
           "tarjeta de identidad nacional", "pakistan"],
    "IL": ["teudat zehut", "תעודת זהות", "israeli id", "passport", "state of israel", "מדינת ישראל"],
    "VN": ["căn cước công dân", "chứng minh nhân dân", "giấy chứng minh nhân dân",
           "giấy tờ tùy thân", "hộ chiếu", "social insurance book", "republic of vietnam", "vietnam"],
}


def detect_country(text: str) -> Optional[str]:
    """
    Detecta el país de origen de un documento basándose en palabras clave.
    
    Args:
        text: Texto OCR del documento
        
    Returns:
        Código de país de 2 letras (ej: "US", "MX") o None si no se detecta
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    for country_code, cues in COUNTRY_CUES.items():
        if any(cue in text_lower for cue in cues):
            return country_code
    
    return None


def get_country_name(country_code: str) -> str:
    """
    Obtiene el nombre completo del país a partir del código.
    
    Args:
        country_code: Código de país de 2 letras
        
    Returns:
        Nombre del país en español
    """
    country_names = {
        "GT": "Guatemala",
        "PH": "Filipinas",
        "MX": "México",
        "HN": "Honduras",
        "CO": "Colombia",
        "PE": "Perú",
        "NI": "Nicaragua",
        "SV": "El Salvador",
        "EC": "Ecuador",
        "DO": "República Dominicana",
        "VE": "Venezuela",
        "US": "Estados Unidos",
        "ES": "España",
        "AR": "Argentina",
        "BR": "Brasil",
        "CL": "Chile",
        "PY": "Paraguay",
        "UY": "Uruguay",
        "BO": "Bolivia",
        "CR": "Costa Rica",
        "PA": "Panamá",
        "CU": "Cuba",
        "HT": "Haití",
        "JM": "Jamaica",
        "TT": "Trinidad y Tobago",
        "PK": "Pakistán",
        "IL": "Israel",
        "VN": "Vietnam",
    }
    
    return country_names.get(country_code, country_code)
