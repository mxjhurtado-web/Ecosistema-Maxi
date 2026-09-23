#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project Hub Component (Level 1) for TEMIS Web Flow
Enterprise Work OS Portfolio Dashboard (Linear / Notion / Monday.com style)
All emojis removed and replaced with professional Lucide SVG icons (WCAG 2.2 AA compliant).
Features:
- Action-driven executive KPIs
- 3-Step Project Creation Wizard Modal
- Portfolio projects list with clear status badges, Scrum progress, and Drive sync.
"""

import reflex as rx
from temis_web.state import FlowState


def kpi_card(title: str, value: rx.Var[str] | str, subtitle: rx.Var[str] | str | None, icon_name: str, color_hex: str, badge_text: str = "") -> rx.Component:
    """Render a single executive KPI metric card without emojis in Executive Light Slate"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon(icon_name, size=18, color=color_hex),
                    padding="2",
                    background_color=f"{color_hex}15",
                    border_radius="8px",
                ),
                rx.spacer(),
                rx.cond(
                    badge_text != "",
                    rx.badge(badge_text, color_scheme="blue", variant="soft", size="1"),
                    rx.box(),
                ),
                width="100%",
                align="center",
            ),
            rx.text(title, size="1", color="#52657a", weight="medium"),
            rx.text(value, size="6", weight="bold", color="#17283c"),
            rx.text(subtitle, size="1", color="#8295a9"),
            spacing="1",
            align="start",
            width="100%",
        ),
        padding="4",
        background_color="#ffffff",
        border="1px solid #d9e2ec",
        border_radius="12px",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
        flex="1",
        min_width="220px",
        _hover={
            "box_shadow": "0 4px 12px 0 rgba(0, 0, 0, 0.08)",
            "border_color": "#c9d6e3",
        },
    )


