#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Right Property Inspector Component for TEMIS Web Flow
Contextual side panel for editing selected node properties, routing, and connections
"""

import reflex as rx
from temis_web.state import FlowState


def property_inspector() -> rx.Component:
    """Right-side property inspector panel"""
    # Active Node Selected View
    active_inspector = rx.vstack(
        # Inspector Header
        rx.hstack(
            rx.icon("sliders", size=15, color="#2563eb"),
            rx.text(f"Nodo: ", FlowState.selected_node_id, size="2", weight="bold", color="#1e293b"),
            rx.spacer(),
            rx.button(
                rx.icon("x", size=13),
                on_click=FlowState.unselect_node,
                color_scheme="gray",
                variant="ghost",
                size="1",
                padding="0",
            ),
            width="100%",
            align="center",
            padding_bottom="2",
            border_bottom="1px solid #e2e8f0",
        ),
        # Label / Text Field
        rx.vstack(
            rx.text("Texto del Nodo:", size="1", weight="bold", color="#475569"),
            rx.text_area(
                value=FlowState.node_label_edit,
                on_change=FlowState.set_selected_node_label,
                size="1",
                width="100%",
                rows="2",
            ),
            align="start",
            spacing="1",
            width="100%",
        ),
        # Swimlane / Carril
        rx.vstack(
            rx.text("Carril / Actor (Swimlane):", size="1", weight="bold", color="#475569"),
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
            rx.text("Sistema Asignado:", size="1", weight="bold", color="#475569"),
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
            rx.text("Canal de Comunicación:", size="1", weight="bold", color="#475569"),
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
        # Position Nudge Control
        rx.vstack(
            rx.text("Reposicionar en Lienzo:", size="1", weight="bold", color="#475569"),
            rx.vstack(
                rx.button(rx.icon("arrow-up", size=13), on_click=lambda: FlowState.move_selected_node(0, -30), size="1", variant="soft", color_scheme="gray"),
                rx.hstack(
                    rx.button(rx.icon("arrow-left", size=13), on_click=lambda: FlowState.move_selected_node(-30, 0), size="1", variant="soft", color_scheme="gray"),
                    rx.button(rx.icon("arrow-right", size=13), on_click=lambda: FlowState.move_selected_node(30, 0), size="1", variant="soft", color_scheme="gray"),
                    spacing="2",
                ),
                rx.button(rx.icon("arrow-down", size=13), on_click=lambda: FlowState.move_selected_node(0, 30), size="1", variant="soft", color_scheme="gray"),
                align="center",
                spacing="1",
                width="100%",
            ),
            align="start",
            spacing="1",
            width="100%",
        ),
        rx.divider(color="#e2e8f0"),
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
                color_scheme="red",
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

    # Empty State View (When no node is clicked)
    empty_inspector = rx.vstack(
        rx.hstack(
            rx.icon("info", size=15, color="#64748b"),
            rx.text("Resumen del Lienzo", size="2", weight="bold", color="#475569"),
            align="center",
            spacing="2",
            padding_bottom="2",
            border_bottom="1px solid #e2e8f0",
            width="100%",
        ),
        rx.vstack(
            rx.hstack(
                rx.text("Nodos en hoja:", size="1", color="#64748b"),
                rx.spacer(),
                rx.badge(FlowState.nodes.length().to(str), color_scheme="blue", variant="soft", size="1"),
                width="100%",
            ),
            rx.hstack(
                rx.text("Conectores:", size="1", color="#64748b"),
                rx.spacer(),
                rx.badge(FlowState.edges.length().to(str), color_scheme="indigo", variant="soft", size="1"),
                width="100%",
            ),
            spacing="2",
            width="100%",
            padding_y="2",
        ),
        rx.box(
            rx.text(
                "💡 Haz clic en cualquier casilla del lienzo para editar sus propiedades, sistemas o conectores.",
                size="1",
                color="#64748b",
                line_height="1.4",
            ),
            background_color="#f8fafc",
            border="1px dashed #cbd5e1",
            border_radius="md",
            padding="2.5",
            width="100%",
        ),
        spacing="3",
        width="100%",
        padding="3",
    )

    return rx.box(
        rx.cond(
            FlowState.selected_node_id != "",
            active_inspector,
            empty_inspector,
        ),
        width="260px",
        height="100%",
        background_color="#ffffff",
        border_left="1px solid #e2e8f0",
        overflow_y="auto",
    )
