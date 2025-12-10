
import os
import json
import logging
import unicodedata
from .rules_engine import GLOBAL_RULES, RULES_BY_DEPT
from ..config.constants import LOCAL_RUBRICS_DIR

logger = logging.getLogger("athenas_lite")

def _normalize_name(s: str) -> str:
    s = (s or "").strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.casefold()

def load_dept_rubric_json_local(dept: str) -> dict | None:
    """
    Busca ./rubricas/<Departamento>.json (tolerante a acentos y mayúsculas).
    - Primero intenta match exacto.
    - Luego intenta match normalizado.
    """
    if not os.path.isdir(LOCAL_RUBRICS_DIR):
        logger.warning(f"Rubrics directory not found: {LOCAL_RUBRICS_DIR}")
        return None

    expected_name = f"{dept}.json"
    expected_path = os.path.join(LOCAL_RUBRICS_DIR, expected_name)
    if os.path.exists(expected_path):
        try:
            with open(expected_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.exception(f"Error loading rubric {expected_path}: {e}")
            return None

    # búsqueda tolerante
    target_norm = _normalize_name(expected_name)
    try:
        for fn in os.listdir(LOCAL_RUBRICS_DIR):
            if not fn.lower().endswith(".json"):
                continue
            if _normalize_name(fn) == target_norm:
                with open(os.path.join(LOCAL_RUBRICS_DIR, fn), "r", encoding="utf-8") as f:
                    return json.load(f)
    except Exception as e:
        logger.exception(f"Error searching rubric for {dept}: {e}")
        return None

    return None

def rubric_json_to_prompt(dept: str, rubric: dict) -> str:
    """
    Convierte la rúbrica JSON en un prompt "Gemini-ready".
    """
    dep = rubric.get("department") or dept
    sections = rubric.get("sections", [])
    criticos = rubric.get("section_VI", {}).get("criticos", [])

    # incluye críticos marcados en items (evitando duplicados)
    existing_keys = {c.get("key") for c in criticos}  # Set de keys ya existentes
    for s in sections:
        for it in s.get("items", []) or []:
            if it.get("critico", False) and it.get("key"):
                key = it["key"]
                if key not in existing_keys:  # Solo agregar si no existe
                    criticos.append({"key": key})
                    existing_keys.add(key)


    out = []
    out.append(f"Departamento: {dep}")
    out.append("ESCUCHA Y Analiza el audio y responde SOLO con un objeto JSON que siga este esquema EXACTO (sin comentarios, sin markdown):")
# ----- INICIO DE INSTRUCCIONES  -----
    out.append("\nInstrucciones clave para la evaluación:")
    out.append("1. 'ok: true' significa que el agente CUMPLIÓ exitosamente el criterio.")
    out.append("2. 'ok: false' significa que el agente NO CUMPLIÓ el criterio (sea por omisión o por error).")
    out.append("3. 'aplicable: false' se usa EXCLUSIVAMENTE cuando el contexto de la llamada hizo IMPOSIBLE evaluar el criterio (ej. el cliente colgó antes del saludo).")
    out.append("4. 'evidencia': Si marcas 'ok: false' o 'aplicable: false', justifica brevemente por qué.")
    # ===== Reglas especiales de evaluación =====
    out.append("\nReglas Especiales de Evaluación:")

    # 1) Reglas comunes para todos
    active_rule_keys = list(RULES_BY_DEPT.get("_COMUNES", []))

    # 2) Reglas específicas del departamento actual
    active_rule_keys += RULES_BY_DEPT.get(dep, [])

    # 3) Quitar duplicados respetando el orden
    seen = set()
    active_rule_keys = [k for k in active_rule_keys if not (k in seen or seen.add(k))]

    # 4) Pegamos el texto de cada regla desde GLOBAL_RULES
    for key in active_rule_keys:
        rule_text = GLOBAL_RULES.get(key)
        if rule_text:
            out.append(rule_text)

    # Refuerzo anti-alucinación
    out.append(
        "\nIMPORTANTE:\n"
        "- Aplica estas reglas SOLO si el contenido del audio coincide claramente con lo descrito.\n"
        "- Si la llamada no encaja en un caso especial, IGNORA la regla especial.\n"
        "- En caso de duda, evalúa únicamente con los criterios generales del JSON."
    )
    out.append(
        "- Si la llamada coincide parcialmente con el caso especial, pero el cumplimiento es razonable, "
        "prefiere marcar 'ok: true' o 'aplicable: false' en lugar de 'ok: false'."
    )

    out.append("\nCriterio de TOLERANCIA (muy importante):")
    out.append(
        "- SOLO marca 'ok: false' cuando la falla sea CLARA, IMPORTANTE y tenga impacto real "
        "en la experiencia del cliente, en la operación o en el cumplimiento."
    )
    out.append(
        "- Si la evidencia es dudosa, incompleta o ambigua, prefiere marcar 'ok: true' o "
        "'aplicable: false' en lugar de castigar al asesor."
    )
    out.append(
        "- Errores pequeños de forma (muletillas, frases no perfectas, ligeros cambios en el guion) "
        "NO deben marcarse como 'ok: false' si el objetivo principal del criterio se cumple."
    )
    out.append(
        "- Nunca inventes errores: si no encuentras evidencia clara en el audio, asume que el criterio "
        "se cumplió o que 'no aplica'."
    )

    # ----- FIN-----

    schema_prompt = f"""
{{
  "department": "{dep}",
  "sections": [
    {{
      "name": "(nombre de la sección, ej: Saludo)",
      "items": [
        {{
          "key": "(clave_del_item, ej: tiempo_respuesta)",
          "peso": "(el peso numérico original del item, ej: 4)",
          "ok": (true | false),
          "aplicable": (true | false),
          "evidencia": "(justificación breve o cita del audio si no aplica o falla)"
        }}
      ]
    }}
  ],
  "section_VI": {{
    "criticos": [
      {{
        "key": "(clave_del_critico, ej: actitud_servicio)",
        "ok": (true | false)
      }}
    ]
  }},
  "fortalezas": ["(lista de 1 a 3 fortalezas observadas)"],
  "compromisos": ["(lista de 1 a 3 compromisos o áreas de mejora)"],
  "contenido_evaluador": "(Un resumen detallado en prosa de la llamada, destacando el desempeño del agente y los puntos clave de la interacción)"
}}
"""
    out.append("\n".join([line.strip() for line in schema_prompt.splitlines()]))

    out.append("\nCriterios y pesos (para tu referencia):")
    for s in sections:
        out.append(f"Sección: {s.get('name','(sin nombre)')}")
        for it in s.get("items", []) or []:
            peso = it.get("peso", 10)
            sug = it.get("sugerencias", [])
            suger = f" | sugerencias: {', '.join(sug)}" if sug else ""
            crit = " | CRITICO" if it.get("critico", False) else ""
            out.append(f" - {it.get('key','(sin clave)')} | peso: {peso}{suger}{crit}")

    if criticos:
        out.append("\nCriterios críticos (para tu referencia):")
        for c in criticos:
            out.append(f" - {c.get('key','(sin clave)')}")

    out.append("\nRecuerda: Responde ÚNICAMENTE con el objeto JSON solicitado.")
    return "\n".join(out)
