import os
import copy
import io
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

def populate_docx_from_template(
    template_path: str,
    project_name: str,
    overview_data: dict,
    steps_data: list,
    legal_framework: list = None,
    validity_data: dict = None,
    clarification_points: list = None,
    keyframes: list = None,
    mode_label: str = "AS-IS"
) -> io.BytesIO:
    doc = docx.Document(template_path)
    
    # Table 0: General Process Overview
    t0 = doc.tables[0]
    
    replacements_t0 = {
        "{{TARGET}}": overview_data.get("target") or "Definir y estandarizar la secuencia operativa del proceso.",
        "{{SCOPE}}": overview_data.get("scope") or "Aplica para todo el personal y sistemas involucrados en la operación.",
        "{{PROCESS_INPUT}}": overview_data.get("process_input") or "Solicitudes de clientes y alertas de operación.",
        "{{PROCESS_OUTPUT}}": overview_data.get("process_output") or "Trámite concluido, resolución de caso y registro en sistemas.",
        "{{FREQUENCY}}": overview_data.get("frequency") or "Siempre que la operación lo requiera."
    }
    
    for row in t0.rows:
        for cell in row.cells:
            for tag, val in replacements_t0.items():
                if tag in cell.text:
                    for p in cell.paragraphs:
                        if tag in p.text:
                            # Replace run text cleanly
                            for r in p.runs:
                                if tag in r.text:
                                    r.text = r.text.replace(tag, val)
                            if tag in p.text: # fallback if tag was split across runs
                                p.text = p.text.replace(tag, val)
                                if p.runs:
                                    p.runs[0].font.name = "Poppins"
                                    p.runs[0].font.size = Pt(9)
                                    p.runs[0].font.color.rgb = RGBColor(0x2A, 0x2A, 0x2A)

    # Table 1: Legal Framework
    t1 = doc.tables[1]
    regs = legal_framework or [
        {"name": "Bank Secrecy Act (BSA)", "applies": "Aplica"},
        {"name": "BSA Compliance", "applies": "Aplica"}
    ]
    # Normalize regs to list of dicts or strings
    norm_regs = []
    for r in regs:
        if isinstance(r, dict):
            norm_regs.append(r)
        elif isinstance(r, str):
            norm_regs.append({"name": r, "applies": "Aplica"})
            
    # Keep row 0 (Header), template has rows 1 and 2
    # Adjust number of rows
    while len(t1.rows) - 1 < len(norm_regs):
        # clone last row
        new_tr = copy.deepcopy(t1.rows[1]._tr)
        t1._tbl.append(new_tr)
        
    while len(t1.rows) - 1 > max(len(norm_regs), 1):
        # remove extra row
        tr = t1.rows[-1]._tr
        t1._tbl.remove(tr)

    for idx, reg_info in enumerate(norm_regs, start=1):
        if idx < len(t1.rows):
            row = t1.rows[idx]
            # Col 0: Framework Name
            row.cells[0].text = reg_info.get("name", "")
            if row.cells[0].paragraphs[0].runs:
                r0 = row.cells[0].paragraphs[0].runs[0]
                r0.font.name = "Poppins"
                r0.font.size = Pt(9)
            # Col 1: Applies
            row.cells[1].text = reg_info.get("applies", "Aplica")
            if row.cells[1].paragraphs[0].runs:
                r1 = row.cells[1].paragraphs[0].runs[0]
                r1.font.name = "Poppins"
                r1.font.size = Pt(9)

    # Table 2: Activity Description & Record Control
    t2 = doc.tables[2]
    num_steps = len(steps_data)
    
    # We use row 1 as template row
    template_tr = copy.deepcopy(t2.rows[1]._tr)
    
    # Ensure t2 has exactly 1 header row + num_steps rows
    while len(t2.rows) - 1 < num_steps:
        new_tr = copy.deepcopy(template_tr)
        t2._tbl.append(new_tr)
        
    while len(t2.rows) - 1 > max(num_steps, 1):
        tr = t2.rows[-1]._tr
        t2._tbl.remove(tr)

    kf_list = keyframes or []
    
    for s_idx, step in enumerate(steps_data, start=1):
        if s_idx >= len(t2.rows):
            break
        row = t2.rows[s_idx]
        
        # Col 0: Step Number
        c0 = row.cells[0]
        c0.text = str(step.get("step_number") or s_idx)
        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if p0.runs:
            p0.runs[0].font.name = "Poppins"
            p0.runs[0].font.size = Pt(9)
            p0.runs[0].font.bold = True
            
        # Col 1: Activity Description
        c1 = row.cells[1]
        c1.text = "" # Clear
        
        resp = step.get("responsible") or "Operación"
        act_name = step.get("activity_name") or "Actividad"
        desc = step.get("activity_description") or ""
        sub_steps = step.get("sub_steps") or []
        
        # Responsible
        p_resp_lbl = c1.paragraphs[0]
        r_resp_lbl = p_resp_lbl.add_run("Responsible:\n")
        r_resp_lbl.font.bold = True
        r_resp_lbl.font.name = "Poppins"
        r_resp_lbl.font.size = Pt(9)
        r_resp_val = p_resp_lbl.add_run(f"{resp}\n\n")
        r_resp_val.font.name = "Poppins"
        r_resp_val.font.size = Pt(9)
        p_resp_lbl.paragraph_format.space_after = Pt(2)
        
        # Activity
        p_act_lbl = c1.add_paragraph()
        r_act_lbl = p_act_lbl.add_run("Activity:\n")
        r_act_lbl.font.bold = True
        r_act_lbl.font.name = "Poppins"
        r_act_lbl.font.size = Pt(9)
        r_act_val = p_act_lbl.add_run(f"{act_name}\n\n")
        r_act_val.font.name = "Poppins"
        r_act_val.font.size = Pt(9)
        p_act_lbl.paragraph_format.space_after = Pt(2)
        
        # Activity Description
        p_desc_lbl = c1.add_paragraph()
        r_desc_lbl = p_desc_lbl.add_run("Activity description:\n")
        r_desc_lbl.font.bold = True
        r_desc_lbl.font.name = "Poppins"
        r_desc_lbl.font.size = Pt(9)
        
        if desc:
            p_desc_val = c1.add_paragraph()
            r_desc_val = p_desc_val.add_run(desc)
            r_desc_val.font.name = "Poppins"
            r_desc_val.font.size = Pt(9)
            p_desc_val.paragraph_format.space_after = Pt(4)
            
        if sub_steps:
            for st in sub_steps:
                p_st = c1.add_paragraph()
                r_st = p_st.add_run(st if st.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "-")) else f"• {st}")
                r_st.font.name = "Poppins"
                r_st.font.size = Pt(9)
                p_st.paragraph_format.space_after = Pt(2)
                
        if step.get("is_decision") and step.get("decision_branches"):
            p_dec = c1.add_paragraph()
            p_dec.paragraph_format.space_before = Pt(4)
            p_dec.paragraph_format.space_after = Pt(2)
            q_text = step.get("decision_question") or f"¿El paso '{act_name}' fue exitoso?"
            r_q = p_dec.add_run(f"{q_text}\n")
            r_q.font.bold = True
            r_q.font.name = "Poppins"
            r_q.font.size = Pt(9)
            
            for b in step["decision_branches"]:
                lbl = b.get("condition_label", "Opción")
                dest = b.get("target_activity_name") or f"Actividad {b.get('target_activity_number', '')}"
                p_b = c1.add_paragraph()
                r_b = p_b.add_run(f"{lbl}: Continuar con la actividad: {dest}.")
                r_b.font.name = "Poppins"
                r_b.font.size = Pt(9)
                p_b.paragraph_format.space_after = Pt(2)

        # Col 2: Record Control (Evidence & Images)
        c2 = row.cells[2]
        c2.text = ""
        
        attached_img_name = step.get("attached_screenshot", "") or step.get("record_control", "")
        img_bytes = None
        img_filename = ""
        
        import base64
        for k in kf_list:
            k_fn = k.get("filename", "")
            if (attached_img_name and attached_img_name in k_fn) or (f"frame_{s_idx:03d}" in k_fn) or (len(kf_list) == len(steps_data) and kf_list.index(k) == s_idx - 1):
                img_filename = k_fn
                if k.get("data_uri") and "base64," in k["data_uri"]:
                    try:
                        b64_data = k["data_uri"].split("base64,")[1]
                        img_bytes = base64.b64decode(b64_data)
                    except Exception:
                        pass
                elif k.get("path") and os.path.exists(k["path"]):
                    try:
                        with open(k["path"], "rb") as f:
                            img_bytes = f.read()
                    except Exception:
                        pass
                break
                
        if img_bytes:
            try:
                p_img = c2.paragraphs[0]
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_img = p_img.add_run()
                r_img.add_picture(io.BytesIO(img_bytes), width=Inches(4.2))
                
                p_cap = c2.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_cap = p_cap.add_run(f"Figura {s_idx}: {step.get('record_control') or img_filename or 'Evidencia del proceso'}")
                r_cap.font.name = "Poppins"
                r_cap.font.size = Pt(8)
                r_cap.font.italic = True
                r_cap.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
            except Exception as e:
                p_rec = c2.paragraphs[0]
                r_rec = p_rec.add_run(step.get("record_control") or "1. Registro / Log")
                r_rec.font.name = "Poppins"
                r_rec.font.size = Pt(9)
        else:
            p_rec = c2.paragraphs[0]
            rec_text = step.get("record_control") or "1."
            r_rec = p_rec.add_run(rec_text)
            r_rec.font.name = "Poppins"
            r_rec.font.size = Pt(9)

    # Table 3: Validity Control & Stakeholders
    t3 = doc.tables[3]
    val = validity_data or {}
    
    replacements_t3 = {
        "{{CODE}}": val.get("code") or "PRJ-01",
        "{{VERSION}}": val.get("version") or "00",
        "{{ELABORATION_DATE}}": val.get("elaboration_date") or "",
        "{{APPROVAL_DATE}}": val.get("approval_date") or "",
        "{{DEVELOPED_BY}}": val.get("developed_by") or "Área de Procesos",
        "{{RESPONSIBLE_AREA}}": val.get("responsible_area") or "Operaciones",
        "{{REVIEWED_BY}}": val.get("reviewed_by") or "Líder de Calidad",
        "{{RESPONSIBLE_DEPARTMENT}}": val.get("responsible_department") or "Cumplimiento",
        "{{INFORMED_AREAS}}": val.get("informed_areas") or "Quality Assurance, Internal Audit, Compliance"
    }
    
    for row in t3.rows:
        for cell in row.cells:
            for tag, val_str in replacements_t3.items():
                if tag in cell.text:
                    for p in cell.paragraphs:
                        if tag in p.text:
                            for r in p.runs:
                                if tag in r.text:
                                    r.text = r.text.replace(tag, val_str)
                            if tag in p.text:
                                p.text = p.text.replace(tag, val_str)
                                if p.runs:
                                    p.runs[0].font.name = "Poppins"
                                    p.runs[0].font.size = Pt(9)

    # Row 8: Signatures
    if len(t3.rows) > 8:
        row8 = t3.rows[8]
        app1 = val.get("approved_by") or "Director de Operaciones & Tecnología"
        app2 = val.get("approved_by_secondary") or "Director de Cumplimiento / BSA"
        row8.cells[0].text = app1
        if row8.cells[0].paragraphs[0].runs:
            row8.cells[0].paragraphs[0].runs[0].font.name = "Poppins"
            row8.cells[0].paragraphs[0].runs[0].font.size = Pt(9)
        row8.cells[2].text = app2
        if row8.cells[2].paragraphs[0].runs:
            row8.cells[2].paragraphs[0].runs[0].font.name = "Poppins"
            row8.cells[2].paragraphs[0].runs[0].font.size = Pt(9)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

