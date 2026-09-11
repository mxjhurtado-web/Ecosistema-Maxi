#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SIPOC Matrix Component for TEMIS Web Flow
Six Sigma Tabular Process Mapping with Bidirectional Synchronization to Flowchart Canvas
"""

import reflex as rx
from temis_web.state import FlowState


def render_sipoc_row(row: rx.Var[dict]) -> rx.Component:
    """Render a single interactive SIPOC step row"""
    return rx.table.row(
        # Step Number (1.0, 2.0...)
        rx.table.cell(
            rx.badge(row["step_num"], color_scheme="blue", variant="solid", size="1"),
            align="center",
            width="60px",
        ),
        # S: Suppliers / Proveedores
        rx.table.cell(
            rx.input(
                value=row["provider"],
                on_change=lambda val: FlowState.update_sipoc_provider(row["id"], val),
                size="1",
                variant="soft",
                radius="small",
                placeholder="ej. Usuario / Cliente",
                width="100%",
            ),
            width="17%",
        ),
        # I: Inputs / Entradas
        rx.table.cell(
            rx.input(
                value=row["input"],
                on_change=lambda val: FlowState.update_sipoc_input(row["id"], val),
                size="1",
                variant="soft",
                radius="small",
                placeholder="ej. Folio vía WhatsApp",
                width="100%",
            ),
            width="17%",
        ),
        # P: Process / Proceso (1.0..N)
        rx.table.cell(
            rx.input(
                value=row["step"],
                on_change=lambda val: FlowState.update_sipoc_step(row["id"], val),
                size="1",
                variant="surface",
                radius="small",
                placeholder="ej. 1.0 Consulta en Chronos",
                width="100%",
            ),
            width="22%",
        ),
        # O: Outputs / Salidas
        rx.table.cell(
            rx.input(
                value=row["output"],
                on_change=lambda val: FlowState.update_sipoc_output(row["id"], val),
                size="1",
                variant="soft",
                radius="small",
                placeholder="ej. Estatus confirmado",
                width="100%",
            ),
            width="17%",
        ),
        # C: Customer / Cliente
        rx.table.cell(
            rx.input(
                value=row["customer"],
                on_change=lambda val: FlowState.update_sipoc_customer(row["id"], val),
                size="1",
                variant="soft",
                radius="small",
                placeholder="ej. Agente / Chronos",
                width="100%",
            ),
            width="14%",
        ),
        # Actions: Delete row
        rx.table.cell(
            rx.icon_button(
                rx.icon("trash-2", size=13),
                on_click=lambda: FlowState.remove_sipoc_row(row["id"]),
                color_scheme="ruby",
                variant="ghost",
                size="1",
            ),
            align="center",
            width="50px",
        ),
    )


def sipoc_matrix() -> rx.Component:
    """Main SIPOC Matrix Table View with Quick Actions & Flow Generation"""
    return rx.box(
        rx.vstack(
            # Top Toolbar & Pipeline Dispatches
            rx.hstack(
                rx.hstack(
                    rx.icon("table-properties", size=24, color="#0284c7"),
                    rx.vstack(
                        rx.text("Matriz SIPOC Six Sigma", size="4", weight="bold", color="#0f172a"),
                        rx.text("Mapeo estructurado: Proveedores ➔ Entradas ➔ Proceso ➔ Salidas ➔ Clientes", size="2", color="#64748b"),
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
                    ),
                    spacing="2",
                ),
                width="100%",
                padding_y="3",
                border_bottom="1px solid #e2e8f0",
                align="center",
            ),

            # SIPOC Interactive Table Container
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("#", width="60px", align="center"),
                            rx.table.column_header_cell("S · PROVEEDORES (Suppliers)", width="17%"),
                            rx.table.column_header_cell("I · ENTRADAS (Inputs)", width="17%"),
                            rx.table.column_header_cell("P · PROCESO (Process 1.0..N)", width="22%"),
                            rx.table.column_header_cell("O · SALIDAS (Outputs)", width="17%"),
                            rx.table.column_header_cell("C · CLIENTES (Customers)", width="14%"),
                            rx.table.column_header_cell("", width="50px", align="center"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(FlowState.sipoc_rows, render_sipoc_row),
                    ),
                    width="100%",
                    variant="surface",
                    size="2",
                ),
                width="100%",
                background_color="#ffffff",
                border="1px solid #e2e8f0",
                border_radius="8px",
                padding="3",
                box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                max_height="calc(100vh - 290px)",
                overflow_y="auto",
            ),

            # Bottom Customer Requirements Banner
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("circle-check", size=16, color="#d97706"),
                        rx.text("Requisitos del Cliente & Notas de Calidad (Customer Requirements)", size="2", weight="bold", color="#92400e"),
                        align="center",
                        spacing="2",
                    ),
                    rx.input(
                        value=FlowState.customer_requirements,
                        on_change=FlowState.set_customer_requirements,
                        placeholder="ej. SLA de respuesta < 5 min, trazabilidad en Chronos y confirmación de satisfacción...",
                        width="100%",
                        size="2",
                        variant="soft",
                        radius="medium",
                    ),
                    width="100%",
                    spacing="1",
                ),
                width="100%",
                background_color="#fffbeb",
                border="1px solid #fde68a",
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
        background_color="#f8fafc",
    )