def project_card(proj: rx.Var[dict]) -> rx.Component:
    """Render an interactive project card in clean Linear/Monday.com style with verified WCAG contrast"""
    return rx.box(
        rx.vstack(
            # Card Top Row: Code, Name, Health Badge & Audit Score
            rx.hstack(
                rx.hstack(
                    rx.badge(
                        proj["code"],
                        color_scheme="blue",
                        variant="surface",
                        size="1",
                    ),
                    rx.text(
                        proj["name"],
                        size="3",
                        weight="bold",
                        color="#17283c",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                # Health Semaphore Badge (T05 - No Emojis, Pure SVG, WCAG 2.2 AA Contrast)
                rx.cond(
                    proj["health_status"] == "green",
                    rx.badge(
                        rx.hstack(rx.icon("circle-check", size=11), rx.text("Salud: Al día"), align="center", spacing="1"),
                        color_scheme="green",
                        variant="solid",
                        size="1",
                    ),
                    rx.cond(
                        proj["health_status"] == "yellow",
                        rx.badge(
                            rx.hstack(rx.icon("triangle-alert", size=11), rx.text("Salud: En riesgo"), align="center", spacing="1"),
                            color_scheme="amber",
                            variant="solid",
                            size="1",
                        ),
                        rx.cond(
                            proj["health_status"] == "red",
                            rx.badge(
                                rx.hstack(rx.icon("circle-alert", size=11), rx.text("Salud: Bloqueado"), align="center", spacing="1"),
                                color_scheme="ruby",
                                variant="solid",
                                size="1",
                            ),
                            rx.badge(
                                rx.hstack(rx.icon("circle", size=11), rx.text("Salud: Sin evaluar"), align="center", spacing="1"),
                                color_scheme="gray",
                                variant="soft",
                                size="1",
                            ),
                        ),
                    ),
                ),
                # Six Sigma Audit Score Badge (Clarified label: Auditoría BPMN)
                rx.cond(
                    (proj["health_status"] == "unrated") | (proj["audit_score"] == 0),
                    rx.badge(
                        rx.hstack(rx.icon("shield", size=11), rx.text("Auditoría: N/A"), align="center", spacing="1"),
                        color_scheme="gray",
                        variant="soft",
                        size="1",
                    ),
                    rx.badge(
                        rx.hstack(
                            rx.icon("shield-check", size=12),
                            rx.text("Auditoría: ", proj["audit_score"], "/100"),
                            align="center",
                            spacing="1",
                        ),
                        color_scheme="purple",
                        variant="soft",
                        size="1",
                    ),
                ),
                width="100%",
                align="center",
            ),

            # Purpose / Scope description
            rx.text(
                proj["purpose"],
                size="2",
                color="#52657a",
                max_width="100%",
                line_clamp=2,
            ),

            rx.divider(color_scheme="gray", opacity=0.15),

            # Middle Row: Governance Phase & Active Sprint
            rx.hstack(
                rx.hstack(
                    rx.icon("layers", size=14, color="#7c3aed"),
                    rx.text(proj["phase_name"], size="1", weight="medium", color="#6d28d9"),
                    align="center",
                    spacing="1",
                    padding_x="2",
                    padding_y="1",
                    background_color="#ede9fe",
                    border_radius="6px",
                ),
                rx.hstack(
                    rx.icon("flame", size=14, color="#ea580c"),
                    rx.text(proj["current_sprint"], " • ", proj["current_sprint_name"], size="1", weight="medium", color="#9a3412"),
                    align="center",
                    spacing="1",
                    padding_x="2",
                    padding_y="1",
                    background_color="#ffedd5",
                    border_radius="6px",
                ),
                wrap="wrap",
                spacing="2",
                width="100%",
                align="center",
            ),

            # Progress Bar (% Avance Backlog)
            rx.vstack(
                rx.hstack(
                    rx.text("Avance del Backlog Scrum:", size="1", color="#52657a", weight="medium"),
                    rx.spacer(),
                    rx.hstack(
                        rx.text(proj["progress_percentage"].to_string(), "% (", proj["completed_sp"].to_string(), "/", proj["total_sp"].to_string(), " SP)", size="1", weight="bold", color="#17283c"),
                        spacing="0",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.progress(
                    value=proj["progress_percentage"],
                    width="100%",
                    height="6px",
                    radius="full",
                    color_scheme="blue",
                ),
                spacing="1",
                width="100%",
            ),

            rx.divider(color_scheme="gray", opacity=0.15),

            # Bottom Row: Manager Avatar, Quick Links & Primary Workspace Button
            rx.hstack(
                # Manager & Date
                rx.hstack(
                    rx.avatar(
                        fallback=proj["manager_initials"],
                        size="1",
                        radius="full",
                        color_scheme="blue",
                    ),
                    rx.vstack(
                        rx.text(proj["manager"], size="1", weight="medium", color="#17283c"),
                        rx.hstack(
                            rx.text("Sponsor:", size="1", color="#52657a"),
                            rx.text(proj["sponsor"], size="1", color="#17283c", weight="medium"),
                            spacing="1",
                        ),
                        spacing="0",
                        align="start",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                # Actions Row
                rx.hstack(
                    rx.cond(
                        proj["drive_folder_url"] != "",
                        rx.button(
                            rx.hstack(
                                rx.icon("folder-open", size=13),
                                rx.text("Drive"),
                                align="center",
                                spacing="1",
                            ),
                            on_click=rx.redirect(proj["drive_folder_url"], is_external=True),
                            color_scheme="gray",
                            variant="soft",
                            size="1",
                            radius="medium",
                            title="Abrir carpeta oficial en Google Drive",
                        ),
                        rx.box(),
                    ),
                    rx.cond(
                        proj["sheet_url"] != "",
                        rx.button(
                            rx.hstack(
                                rx.icon("file-spreadsheet", size=13),
                                rx.text("Plan de Trabajo"),
                                align="center",
                                spacing="1",
                            ),
                            on_click=rx.redirect(proj["sheet_url"], is_external=True),
                            color_scheme="green",
                            variant="soft",
                            size="1",
                            radius="medium",
                            title="Abrir hoja de cálculo oficial en Google Sheets",
                        ),
                        rx.box(),
                    ),
                    # Primary Open Workspace Button (Dominant visual hierarchy)
                    rx.button(
                        rx.hstack(
                            rx.icon("arrow-right", size=14),
                            rx.text("Abrir Espacio de Trabajo", weight="bold"),
                            align="center",
                            spacing="1",
                        ),
                        on_click=lambda: FlowState.open_project_workspace(proj["id"]),
                        color_scheme="blue",
                        size="1",
                        radius="medium",
                    ),
                    # Delete Project Button (Secondary action)
                    rx.button(
                        rx.icon("trash-2", size=13),
                        on_click=lambda: FlowState.prompt_delete_project(proj["id"], proj["name"], proj["code"]),
                        color_scheme="ruby",
                        variant="soft",
                        size="1",
                        radius="medium",
                        title="Eliminar Proyecto",
                    ),
                    align="center",
                    spacing="2",
                    wrap="wrap",
                ),
                width="100%",
                align="center",
            ),
            spacing="3",
            width="100%",
        ),
        padding="4",
        background_color="#ffffff",
        border="1px solid #d9e2ec",
        border_radius="12px",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
        width="100%",
        _hover={
            "border_color": "#c9d6e3",
            "box_shadow": "0 4px 12px 0 rgba(0, 0, 0, 0.08)",
        },
    )


def delete_project_modal() -> rx.Component:
    """Confirmation modal before deleting a project permanently"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.icon("triangle-alert", size=22, color="#dc2626"),
                        padding="2",
                        background_color="#fee2e2",
                        border_radius="8px",
                    ),
                    rx.vstack(
                        rx.dialog.title("¿Eliminar Proyecto del Portafolio?", size="4", weight="bold", color="#991b1b"),
                        rx.dialog.description(
                            "Esta acción eliminará el proyecto y su configuración activa.",
                            size="2",
                            color="#64748b",
                        ),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.divider(),
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.text("Proyecto:", size="1", weight="bold", color="#64748b", width="80px"),
                            rx.text(FlowState.project_to_delete_name, size="2", weight="bold", color="#0f172a"),
                            align="center",
                        ),
                        rx.hstack(
                            rx.text("Código:", size="1", weight="bold", color="#64748b", width="80px"),
                            rx.badge(FlowState.project_to_delete_code, color_scheme="indigo", variant="surface", size="1"),
                            align="center",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    padding="3",
                    background_color="#f8fafc",
                    border="1px solid #e2e8f0",
                    border_radius="8px",
                    width="100%",
                ),
                rx.callout(
                    "Se removerán los diagramas Bézier, matriz SIPOC, sprints y registros de gobernanza. Las carpetas en Google Drive permanecerán en la nube para auditoría.",
                    icon="info",
                    color_scheme="amber",
                    size="1",
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        color_scheme="gray",
                        variant="soft",
                        size="2",
                        on_click=FlowState.close_delete_project_modal,
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(
                            rx.icon("trash-2", size=14),
                            rx.text("Sí, Eliminar Proyecto"),
                            align="center",
                            spacing="1",
                        ),
                        on_click=FlowState.confirm_delete_project,
                        color_scheme="ruby",
                        size="2",
                        radius="medium",
                    ),
                    width="100%",
                    align="center",
                ),
                spacing="4",
                width="100%",
            ),
            width="460px",
            max_width="95vw",
            border_radius="xl",
            padding="5",
            background_color="#ffffff",
        ),
        open=FlowState.show_delete_project_modal,
        on_open_change=FlowState.set_show_delete_project_modal,
    )


def wizard_step_indicator() -> rx.Component:
    """Render 3-step visual progress bar in the project creation modal"""
    return rx.hstack(
        # Step 1: Datos Básicos
        rx.hstack(
            rx.box(
                rx.text("1", size="1", weight="bold", color=rx.cond(FlowState.new_proj_wizard_step >= 1, "#ffffff", "#64748b")),
                width="22px",
                height="22px",
                border_radius="full",
                background_color=rx.cond(FlowState.new_proj_wizard_step >= 1, "#1d4ed8", "#e2e8f0"),
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.text(
                "Datos Básicos",
                size="1",
                weight=rx.cond(FlowState.new_proj_wizard_step == 1, "bold", "medium"),
                color=rx.cond(FlowState.new_proj_wizard_step == 1, "#1d4ed8", "#64748b"),
            ),
            align="center",
            spacing="1",
        ),
        rx.divider(width="30px"),
        # Step 2: Plan e Integraciones
        rx.hstack(
            rx.box(
                rx.text("2", size="1", weight="bold", color=rx.cond(FlowState.new_proj_wizard_step >= 2, "#ffffff", "#64748b")),
                width="22px",
                height="22px",
                border_radius="full",
                background_color=rx.cond(FlowState.new_proj_wizard_step >= 2, "#1d4ed8", "#e2e8f0"),
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.text(
                "Plan & Integraciones",
                size="1",
                weight=rx.cond(FlowState.new_proj_wizard_step == 2, "bold", "medium"),
                color=rx.cond(FlowState.new_proj_wizard_step == 2, "#1d4ed8", "#64748b"),
            ),
            align="center",
            spacing="1",
        ),
        rx.divider(width="30px"),
        # Step 3: Revisar & Confirmar
        rx.hstack(
            rx.box(
                rx.text("3", size="1", weight="bold", color=rx.cond(FlowState.new_proj_wizard_step == 3, "#ffffff", "#64748b")),
                width="22px",
                height="22px",
                border_radius="full",
                background_color=rx.cond(FlowState.new_proj_wizard_step == 3, "#1d4ed8", "#e2e8f0"),
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.text(
                "Revisar & Crear",
                size="1",
                weight=rx.cond(FlowState.new_proj_wizard_step == 3, "bold", "medium"),
                color=rx.cond(FlowState.new_proj_wizard_step == 3, "#1d4ed8", "#64748b"),
            ),
            align="center",
            spacing="1",
        ),
        width="100%",
        align="center",
        justify="center",
        padding_y="2",
    )


def new_project_modal() -> rx.Component:
    """3-Step Wizard dialog modal to create a project and deploy Drive/Sheets scaffolding"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Modal Header
                rx.hstack(
                    rx.box(
                        rx.icon("folder-plus", size=20, color="#1d4ed8"),
                        padding="2",
                        background_color="#eff6ff",
                        border_radius="8px",
                    ),
                    rx.vstack(
                        rx.dialog.title("Alta de Nuevo Proyecto en TEMIS", size="4", weight="bold", color="#0f172a"),
                        rx.dialog.description(
                            "Asistente en 3 pasos para configurar el proyecto, 11 carpetas en Drive y cronograma.",
                            size="2",
                            color="#64748b",
                        ),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),

                wizard_step_indicator(),
                rx.divider(),

                # STEP 1: Datos Básicos
                rx.cond(
                    FlowState.new_proj_wizard_step == 1,
                    rx.vstack(
                        rx.hstack(
                            rx.vstack(
                                rx.text("Nombre del Proyecto *", size="1", weight="bold", color="#334155"),
                                rx.input(
                                    placeholder="Ej: Automatización de Cobranza Digital",
                                    value=FlowState.new_proj_name,
                                    on_change=FlowState.set_new_proj_name,
                                    width="100%",
                                    size="2",
                                ),
                                width="70%",
                                align="start",
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Código Único *", size="1", weight="bold", color="#334155"),
                                rx.input(
                                    placeholder="PRJ-COB",
                                    value=FlowState.new_proj_code,
                                    on_change=FlowState.set_new_proj_code,
                                    width="100%",
                                    size="2",
                                ),
                                width="30%",
                                align="start",
                                spacing="1",
                            ),
                            width="100%",
                            spacing="3",
                        ),
                        rx.vstack(
                            rx.text("Propósito y Alcance Operativo *", size="1", weight="bold", color="#334155"),
                            rx.text_area(
                                placeholder="Describe el objetivo del proceso, qué dolor resuelve y su alcance...",
                                value=FlowState.new_proj_purpose,
                                on_change=FlowState.set_new_proj_purpose,
                                width="100%",
                                size="2",
                                rows="4",
                            ),
                            width="100%",
                            align="start",
                            spacing="1",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.box(),
                ),

                # STEP 2: Plan & Integraciones
                rx.cond(
                    FlowState.new_proj_wizard_step == 2,
                    rx.vstack(
                        rx.hstack(
                            rx.vstack(
                                rx.text("Project Manager / Responsable", size="1", weight="bold", color="#334155"),
                                rx.input(
                                    placeholder="Ing. José Antonio Hurtado",
                                    value=FlowState.new_proj_manager,
                                    on_change=FlowState.set_new_proj_manager,
                                    width="100%",
                                    size="2",
                                ),
                                width="50%",
                                align="start",
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Sponsor / Área Líder", size="1", weight="bold", color="#334155"),
                                rx.input(
                                    placeholder="Dirección de Operaciones & Tecnología",
                                    value=FlowState.new_proj_sponsor,
                                    on_change=FlowState.set_new_proj_sponsor,
                                    width="100%",
                                    size="2",
                                ),
                                width="50%",
                                align="start",
                                spacing="1",
                            ),
                            width="100%",
                            spacing="3",
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Fecha Inicio", size="1", weight="bold", color="#334155"),
                                rx.input(
                                    type="date",
                                    value=FlowState.new_proj_start_date,
                                    on_change=FlowState.set_new_proj_start_date,
                                    width="100%",
                                    size="2",
                                ),
                                width="50%",
                                align="start",
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Fecha Fin Estimada", size="1", weight="bold", color="#334155"),
                                rx.input(
                                    type="date",
                                    value=FlowState.new_proj_end_date,
                                    on_change=FlowState.set_new_proj_end_date,
                                    width="100%",
                                    size="2",
                                ),
                                width="50%",
                                align="start",
                                spacing="1",
                            ),
                            width="100%",
                            spacing="3",
                        ),
                        # Integrations Callout
                        rx.callout(
                            "Se creará automáticamente la estructura oficial de 11 carpetas en Google Drive y se sincronizará la hoja de cálculo de planeación con la Service Account.",
                            icon="info",
                            color_scheme="blue",
                            size="1",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.box(),
                ),

                # STEP 3: Revisar & Confirmar
                rx.cond(
                    FlowState.new_proj_wizard_step == 3,
                    rx.vstack(
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.text("Proyecto:", size="1", weight="bold", color="#64748b", width="120px"),
                                    rx.text(FlowState.new_proj_name, size="2", weight="bold", color="#0f172a"),
                                    align="center",
                                ),
                                rx.hstack(
                                    rx.text("Código:", size="1", weight="bold", color="#64748b", width="120px"),
                                    rx.badge(FlowState.new_proj_code, color_scheme="indigo", variant="surface", size="1"),
                                    align="center",
                                ),
                                rx.hstack(
                                    rx.text("Responsable / PM:", size="1", weight="bold", color="#64748b", width="120px"),
                                    rx.text(FlowState.new_proj_manager, size="1", color="#1e293b"),
                                    align="center",
                                ),
                                rx.hstack(
                                    rx.text("Sponsor:", size="1", weight="bold", color="#64748b", width="120px"),
                                    rx.text(FlowState.new_proj_sponsor, size="1", color="#1e293b"),
                                    align="center",
                                ),
                                rx.hstack(
                                    rx.text("Cronograma:", size="1", weight="bold", color="#64748b", width="120px"),
                                    rx.text(FlowState.new_proj_start_date, " al ", FlowState.new_proj_end_date, size="1", color="#1e293b"),
                                    align="center",
                                ),
                                rx.hstack(
                                    rx.text("Propósito:", size="1", weight="bold", color="#64748b", width="120px"),
                                    rx.text(FlowState.new_proj_purpose, size="1", color="#64748b", line_clamp=2),
                                    align="start",
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            padding="3",
                            background_color="#f8fafc",
                            border="1px solid #e2e8f0",
                            border_radius="8px",
                            width="100%",
                        ),
                        # Live Drive Creation Progress Message
                        rx.cond(
                            FlowState.is_creating_project_drive,
                            rx.callout(
                                FlowState.creation_progress_status,
                                icon="loader",
                                color_scheme="blue",
                                size="1",
                            ),
                            rx.box(),
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.box(),
                ),

                # Modal Footer with Step Navigation
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        color_scheme="gray",
                        variant="soft",
                        size="2",
                        on_click=FlowState.close_new_project_modal,
                    ),
                    rx.spacer(),
                    # Previous Step Button
                    rx.cond(
                        FlowState.new_proj_wizard_step > 1,
                        rx.button(
                            rx.hstack(rx.icon("chevron-left", size=14), rx.text("Atrás"), align="center", spacing="1"),
                            on_click=FlowState.prev_wizard_step,
                            color_scheme="gray",
                            variant="surface",
                            size="2",
                        ),
                        rx.box(),
                    ),
                    # Next Step Button (for steps 1 & 2)
                    rx.cond(
                        FlowState.new_proj_wizard_step < 3,
                        rx.button(
                            rx.hstack(rx.text("Siguiente"), rx.icon("chevron-right", size=14), align="center", spacing="1"),
                            on_click=FlowState.next_wizard_step,
                            color_scheme="blue",
                            size="2",
                        ),
                        # Final Submit Button (for step 3)
                        rx.button(
                            rx.hstack(
                                rx.icon("cloud-upload", size=15),
                                rx.text("Confirmar & Desplegar en Drive"),
                                align="center",
                                spacing="1",
                            ),
                            on_click=FlowState.create_project_with_drive,
                            loading=FlowState.is_creating_project_drive,
                            color_scheme="blue",
                            size="2",
                            radius="medium",
                        ),
                    ),
                    width="100%",
                    align="center",
                    margin_top="2",
                ),
                spacing="4",
                width="100%",
            ),
            width="600px",
            max_width="95vw",
            border_radius="xl",
            padding="5",
            background_color="#ffffff",
        ),
        open=FlowState.show_new_project_modal,
        on_open_change=FlowState.set_show_new_project_modal,
    )


def project_hub() -> rx.Component:
    """Main Project Hub View (Level 1 Portafolio)"""
    return rx.box(
        new_project_modal(),
        delete_project_modal(),
        rx.vstack(
            # 1. Top App Header for Hub
            rx.hstack(
                rx.hstack(
                    rx.icon("network", size=24, color="#38bdf8"),
                    rx.vstack(
                        rx.hstack(
                            rx.text("TEMIS", size="4", weight="bold", color="#ffffff"),
                            rx.badge("Work OS Enterprise", color_scheme="indigo", variant="surface", size="1"),
                            align="center",
                            spacing="2",
                        ),
                        rx.text("Hub de Portafolio & Gobernanza de Procesos", size="1", color="#cbd5e1"),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.spacer(),
                # Subview Switcher: Portfolio vs Users Control (No Emojis)
                rx.segmented_control.root(
                    rx.segmented_control.item("Portafolio de Proyectos", value="portfolio"),
                    rx.segmented_control.item("Control de Usuarios", value="users"),
                    value=FlowState.hub_active_subview,
                    on_change=FlowState.set_hub_active_subview,
                    size="2",
                    radius="medium",
                ),
                rx.spacer(),
                # User Profile & Action Buttons
                rx.hstack(
                    rx.hstack(
                        rx.avatar(
                            fallback=FlowState.user_initials,
                            size="2",
                            radius="full",
                            color_scheme="indigo",
                        ),
                        rx.vstack(
                            rx.text(FlowState.user_name, size="1", weight="bold", color="#ffffff"),
                            rx.text(FlowState.user_email, size="1", color="#cbd5e1"),
                            spacing="0",
                            align="start",
                        ),
                        align="center",
                        spacing="2",
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon("plus", size=15),
                            rx.text("Nuevo Proyecto"),
                            align="center",
                            spacing="1",
                        ),
                        on_click=FlowState.open_new_project_modal,
                        color_scheme="blue",
                        size="2",
                        radius="medium",
                    ),
                    rx.divider(orientation="vertical", size="2"),
                    rx.button(
                        rx.hstack(
                            rx.icon("log-out", size=14),
                            rx.text("Salir"),
                            align="center",
                            spacing="1",
                        ),
                        on_click=FlowState.logout,
                        color_scheme="ruby",
                        variant="soft",
                        size="2",
                        radius="medium",
                        title="Cerrar Sesión",
                    ),
                    align="center",
                    spacing="2",
                ),
                width="100%",
                height="60px",
                align="center",
                padding_x="6",
                background_color="#17324d",
                border_bottom="1px solid #0f2338",
                box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.1)",
            ),

            # 2. Main Content Container
            rx.box(
                rx.vstack(
                    # Executive KPIs Grid (Responsive 1/2/4 cols, Pure Lucide Icons)
                    rx.grid(
                        kpi_card(
                            "Proyectos en Portafolio",
                            FlowState.total_hub_projects_count.to_string(),
                            FlowState.hub_drive_status_summary,
                            "folder-kanban",
                            "#1e5a9a",
                            badge_text="Activos",
                        ),
                        kpi_card(
                            "Story Points Entregados",
                            FlowState.total_completed_sp_count.to_string() + " / " + FlowState.total_sp_count.to_string() + " SP",
                            FlowState.global_progress_pct.to_string() + "% de avance global",
                            "circle-check",
                            "#107c41",
                            badge_text="Scrum",
                        ),
                        kpi_card(
                            "Calidad Six Sigma Promedio",
                            FlowState.average_audit_score.to_string() + " / 100",
                            "Auditoría con IA Gemini 2.5",
                            "shield-check",
                            "#6d28d9",
                            badge_text="IA",
                        ),
                        kpi_card(
                            "Sprints en Ejecución",
                            FlowState.active_sprints_count.to_string() + " Sprints",
                            "Calendario Técnico 2026",
                            "flame",
                            "#b76e00",
                            badge_text="En Curso",
                        ),
                        columns={"initial": "1", "sm": "2", "md": "4"},
                        spacing="4",
                        width="100%",
                    ),

                    # Executive Attention Banner (Action-Driven Section)
                    rx.cond(
                        FlowState.projects_needing_attention.length() > 0,
                        rx.box(
                            rx.hstack(
                                rx.box(
                                    rx.icon("triangle-alert", size=18, color="#b45309"),
                                    padding="2",
                                    background_color="#fef3c7",
                                    border_radius="8px",
                                ),
                                rx.vstack(
                                    rx.hstack(
                                        rx.text("Requieren Atención:", size="2", weight="bold", color="#92400e"),
                                        rx.cond(
                                            FlowState.projects_needing_attention.length() == 1,
                                            rx.text("1 proyecto en riesgo o con entregables pendientes.", size="2", color="#78350f"),
                                            rx.text(FlowState.projects_needing_attention.length().to_string(), " proyectos en riesgo o con entregables pendientes.", size="2", color="#78350f"),
                                        ),
                                        spacing="1",
                                    ),
                                    rx.text("Revisa los sprints y cuellos de botella para mitigar retrasos operativos.", size="1", color="#92400e"),
                                    spacing="0",
                                ),
                                rx.spacer(),
                                rx.button(
                                    rx.hstack(rx.icon("filter", size=12), rx.text("Filtrar en Riesgo"), align="center", spacing="1"),
                                    on_click=lambda: FlowState.set_filter_hub_status("yellow"),
                                    color_scheme="amber",
                                    variant="solid",
                                    size="1",
                                    radius="medium",
                                ),
                                width="100%",
                                align="center",
                                spacing="3",
                            ),
                            padding="3",
                            background_color="#fffbeb",
                            border="1px solid #fde68a",
                            border_radius="10px",
                            width="100%",
                        ),
                        rx.box(),
                    ),

                    # Filter and Search Bar (Polished White Card with Slate Border)
                    rx.hstack(
                        # Search Input
                        rx.hstack(
                            rx.icon("search", size=15, color="#52657a"),
                            rx.input(
                                placeholder="Buscar proyecto por nombre, código, responsable o sprint...",
                                value=FlowState.search_hub_query,
                                on_change=FlowState.set_search_hub_query,
                                width="340px",
                                size="1",
                                variant="surface",
                                radius="medium",
                            ),
                            align="center",
                            spacing="2",
                            padding_x="2",
                            padding_y="1",
                            background_color="#ffffff",
                            border="1px solid #d9e2ec",
                            border_radius="8px",
                        ),
                        rx.spacer(),
                        # Phase Filter
                        rx.hstack(
                            rx.text("Fase:", size="1", color="#52657a", weight="medium"),
                            rx.select.root(
                                rx.select.trigger(placeholder="Todas las Fases", size="1"),
                                rx.select.content(
                                    rx.select.item("Todas las Fases", value="all"),
                                    rx.select.item("Fase 1: Diagnóstico", value="1"),
                                    rx.select.item("Fase 2: Inicio", value="2"),
                                    rx.select.item("Fase 3: Planificación", value="3"),
                                    rx.select.item("Fase 4: Ejecución", value="4"),
                                    rx.select.item("Fase 5: Monitoreo", value="5"),
                                    rx.select.item("Fase 6: Mejora Continua", value="6"),
                                    rx.select.item("Fase 7: Cierre", value="7"),
                                ),
                                value=FlowState.filter_hub_phase,
                                on_change=FlowState.set_filter_hub_phase,
                            ),
                            align="center",
                            spacing="2",
                        ),
                        # Status Filter (Clean, No Emojis)
                        rx.hstack(
                            rx.text("Salud:", size="1", color="#52657a", weight="medium"),
                            rx.select.root(
                                rx.select.trigger(placeholder="Todos", size="1"),
                                rx.select.content(
                                    rx.select.item("Todos los Estados", value="all"),
                                    rx.select.item("Al día (Verde)", value="green"),
                                    rx.select.item("En riesgo (Amarillo)", value="yellow"),
                                    rx.select.item("Bloqueado (Rojo)", value="red"),
                                    rx.select.item("Sin evaluar", value="unrated"),
                                ),
                                value=FlowState.filter_hub_status,
                                on_change=FlowState.set_filter_hub_status,
                            ),
                            align="center",
                            spacing="2",
                        ),
                        width="100%",
                        align="center",
                        padding_y="2",
                    ),

                    # Projects Grid List
                    rx.cond(
                        FlowState.filtered_hub_projects.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                FlowState.filtered_hub_projects,
                                project_card,
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.icon("folder-open", size=48, color="#8295a9"),
                                rx.text("No se encontraron proyectos con los filtros seleccionados.", size="3", weight="medium", color="#17283c"),
                                rx.text("Intenta cambiar el criterio de búsqueda o crea un nuevo proyecto.", size="2", color="#52657a"),
                                rx.cond(
                                    (FlowState.search_hub_query != "") | (FlowState.filter_hub_phase != "all") | (FlowState.filter_hub_status != "all"),
                                    rx.hstack(
                                        rx.button(
                                            rx.hstack(rx.icon("rotate-ccw", size=14), rx.text("Limpiar Filtros"), align="center", spacing="1"),
                                            on_click=FlowState.clear_hub_filters,
                                            color_scheme="gray",
                                            variant="soft",
                                            size="2",
                                        ),
                                        rx.button(
                                            rx.hstack(rx.icon("plus", size=14), rx.text("Crear Nuevo Proyecto"), align="center", spacing="1"),
                                            on_click=FlowState.open_new_project_modal,
                                            color_scheme="blue",
                                            size="2",
                                        ),
                                        spacing="2",
                                        margin_top="2",
                                    ),
                                    rx.button(
                                        rx.hstack(rx.icon("plus", size=14), rx.text("Crear Primer Proyecto"), align="center", spacing="1"),
                                        on_click=FlowState.open_new_project_modal,
                                        color_scheme="blue",
                                        size="2",
                                        margin_top="2",
                                    ),
                                ),
                                align="center",
                                spacing="2",
                            ),
                            padding="12",
                            background_color="#ffffff",
                            border="1px dashed #d9e2ec",
                            border_radius="12px",
                            text_align="center",
                            width="100%",
                        ),
                    ),
                    spacing="5",
                    width="100%",
                    max_width="1280px",
                    margin_x="auto",
                ),
                padding="6",
                width="100%",
                flex="1",
                overflow_y="auto",
            ),
            width="100%",
            height="100vh",
            spacing="0",
        ),
        background_color="#f3f6fa",
        font_family="Inter, sans-serif",
        width="100%",
        height="100vh",
    )
