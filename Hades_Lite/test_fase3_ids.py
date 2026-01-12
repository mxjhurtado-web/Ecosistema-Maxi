# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la deteccion de IDs en HadesLite 2.2
Fase 3: Pruebas de deteccion de numeros de identificacion
"""

import re
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def _extract_id_number_test(texto: str, doc_pais: str | None) -> str | None:
    """Version simplificada de _extract_id_number para pruebas"""
    if not texto: return None
    
    t_searchable = texto.upper().replace('\n', ' ')
    t_clean = t_searchable.replace(' ', '').replace('-', '')
    
    # Colombia: NUIP (10 digitos)
    if doc_pais == "CO":
        nuip_match = re.search(r'(?:NUIP|NUMERO\s*UNICO|IDENTIFICACION\s*PERSONAL)[:\s-]*(\d{10})\b', t_searchable)
        if nuip_match:
            return nuip_match.group(1)
        nuip_fallback = re.search(r'\b(\d{10})\b', t_clean)
        if nuip_fallback:
            return nuip_fallback.group(1)
    
    # Ecuador: NUI/Cedula (10 digitos)
    if doc_pais == "EC":
        nui_match = re.search(r'(?:NUI|CEDULA|IDENTIFICACION)[:\s-]*(\d{10})\b', t_searchable)
        if nui_match:
            return nui_match.group(1)
        nui_fallback = re.search(r'\b(\d{10})\b', t_clean)
        if nui_fallback:
            return nui_fallback.group(1)
    
    # Bolivia: Cedula de Identidad (7-8 digitos)
    if doc_pais == "BO":
        bo_match = re.search(r'(?:CEDULA|CI|IDENTIDAD)[:\s-]*(\d{7,8}(?:-?\d{1,2})?)\b', t_searchable)
        if bo_match:
            return bo_match.group(1).replace('-', '')
        bo_fallback = re.search(r'\b(\d{7,8})\b', t_clean)
        if bo_fallback:
            return bo_fallback.group(1)
    
    # Brasil: CPF (11 digitos) o RG (7-9 digitos)
    if doc_pais == "BR":
        cpf_match = re.search(r'(?:CPF)[:\s-]*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})\b', t_searchable)
        if cpf_match:
            return cpf_match.group(1).replace('.', '').replace('-', '')
        rg_match = re.search(r'(?:RG|REGISTRO\s*GERAL)[:\s-]*(\d{7,9})\b', t_searchable)
        if rg_match:
            return rg_match.group(1)
        br_fallback = re.search(r'\b(\d{11})\b', t_clean)
        if br_fallback:
            return br_fallback.group(1)
        br_rg_fallback = re.search(r'\b(\d{7,9})\b', t_clean)
        if br_rg_fallback:
            return br_rg_fallback.group(1)
    
    return None

# Casos de prueba
test_cases = [
    # Colombia - NUIP (10 digitos)
    ("NUIP: 1234567890", "CO", "1234567890", "Colombia NUIP con keyword"),
    ("NUMERO UNICO: 9876543210", "CO", "9876543210", "Colombia NUIP con texto completo"),
    ("1234567890", "CO", "1234567890", "Colombia NUIP sin keyword"),
    
    # Ecuador - NUI (10 digitos)
    ("NUI: 1234567890", "EC", "1234567890", "Ecuador NUI con keyword"),
    ("CEDULA: 9876543210", "EC", "9876543210", "Ecuador Cedula con keyword"),
    ("1234567890", "EC", "1234567890", "Ecuador NUI sin keyword"),
    
    # Bolivia - Cedula (7-8 digitos)
    ("CEDULA: 12345678", "BO", "12345678", "Bolivia Cedula 8 digitos"),
    ("CI: 1234567", "BO", "1234567", "Bolivia CI 7 digitos"),
    ("12345678", "BO", "12345678", "Bolivia sin keyword"),
    
    # Brasil - CPF/RG
    ("CPF: 123.456.789-01", "BR", "12345678901", "Brasil CPF con formato"),
    ("CPF: 12345678901", "BR", "12345678901", "Brasil CPF sin formato"),
    ("RG: 12345678", "BR", "12345678", "Brasil RG"),
    ("12345678901", "BR", "12345678901", "Brasil CPF sin keyword"),
]

print("=" * 80)
print("PRUEBAS DE DETECCION DE IDs - FASE 3")
print("=" * 80)

exitos = 0
fallos = 0

for texto, pais, esperado, descripcion in test_cases:
    print(f"\nProbando: {descripcion}")
    print(f"Texto: '{texto}' | Pais: {pais}")
    print(f"Esperado: {esperado}")
    
    resultado = _extract_id_number_test(texto, pais)
    
    if resultado == esperado:
        print(f"EXITO: {resultado}")
        exitos += 1
    elif resultado:
        print(f"ERROR: Obtenido '{resultado}' (esperado '{esperado}')")
        fallos += 1
    else:
        print(f"ERROR: No se detecto ningun ID")
        fallos += 1

print("\n" + "=" * 80)
print(f"RESUMEN: {exitos} exitos, {fallos} fallos de {len(test_cases)} pruebas")
print("=" * 80)
