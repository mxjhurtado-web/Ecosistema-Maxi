#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Floating Toast Notification Component for TEMIS Web Flow
Provides non-intrusive, accessible feedback for user actions.
"""

import reflex as rx
from temis_web.state import FlowState


def toast_notification() -> rx.Component:
    """Render a floating toast notification banner in the top-right corner"""
    return rx.cond(
        FlowState.show_toast,
        rx.box(
            rx.hstack(
                rx.match(
                    FlowState.toast_type,
                    ("success", rx.icon("circle-check", size=18, color="#16a34a")),
                    ("warning", rx.icon("alert-triangle", size=18, color="#d97706")),
                    ("error", rx.icon("alert-circle", size=18, color="#dc2626")),
                    rx.icon("info", size=18, color="#2563eb"),
                ),
                rx.text(
                    FlowState.toast_message,
                    size="2",
                    weight="medium",
                    color="#0f172a",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14, color="#64748b"),
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
            border="1px solid #e2e8f0",
            border_radius="10px",
            padding_x="4",
            padding_y="3",
            box_shadow="0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05)",
            max_width="420px",
            min_width="300px",
            transition="all 0.2s ease-in-out",
        ),
        rx.box(),
    )
