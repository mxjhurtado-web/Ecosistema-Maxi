#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Floating Toast Notification Component for TEMIS Web Flow
Provides non-intrusive, accessible feedback for user actions.
Styled in Executive Light Slate Theme (WCAG 2.2 AA compliant).
"""

import reflex as rx
from temis_web.state import FlowState


def toast_notification() -> rx.Component:
    """Render a floating toast notification banner in the top-right corner in light slate theme"""
    return rx.cond(
        FlowState.show_toast,
        rx.box(
            rx.hstack(
                rx.match(
                    FlowState.toast_type,
                    ("success", rx.icon("circle-check", size=18, color="#107c41")),
                    ("warning", rx.icon("triangle-alert", size=18, color="#b76e00")),
                    ("error", rx.icon("circle-alert", size=18, color="#c53929")),
                    rx.icon("info", size=18, color="#1e5a9a"),
                ),
                rx.text(
                    FlowState.toast_message,
                    size="2",
                    weight="medium",
                    color="#17283c",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14, color="#52657a"),
                    on_click=FlowState.dismiss_toast,
                    variant="ghost",
                    size="1",
                    color_scheme="gray",
                    radius="full",
                    title="Cerrar notificación",
                ),
                align="center",
                spacing="3",
                width="100%",
            ),
            position="fixed",
            top="20px",
            right="24px",
            z_index="9999",
            background_color="#ffffff",
            border="1px solid #d9e2ec",
            border_radius="10px",
            padding_x="4",
            padding_y="3",
            box_shadow="0 10px 25px -5px rgba(23, 50, 77, 0.15), 0 4px 6px -2px rgba(23, 50, 77, 0.05)",
            max_width="420px",
            min_width="300px",
            transition="all 0.2s ease-in-out",
        ),
        rx.fragment(),
    )
