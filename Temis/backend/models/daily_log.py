#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Daily Log model for TEMIS
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Date, UniqueConstraint

from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid

from backend.database import Base


class DailyLog(Base):
    """Daily Log model"""
    __tablename__ = "daily_logs"
    __table_args__ = (
        UniqueConstraint('project_id', 'log_date', name='uq_project_log_date'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    log_date = Column(Date, nullable=False, index=True)
    content = Column(Text, nullable=False)  # Markdown format
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime)
    drive_file_id = Column(String(255))  # Google Drive file ID
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<DailyLog {self.project_id} - {self.log_date}>"

    @property
    def is_today(self) -> bool:
        """Check if log is for today"""
        return self.log_date == date.today()
