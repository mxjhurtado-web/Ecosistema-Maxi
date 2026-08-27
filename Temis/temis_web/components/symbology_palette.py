#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Symbology Palette Component for TEMIS Web Flow
Implements the 21 official symbols from the Template & Symbology PDF
"""

import reflex as rx
from temis_web.state import FlowState

SYMBOLS_CATALOG = [
    # Proceso Base
    {"type": "node_start", "label": "Inicio Proceso", "icon": "play-circle", "color": "#2563eb", "bg": "#dbeafe", "category": "Base"},
    {"type": "node_end", "label": "Fin Proceso", "icon": "stop-circle", "color": "#475569", "bg": "#f1f5f9", "category": "Base"},
    {"type": "node_io", "label": "Entrada / Salida", "icon": "arrow-left-right", "color": "#0284c7", "bg": "#e0f2fe", "category": "Base"},
    {"type": "node_activity", "label": "Actividad (Infinitivo)", "icon": "check-square", "color": "#16a34a", "bg": "#dcfce7", "category": "Base"},
    {"type": "node_decision", "label": "Decisión (¿Es válido?)", "icon": "help-circle", "color": "#d97706", "bg": "#fef3c7", "category": "Base"},
    
    # Compuertas & Tiempo
    {"type": "node_split_and", "label": "Símbolo Y (Paralelo ⊗)", "icon": "git-merge", "color": "#7c3aed", "bg": "#ede9fe", "category": "Compuertas"},
    {"type": "node_split_or", "label": "Símbolo O (Exclusivo ⊕)", "icon": "git-branch", "color": "#c026d3", "bg": "#fae8ff", "category": "Compuertas"},
    {"type": "node_delay", "label": "Demora (ej. 5 min)", "icon": "clock", "color": "#ea580c", "bg": "#ffedd5", "category": "Compuertas"},
    
    # Artefactos & Datos
    {"type": "node_document", "label": "Documento único", "icon": "file-text", "color": "#0891b2", "bg": "#cff4fc", "category": "Artefactos"},
    {"type": "node_multi_document", "label": "Varios Documentos", "icon": "files", "color": "#0891b2", "bg": "#cff4fc", "category": "Artefactos"},
    {"type": "node_subprocess", "label": "Subproceso", "icon": "boxes", "color": "#4f46e5", "bg": "#e0e7ff", "category": "Artefactos"},
    {"type": "node_database", "label": "Base de Datos", "icon": "database", "color": "#0d9488", "bg": "#ccfbf1", "category": "Artefactos"},
    {"type": "node_screen", "label": "Pantalla / Menú", "icon": "monitor", "color": "#2563eb", "bg": "#dbeafe", "category": "Artefactos"},
    
    # Sistemas & Canales Oficiales
    {"type": "node_system", "label": "Sistema (Chronos/ERP)", "icon": "cpu", "color": "#059669", "bg": "#d1fae5", "category": "Canales"},
    {"type": "channel_whatsapp", "label": "Canal WhatsApp", "icon": "message-circle", "color": "#16a34a", "bg": "#dcfce7", "category": "Canales"},
    {"type": "channel_freshdesk", "label": "Canal Freshdesk", "icon": "headphones", "color": "#0284c7", "bg": "#e0f2fe", "category": "Canales"},
    {"type": "channel_bria", "label": "Canal Bria", "icon": "phone-call", "color": "#ea580c", "bg": "#ffedd5", "category": "Canales"},
    {"type": "node_automation", "label": "Automatización (Bot)", "icon": "bot", "color": "#9333ea", "bg": "#f3e8ff", "category": "Canales"},
    
    # Conectores & Notas
    {"type": "node_connector", "label": "Conector Actividad (A)", "icon": "circle-dot", "color": "#64748b", "bg": "#f8fafc", "category": "Conectores"},
    {"type": "node_page_connector", "label": "Conector Página (1)", "icon": "file-symlink", "color": "#64748b", "bg": "#f8fafc", "category": "Conectores"},
    {"type": "node_note", "label": "Nota explicativa", "icon": "sticky-note", "color": "#ca8a04", "bg": "#fef9c3", "category": "Conectores"},
]


def palette_button(item: dict) -> rx.Component:
    """Button for dragging or adding a symbol to canvas"""
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(item["icon"], size=16, color=item["color"]),
                background_color=item["bg"],
                padding="2",
                border_radius="md",
            ),
            rx.text(item["label"], size="2", weight="medium", color="#334155"),
            spacing="2",
            align="center",
        ),
        padding="2",
        border_radius="lg",
        border="1px solid #e2e8f0",
        background_color="#ffffff",
        cursor="pointer",
        on_click=lambda: FlowState.add_node_by_type(item["type"], item["label"]),
        _hover={"border_color": item["color"], "box_shadow": "0 2px 4px rgba(0,0,0,0.05)"},
        width="100%",
    )


def symbology_palette() -> rx.Component:
    """Right palette bar containing official PDF symbols"""
    return rx.vstack(
        rx.hstack(
            rx.icon("shapes", size=18, color="#3b82f6"),
            rx.heading("SIMBOLOGÍA OFICIAL", size="3", weight="bold", color="#1e293b"),
            spacing="2",
            align="center",
        ),
        rx.text("Haz clic en cualquier símbolo para agregarlo al lienzo de flujo:", size="1", color="#64748b"),
        rx.scroll_area(
            rx.vstack(
                *[palette_button(sym) for sym in SYMBOLS_CATALOG],
                spacing="2",
                width="100%",
            ),
            type="hover",
            scrollbars="vertical",
            style={"height": "calc(100vh - 150px)"},
        ),
        width="260px",
        height="calc(100vh - 65px)",
        background_color="#ffffff",
        border_left="1px solid #e2e8f0",
        padding="3",
        spacing="3",
    )
