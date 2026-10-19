import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

src_fp = r'C:\Users\User\Downloads\Backlog_Scrum_area_tecnica_TEMIS.xlsx'
repo_fp = r'C:\Users\User\Ecosistema-Maxi\Temis\Backlog_Scrum_area_tecnica_TEMIS.xlsx'

print(f"Loading workbook from: {src_fp}")
wb = openpyxl.load_workbook(src_fp)

# Common Styles
FONT_TITLE = Font(name="Calibri", size=14, bold=True, color="001E293B")
FONT_SUBTITLE = Font(name="Calibri", size=9, italic=True, color="0064748B")
FONT_HDR = Font(name="Calibri", size=10, bold=True, color="00FFFFFF")
FONT_ROW = Font(name="Calibri", size=10, bold=False, color="00334155")
FONT_ROW_BOLD = Font(name="Calibri", size=10, bold=True, color="001E293B")
FONT_HITO = Font(name="Calibri", size=10, bold=True, color="000047C7")

FILL_NAVY = PatternFill(start_color="001E293B", end_color="001E293B", fill_type="solid")
FILL_BLUE_HDR = PatternFill(start_color="000047C7", end_color="000047C7", fill_type="solid")
FILL_LIME_HDR = PatternFill(start_color="0098D801", end_color="0098D801", fill_type="solid")
FILL_ZEBRA_1 = PatternFill(start_color="00FFFFFF", end_color="00FFFFFF", fill_type="solid")
FILL_ZEBRA_2 = PatternFill(start_color="00F8FAFC", end_color="00F8FAFC", fill_type="solid")
FILL_HITO = PatternFill(start_color="00EBF5FF", end_color="00EBF5FF", fill_type="solid")
FILL_IN_PROGRESS = PatternFill(start_color="00FEF9C3", end_color="00FEF9C3", fill_type="solid") # Soft yellow
FILL_COMPLETED = PatternFill(start_color="00DCFCE7", end_color="00DCFCE7", fill_type="solid") # Soft green

BORDER_THIN = Border(
    left=Side(style='thin', color='00E2E8F0'),
    right=Side(style='thin', color='00E2E8F0'),
    top=Side(style='thin', color='00E2E8F0'),
    bottom=Side(style='thin', color='00E2E8F0')
)

# ==============================================================================
# 1. ACTUALIZAR '📅 Agenda Ejecutiva'
# ==============================================================================
print("Updating '📅 Agenda Ejecutiva'...")
ws_agenda = wb['📅 Agenda Ejecutiva']

# Row 11: Sprint 07
ws_agenda.cell(11, 3).value = "🔥 HITO ESTRATÉGICO: Introducción TEMIS Media Studio (Desktop) + Ingesta Web & Plantillas Maestras"
ws_agenda.cell(11, 4).value = "Media Studio / Ingesta ZIP / SIPOC / Plantilla Word Oficial"
ws_agenda.cell(11, 5).value = "Lanzamiento de TEMIS Media Studio (Whisper + Keyframes HD), Ingesta ZIP, Exportador Excel Oficial y Plantilla Maestra Word SAR 90 días"
ws_agenda.cell(11, 6).value = "Completed"
ws_agenda.cell(11, 7).value = 65

# Row 12: Sprint 08
ws_agenda.cell(12, 2).value = "01 Oct 2026 - 31 Oct 2026"
ws_agenda.cell(12, 3).value = "Pruebas de Usuario (UAT), Validación con Jefa de Procesos, Adaptaciones de Usabilidad & Auto-Layout"
ws_agenda.cell(12, 4).value = "UAT / Swimlanes / Usabilidad / Sincronización Bidireccional"
ws_agenda.cell(12, 5).value = "Validación en vivo del pipeline 4 fases (Entrevista->SIPOC->Flujo->Word), pruebas de estrés y refinamiento de carriles swimlanes"
ws_agenda.cell(12, 6).value = "In Progress"
ws_agenda.cell(12, 7).value = 35

