#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Governance & 7-Phase Methodology Component for TEMIS Web Flow
Visual tracking of project phases, key deliverables, gates, and AI quality auditing.
Styled in Executive Light Slate Theme (WCAG 2.2 AA compliant).
"""

import reflex as rx
from temis_web.state import FlowState


PHASE_LIST = [
    {
        "num": 1,
        "name": "Fase 1: Diagnóstico Estratégico",
        "desc": "Identificación de la oportunidad, análisis de dolor operativo y alineación con objetivos de negocio.",
        "owner": "Dirección General / Sponsor",
        "deliverables": ["Ficha de Diagnóstico", "Matriz de Interesados", "Justificación de Negocio"],
        "gate_criteria": "Aprobación de oportunidad y factibilidad inicial.",
        "icon": "search",
        "color": "#1e5a9a"
    },
    {
        "num": 2,
        "name": "Fase 2: Inicio del Proyecto",
        "desc": "Definición formal del Project Charter, asignación de PM / Sponsor y delimitación de alcance.",
        "owner": "Project Manager (PM)",
        "deliverables": ["Project Charter Oficial", "Matriz SIPOC Inicial", "Asignación RACI"],
        "gate_criteria": "Charter firmado y alcance preliminar delimitado.",
        "icon": "play",
        "color": "#4f46e5"
    },
    {
        "num": 3,
        "name": "Fase 3: Planificación Híbrida",
        "desc": "Mapeo de procesos As-Is / To-Be, arquitectura técnica y cronograma Scrum 2026.",
        "owner": "PM & Analista de Procesos",
        "deliverables": ["Diagrama BPMN Multi-Pestaña", "Backlog Scrum Técnico", "Matriz de Riesgos"],
        "gate_criteria": "Plan de trabajo desglosado en Sprints y estimación de SP.",
        "icon": "calendar",
        "color": "#7c3aed"
    },
    {
        "num": 4,
        "name": "Fase 4: Ejecución Iterativa",
        "desc": "Desarrollo de integraciones, sprints técnicos y redacción de procedimientos operativos.",
        "owner": "Equipo de Desarrollo & Procesos",
        "deliverables": ["Manual de Políticas y Procedimientos", "Servicios Backend / UI", "Daily Logs (EOD)"],
        "gate_criteria": "Entregables del sprint completados y documentados.",
        "icon": "code",
        "color": "#0891b2"
    },
    {
        "num": 5,
        "name": "Fase 5: Monitoreo y Control",
        "desc": "Auditoría de calidad Six Sigma, pruebas de extremo a extremo y validación con usuarios.",
        "owner": "Auditor QA / Six Sigma",
        "deliverables": ["Auditoría IA de Calidad (0-100)", "Reporte de Cumplimiento SLA", "Pruebas UAT"],
        "gate_criteria": "Score de calidad Six Sigma >= 80 y sin bloqueos P0.",
        "icon": "shield-check",
        "color": "#107c41"
    },
    {
        "num": 6,
        "name": "Fase 6: Mejora Continua",
        "desc": "Optimización post-lanzamiento, retroalimentación operativa y ajustes de automatización.",
        "owner": "Operaciones & Mejora Continua",
        "deliverables": ["Plan de Ajustes Kaizen", "Encuesta de Satisfacción", "Métricas Operativas"],
        "gate_criteria": "Retroalimentación recopilada y plan de optimización activo.",
        "icon": "trending-up",
        "color": "#b76e00"
    },
    {
        "num": 7,
        "name": "Fase 7: Cierre del Proyecto",
        "desc": "Entrega formal de activos, lecciones aprendidas y traspaso a operaciones continuas.",
        "owner": "PM & Sponsor",
        "deliverables": ["Acta de Cierre Aprobada", "Paquete .temis.json Exportado", "Lecciones Aprendidas"],
        "gate_criteria": "Acta de cierre firmada y archivo respaldado en Drive.",
        "icon": "circle-check",
        "color": "#db2777"
    }
]


def phase_gate_approval_modal() -> rx.Component:
    """Dialog modal for approving phase gate deliverables and advancing sequentially (F01)"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.icon("git-commit-horizontal", size=22, color="#1e5a9a"),
                        padding="2",
                        background_color="#e0e7ff",
                        border_radius="8px",
                    ),
                    rx.vstack(
                        rx.dialog.title("Aprobación de Gate de Gobernanza TEMIS", size="4", weight="bold", color="#17283c"),
                        rx.dialog.description(
                            "Verifica los entregables y confirma la promoción de fase oficial.",
                            size="2",
                            color="#52657a",
                        ),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.divider(),
                # Current vs Target Phase Info
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text("Fase Origen", size="1", color="#64748b", weight="bold"),
                            rx.text(FlowState.phase_name, size="2", weight="bold", color="#17283c"),
                            spacing="0",
                        ),
                        padding="3",
                        background_color="#f8fafc",
                        border="1px solid #e2e8f0",
                        border_radius="8px",
                        flex="1",
                    ),
                    rx.icon("arrow-right", size=20, color="#64748b"),
                    rx.box(
                        rx.vstack(
                            rx.text("Fase Destino (Promoción)", size="1", color="#1d4ed8", weight="bold"),
                            rx.text(FlowState.target_gate_phase_name, size="2", weight="bold", color="#1e5a9a"),
                            spacing="0",
                        ),
                        padding="3",
                        background_color="#eff6ff",
                        border="1px solid #bfdbfe",
                        border_radius="8px",
                        flex="1",
                    ),
                    align="center",
                    width="100%",
                    spacing="3",
                ),
                # Gate Criteria Callout
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("shield-check", size=15, color="#107c41"),
                            rx.text("Criterio de Gate Requerido:", size="1", weight="bold", color="#166534"),
                            spacing="1",
                            align="center",
                        ),
                        rx.text(FlowState.target_gate_criteria, size="2", color="#14532d"),
                        spacing="1",
                    ),
                    padding="3",
                    background_color="#f0fdf4",
                    border="1px solid #bbf7d0",
                    border_radius="8px",
                    width="100%",
                ),
                # Deliverables Checklist (H01)
                rx.vstack(
                    rx.hstack(
                        rx.text("Verificación de Entregables de la Fase:", size="2", weight="bold", color="#17283c"),
                        rx.spacer(),
                        rx.badge(
                            FlowState.phase_gate_checked_deliverables.length().to(str) + " de " + FlowState.target_gate_deliverables.length().to(str) + " Validados",
                            color_scheme=rx.cond(FlowState.all_gate_deliverables_checked, "green", "amber"),
                            variant="surface",
                            size="1",
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.foreach(
                        FlowState.target_gate_deliverables,
                        lambda item: rx.hstack(
                            rx.checkbox(
                                checked=FlowState.phase_gate_checked_deliverables.contains(item),
                                on_change=lambda _: FlowState.toggle_gate_deliverable(item),
                                size="2",
                            ),
                            rx.text(item, size="2", color="#17283c", weight="medium", cursor="pointer"),
                            rx.spacer(),
                            rx.cond(
                                FlowState.phase_gate_checked_deliverables.contains(item),
                                rx.badge(rx.hstack(rx.icon("check", size=10), rx.text("Verificado"), align="center", spacing="1"), color_scheme="green", variant="solid", size="1"),
                                rx.badge(rx.hstack(rx.icon("clock", size=10), rx.text("Pendiente"), align="center", spacing="1"), color_scheme="amber", variant="soft", size="1"),
                            ),
                            on_click=lambda: FlowState.toggle_gate_deliverable(item),
                            align="center",
                            width="100%",
                            padding_y="2",
                            padding_x="3",
                            background_color=rx.cond(
                                FlowState.phase_gate_checked_deliverables.contains(item),
                                "#f0fdf4",
                                "#ffffff",
                            ),
                            border=rx.cond(
                                FlowState.phase_gate_checked_deliverables.contains(item),
                                "1px solid #bbf7d0",
                                "1px solid #e2e8f0",
                            ),
                            border_radius="6px",
                            cursor="pointer",
                        ),
                    ),
                    spacing="2",
                    width="100%",
                ),
                # Checkbox Validation Warning Callout
                rx.cond(
                    ~FlowState.all_gate_deliverables_checked,
                    rx.callout(
                        "Debes verificar y marcar todos los entregables requeridos para habilitar la firma del Gate.",
                        icon="info",
                        color_scheme="amber",
                        size="1",
                        width="100%",
                    ),
                    rx.box(),
                ),
                # Authenticated Signer & Approval Notes (H01)
                rx.vstack(
                    rx.vstack(
                        rx.text("Aprobador Autenticado (Signer):", size="1", weight="bold", color="#52657a"),
                        rx.hstack(
                            rx.icon("user-check", size=16, color="#1e5a9a"),
                            rx.text(FlowState.phase_gate_signer, size="2", weight="bold", color="#17283c"),
                            rx.spacer(),
                            rx.badge("Sesión Verificada", color_scheme="green", variant="soft", size="1"),
                            align="center",
                            spacing="2",
                            padding_x="3",
                            padding_y="2",
                            background_color="#f8fafc",
                            border="1px solid #d9e2ec",
                            border_radius="6px",
                            width="100%",
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Notas / Observaciones de Aprobación:", size="1", weight="bold", color="#52657a"),
                        rx.input(
                            value=FlowState.phase_gate_notes,
                            on_change=FlowState.set_phase_gate_notes,
                            placeholder="ej. Entregables revisados y validados conforme al estándar Six Sigma",
                            size="1",
                            width="100%",
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.divider(),
                # Actions
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        color_scheme="gray",
                        variant="soft",
                        size="2",
                        on_click=FlowState.close_phase_gate_modal,
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(
                            rx.icon("circle-check", size=16),
                            rx.text("Firmar y Avanzar de Fase"),
                            align="center",
                            spacing="1",
                        ),
                        on_click=FlowState.confirm_phase_gate_approval,
                        disabled=~FlowState.all_gate_deliverables_checked,
                        color_scheme="blue",
                        size="2",
                        radius="medium",
                    ),
                    width="100%",
                    align="center",
                ),
                spacing="3",
                width="100%",
            ),
            width="540px",
            max_width="95vw",
            border_radius="xl",
            padding="5",
            background_color="#ffffff",
        ),
        open=FlowState.show_phase_gate_modal,
        on_open_change=FlowState.close_phase_gate_modal,
    )


def phase_blocked_modal() -> rx.Component:
    """Dialog modal shown when attempting to skip phases without completing sequential gates (F01)"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.icon("triangle-alert", size=24, color="#dc2626"),
                        padding="2",
                        background_color="#fee2e2",
                        border_radius="8px",
                    ),
                    rx.vstack(
                        rx.dialog.title("Salto de Fase Bloqueado por Gobernanza", size="4", weight="bold", color="#991b1b"),
                        rx.dialog.description(
                            "La metodología TEMIS exige avance secuencial con aprobación de gates.",
                            size="2",
                            color="#64748b",
                        ),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.divider(),
                rx.box(
                    rx.vstack(
                        rx.text(
                            "No puedes activar ",
                            rx.text(FlowState.target_gate_phase_name, weight="bold", as_="span"),
                            " directamente desde ",
                            rx.text(FlowState.phase_name, weight="bold", as_="span"),
                            ".",
                            size="2",
                            color="#17283c",
                        ),
                        rx.text(
                            "Debes completar y aprobar secuencialmente los entregables de cada fase intermedia para mantener la trazabilidad y calidad Six Sigma.",
                            size="2",
                            color="#52657a",
                        ),
                        spacing="2",
                    ),
                    padding="3",
                    background_color="#f8fafc",
                    border="1px solid #e2e8f0",
                    border_radius="8px",
                    width="100%",
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Entendido",
                        color_scheme="blue",
                        variant="solid",
                        size="2",
                        on_click=FlowState.close_phase_blocked_modal,
                    ),
                    width="100%",
                    align="center",
                ),
                spacing="3",
                width="100%",
            ),
            width="480px",
            max_width="95vw",
            border_radius="xl",
            padding="5",
            background_color="#ffffff",
        ),
        open=FlowState.show_phase_blocked_modal,
        on_open_change=FlowState.close_phase_blocked_modal,
    )


def render_phase_card(p: dict) -> rx.Component:
    """Render a single methodology phase card with operational governance tracking"""
    is_active = FlowState.current_phase == p["num"]
    is_past = FlowState.current_phase > p["num"]
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon(p["icon"], size=18, color=p["color"]),
                    rx.text(p["name"], size="2", weight="bold", color="#17283c"),
                    rx.cond(
                        is_active,
                        rx.badge(rx.hstack(rx.icon("star", size=10), rx.text("Fase Activa"), align="center", spacing="1"), color_scheme="green", variant="solid", size="1"),
                        rx.cond(
                            is_past,
                            rx.badge(rx.hstack(rx.icon("check", size=10), rx.text("Completada"), align="center", spacing="1"), color_scheme="blue", variant="soft", size="1"),
                            rx.badge(rx.hstack(rx.icon("clock", size=10), rx.text("Pendiente"), align="center", spacing="1"), color_scheme="gray", variant="soft", size="1"),
                        ),
                    ),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                rx.cond(
                    is_active,
                    rx.badge("En Curso", color_scheme="green", variant="surface", size="1"),
                    rx.button(
                        "Activar Fase",
                        on_click=lambda: FlowState.request_phase_change(p["num"]),
                        color_scheme="blue",
                        variant="soft",
                        size="1",
                        radius="small",
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.text(p["desc"], size="1", color="#52657a"),
            rx.hstack(
                rx.hstack(
                    rx.icon("user-check", size=13, color="#4f46e5"),
                    rx.text("Responsable: ", size="1", weight="bold", color="#52657a"),
                    rx.text(p["owner"], size="1", color="#4f46e5", weight="medium"),
                    spacing="1",
                    align="center",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.icon("git-commit-horizontal", size=13, color="#107c41"),
                    rx.text("Criterio Gate: ", size="1", weight="bold", color="#52657a"),
                    rx.text(p["gate_criteria"], size="1", color="#107c41", weight="medium"),
                    spacing="1",
                    align="center",
                ),
                width="100%",
                wrap="wrap",
                spacing="2",
            ),
            rx.divider(color_scheme="gray", opacity=0.15),
            rx.hstack(
                rx.text("Entregables & Evidencia Requerida:", size="1", weight="bold", color="#52657a"),
                rx.spacer(),
                rx.hstack(
                    *[
                        rx.badge(
                            rx.hstack(
                                rx.icon("circle-check", size=11),
                                rx.text(d),
                                align="center",
                                spacing="1",
                            ),
                            color_scheme="gray",
                            variant="surface",
                            size="1",
                        ) for d in p["deliverables"]
                    ],
                    wrap="wrap",
                    spacing="1",
                ),
                width="100%",
                wrap="wrap",
                align="center",
            ),
            width="100%",
            spacing="2",
        ),
        background_color=rx.cond(is_active, "#f0fdf4", "#ffffff"),
        border=rx.cond(is_active, "1px solid #86efac", "1px solid #d9e2ec"),
        border_radius="10px",
        padding="4",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
        width="100%",
    )


def render_gate_history_item(log: rx.Var[dict]) -> rx.Component:
    """Render an immutable gate approval log record (H01)"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("shield-check", size=16, color="#107c41"),
                    rx.text(log["phase_name"], size="2", weight="bold", color="#17283c"),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                rx.badge(
                    rx.hstack(rx.icon("calendar", size=11), rx.text(log["approved_at"]), align="center", spacing="1"),
                    color_scheme="blue",
                    variant="surface",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.hstack(
                    rx.icon("user-check", size=13, color="#4f46e5"),
                    rx.text("Aprobado por:", size="1", weight="bold", color="#52657a"),
                    rx.text(log["approved_by"], size="1", color="#4f46e5", weight="bold"),
                    rx.badge(log["user_role"], color_scheme="indigo", variant="soft", size="1"),
                    spacing="1",
                    align="center",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.icon("git-commit-horizontal", size=13, color="#107c41"),
                    rx.text("Criterio:", size="1", weight="bold", color="#52657a"),
                    rx.text(log["gate_criteria"], size="1", color="#107c41"),
                    spacing="1",
                    align="center",
                ),
                width="100%",
                wrap="wrap",
                spacing="2",
            ),
            rx.text(log["notes"], size="1", color="#52657a", font_style="italic"),
            spacing="1",
            width="100%",
        ),
        padding="3",
        background_color="#ffffff",
        border="1px solid #d9e2ec",
        border_left="4px solid #107c41",
        border_radius="8px",
        width="100%",
    )


