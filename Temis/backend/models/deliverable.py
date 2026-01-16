#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deliverable model for TEMIS
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Date, Enum

from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.database import Base


class DeliverableType(str, enum.Enum):
    """Deliverable type"""
    DOCUMENT = "document"
    PRESENTATION = "presentation"
    SPREADSHEET = "spreadsheet"
    CODE = "code"
    MANUAL = "manual"
    OTHER = "other"


class DeliverableStatus(str, enum.Enum):
    """Deliverable status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"


class Deliverable(Base):
    """Deliverable model"""
    __tablename__ = "deliverables"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phase_id = Column(String(36), ForeignKey("phases.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum(DeliverableType), default=DeliverableType.DOCUMENT, nullable=False)
    status = Column(Enum(DeliverableStatus), default=DeliverableStatus.PENDING, nullable=False)
    drive_file_id = Column(String(255))  # Google Drive file ID
    assigned_to = Column(String(36), ForeignKey("users.id"))
    due_date = Column(Date)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    phase = relationship("Phase", foreign_keys=[phase_id])
    assignee = relationship("User", foreign_keys=[assigned_to])

    def __repr__(self):
        return f"<Deliverable {self.name}>"

    @property
    def is_completed(self) -> bool:
        """Check if deliverable is completed"""
        return self.status == DeliverableStatus.APPROVED

    @property
    def is_overdue(self) -> bool:
        """Check if deliverable is overdue"""
        if self.due_date and not self.is_completed:
            from datetime import date
            return date.today() > self.due_date
        return False