# Apply formatting for Agenda
for r in [11, 12]:
    for c in range(1, 8):
        cell = ws_agenda.cell(r, c)
        cell.font = FONT_ROW
        cell.border = BORDER_THIN
        if c == 6: # Status
            cell.fill = FILL_COMPLETED if cell.value == "Completed" else FILL_IN_PROGRESS
            cell.font = FONT_ROW_BOLD
            cell.alignment = Alignment(horizontal="center", vertical="center")
        elif c in [1, 2, 7]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

# ==============================================================================
# 2. ACTUALIZAR 'Backlog Scrum Técnico TEMIS'
# ==============================================================================
print("Updating 'Backlog Scrum Técnico TEMIS'...")
ws_backlog = wb['Backlog Scrum Técnico TEMIS']

# Update Item 14 & 15 status to Completed
ws_backlog.cell(15, 14).value = "Completed"
ws_backlog.cell(15, 12).value = "2026-09-30 00:00:00"
ws_backlog.cell(16, 14).value = "Completed"
ws_backlog.cell(16, 12).value = "2026-09-30 00:00:00"

# New Items (19 to 25)
new_backlog_items = [
    {
        "id": "19",
        "module": "🔥 Media Studio Desktop / Whisper & Keyframes",
        "type": "Epic / HITO GRANDE",
        "story": "Como analista de procesos, quiero una suite de escritorio (TEMIS Media Studio) para transcribir grabaciones de entrevistas offline con Whisper y extraer capturas de pantalla HD automáticamente.",
        "task": "1. Implementar motor Whisper local con faster-whisper. 2. Crear extractor inteligente de fotogramas clave por cambio de escena/sistema. 3. Empaquetar proyecto en archivo .zip con manifiesto .temis.json, subtítulos .vtt y capturas/ sin saturar la red.",
        "seq": "TBD",
        "tech_desc": "Suite de escritorio offline en Python/FFmpeg para procesamiento multimedia local, transcripción sincronizada y captura de evidencias de alta resolución.",
        "priority": "Alta",
        "sp": 15,
        "hours": 75,
        "start": "2026-09-16 00:00:00",
        "end": "2026-09-24 00:00:00",
        "sprint": "Sprint 07",
        "status": "Completed",
        "assigned": "Equipo Técnico TEMIS",
        "criteria": "Suite ejecutable Windows offline, transcripción sin consumo de tokens y exportación de paquetes .zip con imágenes HD listas para web.",
        "ref": "2e80a295, 9b64dc3a"
    },
    {
        "id": "20",
        "module": "Ingesta ZIP & Galería Keyframes Web",
        "type": "User Story",
        "story": "Como usuario de TEMIS Web, quiero subir el paquete .zip de Media Studio para que el sistema indexe la transcripción y muestre la galería de capturas de pantalla de evidencias.",
        "task": "1. Crear parser de paquetes .zip en backend. 2. Implementar visor/galería de capturas de pantalla Base64 en frontend Reflex. 3. Habilitar drag-and-drop y progress spinner.",
        "seq": "TBD",
        "tech_desc": "Servicio de descompresión e indexación en memoria de paquetes .zip con extracción de 500+ bloques de diálogo y galería de imágenes en Base64.",
        "priority": "Alta",
        "sp": 8,
        "hours": 40,
        "start": "2026-09-20 00:00:00",
        "end": "2026-09-26 00:00:00",
        "sprint": "Sprint 07",
        "status": "Completed",
        "assigned": "Equipo Técnico TEMIS",
        "criteria": "Ingesta fluida de ZIP con 500+ bloques y renderizado reactivo de capturas HD en tiempo real.",
        "ref": "5061bb4a, da66633c, aa4e6bbb"
    },
    {
        "id": "21",
        "module": "Plantilla Maestra Word Oficial (.docx)",
        "type": "User Story",
        "story": "Como Jefa de Procesos, quiero que TEMIS genere el Manual de Procedimientos oficial en Word (.docx) cumpliendo al 100% la plantilla maestra corporativa con 4 tablas y evidencias visuales incrustadas.",
        "task": "1. Implementar motor de población sobre Plantilla_Maestra_Oficial_Work_Instructions_TEMIS.docx. 2. Mapear las 4 tablas (Overview, Legal, Actividades, Firmas) con colores institucionales (#0047C7, #98D801, #E2EFD9, #E2E2E2). 3. Incrustar capturas HD en la columna Record Control.",
        "seq": "TBD",
        "tech_desc": "Motor de plantillas dinámico en python-docx con clonación XML de filas de actividad, tipografía Poppins 9pt e incrustación de capturas de pantalla de sistemas en Record Control.",
        "priority": "Alta",
        "sp": 13,
        "hours": 65,
        "start": "2026-09-22 00:00:00",
        "end": "2026-09-29 00:00:00",
        "sprint": "Sprint 07",
        "status": "Completed",
        "assigned": "Equipo Técnico TEMIS",
        "criteria": "Descarga de DOCX oficial idéntico al estándar SAR 90 días con imágenes HD incrustadas, paleta oficial y firmas de aprobación.",
        "ref": "fc7c0eff, 1fcd3fde"
    },
    {
        "id": "22",
        "module": "Exportador Excel SIPOC Oficial",
        "type": "User Story",
        "story": "Como analista de procesos, quiero exportar la Matriz SIPOC a un archivo Excel idéntico a Plantilla Matriz Sipoc.xlsx con tipografía Century Gothic y 11 columnas B-K.",
        "task": "1. Crear servicio sipoc_exporter.py con formato estandarizado. 2. Configurar estructura 1.0..N, cintillo de Requisitos del Cliente y paleta oficial. 3. Añadir botón de descarga directa en UI.",
        "seq": "TBD",
        "tech_desc": "Servicio de exportación en openpyxl que genera matrices SIPOC con diseño corporativo estandarizado (11 columnas pareadas B-K, numeración 1.0 a N y estilos institucionales).",
        "priority": "Media",
        "sp": 5,
        "hours": 25,
        "start": "2026-09-25 00:00:00",
        "end": "2026-09-29 00:00:00",
        "sprint": "Sprint 07",
        "status": "Completed",
        "assigned": "Equipo Técnico TEMIS",
        "criteria": "Archivo .xlsx generado idéntico a Plantilla Matriz Sipoc.xlsx listo para entrega a clientes y directores.",
        "ref": "fc7c0eff"
    },
    {
        "id": "23",
        "module": "Ingesta Multi-Documento & IA Gemini 2.5",
        "type": "User Story",
        "story": "Como analista, quiero cargar múltiples documentos (entrevista + anexos) para que Gemini 2.5 enriquezca incrementalmente el proceso con citas y puntos de aclaración.",
        "task": "1. Implementar narrative_ai_extractor.py con fusión incremental. 2. Detectar puntos pendientes de aclaración con cliente. 3. Soportar transcripciones masivas con Gemini File API.",
        "seq": "TBD",
        "tech_desc": "Motor de enriquecimiento cognitivo con Gemini 2.5 Flash, trazabilidad de citas por párrafo de origen y generación de matriz dual AS-IS / TO-BE.",
        "priority": "Alta",
        "sp": 8,
        "hours": 40,
        "start": "2026-09-24 00:00:00",
        "end": "2026-09-30 00:00:00",
        "sprint": "Sprint 07",
        "status": "Completed",
        "assigned": "Equipo Técnico TEMIS",
        "criteria": "Fusión de documentos base + anexos sin duplicar pasos, detección de aclaraciones y generación de dual SIPOC/BPMN.",
        "ref": "7229b48e, 3d0d6ded, 92be41e7"
    },
    {
        "id": "24",
        "module": "Pruebas de Usuario (UAT) & Validación",
        "type": "User Story",
        "story": "Como equipo de procesos y Jefa de Área, queremos realizar sesiones de prueba en vivo (UAT) del flujo completo (Entrevista -> SIPOC -> Flujo -> Word) para validar usabilidad y rendimiento.",
        "task": "1. Ejecutar pruebas con casos de negocio reales (ej. SAR 90 días). 2. Validar edición manual en cada fase del pipeline. 3. Recopilar observaciones y mejoras de interfaz.",
        "seq": "TBD",
        "tech_desc": "Protocolo de pruebas de aceptación de usuario (UAT) en entorno productivo Web Cloud con casos reales y medición de tiempos de procesamiento.",
        "priority": "Alta",
        "sp": 13,
        "hours": 60,
        "start": "2026-10-01 00:00:00",
        "end": "2026-10-18 00:00:00",
        "sprint": "Sprint 08",
        "status": "In Progress",
        "assigned": "Jefa de Procesos & Equipo Técnico",
        "criteria": "Aprobación formal de las 4 fases de levantamiento, cero errores bloqueantes y checklist de mejoras aprobado.",
        "ref": "UAT-2026-OCT"
    },
    {
        "id": "25",
        "module": "Sincronización Bidireccional & Auto-Layout",
        "type": "User Story",
        "story": "Como diseñador de procesos, quiero optimizaciones en el auto-layout de carriles (swimlanes) y sincronización fluida entre la tabla SIPOC y el lienzo BPMN.",
        "task": "1. Afinar algoritmo de posicionamiento de nodos en swimlanes. 2. Mejorar edición reactiva de compuertas de decisión. 3. Implementar feedback de guardado instantáneo.",
        "seq": "TBD",
        "tech_desc": "Algoritmo de diagramación automática de swimlanes con ordenamiento topológico y sincronización reactiva bidireccional entre estado SIPOC y lienzo.",
        "priority": "Media",
        "sp": 10,
        "hours": 50,
        "start": "2026-10-01 00:00:00",
        "end": "2026-10-31 00:00:00",
        "sprint": "Sprint 08",
        "status": "In Progress",
        "assigned": "Equipo Técnico TEMIS",
        "criteria": "Lienzo BPMN con auto-acomodo de carriles y sincronización en tiempo real sin lag.",
        "ref": "Sprint 08 Dev"
    }
]

