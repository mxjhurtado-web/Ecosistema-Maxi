#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Header Component for TEMIS Web Flow
Single-row sleek 52px top app bar with File menu, project title, Gemini AI prompt, and governance
"""

import reflex as rx
from temis_web.state import FlowState


def header() -> rx.Component:
    """Consolidated single-row top navigation bar"""
    return rx.hstack(
        # Left Section: Logo, File Menu & Editable Title
        rx.hstack(
            rx.hstack(
                rx.icon("network", size=22, color="#3b82f6"),
                rx.text("TEMIS", size="3", weight="bold", color="#0f172a"),
                align="center",
                spacing="2",
            ),
            # File Menu Dropdown (Archivo ▾)
            rx.menu.root(
                rx.menu.trigger(
                    rx.button(
                        rx.icon("folder-open", size=14),
                        " Archivo ▾",
                        color_scheme="gray",
                        variant="ghost",
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
            # Editable Project Title
            rx.hstack(
                rx.input(
                    value=FlowState.project_name,
                    on_change=FlowState.set_project_name,
                    width="210px",
                    size="1",
                    variant="soft",
                    radius="medium",
                ),
                rx.icon("pencil", size=13, color="#94a3b8"),
                align="center",
                spacing="1",
            ),
            align="center",
            spacing="3",
        ),
        # Center-Left Section: 4 Modular View Switchers
        rx.segmented_control.root(
            rx.segmented_control.item("📄 Ficha & Narrativa", value="charter"),
            rx.segmented_control.item("📊 Diagrama de Flujo", value="flow"),
            rx.segmented_control.item("📋 Matriz SIPOC", value="sipoc"),
            rx.segmented_control.item("🏛️ Gobernanza", value="governance"),
            value=FlowState.active_view,
            on_change=FlowState.set_active_view,
            size="1",
            radius="medium",
        ),
        rx.spacer(),
        # Center-Right Section: Gemini AI Prompt Bar
        rx.hstack(
            rx.input(
                placeholder="Describe el proceso para generar con IA (ej: Reembolso por WhatsApp)...",
                value=FlowState.ai_prompt_text,
                on_change=FlowState.set_ai_prompt_text,
                width="280px",
                size="1",
                variant="surface",
                radius="medium",
            ),
            rx.button(
                rx.icon("sparkles", size=14),
                " Generar",
                on_click=FlowState.generate_with_gemini,
                loading=FlowState.is_generating_ai,
                color_scheme="indigo",
                size="1",
                radius="medium",
            ),
            align="center",
            spacing="2",
        ),
        rx.spacer(),
        # Right Section: Auto-Save, AI Auditor & Governance Phase
        rx.hstack(
            rx.badge(FlowState.auto_save_status, color_scheme="green", variant="soft", size="1"),
            rx.button(
                rx.icon("shield-check", size=14),
                " Auditar IA",
                on_click=FlowState.open_audit_modal,
                color_scheme="indigo",
                variant="soft",
                size="1",
                radius="medium",
            ),
            rx.menu.root(
                rx.menu.trigger(
                    rx.button(
                        rx.icon("layers", size=14),
                        " Fase ",
                        FlowState.current_phase,
                        " ▾",
                        color_scheme="purple",
                        variant="soft",
                        size="1",
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
        height="50px",
        align="center",
        padding_x="4",
        background_color="#ffffff",
        border_bottom="1px solid #e2e8f0",
        box_shadow="0 1px 2px 0 rgba(0, 0, 0, 0.03)",
        z_index="10",
    )
