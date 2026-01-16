#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
User model for TEMIS
"""

from sqlalchemy import Column, String, DateTime, Enum

from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.database import Base


class UserRole(str, enum.Enum):
    """User roles"""
    PRIMARY_OWNER = "primary_owner"
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    keycloak_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    created_groups = relationship("Group", back_populates="creator", foreign_keys="Group.created_by")
    created_projects = relationship("Project", back_populates="creator", foreign_keys="Project.created_by")
    group_memberships = relationship("GroupMember", back_populates="user")
    project_memberships = relationship("ProjectMember", back_populates="user")

    def __repr__(self):
        return f"<User {self.email}>"

    def is_primary_owner(self):
        """Check if user is primary owner"""
        return self.role == UserRole.PRIMARY_OWNER

    def can_assign_owners(self):
        """Check if user can assign owners"""
        return self.role == UserRole.PRIMARY_OWNER
