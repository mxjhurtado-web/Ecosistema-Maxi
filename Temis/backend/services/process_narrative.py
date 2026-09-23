#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Process Narrative Service for TEMIS
Generates corporate procedure manuals in formal Markdown and exports
official Word (.docx) documents matching the 4-table corporate standard.
"""

import os
import io
import json
import logging
from typing import Dict, Any, List, Optional
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

logger = logging.getLogger(__name__)


def set_cell_background(cell, fill_hex: str):
    """Set background color for table cell in DOCX"""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex.replace("#", ""))
    tc_pr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set cell padding in DXA"""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tc_mar.append(node)
    tc_pr.append(tc_mar)


def generate_process_narrative_markdown(
    project_name: str,
    overview_data: Dict[str, Any],
    steps_data: List[Dict[str, Any]],
    legal_framework: Optional[List[str]] = None,
    validity_data: Optional[Dict[str, Any]] = None,
    clarification_points: Optional[List[Dict[str, Any]]] = None,
    sipoc_rows: Optional[List[Dict[str, Any]]] = None,
    mode_label: str = "AS-IS"
) -> str:
    """Generate Markdown corporate narrative according to 4-table standard"""
    title = project_name or "Manual de Procedimientos & Narrativa Oficial"
    target = overview_data.get("target") or "Definir y estandarizar la secuencia operativa del proceso."
    scope = overview_data.get("scope") or "Aplica para las áreas y roles involucrados en el proceso."
    p_input = overview_data.get("process_input") or "Solicitudes y transacciones de clientes."
    p_output = overview_data.get("process_output") or "Resolución del trámite y registro en sistemas."
    freq = overview_data.get("frequency") or "Siempre que la operación lo requiera."

    # Legal framework text
    regs_text = "\n".join([f"- {r}" for r in (legal_framework or ["Políticas Operativas Internas", "Bank Secrecy Act (BSA)"])])

    # Steps markdown
    steps_md = []
    for s in steps_data:
        num = s.get("step_number") or len(steps_md) + 1
        resp = s.get("responsible") or "Operación"
        act = s.get("activity_name") or "Actividad"
        desc = s.get("activity_description") or ""
        sys_str = f" a través del sistema **{s['attached_system']}**" if s.get("attached_system") else ""
        chan_str = f" por el canal **{s['attached_channel']}**" if s.get("attached_channel") else ""
        rec_str = f"\n> **Control de Registro / Evidencia:** {s['record_control']}" if s.get("record_control") else ""

        branches_md = ""
        if s.get("is_decision") and s.get("decision_branches"):
            b_lines = []
            for b in s["decision_branches"]:
                lbl = b.get("condition_label", "Opción")
                dest = b.get("target_activity_name") or f"Paso {b.get('target_activity_number', '')}"
                b_lines.append(f"  - **Condición '{lbl}':** Continuar con *{dest}*.")
            branches_md = f"\n**Ramificaciones de Decisión:**\n" + "\n".join(b_lines)

        steps_md.append(
            f"### {num}.0 {act}\n"
            f"**Responsable:** `{resp}`{sys_str}{chan_str}\n\n"
            f"{desc}\n"
            f"{branches_md}"
            f"{rec_str}"
        )

    steps_combined = "\n\n---\n\n".join(steps_md)

    # Clarifications
    clarif_md = ""
    if clarification_points:
        c_lines = []
        for c in clarification_points:
            title_c = c.get("title") or "Punto de Aclaración"
            cont_c = c.get("content") or ""
            c_lines.append(f"> ⚠️ **[PENDIENTE DE ACLARAR CON EL CLIENTE] {title_c}:** {cont_c}")
        clarif_md = "\n\n## 5. Puntos Pendientes de Aclaración con el Cliente\n" + "\n\n".join(c_lines)

    # SIPOC Summary
    sipoc_md = ""
    if sipoc_rows:
        s_lines = []
        for r in sipoc_rows:
            p = r.get("step") or "Paso"
            s = r.get("provider") or "-"
            i = r.get("input") or "-"
            o = r.get("output") or "-"
            c = r.get("customer") or "-"
            s_lines.append(f"| {p} | {s} | {i} | {o} | {c} |")
        sipoc_md = (
            "\n\n## 6. Matriz SIPOC de Transformación\n"
            "| Paso (P) | Proveedor (S) | Entrada (I) | Salida (O) | Cliente (C) |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n" + "\n".join(s_lines)
        )

    # Validity
    val = validity_data or {}
    dev_by = val.get("developed_by") or "Área de Procesos"
    rev_by = val.get("reviewed_by") or "Líder de Calidad"
    app_by = val.get("approved_by") or "Dueño del Proceso"
    version = val.get("version") or "00"
    code = val.get("code") or "PRJ-01"

    narrative = f"""# Manual de Procedimientos & Narrativa Oficial ({mode_label})
# {title}

**Código:** `{code}` | **Versión:** `{version}` | **Modalidad:** `{mode_label}`

---

## 1. Visión General del Proceso (General Process Overview)
- **Objetivo (Target):** {target}
- **Alcance (Scope):** {scope}
- **Entradas (Process Input):** {p_input}
- **Salidas (Process Output):** {p_output}
- **Frecuencia (Frequency):** {freq}

---

## 2. Marco Normativo y Regulatorio (Legal Framework)
{regs_text}

---

## 3. Narrativa Operativa Paso a Paso (Activity Description & Record Control)

{steps_combined}
{clarif_md}
{sipoc_md}

---

## 4. Control de Vigencia y Firmas de Aprobación (Validity Control & Stakeholders)
- **Elaborado por:** {dev_by}
- **Revisado por:** {rev_by}
- **Aprobado por:** {app_by}
"""
    return narrative.strip()


