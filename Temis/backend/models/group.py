#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Group model for TEMIS
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum

from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.database import Base


class GroupMemberRole(str, enum.Enum):
    """Group member roles"""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Group(Base):
    """Group model"""
    __tablename__ = "groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_groups", foreign_keys=[created_by])
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="group")

    def __repr__(self):
        return f"<Group {self.name}>"


class GroupMember(Base):
    """Group membership model"""
    __tablename__ = "group_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(GroupMemberRole), default=GroupMemberRole.MEMBER, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

    def __repr__(self):
        return f"<GroupMember {self.user_id} in {self.group_id}>"
