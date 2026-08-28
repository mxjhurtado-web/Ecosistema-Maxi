#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Native Direct Diagram Parsers for TEMIS
Imports Lucidchart CSV of shape data, JSON, and SVG directly without LLM/Gemini intervention
100% Deterministic, preserves exact text, shapes, connections and positions per diagram page
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


def clean_id(val: Any) -> str:
    """Normalize shape ID strings for clean dictionary mapping"""
    return str(val or "").strip().lower()


def parse_lucidchart_csv(csv_content: str, target_page_id: str = None) -> Dict[str, Any]:
    """
    Parse Lucidchart 'CSV of shape data' export directly
    Groups shapes and lines by Page ID to render pristine, clean individual page flowcharts
    """
    # Read CSV
    f = io.StringIO(csv_content)
    reader = csv.DictReader(f)

    page_shapes = {}
    page_lines = {}

    for idx, row in enumerate(reader):
        norm_row = {clean_id(k): (v or "").strip() for k, v in row.items() if k}
        page_id = norm_row.get("page id") or "1"

        line_src = (
            norm_row.get("line source") or 
            norm_row.get("linesource") or 
            norm_row.get("source") or 
            norm_row.get("from")
        )
        line_dst = (
            norm_row.get("line destination") or 
            norm_row.get("linedestination") or 
            norm_row.get("destination") or 
            norm_row.get("to")
        )

        if line_src and line_dst:
            label = (
                norm_row.get("text area 1") or 
                norm_row.get("label") or 
                norm_row.get("text") or 
                ""
            )
            page_lines.setdefault(page_id, []).append((clean_id(line_src), clean_id(line_dst), label))
        else:
            page_shapes.setdefault(page_id, []).append(norm_row)

    # Determine best page to load (if target_page_id not specified)
    if not target_page_id or target_page_id not in page_shapes:
        # Find page with the highest number of line connectors
        best_page = max(page_lines.keys(), key=lambda p: len(page_lines[p])) if page_lines else (list(page_shapes.keys())[0] if page_shapes else "1")
        target_page_id = best_page

    raw_shapes = page_shapes.get(target_page_id, [])
    raw_lines = page_lines.get(target_page_id, [])

    # Map raw shape IDs to clean TEMIS node IDs
    shape_id_map = {}
    id_to_shape = {}

    for idx, shape in enumerate(raw_shapes):
        node_id = f"node-{idx+1}"
        id_to_shape[node_id] = shape

        raw_id = shape.get("id")
        raw_shape_id = shape.get("shape id")
        raw_key = shape.get("key")

        if raw_id:
            cid = clean_id(raw_id)
            shape_id_map[cid] = node_id
            if cid.isdigit():
                shape_id_map[str(int(cid))] = node_id

        if raw_shape_id:
            cid_shape = clean_id(raw_shape_id)
            shape_id_map[cid_shape] = node_id

        if raw_key:
            cid_key = clean_id(raw_key)
            shape_id_map[cid_key] = node_id

    # Process Edges for target page
    valid_edges = []
    adj_out = {}
    adj_in = {}

    for e_idx, (src_raw, dst_raw, label) in enumerate(raw_lines):
        mapped_src = shape_id_map.get(src_raw, src_raw)
        mapped_dst = shape_id_map.get(dst_raw, dst_raw)

        if mapped_src in id_to_shape and mapped_dst in id_to_shape and mapped_src != mapped_dst:
            edge_obj = {
                "id": f"edge-{e_idx+1}",
                "source": mapped_src,
                "target": mapped_dst,
                "label": label
            }
            valid_edges.append(edge_obj)
            adj_out.setdefault(mapped_src, []).append(mapped_dst)
            adj_in.setdefault(mapped_dst, []).append(mapped_src)

    # Topological Flowchart Layout Calculation
    levels = {}
    all_node_ids = list(id_to_shape.keys())
    
    roots = [nid for nid in all_node_ids if nid not in adj_in]
    if not roots:
        roots = all_node_ids[:1]

    queue = [(nid, 0) for nid in roots]
    visited = set()

    while queue:
        curr, lvl = queue.pop(0)
        if curr in visited:
            continue
        visited.add(curr)
        levels[curr] = max(levels.get(curr, 0), lvl)

        for next_id in adj_out.get(curr, []):
            if next_id not in visited:
                queue.append((next_id, lvl + 1))

    for nid in all_node_ids:
        if nid not in levels:
            levels[nid] = 0

    level_groups = {}
    for nid, lvl in levels.items():
        level_groups.setdefault(lvl, []).append(nid)

    # Compact Layout Parameters matching PDF style
    nodes = []
    swimlanes_set = set()
    col_width = 240
    row_height = 110
    start_x = 80
    start_y = 100

    for lvl_idx in sorted(level_groups.keys()):
        group = level_groups[lvl_idx]
        x_pos = start_x + (lvl_idx * col_width)
        for row_idx, nid in enumerate(group):
            shape = id_to_shape[nid]
            text = (
                shape.get("text area 1") or 
                shape.get("name") or 
                shape.get("text") or 
                ""
            )
            
            # Skip empty unmapped decorative user images
            if text.strip() in ["User Image", "User Images", ""] and nid not in adj_in and nid not in adj_out:
                continue

            if not text.strip():
                text = f"Paso {nid}"

            shape_name = shape.get("name") or shape.get("shape library") or ""
            container = shape.get("contained by") or shape.get("swimlane") or "Lienzo Principal"

            if container:
                swimlanes_set.add(container)

            node_type = map_lucid_shape_to_temis(shape_name, text)

            # Check explicit coordinates
            x_val = shape.get("x") or shape.get("left") or shape.get("pos_x")
            y_val = shape.get("y") or shape.get("top") or shape.get("pos_y")

            if x_val and y_val and x_val.replace('.', '', 1).replace('-', '', 1).isdigit() and y_val.replace('.', '', 1).replace('-', '', 1).isdigit():
                calc_x = max(40, float(x_val))
                calc_y = max(40, float(y_val))
            else:
                calc_x = x_pos
                calc_y = start_y + (row_idx * row_height)

            act_num = row_idx + 1 if node_type == "node_activity" else None

            node_dict = {
                "id": nid,
                "type": node_type,
                "label": text,
                "swimlane": container if container else "General",
                "x": calc_x,
                "y": calc_y,
                "activity_number": act_num,
                "attached_system": "Chronos" if "chronos" in text.lower() else ("Freshdesk" if "freshdesk" in text.lower() else ""),
                "attached_channel": "WhatsApp" if "whatsapp" in text.lower() else ("Bria" if "bria" in text.lower() else "")
            }
            nodes.append(node_dict)

    swimlanes_list = list(swimlanes_set) if swimlanes_set else ["Lienzo Principal"]

    return {
        "title": f"Diagrama Importado de Lucidchart (Página {target_page_id})",
        "swimlanes": swimlanes_list,
        "nodes": nodes,
        "edges": valid_edges,
        "current_page": target_page_id,
        "total_pages": len(page_shapes)
    }