def export_narrative_to_docx(
    project_name: str,
    overview_data: Dict[str, Any],
    steps_data: List[Dict[str, Any]],
    legal_framework: Optional[List[str]] = None,
    validity_data: Optional[Dict[str, Any]] = None,
    clarification_points: Optional[List[Dict[str, Any]]] = None,
    mode_label: str = "AS-IS"
) -> io.BytesIO:
    """
    Generate an official corporate DOCX document matching the exact 4-table standard.
    """
    doc = docx.Document()
    
    # Page Margins (Normal 1 inch)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    title_text = project_name or "Procedimiento Operativo"
    
    # Title & Subtitle
    title_p = doc.add_paragraph()
    run_title = title_p.add_run(f"PROCEDIMIENTO: {title_text.upper()}")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(14)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(23, 40, 60)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub_p = doc.add_paragraph()
    run_sub = sub_p.add_run(f"Narrativa Oficial de Procesos ({mode_label})")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(11)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(82, 101, 122)
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()  # Spacing

    # ==================== TABLE 1: General Process Overview ====================
    t1 = doc.add_table(rows=5, cols=4)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t1.autofit = False

    # Header Row
    cell_hdr = t1.cell(0, 0)
    for c_idx in range(1, 4):
        cell_hdr.merge(t1.cell(0, c_idx))
    cell_hdr.text = "General process overview"
    set_cell_background(cell_hdr, "#1e5a9a")
    cell_hdr.paragraphs[0].runs[0].font.bold = True
    cell_hdr.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
    cell_hdr.paragraphs[0].runs[0].font.name = "Calibri"
    cell_hdr.paragraphs[0].runs[0].font.size = Pt(10)

    # Row 2: Target
    t1.cell(1, 0).text = "Target"
    set_cell_background(t1.cell(1, 0), "#f1f5f9")
    t1.cell(1, 0).paragraphs[0].runs[0].font.bold = True
    cell_tgt = t1.cell(1, 1)
    for c_idx in range(2, 4):
        cell_tgt.merge(t1.cell(1, c_idx))
    cell_tgt.text = overview_data.get("target") or "Definir y estandarizar la secuencia operativa del proceso."

    # Row 3: Scope
    t1.cell(2, 0).text = "Scope"
    set_cell_background(t1.cell(2, 0), "#f1f5f9")
    t1.cell(2, 0).paragraphs[0].runs[0].font.bold = True
    cell_scp = t1.cell(2, 1)
    for c_idx in range(2, 4):
        cell_scp.merge(t1.cell(2, c_idx))
    cell_scp.text = overview_data.get("scope") or "Aplica para todo el personal y sistemas involucrados."

    # Row 4: Process Input & Output
    t1.cell(3, 0).text = "Process input"
    set_cell_background(t1.cell(3, 0), "#f1f5f9")
    t1.cell(3, 0).paragraphs[0].runs[0].font.bold = True
    t1.cell(3, 1).text = overview_data.get("process_input") or "Solicitudes de clientes."

    t1.cell(3, 2).text = "Process output"
    set_cell_background(t1.cell(3, 2), "#f1f5f9")
    t1.cell(3, 2).paragraphs[0].runs[0].font.bold = True
    t1.cell(3, 3).text = overview_data.get("process_output") or "Trámite concluido y registrado."

    # Row 5: Frequency
    t1.cell(4, 0).text = "Frequency"
    set_cell_background(t1.cell(4, 0), "#f1f5f9")
    t1.cell(4, 0).paragraphs[0].runs[0].font.bold = True
    cell_frq = t1.cell(4, 1)
    for c_idx in range(2, 4):
        cell_frq.merge(t1.cell(4, c_idx))
    cell_frq.text = overview_data.get("frequency") or "Siempre que la operación lo requiera."

    # Styling Table 1 cells
    for row in t1.rows:
        for cell in row.cells:
            set_cell_margins(cell, 80, 80, 120, 120)
            if cell.paragraphs[0].runs:
                cell.paragraphs[0].runs[0].font.name = "Calibri"
                cell.paragraphs[0].runs[0].font.size = Pt(9.5)

    doc.add_paragraph()  # Spacing

    # ==================== TABLE 2: Legal Framework ====================
    regs = legal_framework or ["Políticas Internas", "Bank Secrecy Act (BSA) Compliance"]
    t2 = doc.add_table(rows=len(regs) + 1, cols=2)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Header
    c2_hdr = t2.cell(0, 0)
    c2_hdr.merge(t2.cell(0, 1))
    c2_hdr.text = "Legal Framework"
    set_cell_background(c2_hdr, "#1e5a9a")
    c2_hdr.paragraphs[0].runs[0].font.bold = True
    c2_hdr.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
    c2_hdr.paragraphs[0].runs[0].font.name = "Calibri"

    for r_idx, reg in enumerate(regs, start=1):
        t2.cell(r_idx, 0).text = reg
        t2.cell(r_idx, 1).text = ""

    for row in t2.rows:
        for cell in row.cells:
            set_cell_margins(cell, 60, 60, 100, 100)
            if cell.paragraphs[0].runs:
                cell.paragraphs[0].runs[0].font.name = "Calibri"
                cell.paragraphs[0].runs[0].font.size = Pt(9)

    doc.add_paragraph()  # Spacing

    # ==================== TABLE 3: Activity Description & Record Control ====================
    t3 = doc.add_table(rows=len(steps_data) + 1, cols=3)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Headers
    headers_t3 = ["N°", "Activity Description", "Record Control"]
    for c_idx, h_text in enumerate(headers_t3):
        c = t3.cell(0, c_idx)
        c.text = h_text
        set_cell_background(c, "#1e5a9a")
        c.paragraphs[0].runs[0].font.bold = True
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        c.paragraphs[0].runs[0].font.name = "Calibri"
        c.paragraphs[0].runs[0].font.size = Pt(10)

    for s_idx, s in enumerate(steps_data, start=1):
        row = t3.rows[s_idx]
        num_str = str(s.get("step_number") or s_idx)
        row.cells[0].text = num_str
        row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Detailed Description
        resp = s.get("responsible") or "Operación"
        act_name = s.get("activity_name") or "Actividad"
        desc = s.get("activity_description") or ""
        sys_str = f" (Sistema: {s['attached_system']})" if s.get("attached_system") else ""
        chan_str = f" [Canal: {s['attached_channel']}]" if s.get("attached_channel") else ""

        branches_txt = ""
        if s.get("is_decision") and s.get("decision_branches"):
            b_list = []
            for b in s["decision_branches"]:
                lbl = b.get("condition_label", "Opción")
                dest = b.get("target_activity_name") or f"Actividad {b.get('target_activity_number', '')}"
                b_list.append(f"  • {lbl}: Continuar con '{dest}'")
            branches_txt = "\n\nRamificaciones:\n" + "\n".join(b_list)

        full_desc = f"Responsible:\n{resp}\n\nActivity:\n{act_name}{sys_str}{chan_str}\n\nActivity description:\n{desc}{branches_txt}"
        row.cells[1].text = full_desc

        # Record control
        row.cells[2].text = s.get("record_control") or "No aplica."

    # Column widths
    for row in t3.rows:
        row.cells[0].width = Inches(0.6)
        row.cells[1].width = Inches(4.6)
        row.cells[2].width = Inches(1.8)
        for cell in row.cells:
            set_cell_margins(cell, 80, 80, 100, 100)
            if cell.paragraphs[0].runs:
                cell.paragraphs[0].runs[0].font.name = "Calibri"
                cell.paragraphs[0].runs[0].font.size = Pt(9)

    doc.add_paragraph()  # Spacing

    # ==================== TABLE 4: Validity Control & Stakeholders ====================
    val = validity_data or {}
    t4 = doc.add_table(rows=9, cols=4)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Row 1: Validity Control Header
    c4_hdr1 = t4.cell(0, 0)
    for c_idx in range(1, 4):
        c4_hdr1.merge(t4.cell(0, c_idx))
    c4_hdr1.text = "Validity Control"
    set_cell_background(c4_hdr1, "#1e5a9a")
    c4_hdr1.paragraphs[0].runs[0].font.bold = True
    c4_hdr1.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    # Row 2: Code & Version
    t4.cell(1, 0).text = "Code"
    set_cell_background(t4.cell(1, 0), "#f1f5f9")
    t4.cell(1, 1).text = val.get("code") or "PRJ-01"
    t4.cell(1, 2).text = "Version"
    set_cell_background(t4.cell(1, 2), "#f1f5f9")
    t4.cell(1, 3).text = val.get("version") or "00"

    # Row 3: Dates
    t4.cell(2, 0).text = "Elaboration date"
    set_cell_background(t4.cell(2, 0), "#f1f5f9")
    t4.cell(2, 1).text = val.get("elaboration_date") or ""
    t4.cell(2, 2).text = "Approval date"
    set_cell_background(t4.cell(2, 2), "#f1f5f9")
    t4.cell(2, 3).text = val.get("approval_date") or ""

    # Row 4: Stakeholders Header
    c4_hdr2 = t4.cell(3, 0)
    for c_idx in range(1, 4):
        c4_hdr2.merge(t4.cell(3, c_idx))
    c4_hdr2.text = "Stakeholders"
    set_cell_background(c4_hdr2, "#1e5a9a")
    c4_hdr2.paragraphs[0].runs[0].font.bold = True
    c4_hdr2.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    # Row 5: Developed by & Area
    t4.cell(4, 0).text = "Developed by"
    set_cell_background(t4.cell(4, 0), "#f1f5f9")
    t4.cell(4, 1).text = val.get("developed_by") or "Área de Procesos"
    t4.cell(4, 2).text = "Responsible area"
    set_cell_background(t4.cell(4, 2), "#f1f5f9")
    t4.cell(4, 3).text = val.get("responsible_area") or ""

    # Row 6: Reviewed by & Dept
    t4.cell(5, 0).text = "Reviewed by"
    set_cell_background(t4.cell(5, 0), "#f1f5f9")
    t4.cell(5, 1).text = val.get("reviewed_by") or "Calidad / QA"
    t4.cell(5, 2).text = "Responsible department"
    set_cell_background(t4.cell(5, 2), "#f1f5f9")
    t4.cell(5, 3).text = val.get("responsible_department") or ""

    # Row 7: Informed areas
    t4.cell(6, 0).text = "Informed areas"
    set_cell_background(t4.cell(6, 0), "#f1f5f9")
    c4_inf = t4.cell(6, 1)
    for c_idx in range(2, 4):
        c4_inf.merge(t4.cell(6, c_idx))
    c4_inf.text = val.get("informed_areas") or "Quality Assurance, Internal Audit, Compliance"

    # Row 8: Approved by Header
    c4_hdr3 = t4.cell(7, 0)
    for c_idx in range(1, 4):
        c4_hdr3.merge(t4.cell(7, c_idx))
    c4_hdr3.text = "Approved by"
    set_cell_background(c4_hdr3, "#f1f5f9")
    c4_hdr3.paragraphs[0].runs[0].font.bold = True

    # Row 9: Approver Name
    c4_app = t4.cell(8, 0)
    for c_idx in range(1, 4):
        c4_app.merge(t4.cell(8, c_idx))
    c4_app.text = val.get("approved_by") or "Director de Operaciones & Tecnología"

    for row in t4.rows:
        for cell in row.cells:
            set_cell_margins(cell, 60, 60, 100, 100)
            if cell.paragraphs[0].runs:
                cell.paragraphs[0].runs[0].font.name = "Calibri"
                cell.paragraphs[0].runs[0].font.size = Pt(9)

    # Save to BytesIO buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
