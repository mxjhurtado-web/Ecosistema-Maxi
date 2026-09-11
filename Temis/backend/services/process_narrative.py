#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Process Narrative Service for TEMIS
Converts Flowchart DAGs and SIPOC matrices into formal corporate policy, 
procedure manuals, and continuous prose narratives.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)


def generate_local_narrative(
    project_name: str,
    project_purpose: str,
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    sipoc_rows: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Deterministic local generation of corporate procedure manual when Gemini is offline"""
    title = project_name if project_name else "Procedimiento Operativo Estándar"
    purpose = project_purpose if project_purpose else "Definir y estandarizar la secuencia operativa del proceso de inicio a fin."

    # Extract actors, systems, channels
    actors = set()
    systems = set()
    channels = set()
    
    for n in nodes:
        if n.get("swimlane"):
            actors.add(n["swimlane"])
        if n.get("attached_system"):
            systems.add(n["attached_system"])
        if n.get("attached_channel"):
            channels.add(n["attached_channel"])

    actors_str = ", ".join(sorted(actors)) if actors else "Área Operativa / Usuario / Sistema"
    systems_str = ", ".join(sorted(systems)) if systems else "Sistemas Centrales (Chronos / ERP)"
    channels_str = ", ".join(sorted(channels)) if channels else "WhatsApp / Portal Web / Bria"

    # Sort nodes topologically or by X position
    sorted_nodes = sorted(nodes, key=lambda x: (x.get("x", 0), x.get("y", 0)))
    
    steps_md = []
    step_counter = 1
    
    # Map edges for decision tracking
    edge_map = {}
    for e in edges:
        src = e.get("source")
        if src not in edge_map:
            edge_map[src] = []
        edge_map[src].append(e)

    for n in sorted_nodes:
        ntype = n.get("type", "")
        label = n.get("label", "Actividad")
        swimlane = n.get("swimlane", "Operación")
        sys_tag = f" a través de **{n['attached_system']}**" if n.get("attached_system") else ""
        chan_tag = f" por el canal **{n['attached_channel']}**" if n.get("attached_channel") else ""

        if ntype == "node_start":
            steps_md.append(
                f"### {step_counter}.0 Entrada e Inicio del Proceso\n"
                f"El proceso inicia formalmente cuando el participante **[{swimlane}]** "
                f"detona el evento: *\"{label}\"*{chan_tag}. Se reciben los datos iniciales y se habilita el caso para su gestión."
            )
            step_counter += 1
        elif ntype == "node_decision":
            outgoing = edge_map.get(n.get("id"), [])
            branches = []
            for out in outgoing:
                cond = out.get("label") or "Flujo siguiente"
                tgt_id = out.get("target")
                tgt_node = next((item for item in nodes if item["id"] == tgt_id), None)
                tgt_label = tgt_node.get("label", "") if tgt_node else ""
                branches.append(f"  - **Condición '{cond}':** Se deriva de forma inmediata a *\"{tgt_label}\"*.")
            
            branch_text = "\n".join(branches) if branches else "  - Se evalúan los criterios de negocio definidos."
            steps_md.append(
                f"### {step_counter}.0 Punto de Decisión / Validación: {label}\n"
                f"El rol **[{swimlane}]** realiza la validación crítica *\"{label}\"*{sys_tag}. Las ramificaciones son:\n{branch_text}"
            )
            step_counter += 1
        elif ntype == "node_activity":
            act_num = n.get("activity_number") or step_counter
            steps_md.append(
                f"### {act_num}.0 Ejecución de Tarea: {label}\n"
                f"El responsable **[{swimlane}]** ejecuta la actividad operativa de *\"{label}\"*{sys_tag}{chan_tag}. "
                f"Se actualiza el estado de la transacción y se genera el registro auditable correspondiente."
            )
            step_counter += 1
        elif ntype == "node_end":
            steps_md.append(
                f"### {step_counter}.0 Cierre y Conclusión del Proceso\n"
                f"Se completa la etapa final: *\"{label}\"*. El proceso concluye satisfactoriamente con la entrega del producto/resultado "
                f"hacia el participante **[{swimlane}]**."
            )
            step_counter += 1

    steps_text = "\n\n".join(steps_md)

    sipoc_summary = ""
    if sipoc_rows:
        sipoc_lines = []
        for r in sipoc_rows:
            p = r.get("step") or r.get("process") or "Paso"
            s = r.get("provider") or r.get("supplier") or "-"
            i = r.get("input") or "-"
            o = r.get("output") or "-"
            c = r.get("customer") or "-"
            sipoc_lines.append(f"- **{p}**: Proveedor: *{s}* | Entrada: *{i}* ➔ Salida: *{o}* | Cliente: *{c}*")
        sipoc_summary = f"\n\n## 📋 Matriz de Transformación SIPOC\n" + "\n".join(sipoc_lines)

    narrative = f"""# 📘 Manual de Procedimientos & Narrativa Oficial
# {title}

## 🎯 1. Objetivo y Propósito del Proceso
{purpose}

## 👥 2. Matriz de Roles y Responsabilidades
- **Actores y Participantes:** {actors_str}
- **Sistemas y Plataformas:** {systems_str}
- **Canales de Interacción:** {channels_str}

---

## 📝 3. Narrativa Operativa Secuencial (Paso a Paso)

{steps_text}
{sipoc_summary}

---

## ⚖️ 4. Políticas y Reglas de Negocio Clave
1. **Trazabilidad Absoluta:** Toda interacción por canal digital o sistema debe quedar registrada con marca de tiempo y folio.
2. **Control de Calidad:** Las compuertas de decisión deben validar que la totalidad de requisitos previos se cumplan antes de pasar a la siguiente fase.
3. **Escalamiento:** En caso de excepción no contemplada en las reglas estándar, el caso se turna al líder del proceso para dictamen.
"""
    return narrative.strip()


def generate_process_narrative(
    project_name: str,
    project_purpose: str,
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    sipoc_rows: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Generate formal corporate process narrative in continuous prose using Gemini AI
    with automatic fallback to deterministic structural generator.
    """
    if not api_key:
        try:
            from config.config import get_gemini_api_key
            api_key = get_gemini_api_key()
        except Exception:
            api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return generate_local_narrative(project_name, project_purpose, nodes, edges, sipoc_rows)

    try:
        from backend.services.gemini_service import GeminiChatService
        gemini = GeminiChatService(api_key=api_key)

        prompt = f"""Eres un Auditor Senior de Calidad y Procesos Corporativos Six Sigma / BPMN.
Tu tarea es redactar la NARRATIVA OFICIAL Y MANUAL DE PROCEDIMIENTOS en texto corrido y formal a partir del siguiente diagrama de flujo y datos del proyecto.

DATOS DEL PROYECTO:
- Nombre: {project_name}
- Propósito / Para qué es: {project_purpose}

ESTRUCTURA DEL FLUJO (NODOS):
{json.dumps(nodes, ensure_ascii=False, indent=2)}

CONEXIONES (EDGES):
{json.dumps(edges, ensure_ascii=False, indent=2)}

FILAS SIPOC:
{json.dumps(sipoc_rows or [], ensure_ascii=False, indent=2)}

INSTRUCCIONES DE REDACCIÓN:
1. Redacta en prosa continua, formal, clara y estructurada en formato Markdown.
2. La sección principal 'Narrativa Operativa Paso a Paso' debe detallar cada paso con su numeración (1.0, 2.0, 3.0...), indicando qué rol actúa, qué sistemas o canales utiliza (ej. Chronos, WhatsApp), qué datos entran y salen, y qué decisiones se toman.
3. Incluye:
   - Título del Procedimiento
   - Objetivo y Alcance
   - Matriz de Roles, Sistemas y Canales
   - Narrativa Secuencial Detallada (1.0..N)
   - Políticas y Reglas de Cumplimiento
4. Devuelve ÚNICAMENTE el texto en Markdown listo para publicarse como documento oficial.
"""

        response = gemini.get_structured_response(prompt, max_tokens=6000)
        
        # If response returned text or raw JSON string, clean it
        if response and len(response.strip()) > 50:
            cleaned = response.strip()
            # If wrapped in JSON, extract string
            if cleaned.startswith("{") and "narrative" in cleaned:
                try:
                    data = json.loads(cleaned)
                    return data.get("narrative", cleaned)
                except Exception:
                    pass
            return cleaned
        else:
            return generate_local_narrative(project_name, project_purpose, nodes, edges, sipoc_rows)

    except Exception as e:
        logger.warning(f"Gemini narrative generation failed, using local engine: {e}")
        return generate_local_narrative(project_name, project_purpose, nodes, edges, sipoc_rows)
