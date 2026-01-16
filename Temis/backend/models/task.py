#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Task model for TEMIS
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Date, Enum

from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.database import Base


class TaskStatus(str, enum.Enum):
    """Task status"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class TaskPriority(str, enum.Enum):
    """Task priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskSource(str, enum.Enum):
    """Task source"""
    MANUAL = "manual"
    GEMINI_EXTRACTED = "gemini_extracted"


class Task(Base):
    """Task model"""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    entry_id = Column(String(50))  # e.g., TASK-001
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    assigned_to = Column(String(36), ForeignKey("users.id"))
    due_date = Column(Date)
    source = Column(Enum(TaskSource), default=TaskSource.MANUAL, nullable=False)
    daily_log_id = Column(String(36), ForeignKey("daily_logs.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    daily_log = relationship("DailyLog", foreign_keys=[daily_log_id])

    def __repr__(self):
        return f"<Task {self.entry_id}: {self.title}>"
