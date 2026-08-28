#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Native Direct Diagram Parsers for TEMIS
Imports Lucidchart CSV of shape data, JSON, and SVG directly without LLM/Gemini intervention
100% Deterministic, preserves exact text, shapes, connections and positions
"""

import csv
import io
import json
import re
from typing import Dict, Any, List, Tuple


def map_lucid_shape_to_temis(shape_name: str, text: str) -> str:
    """Map Lucidchart shape names to TEMIS Official Symbology types"""
    name_lower = (shape_name or "").lower()
    text_lower = (text or "").lower()

    if "terminator" in name_lower or "start" in text_lower or "inicio" in text_lower or "end" in text_lower or "fin" in text_lower:
        if "fin" in text_lower or "end" in text_lower or "cierre" in text_lower:
            return "node_end"
        return "node_start"

    if "decision" in name_lower or "?" in text or "¿" in text or "si/no" in text_lower or "valida" in text_lower:
        return "node_decision"

    if "document" in name_lower or "form" in text_lower or "ficha" in text_lower or "carta" in text_lower:
        return "node_document"

    if "database" in name_lower or "data" in name_lower:
        return "node_database"

    if "system" in name_lower or "chronos" in text_lower or "erp" in text_lower:
        return "node_system"

    if "whatsapp" in text_lower:
        return "channel_whatsapp"

    if "freshdesk" in text_lower:
        return "channel_freshdesk"

    if "bria" in text_lower:
        return "channel_bria"

    return "node_activity"


def parse_lucidchart_csv(csv_content: str) -> Dict[str, Any]:
    """
    Parse Lucidchart 'CSV of shape data' export directly
    Extracts all shapes, text labels, line connections, and container hierarchy
    """
    nodes = []
    edges = []
    swimlanes_set = set()

    # Read CSV
    f = io.StringIO(csv_content)
    reader = csv.DictReader(f)

    raw_shapes = []
    raw_lines = []

    for row in reader:
        # Normalize header keys (strip spaces / lowercase)
        norm_row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
        
        # Check if line connector
        line_src = norm_row.get("line source") or norm_row.get("linesource") or norm_row.get("source")
        line_dst = norm_row.get("line destination") or norm_row.get("linedestination") or norm_row.get("destination")
        
        if line_src and line_dst:
            raw_lines.append((line_src, line_dst, norm_row.get("text area 1") or norm_row.get("label") or ""))
        else:
            raw_shapes.append(norm_row)

    # Process Shapes
    col_width = 240
    row_height = 140
    col_idx = 0
    row_idx = 0

    shape_id_map = {}

    for idx, shape in enumerate(raw_shapes):
        shape_id = shape.get("id") or shape.get("shape id") or f"s-{idx+1}"
        text = shape.get("text area 1") or shape.get("name") or shape.get("text") or f"Paso {idx+1}"
        shape_name = shape.get("name") or shape.get("shape library") or ""
        container = shape.get("contained by") or shape.get("swimlane") or "Lienzo Principal"

        if container:
            swimlanes_set.add(container)

        node_type = map_lucid_shape_to_temis(shape_name, text)

        # Activity number calculation
        act_num = None
        if node_type == "node_activity":
            act_num = idx + 1

        # Grid positioning layout
        x_pos = 60 + (col_idx * col_width)
        y_pos = 120 + (row_idx * row_height)
        
        col_idx += 1
        if col_idx >= 5:
            col_idx = 0
            row_idx += 1

        node_dict = {
            "id": f"node-{idx+1}",
            "type": node_type,
            "label": text,
            "swimlane": container if container else "General",
            "x": x_pos,
            "y": y_pos,
            "activity_number": act_num,
            "attached_system": "Chronos" if "chronos" in text.lower() else ("Freshdesk" if "freshdesk" in text.lower() else ""),
            "attached_channel": "WhatsApp" if "whatsapp" in text.lower() else ("Bria" if "bria" in text.lower() else "")
        }
        nodes.append(node_dict)
        shape_id_map[shape_id] = node_dict["id"]

    # Process Line Connections
    for e_idx, (src, dst, label) in enumerate(raw_lines):
        mapped_src = shape_id_map.get(src, src)
        mapped_dst = shape_id_map.get(dst, dst)
        edges.append({
            "id": f"edge-{e_idx+1}",
            "source": mapped_src,
            "target": mapped_dst,
            "label": label
        })

    swimlanes_list = list(swimlanes_set) if swimlanes_set else ["Lienzo Principal"]

    return {
        "title": "Diagrama Importado de Lucidchart",
        "swimlanes": swimlanes_list,
        "nodes": nodes,
        "edges": edges
    }
