import sys

# Function under test (copied from ATHENAS_LiteRG_v3.2.1.py)
def _atributos_a_columnas_valor(det_atrib):
    """
    Convierte detalle por atributo en columnas:
      - "Cumplido <key>" = valor 'otorgado' (int o 0/'' si falta)
      - Si estado es "NA", pone "NA=<valor>"
    Retorna: (dict_columnas, set_base_keys)
    Formato esperado en det_atrib:
      {'key': 'tiempo_respuesta', 'estado': 'OK|NO|NA', 'peso': 4, 'otorgado': 4}
    """
    fila = {}
    base_keys = set()
    for d in det_atrib or []:
        key = (d.get("key") or "").strip()
        if not key:
            continue
        col = f"Cumplido {key}"
        
        otorg = d.get("otorgado")
        if otorg is None:
            otorg = d.get("ganado", 0)
        
        estado = d.get("estado", "")

        # Lógica de formateo
        if estado == "NA":
            # Caso solicitado: NA=VALOR
            val_final = f"NA={otorg}"
        else:
            # Caso normal: entero
            try:
                val_final = int(otorg)
            except Exception:
                val_final = 0

        fila[col] = val_final
        base_keys.add(key)
    return fila, base_keys

def test_na_logic():
    print("Testing NA logic...")
    
    test_cases = [
        {
            "name": "OK Item",
            "input": [{'key': 'test_ok', 'estado': 'OK', 'peso': 5, 'otorgado': 5}],
            "expected": {'Cumplido test_ok': 5}
        },
        {
            "name": "NO Item",
            "input": [{'key': 'test_no', 'estado': 'NO', 'peso': 5, 'otorgado': 0}],
            "expected": {'Cumplido test_no': 0}
        },
        {
            "name": "NA Item",
            "input": [{'key': 'test_na', 'estado': 'NA', 'peso': 5, 'otorgado': 5}],
            "expected": {'Cumplido test_na': 'NA=5'}
        },
        {
             "name": "Mixed Items",
             "input": [
                 {'key': 'item1', 'estado': 'OK', 'peso': 10, 'otorgado': 10},
                 {'key': 'item2', 'estado': 'NA', 'peso': 5, 'otorgado': 5}
             ],
             "expected": {'Cumplido item1': 10, 'Cumplido item2': 'NA=5'}
        }
    ]

    all_passed = True
    for case in test_cases:
        result, _ = _atributos_a_columnas_valor(case["input"])
        if result == case["expected"]:
            print(f"PASS: {case['name']}")
        else:
            print(f"FAIL: {case['name']}")
            print(f"  Expected: {case['expected']}")
            print(f"  Got:      {result}")
            all_passed = False
            
    if all_passed:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed.")

if __name__ == "__main__":
    test_na_logic()
