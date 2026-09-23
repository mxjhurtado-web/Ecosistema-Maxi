#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Node Edit Modal Component for TEMIS Web Flow
Dialog to edit node properties (label, attached system, channel, activity number)
Styled in Executive Light Slate Theme (WCAG 2.2 AA compliant).
"""

import reflex as rx
from temis_web.state import FlowState


def edit_node_modal() -> rx.Component:
    """Dialog modal for editing node details in light slate theme"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Propiedades del Nodo", size="4", weight="bold", color="#17283c"),
            rx.dialog.description("Edita la información y símbolos del nodo ", FlowState.modal_node_id, ":", size="2", color="#52657a"),
            rx.vstack(
                # Label field
                rx.vstack(
                    rx.text("Texto / Verbo en Infinitivo:", size="2", weight="bold", color="#52657a"),
                    rx.input(
                        value=FlowState.modal_label,
                        on_change=FlowState.set_modal_label,
                        placeholder="Ej: Verificar solicitud",
                        width="100%",
                        variant="surface",
                    ),
                    width="100%",
                    spacing="1",
                ),
                # System field
                rx.vstack(
                    rx.text("Sistema Involucrado (ej: Chronos, Freshdesk, SAP):", size="2", weight="bold", color="#52657a"),
                    rx.input(
                        value=FlowState.modal_system,
                        on_change=FlowState.set_modal_system,
                        placeholder="Ej: Chronos",
                        width="100%",
                        variant="surface",
                    ),
                    width="100%",
                    spacing="1",
                ),
                # Channel field
                rx.vstack(
                    rx.text("Canal de Comunicación (ej: WhatsApp, Freshdesk, Bria):", size="2", weight="bold", color="#52657a"),
                    rx.input(
                        value=FlowState.modal_channel,
                        on_change=FlowState.set_modal_channel,
                        placeholder="Ej: WhatsApp",
                        width="100%",
                        variant="surface",
                    ),
                    width="100%",
                    spacing="1",
                ),
                # Activity number field
                rx.vstack(
                    rx.text("Número de Actividad (Happy Path):", size="2", weight="bold", color="#52657a"),
                    rx.input(
                        value=FlowState.modal_activity_num,
                        on_change=FlowState.set_modal_activity_num,
                        placeholder="Ej: 1",
                        type="number",
                        width="100%",
                        variant="surface",
                    ),
                    width="100%",
                    spacing="1",
                ),
                spacing="3",
                padding_y="3",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancelar", color_scheme="gray", variant="soft", on_click=FlowState.close_node_edit_modal),
                ),
                rx.dialog.close(
                    rx.button("Guardar Cambios", color_scheme="blue", on_click=FlowState.save_node_edit_modal),
                ),
                spacing="3",
                justify="end",
                margin_top="3",
            ),
            width="460px",
            border_radius="xl",
            padding="5",
            background_color="#ffffff",
            border="1px solid #d9e2ec",
        ),
        open=FlowState.show_modal,
        on_open_change=FlowState.close_node_edit_modal,
    )
