#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chat router for TEMIS
Handles chat message persistence and Gemini AI integration
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

from backend.database import get_db
from backend.models.chat_message import ChatMessage
from backend.models.user import User
from backend.models.project import Project, ProjectMember
from backend.services.gemini_service import GeminiChatService

router = APIRouter()


# Schemas
class ChatMessageCreate(BaseModel):
    project_id: str
    message_date: str  # ISO format date
    role: str  # 'user' or 'assistant'
    content: str
    attachments: Optional[List[str]] = []


class ChatMessageResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    message_date: str
    role: str
    content: str
    attachments: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class GeminiRequest(BaseModel):
    project_id: str
    message: str
    context: Optional[str] = ""


@router.post("/message", response_model=ChatMessageResponse)
def save_message(
    message_data: ChatMessageCreate,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Save a chat message"""
    try:
        # Get user
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify user is member of project (or skip if no members table)
        try:
            member = db.query(ProjectMember).filter(
                ProjectMember.project_id == message_data.project_id,
                ProjectMember.user_id == user.id
            ).first()
            
            if not member:
                # If no member found, just log it but don't fail
                print(f"[WARNING] User {user_email} not found as member of project {message_data.project_id}, but allowing message save")
        except Exception as e:
            print(f"[WARNING] Could not verify project membership: {e}")
            # Continue anyway

        # Create message
        message = ChatMessage(
            project_id=message_data.project_id,
            user_id=user.id,
            message_date=datetime.fromisoformat(message_data.message_date).date(),
            role=message_data.role,
            content=message_data.content,
            attachments=message_data.attachments or []
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)

        return message
    
    except Exception as e:
        print(f"[ERROR] Failed to save chat message: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")


@router.get("/messages", response_model=List[ChatMessageResponse])
def get_messages(
    project_id: str,
    message_date: str,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Get chat messages for a specific date"""
    # Get user
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify user is member of project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="User is not a member of this project")

    # Get messages
    target_date = datetime.fromisoformat(message_date).date()
    messages = db.query(ChatMessage).filter(
        ChatMessage.project_id == project_id,
        ChatMessage.message_date == target_date
    ).order_by(ChatMessage.created_at).all()

    return messages


@router.post("/gemini")
def get_gemini_response(
    request: GeminiRequest,
    user_email: str,
    gemini_api_key: str,  # Passed from frontend
    db: Session = Depends(get_db)
):
    """Get AI response from Gemini"""
    # Get user
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify user is member of project
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == request.project_id,
        ProjectMember.user_id == user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="User is not a member of this project")

    # Get project info for context
    project = db.query(Project).filter(Project.id == request.project_id).first()
    
    try:
        # Initialize Gemini service with user's API key
        gemini_service = GeminiChatService(gemini_api_key)
        
        # Build context
        full_context = f"Proyecto: {project.name}\n"
        if project.description:
            full_context += f"Descripción: {project.description}\n"
        if request.context:
            full_context += f"\n{request.context}"
        
        # Get AI response
        response = gemini_service.get_response(request.message, full_context)
        
        return {"response": response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting Gemini response: {str(e)}")


@router.post("/analyze")
def analyze_project(
    request: GeminiRequest,
    user_email: str,
    gemini_api_key: str,
    db: Session = Depends(get_db)
):
    """Analyze project status and phases using Gemini"""
    from backend.models.phase import Phase
    
    # Get user and verify membership (same as above)
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == request.project_id,
        ProjectMember.user_id == user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="User is not a member of this project")

    # Get project info
    project = db.query(Project).filter(Project.id == request.project_id).first()
    
    # Get phases info
    phases = db.query(Phase).filter(Phase.project_id == request.project_id).order_by(Phase.phase_number).all()
    
    try:
        gemini_service = GeminiChatService(gemini_api_key)
        
        # Build detailed prompt
        prompt = f"""Eres TEMIS, el Asistente Experto en Gestión de Proyectos de esta organización.
Analiza la situación actual del proyecto "{project.name}" vs la Metodología TEMIS de 7 fases.

SOBRE EL PROYECTO:
- Nombre: {project.name}
- Descripción: {project.description or 'Sin descripción'}
- Roles definidos: {project.project_roles or 'Ninguno'}

ESTADO ACTUAL DE LAS FASES:
"""
        for phase in phases:
            status_emoji = {
                "not_started": "⏳",
                "in_progress": "🔄",
                "completed": "✅"
            }.get(phase.status.value, "❓")
            
            prompt += f"- {phase.name} (Fase {phase.phase_number}): {status_emoji} {phase.status.value.upper()}\n"
            if phase.description:
                prompt += f"  Detalle: {phase.description[:200]}\n"

        prompt += """
TAREA:
1. Identifica qué fases están estancadas (ej. si la Fase 0 está completada pero la 1 no ha iniciado).
2. Basado en la metodología, indica qué elementos críticos podrían estar FALTANDO (ej. Charter, Análisis de Stakeholders, etc).
3. Da una recomendación de "Acción del Día" para el usuario para mover el proyecto hacia adelante.

ESTRICTO FORMATO DE RESPUESTA:
### 📊 Informe de Situación
[Resumen de 2 líneas]

### 🚦 Semáforo de Fases
[Lista con emojis]

### 🔍 Detección de Faltantes (GAPS)
- [ ] Elemento 1: Por qué es importante...
- [ ] Elemento 2: ...

### 💡 Sugerencias de Acción
1. **Acción 1**: ...
2. **Acción 2**: ...
"""
        
        # Get AI response
        response = gemini_service.get_response(prompt, "")
        
        return {"response": response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing project: {str(e)}")
