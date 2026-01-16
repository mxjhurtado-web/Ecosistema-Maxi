#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phases router for TEMIS
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.database import get_db
from backend.models.user import User
from backend.models.phase import Phase, PhaseStatus, PHASE_NAMES

router = APIRouter()


class PhaseUpdate(BaseModel):
    """Phase update request"""
    status: Optional[str] = None


class PhaseResponse(BaseModel):
    """Phase response"""
    id: str
    project_id: str
    phase_number: int
    name: str
    description: Optional[str]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/{project_id}/phases", response_model=List[PhaseResponse])
def get_project_phases(
    project_id: str,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Get all phases for project"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    phases = db.query(Phase).filter(
        Phase.project_id == project_id
    ).order_by(Phase.phase_number).all()

    return phases


@router.put("/{project_id}/phases/{phase_number}", response_model=PhaseResponse)
def update_phase(
    project_id: str,
    phase_number: int,
    phase_data: PhaseUpdate,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Update phase status"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    phase = db.query(Phase).filter(
        Phase.project_id == project_id,
        Phase.phase_number == phase_number
    ).first()

    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    # Update status
    if phase_data.status:
        new_status = PhaseStatus(phase_data.status)
        phase.status = new_status

        if new_status == PhaseStatus.IN_PROGRESS and not phase.started_at:
            phase.started_at = datetime.utcnow()
        elif new_status == PhaseStatus.COMPLETED:
            phase.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(phase)

    return phase


@router.post("/{project_id}/phases/{phase_number}/complete", response_model=PhaseResponse)
def complete_phase(
    project_id: str,
    phase_number: int,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Complete phase and move to next"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    phase = db.query(Phase).filter(
        Phase.project_id == project_id,
        Phase.phase_number == phase_number
    ).first()

    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    # Mark as completed
    phase.status = PhaseStatus.COMPLETED
    phase.completed_at = datetime.utcnow()

    # Start next phase if exists
    if phase_number < 7:
        next_phase = db.query(Phase).filter(
            Phase.project_id == project_id,
            Phase.phase_number == phase_number + 1
        ).first()

        if next_phase:
            next_phase.status = PhaseStatus.IN_PROGRESS
            next_phase.started_at = datetime.utcnow()

    db.commit()
    db.refresh(phase)

    return phase
