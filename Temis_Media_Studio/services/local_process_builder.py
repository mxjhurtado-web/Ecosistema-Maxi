#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Local Process Builder for TEMIS Media Studio (100% Offline / 0 Tokens)
Correlates transcript timestamps with extracted keyframe screenshots,
and formats the structured process package without external AI.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("temis_media_studio")


class LocalProcessBuilder:
    """Builds process steps, SIPOC baselines, and links screenshots 100% locally"""

    @classmethod
    def structure_process(
        cls,
        transcript_segments: List[Dict[str, Any]],
        keyframes: List[Dict[str, Any]],
        video_filename: str,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Structure chronological process steps and pair each step with the closest screenshot
        """
        if progress_callback:
            progress_callback("Estructurando bitácora y emparejando capturas por minutaje...")

        clean_name = os.path.splitext(video_filename)[0].replace("_", " ").replace("-", " ").title()

        # 1. Group transcript segments into logical process steps (e.g. every 3-5 sentences or 1-2 minutes)
        steps: List[Dict[str, Any]] = []
        
        if not transcript_segments:
            # Fallback if no audio
            transcript_segments = [{
                "index": 1,
                "timestamp_start": "00:00:00",
                "timestamp_end": "00:01:00",
                "speaker": "Operador",
                "text": "Grabación de video del proceso."
            }]

        # Determine step grouping size
        total_segments = len(transcript_segments)
        group_size = max(1, min(5, total_segments // 8)) if total_segments > 8 else max(1, total_segments // 4)
        if group_size == 0:
            group_size = 1

        step_counter = 1
        for i in range(0, total_segments, group_size):
            chunk = transcript_segments[i:i + group_size]
            first_seg = chunk[0]
            last_seg = chunk[-1]
            
            combined_text = " ".join([s.get("text", "") for s in chunk])
            start_ts = first_seg.get("timestamp_start", "00:00:00")
            start_sec = first_seg.get("start_sec", 0.0)

            # Find closest keyframe screenshot by timestamp
            closest_kf = None
            min_dist = float("inf")
            for kf in keyframes:
                kf_sec = kf.get("timestamp_sec", 0.0)
                dist = abs(kf_sec - start_sec)
                if dist < min_dist:
                    min_dist = dist
                    closest_kf = kf

            attached_img = closest_kf.get("filename", "") if closest_kf else ""
            img_caption = f"Evidencia gráfica en pantalla ({closest_kf.get('timestamp_formatted', start_ts)})" if closest_kf else ""

            # Extract title preview
            first_sentence = combined_text.split(".")[0] if "." in combined_text else combined_text[:60]
            title_text = f"Paso {step_counter}: {first_sentence.strip()[:65]}"
            if len(first_sentence.strip()) > 65:
                title_text += "..."

            steps.append({
                "step_number": step_counter,
                "title": title_text,
                "actor": "Operador / Analista",
                "system": "Sistema en Pantalla",
                "timestamp": start_ts,
                "description": combined_text,
                "attached_screenshot": attached_img,
                "screenshot_caption": img_caption
            })
            step_counter += 1

        # 2. Build High-level SIPOC matrix from steps
        sipoc_rows = []
        for idx, stp in enumerate(steps[:8]):
            sipoc_rows.append({
                "id": f"{idx+1}.0",
                "supplier": "Usuario / Solicitante",
                "input": "Datos del sistema / Solicitud",
                "process": stp.get("title", f"Actividad {idx+1}"),
                "output": "Registro actualizado / Validación",
                "customer": "Área Receptora / Cliente",
                "requirement": "Ejecutar conforme al procedimiento estándar"
            })

        # 3. Build BPMN Nodes & Edges
        bpmn_nodes = [
            {"id": "node-1", "type": "node_start", "label": f"Inicio: {clean_name}", "swimlane": "Input", "x": 40, "y": 140, "attached_system": "", "attached_channel": ""}
        ]
        bpmn_edges = []

        curr_x = 260
        prev_node_id = "node-1"
        for idx, stp in enumerate(steps[:6]):
            nid = f"node-{idx+2}"
            bpmn_nodes.append({
                "id": nid,
                "type": "node_activity",
                "label": stp.get("title", f"Paso {idx+1}")[:45],
                "swimlane": "Operador",
                "x": curr_x,
                "y": 140,
                "attached_system": "Sistema",
                "attached_channel": ""
            })
            bpmn_edges.append({
                "id": f"e{prev_node_id}-{nid}",
                "source": prev_node_id,
                "target": nid,
                "label": ""
            })
            prev_node_id = nid
            curr_x += 240

        end_node_id = f"node-{len(bpmn_nodes)+1}"
        bpmn_nodes.append({
            "id": end_node_id,
            "type": "node_end",
            "label": "Fin: Proceso Concluido",
            "swimlane": "Output",
            "x": curr_x,
            "y": 140,
            "attached_system": "",
            "attached_channel": ""
        })
        bpmn_edges.append({
            "id": f"e{prev_node_id}-{end_node_id}",
            "source": prev_node_id,
            "target": end_node_id,
            "label": ""
        })

        return {
            "project_charter": {
                "project_name": f"Proceso: {clean_name}",
                "project_code": "PRJ-LOCAL-01",
                "purpose": f"Levantamiento de bitácora y evidencia gráfica para '{clean_name}'.",
                "scope": "Desde la recepción inicial hasta la conclusión de la actividad en pantalla.",
                "target_system": "Sistemas Registrados en Video",
                "sponsor": "Área de Procesos y Operaciones",
                "executive_summary": f"Bitácora de levantamiento generada de forma 100% local a partir de la grabación '{video_filename}'. Contiene {len(steps)} pasos cronológicos, {len(keyframes)} capturas de pantalla y transcripción con minutaje exacto."
            },
            "process_steps": steps,
            "sipoc": sipoc_rows,
            "bpmn_nodes": bpmn_nodes,
            "bpmn_edges": bpmn_edges,
            "audit_findings": []
        }
