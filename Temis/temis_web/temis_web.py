#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Application for TEMIS Web Flow (Reflex)
Full-Stack Web App for Process Governance & Official Flowchart Diagrams
"""

import reflex as rx

from temis_web.state import FlowState
from temis_web.components.workspace_sidebar import workspace_sidebar
from temis_web.components.header import header
from temis_web.components.left_dock import left_dock
from temis_web.components.flowchart_canvas import flowchart_canvas
from temis_web.components.property_inspector import property_inspector
from temis_web.components.bottom_bar import bottom_bar
from temis_web.components.project_modal import recent_projects_modal
from temis_web.components.connect_modal import connect_modal
from temis_web.components.audit_modal import audit_modal
from temis_web.components.project_charter import project_charter
from temis_web.components.narrative_analysis_view import narrative_analysis_view
from temis_web.components.diff_merge_modal import diff_merge_modal
from temis_web.components.work_plan_view import work_plan_view
from temis_web.components.sipoc_matrix import sipoc_matrix
from temis_web.components.governance_view import governance_view
from temis_web.components.project_hub import project_hub
from temis_web.components.login_view import login_view
from temis_web.components.user_management_view import user_management_view
from temis_web.components.toast_notification import toast_notification


def workspace_view() -> rx.Component:
    """Level 2 Workspace with lateral navigation sidebar and 6 modular views (H04 Responsive)"""
    return rx.box(
        recent_projects_modal(),
        connect_modal(),
        audit_modal(),
        diff_merge_modal(),
        rx.vstack(
            header(),
            rx.hstack(
                workspace_sidebar(),
                rx.box(
                    rx.match(
                        FlowState.active_view,
                        ("charter", project_charter()),
                        ("narrative", narrative_analysis_view()),
                        ("plan", work_plan_view()),
                        ("sipoc", sipoc_matrix()),
                        ("governance", governance_view()),
                        # Default: Interactive Canvas Flowchart View (BPMN)
                        rx.vstack(
                            rx.hstack(
                                left_dock(),
                                flowchart_canvas(),
                                property_inspector(),
                                width="100%",
                                max_width="100%",
                                flex="1",
                                height="calc(100vh - 92px)",
                                overflow="hidden",
                                spacing="0",
                            ),
                            bottom_bar(),
                            width="100%",
                            height="calc(100vh - 54px)",
                            spacing="0",
                        ),
                    ),
                    flex="1",
                    width="100%",
                    max_width="100vw",
                    height="calc(100vh - 54px)",
                    overflow="hidden",
                ),
                width="100%",
                max_width="100vw",
                height="calc(100vh - 54px)",
                overflow="hidden",
                spacing="0",
            ),
            width="100%",
            max_width="100vw",
            height="100vh",
            overflow="hidden",
            spacing="0",
        ),
        width="100%",
        max_width="100vw",
        height="100vh",
        overflow="hidden",
        background_color="#f3f6fa",
        font_family="Inter, sans-serif",
    )


def hub_view() -> rx.Component:
    """Level 1 Hub: Portfolio or User Management based on hub_active_subview"""
    return rx.cond(
        FlowState.hub_active_subview == "users",
        user_management_view(),
        project_hub(),
    )


def index() -> rx.Component:
    """Main modern SaaS layout of TEMIS: Login, Hub (Portfolio/Users) or Workspace"""
    return rx.box(
        toast_notification(),
        rx.cond(
            ~FlowState.is_authenticated,
            login_view(),
            rx.cond(
                FlowState.active_mode == "hub",
                hub_view(),
                workspace_view(),
            ),
        ),
        width="100%",
        height="100vh",
        background_color="#f3f6fa",
        font_family="Inter, sans-serif",
    )


app = rx.App(
    stylesheets=["style.css"],
)

app.add_page(index, title="TEMIS Web Flow - Work OS & Gobernanza de Procesos")
