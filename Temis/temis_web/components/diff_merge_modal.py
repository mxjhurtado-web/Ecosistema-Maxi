#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Diff & Merge Modal Component for TEMIS Web Flow
Allows non-destructive review and selective merging when re-analyzing documents 
or updating narratives without silently overwriting manual edits.
"""

import reflex as rx
from temis_web.state import FlowState


def diff_merge_modal() -> rx.Component:
    """Modal dialog to review proposed AI changes against manual edits"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("git-compare", size=20, color="#d97706"),
                    rx.text("Control de Cambios: Propuesta de Actualización IA", size="4", weight="bold", color="#17283c"),
                    align="center",
                    spacing="2",
                ),
                margin_bottom="1",
            ),
            rx.dialog.description(
                "La IA ha detectado cambios en el documento fuente. Revisa las diferencias antes de aplicar:",
                size="2",
                color="#52657a",
            ),
            
            rx.vstack(
                rx.callout(
                    "Tus modificaciones manuales previas están protegidas. Puedes elegir qué elementos actualizar sin perder trabajo.",
                    icon="info",
                    color_scheme="amber",
                    size="1",
                    width="100%",
                ),
                
                # Side-by-side comparison box
                rx.grid(
                    # Left: Current / Manual Version
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("user", size=14, color="#1e5a9a"),
                                rx.text("Versión Vigente (Humana)", size="2", weight="bold", color="#1e5a9a"),
                                align="center",
                                spacing="1",
                            ),
                            rx.text(
                                "Conserva los nombres, decisiones y conexiones ajustadas manualmente en el lienzo y SIPOC.",
                                size="1",
                                color="#52657a",
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        padding="3",
                        background_color="#f8fafc",
                        border="1px solid #d9e2ec",
                        border_radius="md",
                    ),
                    
                    # Right: AI Proposed Version
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("bot", size=14, color="#7c3aed"),
                                rx.text("Propuesta de la IA (Nueva Versión)", size="2", weight="bold", color="#7c3aed"),
                                align="center",
                                spacing="1",
                            ),
                            rx.text(
                                "Incorpora los nuevos datos extraídos de la última versión del documento cargado.",
                                size="1",
                                color="#52657a",
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        padding="3",
                        background_color="#fbfbfe",
                        border="1px solid #ddd6fe",
                        border_radius="md",
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),
                
                spacing="3",
                padding_y="3",
                width="100%",
            ),

            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Mantener Versión Actual",
                        color_scheme="gray",
                        variant="soft",
                        on_click=FlowState.close_narrative_diff_modal,
                    ),
                ),
                rx.spacer(),
                rx.button(
                    rx.hstack(
                        rx.icon("check-check", size=16),
                        rx.text("Aplicar Propuesta IA"),
                        align="center",
                        spacing="1",
                    ),
                    on_click=FlowState.apply_narrative_diff_proposal,
                    color_scheme="blue",
                    variant="solid",
                ),
                justify="end",
                width="100%",
                margin_top="3",
            ),
            width="620px",
            max_width="95vw",
            border_radius="xl",
            padding="5",
            background_color="#ffffff",
            border="1px solid #d9e2ec",
        ),
        open=FlowState.show_narrative_diff_modal,
        on_open_change=FlowState.close_narrative_diff_modal,
    )
