#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EOD (End of Day) processing router for TEMIS
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

from backend.database import get_db
from backend.models.user import User
from backend.models.daily_log import DailyLog
from backend.models.task import Task, TaskStatus, TaskPriority, TaskSource
from backend.models.risk import Risk, RiskImpact, RiskProbability, RiskStatus, RiskSource
from backend.models.decision import Decision, DecisionSource
from backend.services.gemini_service import GeminiService

router = APIRouter()


class EODProcessRequest(BaseModel):
    """EOD process request"""
    log_date: date
    gemini_api_key: str
    force: bool = False  # Force reprocessing


class EODProcessResponse(BaseModel):
    """EOD process response"""
    status: str
    processed_at: datetime
    summary: dict


@router.post("/{project_id}/eod-process", response_model=EODProcessResponse)
def process_eod(
    project_id: str,
    eod_data: EODProcessRequest,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Process End of Day - Extract tasks/risks/decisions from daily log"""
    
    # Get user
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get daily log
    daily_log = db.query(DailyLog).filter(
        DailyLog.project_id == project_id,
        DailyLog.log_date == eod_data.log_date
    ).first()

    if not daily_log:
        raise HTTPException(status_code=404, detail="Daily log not found for this date")

    # Check if already processed
    if daily_log.processed and not eod_data.force:
        return {
            "status": "already_processed",
            "processed_at": daily_log.processed_at,
            "summary": {"message": "Daily log already processed. Use force=true to reprocess."}
        }

    # Process with Gemini
    gemini_service = GeminiService(eod_data.gemini_api_key)
    result = gemini_service.process_daily_log(daily_log.content)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to process daily log with Gemini")

    # Counters
    tasks_created = 0
    tasks_updated = 0
    risks_created = 0
    decisions_created = 0

    # Process tasks
    for task_data in result.get("tasks", []):
        entry_id = task_data.get("entry_id")
        action = task_data.get("action", "create")

        # Check if task exists
        existing_task = db.query(Task).filter(
            Task.project_id == project_id,
            Task.entry_id == entry_id
        ).first()

        if existing_task and action in ["update", "close"]:
            # Update existing task
            existing_task.title = task_data.get("title", existing_task.title)
            existing_task.description = task_data.get("description", existing_task.description)
            existing_task.status = TaskStatus(task_data.get("status", existing_task.status.value))
            existing_task.priority = TaskPriority(task_data.get("priority", existing_task.priority.value))
            existing_task.updated_at = datetime.utcnow()
            tasks_updated += 1
        elif not existing_task:
            # Create new task
            task = Task(
                project_id=project_id,
                entry_id=entry_id,
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                status=TaskStatus(task_data.get("status", "todo")),
                priority=TaskPriority(task_data.get("priority", "medium")),
                source=TaskSource.GEMINI_EXTRACTED,
                daily_log_id=daily_log.id
            )
            db.add(task)
            tasks_created += 1

    # Process risks
    for risk_data in result.get("risks", []):
        entry_id = risk_data.get("entry_id")
        
        # Check if risk exists
        existing_risk = db.query(Risk).filter(
            Risk.project_id == project_id,
            Risk.entry_id == entry_id
        ).first()

        if not existing_risk:
            # Create new risk
            risk = Risk(
                project_id=project_id,
                entry_id=entry_id,
                title=risk_data.get("title", ""),
                description=risk_data.get("description", ""),
                impact=RiskImpact(risk_data.get("impact", "medium")),
                probability=RiskProbability(risk_data.get("probability", "medium")),
                mitigation=risk_data.get("mitigation", ""),
                source=RiskSource.GEMINI_EXTRACTED,
                daily_log_id=daily_log.id
            )
            db.add(risk)
            risks_created += 1

    # Process decisions
    for decision_data in result.get("decisions", []):
        entry_id = decision_data.get("entry_id")
        
        # Check if decision exists
        existing_decision = db.query(Decision).filter(
            Decision.project_id == project_id,
            Decision.entry_id == entry_id
        ).first()

        if not existing_decision:
            # Create new decision
            decision = Decision(
                project_id=project_id,
                entry_id=entry_id,
                title=decision_data.get("title", ""),
                description=decision_data.get("description", ""),
                rationale=decision_data.get("rationale", ""),
                decided_by=user.id,
                source=DecisionSource.GEMINI_EXTRACTED,
                daily_log_id=daily_log.id
            )
            db.add(decision)
            decisions_created += 1

    # Mark daily log as processed
    daily_log.processed = True
    daily_log.processed_at = datetime.utcnow()

    # Commit all changes
    db.commit()

    return {
        "status": "success",
        "processed_at": daily_log.processed_at,
        "summary": {
            "tasks_created": tasks_created,
            "tasks_updated": tasks_updated,
            "risks_created": risks_created,
            "decisions_created": decisions_created,
            "gemini_summary": result.get("summary", ""),
            "next_steps": result.get("next_steps", []),
            "blockers": result.get("blockers", []),
            "alerts": result.get("alerts", [])
        }
    }


@router.post("/process-chat-daily")
def process_chat_daily(
    project_id: str,
    date_str: str,
    user_email: str,
    gemini_api_key: str,
    db: Session = Depends(get_db)
):
    """
    Process daily chat messages for EOD
    - Get all chat messages from the day
    - Save conversation to Drive
    - Process with Gemini to extract tasks/risks/decisions
    - Return summary
    """
    from backend.models.chat_message import ChatMessage
    from backend.models.project import Project
    from backend.services.drive_service import DriveService
    from backend.services.gemini_service import GeminiChatService
    from datetime import date as date_type
    
    # Get user
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Parse date
    try:
        target_date = date_type.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get all messages from this date
    messages = db.query(ChatMessage).filter(
        ChatMessage.project_id == project_id,
        ChatMessage.message_date == target_date
    ).order_by(ChatMessage.created_at).all()
    
    if not messages:
        return {
            "status": "no_messages",
            "message": "No messages found for this date"
        }
    
    # Convert messages to dict for Drive backup
    messages_data = []
    conversation_text = ""
    
    for msg in messages:
        msg_dict = {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat()
        }
        messages_data.append(msg_dict)
        
        # Build conversation text for Gemini
        sender = "Usuario" if msg.role == "user" else "TEMIS"
        conversation_text += f"{sender}: {msg.content}\n\n"
    
    # Save conversation to Drive
    drive_saved = False
    if project.drive_folder_id:
        try:
            drive_service = DriveService()
            success, result = drive_service.save_conversation_to_drive(
                project.drive_folder_id,
                date_str,
                messages_data
            )
            drive_saved = success
            if not success:
                print(f"[WARNING] Could not save to Drive: {result}")
        except Exception as e:
            print(f"[WARNING] Drive service error: {e}")
    
    # Process with Gemini to extract insights
    summary_text = ""
    try:
        gemini_service = GeminiChatService(gemini_api_key)
        
        analysis_prompt = f"""
Analiza la siguiente conversación del día {date_str} y extrae:

1. Resumen ejecutivo (2-3 líneas)
2. Tareas mencionadas o completadas
3. Riesgos o bloqueadores identificados
4. Decisiones tomadas
5. Próximos pasos

Conversación:
{conversation_text}

Responde en formato estructurado y conciso.
"""
        
        summary_text = gemini_service.get_response(analysis_prompt, "")
        
    except Exception as e:
        print(f"[WARNING] Gemini analysis error: {e}")
        summary_text = "No se pudo generar análisis automático"
    
    return {
        "status": "success",
        "processed_at": datetime.utcnow().isoformat(),
        "message_count": len(messages),
        "drive_backup": drive_saved,
        "summary": summary_text
    }
