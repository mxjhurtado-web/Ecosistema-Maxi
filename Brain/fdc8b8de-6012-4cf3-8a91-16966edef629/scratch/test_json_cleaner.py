import re
import json

def parse_gemini_json_robust(raw_text: str) -> dict:
    """
    Parsea de forma ultra-robusta la respuesta JSON de Gemini.
    1. Intenta usar json.loads con strict=False.
    2. Si falla (por comillas dobles o backslashes inválidos), usa regex
       para extraer cada campo directamente de la cadena de texto plano.
    """
    text = raw_text.strip()
    
    # Limpieza de Markdown
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n", "", text)
        text = re.sub(r"\n\s*```$", "", text)
        text = text.strip()
        
    try:
        # Intento 1: Standard JSON parser
        return json.loads(text, strict=False)
    except Exception as e:
        print(f"Standard json.loads failed: {e}. Running robust regex extractor...")
        
    # Intento 2: Extractor por Expresiones Regulares para campos individuales
    data = {}
    
    # Helper para limpiar escapes en las cadenas extraídas
    def clean_extracted_value(val: str) -> str:
        # Reemplazar escapes de nueva línea comunes
        val = val.replace("\\n", "\n").replace("\\t", "\t")
        # Quitar escapes de comillas
        val = val.replace('\\"', '"')
        return val.strip()

    # 1. Extraer campos de texto simples
    text_fields = [
        "extracted_ocr",
        "document_country",
        "document_type",
        "extracted_name",
        "id_number",
        "expiration_date",
        "birth_date",
        "issue_date",
        "forensic_analysis_summary"
    ]
    
    for field in text_fields:
        # Buscar el campo capturando todo el valor string hasta la siguiente llave del esquema
        pattern = rf'"{field}"\s*:\s*"(.*?)"\s*(?:,\s*"|,\s*\n\s*"|\s*}})'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            raw_val = match.group(1)
            data[field] = clean_extracted_value(raw_val)
        else:
            data[field] = ""
            
    # 2. Extraer campo booleano photoshop_detected
    photo_match = re.search(r'"photoshop_detected"\s*:\s*(true|false)', text, re.IGNORECASE)
    if photo_match:
        data["photoshop_detected"] = photo_match.group(1).lower() == "true"
    else:
        data["photoshop_detected"] = False
        
    # 3. Extraer puntuaciones (scores)
    scores = {}
    score_fields = [
        "security_elements",
        "printing_quality",
        "digital_manipulation",
        "typography",
        "photography"
    ]
    for score_field in score_fields:
        score_match = re.search(rf'"{score_field}"\s*:\s*(\d+)', text)
        if score_match:
            scores[score_field] = int(score_match.group(1))
        else:
            scores[score_field] = 0
    data["scores"] = scores
    
    # 4. Extraer evidencias (evidences)
    evidences = []
    # Buscar el bloque de evidences: "evidences" : [ ... ]
    ev_match = re.search(r'"evidences"\s*:\s*\[(.*?)\]', text, re.DOTALL)
    if ev_match:
        ev_block = ev_match.group(1).strip()
        # Separar por comas seguidas de salto de línea, o simplemente por nueva línea
        raw_items = re.split(r',\s*\n\s*', ev_block)
        for item in raw_items:
            item = item.strip()
            # Limpiar comillas exteriores
            if item.startswith('"'):
                item = item[1:]
            if item.endswith(','):
                item = item[:-1].strip()
            if item.endswith('"'):
                item = item[:-1]
                
            clean_ev = clean_extracted_value(item).strip()
            if clean_ev:
                evidences.append(clean_ev)
    data["evidences"] = evidences
    
    return data

# Test unitario con evidencias complejas
test_input = """{
  "extracted_ocr": "ARIZONA \\nIdentification Card\\nNumber D04774185\\nExpires \\nDate of Birth 11/05/1988\\nIssued 03/03/2013\\nANTONIO "EL GRANDE" AGUILAR",
  "document_country": "US",
  "document_type": "Tarjeta de Identificación "State ID"",
  "extracted_name": "ANTONIO "EL GRANDE" AGUILAR",
  "id_number": "D04774185",
  "expiration_date": "",
  "birth_date": "11/05/1988",
  "issue_date": "03/03/2013",
  "forensic_analysis_summary": "El documento tiene la firma "Antonio" y es válido.",
  "photoshop_detected": false,
  "scores": {
    "security_elements": 8,
    "printing_quality": 2,
    "digital_manipulation": 1,
    "typography": 1,
    "photography": 1
  },
  "evidences": [
    "Evidencia con "comillas" internas",
    "Otra evidencia"
  ]
}"""

print("Running robust parser test...")
data = parse_gemini_json_robust(test_input)
print("Parsed Successfully:")
print("evidences:", data["evidences"])
