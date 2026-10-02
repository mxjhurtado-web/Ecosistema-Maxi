#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project Charter & Official Process Narrative Component for TEMIS Web Flow
Manages project master data, objectives, scope, and AI-generated policy & procedure manuals.
Styled in Executive Light Slate Theme (WCAG 2.2 AA compliant).
"""

import reflex as rx
from temis_web.state import FlowState


def project_charter() -> rx.Component:
    """Project Charter and Continuous Prose Narrative View"""
    return rx.box(
        rx.vstack(
            # Top Banner
            rx.hstack(
                rx.hstack(
                    rx.icon("file-text", size=24, color="#1e5a9a"),
                    rx.vstack(
                        rx.text("Ficha Técnica del Proceso", size="4", weight="bold", color="#17283c"),
                        rx.text("Datos maestros, propósito operativo y alcance documental del proceso", size="2", color="#52657a"),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        rx.icon("sparkles", size=15),
                        " Redactar con IA",
                        on_click=FlowState.generate_narrative_ai,
                        loading=FlowState.is_generating_narrative,
                        color_scheme="indigo",
                        size="2",
                        radius="medium",
                    ),
                    rx.button(
                        rx.icon("file-text", size=15),
                        " Ficha Técnica (PDF)",
                        on_click=FlowState.export_executive_charter_html,
                        color_scheme="blue",
                        variant="soft",
                        size="2",
                        radius="medium",
                        title="Exportar Ficha Técnica oficial lista para imprimir o PDF",
                    ),
                    rx.button(
                        rx.icon("download", size=15),
                        " Manual (.md)",
                        on_click=FlowState.export_narrative_markdown,
                        color_scheme="gray",
                        variant="soft",
                        size="2",
                        radius="medium",
                        title="Exportar Manual de Procedimientos en Markdown",
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon("table-2", size=15),
                            rx.text("Ver Matriz SIPOC"),
                            rx.icon("arrow-right", size=13),
                            align="center",
                            spacing="1",
                        ),
                        on_click=lambda: FlowState.set_active_view("sipoc"),
                        color_scheme="blue",
                        size="2",
                        radius="medium",
                    ),
                    spacing="2",
                    wrap="wrap",
                ),
                width="100%",
                padding_y="3",
                border_bottom="1px solid #d9e2ec",
                align="center",
            ),

            # 4-Step Operational Workflow Roadmap
            rx.box(
                rx.hstack(
                    rx.hstack(
                        rx.box(
                            rx.text("1", size="1", weight="bold", color="#ffffff"),
                            width="20px", height="20px", border_radius="full", background_color="#1e5a9a",
                            display="flex", align_items="center", justify_content="center",
                        ),
                        rx.text("1. Ficha Técnica", size="1", weight="bold", color="#1e5a9a"),
                        align="center", spacing="1",
                    ),
                    rx.icon("chevron-right", size=14, color="#94a3b8"),
                    rx.hstack(
                        rx.box(
                            rx.text("2", size="1", weight="bold", color="#52657a"),
                            width="20px", height="20px", border_radius="full", background_color="#e2e8f0",
                            display="flex", align_items="center", justify_content="center",
                        ),
                        rx.text("2. Matriz SIPOC", size="1", weight="medium", color="#52657a"),
                        on_click=lambda: FlowState.set_active_view("sipoc"),
                        cursor="pointer",
                        align="center", spacing="1",
                    ),
                    rx.icon("chevron-right", size=14, color="#94a3b8"),
                    rx.hstack(
                        rx.box(
                            rx.text("3", size="1", weight="bold", color="#52657a"),
                            width="20px", height="20px", border_radius="full", background_color="#e2e8f0",
                            display="flex", align_items="center", justify_content="center",
                        ),
                        rx.text("3. Diagrama BPMN", size="1", weight="medium", color="#52657a"),
                        on_click=lambda: FlowState.set_active_view("flow"),
                        cursor="pointer",
                        align="center", spacing="1",
                    ),
                    rx.icon("chevron-right", size=14, color="#94a3b8"),
                    rx.hstack(
                        rx.box(
                            rx.text("4", size="1", weight="bold", color="#52657a"),
                            width="20px", height="20px", border_radius="full", background_color="#e2e8f0",
                            display="flex", align_items="center", justify_content="center",
                        ),
                        rx.text("4. Work Instructions", size="1", weight="medium", color="#52657a"),
                        on_click=lambda: FlowState.set_active_view("narrative"),
                        cursor="pointer",
                        align="center", spacing="1",
                    ),
                    width="100%",
                    align="center",
                    spacing="3",
                    wrap="wrap",
                ),
                padding_x="4",
                padding_y="2.5",
                background_color="#ffffff",
                border="1px solid #d9e2ec",
                border_radius="8px",
                box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                width="100%",
            ),
            
            # Content Grid: Left Form (Charter) & Right Editor (Narrative)
            rx.hstack(
                # Left Panel: Project Charter Master Data
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("briefcase", size=18, color="#1e5a9a"),
                            rx.text("Datos Maestros del Proceso", size="3", weight="bold", color="#17283c"),
                            align="center",
                            spacing="2",
                        ),
                        rx.vstack(
                            rx.text("Nombre del Proceso:", size="1", weight="bold", color="#52657a"),
                            rx.input(
                                value=FlowState.project_name,
                                on_change=FlowState.set_project_name,
                                width="100%",
                                size="2",
                                variant="surface",
                                radius="medium",
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Código del Proceso:", size="1", weight="bold", color="#52657a"),
                                rx.input(
                                    value=FlowState.project_code,
                                    on_change=FlowState.set_project_code,
                                    width="100%",
                                    size="2",
                                    variant="surface",
                                    radius="medium",
                                ),
                                width="50%",
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("ID Iniciativa AppSheet (Opcional):", size="1", weight="bold", color="#52657a"),
                                rx.input(
                                    placeholder="ej. INIT-2026-089",
                                    value=FlowState.external_governance_id,
                                    on_change=FlowState.set_external_governance_id,
                                    width="100%",
                                    size="2",
                                    variant="surface",
                                    radius="medium",
                                ),
                                width="50%",
                                spacing="1",
                            ),
                            width="100%",
                            spacing="3",
                        ),
                        rx.vstack(
                            rx.text("Propósito / Objetivo (\"¿Para qué es?\"):", size="1", weight="bold", color="#52657a"),
                            rx.text_area(
                                value=FlowState.project_purpose,
                                on_change=FlowState.set_project_purpose,
                                width="100%",
                                rows="3",
                                size="2",
                                variant="surface",
                                radius="medium",
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Analista / Responsable del Levantamiento:", size="1", weight="bold", color="#52657a"),
                            rx.input(
                                value=FlowState.project_manager,
                                on_change=FlowState.set_project_manager,
                                width="100%",
                                size="2",
                                variant="surface",
                                radius="medium",
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Alcance Incluido (In Scope):", size="1", weight="bold", color="#52657a"),
                            rx.text_area(
                                value=FlowState.scope_in,
                                on_change=FlowState.set_scope_in,
                                width="100%",
                                rows="2",
                                size="2",
                                variant="surface",
                                radius="medium",
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Fuera de Alcance (Out of Scope):", size="1", weight="bold", color="#52657a"),
                            rx.text_area(
                                value=FlowState.scope_out,
                                on_change=FlowState.set_scope_out,
                                width="100%",
                                rows="2",
                                size="2",
                                variant="surface",
                                radius="medium",
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        width="100%",
                        spacing="3",
                    ),
                    width="40%",
                    min_width="380px",
                    background_color="#ffffff",
                    border="1px solid #d9e2ec",
                    border_radius="10px",
                    padding="4",
                    box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                ),

                # Right Panel: Official Procedure Manual & Narrative
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.hstack(
                                rx.icon("book-open", size=18, color="#107c41"),
                                rx.text("Manual de Políticas y Procedimientos (Narrativa Oficial)", size="3", weight="bold", color="#17283c"),
                                align="center",
                                spacing="2",
                            ),
                            rx.spacer(),
                            rx.badge("Texto Corrido Oficial", color_scheme="green", variant="soft", size="1"),
                            width="100%",
                            align="center",
                        ),
                        rx.tabs.root(
                            rx.tabs.list(
                                rx.tabs.trigger("Vista Previa (Formato Formal)", value="preview"),
                                rx.tabs.trigger("Editor de Texto / Markdown", value="editor"),
                            ),
                            rx.tabs.content(
                                rx.box(
                                    rx.markdown(FlowState.narrative_text),
                                    padding="4",
                                    background_color="#f8fafc",
                                    border="1px solid #d9e2ec",
                                    border_radius="6px",
                                    color="#17283c",
                                    height="calc(100vh - 270px)",
                                    overflow_y="auto",
                                ),
                                value="preview",
                            ),
                            rx.tabs.content(
                                rx.box(
                                    rx.text_area(
                                        value=FlowState.narrative_text,
                                        on_change=FlowState.set_narrative_text,
                                        width="100%",
                                        height="calc(100vh - 270px)",
                                        font_family="monospace",
                                        font_size="13px",
                                        size="3",
                                        variant="surface",
                                        radius="medium",
                                    ),
                                    padding_top="2",
                                ),
                                value="editor",
                            ),
                            default_value="preview",
                            width="100%",
                        ),
                        width="100%",
                        spacing="3",
                    ),
                    width="60%",
                    flex="1",
                    background_color="#ffffff",
                    border="1px solid #d9e2ec",
                    border_radius="10px",
                    padding="4",
                    box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                ),
                width="100%",
                height="calc(100vh - 165px)",
                spacing="4",
                align="start",
            ),
            width="100%",
            height="100%",
            spacing="3",
            padding="4",
        ),
        width="100%",
        height="100%",
        overflow="hidden",
        background_color="#f3f6fa",
    )
