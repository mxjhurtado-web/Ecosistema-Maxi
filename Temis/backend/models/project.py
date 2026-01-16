#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project model for TEMIS
SQLite-compatible version
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.database import Base


class ProjectStatus(str, enum.Enum):
    """Project status"""
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectMemberRole(str, enum.Enum):
    """Project member roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Project(Base):
    """Project model"""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    current_phase = Column(Integer, default=1, nullable=False)  # 1..7
    group_id = Column(String(36), ForeignKey("groups.id"))
    drive_folder_id = Column(String(255))  # Google Drive folder ID
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Project roles as JSON (for SQLite compatibility)
    project_roles = Column(Text)  # JSON string of roles

    # Relationships
    creator = relationship("User", back_populates="created_projects", foreign_keys=[created_by])
    group = relationship("Group", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    phases = relationship("Phase", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.name}>"


class ProjectMember(Base):
    """Project membership model"""
    __tablename__ = "project_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(ProjectMemberRole), default=ProjectMemberRole.MEMBER, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Framework roles as JSON (for SQLite compatibility)
    project_roles = Column(Text)  # JSON string: ["SPONSOR", "PROJECT_LEAD", etc.]

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")

    def __repr__(self):
        return f"<ProjectMember {self.user_id} in {self.project_id}>"
