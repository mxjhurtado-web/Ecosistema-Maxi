#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Import Modal Component for TEMIS Web Flow
Dialog to upload JSON diagrams or TEMIS project packages
"""

import reflex as rx
from temis_web.state import FlowState


def import_modal() -> rx.Component:
    """Dialog modal for uploading and importing JSON diagrams"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Importar Diagrama o Proyecto", size="4", weight="bold"),
            rx.dialog.description(
                "Selecciona o arrastra un archivo de diagrama (.json) o paquete de proyecto (.temis.json):",
                size="2",
                color="#64748b",
            ),
            rx.vstack(
                rx.upload(
                    rx.vstack(
                        rx.icon("upload-cloud", size=36, color="#3b82f6"),
                        rx.text("Haz clic o arrastra tu archivo JSON aquí", size="2", weight="bold", color="#334155"),
                        rx.text("Formatos permitidos: .json, .temis.json", size="1", color="#94a3b8"),
                        align="center",
                        spacing="2",
                        padding="4",
                    ),
                    id="upload_diagram",
                    on_drop=FlowState.handle_file_upload,
                    accept={"application/json": [".json", ".temis.json"]},
                    max_files=1,
                    border="2px dashed #cbd5e1",
                    border_radius="xl",
                    background_color="#f8fafc",
                    width="100%",
                    cursor="pointer",
                ),
                spacing="3",
                padding_y="4",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancelar", color_scheme="gray", variant="soft", on_click=FlowState.close_import_modal),
                ),
                justify="end",
                margin_top="2",
            ),
            width="460px",
            border_radius="xl",
            padding="5",
        ),
        open=FlowState.show_import_modal,
        on_open_change=FlowState.close_import_modal,
    )
