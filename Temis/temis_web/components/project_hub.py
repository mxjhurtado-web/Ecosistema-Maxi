#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project Hub Component (Level 1) for TEMIS Web Flow
Enterprise Work OS Portfolio Dashboard (Monday.com / Linear / Notion style)
Displays projects catalog, KPIs, live Backlog progress %, sprint status, and Google Drive sync.
"""

import reflex as rx
from temis_web.state import FlowState


def kpi_card(title: str, value: rx.Var[str] | str, subtitle: str, icon_name: str, color_hex: str, badge_text: str = "") -> rx.Component:
    """Render a single executive KPI metric card"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon(icon_name, size=20, color=color_hex),
                    padding="2",
                    background_color=f"{color_hex}15",
                    border_radius="8px",
                ),
                rx.spacer(),
                rx.cond(
                    badge_text != "",
                    rx.badge(badge_text, color_scheme="green", variant="soft", size="1"),
                    rx.box(),
                ),
                width="100%",
                align="center",
            ),
            rx.text(title, size="1", color="#64748b", weight="medium"),
            rx.text(value, size="6", weight="bold", color="#0f172a"),
            rx.text(subtitle, size="1", color="#94a3b8"),
            spacing="1",
            align="start",
            width="100%",
        ),
        padding="4",
        background_color="#ffffff",
        border="1px solid #e2e8f0",
        border_radius="12px",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.02)",
        flex="1",
        min_width="220px",
        _hover={
            "box_shadow": "0 4px 12px 0 rgba(0, 0, 0, 0.05)",
            "border_color": "#cbd5e1",
        },
    )


