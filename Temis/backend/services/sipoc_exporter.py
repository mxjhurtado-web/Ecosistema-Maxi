#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SIPOC Excel Exporter for TEMIS
Generates Microsoft Excel (.xlsx) workbooks strictly matching 
the official TEMIS Six Sigma SIPOC template (Century Gothic, 11-column paired layout).
"""

import io
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def export_sipoc_to_excel(
    project_name: str,
    project_purpose: str,
    sipoc_rows: List[Dict[str, Any]],
    customer_requirements: str = ""
) -> io.BytesIO:
    """Generate official Six Sigma SIPOC Excel workbook matching Plantilla Matriz Sipoc.xlsx exactly"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Plantilla de diagrama SIPOC"
    ws.views.sheetView[0].showGridLines = True

    # Color Palette from Official Plantilla Matriz Sipoc.xlsx
    COLOR_S_BADGE = "FF595959"   # Dark Gray (B)
    COLOR_S_HEADER = "FF7F7F7F"  # Mid Gray (C)
    COLOR_I_BADGE = "FF44546A"   # Dark Steel (D)
    COLOR_I_HEADER = "FFADB9CA"  # Light Steel (E)
    COLOR_P_BADGE = "FF595959"   # Dark Gray (F)
    COLOR_P_HEADER = "FF7F7F7F"  # Mid Gray (G)
    COLOR_O_BADGE = "FF333F4F"   # Charcoal (H)
    COLOR_O_HEADER = "FF8496B0"  # Blue Gray (I)
    COLOR_C_BADGE = "FFA5A5A5"   # Silver (J)
    COLOR_C_HEADER = "FFBFBFBF"  # Light Silver (K)
    COLOR_WHITE_TEXT = "FFF2F2F2"
    COLOR_REQ_BG = "FFD6DCE4"    # Light Gray/Blue for Customer Requirements
    COLOR_ZEBRA = "FFF8FAFC"

    # Borders
    thin_side = Side(style="thin", color="CBD5E1")
    thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    bottom_thick = Border(bottom=Side(style="medium", color="475569"))

    # Column Widths matching Plantilla Matriz Sipoc.xlsx exactly
    col_widths = {
        "A": 3.22,
        "B": 11.22,  # S badge
        "C": 20.78,  # S name
        "D": 10.78,  # I badge
        "E": 20.78,  # I name
        "F": 10.78,  # P badge (1.0, 2.0...)
        "G": 20.78,  # P name
        "H": 10.78,  # O badge
        "I": 20.78,  # O name
        "J": 10.78,  # C badge
        "K": 20.78,  # C name
    }
    for col_l, w in col_widths.items():
        ws.column_dimensions[col_l].width = w

    # 1. Row 1: Title
    ws.row_dimensions[1].height = 49.5
    c_title = ws["B1"]
    c_title.value = f"PLANTILLA DE MATRIZ SIPOC — {project_name.upper()}" if project_name else "PLANTILLA DE MATRIZ SIPOC"
    c_title.font = Font(name="Century Gothic", size=20.0, bold=True, color="17283C")
    c_title.alignment = Alignment(horizontal="left", vertical="center")

    # 2. Row 2: Letters & Titles
    ws.row_dimensions[2].height = 75.0
    headers_r2 = [
        ("B", "S", COLOR_S_BADGE, 60.0),
        ("C", "S U P P L I E R S", COLOR_S_HEADER, 11.0),
        ("D", "I", COLOR_I_BADGE, 60.0),
        ("E", "I N P U T", COLOR_I_HEADER, 11.0),
        ("F", "P", COLOR_P_BADGE, 60.0),
        ("G", "P R O C E S S", COLOR_P_HEADER, 11.0),
        ("H", "O", COLOR_O_BADGE, 60.0),
        ("I", "O U T P U T", COLOR_O_HEADER, 11.0),
        ("J", "C", COLOR_C_BADGE, 60.0),
        ("K", "C U S T O M E R", COLOR_C_HEADER, 11.0),
    ]
    for col_l, text, fill_hex, fsize in headers_r2:
        cell = ws[f"{col_l}2"]
        cell.value = text
        cell.font = Font(name="Century Gothic", size=fsize, bold=True, color=COLOR_WHITE_TEXT)
        cell.fill = PatternFill(start_color=fill_hex, end_color=fill_hex, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # 3. Row 3: Theoretical Descriptions
    ws.row_dimensions[3].height = 55.5
    headers_r3 = [
        ("B", None, COLOR_S_BADGE),
        ("C", "Quién suministra lo que se requiere para ejecutar el proceso (Entrada).", COLOR_S_HEADER),
        ("D", None, COLOR_I_BADGE),
        ("E", "Recurso / insumo proporcionado por el proveedor para la incorporación al proceso.", COLOR_I_HEADER),
        ("F", None, COLOR_P_BADGE),
        ("G", "Actividades realizadas para convertir\nde entrada a salida.", COLOR_P_HEADER),
        ("H", None, COLOR_O_BADGE),
        ("I", "Recurso resultante\nde la actividad.", COLOR_O_HEADER),
        ("J", None, COLOR_C_BADGE),
        ("K", "Receptor de\nsalida creada", COLOR_C_HEADER),
    ]
    for col_l, text, fill_hex in headers_r3:
        cell = ws[f"{col_l}3"]
        cell.value = text
        cell.font = Font(name="Century Gothic", size=9.0, bold=True, color=COLOR_WHITE_TEXT)
        cell.fill = PatternFill(start_color=fill_hex, end_color=fill_hex, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # 4. Row 4: Process Subtitle
    ws.row_dimensions[4].height = 18.0
    c_sub = ws["B4"]
    c_sub.value = f"Proceso: {project_name}" if project_name else "Proceso"
    c_sub.font = Font(name="Century Gothic", size=10.0, bold=False, color="475569")
    c_sub.alignment = Alignment(horizontal="left", vertical="center")

    # 5. Row 5: Column Headers
    ws.row_dimensions[5].height = 24.75
    headers_r5 = [
        ("B", "PROVEEDORES", COLOR_S_BADGE),
        ("C", None, COLOR_S_HEADER),
        ("D", "ENTRADA", COLOR_I_BADGE),
        ("E", None, COLOR_I_HEADER),
        ("F", "PROCESO", COLOR_P_BADGE),
        ("G", None, COLOR_P_HEADER),
        ("H", "SALIDA", COLOR_O_BADGE),
        ("I", None, COLOR_O_HEADER),
        ("J", "CLIENTE", COLOR_C_BADGE),
        ("K", None, COLOR_C_HEADER),
    ]
    for col_l, text, fill_hex in headers_r5:
        cell = ws[f"{col_l}5"]
        cell.value = text
        cell.font = Font(name="Century Gothic", size=10.0, bold=True, color=COLOR_WHITE_TEXT)
        cell.fill = PatternFill(start_color=fill_hex, end_color=fill_hex, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # 6. Rows 6+: Data Rows (Paso 1.0, 2.0...)
    rows_to_render = list(sipoc_rows) if sipoc_rows else []
    if len(rows_to_render) < 10:
        for i in range(len(rows_to_render) + 1, 13):
            rows_to_render.append({
                "id": str(i),
                "step_num": f"{i}.0",
                "provider": "",
                "input": "",
                "step": "",
                "output": "",
                "customer": "",
            })

    current_r = 6
    for idx, row_data in enumerate(rows_to_render):
        ws.row_dimensions[current_r].height = 48.0
        step_num_val = row_data.get("step_num") or f"{idx+1}.0"
        
        # Clean process text (remove 1.0 prefix if already in text)
        step_text = row_data.get("step") or row_data.get("process") or ""
        if step_text.startswith(step_num_val):
            step_text = step_text[len(step_num_val):].strip()

        vals = [
            ("B", None, COLOR_S_BADGE, "center", True),
            ("C", row_data.get("provider", "") or row_data.get("supplier", ""), "FFFFFF", "left", False),
            ("D", None, COLOR_I_BADGE, "center", False),
            ("E", row_data.get("input", ""), "FFFFFF", "left", False),
            ("F", step_num_val, COLOR_P_BADGE, "center", True),
            ("G", step_text, "FFFFFF", "left", False),
            ("H", None, COLOR_O_BADGE, "center", False),
            ("I", row_data.get("output", ""), "FFFFFF", "left", False),
            ("J", None, COLOR_C_BADGE, "center", False),
            ("K", row_data.get("customer", ""), "FFFFFF", "left", False),
        ]

        for col_l, val, fill_hex, align_h, is_bold in vals:
            cell = ws[f"{col_l}{current_r}"]
            cell.value = val
            cell.font = Font(
                name="Century Gothic",
                size=10.0,
                bold=is_bold,
                color=COLOR_WHITE_TEXT if fill_hex != "FFFFFF" else "17283C"
            )
            if fill_hex != "FFFFFF":
                cell.fill = PatternFill(start_color=fill_hex, end_color=fill_hex, fill_type="solid")
            else:
                cell.fill = PatternFill(start_color="FFFFFF" if idx % 2 == 0 else COLOR_ZEBRA, end_color="FFFFFF" if idx % 2 == 0 else COLOR_ZEBRA, fill_type="solid")
            cell.alignment = Alignment(horizontal=align_h, vertical="center", wrap_text=True)
            cell.border = thin_border

        current_r += 1

    # 7. Customer Requirements Section (Row 18+ in template)
    ws.row_dimensions[current_r].height = 24.0
    req_cols = ["B", "D", "F", "H", "J"]
    for col_l in req_cols:
        cell = ws[f"{col_l}{current_r}"]
        cell.value = "REQUISITOS DEL CLIENTE"
        cell.font = Font(name="Century Gothic", size=10.0, bold=True, color="17283C")
        cell.fill = PatternFill(start_color=COLOR_REQ_BG, end_color=COLOR_REQ_BG, fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    current_r += 1
    ws.row_dimensions[current_r].height = 36.0
    ws.merge_cells(f"B{current_r}:K{current_r}")
    c_req_val = ws[f"B{current_r}"]
    c_req_val.value = customer_requirements if customer_requirements else "Requisitos del Cliente: Cumplimiento de tiempos de respuesta (SLA), integridad de datos en Chronos y confirmación de satisfacción de servicio."
    c_req_val.font = Font(name="Century Gothic", size=9.5, italic=True, color="334155")
    c_req_val.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    c_req_val.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    c_req_val.border = thin_border

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
