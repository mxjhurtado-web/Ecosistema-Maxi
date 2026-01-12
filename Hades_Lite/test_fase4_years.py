# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la conversion de años en HadesLite 2.2
Fase 4: Pruebas de _coerce_year() aplicado consistentemente
"""

import re
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def _coerce_year(y: int) -> int:
    """Convierte años de 2 digitos a 4 digitos"""
    if y < 100: return 2000 + y if y < 50 else 1900 + y
    return y

# Patrones de fecha (actualizados para aceptar años de 2-4 digitos)
_DATE_RE_NUM_A = re.compile(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b')
_DATE_RE_DMY_H = re.compile(r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b')
_DATE_RE_DD_MM_YYYY_SPACE = re.compile(r'\b(\d{1,2})\s+(\d{1,2})\s+(\d{2,4})\b')

def test_normalize_date(s: str, expected: str, description: str):
    """Prueba la normalizacion de una fecha"""
    print(f"\nProbando: {description}")
    print(f"Entrada: '{s}'")
    print(f"Esperado: {expected}")
    
    result = None
    
    # Probar patron numerico ambiguo (MM/DD/YY o DD/MM/YY)
    m = _DATE_RE_NUM_A.search(s)
    if m:
        a, b, y = m.groups()
        a = int(a); b = int(b); y = _coerce_year(int(y))
        # Asumir formato MM/DD/YY para USA
        month, day = a, b
        result = f"{int(month):02d}/{int(day):02d}/{y:04d}"
        print(f"Detectado por _DATE_RE_NUM_A: {result}")
    
    # Probar patron DD-MM-YYYY
    if not result:
        m = _DATE_RE_DMY_H.search(s)
        if m:
            da, mo, y = list(map(int, m.groups()))
            y = _coerce_year(y)
            result = f"{mo:02d}/{da:02d}/{y:04d}"
            print(f"Detectado por _DATE_RE_DMY_H: {result}")
    
    # Probar patron DD MM YYYY (espacios)
    if not result:
        m = _DATE_RE_DD_MM_YYYY_SPACE.search(s)
        if m:
            d, m_, y = m.groups()
            try:
                d_int, m_int, y_int = int(d), int(m_), int(y)
                y_int = _coerce_year(y_int)
                result = f"{m_int:02d}/{d_int:02d}/{y_int:04d}"
                print(f"Detectado por _DATE_RE_DD_MM_YYYY_SPACE: {result}")
            except ValueError:
                pass
    
    # Verificar resultado
    if result == expected:
        print(f"EXITO: Resultado correcto")
        return True
    elif result:
        print(f"ERROR: Resultado incorrecto (obtenido: {result})")
        return False
    else:
        print(f"ERROR: No se detecto ningun patron")
        return False

# Casos de prueba
test_cases = [
    # I-766 (USA) - Formato MM/DD/YY
    ("02/27/29", "02/27/2029", "I-766 USA - MM/DD/YY con año de 2 digitos"),
    ("12/31/99", "12/31/1999", "Año 99 debe ser 1999"),
    ("01/01/50", "01/01/1950", "Año 50 debe ser 1950"),
    ("01/01/49", "01/01/2049", "Año 49 debe ser 2049"),
    
    # Formatos con guiones
    ("15-08-94", "08/15/1994", "DD-MM-YY con guiones (año 94)"),
    ("01-11-69", "11/01/1969", "DD-MM-YY con guiones (año 69)"),
    
    # Formatos con espacios
    ("22 03 32", "03/22/2032", "DD MM YY con espacios (año 32)"),
    ("18 06 22", "06/18/2022", "DD MM YY con espacios (año 22)"),
]

print("=" * 80)
print("PRUEBAS DE CONVERSION DE AÑOS - FASE 4")
print("=" * 80)

exitos = 0
fallos = 0

for fecha, esperado, descripcion in test_cases:
    if test_normalize_date(fecha, esperado, descripcion):
        exitos += 1
    else:
        fallos += 1

print("\n" + "=" * 80)
print(f"RESUMEN: {exitos} exitos, {fallos} fallos de {len(test_cases)} pruebas")
print("=" * 80)