def project_card(proj: rx.Var[dict]) -> rx.Component:
    """Render an interactive project card in Monday.com style"""
    return rx.box(
        rx.vstack(
            # Card Top Row: Code, Name, Role badge & Action Menu
            rx.hstack(
                rx.hstack(
                    rx.badge(
                        proj["code"],
                        color_scheme="indigo",
                        variant="surface",
                        size="1",
                    ),
                    rx.text(
                        proj["name"],
                        size="3",
                        weight="bold",
                        color="#0f172a",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                # Health Semaphore Badge
                rx.cond(
                    proj["health_status"] == "green",
                    rx.badge("🟢 Al día", color_scheme="green", variant="soft", size="1"),
                    rx.cond(
                        proj["health_status"] == "yellow",
                        rx.badge("🟡 En riesgo", color_scheme="amber", variant="soft", size="1"),
                        rx.badge("🔴 Bloqueado", color_scheme="ruby", variant="soft", size="1"),
                    ),
                ),
                # Six Sigma Audit Score
                rx.badge(
                    rx.hstack(
                        rx.icon("shield-check", size=12),
                        rx.text(proj["audit_score"], "/100"),
                        align="center",
                        spacing="1",
                    ),
                    color_scheme="indigo",
                    variant="soft",
                    size="1",
                ),
                width="100%",
                align="center",
            ),

            # Purpose / Scope description
            rx.text(
                proj["purpose"],
                size="2",
                color="#64748b",
                max_width="100%",
                line_clamp=2,
            ),

            rx.divider(color_scheme="gray", opacity=0.3),

            # Middle Row: Governance Phase & Active Sprint
            rx.hstack(
                rx.hstack(
                    rx.icon("layers", size=14, color="#8b5cf6"),
                    rx.text("Fase ", proj["current_phase"].to_string(), ": ", proj["phase_name"], size="1", weight="medium", color="#6b21a8"),
                    align="center",
                    spacing="1",
                    padding_x="2",
                    padding_y="1",
                    background_color="#f3e8ff",
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
                    rx.text("Avance del Backlog Scrum:", size="1", color="#64748b", weight="medium"),
                    rx.spacer(),
                    rx.hstack(
                        rx.text(proj["progress_percentage"].to_string(), "% (", proj["completed_sp"].to_string(), "/", proj["total_sp"].to_string(), " SP)", size="1", weight="bold", color="#0f172a"),
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
                    color_scheme="indigo",
                ),
                spacing="1",
                width="100%",
            ),

            rx.divider(color_scheme="gray", opacity=0.3),

            # Bottom Row: Manager Avatar, Quick Links & Workspace Button
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
                        rx.text(proj["manager"], size="1", weight="medium", color="#1e293b"),
                        rx.hstack(
                            rx.text("Sponsor:", size="1", color="#94a3b8"),
                            rx.text(proj["sponsor"], size="1", color="#94a3b8"),
                            spacing="1",
                        ),
                        spacing="0",
                        align="start",
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                # External Links (Google Drive & Google Sheet)
                rx.hstack(
                    rx.cond(
                        proj["drive_folder_url"] != "",
                        rx.link(
                            rx.button(
                                rx.icon("folder-open", size=13),
                                " Drive",
                                color_scheme="gray",
                                variant="soft",
                                size="1",
                                radius="medium",
                            ),
                            href=proj["drive_folder_url"],
                            is_external=True,
                        ),
                        rx.box(),
                    ),
                    rx.cond(
                        proj["sheet_url"] != "",
                        rx.link(
                            rx.button(
                                rx.icon("file-spreadsheet", size=13),
                                " Plan de Trabajo",
                                color_scheme="green",
                                variant="soft",
                                size="1",
                                radius="medium",
                            ),
                            href=proj["sheet_url"],
                            is_external=True,
                        ),
                        rx.box(),
                    ),
                    # Primary Open Workspace Button
                    rx.button(
                        rx.icon("sparkles", size=14),
                        " Abrir Espacio de Trabajo",
                        on_click=lambda: FlowState.open_project_workspace(proj["id"]),
                        color_scheme="blue",
                        size="1",
                        radius="medium",
                    ),
                    align="center",
                    spacing="2",
                ),
                width="100%",
                align="center",
            ),
            spacing="3",
            width="100%",
        ),
        padding="4",
        background_color="#ffffff",
        border="1px solid #e2e8f0",
        border_radius="12px",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.02)",
        width="100%",
        _hover={
            "border_color": "#93c5fd",
            "box_shadow": "0 4px 12px 0 rgba(37, 99, 235, 0.06)",
        },
    )


def new_project_modal() -> rx.Component:
    """Dialog modal to create a new project and trigger Google Drive SA replication"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Modal Header
                rx.hstack(
                    rx.box(
                        rx.icon("plus", size=20, color="#2563eb"),
                        padding="2",
                        background_color="#eff6ff",
                        border_radius="8px",
                    ),
                    rx.vstack(
                        rx.dialog.title("Crear Nuevo Proyecto en TEMIS", size="4", weight="bold", color="#0f172a"),
                        rx.dialog.description(
                            "Inicializa el proyecto, crea las 11 carpetas en Google Drive y replica el Google Sheet de planeación.",
                            size="2",
                            color="#64748b",
                        ),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.divider(),

                # Form Fields
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
                            rx.text("Código *", size="1", weight="bold", color="#334155"),
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
                        rx.text("Propósito y Objetivo de Negocio *", size="1", weight="bold", color="#334155"),
                        rx.text_area(
                            placeholder="Describe para qué es el proyecto, qué soluciona y su alcance operativo...",
                            value=FlowState.new_proj_purpose,
                            on_change=FlowState.set_new_proj_purpose,
                            width="100%",
                            size="2",
                            rows="3",
                        ),
                        width="100%",
                        align="start",
                        spacing="1",
                    ),

                    rx.hstack(
                        rx.vstack(
                            rx.text("Project Manager / Responsable", size="1", weight="bold", color="#334155"),
                            rx.input(
                                placeholder="Ing. Mario Hurtado",
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
                                placeholder="Dirección de Operaciones",
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

                # Modal Footer
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        color_scheme="gray",
                        variant="soft",
                        size="2",
                        on_click=FlowState.close_new_project_modal,
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("cloud-upload", size=15),
                        " Crear Proyecto & Desplegar en Drive",
                        on_click=FlowState.create_project_with_drive,
                        loading=FlowState.is_creating_project_drive,
                        color_scheme="blue",
                        size="2",
                        radius="medium",
                    ),
                    width="100%",
                    align="center",
                    margin_top="2",
                ),
                spacing="4",
                width="100%",
            ),
            width="580px",
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
        rx.vstack(
            # 1. Top App Header for Hub
            rx.hstack(
                rx.hstack(
                    rx.icon("network", size=24, color="#2563eb"),
                    rx.vstack(
                        rx.hstack(
                            rx.text("TEMIS", size="4", weight="bold", color="#0f172a"),
                            rx.badge("Work OS Enterprise", color_scheme="indigo", variant="surface", size="1"),
                            align="center",
                            spacing="2",
                        ),
                        rx.text("Hub de Portafolio & Gobernanza de Procesos", size="1", color="#64748b"),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.spacer(),
                # Subview Switcher: Portfolio vs Users Control
                rx.segmented_control.root(
                    rx.segmented_control.item("📂 Portafolio de Proyectos", value="portfolio"),
                    rx.segmented_control.item("👥 Control de Usuarios", value="users"),
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
                            fallback=FlowState.user_name.to(lambda n: n[:2].upper() if n else "US"),
                            size="2",
                            radius="full",
                            color_scheme="indigo",
                        ),
                        rx.vstack(
                            rx.text(FlowState.user_name, size="1", weight="bold", color="#0f172a"),
                            rx.text(FlowState.user_email, size="1", color="#94a3b8"),
                            spacing="0",
                            align="start",
                        ),
                        align="center",
                        spacing="2",
                    ),
                    rx.button(
                        rx.icon("plus", size=15),
                        " Nuevo Proyecto",
                        on_click=FlowState.open_new_project_modal,
                        color_scheme="blue",
                        size="2",
                        radius="medium",
                    ),
                    rx.divider(orientation="vertical", size="2"),
                    rx.button(
                        rx.icon("log-out", size=14),
                        " Salir",
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
                background_color="#ffffff",
                border_bottom="1px solid #e2e8f0",
                box_shadow="0 1px 2px 0 rgba(0, 0, 0, 0.02)",
            ),

            # 2. Main Content Container
            rx.box(
                rx.vstack(
                    # Executive KPIs Row
                    rx.hstack(
                        kpi_card(
                            "Proyectos en Portafolio",
                            FlowState.total_hub_projects_count.to_string(),
                            "100% integrados con Google Drive",
                            "folder-kanban",
                            "#2563eb",
                            badge_text="Activos",
                        ),
                        kpi_card(
                            "Story Points Entregados",
                            FlowState.total_completed_sp_count.to_string() + " / " + FlowState.total_sp_count.to_string() + " SP",
                            FlowState.global_progress_pct.to_string() + "% de avance global",
                            "circle-check",
                            "#16a34a",
                            badge_text="Scrum",
                        ),
                        kpi_card(
                            "Calidad Six Sigma Promedio",
                            FlowState.average_audit_score.to_string() + " / 100",
                            "Auditoría con IA Gemini 2.5",
                            "shield-check",
                            "#8b5cf6",
                            badge_text="IA",
                        ),
                        kpi_card(
                            "Sprints en Ejecución",
                            FlowState.active_sprints_count.to_string() + " Sprints",
                            "Calendario Técnico 2026",
                            "flame",
                            "#ea580c",
                            badge_text="En Curso",
                        ),
                        width="100%",
                        spacing="4",
                        wrap="wrap",
                    ),

                    # Filter and Search Bar
                    rx.hstack(
                        # Search Input
                        rx.hstack(
                            rx.icon("search", size=15, color="#94a3b8"),
                            rx.input(
                                placeholder="Buscar proyecto por nombre, código, responsable o sprint...",
                                value=FlowState.search_hub_query,
                                on_change=FlowState.set_search_hub_query,
                                width="340px",
                                size="1",
                                variant="soft",
                                radius="medium",
                            ),
                            align="center",
                            spacing="2",
                        ),
                        rx.spacer(),
                        # Phase Filter
                        rx.hstack(
                            rx.text("Fase:", size="1", color="#64748b", weight="medium"),
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
                        # Status Filter
                        rx.hstack(
                            rx.text("Salud:", size="1", color="#64748b", weight="medium"),
                            rx.select.root(
                                rx.select.trigger(placeholder="Todos", size="1"),
                                rx.select.content(
                                    rx.select.item("Todos los Estados", value="all"),
                                    rx.select.item("🟢 Al día", value="green"),
                                    rx.select.item("🟡 En riesgo", value="yellow"),
                                    rx.select.item("🔴 Bloqueado", value="red"),
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
                                rx.icon("folder-open", size=48, color="#94a3b8"),
                                rx.text("No se encontraron proyectos con los filtros seleccionados.", size="3", weight="medium", color="#475569"),
                                rx.text("Intenta cambiar el criterio de búsqueda o crea un nuevo proyecto.", size="2", color="#94a3b8"),
                                rx.button(
                                    rx.icon("plus", size=14),
                                    " Crear Primer Proyecto",
                                    on_click=FlowState.open_new_project_modal,
                                    color_scheme="blue",
                                    size="2",
                                    margin_top="2",
                                ),
                                align="center",
                                spacing="2",
                            ),
                            padding="12",
                            background_color="#ffffff",
                            border="1px dashed #cbd5e1",
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
        background_color="#f8fafc",
        font_family="Inter, sans-serif",
        width="100%",
        height="100vh",
    )
