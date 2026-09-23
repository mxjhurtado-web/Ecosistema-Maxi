#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project Charter & Official Process Narrative Component for TEMIS Web Flow
Manages project master data, objectives, scope, and AI-generated policy & procedure manuals.
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
                    rx.icon("file-text", size=24, color="#2563eb"),
                    rx.vstack(
                        rx.text("Ficha del Proyecto & Narrativa Oficial", size="4", weight="bold", color="#17283c"),
                        rx.text("Datos maestros, propósito del proceso y manual de procedimientos en texto corrido", size="2", color="#59697b"),
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
                        " Ficha Ejecutiva (PDF)",
                        on_click=FlowState.export_executive_charter_html,
                        color_scheme="blue",
                        variant="soft",
                        size="2",
                        radius="medium",
                        title="Exportar Ficha Ejecutiva oficial lista para imprimir o PDF",
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
                            rx.icon("network", size=15),
                            rx.text("Ver Diagrama"),
                            rx.icon("arrow-right", size=13),
                            align="center",
                            spacing="1",
                        ),
                        on_click=lambda: FlowState.set_active_view("flow"),
                        color_scheme="blue",
                        size="2",
                        radius="medium",
                    ),
                    spacing="2",
                    wrap="wrap",
                ),
                width="100%",
                padding_y="3",
                border_bottom="1px solid #d7e0ea",
                align="center",
            ),

            # 4-Step Operational Workflow Roadmap (P21)
            rx.box(
                rx.hstack(
                    rx.hstack(
                        rx.box(
                            rx.text("1", size="1", weight="bold", color="#ffffff"),
                            width="20px", height="20px", border_radius="full", background_color="#2563eb",
                            display="flex", align_items="center", justify_content="center",
                        ),
                        rx.text("1. Ficha Charter (Actual)", size="1", weight="bold", color="#2563eb"),
                        align="center", spacing="1",
                    ),
                    rx.icon("chevron-right", size=14, color="#cbd5e1"),
                    rx.hstack(
                        rx.box(
                            rx.text("2", size="1", weight="bold", color="#59697b"),
                            width="20px", height="20px", border_radius="full", background_color="#f1f5f9",
                            display="flex", align_items="center", justify_content="center",
                        ),
                        rx.text("2. Plan & Sprints", size="1", weight="medium", color="#59697b"),
                        on_click=lambda: FlowState.set_active_view("plan"),
                        cursor="pointer",
                        align="center", spacing="1",
                    ),
                    rx.icon("chevron-right", size=14, color="#cbd5e1"),
                    rx.hstack(
                        rx.box(
                            rx.text("3", size="1", weight="bold", color="#59697b"),
                            width="20px", height="20px", border_radius="full", background_color="#f1f5f9",
                            display="flex", align_items="center", justify_content="center",
                        ),
                        rx.text("3. Modelado BPMN / SIPOC", size="1", weight="medium", color="#59697b"),
                        on_click=lambda: FlowState.set_active_view("flow"),
                        cursor="pointer",
                        align="center", spacing="1",
                    ),
                    rx.icon("chevron-right", size=14, color="#cbd5e1"),
                    rx.hstack(
                        rx.box(
                            rx.text("4", size="1", weight="bold", color="#59697b"),
                            width="20px", height="20px", border_radius="full", background_color="#f1f5f9",
                            display="flex", align_items="center", justify_content="center",
                        ),
                        rx.text("4. Gobernanza & Calidad", size="1", weight="medium", color="#59697b"),
                        on_click=lambda: FlowState.set_active_view("governance"),
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
                border="1px solid #d7e0ea",
                border_radius="8px",
                box_shadow="0 1px 2px 0 rgba(0, 0, 0, 0.02)",
                width="100%",
            ),
            
            # Content Grid: Left Form (Charter) & Right Editor (Narrative)
            rx.hstack(
                # Left Panel: Project Charter Master Data
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("briefcase", size=18, color="#1d4ed8"),
                            rx.text("Datos Maestros del Proyecto", size="3", weight="bold", color="#17283c"),
                            align="center",
                            spacing="2",
                        ),
                        rx.vstack(
                            rx.text("Nombre del Proyecto / Proceso:", size="1", weight="bold", color="#59697b"),
                            rx.input(
                                value=FlowState.project_name,
                                on_change=FlowState.set_project_name,
                                width="100%",
                                size="2",
                                radius="medium",
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Propósito / Objetivo (\"¿Para qué es?\"):", size="1", weight="bold", color="#59697b"),
                            rx.text_area(
                                value=FlowState.project_purpose,
                                on_change=FlowState.set_project_purpose,
                                width="100%",
                                rows="3",
                                size="2",
                                radius="medium",
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Líder del Proyecto (PM):", size="1", weight="bold", color="#59697b"),
                                rx.input(
                                    value=FlowState.project_manager,
                                    on_change=FlowState.set_project_manager,
                                    width="100%",
                                    size="2",
                                    radius="medium",
                                ),
                                width="50%",
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Patrocinador (Sponsor):", size="1", weight="bold", color="#59697b"),
                                rx.input(
                                    value=FlowState.project_sponsor,
                                    on_change=FlowState.set_project_sponsor,
                                    width="100%",
                                    size="2",
                                    radius="medium",
                                ),
                                width="50%",
                                spacing="1",
                            ),
                            width="100%",
                            spacing="3",
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Fecha Inicio:", size="1", weight="bold", color="#59697b"),
                                rx.input(
                                    value=FlowState.start_date,
                                    on_change=FlowState.set_start_date,
                                    width="100%",
                                    size="2",
                                    radius="medium",
                                ),
                                width="50%",
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Fecha Entrega Final:", size="1", weight="bold", color="#59697b"),
                                rx.input(
                                    value=FlowState.end_date,
                                    on_change=FlowState.set_end_date,
                                    width="100%",
                                    size="2",
                                    radius="medium",
                                ),
                                width="50%",
                                spacing="1",
                            ),
                            width="100%",
                            spacing="3",
                        ),
                        rx.vstack(
                            rx.text("Alcance Incluido (In Scope):", size="1", weight="bold", color="#59697b"),
                            rx.text_area(
                                value=FlowState.scope_in,
                                on_change=FlowState.set_scope_in,
                                width="100%",
                                rows="2",
                                size="2",
                                radius="medium",
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Fuera de Alcance (Out of Scope):", size="1", weight="bold", color="#59697b"),
                            rx.text_area(
                                value=FlowState.scope_out,
                                on_change=FlowState.set_scope_out,
                                width="100%",
                                rows="2",
                                size="2",
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
                    border="1px solid #d7e0ea",
                    border_radius="10px",
                    padding="4",
                    box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px 0 rgba(0, 0, 0, 0.02)",
                ),

                # Right Panel: Official Procedure Manual & Narrative
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.hstack(
                                rx.icon("book-open", size=18, color="#059669"),
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
                                    background_color="#ffffff",
                                    border="1px solid #d7e0ea",
                                    border_radius="6px",
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
                    border="1px solid #d7e0ea",
                    border_radius="10px",
                    padding="4",
                    box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px 0 rgba(0, 0, 0, 0.02)",
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
