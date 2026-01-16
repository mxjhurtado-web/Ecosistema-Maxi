#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Models package for TEMIS
Import all models to ensure relationships are properly configured
"""

from backend.models.user import User, UserRole
from backend.models.group import Group, GroupMember, GroupMemberRole
from backend.models.project import Project, ProjectStatus, ProjectMember, ProjectMemberRole
from backend.models.phase import Phase, PhaseStatus, PHASE_NAMES
from backend.models.chat_message import ChatMessage

__all__ = [
    'User', 'UserRole',
    'Group', 'GroupMember', 'GroupMemberRole',
    'Project', 'ProjectStatus', 'ProjectMember', 'ProjectMemberRole',
    'Phase', 'PhaseStatus', 'PHASE_NAMES',
    'ChatMessage'
]
