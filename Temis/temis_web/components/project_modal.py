#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Recent Projects Modal Component for TEMIS Web Flow
Dialog to browse and open saved projects from PostgreSQL database
"""

import reflex as rx
from temis_web.state import FlowState


def recent_projects_modal() -> rx.Component:
    """Dialog modal to select and load recent saved projects"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Abrir Proyecto Reciente", size="4", weight="bold"),
            rx.dialog.description(
                "Proyectos guardados en la base de datos de gobierno de proyectos:",
                size="2",
                color="#64748b",
            ),
            rx.vstack(
                rx.cond(
                    FlowState.recent_projects.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            FlowState.recent_projects,
                            lambda proj: rx.box(
                                rx.hstack(
                                    rx.vstack(
                                        rx.text(proj["name"], size="3", weight="bold", color="#1e293b"),
                                        rx.text(
                                            "Actualizado: ", proj.get("updated_at", "Recientemente"),
                                            size="1", color="#64748b"
                                        ),
                                        spacing="1",
                                    ),
                                    rx.spacer(),
                                    rx.button(
                                        "Abrir",
                                        on_click=FlowState.close_recent_modal,
                                        color_scheme="blue",
                                        size="1",
                                        variant="soft",
                                    ),
                                    align="center",
                                    width="100%",
                                ),
                                padding="3",
                                border="1px solid #e2e8f0",
                                border_radius="md",
                                width="100%",
                                _hover={"background_color": "#f8fafc"},
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.box(
                        rx.text("No hay proyectos recientes guardados aún en la base de datos.", size="2", color="#64748b"),
                        padding="4",
                        text_align="center",
                        width="100%",
                    ),
                ),
                spacing="3",
                padding_y="3",
                width="100%",
                max_height="320px",
                overflow_y="auto",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cerrar", color_scheme="gray", variant="soft", on_click=FlowState.close_recent_modal),
                ),
                justify="end",
                margin_top="2",
            ),
            width="480px",
            border_radius="xl",
            padding="5",
        ),
        open=FlowState.show_recent_modal,
        on_open_change=FlowState.close_recent_modal,
    )
