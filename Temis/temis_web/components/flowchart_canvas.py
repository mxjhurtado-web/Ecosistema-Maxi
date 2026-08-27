#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Flowchart Canvas Component for TEMIS Web Flow
Renders interactive Swimlanes, Nodes (with Official Symbology) and Connecting Edges
"""

import reflex as rx
from temis_web.state import FlowState


def render_node(node: rx.Var) -> rx.Component:
    """Render individual diagram node according to official PDF symbology"""
    node_id = node["id"]
    node_type = node["type"]
    label = node["label"]

    is_selected = FlowState.selected_node_id == node_id
    shadow = rx.cond(is_selected, "0 0 0 3px rgba(37, 99, 235, 0.3)", "0 2px 5px rgba(0,0,0,0.08)")

    # 1. Start Node Symbol
    start_shape = rx.box(
        rx.text(label, size="2", weight="bold", color="#1e40af"),
        background_color="#dbeafe",
        border="2px solid #2563eb",
        border_radius="9999px",
        padding_x="5",
        padding_y="2",
    )

    # 2. End Node Symbol
    end_shape = rx.box(
        rx.text(label, size="2", weight="bold", color="#334155"),
        background_color="#f1f5f9",
        border="2px solid #475569",
        border_radius="9999px",
        padding_x="5",
        padding_y="2",
    )

    # 3. Decision Node Symbol (Rombo)
    decision_shape = rx.box(
        rx.vstack(
            rx.icon("circle-help", size=16, color="#d97706"),
            rx.text(label, size="2", weight="bold", color="#92400e", align="center"),
            align="center",
            spacing="1",
        ),
        background_color="#fef3c7",
        border="2px solid #d97706",
        border_radius="lg",
        padding="3",
        width="140px",
    )

    # 4. Activity Node Symbol (Recuadro Verde)
    activity_shape = rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(label, size="2", weight="bold", color="#1e293b"),
                spacing="1",
                align="start",
            ),
            spacing="2",
            align="center",
        ),
        background_color="#ffffff",
        border="2px solid #16a34a",
        border_radius="lg",
        padding="3",
        width="180px",
    )

    # 5. Default / Fallback Symbol
    default_shape = rx.box(
        rx.text(label, size="2", weight="medium", color="#1e293b"),
        background_color="#ffffff",
        border="1px solid #cbd5e1",
        border_radius="md",
        padding="2.5",
    )

    # Dynamic React Pattern Matching for Reactive Vars
    shape = rx.match(
        node_type,
        ("node_start", start_shape),
        ("node_end", end_shape),
        ("node_decision", decision_shape),
        ("node_activity", activity_shape),
        default_shape,
    )

    return rx.box(
        shape,
        position="absolute",
        left=f"{node['x']}px",
        top=f"{node['y']}px",
        box_shadow=shadow,
        cursor="pointer",
        on_click=lambda: FlowState.select_node(node_id),
    )


def flowchart_canvas() -> rx.Component:
    """Main Canvas component rendering Swimlanes and Flowchart"""
    return rx.vstack(
        # Top Diagram Toolbar
        rx.hstack(
            rx.icon("git-commit", size=20, color="#3b82f6"),
            rx.heading(FlowState.diagram_title, size="4", weight="bold", color="#1e293b"),
            rx.button(
                rx.icon("save", size=14),
                " Guardar Cambios",
                on_click=FlowState.save_diagram,
                color_scheme="emerald",
                size="2",
                variant="solid",
                radius="medium",
            ),
            rx.spacer(),
            rx.cond(
                FlowState.selected_node_id != "",
                rx.hstack(
                    rx.badge(f"Nodo: {FlowState.selected_node_id}", color_scheme="blue", variant="soft"),
                    rx.button(
                        rx.icon("copy", size=14),
                        "Duplicar",
                        on_click=FlowState.duplicate_selected_node,
                        color_scheme="blue",
                        variant="soft",
                        size="1",
                    ),
                    rx.button(
                        rx.icon("trash-2", size=14),
                        "Eliminar",
                        on_click=FlowState.delete_selected_node,
                        color_scheme="red",
                        variant="soft",
                        size="1",
                    ),
                    spacing="2",
                    align="center",
                ),
            ),
            width="100%",
            align="center",
            padding="3",
            background_color="#ffffff",
            border_bottom="1px solid #e2e8f0",
        ),
        # Swimlanes Layout & Canvas Area
        rx.box(
            # Swimlanes Header Columns
            rx.hstack(
                rx.box(rx.text("INPUT", size="2", weight="bold", color="#1e293b"), width="25%", background_color="#f8fafc", padding="2", text_align="center", border_right="1px solid #e2e8f0"),
                rx.box(rx.text("ACTOR 1 (ej. Usuario)", size="2", weight="bold", color="#16a34a"), width="25%", background_color="#f0fdf4", padding="2", text_align="center", border_right="1px solid #e2e8f0"),
                rx.box(rx.text("ACTOR 2 (ej. Sistema)", size="2", weight="bold", color="#2563eb"), width="25%", background_color="#eff6ff", padding="2", text_align="center", border_right="1px solid #e2e8f0"),
                rx.box(rx.text("OUTPUT", size="2", weight="bold", color="#475569"), width="25%", background_color="#f8fafc", padding="2", text_align="center"),
                width="100%",
                spacing="0",
                border_bottom="2px solid #cbd5e1",
            ),
            # Interactive Flowchart Board
            rx.box(
                # Render SVG Connections (Edges)
                rx.el.svg(
                    # Arrowhead marker definition
                    rx.el.defs(
                        rx.el.marker(
                            rx.el.polygon(points="0 0, 10 3.5, 0 7", fill="#64748b"),
                            id="arrow",
                            viewBox="0 0 10 10",
                            refX="5",
                            refY="3.5",
                            markerWidth="6",
                            markerHeight="6",
                            orient="auto-start-reverse",
                        ),
                    ),
                    # Dynamic Connection lines between nodes
                    rx.foreach(
                        FlowState.edges,
                        lambda edge: rx.el.path(
                            d="M 120 140 L 280 140",
                            stroke="#64748b",
                            stroke_width="2",
                            marker_end="url(#arrow)",
                        ),
                    ),
                    width="100%",
                    height="100%",
                    position="absolute",
                    top="0",
                    left="0",
                    pointer_events="none",
                ),
                # Render Flowchart Nodes
                rx.foreach(
                    FlowState.nodes,
                    render_node,
                ),
                width="100%",
                height="calc(100vh - 145px)",
                position="relative",
                background_color="#fafafa",
                background_image="radial-gradient(#cbd5e1 1px, transparent 1px)",
                background_size="20px 20px",
                overflow="auto",
            ),
            width="100%",
            height="100%",
        ),
        width="100%",
        spacing="0",
    )
