#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Decision model for TEMIS
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum

from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.database import Base


class DecisionSource(str, enum.Enum):
    """Decision source"""
    MANUAL = "manual"
    GEMINI_EXTRACTED = "gemini_extracted"


class Decision(Base):
    """Decision model"""
    __tablename__ = "decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    entry_id = Column(String(50))  # e.g., DEC-001
    title = Column(String(255), nullable=False)
    description = Column(Text)
    rationale = Column(Text)  # Why this decision was made
    decided_by = Column(String(36), ForeignKey("users.id"))
    decided_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(Enum(DecisionSource), default=DecisionSource.MANUAL, nullable=False)
    daily_log_id = Column(String(36), ForeignKey("daily_logs.id"))

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    decider = relationship("User", foreign_keys=[decided_by])
    daily_log = relationship("DailyLog", foreign_keys=[daily_log_id])

    def __repr__(self):
        return f"<Decision {self.entry_id}: {self.title}>"
