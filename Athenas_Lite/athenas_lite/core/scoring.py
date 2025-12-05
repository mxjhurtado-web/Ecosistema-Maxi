
from .rules_engine import KEYS_ADMINISTRATIVAS

def aplicar_defaults_items(eval_data: dict) -> dict:
    for sec in (eval_data.get("sections") or []):
        for it in (sec.get("items") or []):
            # 1. Defaults básicos ante vacíos
            if "ok" not in it:
                it["ok"] = False
            if "peso" not in it:
                it["peso"] = 10
            if "aplicable" not in it:
                it["aplicable"] = True
            if it.get("evidencia") is None:
                it["evidencia"] = ""

            # 2. BLINDAJE ADMINISTRATIVO (Fuerza Bruta)
            # Si la key está en nuestra lista maestra, ignoramos a la IA
            # y forzamos el estado "NA Positivo" (Amarillo con puntos).
            if it.get("key") in KEYS_ADMINISTRATIVAS:
                it["aplicable"] = False  # Esto hace que se vea como N/A
                it["ok"] = True          # Esto asegura que sume los puntos (NA=Valor)
                # Limpiamos evidencia para evitar textos confusos de la IA
                it["evidencia"] = "Puntos por default (Item Administrativo)"

    return eval_data

def atributos_con_calificacion(sections):
    """
    Devuelve lista de dicts por atributo:
      - OK & aplicable=True  -> otorga 'peso'
      - NO & aplicable=True  -> otorga 0
      - aplicable=False (N/A)-> otorga 'peso'
    """
    detalles = []
    for sec in (sections or []):
        for it in (sec.get("items") or []):
            key = it.get("key", "(sin_key)")
            try:
                peso = int(it.get("peso", 0))
            except Exception:
                peso = 0
            aplicable = it.get("aplicable", True)
            ok = it.get("ok", False)

            if not aplicable:
                estado = "NA"
                otorgado = peso
            else:
                if ok:
                    estado = "OK"
                    otorgado = peso
                else:
                    estado = "NO"
                    otorgado = 0

            detalles.append({"key": key, "peso": peso, "estado": estado, "otorgado": otorgado})
    return detalles

def compute_scores_with_na(sections, criticos):
    """
    Retorna: score_bruto (incluye N/A, cap 100), fallo_critico (bool), score_final, detalles
    """
    detalles = atributos_con_calificacion(sections)
    score_bruto = sum(d["otorgado"] for d in detalles)
    try:
        score_bruto = int(max(0, min(100, score_bruto)))
    except Exception:
        score_bruto = 0
    fallo_critico = any(not c.get("ok", False) for c in (criticos or []))
    score_final = 0 if fallo_critico else score_bruto
    return score_bruto, fallo_critico, score_final, detalles

def _atributos_a_columnas_valor(det_atrib):
    """
    Convierte detalle por atributo en columnas:
      - "Cumplido <key>" = valor 'otorgado' (int o 0/'' si falta)
      - Si estado es "NA", pone "NA=<valor>"
    Retorna: (dict_columnas, set_base_keys)
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
