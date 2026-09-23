#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
User Management View for TEMIS Web Flow
RBAC User Directory, Role Assignment, Project Assignment, Status Management and Privilege Matrix.
All emojis removed and replaced with professional Lucide SVG icons (WCAG 2.2 AA compliant).
"""

import reflex as rx
from temis_web.state import FlowState


def role_badge(role: str) -> rx.Component:
    """Helper to render styled role badges without emojis"""
    return rx.match(
        role,
        ("super_admin", rx.badge(rx.hstack(rx.icon("shield", size=11), rx.text("Super Admin"), align="center", spacing="1"), color_scheme="purple", variant="soft", size="1", radius="medium")),
        ("project_manager", rx.badge(rx.hstack(rx.icon("briefcase", size=11), rx.text("Dueño de Proyecto (PM)"), align="center", spacing="1"), color_scheme="blue", variant="soft", size="1", radius="medium")),
        ("analyst", rx.badge(rx.hstack(rx.icon("bar-chart-3", size=11), rx.text("Analista de Procesos"), align="center", spacing="1"), color_scheme="teal", variant="soft", size="1", radius="medium")),
        ("qa_auditor", rx.badge(rx.hstack(rx.icon("check-circle-2", size=11), rx.text("Auditor QA / Six Sigma"), align="center", spacing="1"), color_scheme="amber", variant="soft", size="1", radius="medium")),
        rx.badge(rx.hstack(rx.icon("user", size=11), rx.text("Colaborador (Invitado)"), align="center", spacing="1"), color_scheme="gray", variant="soft", size="1", radius="medium"),
    )


def status_badge(status: str) -> rx.Component:
    """Helper to render user account status badge"""
    return rx.cond(
        status == "active",
        rx.badge(rx.hstack(rx.icon("circle-dot", size=10, color="#16a34a"), rx.text("Activo"), align="center", spacing="1"), color_scheme="green", variant="soft", size="1", radius="medium"),
        rx.badge(rx.hstack(rx.icon("circle", size=10, color="#dc2626"), rx.text("Inactivo"), align="center", spacing="1"), color_scheme="ruby", variant="soft", size="1", radius="medium"),
    )


def user_assigned_projects_cell(u: dict) -> rx.Component:
    """Helper to render assigned projects column badges"""
    return rx.cond(
        (u["role"] == "super_admin") | u["assigned_projects"].contains("all"),
        rx.badge(
            rx.hstack(rx.icon("globe", size=11), rx.text("Acceso Global (Todos)"), align="center", spacing="1"),
            color_scheme="indigo",
            variant="surface",
            size="1",
            radius="medium",
        ),
        rx.cond(
            u["assigned_projects"].length() > 0,
            rx.hstack(
                rx.foreach(
                    u["assigned_projects"],
                    lambda p_code: rx.badge(
                        rx.hstack(rx.icon("folder", size=10), rx.text(p_code), align="center", spacing="1"),
                        color_scheme="blue",
                        variant="soft",
                        size="1",
                        radius="medium",
                    ),
                ),
                wrap="wrap",
                spacing="1",
                align="center",
            ),
            rx.badge("Sin proyectos", color_scheme="gray", variant="soft", size="1", radius="medium"),
        ),
    )


def user_row(u: dict) -> rx.Component:
    """Single row in the user management table"""
    return rx.table.row(
        # Avatar & Name
        rx.table.cell(
            rx.hstack(
                rx.avatar(
                    fallback=rx.cond(u["initials"] != "", u["initials"], "US"),
                    size="2",
                    radius="full",
                    color_scheme="indigo",
                    variant="soft"
                ),
                rx.vstack(
                    rx.text(u["name"], size="2", weight="bold", color="#0f172a"),
                    rx.text(u["email"], size="1", color="#64748b"),
                    spacing="0",
                    align_items="start"
                ),
                align="center",
                spacing="2"
            )
        ),
        # Role Badge
        rx.table.cell(role_badge(u["role"])),
        # Department
        rx.table.cell(
            rx.hstack(
                rx.icon("building", size=13, color="#94a3b8"),
                rx.text(u["department"], size="1", color="#475569"),
                align="center",
                spacing="1"
            )
        ),
        # Assigned Projects
        rx.table.cell(user_assigned_projects_cell(u)),
        # Status
        rx.table.cell(status_badge(u["status"])),
        # Last Login & Created
        rx.table.cell(
            rx.vstack(
                rx.text(u["last_login"], size="1", weight="medium", color="#334155"),
                rx.hstack(
                    rx.text("Registrado:", size="1", color="#94a3b8"),
                    rx.text(u["created_at"], size="1", color="#94a3b8"),
                    spacing="1"
                ),
                spacing="0",
                align_items="start"
            )
        ),
        # Actions
        rx.table.cell(
            rx.hstack(
                # Role Menu
                rx.menu.root(
                    rx.menu.trigger(
                        rx.button(
                            rx.hstack(
                                rx.icon("user-cog", size=13),
                                rx.text("Rol"),
                                rx.icon("chevron-down", size=12),
                                align="center",
                                spacing="1",
                            ),
                            variant="soft",
                            color_scheme="gray",
                            size="1",
                            radius="medium"
                        )
                    ),
                    rx.menu.content(
                        rx.menu.item("Super Admin", on_click=lambda: FlowState.update_user_role_action(u["email"], "super_admin")),
                        rx.menu.item("Dueño de Proyecto (PM)", on_click=lambda: FlowState.update_user_role_action(u["email"], "project_manager")),
                        rx.menu.item("Analista de Procesos", on_click=lambda: FlowState.update_user_role_action(u["email"], "analyst")),
                        rx.menu.item("Auditor QA / Six Sigma", on_click=lambda: FlowState.update_user_role_action(u["email"], "qa_auditor")),
                        rx.menu.item("Colaborador (Invitado)", on_click=lambda: FlowState.update_user_role_action(u["email"], "collaborator")),
                    )
                ),
                # Assign Projects Button
                rx.button(
                    rx.hstack(
                        rx.icon("folder-git-2", size=13),
                        rx.text("Proyectos"),
                        align="center",
                        spacing="1",
                    ),
                    on_click=lambda: FlowState.open_assign_projects_modal(u["email"]),
                    variant="soft",
                    color_scheme="blue",
                    size="1",
                    radius="medium",
                    title="Asignar proyectos al usuario",
                ),
                rx.cond(
                    u["email"] == FlowState.user_email,
                    rx.badge(
                        "Sesión Actual",
                        color_scheme="indigo",
                        variant="soft",
                        size="1",
                        radius="medium",
                        title="Tu cuenta actual no puede ser desactivada ni eliminada"
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon("power", size=13),
                            on_click=lambda: FlowState.toggle_user_status_action(u["email"]),
                            variant="soft",
                            color_scheme="amber",
                            size="1",
                            radius="medium",
                            title="Activar / Desactivar acceso"
                        ),
                        rx.button(
                            rx.icon("trash-2", size=13),
                            on_click=lambda: FlowState.delete_user_action(u["email"]),
                            variant="soft",
                            color_scheme="ruby",
                            size="1",
                            radius="medium",
                            title="Eliminar usuario"
                        ),
                        spacing="1",
                        align="center"
                    )
                ),
                align="center",
                spacing="1"
            )
        ),
        style={"_hover": {"background_color": "#f8fafc"}}
    )


def assign_projects_modal() -> rx.Component:
    """Modal dialog to assign specific projects or global access to a user"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.icon("folder-git-2", size=22, color="#1d4ed8"),
                        padding="2",
                        background_color="#eff6ff",
                        border_radius="8px",
                    ),
                    rx.vstack(
                        rx.dialog.title("Asignar Proyectos al Usuario", size="4", weight="bold", color="#0f172a"),
                        rx.dialog.description(
                            "Selecciona a qué proyectos del portafolio tiene acceso este usuario.",
                            size="2",
                            color="#64748b",
                        ),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.divider(),

                # Target User Summary Card
                rx.box(
                    rx.hstack(
                        rx.avatar(
                            fallback="US",
                            size="2",
                            radius="full",
                            color_scheme="indigo",
                        ),
                        rx.vstack(
                            rx.text(FlowState.assign_user_name, size="2", weight="bold", color="#0f172a"),
                            rx.text(FlowState.assign_user_email, size="1", color="#64748b"),
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.badge(FlowState.assign_user_role, color_scheme="blue", variant="soft", size="1"),
                        align="center",
                        spacing="2",
                        width="100%",
                    ),
                    padding="3",
                    background_color="#f8fafc",
                    border="1px solid #e2e8f0",
                    border_radius="8px",
                    width="100%",
                ),

                # Global Access Option
                rx.box(
                    rx.hstack(
                        rx.checkbox(
                            checked=FlowState.assign_user_projects.contains("all"),
                            on_change=lambda: FlowState.toggle_assign_project("all"),
                        ),
                        rx.vstack(
                            rx.text("Acceso Global a Todos los Proyectos", size="2", weight="bold", color="#0f172a"),
                            rx.text("El usuario tendrá visibilidad y acceso a todos los proyectos actuales y futuros.", size="1", color="#64748b"),
                            spacing="0",
                            align_items="start",
                        ),
                        align="center",
                        spacing="3",
                        width="100%",
                    ),
                    padding="3",
                    background_color=rx.cond(FlowState.assign_user_projects.contains("all"), "#eff6ff", "#ffffff"),
                    border=rx.cond(FlowState.assign_user_projects.contains("all"), "1px solid #bfdbfe", "1px solid #e2e8f0"),
                    border_radius="8px",
                    width="100%",
                ),

                # Individual Projects List
                rx.cond(
                    ~FlowState.assign_user_projects.contains("all"),
                    rx.vstack(
                        rx.text("Seleccionar Proyectos Específicos:", size="1", weight="bold", color="#334155"),
                        rx.box(
                            rx.vstack(
                                rx.foreach(
                                    FlowState.available_project_options,
                                    lambda opt: rx.box(
                                        rx.hstack(
                                            rx.checkbox(
                                                checked=FlowState.assign_user_projects.contains(opt["code"]),
                                                on_change=lambda: FlowState.toggle_assign_project(opt["code"]),
                                            ),
                                            rx.badge(opt["code"], color_scheme="indigo", variant="surface", size="1"),
                                            rx.text(opt["name"], size="2", weight="medium", color="#1e293b", line_clamp=1),
                                            align="center",
                                            spacing="2",
                                            width="100%",
                                        ),
                                        padding="2",
                                        border_bottom="1px solid #f1f5f9",
                                        width="100%",
                                    )
                                ),
                                spacing="1",
                                width="100%",
                            ),
                            max_height="220px",
                            overflow_y="auto",
                            background_color="#ffffff",
                            border="1px solid #e2e8f0",
                            border_radius="8px",
                            padding="2",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.box(),
                ),

                # Modal Actions
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        color_scheme="gray",
                        variant="soft",
                        size="2",
                        on_click=FlowState.close_assign_projects_modal,
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(
                            rx.icon("check", size=14),
                            rx.text("Guardar Asignación"),
                            align="center",
                            spacing="1",
                        ),
                        on_click=FlowState.save_user_projects_assignment,
                        color_scheme="indigo",
                        size="2",
                        radius="medium",
                    ),
                    width="100%",
                    align="center",
                ),
                spacing="4",
                width="100%",
            ),
            width="500px",
            max_width="95vw",
            border_radius="xl",
            padding="5",
            background_color="#ffffff",
        ),
        open=FlowState.show_assign_projects_modal,
        on_open_change=FlowState.set_show_assign_projects_modal,
    )


