#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sidebar component for TEMIS Web Flow
Navigation for the 7 framework phases
"""

import reflex as rx
from temis_web.state import FlowState

PHASES_DATA = [
    {"num": 1, "name": "Diagnóstico Estratégico", "icon": "file-search"},
    {"num": 2, "name": "Inicio del Proyecto", "icon": "rocket"},
    {"num": 3, "name": "Planificación Híbrida", "icon": "layout-grid"},
    {"num": 4, "name": "Ejecución Iterativa", "icon": "code"},
    {"num": 5, "name": "Monitoreo y Control", "icon": "activity"},
    {"num": 6, "name": "Mejora Continua", "icon": "trending-up"},
    {"num": 7, "name": "Cierre del Proyecto", "icon": "circle-check"},
]


def phase_item(phase: dict) -> rx.Component:
    """Single phase sidebar item"""
    is_active = FlowState.current_phase == phase["num"]
    return rx.box(
        rx.hstack(
            rx.icon(phase["icon"], size=18, color=rx.cond(is_active, "#2563eb", "#64748b")),
            rx.vstack(
                rx.text(f"Fase {phase['num']}", size="1", weight="bold", color=rx.cond(is_active, "#2563eb", "#94a3b8")),
                rx.text(phase["name"], size="2", weight="medium", color=rx.cond(is_active, "#1e293b", "#334155")),
                spacing="0",
            ),
            spacing="3",
            align="center",
        ),
        padding_x="3",
        padding_y="2.5",
        border_radius="md",
        background_color=rx.cond(is_active, "#eff6ff", "transparent"),
        border_left=rx.cond(is_active, "3px solid #2563eb", "3px solid transparent"),
        cursor="pointer",
        on_click=lambda: FlowState.set_phase(phase["num"]),
        _hover={"background_color": "#f1f5f9"},
        width="100%",
    )


def sidebar() -> rx.Component:
    """Left sidebar component"""
    return rx.vstack(
        rx.text("MARCO DE GOBERNANZA", size="1", weight="bold", color="#94a3b8", padding_x="3", padding_top="2"),
        rx.vstack(
            *[phase_item(p) for p in PHASES_DATA],
            spacing="1",
            width="100%",
        ),
        rx.divider(color_scheme="gray", margin_y="3"),
        rx.vstack(
            rx.text("ACCIONES DE LIENZO", size="1", weight="bold", color="#94a3b8", padding_x="3"),
            rx.button(
                rx.icon("trash-2", size=16),
                " Limpiar Lienzo",
                on_click=FlowState.clear_canvas,
                color_scheme="red",
                variant="soft",
                width="100%",
                size="2",
            ),
            spacing="2",
            width="100%",
            padding_x="1",
        ),
        width="240px",
        height="calc(100vh - 65px)",
        background_color="#ffffff",
        border_right="1px solid #e2e8f0",
        padding="3",
        spacing="3",
    )
