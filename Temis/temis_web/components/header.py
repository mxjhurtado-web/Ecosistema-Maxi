#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Header Component for TEMIS Web Flow (Workspace Level 2)
Consolidated sleek 54px top app bar with context, Gemini AI Prompt, auto-save status and File menu.
All emojis replaced with professional Lucide icons (WCAG 2.2 AA compliant).
"""

import reflex as rx
from temis_web.state import FlowState


def header() -> rx.Component:
    """Consolidated top context bar for the active workspace"""
    return rx.hstack(
        # Left Section: Active Project Title & Phase Context
        rx.hstack(
            rx.hstack(
                rx.icon("network", size=20, color="#3b82f6"),
                rx.text("TEMIS", size="3", weight="bold", color="#f8fafc"),
                align="center",
                spacing="2",
            ),
            rx.divider(orientation="vertical", size="2"),
            rx.badge(FlowState.project_code, color_scheme="indigo", variant="surface", size="1"),
            rx.input(
                value=FlowState.project_name,
                on_change=FlowState.set_project_name,
                width="240px",
                size="1",
                variant="soft",
                radius="medium",
                title="Editar nombre del proyecto",
            ),
            align="center",
            spacing="3",
        ),

        rx.spacer(),

        # Center Section: Gemini AI Prompt Bar
        rx.hstack(
            rx.input(
                placeholder="Describe el proceso para modelar o enriquecer con IA...",
                value=FlowState.ai_prompt_text,
                on_change=FlowState.set_ai_prompt_text,
                width="340px",
                size="1",
                variant="surface",
                radius="medium",
            ),
            rx.button(
                rx.hstack(
                    rx.icon("sparkles", size=13),
                    rx.text("Generar con IA", size="1", weight="medium"),
                    align="center",
                    spacing="1",
                ),
                on_click=FlowState.generate_with_gemini,
                loading=FlowState.is_generating_ai,
                color_scheme="blue",
                size="1",
                radius="medium",
            ),
            align="center",
            spacing="2",
        ),

        rx.spacer(),

        # Right Section: Auto-Save Status, File Menu & User Profile
        rx.hstack(
            # Auto-save status
            rx.badge(
                rx.hstack(
                    rx.icon("circle-check", size=12),
                    rx.text(FlowState.auto_save_status),
                    align="center",
                    spacing="1",
                ),
                color_scheme="green",
                variant="soft",
                size="1",
            ),

            # File Actions Menu (Archivo)
            rx.menu.root(
                rx.menu.trigger(
                    rx.button(
                        rx.hstack(
                            rx.icon("folder-cog", size=14),
                            rx.text("Archivo", size="1"),
                            rx.icon("chevron-down", size=12),
                            align="center",
                            spacing="1",
                        ),
                        color_scheme="gray",
                        variant="soft",
                        size="1",
                        radius="medium",
                    ),
                ),
                rx.menu.content(
                    rx.menu.item(
                        rx.hstack(rx.icon("save", size=14), rx.text("Guardar Cambios"), align="center", spacing="2"),
                        on_click=FlowState.save_diagram,
                    ),
                    rx.menu.item(
                        rx.hstack(rx.icon("folder-git-2", size=14), rx.text("Catálogo de Flujos..."), align="center", spacing="2"),
                        on_click=FlowState.open_recent_modal,
                    ),
                    rx.menu.separator(),
                    rx.menu.item(
                        rx.hstack(rx.icon("file-check", size=14), rx.text("Ficha Ejecutiva (PDF / HTML)"), align="center", spacing="2"),
                        on_click=FlowState.export_executive_charter_html,
                    ),
                    rx.menu.item(
                        rx.hstack(rx.icon("upload", size=14), rx.text("Importar Diagrama / PDF..."), align="center", spacing="2"),
                        on_click=FlowState.open_import_modal,
                    ),
                    rx.menu.item(
                        rx.hstack(rx.icon("package", size=14), rx.text("Exportar Paquete (.temis.json)"), align="center", spacing="2"),
                        on_click=FlowState.export_project_package,
                    ),
                    rx.menu.item(
                        rx.hstack(rx.icon("file-spreadsheet", size=14), rx.text("Exportar Excel SIPOC (.xlsx)"), align="center", spacing="2"),
                        on_click=FlowState.export_sipoc_excel,
                    ),
                    rx.menu.item(
                        rx.hstack(rx.icon("file-text", size=14), rx.text("Exportar Manual (.md)"), align="center", spacing="2"),
                        on_click=FlowState.export_narrative_markdown,
                    ),
                ),
            ),

            # Exit / Return to Portfolio
            rx.button(
                rx.hstack(
                    rx.icon("log-out", size=13),
                    rx.text("Salir", size="1"),
                    align="center",
                    spacing="1",
                ),
                on_click=FlowState.return_to_hub,
                color_scheme="gray",
                variant="ghost",
                size="1",
                radius="medium",
                title="Regresar al Hub de Portafolio",
            ),

            align="center",
            spacing="3",
        ),
        width="100%",
        height="54px",
        padding_x="4",
        background_color="#0f172a",
        border_bottom="1px solid #1e293b",
        align="center",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.4)",
    )