# Write new items to ws_backlog
current_row = 20
for item in new_backlog_items:
    vals = [
        item["id"], item["module"], item["type"], item["story"], item["task"],
        item["seq"], item["tech_desc"], item["priority"], item["sp"], item["hours"],
        item["start"], item["end"], item["sprint"], item["status"], item["assigned"],
        item["criteria"], item["ref"]
    ]
    fill_to_use = FILL_HITO if "HITO" in item["type"] else (FILL_ZEBRA_2 if current_row % 2 == 0 else FILL_ZEBRA_1)
    
    for c_idx, val in enumerate(vals, start=1):
        cell = ws_backlog.cell(current_row, c_idx, value=val)
        cell.font = FONT_ROW_BOLD if (c_idx in [1, 2, 8, 14] or "HITO" in item["type"]) else FONT_ROW
        cell.fill = fill_to_use
        cell.border = BORDER_THIN
        if c_idx in [1, 8, 9, 10, 13, 14]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
            if c_idx == 14:
                cell.fill = FILL_COMPLETED if val == "Completed" else FILL_IN_PROGRESS
        elif c_idx in [11, 12]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            
    current_row += 1

# ==============================================================================
# 3. ACTUALIZAR 'Relacion Commits'
# ==============================================================================
print("Updating 'Relacion Commits'...")
ws_rel = wb['Relacion Commits']

