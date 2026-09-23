#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SIPOC Matrix Component for TEMIS Web Flow
Six Sigma Tabular Process Mapping with Bidirectional Synchronization to Flowchart Canvas
Styled in Executive Light Slate Theme with expansive column widths, AI Proposal Review Modal, and smooth horizontal scroll.
"""

import reflex as rx
from temis_web.state import FlowState


def sipoc_ai_proposal_modal() -> rx.Component:
    """Modal dialog for reviewing and accepting/discarding AI-generated SIPOC rows"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("sparkles", size=20, color="#1e5a9a"),
                    rx.dialog.title("Propuesta de Matriz SIPOC generada por IA", size="3", weight="bold", color="#17283c"),
                    align="center",
                    spacing="2",
                ),
                rx.dialog.description(
                    "La Inteligencia Artificial ha propuesto la siguiente estructura para su proceso. Revise los pasos antes de confirmar la actualización:",
                    size="2",
                    color="#52657a",
                ),
                # Table Preview of Proposal
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("#", width="45px", align="center"),
                                rx.table.column_header_cell("S · PROVEEDORES", width="150px"),
                                rx.table.column_header_cell("I · ENTRADAS", width="150px"),
                                rx.table.column_header_cell("P · PROCESO", width="240px"),
                                rx.table.column_header_cell("O · SALIDAS", width="150px"),
                                rx.table.column_header_cell("C · CLIENTES", width="140px"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                FlowState.ai_sipoc_proposal_rows,
                                lambda r: rx.table.row(
                                    rx.table.cell(rx.badge(r["step_num"], color_scheme="blue", variant="solid", size="1"), align="center"),
                                    rx.table.cell(rx.text(r["provider"], size="1", color="#17283c")),
                                    rx.table.cell(rx.text(r["input"], size="1", color="#17283c")),
                                    rx.table.cell(rx.text(r["step"], size="1", weight="bold", color="#17283c")),
                                    rx.table.cell(rx.text(r["output"], size="1", color="#17283c")),
                                    rx.table.cell(rx.text(r["customer"], size="1", color="#17283c")),
                                ),
                            ),
                        ),
                        width="100%",
                        variant="surface",
                        size="1",
                    ),
                    max_height="320px",
                    overflow_y="auto",
                    overflow_x="auto",
                    border="1px solid #d9e2ec",
                    border_radius="md",
                    width="100%",
                    background_color="#ffffff",
                ),
                # Action Buttons
                rx.hstack(
                    rx.button(
                        "Descartar propuesta",
                        on_click=FlowState.cancel_sipoc_ai_proposal,
                        color_scheme="gray",
                        variant="soft",
                        size="2",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(rx.icon("plus", size=14), rx.text("Añadir al final")),
                        on_click=lambda: FlowState.apply_sipoc_ai_proposal("append"),
                        color_scheme="green",
                        variant="soft",
                        size="2",
                    ),
                    rx.button(
                        rx.hstack(rx.icon("check", size=14), rx.text("Reemplazar matriz")),
                        on_click=lambda: FlowState.apply_sipoc_ai_proposal("replace"),
                        color_scheme="blue",
                        variant="solid",
                        size="2",
                    ),
                    width="100%",
                    spacing="2",
                    padding_top="3",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="850px",
            background_color="#ffffff",
            border="1px solid #d9e2ec",
            border_radius="xl",
            padding="5",
            box_shadow="0 20px 25px -5px rgba(0, 0, 0, 0.1)",
        ),
        open=FlowState.show_sipoc_ai_modal,
    )


