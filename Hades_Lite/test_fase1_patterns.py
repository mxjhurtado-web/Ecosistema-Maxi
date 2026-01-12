# -*- coding: utf-8 -*-
"""
Script de prueba para verificar los nuevos patrones de fecha en HadesLite 2.2
Fase 1: Pruebas de los nuevos regex patterns
"""

import re
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Copiar los diccionarios y patrones del codigo principal
_MONTHS_ES = {
    # Nombres completos
    "enero":1, "febrero":2, "marzo":3, "abril":4, "mayo":5, "junio":6,
    "julio":7, "agosto":8, "septiembre":9, "setiembre":9, "octubre":10, "noviembre":11, "diciembre":12,
    # Abreviaciones de 3 letras
    "ene":1, "feb":2, "mar":3, "abr":4, "may":5, "jun":6,
    "jul":7, "ago":8, "sep":9, "oct":10, "nov":11, "dic":12
}

# Nuevos patrones
_DATE_RE_MM_YYYY = re.compile(r'\b(\d{1,2})/(\d{4})\b')
_DATE_RE_DD_MM_YYYY_DOT = re.compile(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b')
_DATE_RE_TXT_ES_FULL = re.compile(r'\b(\d{1,2})[-\s]+([a-z]+)[-\s]+(\d{2,4})\b', re.IGNORECASE)

def _coerce_year(y: int) -> int:
    if y < 100: return 2000 + y if y < 50 else 1900 + y
    return y

# Casos de prueba basados en el documento
test_cases = [
    # MM/YYYY (Venezuela)
    ("03/2027", "MM/YYYY", "03/01/2027"),
    
    # DD.MM.YYYY (Costa Rica)
    ("30.10.2000", "DD.MM.YYYY", "10/30/2000"),
    ("18.10.2030", "DD.MM.YYYY", "10/18/2030"),
    
    # Fechas textuales en espanol con guiones (Panama)
    ("31-ago-2027", "DD-MES-YYYY", "08/31/2027"),
    
    # Fechas textuales en espanol con espacios (Republica Dominicana, Chile)
    ("15 agosto 1994", "DD MES YYYY", "08/15/1994"),
    ("15 mayo 2034", "DD MES YYYY", "05/15/2034"),
    
    # Brasil
    ("16 MAR 2004", "DD MES YYYY", "03/16/2004"),
]

print("=" * 80)
print("PRUEBAS DE NUEVOS PATRONES REGEX - FASE 1")
print("=" * 80)

exitos = 0
fallos = 0

for fecha_original, formato, esperado in test_cases:
    print(f"\nProbando: '{fecha_original}' (Formato: {formato})")
    print(f"Esperado: {esperado}")
    
    resultado = None
    
    # Probar MM/YYYY
    m = _DATE_RE_MM_YYYY.search(fecha_original)
    if m:
        mm, y = m.groups()
        mm_int = int(mm)
        if 1 <= mm_int <= 12:
            resultado = f"{mm_int:02d}/01/{int(y):04d}"
            print(f"Detectado por _DATE_RE_MM_YYYY: {resultado}")
    
    # Probar DD.MM.YYYY
    if not resultado:
        m = _DATE_RE_DD_MM_YYYY_DOT.search(fecha_original)
        if m:
            d, mm, y = m.groups()
            try:
                d_int, mm_int, y_int = int(d), int(mm), int(y)
                if 1 <= d_int <= 31 and 1 <= mm_int <= 12:
                    resultado = f"{mm_int:02d}/{d_int:02d}/{y_int:04d}"
                    print(f"Detectado por _DATE_RE_DD_MM_YYYY_DOT: {resultado}")
            except ValueError:
                pass
    
    # Probar fechas textuales en espanol
    if not resultado:
        m = _DATE_RE_TXT_ES_FULL.search(fecha_original)
        if m:
            da, mon, y = m.groups()
            mo = _MONTHS_ES.get(mon.lower())
            if mo:
                resultado = f"{int(mo):02d}/{int(da):02d}/{_coerce_year(int(y)):04d}"
                print(f"Detectado por _DATE_RE_TXT_ES_FULL: {resultado}")
    
    # Verificar resultado
    if resultado == esperado:
        print(f"EXITO: Resultado correcto")
        exitos += 1
    elif resultado:
        print(f"ERROR: Resultado incorrecto (obtenido: {resultado})")
        fallos += 1
    else:
        print(f"ERROR: No se detecto ningun patron")
        fallos += 1

print("\n" + "=" * 80)
print(f"RESUMEN: {exitos} exitos, {fallos} fallos de {len(test_cases)} pruebas")
print("=" * 80)
