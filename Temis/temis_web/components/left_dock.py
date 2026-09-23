#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Left Shape Dock Component for TEMIS Web Flow
Collapsible tool palette for BPMN, Systems, Channels, and Gateways
Styled in Executive Light Slate Theme (WCAG 2.2 AA compliant).
"""

import reflex as rx
from temis_web.state import FlowState


def shape_button(icon_name: str, label: str, node_type: str, color: str = "#52657a") -> rx.Component:
    """Reusable compact shape button in light slate theme"""
    return rx.button(
        rx.hstack(
            rx.icon(icon_name, size=14, color=color),
            rx.text(label, size="1", weight="medium", color="#17283c", truncate=True),
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
        _hover={"background_color": "#d9e2ec"},
    )


def left_dock() -> rx.Component:
    """Left sidebar shape dock"""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.icon("shapes", size=15, color="#1e5a9a"),
                rx.text("FORMAS", size="1", weight="bold", color="#52657a", letter_spacing="0.05em"),
                align="center",
                spacing="2",
                padding_x="2",
                padding_y="1",
            ),
            # BPMN Category
            rx.vstack(
                rx.text("BPMN / Proceso", size="1", weight="bold", color="#52657a", padding_x="2"),
                shape_button("circle-play", "Inicio Proceso", "node_start", "#1e5a9a"),
                shape_button("square-check", "Actividad", "node_activity", "#107c41"),
                shape_button("circle-help", "Decisión", "node_decision", "#b76e00"),
                shape_button("circle-stop", "Fin Proceso", "node_end", "#52657a"),
                shape_button("clock", "Demora / Espera", "node_activity", "#ea580c"),
                shape_button("file-text", "Documento", "node_document", "#1e5a9a"),
                shape_button("layers", "Subproceso", "node_activity", "#7c3aed"),
                spacing="1",
                width="100%",
            ),
            rx.divider(color_scheme="gray", opacity=0.15),
            # Systems & Channels Category
            rx.vstack(
                rx.text("Sistemas & Canales", size="1", weight="bold", color="#52657a", padding_x="2"),
                shape_button("cpu", "Sistema Chronos", "node_system", "#107c41"),
                shape_button("database", "Base de Datos", "node_database", "#0891b2"),
                shape_button("monitor", "Pantalla / Menú", "node_system", "#1e5a9a"),
                shape_button("message-circle", "WhatsApp", "channel_whatsapp", "#107c41"),
                shape_button("headphones", "Freshdesk", "channel_freshdesk", "#1e5a9a"),
                shape_button("phone-call", "Canal Bria", "channel_bria", "#ea580c"),
                spacing="1",
                width="100%",
            ),
            rx.divider(color_scheme="gray", opacity=0.15),
            # Logic Gateways
            rx.vstack(
                rx.text("Compuertas", size="1", weight="bold", color="#52657a", padding_x="2"),
                shape_button("git-merge", "Paralelo (Y)", "node_activity", "#7c3aed"),
                shape_button("git-branch", "Exclusivo (O)", "node_decision", "#db2777"),
                spacing="1",
                width="100%",
            ),
            spacing="2",
            width="100%",
            padding="2",
        ),
        width="180px",
        height="100%",
        background_color="#eaf0f6",
        border_right="1px solid #d9e2ec",
        overflow_y="auto",
    )
