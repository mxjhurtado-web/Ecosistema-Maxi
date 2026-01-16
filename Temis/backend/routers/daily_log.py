#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Daily Log router for TEMIS
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

from backend.database import get_db
from backend.models.user import User
from backend.models.daily_log import DailyLog
from backend.services.drive_service import DriveService

router = APIRouter()


class DailyLogCreate(BaseModel):
    """Daily log creation request"""
    log_date: date
    content: str


class DailyLogUpdate(BaseModel):
    """Daily log update request"""
    content: str


class DailyLogResponse(BaseModel):
    """Daily log response"""
    id: str
    project_id: str
    log_date: date
    content: str
    processed: bool
    processed_at: Optional[datetime]
    drive_file_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/{project_id}/dailylog", response_model=DailyLogResponse)
def create_daily_log(
    project_id: str,
    log_data: DailyLogCreate,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Create or update daily log"""
    # Get user
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if log already exists for this date
    existing_log = db.query(DailyLog).filter(
        DailyLog.project_id == project_id,
        DailyLog.log_date == log_data.log_date
    ).first()

    if existing_log:
        # Update existing log
        existing_log.content = log_data.content
        existing_log.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_log)
        return existing_log

    # Create new log
    daily_log = DailyLog(
        project_id=project_id,
        log_date=log_data.log_date,
        content=log_data.content,
        created_by=user.id
    )
    db.add(daily_log)
    db.commit()
    db.refresh(daily_log)

    return daily_log


@router.get("/{project_id}/dailylog", response_model=Optional[DailyLogResponse])
def get_daily_log(
    project_id: str,
    log_date: date,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Get daily log for specific date"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    daily_log = db.query(DailyLog).filter(
        DailyLog.project_id == project_id,
        DailyLog.log_date == log_date
    ).first()

    return daily_log


@router.put("/{project_id}/dailylog/{log_id}", response_model=DailyLogResponse)
def update_daily_log(
    project_id: str,
    log_id: str,
    log_data: DailyLogUpdate,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Update daily log"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    daily_log = db.query(DailyLog).filter(
        DailyLog.id == log_id,
        DailyLog.project_id == project_id
    ).first()

    if not daily_log:
        raise HTTPException(status_code=404, detail="Daily log not found")

    daily_log.content = log_data.content
    daily_log.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(daily_log)

    return daily_log
