#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Proyecto Max router for TEMIS
Handles Proyecto Max document generation and updates
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date

from backend.database import get_db
from backend.models.user import User
from backend.models.project import Project
from backend.models.daily_log import DailyLog
from backend.models.task import Task
from backend.models.risk import Risk
from backend.models.decision import Decision
from backend.services.proyecto_max_service import ProyectoMaxUpdater
from backend.services.gemini_service import GeminiService
from backend.services.drive_service import DriveService

router = APIRouter()


class ProyectoMaxUpdateRequest(BaseModel):
    """Request to update Proyecto Max"""
    gemini_api_key: str


class ProyectoMaxGenerateRequest(BaseModel):
    """Request to generate complete Proyecto Max"""
    gemini_api_key: str
    include_all_phases: bool = True


@router.post("/{project_id}/proyecto-max/update")
async def update_proyecto_max(
    project_id: str,
    request: ProyectoMaxUpdateRequest,
    user_email: str,
    db: Session = Depends(get_db)
):
    """
    Update Proyecto Max with current project data (Opción A)
    Called automatically after EOD or manually
    """
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get project data
    daily_logs = db.query(DailyLog).filter(DailyLog.project_id == project_id).all()
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    risks = db.query(Risk).filter(Risk.project_id == project_id).all()
    decisions = db.query(Decision).filter(Decision.project_id == project_id).all()

    # Convert to dicts
    daily_logs_data = [{"content": log.content, "date": log.log_date} for log in daily_logs]
    tasks_data = [{"id": str(task.id), "title": task.title, "status": task.status.value} for task in tasks]
    risks_data = [{
        "entry_id": risk.entry_id,
        "title": risk.title,
        "impact": risk.impact.value,
        "probability": risk.probability.value,
        "mitigation": risk.mitigation,
        "status": risk.status.value
    } for risk in risks]
    decisions_data = [{
        "entry_id": decision.entry_id,
        "title": decision.title,
        "rationale": decision.rationale,
        "decided_by": str(decision.decided_by)
    } for decision in decisions]

    # Update Proyecto Max
    gemini_service = GeminiService(request.gemini_api_key)
    drive_service = DriveService()
    updater = ProyectoMaxUpdater(gemini_service, drive_service)

    result = await updater.update_proyecto_max(
        project_id=str(project.id),
        project_name=project.name,
        daily_logs=daily_logs_data,
        tasks=tasks_data,
        risks=risks_data,
        decisions=decisions_data,
        gemini_api_key=request.gemini_api_key
    )

    return result


@router.post("/{project_id}/proyecto-max/generate")
async def generate_proyecto_max_complete(
    project_id: str,
    request: ProyectoMaxGenerateRequest,
    user_email: str,
    db: Session = Depends(get_db)
):
    """
    Generate complete Proyecto Max document (Opción B)
    Called when user clicks "Generar Avance" button
    """
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # TODO: Gather all project data from all phases
    project_data = {
        "name": project.name,
        "description": project.description,
        "current_phase": project.current_phase,
        # Add more data as needed
    }

    # Generate complete document
    gemini_service = GeminiService(request.gemini_api_key)
    drive_service = DriveService()
    updater = ProyectoMaxUpdater(gemini_service, drive_service)

    document_content = updater.generate_proyecto_max_complete(
        project_data=project_data,
        gemini_api_key=request.gemini_api_key
    )

    return {
        "status": "success",
        "document_content": document_content,
        "timestamp": date.today().isoformat()
    }
