#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Work Plan & Capacity Planner View (Planificador Inteligente de Trabajo) for TEMIS
Integrates parameter configuration, capacity calculation, Gemini 2.5 Flash AI generation,
interactive Scrum Backlog, Sprints Agenda, and two-way Google Sheets synchronization.
"""

import reflex as rx
from temis_web.state import FlowState


def capacity_stat(title: str, value: rx.Var[str] | str, subtitle: str, icon_name: str, color_hex: str) -> rx.Component:
    """Render a compact stat badge in the capacity dashboard"""
    return rx.hstack(
        rx.box(
            rx.icon(icon_name, size=18, color=color_hex),
            padding="2",
            background_color=f"{color_hex}15",
            border_radius="6px",
        ),
        rx.vstack(
            rx.text(title, size="1", color="#59697b", weight="medium"),
            rx.hstack(
                rx.text(value, size="3", weight="bold", color="#17283c"),
                rx.text(subtitle, size="1", color="#8b9bae"),
                align="baseline",
                spacing="1",
            ),
            spacing="0",
            align="start",
        ),
        padding="2",
        background_color="#ffffff",
        border="1px solid #d7e0ea",
        border_radius="8px",
        box_shadow="0 1px 2px 0 rgba(0, 0, 0, 0.02)",
        align="center",
        spacing="2",
        flex="1",
        min_width="160px",
    )


def render_backlog_row(item: rx.Var[dict]) -> rx.Component:
    """Render a single task/user story row in the Scrum Backlog Table"""
    return rx.table.row(
        rx.table.cell(
            rx.text(item["item_id"], size="1", weight="bold", color="#64748b"),
            align="center",
        ),
        rx.table.cell(
            rx.badge(item["module"], color_scheme="indigo", variant="soft", size="1"),
            align="left",
        ),
        rx.table.cell(
            rx.vstack(
                rx.text(item["user_story"], size="2", weight="medium", color="#17283c"),
                rx.cond(
                    item["deliverable"] != "",
                    rx.hstack(
                        rx.icon("package", size=12, color="#059669"),
                        rx.hstack(
                            rx.text("Entregable:", size="1", color="#059669"),
                            rx.text(item["deliverable"], size="1", color="#059669"),
                            spacing="1",
                        ),
                        align="center",
                        spacing="1",
                    ),
                    rx.box(),
                ),
                spacing="1",
                align="start",
            ),
            align="left",
        ),
        rx.table.cell(
            rx.badge(
                rx.hstack(
                    rx.icon("flame", size=12, color="#ea580c"),
                    rx.text(item["sprint"]),
                    align="center",
                    spacing="1",
                ),
                color_scheme="orange",
                variant="soft",
                size="1",
            ),
            align="center",
        ),
        rx.table.cell(
            rx.badge(item["story_points"].to_string(), " SP", color_scheme="blue", variant="surface", size="1"),
            align="center",
        ),
        rx.table.cell(
            rx.badge(item["hours_estimated"].to_string(), " hrs", color_scheme="gray", variant="soft", size="1"),
            align="center",
        ),
        rx.table.cell(
            rx.vstack(
                rx.text(item["start_date"], size="1", color="#475569"),
                rx.hstack(
                    rx.text("al", size="1", color="#94a3b8"),
                    rx.text(item["end_date"], size="1", color="#94a3b8"),
                    spacing="1",
                ),
                spacing="0",
                align="center",
            ),
            align="center",
        ),
        rx.table.cell(
            rx.badge(item["role"], color_scheme="purple", variant="soft", size="1"),
            align="left",
        ),
        rx.table.cell(
            rx.cond(
                item["priority"] == "Alta",
                rx.badge(rx.hstack(rx.icon("alert-circle", size=10), rx.text("Alta"), align="center", spacing="1"), color_scheme="ruby", variant="soft", size="1"),
                rx.cond(
                    item["priority"] == "Media",
                    rx.badge(rx.hstack(rx.icon("alert-triangle", size=10), rx.text("Media"), align="center", spacing="1"), color_scheme="amber", variant="soft", size="1"),
                    rx.badge(rx.hstack(rx.icon("circle", size=10), rx.text("Baja"), align="center", spacing="1"), color_scheme="green", variant="soft", size="1"),
                ),
            ),
            align="center",
        ),
        rx.table.cell(
            rx.icon_button(
                rx.icon("trash-2", size=13),
                on_click=lambda: FlowState.delete_backlog_item(item["item_id"]),
                color_scheme="ruby",
                variant="ghost",
                size="1",
            ),
            align="center",
        ),
    )


def render_sprint_card(sprint: rx.Var[dict]) -> rx.Component:
    """Render a card for an individual Sprint in the Timeline view"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("flame", size=18, color="#ea580c"),
                    rx.text(sprint["sprint_id"], size="3", weight="bold", color="#0f172a"),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                rx.cond(
                    sprint["status"] == "In Progress",
                    rx.badge(rx.hstack(rx.icon("flame", size=11), rx.text("En Progreso"), align="center", spacing="1"), color_scheme="orange", variant="surface", size="1"),
                    rx.badge(rx.hstack(rx.icon("calendar", size=11), rx.text("Planificado"), align="center", spacing="1"), color_scheme="gray", variant="soft", size="1"),
                ),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.icon("calendar", size=13, color="#64748b"),
                rx.text(sprint["period"], size="1", weight="medium", color="#475569"),
                align="center",
                spacing="1",
            ),
            rx.divider(color_scheme="gray", opacity=0.3),
            rx.vstack(
                rx.text("Objetivo Central:", size="1", weight="bold", color="#334155"),
                rx.text(sprint["objective"], size="2", color="#64748b"),
                spacing="1",
                align="start",
            ),
            rx.hstack(
                rx.badge("Módulo: ", sprint["modules"], color_scheme="indigo", variant="soft", size="1"),
                rx.badge("Hito: ", sprint["milestone"], color_scheme="green", variant="soft", size="1"),
                wrap="wrap",
                spacing="1",
            ),
            rx.divider(color_scheme="gray", opacity=0.3),
            rx.hstack(
                rx.badge(sprint["story_points"].to_string(), " Story Points", color_scheme="blue", variant="surface", size="1"),
                rx.badge(sprint["hours_estimated"].to_string(), " Horas Estimadas", color_scheme="gray", variant="soft", size="1"),
                width="100%",
                align="center",
            ),
            spacing="3",
            width="100%",
        ),
        padding="4",
        background_color="#ffffff",
        border="1px solid #e2e8f0",
        border_radius="10px",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.02)",
        flex="1",
        min_width="320px",
        max_width="400px",
        _hover={
            "border_color": "#cbd5e1",
            "box_shadow": "0 4px 10px 0 rgba(0, 0, 0, 0.04)",
        },
    )


