#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase model for TEMIS
7-phase framework
"""

from sqlalchemy import Column, String, Text, DateTime, Date, ForeignKey, Integer, Enum, UniqueConstraint

from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from backend.database import Base


class PhaseStatus(str, enum.Enum):
    """Phase status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# Phase names mapping (sin acentos para evitar UnicodeEncodeError)
PHASE_NAMES = {
    1: "Diagnostico Estrategico",
    2: "Inicio del Proyecto",
    3: "Planificacion Hibrida",
    4: "Ejecucion Iterativa",
    5: "Monitoreo y Control",
    6: "Mejora Continua",
    7: "Cierre del Proyecto"
}


class Phase(Base):
    """Phase model (7 phases per project)"""
    __tablename__ = "phases"
    __table_args__ = (
        UniqueConstraint('project_id', 'phase_number', name='uq_project_phase'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    phase_number = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)  # Description from document analysis
    tasks = Column(Text, nullable=True)        # JSON string of tasks
    deliverables = Column(Text, nullable=True) # JSON string of deliverables
    status = Column(Enum(PhaseStatus), default=PhaseStatus.NOT_STARTED)
    progress = Column(Integer, default=0)      # Progress percentage (0-100)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="phases")

    def __repr__(self):
        return f"<Phase {self.phase_number}: {self.name}>"

    @staticmethod
    def get_phase_name(phase_number: int) -> str:
        """Get phase name by number"""
        return PHASE_NAMES.get(phase_number, f"Fase {phase_number}")
