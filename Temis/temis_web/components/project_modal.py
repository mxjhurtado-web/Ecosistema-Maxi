#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Saved Flows & Projects Catalog Modal Component for TEMIS Web Flow
Dialog to browse, search, open, export and manage saved process flows
"""

import reflex as rx
from temis_web.state import FlowState


def render_saved_project_card(proj: rx.Var[dict]) -> rx.Component:
    """Render a single saved flow/project card in the catalog in dark theme"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.icon("network", size=16, color="#38bdf8"),
                        rx.text(proj["name"], size="3", weight="bold", color="#f8fafc"),
                        align="center",
                        spacing="2",
                    ),
                    rx.text(
                        proj["purpose"],
                        size="1",
                        color="#94a3b8",
                        max_width="440px",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        rx.icon("folder-open", size=13),
                        " Abrir",
                        on_click=lambda: FlowState.load_saved_project(proj["id"]),
                        color_scheme="blue",
                        size="1",
                        radius="medium",
                    ),
                    rx.button(
                        rx.icon("download", size=13),
                        " .temis.json",
                        on_click=lambda: FlowState.export_single_saved_package(proj["id"]),
                        color_scheme="gray",
                        variant="soft",
                        size="1",
                        radius="medium",
                    ),
                    rx.icon_button(
                        rx.icon("trash-2", size=13),
                        on_click=lambda: FlowState.delete_saved_project(proj["id"]),
                        color_scheme="ruby",
                        variant="ghost",
                        size="1",
                    ),
                    align="center",
                    spacing="2",
                ),
                width="100%",
                align="center",
            ),
            rx.divider(),
            rx.hstack(
                rx.badge(
                    "Fase ", proj["current_phase"],
                    color_scheme="purple",
                    variant="soft",
                    size="1",
                ),
                rx.badge(
                    proj["steps_count"], " pasos SIPOC",
                    color_scheme="blue",
                    variant="soft",
                    size="1",
                ),
                rx.badge(
                    proj["nodes_count"], " nodos BPMN",
                    color_scheme="green",
                    variant="soft",
                    size="1",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.icon("calendar", size=12, color="#94a3b8"),
                    rx.text(proj["updated_at"], size="1", color="#94a3b8"),
                    align="center",
                    spacing="1",
                ),
                width="100%",
                align="center",
            ),
            spacing="2",
            width="100%",
        ),
        padding="3",
        background_color="#131b2e",
        border="1px solid #1e293b",
        border_radius="8px",
        width="100%",
        _hover={
            "border_color": "#3b82f6",
            "box_shadow": "0 4px 12px 0 rgba(0, 0, 0, 0.4)",
        },
    )


def recent_projects_modal() -> rx.Component:
    """Dialog modal to browse and manage saved projects catalog in dark executive slate"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Modal Header
                rx.hstack(
                    rx.icon("folder-git-2", size=22, color="#38bdf8"),
                    rx.vstack(
                        rx.dialog.title("Catálogo de Flujos & Proyectos Guardados", size="4", weight="bold", color="#f8fafc"),
                        rx.dialog.description(
                            "Explora, abre y gestiona los procesos documentados en TEMIS",
                            size="2",
                            color="#94a3b8",
                        ),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),

                # Search Filter Bar
                rx.hstack(
                    rx.input(
                        placeholder="Buscar flujo por nombre, propósito o líder...",
                        value=FlowState.search_saved_query,
                        on_change=FlowState.set_search_saved_query,
                        width="100%",
                        size="2",
                        variant="surface",
                        radius="medium",
                    ),
                    width="100%",
                    padding_y="1",
                ),

                # Projects List
                rx.box(
                    rx.cond(
                        FlowState.filtered_saved_projects.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                FlowState.filtered_saved_projects,
                                render_saved_project_card,
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.icon("folder-open", size=32, color="#64748b"),
                                rx.text("No se encontraron flujos guardados con ese criterio.", size="2", color="#94a3b8"),
                                align="center",
                                spacing="2",
                            ),
                            padding="6",
                            text_align="center",
                            width="100%",
                        ),
                    ),
                    width="100%",
                    max_height="380px",
                    overflow_y="auto",
                    padding_right="1",
                ),

                # Bottom Footer Actions
                rx.hstack(
                    rx.button(
                        rx.icon("plus", size=15),
                        " Nuevo Flujo en Blanco",
                        on_click=FlowState.create_new_project,
                        color_scheme="blue",
                        variant="solid",
                        size="2",
                        radius="medium",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.button("Cerrar", color_scheme="gray", variant="soft", size="2", on_click=FlowState.close_recent_modal),
                    ),
                    width="100%",
                    align="center",
                    margin_top="2",
                ),
                spacing="3",
                width="100%",
            ),
            width="650px",
            max_width="95vw",
            border_radius="xl",
            padding="5",
            background_color="#0f172a",
            border="1px solid #1e293b",
        ),
        open=FlowState.show_recent_modal,
        on_open_change=FlowState.close_recent_modal,
    )
