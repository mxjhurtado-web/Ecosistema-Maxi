#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Flowchart Canvas Component for TEMIS Web Flow
High-performance SVG and CSS canvas for Swimlanes, Nodes, and Bézier Connectors
"""

import reflex as rx
from temis_web.state import FlowState
from temis_web.components.edit_modal import edit_node_modal
from temis_web.components.import_modal import import_modal


def render_node(node: rx.Var) -> rx.Component:
    """Render individual diagram node according to official PDF symbology"""
    node_id = node["id"]
    node_type = node["type"]
    label = node["label"]

    is_selected = FlowState.selected_node_id == node_id
    shadow = rx.cond(is_selected, "0 0 0 3px rgba(37, 99, 235, 0.4), 0 4px 12px rgba(0,0,0,0.1)", "0 2px 6px rgba(0,0,0,0.06)")

    # 1. Start Node Symbol (Pill)
    start_shape = rx.box(
        rx.hstack(
            rx.icon("play", size=13, color="#2563eb"),
            rx.text(label, size="2", weight="bold", color="#1e40af", truncate=True),
            align="center",
            spacing="1.5",
        ),
        background_color="#eff6ff",
        border="2px solid #3b82f6",
        border_radius="9999px",
        padding_x="4",
        padding_y="1.5",
        width="130px",
        height="42px",
        display="flex",
        align_items="center",
        justify_content="center",
    )

    # 2. End Node Symbol (Pill)
    end_shape = rx.box(
        rx.hstack(
            rx.icon("square", size=13, color="#475569"),
            rx.text(label, size="2", weight="bold", color="#334155", truncate=True),
            align="center",
            spacing="1.5",
        ),
        background_color="#f8fafc",
        border="2px solid #64748b",
        border_radius="9999px",
        padding_x="4",
        padding_y="1.5",
        width="130px",
        height="42px",
        display="flex",
        align_items="center",
        justify_content="center",
    )

    # 3. Decision Node Symbol (Rombo / Card)
    decision_shape = rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("circle-help", size=14, color="#d97706"),
                rx.text(label, size="2", weight="bold", color="#92400e", line_height="1.2"),
                align="center",
                spacing="1.5",
            ),
            align="center",
            justify="center",
            height="100%",
        ),
        background_color="#fffbeb",
        border="2px solid #f59e0b",
        border_radius="lg",
        padding="2.5",
        width="160px",
        height="68px",
    )

    # 4. Activity Node Symbol (Tarjeta Verde con Badges)
    activity_shape = rx.box(
        rx.vstack(
            rx.hstack(
                rx.cond(
                    node["activity_number"].to(str) != "",
                    rx.badge(node["activity_number"].to(str), color_scheme="green", variant="solid", size="1"),
                ),
                rx.text(label, size="2", weight="bold", color="#1e293b", line_height="1.2"),
                align="center",
                spacing="1.5",
            ),
            rx.hstack(
                rx.cond(
                    node["attached_system"].to(str) != "",
                    rx.badge(node["attached_system"].to(str), color_scheme="blue", variant="soft", size="1"),
                ),
                rx.cond(
                    node["attached_channel"].to(str) != "",
                    rx.badge(node["attached_channel"].to(str), color_scheme="green", variant="soft", size="1"),
                ),
                spacing="1",
                align="center",
            ),
            spacing="1",
            align="start",
            justify="center",
            height="100%",
        ),
        background_color="#ffffff",
        border="2px solid #22c55e",
        border_radius="lg",
        padding="2.5",
        width="190px",
        height="68px",
    )

    # 5. System / Channel Node Symbol
    system_shape = rx.box(
        rx.hstack(
            rx.icon("cpu", size=14, color="#059669"),
            rx.text(label, size="2", weight="bold", color="#065f46", line_height="1.2"),
            align="center",
            spacing="1.5",
            height="100%",
        ),
        background_color="#ecfdf5",
        border="2px solid #10b981",
        border_radius="md",
        padding="2.5",
        width="175px",
        height="58px",
    )

    # 6. Default / Fallback Symbol
    default_shape = rx.box(
        rx.text(label, size="2", weight="medium", color="#1e293b"),
        background_color="#ffffff",
        border="1px solid #cbd5e1",
        border_radius="md",
        padding="2.5",
        width="160px",
        height="52px",
    )

    # Match reactive shape by type
    shape = rx.match(
        node_type,
        ("node_start", start_shape),
        ("node_end", end_shape),
        ("node_decision", decision_shape),
        ("node_activity", activity_shape),
        ("node_system", system_shape),
        ("channel_whatsapp", system_shape),
        ("channel_freshdesk", system_shape),
        ("channel_bria", system_shape),
        default_shape,
    )

    return rx.box(
        shape,
        position="absolute",
        left=node["x"].to(str) + "px",
        top=node["y"].to(str) + "px",
        box_shadow=shadow,
        cursor="pointer",
        on_click=lambda: FlowState.select_node(node_id),
        transition="all 0.15s ease",
    )


def flowchart_canvas() -> rx.Component:
    """Main Canvas component rendering Swimlanes and Flowchart"""
    return rx.box(
        edit_node_modal(),
        import_modal(),
        # Swimlanes Column Headers (Optional)
        rx.cond(
            FlowState.show_swimlanes,
            rx.hstack(
                rx.box(rx.text("INPUT", size="1", weight="bold", color="#475569"), width="25%", background_color="#f8fafc", padding="2", text_align="center", border_right="1px solid #e2e8f0"),
                rx.box(rx.text("ACTOR 1 (Usuario)", size="1", weight="bold", color="#16a34a"), width="25%", background_color="#f0fdf4", padding="2", text_align="center", border_right="1px solid #e2e8f0"),
                rx.box(rx.text("ACTOR 2 (Sistema)", size="1", weight="bold", color="#2563eb"), width="25%", background_color="#eff6ff", padding="2", text_align="center", border_right="1px solid #e2e8f0"),
                rx.box(rx.text("OUTPUT", size="1", weight="bold", color="#475569"), width="25%", background_color="#f8fafc", padding="2", text_align="center"),
                width="100%",
                spacing="0",
                border_bottom="1px solid #cbd5e1",
            ),
        ),
        # Flowchart Drawing Area
        rx.box(
            # SVG Edge Connections
            rx.el.svg(
                rx.el.defs(
                    rx.el.marker(
                        rx.el.polygon(points="0 0, 10 3.5, 0 7", fill="#2563eb"),
                        id="arrow-blue",
                        viewBox="0 0 10 10",
                        refX="6",
                        refY="3.5",
                        markerWidth="7",
                        markerHeight="7",
                        orient="auto-start-reverse",
                    ),
                ),
                # Dynamic Bézier Curves
                rx.foreach(
                    FlowState.computed_edges,
                    lambda edge: rx.el.g(
                        rx.el.path(
                            d=edge["d"],
                            stroke="#2563eb",
                            stroke_width="2.5",
                            fill="none",
                            marker_end="url(#arrow-blue)",
                        ),
                        rx.cond(
                            edge["has_label"],
                            rx.el.text(
                                edge["label"],
                                x=edge["label_x"].to(str),
                                y=edge["label_y"].to(str),
                                fill="#16a34a",
                                font_size="12px",
                                font_weight="bold",
                                text_anchor="middle",
                            ),
                        ),
                    ),
                ),
                width="6000px",
                height="6000px",
                position="absolute",
                top="0",
                left="0",
                pointer_events="none",
                style={"zIndex": 1, "overflow": "visible"},
            ),
            # Render All Nodes
            rx.foreach(
                FlowState.nodes,
                render_node,
            ),
            width=FlowState.zoom_width,
            height=FlowState.zoom_height,
            min_height="100%",
            min_width="100%",
            position="relative",
            background_color="#fafafa",
            background_image="radial-gradient(#cbd5e1 1px, transparent 1px)",
            background_size="24px 24px",
            style={
                "transform": f"scale({FlowState.zoom_level})",
                "transformOrigin": "0 0",
                "transition": "transform 0.15s ease",
            },
        ),
        width="100%",
        height="100%",
        position="relative",
        overflow="auto",
        flex="1",
    )