# Check max row of ws_rel
rel_start_row = 22 # After existing items
new_rel_rows = [
    ["14", "Exportador Gráfico PNG/PDF Pro", "Exportador vectorial PNG/PDF y pre-renderizado", "Sprint 07", "2", "Alta", "603d7945, 158f0ff4"],
    ["15", "Auto-Guardado PostgreSQL Cloud", "Sincronización cloud y mitigación de timeouts en Render", "Sprint 07", "3", "Alta", "237f7f7c, aa4e6bbb, 3590e8d9"],
    ["19", "🔥 Media Studio Desktop / Whisper & Keyframes", "Suite de escritorio offline para extracción multimedia", "Sprint 07", "3", "Crítica", "2e80a295, 9b64dc3a, b348d651"],
    ["20", "Ingesta ZIP & Galería Keyframes Web", "Ingesta de paquetes ZIP con galería Base64 de capturas", "Sprint 07", "4", "Alta", "5061bb4a, da66633c, 012ff586, 88b86dd8"],
    ["21", "Plantilla Maestra Word Oficial (.docx)", "Manual oficial Word 4 tablas con capturas HD incrustadas", "Sprint 07", "3", "Crítica", "fc7c0eff, 1fcd3fde, d785d2c8"],
    ["22", "Exportador Excel SIPOC Oficial", "Generador Excel idéntico a Plantilla Matriz Sipoc.xlsx", "Sprint 07", "2", "Alta", "fc7c0eff, 1fcd3fde"],
    ["23", "Ingesta Multi-Documento & IA Gemini 2.5", "Enriquecimiento cognitivo incremental con Gemini 2.5", "Sprint 07", "3", "Alta", "7229b48e, 3d0d6ded, 92be41e7"],
    ["24", "Pruebas de Usuario (UAT) & Validación", "Sesiones de prueba en vivo con Jefa de Procesos", "Sprint 08", "1", "Alta", "En Curso (Sprint 08)"],
    ["25", "Sincronización Bidireccional & Auto-Layout", "Optimización de swimlanes y sincronización reactiva", "Sprint 08", "1", "Media", "En Curso (Sprint 08)"]
]

