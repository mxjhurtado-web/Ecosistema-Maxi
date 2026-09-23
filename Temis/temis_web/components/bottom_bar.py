#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bottom Bar Component for TEMIS Web Flow
Lucidchart/Excel style bottom bar containing Document Page Tabs and Zoom Navigation Controls
"""

import reflex as rx
from temis_web.state import FlowState


def bottom_bar() -> rx.Component:
    """Bottom bar with page tabs and zoom controls in dark executive slate"""
    return rx.hstack(
        # Left: Multi-Tab Page Switcher
        rx.hstack(
            rx.icon("layers", size=14, color="#38bdf8"),
            rx.foreach(
                FlowState.project_pages,
                lambda page, idx: rx.hstack(
                    rx.button(
                        page["name"],
                        on_click=lambda: FlowState.select_page_tab(idx),
                        color_scheme=rx.cond(FlowState.active_page_index == idx, "blue", "gray"),
                        variant=rx.cond(FlowState.active_page_index == idx, "solid", "ghost"),
                        size="1",
                        radius="medium",
                        font_size="12px",
                    ),
                    rx.cond(
                        FlowState.project_pages.length() > 1,
                        rx.button(
                            rx.icon("x", size=11),
                            on_click=lambda: FlowState.delete_tab_page(idx),
                            color_scheme="gray",
                            variant="ghost",
                            size="1",
                            padding="0",
                        ),
                    ),
                    align="center",
                    spacing="1",
                    background_color=rx.cond(FlowState.active_page_index == idx, "rgba(59, 130, 246, 0.2)", "transparent"),
                    border=rx.cond(FlowState.active_page_index == idx, "1px solid rgba(59, 130, 246, 0.4)", "1px solid transparent"),
                    border_radius="md",
                    padding_x="1",
                ),
            ),
            # Add New Page Tab Button
            rx.button(
                rx.icon("plus", size=13),
                on_click=FlowState.add_new_tab_page,
                color_scheme="blue",
                variant="ghost",
                size="1",
                radius="medium",
            ),
            align="center",
            spacing="1",
            overflow_x="auto",
            max_width="70vw",
        ),
        rx.spacer(),
        # Right: Zoom and View Controls
        rx.hstack(
            rx.button(
                rx.icon("columns-2", size=13),
                rx.cond(FlowState.show_swimlanes, "Ocultar Carriles", "Ver Carriles"),
                on_click=FlowState.toggle_swimlanes,
                color_scheme="gray",
                variant="ghost",
                size="1",
            ),
            rx.button(
                rx.icon("minus", size=12),
                on_click=FlowState.zoom_out,
                color_scheme="gray",
                variant="ghost",
                size="1",
            ),
            rx.text(FlowState.zoom_percent, size="1", weight="bold", color="#f8fafc", min_width="42px", text_align="center"),
            rx.button(
                rx.icon("plus", size=12),
                on_click=FlowState.zoom_in,
                color_scheme="gray",
                variant="ghost",
                size="1",
            ),
            rx.button(
                rx.icon("maximize-2", size=12),
                on_click=FlowState.zoom_reset,
                color_scheme="gray",
                variant="ghost",
                size="1",
            ),
            align="center",
            spacing="1",
            background_color="#131b2e",
            border="1px solid #1e293b",
            border_radius="md",
            padding_x="2",
            padding_y="1",
        ),
        width="100%",
        height="38px",
        align="center",
        padding_x="3",
        background_color="#0f172a",
        border_top="1px solid #1e293b",
        z_index="10",
    )
