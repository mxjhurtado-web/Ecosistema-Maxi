#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Header component for TEMIS Web Flow
Top navbar with title, Gemini AI prompt bar and phase indicator
"""

import reflex as rx
from temis_web.state import FlowState


def header() -> rx.Component:
    """Header bar component"""
    return rx.box(
        rx.hstack(
            # Logo, File Menu & Editable Project Title
            rx.hstack(
                rx.icon("git-branch", size=26, color="#3b82f6"),
                # File Menu Dropdown (Archivo ▾)
                rx.menu.root(
                    rx.menu.trigger(
                        rx.button(
                            rx.icon("folder-open", size=15),
                            " Archivo ▾",
                            color_scheme="gray",
                            variant="soft",
                            size="2",
                            radius="medium",
                        ),
                    ),
                    rx.menu.content(
                        rx.menu.item(
                            rx.hstack(rx.icon("file-plus", size=14), rx.text("Nuevo Proyecto"), align="center", spacing="2"),
                            on_click=FlowState.create_new_project,
                        ),
                        rx.menu.item(
                            rx.hstack(rx.icon("folder", size=14), rx.text("Abrir Reciente..."), align="center", spacing="2"),
                            on_click=FlowState.open_recent_modal,
                        ),
                        rx.menu.item(
                            rx.hstack(rx.icon("save", size=14), rx.text("Guardar Cambios"), align="center", spacing="2"),
                            on_click=FlowState.save_diagram,
                        ),
                        rx.menu.separator(),
                        rx.menu.item(
                            rx.hstack(rx.icon("upload", size=14), rx.text("Importar Diagrama / PDF..."), align="center", spacing="2"),
                            on_click=FlowState.open_import_modal,
                        ),
                        rx.menu.item(
                            rx.hstack(rx.icon("download", size=14), rx.text("Exportar JSON..."), align="center", spacing="2"),
                            on_click=FlowState.export_as_json,
                        ),
                        rx.menu.item(
                            rx.hstack(rx.icon("package", size=14), rx.text("Exportar Paquete (.temis.json)"), align="center", spacing="2"),
                            on_click=FlowState.export_project_package,
                        ),
                    ),
                ),
                # Editable Project Name Input
                rx.hstack(
                    rx.input(
                        value=FlowState.project_name,
                        on_change=FlowState.set_project_name,
                        width="240px",
                        size="2",
                        variant="soft",
                        radius="medium",
                    ),
                    rx.icon("pencil", size=14, color="#64748b"),
                    align="center",
                    spacing="1",
                ),
                align="center",
                spacing="3",
            ),
            rx.spacer(),
            # Gemini AI Prompt Bar
            rx.hstack(
                rx.input(
                    placeholder="Describe el proceso para que Gemini genere el flujo (ej: Reembolso de dinero por WhatsApp)...",
                    value=FlowState.ai_prompt_text,
                    on_change=FlowState.set_ai_prompt_text,
                    width="420px",
                    size="2",
                    variant="surface",
                    radius="large",
                ),
                rx.button(
                    rx.icon("sparkles", size=16),
                    " Generar con IA",
                    on_click=FlowState.generate_with_gemini,
                    loading=FlowState.is_generating_ai,
                    color_scheme="indigo",
                    size="2",
                    radius="large",
                ),
                align="center",
                spacing="2",
            ),
            rx.spacer(),
            # Status Badge & Governance Phase Dropdown
            rx.hstack(
                rx.badge(FlowState.status_message, color_scheme="blue", variant="soft", size="2"),
                rx.menu.root(
                    rx.menu.trigger(
                        rx.button(
                            rx.icon("layers", size=16),
                            " Gobernanza: Fase ",
                            FlowState.current_phase,
                            " ▾",
                            color_scheme="purple",
                            variant="soft",
                            size="2",
                        ),
                    ),
                    rx.menu.content(
                        rx.menu.item("Fase 1: Diagnóstico Estratégico", on_click=lambda: FlowState.set_phase(1)),
                        rx.menu.item("Fase 2: Inicio del Proyecto", on_click=lambda: FlowState.set_phase(2)),
                        rx.menu.item("Fase 3: Planificación Híbrida", on_click=lambda: FlowState.set_phase(3)),
                        rx.menu.item("Fase 4: Ejecución Iterativa", on_click=lambda: FlowState.set_phase(4)),
                        rx.menu.item("Fase 5: Monitoreo y Control", on_click=lambda: FlowState.set_phase(5)),
                        rx.menu.item("Fase 6: Mejora Continua", on_click=lambda: FlowState.set_phase(6)),
                        rx.menu.item("Fase 7: Cierre del Proyecto", on_click=lambda: FlowState.set_phase(7)),
                    ),
                ),
                align="center",
                spacing="2",
            ),
            width="100%",
            align="center",
            padding_x="4",
            padding_y="3",
        ),
        background_color="#ffffff",
        border_bottom="1px solid #e2e8f0",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
        width="100%",
    )