for r_idx, r_data in enumerate(new_rel_rows, start=rel_start_row):
    fill_to_use = FILL_HITO if "HITO" in r_data[1] else (FILL_ZEBRA_2 if r_idx % 2 == 0 else FILL_ZEBRA_1)
    for c_idx, val in enumerate(r_data, start=1):
        cell = ws_rel.cell(r_idx, c_idx, value=val)
        cell.font = FONT_ROW_BOLD if c_idx in [1, 5, 6] or "HITO" in r_data[1] else FONT_ROW
        cell.fill = fill_to_use
        cell.border = BORDER_THIN
        if c_idx in [1, 4, 5, 6]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

# ==============================================================================
# 4. ACTUALIZAR 'Historial Commits'
# ==============================================================================
print("Updating 'Historial Commits'...")
ws_hist = wb['Historial Commits']

# Load recent commits JSON
with open('scratch/recent_commits.json', 'r', encoding='utf-8') as f:
    recent_commits = json.load(f)

# Clear existing commit rows and rebuild fresh list with all commits in chronological descending order
existing_first_row = 2
ws_hist.delete_rows(2, ws_hist.max_row)

for idx, c in enumerate(recent_commits, start=2):
    msg = c["message"]
    # categorize
    cat = "Frontend / UI"
    sprint = "Sprint 07 - Sep 2026"
    just = msg
    
    if "narrative" in msg or "template" in msg or "docx" in msg or "SAR 90" in msg:
        cat = "Plantilla Maestra Word / Narrativa"
        sprint = "Sprint 07 - Sep 2026"
        just = "Integración del motor de población sobre Plantilla_Maestra_Oficial_Work_Instructions_TEMIS.docx y 4 tablas oficiales."
    elif "studio" in msg or "faster-whisper" in msg or "Media Studio" in msg:
        cat = "🔥 HITO: TEMIS Media Studio Desktop"
        sprint = "Sprint 07 - Sep 2026"
        just = "Suite de escritorio offline para extracción multimedia, transcripción local Whisper y captura de fotogramas clave HD."
    elif "zip" in msg or "upload" in msg:
        cat = "Ingesta ZIP / Galería Evidencias"
        sprint = "Sprint 07 - Sep 2026"
        just = "Parser de paquetes .zip de Media Studio, visor reactivo de capturas Base64 y drag-and-drop en web."
    elif "sipoc" in msg or "export" in msg:
        cat = "SIPOC / Excel Oficial"
        sprint = "Sprint 07 - Sep 2026"
        just = "Estandarización del exportador Excel idéntico a Plantilla Matriz Sipoc.xlsx con 11 columnas y Century Gothic."
    elif "deploy" in msg or "render" in msg or "prod_server" in msg or "PORT" in msg:
        cat = "DevOps / Despliegue Cloud"
        sprint = "Sprint 07 - Sep 2026"
        just = "Optimización de servidor de producción ASGI, configuración de endpoints de upload y resolución de timeouts en Render."
    elif "drive" in msg or "persistence" in msg:
        cat = "Google Drive / Persistencia"
        sprint = "Sprint 07 - Sep 2026"
        just = "Respaldo automático en Google Workspace Shared Drive con Service Account institucional."
    elif "Gemini" in msg or "media" in msg or "transcrib" in msg:
        cat = "IA / Gemini 2.5 / Audio"
        sprint = "Sprint 07 - Sep 2026"
        just = "Ingesta de audios y videos masivos con Gemini File API y extracción incremental de narrativa."
    elif "Lucidchart" in msg or "lucid" in msg:
        cat = "Parser Lucidchart"
        sprint = "Sprint 05 - Ago 2026"
        just = "Parser nativo determinista para diagramas de Lucidchart sin alucinaciones de IA."
    elif "2026-08" in c["date"]:
        cat = "Hito Migración Web SaaS"
        sprint = "Sprint 05 - Ago 2026"
    elif "2026-09" in c["date"] and int(c["date"].split("-")[2][:2]) <= 15:
        cat = "UI/UX Pro / Suite"
        sprint = "Sprint 06 - Sep 2026"
        
    vals = [c["hash"], c["date"], c["author"], c["message"], cat, sprint, just]
    fill_to_use = FILL_HITO if "HITO" in cat else (FILL_ZEBRA_2 if idx % 2 == 0 else FILL_ZEBRA_1)
    
    for c_idx, val in enumerate(vals, start=1):
        cell = ws_hist.cell(idx, c_idx, value=val)
        cell.font = FONT_ROW_BOLD if (c_idx in [1, 5] or "HITO" in cat) else FONT_ROW
        cell.fill = fill_to_use
        cell.border = BORDER_THIN
        if c_idx in [1, 2, 5, 6]:
            cell.alignment = Alignment(horizontal="center", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

# ==============================================================================
# 5. ACTUALIZAR '📊 Dashboard Ejecutivo' FORMULAS
# ==============================================================================
print("Updating '📊 Dashboard Ejecutivo' formulas...")
ws_dash = wb['📊 Dashboard Ejecutivo']

# Update ranges from B2:B50 to B2:B65 across dashboard formulas
for r in range(1, ws_dash.max_row + 1):
    for c in range(1, ws_dash.max_column + 1):
        cell = ws_dash.cell(r, c)
        if cell.value and isinstance(cell.value, str) and "=" in cell.value:
            if "B2:B50" in cell.value or "M2:M50" in cell.value:
                cell.value = cell.value.replace("B2:B50", "B2:B65").replace("M2:M50", "M2:M65").replace("N2:N50", "N2:N65").replace("I2:I50", "I2:I65").replace("J2:J50", "J2:J65")

# Update module rows in Dashboard if needed
# Row 16: Sprint 07 Status in Dashboard
ws_dash.cell(16, 13).value = "Completed"
ws_dash.cell(17, 13).value = "In Progress"

# Save updated workbook
print(f"Saving updated workbook to: {src_fp}")
wb.save(src_fp)

# Also save copy to repository
print(f"Saving copy to repository: {repo_fp}")
wb.save(repo_fp)
print("SUCCESS: Backlog Scrum Excel updated in both locations!")
