#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Header component for TEMIS Web Flow
Top navbar with title, Gemini AI prompt bar and phase indicator
"""

import reflex as rx
from temis_web.state import FlowState


def header() -> rx.Component:
    """Header bar component"""
    return rx.box(
        rx.hstack(
            # Logo & Title
            rx.hstack(
                rx.icon("git-branch", size=28, color="#3b82f6"),
                rx.vstack(
                    rx.heading("TEMIS Web Flow", size="5", weight="bold", color="#1e293b"),
                    rx.text("Herramienta de Flujos & Gobierno de Proyectos", size="1", color="#64748b"),
                    spacing="0",
                ),
                align="center",
                spacing="3",
            ),
            rx.spacer(),
            # Gemini AI Prompt Bar
            rx.hstack(
                rx.input(
                    placeholder="Describe el proceso para que Gemini genere el flujo (ej: Reembolso de dinero por WhatsApp)...",
                    value=FlowState.ai_prompt_text,
                    on_change=FlowState.set_ai_prompt_text,
                    width="420px",
                    size="2",
                    variant="surface",
                    radius="large",
                ),
                rx.button(
                    rx.icon("sparkles", size=16),
                    " Generar con IA",
                    on_click=FlowState.generate_with_gemini,
                    loading=FlowState.is_generating_ai,
                    color_scheme="indigo",
                    size="2",
                    radius="large",
                ),
                align="center",
                spacing="2",
            ),
            rx.spacer(),
            # Status Badge & Governance Phase Dropdown
            rx.hstack(
                rx.badge(FlowState.status_message, color_scheme="blue", variant="soft", size="2"),
                rx.menu.root(
                    rx.menu.trigger(
                        rx.button(
                            rx.icon("layers", size=16),
                            " Gobernanza: Fase ",
                            FlowState.current_phase,
                            " ▾",
                            color_scheme="purple",
                            variant="soft",
                            size="2",
                        ),
                    ),
                    rx.menu.content(
                        rx.menu.item("Fase 1: Diagnóstico Estratégico", on_click=lambda: FlowState.set_phase(1)),
                        rx.menu.item("Fase 2: Inicio del Proyecto", on_click=lambda: FlowState.set_phase(2)),
                        rx.menu.item("Fase 3: Planificación Híbrida", on_click=lambda: FlowState.set_phase(3)),
                        rx.menu.item("Fase 4: Ejecución Iterativa", on_click=lambda: FlowState.set_phase(4)),
                        rx.menu.item("Fase 5: Monitoreo y Control", on_click=lambda: FlowState.set_phase(5)),
                        rx.menu.item("Fase 6: Mejora Continua", on_click=lambda: FlowState.set_phase(6)),
                        rx.menu.item("Fase 7: Cierre del Proyecto", on_click=lambda: FlowState.set_phase(7)),
                    ),
                ),
                align="center",
                spacing="2",
            ),
            width="100%",
            align="center",
            padding_x="4",
            padding_y="3",
        ),
        background_color="#ffffff",
        border_bottom="1px solid #e2e8f0",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
        width="100%",
    )
