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
            rx.icon("play", size=13, color="#60a5fa"),
            rx.text(label, size="2", weight="bold", color="#93c5fd", truncate=True),
            align="center",
            spacing="1",
        ),
        background_color="rgba(37, 99, 235, 0.2)",
        border="2px solid #3b82f6",
        border_radius="9999px",
        padding_x="4",
        padding_y="1",
        width="130px",
        height="42px",
        display="flex",
        align_items="center",
        justify_content="center",
    )

    # 2. End Node Symbol (Pill)
    end_shape = rx.box(
        rx.hstack(
            rx.icon("square", size=13, color="#94a3b8"),
            rx.text(label, size="2", weight="bold", color="#e2e8f0", truncate=True),
            align="center",
            spacing="1",
        ),
        background_color="#1e293b",
        border="2px solid #64748b",
        border_radius="9999px",
        padding_x="4",
        padding_y="1",
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
                rx.icon("circle-help", size=14, color="#f59e0b"),
                rx.text(label, size="2", weight="bold", color="#fde68a", line_height="1.2"),
                align="center",
                spacing="1",
            ),
            align="center",
            justify="center",
            height="100%",
        ),
        background_color="rgba(245, 158, 11, 0.2)",
        border="2px solid #f59e0b",
        border_radius="lg",
        padding="2",
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
                rx.text(label, size="2", weight="bold", color="#f8fafc", line_height="1.2"),
                align="center",
                spacing="1",
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
        background_color="#131b2e",
        border="2px solid #10b981",
        border_radius="lg",
        padding="2",
        width="190px",
        height="68px",
    )

    # 5. System / Channel Node Symbol
    system_shape = rx.box(
        rx.hstack(
            rx.icon("cpu", size=14, color="#34d399"),
            rx.text(label, size="2", weight="bold", color="#a7f3d0", line_height="1.2"),
            align="center",
            spacing="1",
            height="100%",
        ),
        background_color="rgba(16, 185, 129, 0.15)",
        border="2px solid #10b981",
        border_radius="md",
        padding="2",
        width="175px",
        height="58px",
    )

    # 6. Default / Fallback Symbol
    default_shape = rx.box(
        rx.text(label, size="2", weight="medium", color="#f8fafc"),
        background_color="#131b2e",
        border="1px solid #334155",
        border_radius="md",
        padding="2",
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
                rx.box(rx.text("INPUT", size="1", weight="bold", color="#94a3b8"), width="25%", background_color="#0f172a", padding="2", text_align="center", border_right="1px solid #1e293b"),
                rx.box(rx.text("ACTOR 1 (Usuario)", size="1", weight="bold", color="#34d399"), width="25%", background_color="rgba(16, 185, 129, 0.08)", padding="2", text_align="center", border_right="1px solid #1e293b"),
                rx.box(rx.text("ACTOR 2 (Sistema)", size="1", weight="bold", color="#38bdf8"), width="25%", background_color="rgba(59, 130, 246, 0.08)", padding="2", text_align="center", border_right="1px solid #1e293b"),
                rx.box(rx.text("OUTPUT", size="1", weight="bold", color="#94a3b8"), width="25%", background_color="#0f172a", padding="2", text_align="center"),
                width="100%",
                spacing="0",
                border_bottom="1px solid #1e293b",
            ),
        ),
        # Flowchart Drawing Area
        rx.box(
            # SVG Edge Connections
            rx.el.svg(
                rx.el.defs(
                    rx.el.marker(
                        rx.el.polygon(points="0 0, 10 3.5, 0 7", fill="#38bdf8"),
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
                            stroke="#38bdf8",
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
                                fill="#34d399",
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
            background_color="#0b0f17",
            background_image="radial-gradient(#1e293b 1.5px, transparent 1.5px)",
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
