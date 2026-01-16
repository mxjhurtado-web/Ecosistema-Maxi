#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wizard and Suggestions Router for TEMIS
Handles conversational project creation and contextual suggestions
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime

from backend.database import get_db
from backend.models.user import User
from backend.models.project import Project, ProjectStatus, ProjectMember, ProjectMemberRole
from backend.models.phase import Phase, PhaseStatus, PHASE_NAMES
from backend.services.project_wizard import ProjectWizardService
from backend.services.project_suggestions import ProjectSuggestionsService

router = APIRouter(prefix="/api/wizard", tags=["wizard"])

# Initialize services
wizard_service = ProjectWizardService()
suggestions_service = ProjectSuggestionsService()


# Pydantic models
class WizardStartRequest(BaseModel):
    user_email: str


class WizardAnswerRequest(BaseModel):
    session_id: str
    answer: Any


class DailyStandupRequest(BaseModel):
    project_id: str
    user_email: str
    yesterday: str
    today: str
    blockers: Optional[str] = None


@router.post("/start")
def start_wizard(request: WizardStartRequest, db: Session = Depends(get_db)):
    """Start a new project creation wizard session"""
    user = db.query(User).filter(User.email == request.user_email).first()
    
    # If user not found by email, try to get the first user (for development)
    if not user:
        print(f"[WARNING] User not found with email: {request.user_email}")
        user = db.query(User).first()
        if user:
            print(f"[INFO] Using first available user: {user.email}")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = wizard_service.start_wizard(user.id)
    return result


@router.post("/answer")
def process_wizard_answer(request: WizardAnswerRequest, db: Session = Depends(get_db)):
    """Process wizard answer and get next step"""
    result = wizard_service.process_answer(request.session_id, request.answer)
    
    # If wizard is completed, create the project
    if result.get("completed"):
        project_data = result["project_data"]
        
        # Get user from session
        session = wizard_service.sessions.get(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        user = db.query(User).filter(User.id == session["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create project
        project = Project(
            name=project_data.get("project_name"),
            description=project_data.get("objective"),
            status=ProjectStatus.ACTIVE,
            created_by=user.id
        )
        db.add(project)
        db.flush()
        
        # Add owner
        project_member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectMemberRole.OWNER
        )
        db.add(project_member)
        
        # Create 7 phases
        import json
        for phase_num in range(1, 8):
            phase = Phase(
                project_id=project.id,
                phase_number=phase_num,
                name=PHASE_NAMES.get(phase_num),
                status=PhaseStatus.NOT_STARTED,
                progress=0,
                description=f"Fase {phase_num}: {PHASE_NAMES.get(phase_num)}",
                tasks=json.dumps([], ensure_ascii=False),
                deliverables=json.dumps([], ensure_ascii=False)
            )
            db.add(phase)
        
        # Store roles as JSON
        roles = []
        if project_data.get("sponsor_name"):
            roles.append({
                "name": project_data["sponsor_name"],
                "position": "Sponsor del Proyecto",
                "responsibilities": "Autorización y patrocinio ejecutivo"
            })
        if project_data.get("project_lead"):
            roles.append({
                "name": project_data["project_lead"],
                "position": "Project Lead",
                "responsibilities": "Gestión integral del proyecto"
            })
        
        project.project_roles = json.dumps(roles, ensure_ascii=False)
        
        db.commit()
        db.refresh(project)
        
        # Clean up session
        del wizard_service.sessions[request.session_id]
        
        return {
            "completed": True,
            "project_id": project.id,
            "project_name": project.name,
            "message": result["step"]["message"]
        }
    
    return result


@router.get("/projects/{project_id}/suggestions")
def get_project_suggestions(
    project_id: str,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Get contextual suggestions for a project"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get phases
    phases = db.query(Phase).filter(Phase.project_id == project_id).all()
    
    # Generate suggestions
    suggestions = suggestions_service.get_suggestions(project, phases)
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "suggestions": suggestions
    }


@router.get("/projects/{project_id}/daily-standup")
def get_daily_standup_questions(
    project_id: str,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Get Daily Standup questions for a project"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Find current phase (first in-progress or not-started)
    phases = db.query(Phase).filter(Phase.project_id == project_id).order_by(Phase.phase_number).all()
    current_phase = next((p for p in phases if p.progress < 100), phases[0] if phases else None)
    
    if not current_phase:
        raise HTTPException(status_code=404, detail="No active phase found")
    
    questions = suggestions_service.get_daily_standup_questions(project, current_phase)
    return questions


@router.post("/projects/{project_id}/daily-standup")
def submit_daily_standup(
    project_id: str,
    request: DailyStandupRequest,
    db: Session = Depends(get_db)
):
    """Submit Daily Standup responses"""
    from backend.models.chat_message import ChatMessage
    
    user = db.query(User).filter(User.email == request.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create chat message with standup summary
    standup_summary = f"""📅 **Daily Standup - {datetime.now().strftime('%d/%m/%Y')}**

✅ **Ayer:**
{request.yesterday}

🎯 **Hoy:**
{request.today}
"""
    
    if request.blockers:
        standup_summary += f"""
⚠️ **Bloqueos:**
{request.blockers}
"""
    
    message = ChatMessage(
        project_id=project_id,
        user_id=user.id,
        content=standup_summary,
        is_ai=False
    )
    db.add(message)
    db.commit()
    
    return {
        "status": "success",
        "message": "Daily Standup registrado correctamente"
    }
