#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Process Auditor Modal Component for TEMIS Web Flow
Structural Governance Analysis & Audit Results powered by Gemini AI
"""

import reflex as rx
from temis_web.state import FlowState


def audit_modal() -> rx.Component:
    """Dialog modal presenting AI Process Audit results and recommendations"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.icon("shield-check", size=24, color="#4f46e5"),
                rx.vstack(
                    rx.dialog.title("Auditoría de Gobierno de Procesos (IA TEMIS)", size="4", weight="bold"),
                    rx.dialog.description("Análisis de calidad, completitud y cumplimiento de las reglas del flujo.", size="2", color="#64748b"),
                    spacing="0",
                ),
                align="center",
                spacing="3",
            ),
            rx.vstack(
                # Score Badge Header
                rx.hstack(
                    rx.badge(
                        "Puntaje de Calidad: ", FlowState.audit_score.to(str), "/100",
                        color_scheme=rx.cond(FlowState.audit_score >= 80, "green", rx.cond(FlowState.audit_score >= 60, "amber", "red")),
                        variant="solid",
                        size="3",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("refresh-cw", size=14),
                        " Re-Auditar",
                        on_click=FlowState.run_ai_process_audit,
                        loading=FlowState.is_auditing_ai,
                        size="1",
                        color_scheme="indigo",
                        variant="soft",
                    ),
                    width="100%",
                    align="center",
                    padding_y="2",
                ),
                # Findings List
                rx.vstack(
                    rx.foreach(
                        FlowState.audit_findings,
                        lambda item: rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.badge(item["severity"], color_scheme=rx.cond(item["severity"] == "Alta", "red", rx.cond(item["severity"] == "Media", "amber", "green")), variant="solid", size="1"),
                                    rx.text(item["title"], size="2", weight="bold", color="#1e293b"),
                                    align="center",
                                    spacing="2",
                                ),
                                rx.text(item["description"], size="2", color="#475569"),
                                rx.box(
                                    rx.hstack(
                                        rx.icon("lightbulb", size=14, color="#d97706"),
                                        rx.text("Recomendación: ", item["recommendation"], size="2", weight="medium", color="#92400e"),
                                        align="center",
                                        spacing="2",
                                    ),
                                    background_color="#fef3c7",
                                    padding="2.5",
                                    border_radius="md",
                                    width="100%",
                                ),
                                spacing="2",
                                align="start",
                                width="100%",
                            ),
                            padding="3",
                            border="1px solid #e2e8f0",
                            border_radius="lg",
                            background_color="#ffffff",
                            width="100%",
                        ),
                    ),
                    spacing="3",
                    width="100%",
                    max_height="360px",
                    overflow_y="auto",
                ),
                spacing="3",
                padding_y="2",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cerrar", color_scheme="gray", variant="soft", on_click=FlowState.close_audit_modal),
                ),
                justify="end",
                margin_top="3",
            ),
            width="560px",
            border_radius="xl",
            padding="5",
        ),
        open=FlowState.show_audit_modal,
        on_open_change=FlowState.close_audit_modal,
    )
