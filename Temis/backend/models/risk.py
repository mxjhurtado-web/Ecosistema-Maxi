#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Risk model for TEMIS
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum

from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.database import Base


class RiskImpact(str, enum.Enum):
    """Risk impact"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskProbability(str, enum.Enum):
    """Risk probability"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskStatus(str, enum.Enum):
    """Risk status"""
    OPEN = "open"
    MITIGATING = "mitigating"
    CLOSED = "closed"


class RiskSource(str, enum.Enum):
    """Risk source"""
    MANUAL = "manual"
    GEMINI_EXTRACTED = "gemini_extracted"


class Risk(Base):
    """Risk model"""
    __tablename__ = "risks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    entry_id = Column(String(50))  # e.g., RISK-001
    title = Column(String(255), nullable=False)
    description = Column(Text)
    impact = Column(Enum(RiskImpact), default=RiskImpact.MEDIUM, nullable=False)
    probability = Column(Enum(RiskProbability), default=RiskProbability.MEDIUM, nullable=False)
    mitigation = Column(Text)
    status = Column(Enum(RiskStatus), default=RiskStatus.OPEN, nullable=False)
    source = Column(Enum(RiskSource), default=RiskSource.MANUAL, nullable=False)
    daily_log_id = Column(String(36), ForeignKey("daily_logs.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    daily_log = relationship("DailyLog", foreign_keys=[daily_log_id])

    def __repr__(self):
        return f"<Risk {self.entry_id}: {self.title}>"
