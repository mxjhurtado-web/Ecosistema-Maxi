#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extended User model for TEMIS - Framework Roles
Based on: Framework gestión de proyectos.pdf
"""

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Boolean

from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.database import Base


class UserRole(str, enum.Enum):
    """User global roles"""
    PRIMARY_OWNER = "primary_owner"  # mxjhurtado@maxillc.com
    OWNER = "owner"                  # Can create projects and assign roles
    MEMBER = "member"                # Can participate in projects
    VIEWER = "viewer"                # Read-only access


class ProjectRole(str, enum.Enum):
    """Project-specific roles (Framework roles)"""
    SPONSOR = "sponsor"                    # Aprueba presupuesto y cambios mayores
    PROJECT_LEAD = "project_lead"          # Responsable general del proyecto (PM)
    PRODUCT_OWNER = "product_owner"        # Define backlog y prioridades
    AGILE_LEAD = "agile_lead"             # Facilita ceremonias Scrum
    UX_DESIGNER = "ux_designer"           # Diseño de experiencia
    DEVELOPER = "developer"                # Desarrollo
    QA_ENGINEER = "qa_engineer"           # Calidad y testing
    PROCESS_OWNER = "process_owner"       # Responsable de procesos
    DATA_QUALITY = "data_quality"         # Responsable de calidad de datos
    STAKEHOLDER = "stakeholder"           # Miembro del comité


# Matriz de permisos por rol
ROLE_PERMISSIONS = {
    ProjectRole.SPONSOR: {
        "can_approve_budget": True,
        "can_approve_major_changes": True,
        "can_close_project": True,
        "can_edit_charter": True,
        "can_assign_roles": False,
        "can_close_sprint": False
    },
    ProjectRole.PROJECT_LEAD: {
        "can_approve_budget": True,
        "can_approve_major_changes": True,
        "can_close_project": True,
        "can_edit_charter": True,
        "can_assign_roles": True,
        "can_close_sprint": True,
        "can_manage_all": True
    },
    ProjectRole.PRODUCT_OWNER: {
        "can_approve_budget": False,
        "can_approve_major_changes": False,  # Solo cambios de backlog
        "can_close_project": False,
        "can_edit_charter": True,
        "can_assign_roles": False,
        "can_close_sprint": True,
        "can_manage_backlog": True
    },
    ProjectRole.AGILE_LEAD: {
        "can_approve_budget": False,
        "can_approve_major_changes": False,
        "can_close_project": False,
        "can_edit_charter": False,
        "can_assign_roles": False,
        "can_close_sprint": True,
        "can_facilitate_ceremonies": True
    },
    ProjectRole.DEVELOPER: {
        "can_approve_budget": False,
        "can_approve_major_changes": False,
        "can_close_project": False,
        "can_edit_charter": False,
        "can_assign_roles": False,
        "can_close_sprint": False,
        "can_contribute": True
    }
}


class ProjectMemberExtended(Base):
    """Extended project membership with framework roles"""
    __tablename__ = "project_members_extended"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Framework roles (un usuario puede tener múltiples roles)
    is_sponsor = Column(Boolean, default=False)
    is_project_lead = Column(Boolean, default=False)
    is_product_owner = Column(Boolean, default=False)
    is_agile_lead = Column(Boolean, default=False)
    is_ux_designer = Column(Boolean, default=False)
    is_developer = Column(Boolean, default=False)
    is_qa_engineer = Column(Boolean, default=False)
    is_process_owner = Column(Boolean, default=False)
    is_data_quality = Column(Boolean, default=False)
    is_stakeholder = Column(Boolean, default=False)
    
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    user = relationship("User", foreign_keys=[user_id])

    def get_roles(self) -> list:
        """Get list of roles for this member"""
        roles = []
        if self.is_sponsor: roles.append(ProjectRole.SPONSOR)
        if self.is_project_lead: roles.append(ProjectRole.PROJECT_LEAD)
        if self.is_product_owner: roles.append(ProjectRole.PRODUCT_OWNER)
        if self.is_agile_lead: roles.append(ProjectRole.AGILE_LEAD)
        if self.is_ux_designer: roles.append(ProjectRole.UX_DESIGNER)
        if self.is_developer: roles.append(ProjectRole.DEVELOPER)
        if self.is_qa_engineer: roles.append(ProjectRole.QA_ENGINEER)
        if self.is_process_owner: roles.append(ProjectRole.PROCESS_OWNER)
        if self.is_data_quality: roles.append(ProjectRole.DATA_QUALITY)
        if self.is_stakeholder: roles.append(ProjectRole.STAKEHOLDER)
        return roles

    def has_permission(self, permission: str) -> bool:
        """Check if member has specific permission"""
        roles = self.get_roles()
        for role in roles:
            if role in ROLE_PERMISSIONS:
                if ROLE_PERMISSIONS[role].get(permission, False):
                    return True
        return False

    def can_approve_changes(self) -> bool:
        """Check if can approve changes"""
        return self.has_permission("can_approve_major_changes")

    def can_close_sprint(self) -> bool:
        """Check if can close sprint"""
        return self.has_permission("can_close_sprint")