def render_gate_history_section() -> rx.Component:
    """Render the immutable audit history of completed phase gates (H01)"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("history", size=18, color="#1e5a9a"),
                rx.text("Bitácora Inmutable de Aprobación de Gates", size="3", weight="bold", color="#17283c"),
                rx.spacer(),
                rx.badge(
                    FlowState.gate_approvals_history.length().to(str) + " Gates Aprobados",
                    color_scheme="green",
                    variant="soft",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            rx.divider(color_scheme="gray", opacity=0.15),
            rx.cond(
                FlowState.gate_approvals_history.length() > 0,
                rx.vstack(
                    rx.foreach(FlowState.gate_approvals_history, render_gate_history_item),
                    spacing="2",
                    width="100%",
                ),
                rx.box(
                    rx.hstack(
                        rx.icon("info", size=14, color="#52657a"),
                        rx.text("Aún no se han registrado aprobaciones de gate en este proyecto. Al avanzar secuencialmente de fase, se generará la bitácora inmutable de auditoría.", size="1", color="#52657a"),
                        spacing="2",
                        align="center",
                    ),
                    padding="3",
                    background_color="#ffffff",
                    border="1px dashed #d9e2ec",
                    border_radius="8px",
                    width="100%",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        padding="4",
        background_color="#f8fafc",
        border="1px solid #d9e2ec",
        border_radius="10px",
        width="100%",
    )


def governance_view() -> rx.Component:
    """Governance & Methodology View (F01)"""
    return rx.box(
        phase_gate_approval_modal(),
        phase_blocked_modal(),
        rx.vstack(
            # Header
            rx.hstack(
                rx.hstack(
                    rx.icon("layers", size=24, color="#1e5a9a"),
                    rx.vstack(
                        rx.text("Gobernanza & Metodología de 7 Fases", size="4", weight="bold", color="#17283c"),
                        rx.text("Ciclo de vida corporativo de procesos, control de entregables y auditoría de calidad", size="2", color="#52657a"),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        rx.hstack(
                            rx.icon(rx.cond(FlowState.is_audit_outdated, "refresh-cw", "shield-check"), size=15),
                            rx.text(rx.cond(FlowState.is_audit_outdated, " Re-Auditar Proceso (Desactualizado)", " Auditar Proceso con IA")),
                            align="center",
                            spacing="1",
                        ),
                        on_click=FlowState.open_audit_modal,
                        color_scheme=rx.cond(FlowState.is_audit_outdated, "amber", "indigo"),
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
                border_bottom="1px solid #d9e2ec",
                align="center",
            ),

            # Scrollable Content: 7 Phases Cards + Gate History Section
            rx.box(
                rx.vstack(
                    rx.vstack(
                        *[render_phase_card(p) for p in PHASE_LIST],
                        width="100%",
                        spacing="3",
                    ),
                    render_gate_history_section(),
                    width="100%",
                    spacing="4",
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
        background_color="#f3f6fa",
    )
