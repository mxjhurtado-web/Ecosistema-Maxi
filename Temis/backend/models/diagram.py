#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Diagram model for TEMIS Process Flow Diagrams
Supports custom symbology and swimlanes
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import json

from backend.database import Base


class Diagram(Base):
    """Diagram model for storing process flowcharts"""
    __tablename__ = "diagrams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    phase_id = Column(String(36), ForeignKey("phases.id", ondelete="SET NULL"), nullable=True)
    
    title = Column(String(255), nullable=False, default="Nuevo Diagrama de Flujo")
    description = Column(Text, nullable=True)
    
    # JSON String fields
    swimlanes = Column(Text, nullable=False, default=json.dumps(["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"]))
    nodes = Column(Text, nullable=False, default=json.dumps([]))
    edges = Column(Text, nullable=False, default=json.dumps([]))
    viewport = Column(Text, nullable=False, default=json.dumps({"x": 0, "y": 0, "zoom": 1}))
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", backref="diagrams")
    phase = relationship("Phase", backref="diagrams")

    def __repr__(self):
        return f"<Diagram '{self.title}' in Project {self.project_id}>"

    def to_dict(self):
        """Convert diagram model to dict"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "phase_id": self.phase_id,
            "title": self.title,
            "description": self.description,
            "swimlanes": json.loads(self.swimlanes) if self.swimlanes else [],
            "nodes": json.loads(self.nodes) if self.nodes else [],
            "edges": json.loads(self.edges) if self.edges else [],
            "viewport": json.loads(self.viewport) if self.viewport else {"x": 0, "y": 0, "zoom": 1},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
