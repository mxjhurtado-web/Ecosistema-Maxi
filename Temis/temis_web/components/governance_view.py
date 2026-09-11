#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Governance & 7-Phase Methodology Component for TEMIS Web Flow
Visual tracking of project phases, key deliverables, gates, and AI quality auditing.
"""

import reflex as rx
from temis_web.state import FlowState


PHASE_LIST = [
    {
        "num": 1,
        "name": "Fase 1: Diagnóstico Estratégico",
        "desc": "Identificación de la oportunidad, análisis de dolor operativo y alineación con objetivos de negocio.",
        "deliverables": ["Ficha de Diagnóstico", "Matriz de Interesados", "Justificación de Negocio"],
        "icon": "search",
        "color": "#3b82f6"
    },
    {
        "num": 2,
        "name": "Fase 2: Inicio del Proyecto",
        "desc": "Definición formal del Project Charter, asignación de PM / Sponsor y delimitación de alcance.",
        "deliverables": ["Project Charter Oficial", "Matriz SIPOC Inicial", "Asignación RACI"],
        "icon": "play",
        "color": "#6366f1"
    },
    {
        "num": 3,
        "name": "Fase 3: Planificación Híbrida",
        "desc": "Mapeo de procesos As-Is / To-Be, arquitectura técnica y cronograma Scrum 2026.",
        "deliverables": ["Diagrama BPMN Multi-Pestaña", "Backlog Scrum Técnico", "Matriz de Riesgos"],
        "icon": "calendar",
        "color": "#8b5cf6"
    },
    {
        "num": 4,
        "name": "Fase 4: Ejecución Iterativa",
        "desc": "Desarrollo de integraciones, sprints técnicos y redacción de procedimientos operativos.",
        "deliverables": ["Manual de Políticas y Procedimientos", "Servicios Backend / UI", "Daily Logs (EOD)"],
        "icon": "code",
        "color": "#06b6d4"
    },
    {
        "num": 5,
        "name": "Fase 5: Monitoreo y Control",
        "desc": "Auditoría de calidad Six Sigma, pruebas de extremo a extremo y validación con usuarios.",
        "deliverables": ["Auditoría IA de Calidad (0-100)", "Reporte de Cumplimiento SLA", "Pruebas UAT"],
        "icon": "shield-check",
        "color": "#10b981"
    },
    {
        "num": 6,
        "name": "Fase 6: Mejora Continua",
        "desc": "Optimización post-lanzamiento, retroalimentación operativa y ajustes de automatización.",
        "deliverables": ["Plan de Ajustes Kaizen", "Encuesta de Satisfacción", "Métricas Operativas"],
        "icon": "trending-up",
        "color": "#f59e0b"
    },
    {
        "num": 7,
        "name": "Fase 7: Cierre del Proyecto",
        "desc": "Entrega formal de activos, lecciones aprendidas y traspaso a operaciones continuas.",
        "deliverables": ["Acta de Cierre Aprobada", "Paquete .temis.json Exportado", "Lecciones Aprendidas"],
        "icon": "check-circle-2",
        "color": "#ec4899"
    }
]


def render_phase_card(p: dict) -> rx.Component:
    """Render a single methodology phase card"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(p["icon"], size=18, color=p["color"]),
                rx.text(p["name"], size="2", weight="bold", color="#1e293b"),
                rx.spacer(),
                rx.button(
                    "Activar Fase",
                    on_click=lambda: FlowState.set_phase(p["num"]),
                    color_scheme="purple",
                    variant="soft",
                    size="1",
                    radius="small",
                ),
                width="100%",
                align="center",
            ),
            rx.text(p["desc"], size="1", color="#64748b"),
            rx.divider(),
            rx.text("Entregables Clave:", size="1", weight="bold", color="#475569"),
            rx.hstack(
                *[rx.badge(d, color_scheme="gray", variant="soft", size="1") for d in p["deliverables"]],
                wrap="wrap",
                spacing="1",
            ),
            width="100%",
            spacing="2",
        ),
        background_color="#ffffff",
        border="1px solid #e2e8f0",
        border_radius="8px",
        padding="3",
        box_shadow="0 1px 2px 0 rgba(0, 0, 0, 0.03)",
        width="100%",
    )


def governance_view() -> rx.Component:
    """Governance & Methodology View"""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.hstack(
                    rx.icon("layers", size=24, color="#7c3aed"),
                    rx.vstack(
                        rx.text("Gobernanza & Metodología de 7 Fases", size="4", weight="bold", color="#0f172a"),
                        rx.text("Ciclo de vida corporativo de procesos, control de entregables y auditoría de calidad", size="2", color="#64748b"),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        rx.icon("shield-check", size=15),
                        " Auditar Proceso con IA",
                        on_click=FlowState.open_audit_modal,
                        color_scheme="indigo",
                        size="2",
                        radius="medium",
                    ),
                    rx.badge(
                        "Fase Actual: " + FlowState.phase_name,
                        color_scheme="purple",
                        variant="surface",
                        size="2",
                    ),
                    spacing="2",
                    align="center",
                ),
                width="100%",
                padding_y="3",
                border_bottom="1px solid #e2e8f0",
                align="center",
            ),

            # Grid of 7 Phases
            rx.box(
                rx.vstack(
                    *[render_phase_card(p) for p in PHASE_LIST],
                    width="100%",
                    spacing="3",
                ),
                width="100%",
                max_height="calc(100vh - 165px)",
                overflow_y="auto",
                padding_right="2",
            ),
            width="100%",
            height="100%",
            spacing="3",
            padding="4",
        ),
        width="100%",
        height="100%",
        overflow="hidden",
        background_color="#f8fafc",
    )
