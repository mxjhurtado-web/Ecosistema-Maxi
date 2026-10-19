import openpyxl
import copy
import os
import sys

def update_backlog_file(filepath):
    print(f"Updating: {filepath}")
    wb = openpyxl.load_workbook(filepath)
    
    # 1. Update Backlog Scrum Técnico TEMIS
    ws_backlog = wb['Backlog Scrum Técnico TEMIS']
    
    # Check if 26 and 27 already exist
    existing_ids = [str(ws_backlog.cell(row=r, column=1).value) for r in range(2, ws_backlog.max_row + 1)]
    
    if '26' not in existing_ids:
        new_items = [
            [
                '26',
                '🔥 Desacoplamiento Gobernanza ➔ AppSheet',
                'Epic / HITO ARQUITECTURA',
                'Como Director de Tecnología y PMO, quiero desacoplar el flujo de gobernanza corporativa (7 fases, diarios, aprobaciones) hacia Google AppSheet, para que TEMIS opere exclusivamente como Motor Especializado de Automatización Documental de Procesos.',
                '1. Delegar intake, estatus y aprobaciones a AppSheet. 2. Integrar ID de Iniciativa AppSheet (external_governance_id) en Ficha Técnica. 3. Limpiar navegación y sidebar en Reflex hacia 4 módulos técnicos (Ficha, SIPOC, BPMN, Work Instructions).',
                'TBD',
                'Separación de responsabilidades arquitecturales: AppSheet como capa de gobernanza institucional y TEMIS Web como motor de modelado BPMN, SIPOC y generación DOCX oficial.',
                'Alta',
                13,
                55,
                '2026-10-01 00:00:00',
                '2026-10-15 00:00:00',
                'Sprint 08',
                'Completed',
                'Equipo Técnico TEMIS',
                '• Navegación simplificada a 4 vistas técnicas (Ficha, SIPOC, BPMN, Work Instructions).\n• ID de Gobernanza AppSheet persistido en proyectos.\n• Cero dependencias circulares con tablas de gobernanza.',
                'Plan Técnico Desacoplamiento v1.0'
            ],
            [
                '27',
                'Reorientación Auditor IA Calidad Técnica (0-100)',
                'User Story',
                'Como analista y Jefa de Procesos, quiero que el Auditor IA evalúe la completitud y consistencia técnica de la documentación (nodos BPMN, sistemas/canales, consistencia SIPOC y capturas HD) sin penalizaciones por gobernanza externa.',
                '1. Rediseñar rúbrica 0-100 pts con 4 pilares técnicos. 2. Ajustar prompt de auditoría en backend. 3. Actualizar interfaz modal en Reflex con feedback positivo y métricas de calidad documental.',
                'TBD',
                'Motor de auditoría técnica con IA enfocado en consistencia SIPOC-BPMN, conectividad de flujos, asignación de sistemas y completitud de evidencias visuales.',
                'Alta',
                8,
                35,
                '2026-10-02 00:00:00',
                '2026-10-10 00:00:00',
                'Sprint 08',
                'Completed',
                'Equipo Técnico TEMIS',
                '• Auditoría técnica 0-100 pts con desglose por pilar.\n• Sin penalizaciones por roles o fases de gobernanza.\n• Diagnóstico accionable en tiempo real.',
                'audit_modal.py, state.py'
            ]
        ]
        
        template_row = ws_backlog.max_row
        for item in new_items:
            ws_backlog.append(item)
            curr_row = ws_backlog.max_row
            # Copy styles from template_row
            for col_idx in range(1, len(item) + 1):
                cell = ws_backlog.cell(row=curr_row, column=col_idx)
                tmpl_cell = ws_backlog.cell(row=template_row, column=col_idx)
                if tmpl_cell.has_style:
                    cell.font = copy.copy(tmpl_cell.font)
                    cell.border = copy.copy(tmpl_cell.border)
                    cell.fill = copy.copy(tmpl_cell.fill)
                    cell.number_format = tmpl_cell.number_format
                    cell.protection = copy.copy(tmpl_cell.protection)
                    cell.alignment = copy.copy(tmpl_cell.alignment)
        print("Added items 26 and 27 to Backlog Scrum Técnico TEMIS.")

    # 2. Update Agenda Ejecutiva
    agenda_sheet_name = None
    for name in wb.sheetnames:
        if 'Agenda Ejecutiva' in name:
            agenda_sheet_name = name
            break
            
    if agenda_sheet_name:
        ws_agenda = wb[agenda_sheet_name]
        for r in range(5, ws_agenda.max_row + 1):
            if ws_agenda.cell(row=r, column=1).value == 'Sprint 08':
                ws_agenda.cell(row=r, column=3).value = '🔥 HITO DE ARQUITECTURA: Desacoplamiento de Gobernanza a AppSheet & Enfoque Motor Documental TEMIS'
                ws_agenda.cell(row=r, column=4).value = 'AppSheet Link / Ficha Técnica / SIPOC / BPMN / DOCX / Auditor IA'
                ws_agenda.cell(row=r, column=5).value = 'Desacoplamiento a AppSheet, Reenfoque a 4 Vistas Técnicas, Auditor IA 0-100 pts técnico, UAT en vivo y auto-layout'
                ws_agenda.cell(row=r, column=7).value = 44
                print("Updated Sprint 08 in Agenda Ejecutiva.")
                break

    # 3. Update Relacion Commits
    if 'Relacion Commits' in wb.sheetnames:
        ws_rel = wb['Relacion Commits']
        existing_rel_ids = [str(ws_rel.cell(row=r, column=1).value) for r in range(3, ws_rel.max_row + 1)]
        if '26' not in existing_rel_ids:
            new_rels = [
                ['26', 'Desacoplamiento Gobernanza / AppSheet', 'Desacoplamiento de gobernanza corporativa hacia AppSheet e integración external_governance_id', 'Sprint 08', 1, 'Alta', 'feat(architecture)'],
                ['27', 'Auditor IA Calidad Técnica', 'Reorientación de rúbrica 0-100 pts a consistencia técnica BPMN/SIPOC/Evidencias', 'Sprint 08', 1, 'Alta', 'feat(audit)']
            ]
            template_rel_row = ws_rel.max_row
            for r_data in new_rels:
                ws_rel.append(r_data)
                curr_row = ws_rel.max_row
                for col_idx in range(1, len(r_data) + 1):
                    cell = ws_rel.cell(row=curr_row, column=col_idx)
                    tmpl_cell = ws_rel.cell(row=template_rel_row, column=col_idx)
                    if tmpl_cell.has_style:
                        cell.font = copy.copy(tmpl_cell.font)
                        cell.border = copy.copy(tmpl_cell.border)
                        cell.fill = copy.copy(tmpl_cell.fill)
                        cell.number_format = tmpl_cell.number_format
                        cell.protection = copy.copy(tmpl_cell.protection)
                        cell.alignment = copy.copy(tmpl_cell.alignment)
            print("Added items 26 and 27 to Relacion Commits.")

    # 4. Update Historial Commits
    if 'Historial Commits' in wb.sheetnames:
        ws_hist = wb['Historial Commits']
        new_commits = [
            [
                '7b49a12c',
                '2026-10-02 14:30:00 -0600',
                'Jose Antonio Hurtado Palestina',
                'feat(architecture): decouple corporate governance to AppSheet and re-scope TEMIS as Process Documentation Engine',
                'Arquitectura / Gobernanza AppSheet',
                'Sprint 08 - Oct 2026',
                'Desacoplamiento de gobernanza corporativa hacia AppSheet, reorientación a 4 vistas técnicas (Ficha, SIPOC, BPMN, Work Instructions) y actualización del Auditor IA a calidad técnica (0-100 pts).'
            ]
        ]
        # Insert after row 1 (header)
        for commit_data in reversed(new_commits):
            ws_hist.insert_rows(2)
            for col_idx, val in enumerate(commit_data, start=1):
                cell = ws_hist.cell(row=2, column=col_idx, value=val)
                # style from row 3
                tmpl_cell = ws_hist.cell(row=3, column=col_idx)
                if tmpl_cell.has_style:
                    cell.font = copy.copy(tmpl_cell.font)
                    cell.border = copy.copy(tmpl_cell.border)
                    cell.fill = copy.copy(tmpl_cell.fill)
                    cell.number_format = tmpl_cell.number_format
                    cell.protection = copy.copy(tmpl_cell.protection)
                    cell.alignment = copy.copy(tmpl_cell.alignment)
        print("Added latest commit to Historial Commits.")

    wb.save(filepath)
    print(f"Successfully saved {filepath}\n")

if __name__ == '__main__':
    downloads_path = r'C:\Users\User\Downloads\Backlog_Scrum_area_tecnica_TEMIS.xlsx'
    repo_path = r'C:\Users\User\Ecosistema-Maxi\Temis\Backlog_Scrum_area_tecnica_TEMIS.xlsx'
    
    if os.path.exists(downloads_path):
        update_backlog_file(downloads_path)
    if os.path.exists(repo_path):
        update_backlog_file(repo_path)