def new_user_modal() -> rx.Component:
    """Modal to register a new user in TEMIS with role & project assignment"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("user-plus", size=20, color="#1d4ed8"),
                    rx.text("Registrar Nuevo Usuario en TEMIS", size="4", weight="bold"),
                    align="center",
                    spacing="2"
                )
            ),
            rx.dialog.description(
                "Ingresa los datos del colaborador y asigna su perfil de acceso y proyectos autorizados.",
                size="2",
                color="#64748b",
                margin_bottom="16px"
            ),
            rx.vstack(
                # Name Field
                rx.vstack(
                    rx.text("Nombre Completo y Título *", size="1", weight="bold", color="#334155"),
                    rx.input(
                        placeholder="ej. Lic. Ana Martínez o Ing. Juan Pérez",
                        value=FlowState.new_user_name,
                        on_change=FlowState.set_new_user_name,
                        width="100%",
                        size="2",
                        radius="medium"
                    ),
                    align_items="start",
                    width="100%",
                    spacing="1"
                ),
                # Email Field
                rx.vstack(
                    rx.text("Correo Electrónico Institucional *", size="1", weight="bold", color="#334155"),
                    rx.input(
                        placeholder="usuario@maxillc.com",
                        value=FlowState.new_user_email,
                        on_change=FlowState.set_new_user_email,
                        type="email",
                        width="100%",
                        size="2",
                        radius="medium"
                    ),
                    align_items="start",
                    width="100%",
                    spacing="1"
                ),
                # Role Selection (No Emojis)
                rx.vstack(
                    rx.text("Perfil / Rol Asignado", size="1", weight="bold", color="#334155"),
                    rx.select.root(
                        rx.select.trigger(width="100%", size="2"),
                        rx.select.content(
                            rx.select.item("Super Admin (Acceso Total)", value="super_admin"),
                            rx.select.item("Dueño de Proyecto (PM)", value="project_manager"),
                            rx.select.item("Analista de Procesos", value="analyst"),
                            rx.select.item("Auditor QA / Six Sigma", value="qa_auditor"),
                            rx.select.item("Colaborador (Invitado)", value="collaborator"),
                        ),
                        value=FlowState.new_user_role,
                        on_change=FlowState.set_new_user_role,
                    ),
                    align_items="start",
                    width="100%",
                    spacing="1"
                ),
                # Department Field
                rx.vstack(
                    rx.text("Área / Departamento", size="1", weight="bold", color="#334155"),
                    rx.input(
                        placeholder="ej. Operaciones, TI, Finanzas, Calidad",
                        value=FlowState.new_user_department,
                        on_change=FlowState.set_new_user_department,
                        width="100%",
                        size="2",
                        radius="medium"
                    ),
                    align_items="start",
                    width="100%",
                    spacing="1"
                ),

                # Assigned Projects Selection Section
                rx.vstack(
                    rx.text("Asignación de Proyectos Inicial", size="1", weight="bold", color="#334155"),
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.checkbox(
                                    checked=FlowState.new_user_assigned_projects.contains("all"),
                                    on_change=lambda: FlowState.toggle_new_user_project("all"),
                                ),
                                rx.text("Acceso Global (Todos los Proyectos)", size="2", weight="medium", color="#1e293b"),
                                align="center",
                                spacing="2",
                            ),
                            rx.cond(
                                ~FlowState.new_user_assigned_projects.contains("all"),
                                rx.vstack(
                                    rx.foreach(
                                        FlowState.available_project_options,
                                        lambda opt: rx.hstack(
                                            rx.checkbox(
                                                checked=FlowState.new_user_assigned_projects.contains(opt["code"]),
                                                on_change=lambda: FlowState.toggle_new_user_project(opt["code"]),
                                            ),
                                            rx.badge(opt["code"], color_scheme="indigo", size="1"),
                                            rx.text(opt["name"], size="1", color="#334155", line_clamp=1),
                                            align="center",
                                            spacing="2",
                                        )
                                    ),
                                    spacing="1",
                                    padding_left="4",
                                    width="100%",
                                ),
                                rx.box(),
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        padding="3",
                        background_color="#f8fafc",
                        border="1px solid #e2e8f0",
                        border_radius="8px",
                        width="100%",
                    ),
                    align_items="start",
                    width="100%",
                    spacing="1"
                ),

                # Password Field (Masked & Security Guidance)
                rx.vstack(
                    rx.text("Contraseña Temporal de Primer Acceso", size="1", weight="bold", color="#334155"),
                    rx.input(
                        placeholder="••••••••••••",
                        type="password",
                        value=FlowState.new_user_password,
                        on_change=FlowState.set_new_user_password,
                        width="100%",
                        size="2",
                        radius="medium"
                    ),
                    rx.text(
                        "Se asignará una contraseña temporal de primer acceso (mínimo 8 caracteres). El usuario deberá actualizarla en su primer inicio de sesión.",
                        size="1",
                        color="#64748b"
                    ),
                    align_items="start",
                    width="100%",
                    spacing="1"
                ),
                spacing="3",
                width="100%",
                margin_bottom="16px"
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button("Cancelar", variant="soft", color_scheme="gray", size="2")
                ),
                rx.button(
                    rx.hstack(rx.icon("user-plus", size=15), rx.text("Guardar y Dar Acceso"), align="center", spacing="1"),
                    on_click=FlowState.submit_new_user,
                    color_scheme="indigo",
                    size="2",
                    radius="medium"
                ),
                justify="end",
                spacing="2",
                width="100%"
            ),
            max_width="520px",
            border_radius="16px",
            padding="24px"
        ),
        open=FlowState.show_new_user_modal,
        on_open_change=FlowState.set_show_new_user_modal,
    )


def user_management_view() -> rx.Component:
    """Main view for User Control & RBAC in TEMIS (Level 1 Subview)"""
    return rx.box(
        new_user_modal(),
        assign_projects_modal(),
        rx.vstack(
            # Top Navigation Bar
            rx.hstack(
                rx.hstack(
                    rx.icon("network", size=24, color="#1d4ed8"),
                    rx.vstack(
                        rx.hstack(
                            rx.text("TEMIS", size="4", weight="bold", color="#0f172a"),
                            rx.badge("Work OS Enterprise", color_scheme="indigo", variant="surface", size="1"),
                            align="center",
                            spacing="2",
                        ),
                        rx.text("Control y Administración de Accesos & Perfiles", size="1", color="#64748b"),
                        spacing="0",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.spacer(),
                # View Switcher (Portfolio vs Users - No Emojis)
                rx.segmented_control.root(
                    rx.segmented_control.item("Portafolio de Proyectos", value="portfolio"),
                    rx.segmented_control.item("Control de Usuarios", value="users"),
                    value=FlowState.hub_active_subview,
                    on_change=FlowState.set_hub_active_subview,
                    size="2",
                    radius="medium"
                ),
                rx.spacer(),
                # User Profile & Logout
                rx.hstack(
                    rx.avatar(
                        fallback=FlowState.user_initials,
                        size="2",
                        radius="full",
                        color_scheme="indigo",
                        variant="soft"
                    ),
                    rx.vstack(
                        rx.text(FlowState.user_name, size="1", weight="bold", color="#0f172a"),
                        rx.badge("Super Admin", color_scheme="purple", variant="soft", size="1"),
                        spacing="0",
                        align_items="start"
                    ),
                    rx.divider(orientation="vertical", size="2"),
                    rx.button(
                        rx.hstack(rx.icon("log-out", size=14), rx.text("Salir"), align="center", spacing="1"),
                        on_click=FlowState.logout,
                        color_scheme="ruby",
                        variant="soft",
                        size="2",
                        radius="medium",
                        title="Cerrar Sesión",
                    ),
                    align="center",
                    spacing="2"
                ),
                width="100%",
                height="60px",
                padding_x="6",
                background_color="#ffffff",
                border_bottom="1px solid #e2e8f0",
                align="center",
                box_shadow="0 1px 2px 0 rgba(0, 0, 0, 0.02)",
            ),

            # Main Body Container
            rx.box(
                rx.vstack(
                    # 4 KPI Cards
                    rx.grid(
                        # Card 1: Total Users
                        rx.box(
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Total Usuarios", size="1", weight="medium", color="#64748b"),
                                    rx.text(FlowState.users_total_count, size="6", weight="bold", color="#0f172a"),
                                    spacing="0"
                                ),
                                rx.spacer(),
                                rx.box(
                                    rx.icon("users", size=20, color="#1d4ed8"),
                                    padding="3",
                                    background_color="#eff6ff",
                                    border_radius="12px"
                                ),
                                align="center"
                            ),
                            padding="4",
                            background_color="#ffffff",
                            border="1px solid #e2e8f0",
                            border_radius="12px",
                            box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.02)"
                        ),
                        # Card 2: Super Admins
                        rx.box(
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Super Administradores", size="1", weight="medium", color="#64748b"),
                                    rx.text(FlowState.users_super_admin_count, size="6", weight="bold", color="#7c3aed"),
                                    spacing="0"
                                ),
                                rx.spacer(),
                                rx.box(
                                    rx.icon("shield", size=20, color="#7c3aed"),
                                    padding="3",
                                    background_color="#ede9fe",
                                    border_radius="12px"
                                ),
                                align="center"
                            ),
                            padding="4",
                            background_color="#ffffff",
                            border="1px solid #e2e8f0",
                            border_radius="12px",
                            box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.02)"
                        ),
                        # Card 3: Project Managers
                        rx.box(
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Dueños de Proyecto (PM)", size="1", weight="medium", color="#64748b"),
                                    rx.text(FlowState.users_pm_count, size="6", weight="bold", color="#2563eb"),
                                    spacing="0"
                                ),
                                rx.spacer(),
                                rx.box(
                                    rx.icon("briefcase", size=20, color="#2563eb"),
                                    padding="3",
                                    background_color="#dbeafe",
                                    border_radius="12px"
                                ),
                                align="center"
                            ),
                            padding="4",
                            background_color="#ffffff",
                            border="1px solid #e2e8f0",
                            border_radius="12px",
                            box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.02)"
                        ),
                        # Card 4: Analysts & Collaborators
                        rx.box(
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Analistas & Calidad", size="1", weight="medium", color="#64748b"),
                                    rx.text(FlowState.users_analyst_qa_count, size="6", weight="bold", color="#0d9488"),
                                    spacing="0"
                                ),
                                rx.spacer(),
                                rx.box(
                                    rx.icon("check-circle-2", size=20, color="#0d9488"),
                                    padding="3",
                                    background_color="#ccfbf1",
                                    border_radius="12px"
                                ),
                                align="center"
                            ),
                            padding="4",
                            background_color="#ffffff",
                            border="1px solid #e2e8f0",
                            border_radius="12px",
                            box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.02)"
                        ),
                        columns="4",
                        spacing="4",
                        width="100%",
                    ),

                    # Search & Action Bar
                    rx.hstack(
                        rx.input(
                            rx.input.slot(rx.icon("search", size=15, color="#94a3b8")),
                            placeholder="Buscar por nombre, correo o departamento...",
                            value=FlowState.user_search_query,
                            on_change=FlowState.set_user_search_query,
                            width="340px",
                            size="2",
                            radius="medium"
                        ),
                        rx.select.root(
                            rx.select.trigger(width="180px", size="2"),
                            rx.select.content(
                                rx.select.item("Todos los perfiles", value="all"),
                                rx.select.item("Super Admin", value="super_admin"),
                                rx.select.item("Dueño de Proyecto", value="project_manager"),
                                rx.select.item("Analista de Procesos", value="analyst"),
                                rx.select.item("Auditor QA", value="qa_auditor"),
                                rx.select.item("Colaborador", value="collaborator"),
                            ),
                            value=FlowState.user_filter_role,
                            on_change=FlowState.set_user_filter_role,
                        ),
                        rx.select.root(
                            rx.select.trigger(width="150px", size="2"),
                            rx.select.content(
                                rx.select.item("Todos los estados", value="all"),
                                rx.select.item("Activos", value="active"),
                                rx.select.item("Inactivos", value="inactive"),
                            ),
                            value=FlowState.user_filter_status,
                            on_change=FlowState.set_user_filter_status,
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.hstack(rx.icon("user-plus", size=15), rx.text("Registrar Nuevo Usuario", weight="bold"), align="center", spacing="1"),
                            on_click=FlowState.open_new_user_modal,
                            color_scheme="blue",
                            size="2",
                            radius="medium",
                        ),
                        width="100%",
                        align="center",
                        spacing="3"
                    ),

                    # Users Table Card
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Usuario & Correo"),
                                    rx.table.column_header_cell("Perfil / Rol RBAC"),
                                    rx.table.column_header_cell("Departamento"),
                                    rx.table.column_header_cell("Proyectos Asignados"),
                                    rx.table.column_header_cell("Estado"),
                                    rx.table.column_header_cell("Último Acceso"),
                                    rx.table.column_header_cell("Acciones"),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(
                                    FlowState.filtered_users_list,
                                    user_row
                                )
                            ),
                            width="100%",
                            variant="surface"
                        ),
                        background_color="#ffffff",
                        border="1px solid #e2e8f0",
                        border_radius="12px",
                        width="100%",
                        overflow="hidden",
                        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.02)"
                    ),

                    # RBAC Privilege Matrix Card
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("shield-check", size=18, color="#1d4ed8"),
                                rx.text("Matriz de Privilegios & Permisos por Rol en TEMIS", size="2", weight="bold", color="#0f172a"),
                                align="center",
                                spacing="2"
                            ),
                            rx.grid(
                                rx.box(
                                    rx.vstack(
                                        rx.badge(rx.hstack(rx.icon("shield", size=11), rx.text("Super Admin"), align="center", spacing="1"), color_scheme="purple", variant="soft", size="1"),
                                        rx.text("• Acceso total al Portafolio", size="1", color="#475569"),
                                        rx.text("• Gestión de usuarios y perfiles", size="1", color="#475569"),
                                        rx.text("• Sync con Google Drive y Sheets", size="1", color="#475569"),
                                        rx.text("• Auditoría IA y control de 7 fases", size="1", color="#475569"),
                                        spacing="1",
                                        align_items="start"
                                    ),
                                    padding="3",
                                    background_color="#f8fafc",
                                    border_radius="8px",
                                    border="1px solid #e2e8f0"
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.badge(rx.hstack(rx.icon("briefcase", size=11), rx.text("Dueño de Proyecto"), align="center", spacing="1"), color_scheme="blue", variant="soft", size="1"),
                                        rx.text("• Creación de nuevos proyectos", size="1", color="#475569"),
                                        rx.text("• Plan de trabajo y Sprints IA", size="1", color="#475569"),
                                        rx.text("• Edición de Ficha Charter", size="1", color="#475569"),
                                        rx.text("• Exportación de paquetes .temis", size="1", color="#475569"),
                                        spacing="1",
                                        align_items="start"
                                    ),
                                    padding="3",
                                    background_color="#f8fafc",
                                    border_radius="8px",
                                    border="1px solid #e2e8f0"
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.badge(rx.hstack(rx.icon("bar-chart-3", size=11), rx.text("Analista de Procesos"), align="center", spacing="1"), color_scheme="teal", variant="soft", size="1"),
                                        rx.text("• Modelado de diagramas Bézier", size="1", color="#475569"),
                                        rx.text("• Edición de Matriz SIPOC", size="1", color="#475569"),
                                        rx.text("• Generación con Gemini AI", size="1", color="#475569"),
                                        rx.text("• Registro de Daily Logs", size="1", color="#475569"),
                                        spacing="1",
                                        align_items="start"
                                    ),
                                    padding="3",
                                    background_color="#f8fafc",
                                    border_radius="8px",
                                    border="1px solid #e2e8f0"
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.badge(rx.hstack(rx.icon("check-circle-2", size=11), rx.text("Auditor QA / Six Sigma"), align="center", spacing="1"), color_scheme="amber", variant="soft", size="1"),
                                        rx.text("• Ejecución de Auditorías IA", size="1", color="#475569"),
                                        rx.text("• Validación de reglas Six Sigma", size="1", color="#475569"),
                                        rx.text("• Aprobación de entregables", size="1", color="#475569"),
                                        rx.text("• Consulta de bitácora y avance", size="1", color="#475569"),
                                        spacing="1",
                                        align_items="start"
                                    ),
                                    padding="3",
                                    background_color="#f8fafc",
                                    border_radius="8px",
                                    border="1px solid #e2e8f0"
                                ),
                                columns="4",
                                spacing="3",
                                width="100%"
                            ),
                            spacing="3",
                            width="100%"
                        ),
                        padding="4",
                        background_color="#ffffff",
                        border="1px solid #e2e8f0",
                        border_radius="12px",
                        width="100%",
                        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.02)"
                    ),

                    spacing="5",
                    width="100%",
                    max_width="1280px",
                    margin_x="auto",
                ),
                padding="6",
                width="100%",
                flex="1",
                overflow_y="auto",
            ),
            width="100%",
            height="100vh",
            spacing="0",
        ),
        background_color="#f8fafc",
        width="100%",
        height="100vh",
        font_family="Inter, sans-serif",
    )