def work_plan_view() -> rx.Component:
    """Main Work Plan & Capacity Planner View (Planificador Inteligente de Trabajo)"""
    return rx.box(
        rx.vstack(
            # 1. Top Section: Planning Parameters & Capacity Calculator
            rx.box(
                rx.vstack(
                    # Header Banner
                    rx.hstack(
                        rx.hstack(
                            rx.icon("calendar-clock", size=22, color="#2563eb"),
                            rx.vstack(
                                rx.text("Plan de Trabajo & Planificador Inteligente de Sprints", size="4", weight="bold", color="#17283c"),
                                rx.text("Configura la capacidad laboral y genera la distribución automática de Sprints y Backlog con Gemini 2.5 Flash", size="2", color="#59697b"),
                                spacing="0",
                            ),
                            align="center",
                            spacing="3",
                        ),
                        rx.spacer(),
                        # Action Buttons: Gemini Generator & Sheet Sync
                        rx.hstack(
                            rx.button(
                                rx.icon("sparkles", size=15),
                                " Generar con Gemini AI",
                                on_click=FlowState.generate_work_plan_ai,
                                loading=FlowState.is_generating_plan_ai,
                                color_scheme="indigo",
                                size="2",
                                radius="medium",
                            ),
                            rx.button(
                                rx.icon("cloud-upload", size=15),
                                " Sincronizar Google Sheet",
                                on_click=FlowState.sync_work_plan_to_google_sheet,
                                loading=FlowState.is_syncing_plan_sheet,
                                color_scheme="green",
                                size="2",
                                radius="medium",
                            ),
                            rx.cond(
                                FlowState.sheet_url != "",
                                rx.link(
                                    rx.button(
                                        rx.icon("external-link", size=14),
                                        " Abrir Sheet",
                                        color_scheme="gray",
                                        variant="soft",
                                        size="2",
                                        radius="medium",
                                    ),
                                    href=FlowState.sheet_url,
                                    is_external=True,
                                ),
                                rx.box(),
                            ),
                            spacing="2",
                            align="center",
                        ),
                        width="100%",
                        align="center",
                    ),

                    rx.divider(color_scheme="gray", opacity=0.3),

                    # Inputs Row: Dates, Hours/Day, Work Days Scheme
                    rx.hstack(
                        rx.vstack(
                            rx.text("Fecha Inicio:", size="1", weight="bold", color="#475569"),
                            rx.input(
                                type="date",
                                value=FlowState.plan_start_date,
                                on_change=FlowState.set_plan_start_date,
                                size="1",
                                width="100%",
                            ),
                            width="20%",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Fecha Término:", size="1", weight="bold", color="#475569"),
                            rx.input(
                                type="date",
                                value=FlowState.plan_end_date,
                                on_change=FlowState.set_plan_end_date,
                                size="1",
                                width="100%",
                            ),
                            width="20%",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Jornada Diaria:", size="1", weight="bold", color="#475569"),
                            rx.select.root(
                                rx.select.trigger(size="1"),
                                rx.select.content(
                                    rx.select.item("8 horas (Completa)", value="8"),
                                    rx.select.item("6 horas", value="6"),
                                    rx.select.item("4 horas (Medio tiempo)", value="4"),
                                    rx.select.item("2 horas", value="2"),
                                ),
                                value=FlowState.plan_daily_hours.to_string(),
                                on_change=FlowState.set_plan_daily_hours,
                            ),
                            width="25%",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text("Régimen Semanal:", size="1", weight="bold", color="#475569"),
                            rx.select.root(
                                rx.select.trigger(size="1"),
                                rx.select.content(
                                    rx.select.item("Lunes a Viernes (5 días)", value="mon_fri"),
                                    rx.select.item("Lunes a Sábado (6 días)", value="mon_sat"),
                                    rx.select.item("Toda la semana (7 días)", value="full_week"),
                                ),
                                value=FlowState.plan_work_days_mode,
                                on_change=FlowState.set_plan_work_days_mode,
                            ),
                            width="35%",
                            spacing="1",
                        ),
                        width="100%",
                        spacing="3",
                        align="end",
                    ),

                    # Capacity KPI Badges Grid (Responsive 1/2/4 cols)
                    rx.grid(
                        capacity_stat(
                            "Días Hábiles Reales",
                            FlowState.plan_working_days_count.to_string() + " días",
                            "en calendario",
                            "calendar",
                            "#2563eb",
                        ),
                        capacity_stat(
                            "Capacidad Total Disponible",
                            FlowState.plan_total_capacity_hours.to_string() + " hrs",
                            "productivas",
                            "clock",
                            "#16a34a",
                        ),
                        capacity_stat(
                            "Sprints Recomendados",
                            FlowState.plan_suggested_sprints_count.to_string() + " Sprints",
                            "de 2 semanas",
                            "flame",
                            "#ea580c",
                        ),
                        capacity_stat(
                            "Horas Planificadas",
                            FlowState.plan_total_planned_hours.to_string() + " hrs",
                            "(" + FlowState.plan_total_sp.to_string() + " SP)",
                            "circle-check",
                            "#8b5cf6",
                        ),
                        columns={"initial": "1", "sm": "2", "md": "4"},
                        spacing="3",
                        width="100%",
                    ),

                    # Description Text Area for Gemini Scope Prompt
                    rx.vstack(
                        rx.text("Descripción de Actividades & Alcance del Proyecto (Prompt para IA):", size="1", weight="bold", color="#475569"),
                        rx.text_area(
                            placeholder="Describe qué actividades, módulos, integraciones, pruebas y entregables se realizarán (ej: 'Automatizar atención de aclaraciones por WhatsApp con conexión a Chronos y Freshdesk, incluyendo manuales, capacitación y auditoría Six Sigma')...",
                            value=FlowState.plan_activities_description,
                            on_change=FlowState.set_plan_activities_description,
                            width="100%",
                            size="2",
                            rows="2",
                            radius="medium",
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),
                padding="4",
                background_color="#ffffff",
                border="1px solid #e2e8f0",
                border_radius="10px",
                box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.02)",
                width="100%",
            ),

            # 2. Middle Section: Subtab Switcher & Filters
            rx.hstack(
                rx.segmented_control.root(
                    rx.segmented_control.item("Backlog Scrum Técnico (Tareas & SP)", value="backlog"),
                    rx.segmented_control.item("Agenda de Sprints (Cronograma)", value="sprints"),
                    value=FlowState.plan_active_subtab,
                    on_change=FlowState.set_plan_active_subtab,
                    size="2",
                    radius="medium",
                ),
                rx.spacer(),
                # Sprint Filter
                rx.cond(
                    FlowState.plan_active_subtab == "backlog",
                    rx.hstack(
                        rx.icon("search", size=14, color="#94a3b8"),
                        rx.input(
                            placeholder="Buscar en el backlog...",
                            value=FlowState.plan_search_query,
                            on_change=FlowState.set_plan_search_query,
                            width="220px",
                            size="1",
                            variant="soft",
                        ),
                        rx.select.root(
                            rx.select.trigger(placeholder="Filtrar por Sprint", size="1"),
                            rx.select.content(
                                rx.select.item("Todos los Sprints", value="all"),
                                rx.foreach(
                                    FlowState.plan_sprint_options,
                                    lambda s: rx.select.item(s, value=s),
                                ),
                            ),
                            value=FlowState.plan_filter_sprint,
                            on_change=FlowState.set_plan_filter_sprint,
                        ),
                        rx.button(
                            rx.icon("plus", size=13),
                            " Agregar Tarea",
                            on_click=FlowState.add_backlog_item,
                            color_scheme="indigo",
                            variant="soft",
                            size="1",
                            radius="medium",
                        ),
                        align="center",
                        spacing="2",
                        wrap="wrap",
                    ),
                    rx.box(),
                ),
                width="100%",
                align="center",
                padding_y="1",
                wrap="wrap",
            ),

            # 3. Main Body: Backlog Table vs Sprints Cards
            rx.cond(
                FlowState.plan_active_subtab == "backlog",
                # Subtab 1: Backlog Scrum Table
                rx.box(
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("ID", width="50px"),
                                    rx.table.column_header_cell("Módulo / Épica", width="150px"),
                                    rx.table.column_header_cell("Historia de Usuario / Tarea Técnica", min_width="320px"),
                                    rx.table.column_header_cell("Sprint", width="110px"),
                                    rx.table.column_header_cell("Story Points", width="90px"),
                                    rx.table.column_header_cell("Horas", width="80px"),
                                    rx.table.column_header_cell("Fechas", width="120px"),
                                    rx.table.column_header_cell("Rol Asignado", width="130px"),
                                    rx.table.column_header_cell("Prioridad", width="90px"),
                                    rx.table.column_header_cell("Acciones", width="60px"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    FlowState.plan_filtered_backlog,
                                    render_backlog_row,
                                ),
                            ),
                            variant="surface",
                            size="1",
                            width="100%",
                            min_width="940px",
                        ),
                        overflow_x="auto",
                        width="100%",
                    ),
                    background_color="#ffffff",
                    border="1px solid #d7e0ea",
                    border_radius="10px",
                    overflow="hidden",
                    width="100%",
                    max_height="calc(100vh - 420px)",
                    overflow_y="auto",
                    box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px 0 rgba(0, 0, 0, 0.02)",
                ),
                # Subtab 2: Sprints Agenda Cards
                rx.box(
                    rx.hstack(
                        rx.foreach(
                            FlowState.plan_sprints,
                            render_sprint_card,
                        ),
                        wrap="wrap",
                        spacing="3",
                        width="100%",
                        align="start",
                    ),
                    width="100%",
                    max_height="calc(100vh - 420px)",
                    overflow_y="auto",
                    padding="1",
                ),
            ),
            spacing="3",
            width="100%",
            height="100%",
        ),
        padding="4",
        width="100%",
        height="100%",
        overflow="hidden",
        background_color="#f3f6fa",
    )
