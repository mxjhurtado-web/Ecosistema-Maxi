#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Left Shape Dock Component for TEMIS Web Flow
Collapsible tool palette for BPMN, Systems, Channels, and Gateways
"""

import reflex as rx
from temis_web.state import FlowState


def shape_button(icon_name: str, label: str, node_type: str, color: str = "#475569") -> rx.Component:
    """Reusable compact shape button"""
    return rx.button(
        rx.hstack(
            rx.icon(icon_name, size=14, color=color),
            rx.text(label, size="1", weight="medium", color="#1e293b", truncate=True),
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
        padding_y="1.5",
        border_radius="md",
        _hover={"background_color": "#f1f5f9"},
    )


def left_dock() -> rx.Component:
    """Left sidebar shape dock"""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("shapes", size=15, color="#2563eb"),
                rx.text("FORMAS", size="1", weight="bold", color="#64748b", letter_spacing="0.05em"),
                align="center",
                spacing="2",
                padding_x="2",
                padding_y="1",
            ),
            # BPMN Category
            rx.vstack(
                rx.text("BPMN / Proceso", size="1", weight="bold", color="#94a3b8", padding_x="2"),
                shape_button("play-circle", "Inicio Proceso", "node_start", "#2563eb"),
                shape_button("square-check", "Actividad", "node_activity", "#16a34a"),
                shape_button("circle-help", "Decisión", "node_decision", "#d97706"),
                shape_button("stop-circle", "Fin Proceso", "node_end", "#64748b"),
                shape_button("clock", "Demora / Espera", "node_activity", "#ea580c"),
                shape_button("file-text", "Documento", "node_document", "#0284c7"),
                shape_button("layers", "Subproceso", "node_activity", "#7c3aed"),
                spacing="1",
                width="100%",
            ),
            rx.divider(color="#e2e8f0"),
            # Systems & Channels Category
            rx.vstack(
                rx.text("Sistemas & Canales", size="1", weight="bold", color="#94a3b8", padding_x="2"),
                shape_button("cpu", "Sistema Chronos", "node_system", "#059669"),
                shape_button("database", "Base de Datos", "node_database", "#0891b2"),
                shape_button("monitor", "Pantalla / Menú", "node_system", "#2563eb"),
                shape_button("message-circle", "WhatsApp", "channel_whatsapp", "#16a34a"),
                shape_button("headphones", "Freshdesk", "channel_freshdesk", "#0284c7"),
                shape_button("phone-call", "Canal Bria", "channel_bria", "#ea580c"),
                spacing="1",
                width="100%",
            ),
            rx.divider(color="#e2e8f0"),
            # Logic Gateways
            rx.vstack(
                rx.text("Compuertas", size="1", weight="bold", color="#94a3b8", padding_x="2"),
                shape_button("git-merge", "Paralelo (Y)", "node_activity", "#9333ea"),
                shape_button("git-branch", "Exclusivo (O)", "node_decision", "#c026d3"),
                spacing="1",
                width="100%",
            ),
            spacing="2",
            width="100%",
            padding="2",
        ),
        width="180px",
        height="100%",
        background_color="#ffffff",
        border_right="1px solid #e2e8f0",
        overflow_y="auto",
    )
