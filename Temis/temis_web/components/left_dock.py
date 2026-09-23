#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Left Shape Dock Component for TEMIS Web Flow
Collapsible tool palette for BPMN, Systems, Channels, and Gateways
"""

import reflex as rx
from temis_web.state import FlowState


def shape_button(icon_name: str, label: str, node_type: str, color: str = "#94a3b8") -> rx.Component:
    """Reusable compact shape button"""
    return rx.button(
        rx.hstack(
            rx.icon(icon_name, size=14, color=color),
            rx.text(label, size="1", weight="medium", color="#f8fafc", truncate=True),
            align="center",
            spacing="2",
            width="100%",
        ),
        on_click=lambda: FlowState.add_node_by_type(node_type, label),
        variant="ghost",
        color_scheme="gray",
        size="1",
        width="100%",
        justify="start",
        padding_x="2",
        padding_y="1",
        border_radius="md",
        _hover={"background_color": "#1e293b"},
    )


def left_dock() -> rx.Component:
    """Left sidebar shape dock"""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("shapes", size=15, color="#3b82f6"),
                rx.text("FORMAS", size="1", weight="bold", color="#64748b", letter_spacing="0.05em"),
                align="center",
                spacing="2",
                padding_x="2",
                padding_y="1",
            ),
            # BPMN Category
            rx.vstack(
                rx.text("BPMN / Proceso", size="1", weight="bold", color="#64748b", padding_x="2"),
                shape_button("circle-play", "Inicio Proceso", "node_start", "#3b82f6"),
                shape_button("square-check", "Actividad", "node_activity", "#10b981"),
                shape_button("circle-help", "Decisión", "node_decision", "#f59e0b"),
                shape_button("circle-stop", "Fin Proceso", "node_end", "#94a3b8"),
                shape_button("clock", "Demora / Espera", "node_activity", "#f97316"),
                shape_button("file-text", "Documento", "node_document", "#38bdf8"),
                shape_button("layers", "Subproceso", "node_activity", "#a855f7"),
                spacing="1",
                width="100%",
            ),
            rx.divider(color_scheme="gray", opacity=0.15),
            # Systems & Channels Category
            rx.vstack(
                rx.text("Sistemas & Canales", size="1", weight="bold", color="#64748b", padding_x="2"),
                shape_button("cpu", "Sistema Chronos", "node_system", "#10b981"),
                shape_button("database", "Base de Datos", "node_database", "#06b6d4"),
                shape_button("monitor", "Pantalla / Menú", "node_system", "#3b82f6"),
                shape_button("message-circle", "WhatsApp", "channel_whatsapp", "#10b981"),
                shape_button("headphones", "Freshdesk", "channel_freshdesk", "#38bdf8"),
                shape_button("phone-call", "Canal Bria", "channel_bria", "#f97316"),
                spacing="1",
                width="100%",
            ),
            rx.divider(color_scheme="gray", opacity=0.15),
            # Logic Gateways
            rx.vstack(
                rx.text("Compuertas", size="1", weight="bold", color="#64748b", padding_x="2"),
                shape_button("git-merge", "Paralelo (Y)", "node_activity", "#a855f7"),
                shape_button("git-branch", "Exclusivo (O)", "node_decision", "#ec4899"),
                spacing="1",
                width="100%",
            ),
            spacing="2",
            width="100%",
            padding="2",
        ),
        width="180px",
        height="100%",
        background_color="#0f172a",
        border_right="1px solid #1e293b",
        overflow_y="auto",
    )
