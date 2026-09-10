#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Application for TEMIS Web Flow (Reflex)
Full-Stack Web App for Process Governance & Official Flowchart Diagrams
"""

import reflex as rx

from temis_web.state import FlowState
from temis_web.components.header import header
from temis_web.components.left_dock import left_dock
from temis_web.components.flowchart_canvas import flowchart_canvas
from temis_web.components.property_inspector import property_inspector
from temis_web.components.bottom_bar import bottom_bar
from temis_web.components.project_modal import recent_projects_modal
from temis_web.components.connect_modal import connect_modal
from temis_web.components.audit_modal import audit_modal


def index() -> rx.Component:
    """Main modern SaaS layout of TEMIS Web Flow (Lucidchart / Figma style)"""
    return rx.box(
        recent_projects_modal(),
        connect_modal(),
        audit_modal(),
        rx.vstack(
            header(),
            rx.hstack(
                left_dock(),
                flowchart_canvas(),
                property_inspector(),
                width="100%",
                flex="1",
                height="calc(100vh - 88px)",
                overflow="hidden",
                spacing="0",
            ),
            bottom_bar(),
            width="100%",
            height="100vh",
            spacing="0",
        ),
        background_color="#f8fafc",
        font_family="Inter, sans-serif",
    )


app = rx.App(
    stylesheets=["style.css"],
)

app.add_page(index, title="TEMIS Web Flow - Herramienta de Flujos y Gobierno")
