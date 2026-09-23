#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Workspace Sidebar Component for TEMIS Web Flow
Modern 230px collapsible left-hand navigation sidebar (Linear / Notion / Monday.com style)
Organizes project workflows into: Charter, Plan, Process Modeling (BPMN / SIPOC) and Governance.
"""

import reflex as rx
from temis_web.state import FlowState


def nav_item(label: str, icon_name: str, view_value: str, badge_text: str = "") -> rx.Component:
    """Render an interactive navigation item in the sidebar"""
    is_active = FlowState.active_view == view_value
    return rx.box(
        rx.hstack(
            rx.icon(
                icon_name,
                size=16,
                color=rx.cond(is_active, "#38bdf8", "#94a3b8"),
            ),
            rx.text(
                label,
                size="2",
                weight=rx.cond(is_active, "bold", "medium"),
                color=rx.cond(is_active, "#f8fafc", "#94a3b8"),
            ),
            rx.spacer(),
            rx.cond(
                badge_text != "",
                rx.badge(badge_text, color_scheme="blue", variant="soft", size="1"),
                rx.box(),
            ),
            align="center",
            spacing="2",
            width="100%",
        ),
        on_click=lambda: FlowState.set_active_view(view_value),
        padding_x="3",
        padding_y="2",
        border_radius="8px",
        background_color=rx.cond(is_active, "rgba(59, 130, 246, 0.15)", "transparent"),
        border=rx.cond(is_active, "1px solid rgba(59, 130, 246, 0.35)", "1px solid transparent"),
        cursor="pointer",
        role="button",
        tab_index=0,
        width="100%",
        _hover={
            "background_color": rx.cond(is_active, "rgba(59, 130, 246, 0.2)", "rgba(255, 255, 255, 0.04)"),
            "border_color": rx.cond(is_active, "rgba(59, 130, 246, 0.4)", "rgba(255, 255, 255, 0.08)"),
        },
        _focus_visible={
            "outline": "2px solid #3b82f6",
            "outline_offset": "2px",
        },
        transition="all 0.15s ease",
    )


def workspace_sidebar() -> rx.Component:
    """Left navigation sidebar for Level 2 Workspace"""
    return rx.box(
        rx.vstack(
            # 1. Back to Portfolio Navigation Header
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("arrow-left", size=14),
                        rx.text("Portafolio", size="1", weight="bold"),
                        align="center",
                        spacing="1",
                    ),
                    on_click=FlowState.return_to_hub,
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                    radius="medium",
                ),
                rx.spacer(),
                rx.badge("Workspace", color_scheme="indigo", variant="surface", size="1"),
                width="100%",
                align="center",
                padding_bottom="2",
                border_bottom="1px solid #1e293b",
            ),

            # 2. Active Project Context Box
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.badge(FlowState.project_code, color_scheme="indigo", variant="solid", size="1"),
                        rx.spacer(),
                        rx.badge(
                            FlowState.phase_name,
                            color_scheme="purple",
                            variant="soft",
                            size="1",
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.text(
                        FlowState.project_name,
                        size="2",
                        weight="bold",
                        color="#f8fafc",
                        max_width="100%",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                    ),
                    rx.hstack(
                        rx.icon("user", size=12, color="#94a3b8"),
                        rx.text(FlowState.project_manager, size="1", color="#94a3b8"),
                        align="center",
                        spacing="1",
                    ),
                    spacing="1",
                    width="100%",
                ),
                padding="3",
                background_color="#131b2e",
                border="1px solid #1e293b",
                border_radius="8px",
                box_shadow="0 1px 2px 0 rgba(0, 0, 0, 0.4)",
                width="100%",
            ),

            # 3. Navigation Groups
            rx.vstack(
                # Group 1: Definición & Planificación
                rx.vstack(
                    rx.text("DEFINICIÓN & PLAN", size="1", weight="bold", color="#64748b", letter_spacing="0.05em"),
                    nav_item("Ficha del Proyecto", "file-text", "charter"),
                    nav_item("Plan & Backlog Scrum", "calendar-range", "plan"),
                    spacing="1",
                    width="100%",
                ),

                # Group 2: Modelado de Procesos
                rx.vstack(
                    rx.text("MODELADO DE PROCESOS", size="1", weight="bold", color="#64748b", letter_spacing="0.05em"),
                    nav_item("Diagrama de Flujo (BPMN)", "network", "flow"),
                    nav_item("Matriz SIPOC Tabular", "table-2", "sipoc"),
                    spacing="1",
                    width="100%",
                ),

                # Group 3: Gobernanza & Calidad
                rx.vstack(
                    rx.text("GOBERNANZA & CALIDAD", size="1", weight="bold", color="#64748b", letter_spacing="0.05em"),
                    nav_item("Metodología 7 Fases", "layers", "governance"),
                    rx.box(
                        rx.hstack(
                            rx.icon("shield-check", size=16, color="#a855f7"),
                            rx.text("Auditoría IA (0-100)", size="2", weight="medium", color="#c084fc"),
                            rx.spacer(),
                            rx.badge("Six Sigma", color_scheme="purple", variant="soft", size="1"),
                            align="center",
                            spacing="2",
                            width="100%",
                        ),
                        on_click=FlowState.open_audit_modal,
                        padding_x="3",
                        padding_y="2",
                        border_radius="8px",
                        background_color="rgba(139, 92, 246, 0.12)",
                        border="1px solid rgba(139, 92, 246, 0.3)",
                        cursor="pointer",
                        width="100%",
                        _hover={"background_color": "rgba(139, 92, 246, 0.2)"},
                    ),
                    spacing="1",
                    width="100%",
                ),

                spacing="4",
                width="100%",
                padding_y="2",
                flex="1",
            ),

            # 4. External Integrations Shortcuts
            rx.vstack(
                rx.divider(),
                rx.hstack(
                    rx.cond(
                        FlowState.drive_folder_url != "",
                        rx.button(
                            rx.hstack(
                                rx.icon("folder-open", size=13),
                                rx.text("Drive", size="1"),
                                align="center",
                                spacing="1",
                            ),
                            on_click=rx.redirect(FlowState.drive_folder_url, is_external=True),
                            color_scheme="gray",
                            variant="soft",
                            size="1",
                            radius="medium",
                            title="Abrir carpeta en Google Drive",
                        ),
                        rx.box(),
                    ),
                    rx.cond(
                        FlowState.sheet_url != "",
                        rx.button(
                            rx.hstack(
                                rx.icon("file-spreadsheet", size=13),
                                rx.text("Sheet", size="1"),
                                align="center",
                                spacing="1",
                            ),
                            on_click=rx.redirect(FlowState.sheet_url, is_external=True),
                            color_scheme="green",
                            variant="soft",
                            size="1",
                            radius="medium",
                            title="Abrir hoja de cálculo en Google Sheets",
                        ),
                        rx.box(),
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon("save", size=13),
                            rx.text("Guardar", size="1"),
                            align="center",
                            spacing="1",
                        ),
                        on_click=FlowState.save_current_project,
                        color_scheme="blue",
                        variant="soft",
                        size="1",
                        radius="medium",
                        title="Guardar estado del proyecto",
                    ),
                    width="100%",
                    align="center",
                    spacing="2",
                ),
                spacing="2",
                width="100%",
                padding_top="2",
            ),
            spacing="3",
            width="100%",
            height="100%",
        ),
        width="240px",
        min_width="240px",
        max_width="240px",
        height="100vh",
        background_color="#0f172a",
        border_right="1px solid #1e293b",
        padding="3",
        box_shadow="1px 0 3px 0 rgba(0, 0, 0, 0.4)",
        display="flex",
        flex_direction="column",
    )
