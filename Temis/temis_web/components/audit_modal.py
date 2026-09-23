#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Process Auditor Modal Component for TEMIS Web Flow
Structural Governance Analysis & Audit Results powered by Gemini AI
Styled in Executive Light Slate Theme (WCAG 2.2 AA compliant).
"""

import reflex as rx
from temis_web.state import FlowState


def audit_modal() -> rx.Component:
    """Dialog modal presenting AI Process Audit results and recommendations in executive light slate (F03)"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.box(
                    rx.icon("shield-check", size=24, color="#1e5a9a"),
                    padding="2",
                    background_color="#e0e7ff",
                    border_radius="8px",
                ),
                rx.vstack(
                    rx.dialog.title("Auditoría de Calidad & Gobierno de Procesos (IA TEMIS)", size="4", weight="bold", color="#17283c"),
                    rx.dialog.description("Análisis de reglas Six Sigma, completitud BPMN y asignación de sistemas/canales.", size="2", color="#52657a"),
                    spacing="0",
                ),
                align="center",
                spacing="3",
            ),
            rx.divider(margin_y="2"),
            rx.cond(
                FlowState.has_audit_run,
                # State 1: Audit has been executed
                rx.vstack(
                    # Score Badge & Delta Header
                    rx.vstack(
                        rx.hstack(
                            rx.badge(
                                "Puntaje de Calidad: ", FlowState.audit_score.to(str), "/100",
                                color_scheme=rx.cond(FlowState.audit_score >= 80, "green", rx.cond(FlowState.audit_score >= 60, "amber", "red")),
                                variant="solid",
                                size="3",
                            ),
                            rx.badge(
                                rx.hstack(
                                    rx.icon("trending-up", size=12, color="#107c41"),
                                    rx.text(FlowState.audit_score_delta_label, " vs anterior"),
                                    align="center",
                                    spacing="1",
                                ),
                                color_scheme="green",
                                variant="soft",
                                size="2",
                            ),
                            rx.spacer(),
                            rx.button(
                                rx.hstack(
                                    rx.icon("refresh-cw", size=14),
                                    rx.text("Re-Auditar Flujo"),
                                    align="center",
                                    spacing="1",
                                ),
                                on_click=FlowState.run_ai_process_audit,
                                loading=FlowState.is_auditing_ai,
                                size="2",
                                color_scheme="blue",
                                variant="soft",
                                radius="medium",
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.hstack(
                            rx.hstack(
                                rx.icon("calendar", size=12, color="#52657a"),
                                rx.text("Última Evaluación: ", FlowState.last_audit_date, size="1", color="#52657a"),
                                align="center",
                                spacing="1",
                            ),
                            rx.text("·", size="1", color="#94a3b8"),
                            rx.hstack(
                                rx.icon("shield", size=12, color="#52657a"),
                                rx.text("Reglas: ", FlowState.audit_rules_version, size="1", color="#52657a"),
                                align="center",
                                spacing="1",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        width="100%",
                        spacing="2",
                        padding_y="1",
                    ),
                    # Findings List
                    rx.vstack(
                        rx.foreach(
                            FlowState.audit_findings,
                            lambda item: rx.box(
                                rx.vstack(
                                    rx.hstack(
                                        rx.badge(item["severity"], color_scheme=rx.cond(item["severity"] == "Alta", "red", rx.cond(item["severity"] == "Media", "amber", "green")), variant="solid", size="1"),
                                        rx.text(item["title"], size="2", weight="bold", color="#17283c"),
                                        align="center",
                                        spacing="2",
                                    ),
                                    rx.text(item["description"], size="2", color="#52657a"),
                                    rx.box(
                                        rx.hstack(
                                            rx.icon("lightbulb", size=14, color="#b45309"),
                                            rx.text("Recomendación: ", item["recommendation"], size="2", weight="medium", color="#92400e"),
                                            align="center",
                                            spacing="2",
                                        ),
                                        background_color="#fffbeb",
                                        border="1px solid #fde68a",
                                        padding="2.5",
                                        border_radius="md",
                                        width="100%",
                                    ),
                                    spacing="2",
                                    align="start",
                                    width="100%",
                                ),
                                padding="3",
                                border="1px solid #d9e2ec",
                                border_radius="lg",
                                background_color="#f8fafc",
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
                # State 2: No previous audit on this project
                rx.box(
                    rx.vstack(
                        rx.box(
                            rx.icon("sparkles", size=36, color="#4f46e5"),
                            padding="3",
                            background_color="#ede9fe",
                            border_radius="full",
                        ),
                        rx.text("Evaluación de Calidad Pendiente", size="3", weight="bold", color="#17283c"),
                        rx.text(
                            "Este proyecto aún no ha sido evaluado. El motor de Inteligencia Artificial analizará el diagrama en busca de nodos huérfanos, decisiones sin bifurcación Sí/No y actividades sin sistema o canal asignado.",
                            size="2",
                            color="#52657a",
                            text_align="center",
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon("sparkles", size=16),
                                rx.text("Ejecutar Auditoría con Gemini AI"),
                                align="center",
                                spacing="2",
                            ),
                            on_click=FlowState.run_ai_process_audit,
                            loading=FlowState.is_auditing_ai,
                            color_scheme="indigo",
                            size="3",
                            radius="medium",
                            margin_top="2",
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                        padding_y="5",
                    ),
                    width="100%",
                ),
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cerrar", color_scheme="gray", variant="soft", on_click=FlowState.close_audit_modal),
                ),
                justify="end",
                margin_top="3",
            ),
            width="580px",
            max_width="95vw",
            border_radius="xl",
            padding="5",
            background_color="#ffffff",
            border="1px solid #d9e2ec",
        ),
        open=FlowState.show_audit_modal,
        on_open_change=FlowState.close_audit_modal,
    )
