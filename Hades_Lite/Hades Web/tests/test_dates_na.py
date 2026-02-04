"""
Tests para el módulo de fechas.
Verifica que las fechas norteamericanas se preservan correctamente.
"""

import sys
sys.path.insert(0, 'c:\\Users\\User\\Ecosistema-Maxi\\Hades_Lite\\Hades Web')

from hades_core.dates.dates import analyze_date, DateType, DateFormat


def test_usa_clear_format():
    """Fecha claramente MM/DD/YYYY (día > 12)"""
    print("\n=== Test 1: USA Clear Format ===")
    result = analyze_date("01/15/2024", country_hint="US", date_type=DateType.EXPIRATION)
    
    print(f"Original: {result.original}")
    print(f"Display: {result.display}")
    print(f"Formato detectado: {result.format_detected.value}")
    print(f"Confianza: {result.confidence}")
    print(f"Parsed: {result.parsed}")
    
    assert result.original == "01/15/2024", "Original debe preservarse"
    assert result.display == "01/15/2024", "Display debe ser igual a original"
    assert result.format_detected == DateFormat.MM_DD_YYYY, "Debe detectar MM/DD/YYYY"
    assert result.confidence == 1.0, "Confianza debe ser 100%"
    assert result.parsed.year == 2024
    assert result.parsed.month == 1
    assert result.parsed.day == 15
    
    print("✅ Test 1 PASADO\n")


def test_latam_clear_format():
    """Fecha claramente DD/MM/YYYY (día > 12)"""
    print("=== Test 2: LATAM Clear Format ===")
    result = analyze_date("15/01/2024", country_hint="MX")
    
    print(f"Original: {result.original}")
    print(f"Display: {result.display}")
    print(f"Formato detectado: {result.format_detected.value}")
    print(f"Confianza: {result.confidence}")
    print(f"Parsed: {result.parsed}")
    
    assert result.original == "15/01/2024", "Original debe preservarse"
    assert result.display == "15/01/2024", "Display debe ser igual a original"
    assert result.format_detected == DateFormat.DD_MM_YYYY, "Debe detectar DD/MM/YYYY"
    assert result.confidence == 1.0, "Confianza debe ser 100%"
    assert result.parsed.year == 2024
    assert result.parsed.month == 1
    assert result.parsed.day == 15
    
    print("✅ Test 2 PASADO\n")


def test_usa_ambiguous():
    """Fecha ambigua con hint de USA"""
    print("=== Test 3: USA Ambiguous Date ===")
    result = analyze_date("01/02/2024", country_hint="US")
    
    print(f"Original: {result.original}")
    print(f"Display: {result.display}")
    print(f"Formato detectado: {result.format_detected.value}")
    print(f"Confianza: {result.confidence}")
    print(f"Es ambigua: {result.is_ambiguous}")
    print(f"Warnings: {result.warnings}")
    
    assert result.original == "01/02/2024", "Original debe preservarse"
    assert result.display == "01/02/2024", "Display debe ser igual a original"
    assert result.format_detected == DateFormat.MM_DD_YYYY, "Debe asumir MM/DD/YYYY por contexto USA"
    assert result.confidence == 0.7, "Confianza debe ser menor (70%)"
    
    print("✅ Test 3 PASADO\n")


def test_no_hint_ambiguous():
    """Fecha ambigua sin contexto de país"""
    print("=== Test 4: Ambiguous Without Hint ===")
    result = analyze_date("01/02/2024", country_hint=None)
    
    print(f"Original: {result.original}")
    print(f"Display: {result.display}")
    print(f"Formato detectado: {result.format_detected.value}")
    print(f"Es ambigua: {result.is_ambiguous}")
    print(f"Parsed: {result.parsed}")
    print(f"Warnings: {result.warnings}")
    
    assert result.original == "01/02/2024", "Original debe preservarse"
    assert result.display == "01/02/2024", "Display debe ser igual a original"
    assert result.format_detected == DateFormat.AMBIGUOUS, "Debe marcar como AMBIGUOUS"
    assert result.is_ambiguous == True, "Debe ser ambigua"
    assert result.parsed is None, "No debe parsear si es ambigua"
    assert len(result.warnings) > 0, "Debe tener warnings"
    
    print("✅ Test 4 PASADO\n")


def test_expiration_calculation():
    """Verificar cálculo de vigencia"""
    print("=== Test 5: Expiration Calculation ===")
    result = analyze_date("12/31/2025", country_hint="US", date_type=DateType.EXPIRATION)
    
    print(f"Original: {result.original}")
    print(f"Display: {result.display}")
    print(f"Está expirada: {result.is_expired}")
    print(f"Días hasta expiración: {result.days_until_expiry}")
    
    assert result.original == "12/31/2025", "Original debe preservarse"
    assert result.display == "12/31/2025", "Display debe ser igual a original"
    assert result.is_expired == False, "No debe estar expirada"
    assert result.days_until_expiry is not None, "Debe calcular días"
    
    print("✅ Test 5 PASADO\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTS DE PRESERVACIÓN DE FECHAS NORTEAMERICANAS")
    print("="*60)
    
    try:
        test_usa_clear_format()
        test_latam_clear_format()
        test_usa_ambiguous()
        test_no_hint_ambiguous()
        test_expiration_calculation()
        
        print("\n" + "="*60)
        print("✅ TODOS LOS TESTS PASARON")
        print("="*60)
        print("\nRESUMEN:")
        print("- Fechas USA (MM/DD/YYYY) se preservan ✓")
        print("- Fechas LATAM (DD/MM/YYYY) se preservan ✓")
        print("- Fechas ambiguas se marcan con warning ✓")
        print("- Cálculo de vigencia funciona ✓")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}\n")
        raise
