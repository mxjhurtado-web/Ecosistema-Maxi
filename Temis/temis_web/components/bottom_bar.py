#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bottom Bar Component for TEMIS Web Flow
Lucidchart/Excel style bottom bar containing Document Page Tabs and Zoom Navigation Controls
"""

import reflex as rx
from temis_web.state import FlowState


def bottom_bar() -> rx.Component:
    """Bottom bar with page tabs and zoom controls"""
    return rx.hstack(
        # Left: Multi-Tab Page Switcher
        rx.hstack(
            rx.icon("layers", size=14, color="#4f46e5"),
            rx.foreach(
                FlowState.project_pages,
                lambda page, idx: rx.hstack(
                    rx.button(
                        page["name"],
                        on_click=lambda: FlowState.select_page_tab(idx),
                        color_scheme=rx.cond(FlowState.active_page_index == idx, "indigo", "gray"),
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
                    background_color=rx.cond(FlowState.active_page_index == idx, "#ede9fe", "transparent"),
                    border_radius="md",
                    padding_x="1",
                ),
            ),
            # Add New Page Tab Button
            rx.button(
                rx.icon("plus", size=13),
                on_click=FlowState.add_new_tab_page,
                color_scheme="indigo",
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
            rx.text(FlowState.zoom_percent, size="1", weight="bold", color="#475569", min_width="42px", text_align="center"),
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
            background_color="#f1f5f9",
            border_radius="md",
            padding_x="2",
            padding_y="1",
        ),
        width="100%",
        height="38px",
        align="center",
        padding_x="3",
        background_color="#ffffff",
        border_top="1px solid #e2e8f0",
        z_index="10",
    )
