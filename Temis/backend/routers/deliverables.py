#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deliverables router for TEMIS
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

from backend.database import get_db
from backend.models.user import User
from backend.models.phase import Phase
from backend.models.deliverable import Deliverable, DeliverableType, DeliverableStatus

router = APIRouter()


class DeliverableCreate(BaseModel):
    """Deliverable creation request"""
    name: str
    description: Optional[str] = None
    type: str = "document"
    assigned_to_email: Optional[str] = None
    due_date: Optional[date] = None


class DeliverableUpdate(BaseModel):
    """Deliverable update request"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to_email: Optional[str] = None
    due_date: Optional[date] = None


class DeliverableResponse(BaseModel):
    """Deliverable response"""
    id: str
    phase_id: str
    name: str
    description: Optional[str]
    type: str
    status: str
    drive_file_id: Optional[str]
    assigned_to: Optional[str]
    due_date: Optional[date]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/{project_id}/phases/{phase_number}/deliverables", response_model=DeliverableResponse)
def create_deliverable(
    project_id: str,
    phase_number: int,
    deliverable_data: DeliverableCreate,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Create deliverable for phase"""
    # Get user
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get phase
    phase = db.query(Phase).filter(
        Phase.project_id == project_id,
        Phase.phase_number == phase_number
    ).first()

    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    # Get assignee if provided
    assigned_to_id = None
    if deliverable_data.assigned_to_email:
        assignee = db.query(User).filter(User.email == deliverable_data.assigned_to_email).first()
        if assignee:
            assigned_to_id = assignee.id

    # Create deliverable
    deliverable = Deliverable(
        phase_id=phase.id,
        name=deliverable_data.name,
        description=deliverable_data.description,
        type=DeliverableType(deliverable_data.type),
        assigned_to=assigned_to_id,
        due_date=deliverable_data.due_date
    )

    db.add(deliverable)
    db.commit()
    db.refresh(deliverable)

    return deliverable


@router.get("/{project_id}/phases/{phase_number}/deliverables", response_model=List[DeliverableResponse])
def get_phase_deliverables(
    project_id: str,
    phase_number: int,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Get deliverables for phase"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get phase
    phase = db.query(Phase).filter(
        Phase.project_id == project_id,
        Phase.phase_number == phase_number
    ).first()

    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    # Get deliverables
    deliverables = db.query(Deliverable).filter(
        Deliverable.phase_id == phase.id
    ).all()

    return deliverables


@router.put("/{project_id}/deliverables/{deliverable_id}", response_model=DeliverableResponse)
def update_deliverable(
    project_id: str,
    deliverable_id: str,
    deliverable_data: DeliverableUpdate,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Update deliverable"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    deliverable = db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()
    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")

    # Update fields
    if deliverable_data.name:
        deliverable.name = deliverable_data.name
    if deliverable_data.description is not None:
        deliverable.description = deliverable_data.description
    if deliverable_data.status:
        deliverable.status = DeliverableStatus(deliverable_data.status)
        if deliverable.status == DeliverableStatus.APPROVED:
            deliverable.completed_at = datetime.utcnow()
    if deliverable_data.assigned_to_email:
        assignee = db.query(User).filter(User.email == deliverable_data.assigned_to_email).first()
        if assignee:
            deliverable.assigned_to = assignee.id
    if deliverable_data.due_date:
        deliverable.due_date = deliverable_data.due_date

    db.commit()
    db.refresh(deliverable)

    return deliverable


@router.delete("/{project_id}/deliverables/{deliverable_id}")
def delete_deliverable(
    project_id: str,
    deliverable_id: str,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Delete deliverable"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    deliverable = db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()
    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")

    db.delete(deliverable)
    db.commit()

    return {"status": "deleted", "id": deliverable_id}