if __name__ == "__main__":
    overview = {
        "target": "Dar seguimiento a los reportes de Actividades Sospechosas (SAR) generados y enviados a FinCEN.",
        "scope": "Aplica a todos los reportes SAR levantados por alertas transaccionales, sospecha de fraude o requerimientos regulatorios.",
        "process_input": "Reportes SAR generados por alertas transaccionales y sospecha de fraude.",
        "process_output": "Permitir que los clientes realicen transacciones sin requerir nuevamente información de SAR.",
        "frequency": "Periodicidad diaria."
    }
    steps = [
        {
            "step_number": 1,
            "responsible": "System Analyst",
            "activity_name": "Realizar asignación de caso",
            "activity_description": "El analista ingresa a la plataforma y realiza la distribución de casos SAR del día.",
            "sub_steps": ["1. Abrir sistema SAR", "2. Descargar base de datos (año) SARs.xls", "3. Filtrar casos pendientes"],
            "record_control": "(año) SARs.xls"
        },
        {
            "step_number": 2,
            "responsible": "analistas BSA Monitoring",
            "activity_name": "Analizar el informe de SAR previo",
            "activity_description": "Revisar los antecedentes del cliente en la bitácora histórica.",
            "sub_steps": ["1. Validar nombre y número de identificación", "2. Comparar patrones transaccionales"],
            "record_control": "1. Bitácora de seguimiento\n2. Cédula de análisis"
        },
        {
            "step_number": 3,
            "responsible": "analistas BSA Monitoring",
            "activity_name": "Determinar procedencia o descarte",
            "activity_description": "Determinar si la transacción cuenta con justificación documental o requiere reporte.",
            "is_decision": True,
            "decision_question": "¿La transacción se encuentra justificada?",
            "decision_branches": [
                {"condition_label": "Sí", "target_activity_name": "Cierre de caso y archivo"},
                {"condition_label": "No", "target_activity_name": "Generación de SAR FinCEN"}
            ],
            "record_control": "Dictamen de análisis BSA"
        }
    ]
    validity = {
        "code": "BSA-SAR-01",
        "version": "01",
        "elaboration_date": "29/09/2026",
        "approval_date": "30/09/2026",
        "developed_by": "Laura Marisol Vega Velazquez",
        "responsible_area": "Cumplimiento Regulatorio",
        "reviewed_by": "Gerente de BSA / AML",
        "responsible_department": "Dirección de Cumplimiento",
        "informed_areas": "Auditoría Interna, Operaciones, Legal",
        "approved_by": "Director de Cumplimiento",
        "approved_by_secondary": "Director General"
    }
    
    out_buf = populate_docx_from_template(
        template_path='backend/templates/master_work_instructions_template.docx',
        project_name='Seguimiento de SAR 90 dias',
        overview_data=overview,
        steps_data=steps,
        legal_framework=['Bank Secrecy Act (BSA)', 'BSA Compliance', 'Anti-Money Laundering (AML) Act'],
        validity_data=validity,
        mode_label='AS-IS'
    )
    
    with open('scratch/test_output_populated.docx', 'wb') as f:
        f.write(out_buf.getvalue())
    print(f"Test file generated: scratch/test_output_populated.docx ({len(out_buf.getvalue())} bytes)")
