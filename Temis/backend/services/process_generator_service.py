#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Process Generator Service for TEMIS
Transforms curated Narrative Analysis results into:
1. Dual SIPOC Matrices (AS-IS and TO-BE)
2. Dual Multi-Tab BPMN Flowchart Canvas Pages (AS-IS and TO-BE)
with topological node placement, swimlane partitioning, and Bézier routing.
"""

from typing import Dict, Any, List, Tuple, Optional
import uuid
import datetime
from backend.models.narrative_source_model import (
    NarrativeAnalysisResult,
    ActivityStepData,
    DualSipocProposal,
    SipocRowModel,
)


class ProcessGeneratorService:
    """Generates SIPOC matrices and BPMN canvas graphs from structured narrative steps"""

    @staticmethod
    def generate_dual_sipoc(analysis: NarrativeAnalysisResult) -> DualSipocProposal:
        """
        Generate AS-IS and TO-BE SIPOC rows from analysis result.
        """
        asis_rows: List[SipocRowModel] = []
        for idx, s in enumerate(analysis.asis_steps, start=1):
            prov = s.responsible if s.responsible else "Área Operativa"
            inp = f"Datos / {s.attached_system}" if s.attached_system else "Solicitud del proceso"
            out = s.record_control if s.record_control else f"Registro de {s.activity_name}"
            cust = "Cliente / Área Solicitante" if idx == len(analysis.asis_steps) else "Siguiente Responsable"
            
            asis_rows.append(SipocRowModel(
                id=f"sipoc-asis-{idx}",
                step=f"{s.step_number}.0 {s.activity_name}",
                provider=prov,
                input=inp,
                output=out,
                customer=cust,
                requirements="Cumplimiento de políticas y validación de datos",
                source_ref=s.source_citation or f"Paso {s.step_number}"
            ))

        tobe_rows: List[SipocRowModel] = []
        for idx, s in enumerate(analysis.tobe_steps, start=1):
            prov = s.responsible if s.responsible else "Sistema / Bot"
            inp = f"Traspaso API / {s.attached_system or 'Chronos'}"
            out = s.record_control if s.record_control else f"Validación Digital de {s.activity_name}"
            cust = "Cliente Final / Auditoría" if idx == len(analysis.tobe_steps) else "Sistema Siguiente"

            tobe_rows.append(SipocRowModel(
                id=f"sipoc-tobe-{idx}",
                step=f"{s.step_number}.0 {s.activity_name}",
                provider=prov,
                input=inp,
                output=out,
                customer=cust,
                requirements="Validación automática con SLA < 15 min",
                source_ref=s.source_citation or f"Paso {s.step_number} (TO-BE)"
            ))

        return DualSipocProposal(
            asis_rows=asis_rows,
            tobe_rows=tobe_rows,
            generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    @staticmethod
    def generate_bpmn_page(
        steps: List[ActivityStepData],
        page_id: str,
        page_name: str,
        diagram_type: str = "asis"
    ) -> Dict[str, Any]:
        """
        Build a complete flowchart page dictionary compatible with FlowState.project_pages
        """
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        swimlanes_set: List[str] = []

        # Collect unique swimlanes preserving order
        for s in steps:
            lane = s.responsible.strip() if s.responsible else "Operación General"
            if lane not in swimlanes_set:
                swimlanes_set.append(lane)

        if not swimlanes_set:
            swimlanes_set = ["Operación General"]

        # If swimlanes don't have Input/Output, add them for clean boundaries if needed
        swimlane_y_map = {lane: 80 + (idx * 160) for idx, lane in enumerate(swimlanes_set)}

        # 1. Start Node
        first_lane = swimlanes_set[0]
        start_node_id = f"node-{diagram_type}-start"
        nodes.append({
            "id": start_node_id,
            "type": "node_start",
            "label": f"Inicio: {page_name}",
            "swimlane": first_lane,
            "x": 60,
            "y": swimlane_y_map.get(first_lane, 80),
            "activity_number": None,
            "attached_system": "",
            "attached_channel": ""
        })

        col_spacing = 260
        prev_node_id = start_node_id
        step_id_map: Dict[int, str] = {}

        # 2. Activity & Decision Nodes
        for idx, s in enumerate(steps, start=1):
            curr_x = 60 + (idx * col_spacing)
            lane = s.responsible.strip() if s.responsible else first_lane
            curr_y = swimlane_y_map.get(lane, 80)
            
            node_id = f"node-{diagram_type}-{s.step_number}"
            step_id_map[s.step_number] = node_id

            node_type = "node_decision" if s.is_decision else "node_activity"
            label = s.decision_question if (s.is_decision and s.decision_question) else s.activity_name

            nodes.append({
                "id": node_id,
                "type": node_type,
                "label": label,
                "swimlane": lane,
                "x": curr_x,
                "y": curr_y,
                "activity_number": s.step_number if not s.is_decision else None,
                "attached_system": s.attached_system or "",
                "attached_channel": s.attached_channel or ""
            })

            # Connect from previous sequential node
            edge_id = f"edge-{diagram_type}-{len(edges)+1}"
            edges.append({
                "id": edge_id,
                "source": prev_node_id,
                "target": node_id,
                "label": ""
            })
            prev_node_id = node_id

        # 3. Decision branches wiring if specified
        for s in steps:
            if s.is_decision and s.decision_branches:
                src_id = step_id_map.get(s.step_number)
                if not src_id:
                    continue
                for b in s.decision_branches:
                    tgt_num = b.target_activity_number
                    if tgt_num and tgt_num in step_id_map:
                        tgt_id = step_id_map[tgt_num]
                        # Check if edge already exists
                        if not any(e["source"] == src_id and e["target"] == tgt_id for e in edges):
                            edges.append({
                                "id": f"edge-{diagram_type}-{len(edges)+1}",
                                "source": src_id,
                                "target": tgt_id,
                                "label": b.condition_label
                            })

        # 4. End Node
        last_lane = swimlanes_set[-1]
        end_x = 60 + ((len(steps) + 1) * col_spacing)
        end_node_id = f"node-{diagram_type}-end"
        nodes.append({
            "id": end_node_id,
            "type": "node_end",
            "label": f"Fin {page_name}",
            "swimlane": last_lane,
            "x": end_x,
            "y": swimlane_y_map.get(last_lane, 80),
            "activity_number": None,
            "attached_system": "",
            "attached_channel": ""
        })

        edges.append({
            "id": f"edge-{diagram_type}-{len(edges)+1}",
            "source": prev_node_id,
            "target": end_node_id,
            "label": "Concluido"
        })

        return {
            "page_id": page_id,
            "name": page_name,
            "diagram_type": diagram_type,
            "swimlanes": swimlanes_set,
            "nodes": nodes,
            "edges": edges,
            "provenance_tag": f"Generado desde análisis de narrativa ({diagram_type.upper()})"
        }

    @staticmethod
    def generate_dual_bpmn(analysis: NarrativeAnalysisResult) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate both AS-IS and TO-BE BPMN diagram pages.
        """
        page_asis = ProcessGeneratorService.generate_bpmn_page(
            steps=analysis.asis_steps,
            page_id="bpmn-asis",
            page_name="Flujo AS-IS (Proceso Actual)",
            diagram_type="asis"
        )

        page_tobe = ProcessGeneratorService.generate_bpmn_page(
            steps=analysis.tobe_steps if analysis.tobe_steps else analysis.asis_steps,
            page_id="bpmn-tobe",
            page_name="Flujo TO-BE (Proceso Deseado / Optimizado)",
            diagram_type="tobe"
        )

        return page_asis, page_tobe
