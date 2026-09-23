#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Login View for TEMIS Web Flow
Refined enterprise SaaS authentication screen with email & password access.
"""

import reflex as rx
from temis_web.state import FlowState


def login_view() -> rx.Component:
    """The enterprise login page component for TEMIS Work OS in dark executive slate."""
    return rx.box(
        # Subtle ambient electric blue glows
        rx.box(
            style={
                "position": "absolute",
                "width": "400px",
                "height": "400px",
                "background_color": "#3b82f6",
                "filter": "blur(180px)",
                "opacity": "0.12",
                "top": "15%",
                "left": "25%",
                "z_index": "0"
            }
        ),
        rx.box(
            style={
                "position": "absolute",
                "width": "400px",
                "height": "400px",
                "background_color": "#0ea5e9",
                "filter": "blur(180px)",
                "opacity": "0.10",
                "bottom": "15%",
                "right": "25%",
                "z_index": "0"
            }
        ),
        
        # Centered Login Card
        rx.center(
            rx.vstack(
                rx.vstack(
                    # TEMIS Header & Logo
                    rx.vstack(
                        rx.hstack(
                            rx.icon("network", size=32, color="#38bdf8"),
                            rx.text("TEMIS", size="8", weight="bold", color="#f8fafc"),
                            align="center",
                            spacing="2",
                        ),
                        rx.text(
                            "Work OS & Gobernanza de Procesos Corporativos",
                            size="2",
                            weight="medium",
                            color="#94a3b8",
                            text_align="center"
                        ),
                        rx.badge("TEMIS v2.0 · Acceso Corporativo", color_scheme="blue", variant="soft", size="1"),
                        spacing="2",
                        align="center",
                        margin_bottom="16px",
                    ),

                    # Error Alert Display
                    rx.cond(
                        FlowState.login_error_message != "",
                        rx.callout.root(
                            rx.callout.icon(rx.icon("triangle-alert", size=16)),
                            rx.callout.text(FlowState.login_error_message, size="1"),
                            color_scheme="ruby",
                            role="alert",
                            width="100%",
                            margin_bottom="12px",
                        )
                    ),

                    # Login Form
                    rx.vstack(
                        # Email Input
                        rx.vstack(
                            rx.hstack(
                                rx.icon("mail", size=14, color="#94a3b8"),
                                rx.text("Correo Electrónico Institucional", size="1", weight="bold", color="#94a3b8"),
                                align="center",
                                spacing="1"
                            ),
                            rx.input(
                                placeholder="mxjhurtado@maxillc.com",
                                value=FlowState.login_email,
                                on_change=FlowState.set_login_email,
                                type="email",
                                width="100%",
                                size="2",
                                variant="surface",
                                radius="medium",
                            ),
                            align_items="start",
                            width="100%",
                            spacing="1",
                        ),
                        
                        # Password Input
                        rx.vstack(
                            rx.hstack(
                                rx.icon("lock", size=14, color="#94a3b8"),
                                rx.text("Contraseña de Acceso", size="1", weight="bold", color="#94a3b8"),
                                align="center",
                                spacing="1"
                            ),
                            rx.input(
                                placeholder="••••••••••••",
                                value=FlowState.login_password,
                                on_change=FlowState.set_login_password,
                                type="password",
                                width="100%",
                                size="2",
                                variant="surface",
                                radius="medium",
                            ),
                            align_items="start",
                            width="100%",
                            spacing="1",
                        ),

                        # Submit Button
                        rx.button(
                            rx.hstack(
                                rx.icon("log-in", size=16),
                                rx.text("Iniciar Sesión en TEMIS", weight="bold"),
                                align="center",
                                spacing="2"
                            ),
                            on_click=FlowState.handle_login,
                            loading=FlowState.is_logging_in,
                            width="100%",
                            size="3",
                            color_scheme="blue",
                            radius="medium",
                            margin_top="12px",
                            box_shadow="0 4px 14px 0 rgba(59, 130, 246, 0.35)",
                        ),
                        
                        # Help footnote
                        rx.hstack(
                            rx.icon("shield-check", size=13, color="#10b981"),
                            rx.text(
                                "Autenticación centralizada y control de roles RBAC",
                                size="1",
                                color="#94a3b8"
                            ),
                            align="center",
                            spacing="1",
                            margin_top="16px"
                        ),
                        
                        spacing="3",
                        width="100%",
                    ),
                    
                    padding="36px",
                    width="420px",
                    background_color="#131b2e",
                    border="1px solid #1e293b",
                    border_radius="16px",
                    box_shadow="0 25px 50px -12px rgba(0, 0, 0, 0.5)",
                ),
                align="center",
                width="100%",
            ),
            height="100vh",
            width="100vw",
            z_index="10"
        ),
        background_color="#0b0f17",
        width="100vw",
        height="100vh",
        position="relative",
        overflow="hidden",
        font_family="Inter, sans-serif",
    )
