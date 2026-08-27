#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Application for TEMIS Web Flow (Reflex)
Full-Stack Web App for Process Governance & Official Flowchart Diagrams
"""

import reflex as rx

from temis_web.state import FlowState
from temis_web.components.header import header
from temis_web.components.sidebar import sidebar
from temis_web.components.symbology_palette import symbology_palette
from temis_web.components.flowchart_canvas import flowchart_canvas


def index() -> rx.Component:
    """Main page layout of TEMIS Web Flow"""
    return rx.box(
        rx.vstack(
            header(),
            rx.hstack(
                sidebar(),
                flowchart_canvas(),
                symbology_palette(),
                width="100%",
                spacing="0",
            ),
            width="100%",
            height="100vh",
            spacing="0",
        ),
        background_color="#f8fafc",
        font_family="Inter, sans-serif",
    )


app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="blue",
        radius="medium",
    )
)

app.add_page(index, title="TEMIS Web Flow - Herramienta de Flujos y Gobierno")
