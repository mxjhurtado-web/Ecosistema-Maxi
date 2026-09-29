#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Process Narrative Service for TEMIS
Generates corporate procedure manuals in formal Markdown and exports
official Word (.docx) documents strictly matching the 4-table corporate standard
(Seguimiento de SAR 90 dias.docx - Blue #0047C7, Lime Green #98D801, Mint #E2EFD9).
"""

import os
import io
import json
import base64
import logging
from typing import Dict, Any, List, Optional
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

logger = logging.getLogger(__name__)


def set_cell_background(cell, fill_hex: str):
    """Set background color for table cell in DOCX"""
    clean_hex = fill_hex.replace("#", "").upper()
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{clean_hex}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
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
    regs_text = "\n".join([f"- {r}" for r in (legal_framework or ["Políticas Operativas Internas", "Bank Secrecy Act (BSA) Compliance"])])

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
            branches_md = f"\n**Regla de Decisión:**\n" + "\n".join(b_lines)

        substeps_md = ""
        if s.get("sub_steps"):
            substeps_md = "\n" + "\n".join([f"{st}" if st.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "-")) else f"- {st}" for st in s["sub_steps"]])

        steps_md.append(
            f"### {num}.0 {act}\n"
            f"**Responsable:** `{resp}`{sys_str}{chan_str}\n\n"
            f"{desc}{substeps_md}\n"
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
            p = r.get("step") or r.get("process") or "Paso"
            s = r.get("provider") or r.get("supplier") or "-"
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
    keyframes: Optional[List[Dict[str, Any]]] = None,
    mode_label: str = "AS-IS"
) -> io.BytesIO:
    """
    Generate an official corporate DOCX document matching Seguimiento de SAR 90 dias.docx exactly:
    - Table 1: General process overview (Header #0047C7, Labels #E2E2E2)
    - Table 2: Legal Framework (Header #0047C7)
    - Table 3: Description of Activities (Header #98D801, Activity Description with Responsible/Activity/Steps, Record Control with embedded keyframes)
    - Table 4: Validity Control & Stakeholders (Header #98D801, Mint Labels #E2EFD9)
    """
    doc = docx.Document()
    
    # Palette Colors
    COLOR_BLUE_HDR = "0047C7"    # Electric Blue (Tables 1 & 2)
    COLOR_GRAY_LBL = "E2E2E2"    # Light Gray (Table 1 labels)
    COLOR_LIME_HDR = "98D801"    # Lime Green (Tables 3 & 4)
    COLOR_MINT_LBL = "E2EFD9"    # Soft Mint Green (Table 4 stakeholders/labels)

    # Page Margins (0.8 inch)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    title_text = project_name or "Procedimiento Operativo"
    
    # 1. Main Title
    title_p = doc.add_paragraph()
    run_title = title_p.add_run(f"PROCEDIMIENTO: {title_text.upper()}")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(14)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x17, 0x28, 0x3C)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub_p = doc.add_paragraph()
    run_sub = sub_p.add_run(f"Narrativa Oficial de Procedimientos ({mode_label})")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(10.5)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x52, 0x65, 0x7A)
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(8)

    # ==================== TABLE 1: General Process Overview ====================
    t1 = doc.add_table(rows=5, cols=4)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t1.autofit = False

    # Row 0: General process overview Header
    cell_hdr = t1.cell(0, 0)
    for c_idx in range(1, 4):
        cell_hdr.merge(t1.cell(0, c_idx))
    cell_hdr.text = "General process overview"
    set_cell_background(cell_hdr, COLOR_BLUE_HDR)
    p_hdr = cell_hdr.paragraphs[0]
    p_hdr.runs[0].font.bold = True
    p_hdr.runs[0].font.color.rgb = RGBColor(255, 255, 255)
    p_hdr.runs[0].font.name = "Calibri"
    p_hdr.runs[0].font.size = Pt(10)

    # Row 1: Target
    t1.cell(1, 0).text = "Target"
    set_cell_background(t1.cell(1, 0), COLOR_GRAY_LBL)
    t1.cell(1, 0).paragraphs[0].runs[0].font.bold = True
    cell_tgt = t1.cell(1, 1)
    for c_idx in range(2, 4):
        cell_tgt.merge(t1.cell(1, c_idx))
    cell_tgt.text = overview_data.get("target") or "Definir y estandarizar la secuencia operativa del proceso."

    # Row 2: Scope
    t1.cell(2, 0).text = "Scope"
    set_cell_background(t1.cell(2, 0), COLOR_GRAY_LBL)
    t1.cell(2, 0).paragraphs[0].runs[0].font.bold = True
    cell_scp = t1.cell(2, 1)
    for c_idx in range(2, 4):
        cell_scp.merge(t1.cell(2, c_idx))
    cell_scp.text = overview_data.get("scope") or "Aplica para todo el personal y sistemas involucrados en la operación."

    # Row 3: Process Input & Output
    t1.cell(3, 0).text = "Process input"
    set_cell_background(t1.cell(3, 0), COLOR_GRAY_LBL)
    t1.cell(3, 0).paragraphs[0].runs[0].font.bold = True
    t1.cell(3, 1).text = overview_data.get("process_input") or "Solicitudes de clientes y alertas de operación."

    t1.cell(3, 2).text = "Process output"
    set_cell_background(t1.cell(3, 2), COLOR_GRAY_LBL)
    t1.cell(3, 2).paragraphs[0].runs[0].font.bold = True
    t1.cell(3, 3).text = overview_data.get("process_output") or "Trámite concluido, resolución de caso y registro en sistemas."

    # Row 4: Frequency
    t1.cell(4, 0).text = "Frequency"
    set_cell_background(t1.cell(4, 0), COLOR_GRAY_LBL)
    t1.cell(4, 0).paragraphs[0].runs[0].font.bold = True
    cell_frq = t1.cell(4, 1)
    for c_idx in range(2, 4):
        cell_frq.merge(t1.cell(4, c_idx))
    cell_frq.text = overview_data.get("frequency") or "Siempre que la operación lo requiera."

    # Styling Table 1 cells & widths
    t1_widths = [Inches(1.5), Inches(2.1), Inches(1.5), Inches(2.1)]
    for row in t1.rows:
        for c_idx, cell in enumerate(row.cells):
            set_cell_margins(cell, 70, 70, 100, 100)
            if cell.paragraphs[0].runs:
                cell.paragraphs[0].runs[0].font.name = "Calibri"
                cell.paragraphs[0].runs[0].font.size = Pt(9.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ==================== TABLE 2: Legal Framework ====================
    regs = legal_framework or ["Bank Secrecy Act (BSA)", "BSA Compliance", "Políticas Operativas Internas"]
    t2 = doc.add_table(rows=len(regs) + 1, cols=2)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t2.autofit = False
    
    # Header
    c2_hdr = t2.cell(0, 0)
    c2_hdr.merge(t2.cell(0, 1))
    c2_hdr.text = "Legal Framework"
    set_cell_background(c2_hdr, COLOR_BLUE_HDR)
    c2_hdr.paragraphs[0].runs[0].font.bold = True
    c2_hdr.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
    c2_hdr.paragraphs[0].runs[0].font.name = "Calibri"
    c2_hdr.paragraphs[0].runs[0].font.size = Pt(10)

    for r_idx, reg in enumerate(regs, start=1):
        t2.cell(r_idx, 0).text = reg
        t2.cell(r_idx, 1).text = ""

    for row in t2.rows:
        row.cells[0].width = Inches(4.5)
        row.cells[1].width = Inches(2.7)
        for cell in row.cells:
            set_cell_margins(cell, 60, 60, 100, 100)
            if cell.paragraphs[0].runs:
                cell.paragraphs[0].runs[0].font.name = "Calibri"
                cell.paragraphs[0].runs[0].font.size = Pt(9)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ==================== TABLE 3: Description of Activities & Record Control ====================
    t3 = doc.add_table(rows=len(steps_data) + 1, cols=3)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    t3.autofit = False

    # Headers
    headers_t3 = ["N°", "Activity Description", "Record Control"]
    for c_idx, h_text in enumerate(headers_t3):
        c = t3.cell(0, c_idx)
        c.text = h_text
        set_cell_background(c, COLOR_LIME_HDR)
        c.paragraphs[0].runs[0].font.bold = True
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        c.paragraphs[0].runs[0].font.name = "Calibri"
        c.paragraphs[0].runs[0].font.size = Pt(10)

    # Keyframes indexing helper
    kf_list = keyframes or []
    
    for s_idx, s in enumerate(steps_data, start=1):
        row = t3.rows[s_idx]
        num_str = str(s.get("step_number") or s_idx)
        
        # Col 0: N°
        c0 = row.cells[0]
        c0.text = num_str
        c0.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c0.paragraphs[0].runs[0].font.bold = True
        c0.paragraphs[0].runs[0].font.name = "Calibri"

        # Col 1: Structured Activity Description matching SAR 90 dias
        c1 = row.cells[1]
        c1.text = ""  # Clear default empty paragraph
        
        resp = s.get("responsible") or "Analista Operativo"
        act_name = s.get("activity_name") or "Actividad Operativa"
        desc = s.get("activity_description") or ""
        sub_steps = s.get("sub_steps") or []

        # 1. Responsible:
        p_resp = c1.paragraphs[0]
        r_resp_lbl = p_resp.add_run("Responsible:\n")
        r_resp_lbl.font.bold = True
        r_resp_lbl.font.name = "Calibri"
        r_resp_lbl.font.size = Pt(9.5)
        r_resp_val = p_resp.add_run(f"{resp}\n\n")
        r_resp_val.font.name = "Calibri"
        r_resp_val.font.size = Pt(9.5)

        # 2. Activity:
        p_act = c1.add_paragraph()
        r_act_lbl = p_act.add_run("Activity:\n")
        r_act_lbl.font.bold = True
        r_act_lbl.font.name = "Calibri"
        r_act_lbl.font.size = Pt(9.5)
        r_act_val = p_act.add_run(f"{act_name}\n\n")
        r_act_val.font.name = "Calibri"
        r_act_val.font.size = Pt(9.5)

        # 3. Activity description:
        p_desc = c1.add_paragraph()
        r_desc_lbl = p_desc.add_run("Activity description:\n")
        r_desc_lbl.font.bold = True
        r_desc_lbl.font.name = "Calibri"
        r_desc_lbl.font.size = Pt(9.5)

        if desc:
            p_desc_txt = c1.add_paragraph()
            r_desc_txt = p_desc_txt.add_run(desc)
            r_desc_txt.font.name = "Calibri"
            r_desc_txt.font.size = Pt(9)
            p_desc_txt.paragraph_format.space_after = Pt(4)

        # Sub-steps (numbered 1., 2., 3.)
        if sub_steps:
            for st in sub_steps:
                p_st = c1.add_paragraph()
                r_st = p_st.add_run(st if st.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "-")) else f"• {st}")
                r_st.font.name = "Calibri"
                r_st.font.size = Pt(9)
                p_st.paragraph_format.space_after = Pt(2)

        # Decision rule (Sí / No)
        if s.get("is_decision") and s.get("decision_branches"):
            p_dec = c1.add_paragraph()
            p_dec.paragraph_format.space_before = Pt(4)
            p_dec.paragraph_format.space_after = Pt(2)
            q_text = s.get("decision_question") or f"¿El paso '{act_name}' fue exitoso?"
            r_q = p_dec.add_run(f"{q_text}\n")
            r_q.font.bold = True
            r_q.font.name = "Calibri"
            r_q.font.size = Pt(9)
            
            for b in s["decision_branches"]:
                lbl = b.get("condition_label", "Opción")
                dest = b.get("target_activity_name") or f"Actividad {b.get('target_activity_number', '')}"
                p_b = c1.add_paragraph()
                r_b = p_b.add_run(f"{lbl}: Continuar con la actividad: {dest}.")
                r_b.font.name = "Calibri"
                r_b.font.size = Pt(9)
                p_b.paragraph_format.space_after = Pt(2)

        # Col 2: Record Control (Evidence & Embedded Keyframes)
        c2 = row.cells[2]
        c2.text = ""
        
        # Check for keyframe image to embed
        attached_img_name = s.get("attached_screenshot", "") or s.get("record_control", "")
        img_bytes = None
        img_filename = ""

        # Try finding in keyframes list
        for k in kf_list:
            k_fn = k.get("filename", "")
            if (attached_img_name and attached_img_name in k_fn) or (f"frame_{s_idx:03d}" in k_fn) or (len(kf_list) == len(steps_data) and kf_list.index(k) == s_idx - 1):
                img_filename = k_fn
                if k.get("data_uri") and "base64," in k["data_uri"]:
                    try:
                        b64_data = k["data_uri"].split("base64,")[1]
                        img_bytes = base64.b64decode(b64_data)
                    except Exception as e:
                        logger.warning(f"Error decoding base64 image {k_fn}: {e}")
                elif k.get("path") and os.path.exists(k["path"]):
                    try:
                        with open(k["path"], "rb") as f:
                            img_bytes = f.read()
                    except Exception as e:
                        logger.warning(f"Error reading image path {k['path']}: {e}")
                break

        # If image found, embed in cell
        if img_bytes:
            try:
                p_img = c2.paragraphs[0]
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_img = p_img.add_run()
                r_img.add_picture(io.BytesIO(img_bytes), width=Inches(2.4))
                
                p_cap = c2.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_cap = p_cap.add_run(f"Figura {s_idx}: {s.get('record_control') or img_filename or 'Evidencia del proceso'}")
                r_cap.font.size = Pt(8)
                r_cap.font.italic = True
                r_cap.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
            except Exception as pic_err:
                logger.warning(f"Could not embed picture in DOCX: {pic_err}")
                p_rec = c2.paragraphs[0]
                p_rec.add_run(s.get("record_control") or "1. Registro / Log")
        else:
            p_rec = c2.paragraphs[0]
            rec_text = s.get("record_control") or "1."
            p_rec.add_run(rec_text)
            p_rec.runs[0].font.name = "Calibri"
            p_rec.runs[0].font.size = Pt(9)

    # Set Column Widths for Table 3
    for row in t3.rows:
        row.cells[0].width = Inches(0.4)
        row.cells[1].width = Inches(4.3)
        row.cells[2].width = Inches(2.5)
        for cell in row.cells:
            set_cell_margins(cell, 70, 70, 90, 90)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # ==================== TABLE 4: Validity Control & Stakeholders ====================
    val = validity_data or {}
    t4 = doc.add_table(rows=9, cols=4)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    t4.autofit = False

    # Row 0: Validity Control Header
    c4_hdr1 = t4.cell(0, 0)
    for c_idx in range(1, 4):
        c4_hdr1.merge(t4.cell(0, c_idx))
    c4_hdr1.text = "Validity Control"
    set_cell_background(c4_hdr1, COLOR_LIME_HDR)
    p_vhdr = c4_hdr1.paragraphs[0]
    p_vhdr.runs[0].font.bold = True
    p_vhdr.runs[0].font.color.rgb = RGBColor(255, 255, 255)
    p_vhdr.runs[0].font.name = "Calibri"
    p_vhdr.runs[0].font.size = Pt(10)

    # Row 1: Code & Version
    t4.cell(1, 0).text = "Code"
    set_cell_background(t4.cell(1, 0), COLOR_MINT_LBL)
    t4.cell(1, 0).paragraphs[0].runs[0].font.bold = True
    t4.cell(1, 1).text = val.get("code") or "PRJ-01"
    t4.cell(1, 2).text = "Version"
    set_cell_background(t4.cell(1, 2), COLOR_MINT_LBL)
    t4.cell(1, 2).paragraphs[0].runs[0].font.bold = True
    t4.cell(1, 3).text = val.get("version") or "00"

    # Row 2: Dates
    t4.cell(2, 0).text = "Elaboration date"
    set_cell_background(t4.cell(2, 0), COLOR_MINT_LBL)
    t4.cell(2, 0).paragraphs[0].runs[0].font.bold = True
    t4.cell(2, 1).text = val.get("elaboration_date") or ""
    t4.cell(2, 2).text = "Approval date"
    set_cell_background(t4.cell(2, 2), COLOR_MINT_LBL)
    t4.cell(2, 2).paragraphs[0].runs[0].font.bold = True
    t4.cell(2, 3).text = val.get("approval_date") or ""

    # Row 3: Stakeholders Header
    c4_hdr2 = t4.cell(3, 0)
    for c_idx in range(1, 4):
        c4_hdr2.merge(t4.cell(3, c_idx))
    c4_hdr2.text = "Stakeholders"
    set_cell_background(c4_hdr2, COLOR_MINT_LBL)
    c4_hdr2.paragraphs[0].runs[0].font.bold = True
    c4_hdr2.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x17, 0x28, 0x3C)
    c4_hdr2.paragraphs[0].runs[0].font.name = "Calibri"

    # Row 4: Developed by & Area
    t4.cell(4, 0).text = "Developed by"
    set_cell_background(t4.cell(4, 0), COLOR_MINT_LBL)
    t4.cell(4, 0).paragraphs[0].runs[0].font.bold = True
    t4.cell(4, 1).text = val.get("developed_by") or "Área de Procesos"
    t4.cell(4, 2).text = "Responsible area"
    set_cell_background(t4.cell(4, 2), COLOR_MINT_LBL)
    t4.cell(4, 2).paragraphs[0].runs[0].font.bold = True
    t4.cell(4, 3).text = val.get("responsible_area") or "Operaciones"

    # Row 5: Reviewed by & Dept
    t4.cell(5, 0).text = "Reviewed by"
    set_cell_background(t4.cell(5, 0), COLOR_MINT_LBL)
    t4.cell(5, 0).paragraphs[0].runs[0].font.bold = True
    t4.cell(5, 1).text = val.get("reviewed_by") or "Líder de Calidad / QA"
    t4.cell(5, 2).text = "Responsible department"
    set_cell_background(t4.cell(5, 2), COLOR_MINT_LBL)
    t4.cell(5, 2).paragraphs[0].runs[0].font.bold = True
    t4.cell(5, 3).text = val.get("responsible_department") or "Cumplimiento"

    # Row 6: Informed areas
    t4.cell(6, 0).text = "Informed areas"
    set_cell_background(t4.cell(6, 0), COLOR_MINT_LBL)
    t4.cell(6, 0).paragraphs[0].runs[0].font.bold = True
    c4_inf = t4.cell(6, 1)
    for c_idx in range(2, 4):
        c4_inf.merge(t4.cell(6, c_idx))
    c4_inf.text = val.get("informed_areas") or "Quality Assurance, Internal Audit, Compliance"

    # Row 7: Approved by Header
    c4_hdr3 = t4.cell(7, 0)
    for c_idx in range(1, 4):
        c4_hdr3.merge(t4.cell(7, c_idx))
    c4_hdr3.text = "Approved by"
    set_cell_background(c4_hdr3, COLOR_MINT_LBL)
    c4_hdr3.paragraphs[0].runs[0].font.bold = True
    c4_hdr3.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x17, 0x28, 0x3C)

    # Row 8: Approver Signature Slots
    c4_app1 = t4.cell(8, 0)
    c4_app1.merge(t4.cell(8, 1))
    c4_app1.text = val.get("approved_by") or "Director de Operaciones & Tecnología"
    c4_app2 = t4.cell(8, 2)
    c4_app2.merge(t4.cell(8, 3))
    c4_app2.text = val.get("approved_by_secondary") or "Director de Cumplimiento / BSA"

    # Widths for Table 4
    t4_widths = [Inches(1.5), Inches(2.1), Inches(1.5), Inches(2.1)]
    for row in t4.rows:
        for c_idx, cell in enumerate(row.cells):
            set_cell_margins(cell, 60, 60, 90, 90)
            if cell.paragraphs[0].runs:
                cell.paragraphs[0].runs[0].font.name = "Calibri"
                cell.paragraphs[0].runs[0].font.size = Pt(9)

    # Save to BytesIO buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