def render_sipoc_row(row: rx.Var[dict]) -> rx.Component:
    """Render a single interactive SIPOC step row with generous column widths and multiline process description"""
    return rx.table.row(
        # Step Number (1.0, 2.0...)
        rx.table.cell(
            rx.badge(row["step_num"], color_scheme="blue", variant="solid", size="1"),
            align="center",
            width="50px",
        ),
        # S: Suppliers / Proveedores
        rx.table.cell(
            rx.input(
                value=row["provider"],
                on_change=lambda val: FlowState.update_sipoc_provider(row["id"], val),
                size="1",
                variant="surface",
                radius="small",
                placeholder="ej. Usuario / Cliente",
                width="100%",
            ),
            width="180px",
            min_width="160px",
        ),
        # I: Inputs / Entradas
        rx.table.cell(
            rx.input(
                value=row["input"],
                on_change=lambda val: FlowState.update_sipoc_input(row["id"], val),
                size="1",
                variant="surface",
                radius="small",
                placeholder="ej. Folio vía WhatsApp",
                width="100%",
            ),
            width="180px",
            min_width="160px",
        ),
        # P: Process / Proceso (1.0..N) - Multiline Text Area to prevent text cutoffs
        rx.table.cell(
            rx.text_area(
                value=row["step"],
                on_change=lambda val: FlowState.update_sipoc_step(row["id"], val),
                size="1",
                variant="surface",
                radius="small",
                placeholder="ej. 1.0 Consulta de estatus en base de datos Chronos",
                width="100%",
                rows="2",
            ),
            width="280px",
            min_width="220px",
        ),
        # O: Outputs / Salidas
        rx.table.cell(
            rx.input(
                value=row["output"],
                on_change=lambda val: FlowState.update_sipoc_output(row["id"], val),
                size="1",
                variant="surface",
                radius="small",
                placeholder="ej. Estatus confirmado",
                width="100%",
            ),
            width="180px",
            min_width="160px",
        ),
        # C: Customer / Cliente
        rx.table.cell(
            rx.input(
                value=row["customer"],
                on_change=lambda val: FlowState.update_sipoc_customer(row["id"], val),
                size="1",
                variant="surface",
                radius="small",
                placeholder="ej. Agente / Chronos",
                width="100%",
            ),
            width="160px",
            min_width="140px",
        ),
        # Actions: Delete row with accessible aria-label and tooltip
        rx.table.cell(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("trash-2", size=13),
                    on_click=lambda: FlowState.remove_sipoc_row(row["id"]),
                    color_scheme="ruby",
                    variant="ghost",
                    size="1",
                    aria_label="Eliminar paso",
                ),
                content="Eliminar paso",
            ),
            align="center",
            width="50px",
        ),
    )


