#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Import Modal Component for TEMIS Web Flow
Dialog to upload JSON diagrams or TEMIS project packages
Styled in Executive Light Slate Theme (WCAG 2.2 AA compliant).
"""

import reflex as rx
from temis_web.state import FlowState


def import_modal() -> rx.Component:
    """Dialog modal for uploading and importing JSON diagrams in light slate theme"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Importar Diagrama o Proyecto", size="4", weight="bold", color="#17283c"),
            rx.dialog.description(
                "Selecciona o arrastra un archivo en formato PDF, JSON, CSV o paquete .temis.json:",
                size="2",
                color="#52657a",
            ),
            rx.vstack(
                rx.upload(
                    rx.vstack(
                        rx.icon("cloud-upload", size=36, color="#1e5a9a"),
                        rx.text("Haz clic o arrastra tu archivo PDF, JSON o CSV aquí", size="2", weight="bold", color="#17283c"),
                        rx.text("Formatos permitidos: .pdf, .json, .csv, .temis.json", size="1", color="#52657a"),
                        align="center",
                        spacing="2",
                        padding="4",
                    ),
                    id="upload_diagram",
                    on_drop=FlowState.handle_file_upload,
                    accept={
                        "application/pdf": [".pdf"],
                        "application/json": [".json", ".temis.json"],
                        "text/csv": [".csv"],
                    },
                    max_files=1,
                    border="2px dashed #d9e2ec",
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
            background_color="#ffffff",
            border="1px solid #d9e2ec",
        ),
        open=FlowState.show_import_modal,
        on_open_change=FlowState.close_import_modal,
    )
