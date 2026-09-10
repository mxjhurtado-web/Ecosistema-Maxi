#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Connect Nodes Modal Component for TEMIS Web Flow
Allows users to interactively draw SVG Bézier connections between shapes
"""

import reflex as rx
from temis_web.state import FlowState


def connect_modal() -> rx.Component:
    """Dialog modal to interactively connect selected node to a target node"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("link", size=20, color="#2563eb"),
                    rx.text("Conectar Nodo a Destino", size="4", weight="bold"),
                    align="center",
                    spacing="2",
                ),
            ),
            rx.dialog.description(
                "Establece una línea de conexión Bézier y una etiqueta de decisión:",
                size="2",
                color="#64748b",
            ),
            rx.vstack(
                rx.vstack(
                    rx.text("Nodo de Origen:", size="2", weight="bold", color="#334155"),
                    rx.badge(FlowState.selected_node_id, color_scheme="blue", variant="soft", size="2"),
                    align="start",
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Selecciona el Nodo Destino:", size="2", weight="bold", color="#334155"),
                    rx.select(
                        FlowState.target_node_options,
                        placeholder="Elegir nodo destino...",
                        on_change=FlowState.set_connect_target_id,
                        width="100%",
                    ),
                    align="start",
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Etiqueta del Conector (Opcional):", size="2", weight="bold", color="#334155"),
                    rx.input(
                        placeholder="ej: Sí, No, Válido, Aprobado, Reintentar...",
                        value=FlowState.connect_label,
                        on_change=FlowState.set_connect_label,
                        width="100%",
                        size="2",
                        variant="surface",
                    ),
                    align="start",
                    spacing="1",
                    width="100%",
                ),
                spacing="4",
                padding_y="3",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancelar", color_scheme="gray", variant="soft", on_click=FlowState.close_connect_modal),
                ),
                rx.button(
                    rx.icon("check", size=16),
                    " Crear Conexión",
                    on_click=FlowState.add_connection,
                    color_scheme="blue",
                    variant="solid",
                ),
                justify="end",
                spacing="2",
                margin_top="3",
            ),
            width="460px",
            border_radius="xl",
            padding="5",
        ),
        open=FlowState.show_connect_modal,
        on_open_change=FlowState.close_connect_modal,
    )
