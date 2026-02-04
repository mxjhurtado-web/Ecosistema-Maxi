# Hades Core - Motor de Análisis

Motor de análisis forense de documentos extraído de Hades Ultimate.

## 📦 Módulos

### `analyzer.py`
Módulo principal que integra todos los componentes.

```python
from hades_core import analyze_image

# Analizar una imagen
with open("license.jpg", "rb") as f:
    image_bytes = f.read()

result = analyze_image(image_bytes, gemini_api_key="tu_api_key")

print(f"País: {result.country_name}")
print(f"Semáforo: {result.semaforo.value}")
print(f"Fecha de vencimiento: {result.dates['expiration'].display}")
```

### `dates/`
Detección y procesamiento de fechas **CON PRESERVACIÓN**.

```python
from hades_core.dates.dates import analyze_date, DateType

# Analizar una fecha
date_info = analyze_date("01/15/2024", country_hint="US", date_type=DateType.EXPIRATION)

print(date_info.original)   # "01/15/2024" ← SIN CAMBIOS
print(date_info.display)    # "01/15/2024" ← SIN CAMBIOS
print(date_info.parsed)     # datetime(2024, 1, 15) ← Para validaciones
```

**CAMBIO CLAVE vs Hades Ultimate:**
- ✅ `original` y `display` NUNCA se modifican
- ✅ `parsed` solo se usa para validaciones internas
- ✅ Fechas norteamericanas (MM/DD/YYYY) se preservan

### `country.py`
Detección de país del documento.

```python
from hades_core.country import detect_country, get_country_name

country_code = detect_country("INSTITUTO NACIONAL ELECTORAL")
print(country_code)  # "MX"
print(get_country_name(country_code))  # "México"
```

### `ocr.py`
OCR usando Google Gemini Vision.

```python
from hades_core.ocr import extract_text_from_image

text, metadata = extract_text_from_image(image_bytes, api_key="tu_api_key")
print(text)  # Texto extraído del documento
```

### `forensics.py`
Análisis forense de autenticidad.

```python
from hades_core.forensics import analyze_document_authenticity

result = analyze_document_authenticity(ocr_text, image_bytes)
print(result.semaforo.value)  # "verde", "amarillo", "rojo"
print(result.score)  # 0-100
```

## 🔧 Instalación

```bash
cd hades_core
pip install -r requirements.txt
```

## 🧪 Tests

```bash
# Test de fechas
python ../tests/test_simple.py

# Test de integración
python ../tests/test_integration.py
```

## ✅ Cambios vs Hades Ultimate

### Mantenido (Sin Cambios)
- ✅ Sistema de semáforo (verde/amarillo/rojo)
- ✅ Detección de país
- ✅ Extracción de IDs
- ✅ Prompts de Gemini
- ✅ Lógica de análisis forense

### Modificado
- 🔧 **Fechas:** Ahora se preserva el formato original del OCR
  - Antes: `"01/15/2024"` → `"15/01/2024"` (reformateado)
  - Ahora: `"01/15/2024"` → `"01/15/2024"` (preservado)

## 📊 Estructura de Resultado

```python
{
    "ocr_text": "...",
    "country": {
        "code": "US",
        "name": "Estados Unidos"
    },
    "dates": {
        "birth": {
            "original": "01/15/1990",
            "display": "01/15/1990",
            "format": "MM/DD/YYYY",
            "confidence": 1.0,
            "is_valid": true,
            "is_ambiguous": false
        },
        "expiration": {
            "original": "12/31/2025",
            "display": "12/31/2025",
            "format": "MM/DD/YYYY",
            "is_expired": false,
            "days_until_expiry": 365
        }
    },
    "forensics": {
        "score": 5,
        "semaforo": "verde",
        "details": [...],
        "warnings": []
    }
}
```

## 🚀 Próximos Pasos

- [ ] Expandir análisis forense con Gemini Vision
- [ ] Agregar extracción de IDs
- [ ] Agregar extracción de nombres
- [ ] Implementar CLI de prueba
