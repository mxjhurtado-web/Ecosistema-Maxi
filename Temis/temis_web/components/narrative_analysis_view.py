#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Narrative Analysis View Component for TEMIS Web Flow
Complete workspace view for uploading source client documents (DOCX/PDF),
reviewing AI extractions with paragraph citations (Human-in-the-Loop),
generating Dual AS-IS/TO-BE SIPOCs, official 4-table Word manuals, and BPMN canvas graphs.
Styled in Executive Light Slate Theme (WCAG 2.2 AA compliant).
"""

import reflex as rx
from temis_web.state import FlowState


def step_indicator(step_num: int, label: str, current_step: rx.Var[int]) -> rx.Component:
    """Render a sequential step indicator pill"""
    is_active = current_step == step_num
    is_completed = current_step > step_num
    
    bg_color = rx.cond(is_active, "#1e5a9a", rx.cond(is_completed, "#10b981", "#e2e8f0"))
    text_color = rx.cond(is_active | is_completed, "#ffffff", "#64748b")
    
    return rx.hstack(
        rx.center(
            rx.cond(
                is_completed,
                rx.icon("check", size=14, color="#ffffff"),
                rx.text(str(step_num), size="1", weight="bold", color=text_color),
            ),
            width="24px",
            height="24px",
            border_radius="full",
            background_color=bg_color,
        ),
        rx.text(
            label,
            size="2",
            weight=rx.cond(is_active, "bold", "medium"),
            color=rx.cond(is_active, "#17283c", "#64748b"),
        ),
        align="center",
        spacing="2",
    )


def finding_card(finding: rx.Var[dict]) -> rx.Component:
    """Render a single extracted finding with citation and curation controls"""
    status = finding["curation_status"]
    
    status_badge = rx.cond(
        status == "approved",
        rx.badge("Aprobado", color_scheme="green", variant="surface", size="1"),
        rx.cond(
            status == "pending_clarification",
            rx.badge("Pendiente Aclaración", color_scheme="amber", variant="surface", size="1"),
            rx.badge("Descartado", color_scheme="gray", variant="surface", size="1")
        )
    )
    
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge(finding["category"], color_scheme="blue", variant="soft", size="1"),
                rx.spacer(),
                status_badge,
                width="100%",
                align="center",
            ),
            rx.text(finding["title"], size="2", weight="bold", color="#17283c"),
            rx.text(finding["content"], size="2", color="#334155", line_height="1.5"),
            
            # Citation box
            rx.cond(
                finding["source_quote"] != "",
                rx.box(
                    rx.hstack(
                        rx.icon("quote", size=14, color="#64748b"),
                        rx.vstack(
                            rx.text(
                                f"\"{finding['source_quote']}\"",
                                size="1",
                                italic=True,
                                color="#475569",
                            ),
                            rx.cond(
                                finding["source_paragraph_index"] != None,
                                rx.badge(
                                    f"Bloque {finding['source_paragraph_index']}",
                                    color_scheme="gray",
                                    variant="soft",
                                    size="1",
                                ),
                                rx.box(),
                            ),
                            spacing="1",
                            align="start",
                        ),
                        align="start",
                        spacing="2",
                        width="100%",
                    ),
                    padding="2",
                    background_color="#f8fafc",
                    border_left="3px solid #3b82f6",
                    border_radius="4px",
                    width="100%",
                ),
                rx.box(),
            ),
            
            # Action controls
            rx.hstack(
                rx.button(
                    rx.hstack(rx.icon("check", size=12), rx.text("Aprobar", size="1"), align="center", spacing="1"),
                    on_click=lambda: FlowState.update_finding_status(finding["id"], "approved"),
                    color_scheme="green",
                    variant="soft",
                    size="1",
                ),
                rx.button(
                    rx.hstack(rx.icon("circle-help", size=12), rx.text("Duda", size="1"), align="center", spacing="1"),
                    on_click=lambda: FlowState.update_finding_status(finding["id"], "pending_clarification"),
                    color_scheme="amber",
                    variant="soft",
                    size="1",
                ),
                rx.button(
                    rx.hstack(rx.icon("x", size=12), rx.text("Descartar", size="1"), align="center", spacing="1"),
                    on_click=lambda: FlowState.update_finding_status(finding["id"], "discarded"),
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
                spacing="2",
                margin_top="2",
                justify="end",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        padding="4",
        background_color="#ffffff",
        border="1px solid #e2e8f0",
        border_radius="8px",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
        width="100%",
    )


def keyframe_thumbnail_card(item: rx.Var[dict]) -> rx.Component:
    """Render a single keyframe screenshot thumbnail card"""
    filename = item["filename"].to(str)
    timestamp = item["timestamp_formatted"].to(str)
    data_uri = item["data_uri"].to(str)

    return rx.box(
        rx.vstack(
            rx.image(
                src=data_uri,
                width="100%",
                height="110px",
                object_fit="cover",
                border_radius="md",
                border="1px solid #cbd5e1",
            ),
            rx.hstack(
                rx.icon("camera", size=12, color="#0284c7"),
                rx.text(filename, size="1", weight="bold", color="#17283c", truncate=True),
                rx.spacer(),
                rx.badge(timestamp, color_scheme="blue", variant="surface", size="1"),
                align="center",
                width="100%",
            ),
            spacing="1",
            width="100%",
        ),
        padding="2",
        background_color="#ffffff",
        border="1px solid #e2e8f0",
        border_radius="lg",
        box_shadow="0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    )


def keyframes_gallery_section() -> rx.Component:
    """Gallery showing extracted screenshots from TEMIS Media Studio"""
    return rx.cond(
        FlowState.has_keyframes_gallery,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("camera", size=20, color="#0284c7"),
                    rx.heading("Capturas de Pantalla Clave (TEMIS Media Studio)", size="3", color="#17283c"),
                    rx.spacer(),
                    rx.badge("Extracción Automática HD", color_scheme="blue", variant="surface", size="1"),
                    align="center",
                    width="100%",
                ),
                rx.text("Evidencias visuales de la sesión capturadas en cambios de escena (listas para integrarse al Manual y Diagrama):", size="2", color="#52657a"),
                rx.grid(
                    rx.foreach(
                        FlowState.narrative_keyframes_gallery,
                        keyframe_thumbnail_card
                    ),
                    columns="4",
                    spacing="3",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            padding="4",
            background_color="#f0fdf4",
            border="1px solid #bbf7d0",
            border_radius="xl",
            box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
            width="100%",
        ),
        rx.box(),
    )


def document_library_item(doc: rx.Var[dict]) -> rx.Component:
    """Render a single document or media file in the project library"""
    is_media = doc["is_media"].to(bool)
    media_type = doc["media_type"].to(str)
    duration = doc["duration_formatted"].to(str)
    filename = doc["filename"].to(str)
    uploaded_by = doc["uploaded_by"].to(str)
    uploaded_at = doc["uploaded_at"].to(str)
    total_blocks = doc["total_paragraphs"].to(str)
    
    return rx.hstack(
        rx.cond(
            is_media,
            rx.icon("file-audio", size=18, color="#7c3aed"),
            rx.icon("file-text", size=18, color="#1e5a9a")
        ),
        rx.vstack(
            rx.hstack(
                rx.text(filename, size="2", weight="bold", color="#17283c"),
                rx.cond(
                    is_media,
                    rx.badge(media_type, color_scheme="purple", variant="soft", size="1", text_transform="uppercase"),
                    rx.badge("DOC", color_scheme="blue", variant="soft", size="1")
                ),
                rx.cond(
                    duration != "N/A",
                    rx.badge(duration, color_scheme="gray", variant="surface", size="1"),
                    rx.box()
                ),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.text("Subido por: ", size="1", color="#64748b"),
                rx.text(uploaded_by, size="1", color="#64748b", weight="medium"),
                rx.text(" | ", size="1", color="#94a3b8"),
                rx.text(uploaded_at, size="1", color="#64748b"),
                rx.text(" | ", size="1", color="#94a3b8"),
                rx.text(total_blocks, size="1", color="#64748b"),
                rx.text(" bloques indexados", size="1", color="#64748b"),
                spacing="1",
                align="center",
            ),
            spacing="1",
            align="start",
        ),
        rx.spacer(),
        rx.badge("Indexado", color_scheme="green", variant="soft", size="1"),
        align="center",
        padding="3",
        background_color="#ffffff",
        border="1px solid #e2e8f0",
        border_radius="md",
        width="100%",
    )


def narrative_analysis_view() -> rx.Component:
    """Main view for client narrative ingestion, extraction with citations and process generation"""
    return rx.box(
        rx.vstack(
            # 1. Header Bar
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.icon("file-search", size=22, color="#1e5a9a"),
                        rx.heading("Análisis de Narrativa & Ingesta Multimedia", size="5", weight="bold", color="#17283c"),
                        rx.badge("Gemini 2.5 Flash", color_scheme="purple", variant="soft", size="1"),
                        rx.badge("ZIP Media Studio / Documentos", color_scheme="blue", variant="surface", size="1"),
                        align="center",
                        spacing="2",
                    ),
                    rx.text(
                        "Ingesta integral de paquetes ZIP generados por TEMIS Media Studio (con capturas visuales HD de la sesión) y documentos corporativos (.docx, .pdf) para generar SIPOCs duales, diagramas BPMN y manuales de procedimientos.",
                        size="2",
                        color="#52657a",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                align="center",
                width="100%",
                padding_bottom="3",
                border_bottom="1px solid #d9e2ec",
            ),

            # 2. Sequential Step Progress Bar
            rx.hstack(
                step_indicator(1, "1. Ingesta Multimedia & Documentos", FlowState.narrative_analysis_step),
                rx.icon("chevron-right", size=16, color="#94a3b8"),
                step_indicator(2, "2. Revisión con Citas / Minutaje (Human-in-the-Loop)", FlowState.narrative_analysis_step),
                rx.icon("chevron-right", size=16, color="#94a3b8"),
                step_indicator(3, "3. Generación de Artefactos", FlowState.narrative_analysis_step),
                rx.icon("chevron-right", size=16, color="#94a3b8"),
                step_indicator(4, "4. Manual & Entrega", FlowState.narrative_analysis_step),
                spacing="4",
                align="center",
                padding_y="3",
                width="100%",
                overflow_x="auto",
            ),

            # 3. Step 1: Upload & Document Management
            rx.cond(
                FlowState.narrative_analysis_step == 1,
                rx.vstack(
                    rx.grid(
                        # Left: Universal Upload Dropzone
                        rx.box(
                            rx.vstack(
                                rx.upload(
                                    rx.vstack(
                                        rx.hstack(
                                            rx.icon("archive", size=28, color="#0284c7"),
                                            rx.icon("file-text", size=28, color="#1e5a9a"),
                                            rx.icon("file-badge", size=28, color="#7c3aed"),
                                            spacing="3",
                                            align="center",
                                        ),
                                        rx.text("Arrastra o selecciona Paquete ZIP de TEMIS Media Studio o Documento", size="3", weight="bold", color="#17283c", text_align="center"),
                                        rx.text("Paquetes: ZIP (.zip) de Media Studio con capturas | Documentos: Word (.docx), PDF (.pdf), Subtítulos (.vtt, .srt) | Proyectos: TEMIS (.json)", size="2", color="#52657a", text_align="center"),
                                        align="center",
                                        spacing="2",
                                        padding="6",
                                    ),
                                    id="upload_narrative_doc",
                                    max_files=1,
                                    border="2px dashed #cbd5e1",
                                    border_radius="xl",
                                    background_color="#f8fafc",
                                    width="100%",
                                    cursor="pointer",
                                    _hover={"border_color": "#1e5a9a", "background_color": "#f1f5f9"},
                                ),
                                
                                # Selected file action container (when file selected via click dialog)
                                rx.cond(
                                    rx.selected_files("upload_narrative_doc"),
                                    rx.box(
                                        rx.vstack(
                                            rx.hstack(
                                                rx.icon("file-check", size=18, color="#10b981"),
                                                rx.text("Archivo listo para procesar:", size="2", weight="bold", color="#17283c"),
                                                rx.foreach(rx.selected_files("upload_narrative_doc"), lambda f: rx.badge(f, color_scheme="blue", variant="solid", size="1")),
                                                rx.spacer(),
                                                rx.button(
                                                    "Limpiar",
                                                    on_click=rx.clear_selected_files("upload_narrative_doc"),
                                                    color_scheme="gray",
                                                    variant="ghost",
                                                    size="1",
                                                ),
                                                align="center",
                                                spacing="2",
                                                width="100%",
                                            ),
                                            rx.button(
                                                rx.hstack(
                                                    rx.icon("sparkles", size=16),
                                                    rx.text("Cargar y Procesar Paquete / Documento"),
                                                    align="center",
                                                    spacing="2",
                                                ),
                                                on_click=FlowState.handle_narrative_file_upload(rx.upload_files(upload_id="upload_narrative_doc")),
                                                loading=FlowState.is_uploading_narrative,
                                                color_scheme="blue",
                                                size="3",
                                                width="100%",
                                            ),
                                            spacing="2",
                                            width="100%",
                                        ),
                                        padding="3",
                                        background_color="#e0f2fe",
                                        border="1px solid #7dd3fc",
                                        border_radius="lg",
                                        width="100%",
                                    ),
                                    rx.box(),
                                ),
                                rx.cond(
                                    FlowState.is_uploading_narrative,
                                    rx.box(
                                        rx.hstack(
                                            rx.spinner(size="2", color="#0284c7"),
                                            rx.text("Procesando paquete e indexando evidencias visuales...", size="2", weight="medium", color="#0284c7"),
                                            align="center",
                                            spacing="2",
                                        ),
                                        padding="3",
                                        background_color="#f0f9ff",
                                        border="1px solid #bae6fd",
                                        border_radius="md",
                                        width="100%",
                                    ),
                                    rx.box(),
                                ),
                                rx.hstack(
                                    rx.icon("info", size=14, color="#0284c7"),
                                    rx.text(
                                        "💡 Flujo Óptimo: Arrastra el archivo 'Paquete_TEMIS_...zip' (~1 MB) generado por TEMIS Media Studio. Contiene las capturas y bitácora estructuradas sin el archivo de audio pesado para sincronización inmediata.",
                                        size="1",
                                        color="#0369a1",
                                    ),
                                    align="center",
                                    spacing="1",
                                    padding_top="1",
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            padding="4",
                            background_color="#ffffff",
                            border="1px solid #e2e8f0",
                            border_radius="xl",
                            box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                        ),

                        # Right: Active Document/Media Metadata & Execution Action
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon("file-check", size=20, color="#10b981"),
                                    rx.heading("Archivo Activo en Proyecto", size="3", color="#17283c"),
                                    align="center",
                                    spacing="2",
                                ),
                                rx.cond(
                                    FlowState.active_narrative_doc_name != "",
                                    rx.vstack(
                                        rx.box(
                                            rx.vstack(
                                                rx.hstack(
                                                    rx.cond(
                                                        FlowState.active_is_media_studio_package,
                                                        rx.badge("PAQUETE ZIP MEDIA STUDIO", color_scheme="cyan", variant="solid", size="1"),
                                                        rx.cond(
                                                            FlowState.active_narrative_is_media,
                                                            rx.badge(FlowState.active_narrative_media_type.upper(), color_scheme="purple", variant="solid", size="1"),
                                                            rx.badge("DOCX / PDF", color_scheme="blue", variant="solid", size="1"),
                                                        ),
                                                    ),
                                                    rx.text(FlowState.active_narrative_doc_name, size="2", weight="bold", color="#17283c"),
                                                    spacing="2",
                                                    align="center",
                                                ),
                                                rx.cond(
                                                    FlowState.active_narrative_is_media,
                                                    rx.hstack(
                                                        rx.icon("clock", size=14, color="#7c3aed"),
                                                        rx.text(f"Duración: {FlowState.active_narrative_duration}", size="1", weight="bold", color="#7c3aed"),
                                                        spacing="1",
                                                        align="center",
                                                    ),
                                                    rx.box(),
                                                ),
                                                rx.text(f"Subido por: {FlowState.user_name} ({FlowState.user_email})", size="1", color="#52657a"),
                                                rx.text(f"Párrafos/Bloques indexados: {FlowState.narrative_total_blocks}", size="1", color="#52657a"),
                                                spacing="1",
                                            ),
                                            padding="3",
                                            background_color="#f1f5f9",
                                            border_radius="md",
                                            width="100%",
                                        ),

                                        # Transcript Backup Download Box (if media or subtitles)
                                        rx.cond(
                                            FlowState.has_active_transcript_backup,
                                            rx.box(
                                                rx.vstack(
                                                    rx.hstack(
                                                        rx.icon("file-text", size=16, color="#1e5a9a"),
                                                        rx.text("Minuta & Transcripción de Respaldo", size="2", weight="bold", color="#17283c"),
                                                        align="center",
                                                        spacing="2",
                                                    ),
                                                    rx.text("Guarda una copia de auditoría con minutaje y diálogo literal.", size="1", color="#64748b"),
                                                    rx.hstack(
                                                        rx.button(
                                                            rx.hstack(rx.icon("download", size=14), rx.text("Descargar Word (.docx)", size="1"), align="center", spacing="1"),
                                                            on_click=FlowState.export_transcript_docx,
                                                            color_scheme="blue",
                                                            variant="soft",
                                                            size="1",
                                                        ),
                                                        rx.button(
                                                            rx.hstack(rx.icon("file-code", size=14), rx.text("Descargar (.txt)", size="1"), align="center", spacing="1"),
                                                            on_click=FlowState.export_transcript_txt,
                                                            color_scheme="gray",
                                                            variant="soft",
                                                            size="1",
                                                        ),
                                                        spacing="2",
                                                        width="100%",
                                                    ),
                                                    spacing="2",
                                                    width="100%",
                                                ),
                                                padding="3",
                                                background_color="#f8fafc",
                                                border="1px solid #e2e8f0",
                                                border_radius="md",
                                                width="100%",
                                            ),
                                            rx.box(),
                                        ),

                                        # If existing process findings exist, show Enrich vs Re-analyze options
                                        rx.cond(
                                            FlowState.extracted_findings,
                                            rx.vstack(
                                                rx.button(
                                                    rx.hstack(
                                                        rx.icon("sparkles", size=16),
                                                        rx.text("Enriquecer Proceso Existente (Incremental)"),
                                                        align="center",
                                                        spacing="2",
                                                    ),
                                                    on_click=FlowState.enrich_narrative_with_new_doc,
                                                    loading=FlowState.is_analyzing_narrative,
                                                    color_scheme="purple",
                                                    size="3",
                                                    width="100%",
                                                ),
                                                rx.button(
                                                    rx.hstack(
                                                        rx.icon("refresh-cw", size=14),
                                                        rx.text("Reemplazar y Re-analizar todo desde cero", size="2"),
                                                        align="center",
                                                        spacing="2",
                                                    ),
                                                    on_click=FlowState.run_narrative_ai_analysis,
                                                    loading=FlowState.is_analyzing_narrative,
                                                    color_scheme="gray",
                                                    variant="soft",
                                                    size="2",
                                                    width="100%",
                                                ),
                                                spacing="2",
                                                width="100%",
                                            ),
                                            rx.button(
                                                rx.hstack(
                                                    rx.icon("sparkles", size=16),
                                                    rx.text("Analizar con Gemini 2.5 Flash"),
                                                    align="center",
                                                    spacing="2",
                                                ),
                                                on_click=FlowState.run_narrative_ai_analysis,
                                                loading=FlowState.is_analyzing_narrative,
                                                color_scheme="purple",
                                                size="3",
                                                width="100%",
                                            ),
                                        ),
                                        spacing="3",
                                        width="100%",
                                    ),
                                    rx.text("Ningún archivo cargado aún. Arrastra un documento, audio o video para iniciar el análisis.", size="2", color="#64748b", italic=True),
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            padding="4",
                            background_color="#ffffff",
                            border="1px solid #e2e8f0",
                            border_radius="xl",
                            box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                        ),
                        columns="2",
                        spacing="4",
                        width="100%",
                    ),
                    
                    # Keyframe Screenshots Gallery from Media Studio ZIP
                    keyframes_gallery_section(),

                    # Project Document & Media History / Multi-Document Library
                    rx.cond(
                        FlowState.narrative_documents,
                        rx.vstack(
                            rx.hstack(
                                rx.icon("folder-archive", size=18, color="#1e5a9a"),
                                rx.heading("Biblioteca de Documentos & Medios del Proyecto", size="3", color="#17283c"),
                                align="center",
                                spacing="2",
                            ),
                            rx.text("Historial de archivos, grabaciones de entrevistas y minutas que nutren este proceso.", size="2", color="#52657a"),
                            rx.vstack(
                                rx.foreach(
                                    FlowState.narrative_documents,
                                    document_library_item
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                            padding="4",
                            background_color="#ffffff",
                            border="1px solid #e2e8f0",
                            border_radius="xl",
                            box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                        ),
                        rx.box(),
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.box(),
            ),

            # 4. Step 2: Human-in-the-Loop Review & Citations
            rx.cond(
                FlowState.narrative_analysis_step == 2,
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.heading("Revisión de Hallazgos y Citas Textuales", size="4", color="#17283c"),
                            rx.text("Valida cada afirmación extraída. Cada dato contiene el fragmento textual de respaldo.", size="2", color="#52657a"),
                            spacing="1",
                            align="start",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.hstack(
                                rx.icon("arrow-right", size=16),
                                rx.text("Avanzar a Generación"),
                                align="center",
                                spacing="1",
                            ),
                            on_click=lambda: FlowState.set_narrative_analysis_step(3),
                            color_scheme="blue",
                            size="2",
                        ),
                        width="100%",
                        align="center",
                    ),

                    # Summary cards: Target & Scope
                    rx.grid(
                        rx.box(
                            rx.vstack(
                                rx.text("Propósito (Target):", size="1", weight="bold", color="#1e5a9a"),
                                rx.text(FlowState.narrative_overview_target, size="2", color="#17283c"),
                                spacing="1",
                            ),
                            padding="3",
                            background_color="#f8fafc",
                            border="1px solid #e2e8f0",
                            border_radius="md",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("Alcance (Scope):", size="1", weight="bold", color="#1e5a9a"),
                                rx.text(FlowState.narrative_overview_scope, size="2", color="#17283c"),
                                spacing="1",
                            ),
                            padding="3",
                            background_color="#f8fafc",
                            border="1px solid #e2e8f0",
                            border_radius="md",
                        ),
                        columns="2",
                        spacing="3",
                        width="100%",
                    ),

                    # Keyframe Screenshots in Review
                    keyframes_gallery_section(),

                    # Findings List
                    rx.text("Hallazgos Clasificados:", size="3", weight="bold", color="#17283c"),
                    rx.vstack(
                        rx.foreach(FlowState.extracted_findings, finding_card),
                        spacing="3",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.box(),
            ),

            # 5. Step 3: Artifacts Generation Action Center
            rx.cond(
                FlowState.narrative_analysis_step == 3,
                rx.vstack(
                    rx.heading("Centro de Generación de Artefactos de Proceso", size="4", color="#17283c"),
                    rx.text("Genera los entregables interconectados basados en los hallazgos validados:", size="2", color="#52657a"),
                    
                    rx.grid(
                        # Card 1: Dual SIPOC
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon("table-2", size=24, color="#1e5a9a"),
                                    rx.heading("1. Matrices SIPOC Duales", size="3", color="#17283c"),
                                    align="center",
                                    spacing="2",
                                ),
                                rx.text(
                                    "Genera la matriz SIPOC AS-IS (operación actual) y TO-BE (operación optimizada con sistemas y automatizaciones).",
                                    size="2",
                                    color="#52657a",
                                ),
                                rx.button(
                                    "Generar SIPOCs AS-IS y TO-BE",
                                    on_click=FlowState.generate_dual_sipoc_from_analysis,
                                    color_scheme="blue",
                                    variant="solid",
                                    width="100%",
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            padding="4",
                            background_color="#ffffff",
                            border="1px solid #e2e8f0",
                            border_radius="xl",
                            box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                        ),

                        # Card 2: Dual BPMN Diagrams
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon("network", size=24, color="#7c3aed"),
                                    rx.heading("2. Diagramas BPMN en Lienzo", size="3", color="#17283c"),
                                    align="center",
                                    spacing="2",
                                ),
                                rx.text(
                                    "Crea automáticamente dos pestañas en el lienzo de diagramas: 'Flujo AS-IS' y 'Flujo TO-BE' con swimlanes, canales y curvas Bézier.",
                                    size="2",
                                    color="#52657a",
                                ),
                                rx.button(
                                    "Generar Diagramas BPMN Duales",
                                    on_click=FlowState.generate_dual_bpmn_from_analysis,
                                    color_scheme="purple",
                                    variant="solid",
                                    width="100%",
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            padding="4",
                            background_color="#ffffff",
                            border="1px solid #e2e8f0",
                            border_radius="xl",
                            box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                        ),

                        # Card 3: Narrative 4-Table Manual
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon("file-text", size=24, color="#10b981"),
                                    rx.heading("3. Manual & Plantilla Oficial (4 Tablas)", size="3", color="#17283c"),
                                    align="center",
                                    spacing="2",
                                ),
                                rx.text(
                                    "Genera el manual de procedimientos corporativo completo en Word (.docx) con las 4 tablas oficiales y puntos pendientes.",
                                    size="2",
                                    color="#52657a",
                                ),
                                rx.button(
                                    "Generar Manual Oficial de Procedimientos",
                                    on_click=FlowState.generate_narrative_document_from_analysis,
                                    color_scheme="green",
                                    variant="solid",
                                    width="100%",
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            padding="4",
                            background_color="#ffffff",
                            border="1px solid #e2e8f0",
                            border_radius="xl",
                            box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                        ),
                        columns="3",
                        spacing="4",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.box(),
            ),

            # 6. Step 4: Official Manual & Delivery Preview
            rx.cond(
                FlowState.narrative_analysis_step == 4,
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.heading("Manual de Procedimientos Generado", size="4", color="#17283c"),
                            rx.text("Entregable listo para revisión, exportación a Word y vinculación con la Fase 1 / 2 de Gobernanza.", size="2", color="#52657a"),
                            spacing="1",
                            align="start",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.hstack(
                                rx.icon("download", size=16),
                                rx.text("Descargar Word Oficial (.docx)"),
                                align="center",
                                spacing="1",
                            ),
                            on_click=FlowState.export_narrative_word,
                            color_scheme="blue",
                            size="2",
                        ),
                        width="100%",
                        align="center",
                    ),

                    # Markdown Preview Container
                    rx.box(
                        rx.markdown(FlowState.generated_narrative_markdown),
                        padding="5",
                        background_color="#ffffff",
                        border="1px solid #e2e8f0",
                        border_radius="xl",
                        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                        width="100%",
                        max_height="600px",
                        overflow_y="auto",
                    ),

                    # Navigation Quick Links
                    rx.hstack(
                        rx.button(
                            rx.hstack(rx.icon("table-2", size=16), rx.text("Ver Matriz SIPOC"), align="center", spacing="1"),
                            on_click=lambda: FlowState.set_active_view("sipoc"),
                            color_scheme="gray",
                            variant="soft",
                        ),
                        rx.button(
                            rx.hstack(rx.icon("network", size=16), rx.text("Ver Diagrama de Flujo (BPMN)"), align="center", spacing="1"),
                            on_click=lambda: FlowState.set_active_view("flow"),
                            color_scheme="gray",
                            variant="soft",
                        ),
                        rx.button(
                            rx.hstack(rx.icon("layers", size=16), rx.text("Ver Gobernanza & Gates"), align="center", spacing="1"),
                            on_click=lambda: FlowState.set_active_view("governance"),
                            color_scheme="gray",
                            variant="soft",
                        ),
                        spacing="3",
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.box(),
            ),

            spacing="4",
            width="100%",
            padding="4",
        ),
        width="100%",
        height="100%",
        overflow_y="auto",
        background_color="#f8fafc",
    )
