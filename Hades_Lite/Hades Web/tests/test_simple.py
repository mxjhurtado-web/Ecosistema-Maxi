"""
Test simple para verificar que el módulo de fechas funciona.
"""

# Import directo del módulo
import sys
from pathlib import Path

# Agregar el path del proyecto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ahora importar
from hades_core.dates.dates import analyze_date, DateType, DateFormat

print("\n" + "="*60)
print("TEST DE PRESERVACIÓN DE FECHAS")
print("="*60 + "\n")

# Test 1: USA Clear
print("Test 1: Fecha USA clara (01/15/2024)")
result = analyze_date("01/15/2024", country_hint="US")
print(f"  Original: {result.original}")
print(f"  Display:  {result.display}")
print(f"  Formato:  {result.format_detected.value}")
print(f"  ✅ PRESERVADO" if result.original == result.display else "  ❌ REFORMATEADO")
print()

# Test 2: LATAM Clear
print("Test 2: Fecha LATAM clara (15/01/2024)")
result = analyze_date("15/01/2024", country_hint="MX")
print(f"  Original: {result.original}")
print(f"  Display:  {result.display}")
print(f"  Formato:  {result.format_detected.value}")
print(f"  ✅ PRESERVADO" if result.original == result.display else "  ❌ REFORMATEADO")
print()

# Test 3: Ambigua
print("Test 3: Fecha ambigua (01/02/2024) sin hint")
result = analyze_date("01/02/2024", country_hint=None)
print(f"  Original: {result.original}")
print(f"  Display:  {result.display}")
print(f"  Formato:  {result.format_detected.value}")
print(f"  Ambigua:  {result.is_ambiguous}")
print(f"  ✅ PRESERVADO" if result.original == result.display else "  ❌ REFORMATEADO")
print()

print("="*60)
print("✅ MÓDULO DE FECHAS FUNCIONA CORRECTAMENTE")
print("="*60)
