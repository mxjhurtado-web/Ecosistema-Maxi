#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Right Property Inspector Component for TEMIS Web Flow
Contextual side panel for editing selected node properties, routing, and connections
Styled in Executive Light Slate Theme with 44x44px accessible nudge controls and collapsible layout (WCAG 2.2 AA compliant).
"""

import reflex as rx
from temis_web.state import FlowState


def property_inspector() -> rx.Component:
    """Right-side property inspector panel with collapsible mode and accessible 44x44px controls"""
    # 1. Active Node Selected View
    active_inspector = rx.vstack(
        # Inspector Header
        rx.hstack(
            rx.hstack(
                rx.icon("sliders-horizontal", size=15, color="#1e5a9a"),
                rx.text(f"Nodo: ", FlowState.selected_node_id, size="2", weight="bold", color="#17283c"),
                align="center",
                spacing="2",
            ),
            rx.spacer(),
            rx.tooltip(
                rx.button(
                    rx.icon("panel-right-close", size=14, color="#52657a"),
                    on_click=FlowState.toggle_inspector,
                    color_scheme="gray",
                    variant="ghost",
                    size="1",
                    padding="1",
                    aria_label="Ocultar panel de propiedades",
                ),
                content="Ocultar panel",
            ),
            rx.tooltip(
                rx.button(
                    rx.icon("x", size=14, color="#52657a"),
                    on_click=FlowState.unselect_node,
                    color_scheme="gray",
                    variant="ghost",
                    size="1",
                    padding="1",
                    aria_label="Deseleccionar nodo",
                ),
                content="Deseleccionar nodo",
            ),
            width="100%",
            align="center",
            padding_bottom="2",
            border_bottom="1px solid #d9e2ec",
        ),
        # Label / Text Field
        rx.vstack(
            rx.text("Texto del Nodo:", size="1", weight="bold", color="#52657a"),
            rx.text_area(
                value=FlowState.node_label_edit,
                on_change=FlowState.set_selected_node_label,
                size="1",
                width="100%",
                rows="2",
                variant="surface",
            ),
            align="start",
            spacing="1",
            width="100%",
        ),
        # Swimlane / Carril
        rx.vstack(
            rx.text("Carril / Actor (Swimlane):", size="1", weight="bold", color="#52657a"),
            rx.input(
                value=FlowState.node_swimlane_edit,
                on_change=FlowState.set_selected_node_swimlane,
                size="1",
                width="100%",
                variant="surface",
            ),
            align="start",
            spacing="1",
            width="100%",
        ),
        # Attached System
        rx.vstack(
            rx.text("Sistema Asignado:", size="1", weight="bold", color="#52657a"),
            rx.select(
                ["", "Chronos ERP", "Freshdesk", "Base de Datos", "Servicio Web"],
                value=FlowState.selected_node_system,
                on_change=FlowState.set_selected_node_system,
                size="1",
                width="100%",
            ),
            align="start",
            spacing="1",
            width="100%",
        ),
        # Attached Channel
        rx.vstack(
            rx.text("Canal de Comunicación:", size="1", weight="bold", color="#52657a"),
            rx.select(
                ["", "WhatsApp", "Bria", "Correo / Formulario", "Presencial"],
                value=FlowState.selected_node_channel,
                on_change=FlowState.set_selected_node_channel,
                size="1",
                width="100%",
            ),
            align="start",
            spacing="1",
            width="100%",
        ),
        # Quick Connect Action Button
        rx.button(
            rx.hstack(
                rx.icon("link", size=14),
                rx.text("Conectar a otro Nodo...", size="1", weight="bold"),
                align="center",
                spacing="2",
            ),
            on_click=FlowState.open_connect_modal,
            color_scheme="blue",
            variant="solid",
            size="2",
            width="100%",
            margin_top="1",
        ),
        # Accessible 44x44px Position Nudge Control
        rx.vstack(
            rx.text("Reposicionar en Lienzo:", size="1", weight="bold", color="#52657a"),
            rx.vstack(
                rx.tooltip(
                    rx.button(
                        rx.icon("arrow-up", size=18, color="#17324d"),
                        on_click=lambda: FlowState.move_selected_node(0, -30),
                        width="44px",
                        height="44px",
                        background_color="#eaf0f6",
                        border="1px solid #cbd5e1",
                        border_radius="md",
                        _hover={"background_color": "#d0e2f2", "border_color": "#1e5a9a"},
                        aria_label="Mover nodo arriba",
                    ),
                    content="Mover nodo arriba",
                ),
                rx.hstack(
                    rx.tooltip(
                        rx.button(
                            rx.icon("arrow-left", size=18, color="#17324d"),
                            on_click=lambda: FlowState.move_selected_node(-30, 0),
                            width="44px",
                            height="44px",
                            background_color="#eaf0f6",
                            border="1px solid #cbd5e1",
                            border_radius="md",
                            _hover={"background_color": "#d0e2f2", "border_color": "#1e5a9a"},
                            aria_label="Mover nodo a la izquierda",
                        ),
                        content="Mover nodo a la izquierda",
                    ),
                    rx.tooltip(
                        rx.button(
                            rx.icon("arrow-right", size=18, color="#17324d"),
                            on_click=lambda: FlowState.move_selected_node(30, 0),
                            width="44px",
                            height="44px",
                            background_color="#eaf0f6",
                            border="1px solid #cbd5e1",
                            border_radius="md",
                            _hover={"background_color": "#d0e2f2", "border_color": "#1e5a9a"},
                            aria_label="Mover nodo a la derecha",
                        ),
                        content="Mover nodo a la derecha",
                    ),
                    spacing="2",
                ),
                rx.tooltip(
                    rx.button(
                        rx.icon("arrow-down", size=18, color="#17324d"),
                        on_click=lambda: FlowState.move_selected_node(0, 30),
                        width="44px",
                        height="44px",
                        background_color="#eaf0f6",
                        border="1px solid #cbd5e1",
                        border_radius="md",
                        _hover={"background_color": "#d0e2f2", "border_color": "#1e5a9a"},
                        aria_label="Mover nodo abajo",
                    ),
                    content="Mover nodo abajo",
                ),
                align="center",
                spacing="1",
                width="100%",
            ),
            align="start",
            spacing="1",
            width="100%",
        ),
        rx.divider(color_scheme="gray", opacity=0.15),
        # Secondary Node Actions (Duplicate & Delete)
        rx.hstack(
            rx.button(
                rx.icon("copy", size=13),
                "Duplicar",
                on_click=FlowState.duplicate_selected_node,
                color_scheme="gray",
                variant="soft",
                size="1",
                flex="1",
            ),
            rx.button(
                rx.icon("trash-2", size=13),
                "Eliminar",
                on_click=FlowState.delete_selected_node,
                color_scheme="ruby",
                variant="soft",
                size="1",
                flex="1",
            ),
            spacing="2",
            width="100%",
        ),
        spacing="3",
        width="100%",
        padding="3",
    )

    # 2. Empty State View (When no node is selected)
    empty_inspector = rx.vstack(
        rx.hstack(
            rx.icon("info", size=15, color="#52657a"),
            rx.text("Resumen del Lienzo", size="2", weight="bold", color="#17283c"),
            rx.spacer(),
            rx.tooltip(
                rx.button(
                    rx.icon("panel-right-close", size=14, color="#52657a"),
                    on_click=FlowState.toggle_inspector,
                    color_scheme="gray",
                    variant="ghost",
                    size="1",
                    padding="1",
                    aria_label="Ocultar panel de propiedades",
                ),
                content="Ocultar panel",
            ),
            align="center",
            spacing="2",
            padding_bottom="2",
            border_bottom="1px solid #d9e2ec",
            width="100%",
        ),
        rx.vstack(
            rx.hstack(
                rx.text("Nodos en hoja:", size="1", color="#52657a"),
                rx.spacer(),
                rx.badge(FlowState.nodes.length().to(str), color_scheme="blue", variant="soft", size="1"),
                width="100%",
            ),
            rx.hstack(
                rx.text("Conectores:", size="1", color="#52657a"),
                rx.spacer(),
                rx.badge(FlowState.edges.length().to(str), color_scheme="indigo", variant="soft", size="1"),
                width="100%",
            ),
            spacing="2",
            width="100%",
            padding_y="2",
        ),
        rx.box(
            rx.hstack(
                rx.icon("info", size=13, color="#52657a"),
                rx.text(
                    "Haz clic en cualquier símbolo del lienzo para editar sus propiedades, sistemas o conectores.",
                    size="1",
                    color="#52657a",
                    line_height="1.4",
                ),
                align="start",
                spacing="2",
            ),
            background_color="#f8fafc",
            border="1px dashed #d9e2ec",
            border_radius="md",
            padding="2.5",
            width="100%",
        ),
        spacing="3",
        width="100%",
        padding="3",
    )

    # 3. Collapsed View Strip (For 100% canvas view)
    collapsed_strip = rx.box(
        rx.tooltip(
            rx.button(
                rx.icon("panel-right-open", size=16, color="#1e5a9a"),
                on_click=FlowState.toggle_inspector,
                variant="ghost",
                color_scheme="gray",
                size="1",
                padding="1",
                aria_label="Expandir panel de propiedades",
            ),
            content="Expandir propiedades",
        ),
        width="38px",
        height="100%",
        background_color="#ffffff",
        border_left="1px solid #d9e2ec",
        display="flex",
        align_items="start",
        justify_content="center",
        padding_top="2",
    )

    # 4. Expanded Full Width View
    expanded_view = rx.box(
        rx.cond(
            FlowState.selected_node_id != "",
            active_inspector,
            empty_inspector,
        ),
        width="260px",
        height="100%",
        background_color="#ffffff",
        border_left="1px solid #d9e2ec",
        overflow_y="auto",
    )

    return rx.cond(
        FlowState.is_inspector_collapsed,
        collapsed_strip,
        expanded_view,
    )