def sipoc_matrix() -> rx.Component:
    """Main SIPOC Matrix Table View with Quick Actions, AI Proposal Modal & Non-Destructive Flow Sync"""
    return rx.box(
        sipoc_ai_proposal_modal(),
        rx.vstack(
            # Top Toolbar & Pipeline Dispatches
            rx.hstack(
                rx.hstack(
                    rx.icon("table-properties", size=24, color="#1e5a9a"),
                    rx.vstack(
                        rx.hstack(
                            rx.text("Matriz SIPOC Six Sigma", size="4", weight="bold", color="#17283c"),
                            rx.cond(
                                FlowState.is_sipoc_flow_outdated,
                                rx.badge("Diagrama desactualizado", color_scheme="amber", variant="soft", size="1"),
                            ),
                            align="center",
                            spacing="2",
                        ),
                        rx.text("Mapeo estructurado: Proveedores -> Entradas -> Proceso -> Salidas -> Clientes", size="2", color="#52657a"),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        rx.icon("zap", size=15),
                        " Generar Diagrama de Flujo",
                        on_click=FlowState.sync_sipoc_to_flow,
                        color_scheme="blue",
                        size="2",
                        radius="medium",
                        title="Generar o actualizar diagrama en la pestaña 'Flujo SIPOC'",
                    ),
                    rx.button(
                        rx.icon("sparkles", size=15),
                        " Completar con IA",
                        on_click=FlowState.complete_sipoc_with_ai,
                        loading=FlowState.is_completing_sipoc,
                        color_scheme="indigo",
                        variant="soft",
                        size="2",
                        radius="medium",
                        title="Autocompletar pasos sugeridos con Gemini AI",
                    ),
                    rx.button(
                        rx.icon("plus", size=15),
                        " Agregar Paso",
                        on_click=FlowState.add_sipoc_row,
                        color_scheme="green",
                        variant="soft",
                        size="2",
                        radius="medium",
                    ),
                    rx.button(
                        rx.icon("file-spreadsheet", size=15),
                        " Exportar Excel (.xlsx)",
                        on_click=FlowState.export_sipoc_excel,
                        color_scheme="gray",
                        variant="soft",
                        size="2",
                        radius="medium",
                        title="Descargar plantilla Excel Six Sigma",
                    ),
                    spacing="2",
                    wrap="wrap",
                ),
                width="100%",
                padding_y="3",
                border_bottom="1px solid #d9e2ec",
                align="center",
                wrap="wrap",
            ),

            # Outdated Flow Warning Banner (F06)
            rx.cond(
                FlowState.is_sipoc_flow_outdated,
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.icon("refresh-cw", size=18, color="#b45309"),
                            padding="2",
                            background_color="#fef3c7",
                            border_radius="6px",
                        ),
                        rx.vstack(
                            rx.text("Diagrama desactualizado respecto a la Matriz SIPOC", size="2", weight="bold", color="#92400e"),
                            rx.text("Se detectaron modificaciones recientes en los pasos SIPOC. Sincroniza el diagrama para actualizar los bloques en el lienzo BPMN.", size="1", color="#78350f"),
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.hstack(
                                rx.icon("zap", size=14),
                                rx.text("Sincronizar Diagrama"),
                                align="center",
                                spacing="1",
                            ),
                            on_click=FlowState.sync_sipoc_to_flow,
                            color_scheme="amber",
                            variant="solid",
                            size="1",
                            radius="medium",
                        ),
                        width="100%",
                        align="center",
                        spacing="3",
                    ),
                    padding="3",
                    background_color="#fffbeb",
                    border="1px solid #fde68a",
                    border_radius="8px",
                    width="100%",
                ),
                rx.box(),
            ),

            # SIPOC Interactive Table Container (Self-contained horizontal scroll to prevent 1271px mobile blowout)
            rx.box(
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("#", width="50px", align="center"),
                                rx.table.column_header_cell("S · PROVEEDORES (Suppliers)", width="180px"),
                                rx.table.column_header_cell("I · ENTRADAS (Inputs)", width="180px"),
                                rx.table.column_header_cell("P · PROCESO (Process 1.0..N)", width="280px"),
                                rx.table.column_header_cell("O · SALIDAS (Outputs)", width="180px"),
                                rx.table.column_header_cell("C · CLIENTES (Customers)", width="160px"),
                                rx.table.column_header_cell("", width="50px", align="center"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(FlowState.sipoc_rows, render_sipoc_row),
                        ),
                        width="100%",
                        min_width="980px",
                        variant="surface",
                        size="2",
                    ),
                    overflow_x="auto",
                    width="100%",
                    max_width="100%",
                ),
                width="100%",
                max_width="100%",
                background_color="#ffffff",
                border="1px solid #d9e2ec",
                border_radius="10px",
                padding="3",
                box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                max_height="calc(100vh - 290px)",
                overflow_y="auto",
            ),

            # Bottom Customer Requirements Banner
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("circle-check", size=16, color="#107c41"),
                        rx.text("Requisitos del Cliente & Notas de Calidad (Customer Requirements)", size="2", weight="bold", color="#17283c"),
                        align="center",
                        spacing="2",
                    ),
                    rx.input(
                        value=FlowState.customer_requirements,
                        on_change=FlowState.set_customer_requirements,
                        placeholder="ej. SLA de respuesta < 5 min, trazabilidad en Chronos y confirmación de satisfacción...",
                        width="100%",
                        size="2",
                        variant="surface",
                        radius="medium",
                    ),
                    width="100%",
                    spacing="1",
                ),
                width="100%",
                background_color="#f8fafc",
                border="1px solid #d9e2ec",
                border_radius="8px",
                padding="3",
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
