#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projects router for TEMIS
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.database import get_db
from backend.models.user import User
from backend.models.project import Project, ProjectStatus, ProjectMember, ProjectMemberRole
from backend.models.phase import Phase, PhaseStatus, PHASE_NAMES
from backend.services.drive_service import DriveService

router = APIRouter()


class ProjectCreate(BaseModel):
    """Project creation request"""
    name: str
    description: Optional[str] = None
    group_id: Optional[str] = None


class ProjectImport(BaseModel):
    """Project import request"""
    project_code: str
    user_email: str


class ProjectFromDocument(BaseModel):
    """Create project from document request"""
    project_name: str
    file_content: str
    file_extension: str
    gemini_api_key: str
    user_email: str


class ProjectFromDocumentUpdate(BaseModel):
    """Update project from document request"""
    file_content: str
    file_extension: str
    gemini_api_key: str
    user_email: str


class PhaseResponse(BaseModel):
    """Phase response"""
    id: str
    phase_number: int
    name: str
    description: Optional[str]
    status: str
    progress: int
    tasks: Optional[str]
    deliverables: Optional[str]

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    """Project response"""
    id: str
    name: str
    description: Optional[str]
    status: str
    current_phase: int
    drive_folder_id: Optional[str]
    project_roles: Optional[str]
    created_at: datetime
    updated_at: datetime
    phases: List[PhaseResponse] = []

    class Config:
        from_attributes = True


@router.post("/", response_model=ProjectResponse)
def create_project(
    project_data: ProjectCreate,
    user_email: str,  # From auth middleware
    db: Session = Depends(get_db)
):
    """Create new project"""
    # Get user
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create project
    project = Project(
        name=project_data.name,
        description=project_data.description,
        group_id=project_data.group_id if project_data.group_id else None,
        created_by=user.id
    )
    db.add(project)
    db.flush()  # Get project ID

    print(f"[DEBUG] Creating project: {project.name}")

    # Add creator as owner
    print(f"[DEBUG] Adding owner for project: {project.name}")
    project_member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectMemberRole.OWNER
    )
    db.add(project_member)
    print(f"[DEBUG] Owner added to session")

    # Create 7 phases
    print(f"[DEBUG] Creating 7 phases...")
    try:
        for phase_num in range(1, 8):
            phase_name = PHASE_NAMES[phase_num]
            print(f"[DEBUG] Creating phase {phase_num}: {phase_name}")
            phase = Phase(
                project_id=project.id,
                phase_number=phase_num,
                name=phase_name,
                status=PhaseStatus.NOT_STARTED
            )
            db.add(phase)
        print(f"[DEBUG] All 7 phases added to session")
    except Exception as e:
        import traceback
        print(f"[ERROR] Error creating phases: {str(e)}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating phases: {str(e)}")

    # Create Drive folder
    try:
        from backend.services.drive_service import DriveService
        drive_service = DriveService()
        success, folder_id = drive_service.create_project_folder(project.name, str(project.id)[:8])
        
        if success:
            project.drive_folder_id = folder_id
            print(f"[OK] Drive folder created: {folder_id}")
        else:
            print(f"[WARNING] Could not create Drive folder: {folder_id}")
    except Exception as e:
        print(f"[WARNING] Drive service not available: {e}")

    # Commit all changes
    try:
        print(f"[DEBUG] About to commit project: {project.name}")
        db.commit()
        db.refresh(project)
        print(f"[OK] Project created successfully: {project.id} - {project.name}")
        print(f"[OK] Owner added: {user.email}")
        print(f"[OK] Phases created: 7")
    except Exception as e:
        import traceback
        print(f"[ERROR] Error committing project: {str(e)}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        print(f"[ERROR] Traceback:")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")

    return project


@router.post("/create-from-document")
async def create_project_from_document(
    request: ProjectFromDocument,
    db: Session = Depends(get_db)
):
    """
    Create project from document analysis
    Gemini analyzes the document and distributes content across 7 phases
    """
    import base64
    from backend.services.document_parser import DocumentParser
    from backend.services.gemini_document_analyzer import GeminiDocumentAnalyzer
    
    # Get user
    user = db.query(User).filter(User.email == request.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Decode file content
        file_bytes = base64.b64decode(request.file_content)
        
        # Extract text from document
        print(f"[DEBUG] Extracting text from {request.file_extension} file...")
        text = DocumentParser.extract_text(file_bytes, request.file_extension)
        
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from document")
        
        print(f"[DEBUG] Extracted {len(text)} characters")
        
        # Analyze with Gemini
        print(f"[DEBUG] Analyzing document with Gemini...")
        analyzer = GeminiDocumentAnalyzer(request.gemini_api_key)
        analysis = analyzer.analyze_for_phases(text)
        
        print(f"[DEBUG] Analysis complete: {analysis.get('project_summary', 'N/A')}")
        
        # Extract roles
        roles_data = analysis.get('roles', [])
        import json
        
        # Create project
        project = Project(
            name=request.project_name,
            description=analysis.get('project_summary', ''),
            status=ProjectStatus.ACTIVE,
            project_roles=json.dumps(roles_data, ensure_ascii=False),
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
        
        # Create 7 phases with analysis data
        for phase_data in analysis.get('phases', []):
            phase_num = phase_data.get('phase_number', 1)  # 1-7 expected from prompt
            phase_name = PHASE_NAMES.get(phase_num, f"Fase {phase_num}")
            
            # Map analysis status to PhaseStatus enum
            status_map = {
                "completed": PhaseStatus.COMPLETED,
                "in_progress": PhaseStatus.IN_PROGRESS,
                "not_started": PhaseStatus.NOT_STARTED
            }
            phase_status = status_map.get(phase_data.get('status'), PhaseStatus.NOT_STARTED)
            
            phase = Phase(
                project_id=project.id,
                phase_number=phase_num,
                name=phase_name,
                status=phase_status,
                progress=phase_data.get('progress', 0),
                description=phase_data.get('description', ''),
                tasks=json.dumps(phase_data.get('tasks', []), ensure_ascii=False),
                deliverables=json.dumps(phase_data.get('deliverables', []), ensure_ascii=False)
            )
            db.add(phase)
        
        # Create Drive folder and analysis document
        try:
            from backend.services.drive_service import DriveService
            drive_service = DriveService()
            success, folder_id = drive_service.create_project_folder(project.name, str(project.id)[:8])
            
            if success:
                project.drive_folder_id = folder_id
                
                # 1. Create Analysis Document in Drive
                analysis_content = f"ANÁLISIS INICIAL DE PROYECTO - TEMIS\n"
                analysis_content += f"==================================\n\n"
                analysis_content += f"PROYECTO: {project.name}\n"
                analysis_content += f"RESUMEN: {project.description}\n\n"
                
                analysis_content += "ROLES IDENTIFICADOS:\n"
                for role in roles_data:
                    analysis_content += f"- {role.get('name')} ({role.get('position')}): {role.get('responsibilities')}\n"
                
                analysis_content += "\nELEMENTOS FALTANTES SEGÚN METODOLOGÍA:\n"
                for missing in analysis.get('missing_from_methodology', []):
                    analysis_content += f"- [ ] {missing}\n"
                
                drive_service.create_or_update_file(analysis_content, "00_Analisis_Inicial_Gemini.txt", folder_id)

                # 2. Create Phase Summaries in their respective folders
                phase_folders = {
                    1: "01_Diagnostico",
                    2: "02_Inicio",
                    3: "03_Planificacion",
                    4: "04_Ejecucion",
                    5: "05_Monitoreo",
                    6: "06_Mejora_Continua",
                    7: "07_Cierre"
                }

                for p_data in analysis.get('phases', []):
                    p_num = p_data.get('phase_number')
                    folder_name = phase_folders.get(p_num)
                    
                    if folder_name:
                        success_p, phase_folder_id = drive_service.ensure_folder_exists(folder_id, folder_name)
                        if success_p:
                            p_progress = p_data.get('progress', 0)
                            p_status = p_data.get('status', 'not_started')
                            p_desc = p_data.get('description', '')
                            p_tasks = p_data.get('tasks', [])
                            p_deliverables = p_data.get('deliverables', [])

                            summary = f"RESUMEN INICIAL DE FASE {p_num}: {p_data.get('phase_name')}\n"
                            summary += f"Estado: {p_status.upper()} | Progreso: {p_progress}%\n"
                            summary += f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                            summary += f"----------------------------------------------------------\n\n"
                            summary += f"ANÁLISIS DE LA IA:\n{p_desc}\n\n"
                            
                            summary += "ENTREGABLES DETECTADOS:\n"
                            for d in p_deliverables:
                                summary += f"- [x] {d}\n"
                            
                            summary += "\nCHECKLIST SUGERIDO:\n"
                            for t in p_tasks:
                                summary += f"- [ ] {t}\n"

                            drive_service.create_or_update_file(summary, "00_RESUMEN_INICIAL_FASE.txt", phase_folder_id)
                
        except Exception as e:
            print(f"[WARNING] Drive service error: {e}")
        
        # Commit
        db.commit()
        db.refresh(project)
        
        return {
            "status": "success",
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description
            },
            "analysis": analysis
        }
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Error creating project from document: {e}")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=ProjectResponse)
def import_project(
    import_data: ProjectImport,
    db: Session = Depends(get_db)
):
    """Import existing project by code"""
    # Validate user exists and is authenticated
    user = db.query(User).filter(User.email == import_data.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found or not authenticated")

    # Find project by code (project ID)
    project = db.query(Project).filter(Project.id == import_data.project_code).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found. Verify the code is correct.")

    # Check if user is already a member
    existing_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project.id,
        ProjectMember.user_id == user.id
    ).first()

    if existing_member:
        raise HTTPException(status_code=400, detail="You are already a member of this project")

    # Add user as member
    project_member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role=ProjectMemberRole.MEMBER
    )
    db.add(project_member)
    db.commit()

    return project


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    user_email: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List user's projects"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get projects where user is member
    query = db.query(Project).join(ProjectMember).filter(
        ProjectMember.user_id == user.id
    )

    if status:
        query = query.filter(Project.status == status)

    projects = query.all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Get project details"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if user has access
    is_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id
    ).first()

    if not is_member:
        raise HTTPException(status_code=403, detail="Access denied")

    return project


@router.delete('/{project_id}')
def delete_project(project_id: str, user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')
    is_owner = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user.id, ProjectMember.role == ProjectMemberRole.OWNER).first()
    if not is_owner:
        raise HTTPException(status_code=403, detail='Only owners can delete projects')
    db.delete(project)
    db.commit()
    return {'message': 'Project deleted successfully'}


@router.post("/{project_id}/update-from-document")
async def update_project_from_document(
    project_id: str,
    request: ProjectFromDocumentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing project from a new document
    """
    import base64
    from backend.services.document_parser import DocumentParser
    from backend.services.gemini_document_analyzer import GeminiDocumentAnalyzer
    from datetime import datetime
    from backend.models.phase import Phase, PhaseStatus, PHASE_NAMES
    
    # Get user
    user = db.query(User).filter(User.email == request.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # Decode and extract text
        file_bytes = base64.b64decode(request.file_content)
        text = DocumentParser.extract_text(file_bytes, request.file_extension)
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from document")
        
        # Analyze with Gemini
        analyzer = GeminiDocumentAnalyzer(request.gemini_api_key)
        analysis = analyzer.analyze_for_phases(text)
        
        # Update project info
        if analysis.get('project_summary'):
            project.description = analysis.get('project_summary')
        
        roles_data = analysis.get('roles', [])
        if roles_data:
            import json
            project.project_roles = json.dumps(roles_data, ensure_ascii=False)
        
        # Update phases
        print(f"[DEBUG] Updating phases for project {project_id}...")
        for phase_data in analysis.get('phases', []):
            phase_num = phase_data.get('phase_number', 1)
            
            # Map status
            status_map = {
                "completed": PhaseStatus.COMPLETED,
                "in_progress": PhaseStatus.IN_PROGRESS,
                "not_started": PhaseStatus.NOT_STARTED
            }
            new_status = status_map.get(phase_data.get('status'), PhaseStatus.NOT_STARTED)
            
            # Find and update phase
            phase = db.query(Phase).filter(Phase.project_id == project_id, Phase.phase_number == phase_num).first()
            if phase:
                print(f"[DEBUG] Updating Phase {phase_num}: Name={phase_data.get('phase_name')}, Progress={phase_data.get('progress')}%")
                phase.status = new_status
                phase.progress = phase_data.get('progress', 0)
                phase.name = phase_data.get('phase_name', phase.name)
                if phase_data.get('description'):
                    phase.description = phase_data.get('description')
                
                import json
                phase.tasks = json.dumps(phase_data.get('tasks', []), ensure_ascii=False)
                phase.deliverables = json.dumps(phase_data.get('deliverables', []), ensure_ascii=False)
                print(f"[DEBUG] Phase {phase_num} updated successfully")
            else:
                # Create phase if it doesn't exist
                print(f"[WARNING] Phase {phase_num} not found, creating it...")
                phase = Phase(
                    project_id=project_id,
                    phase_number=phase_num,
                    name=phase_data.get('phase_name', PHASE_NAMES.get(phase_num, f"Fase {phase_num}")),
                    status=new_status,
                    progress=phase_data.get('progress', 0),
                    description=phase_data.get('description', ''),
                    tasks=json.dumps(phase_data.get('tasks', []), ensure_ascii=False),
                    deliverables=json.dumps(phase_data.get('deliverables', []), ensure_ascii=False)
                )
                db.add(phase)
                print(f"[DEBUG] Phase {phase_num} created successfully")
        
        # Handle Drive operations
        if project.drive_folder_id:
            try:
                from backend.services.drive_service import DriveService
                drive_service = DriveService()
                
                # 1. Ensure "Documentos_Fuentes" folder exists and upload source
                success_f, source_folder_id = drive_service.ensure_folder_exists(project.drive_folder_id, "Documentos_Fuentes")
                if success_f:
                    import tempfile
                    import os
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_orig_name = f"{timestamp}_Fuente{request.file_extension}"
                    
                    with tempfile.NamedTemporaryFile(delete=False) as tf:
                        tf.write(file_bytes)
                        temp_path = tf.name
                    
                    drive_service.upload_file(temp_path, file_orig_name, source_folder_id)
                    os.remove(temp_path)
                
                # 2. Update Global Analysis Document
                analysis_content = f"ACTUALIZACIÓN DE ANÁLISIS DE PROYECTO - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                analysis_content += f"==========================================================\n\n"
                analysis_content += f"PROYECTO: {project.name}\n"
                analysis_content += f"RESUMEN: {project.description}\n\n"
                
                analysis_content += "ROLES IDENTIFICADOS:\n"
                for role in roles_data:
                    analysis_content += f"- {role.get('name')} ({role.get('position')}): {role.get('responsibilities')}\n"
                
                analysis_content += "\nELEMENTOS FALTANTES SEGÚN METODOLOGÍA:\n"
                for missing in analysis.get('missing_from_methodology', []):
                    analysis_content += f"- [ ] {missing}\n"
                
                analysis_file_name = f"Analisis_Actualizado_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                drive_service.create_or_update_file(analysis_content, analysis_file_name, project.drive_folder_id)

                # 3. Create/Update Phase Summaries in their respective folders
                phase_folders = {
                    1: "01_Diagnostico",
                    2: "02_Inicio",
                    3: "03_Planificacion",
                    4: "04_Ejecucion",
                    5: "05_Monitoreo",
                    6: "06_Mejora_Continua",
                    7: "07_Cierre"
                }

                for phase_data in analysis.get('phases', []):
                    p_num = phase_data.get('phase_number')
                    folder_name = phase_folders.get(p_num)
                    
                    if folder_name:
                        # Find/Ensure folder exists
                        success_p, phase_folder_id = drive_service.ensure_folder_exists(project.drive_folder_id, folder_name)
                        if success_p:
                            p_progress = phase_data.get('progress', 0)
                            p_status = phase_data.get('status', 'not_started')
                            p_desc = phase_data.get('description', '')
                            p_tasks = phase_data.get('tasks', [])
                            p_deliverables = phase_data.get('deliverables', [])

                            summary = f"RESUMEN DE FASE {p_num}: {phase_data.get('phase_name')}\n"
                            summary += f"Estado: {p_status.upper()} | Progreso: {p_progress}%\n"
                            summary += f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                            summary += f"----------------------------------------------------------\n\n"
                            summary += f"DESCRIPCIÓN DEL ANÁLISIS:\n{p_desc}\n\n"
                            
                            summary += "EVIDENCIAS DETECTADAS / ENTREGABLES:\n"
                            for d in p_deliverables:
                                summary += f"- [x] {d}\n"
                            
                            summary += "\nTAREAS / CHECKLIST METODOLÓGICO:\n"
                            for t in p_tasks:
                                summary += f"- [ ] {t}\n"

                            drive_service.create_or_update_file(summary, "00_RESUMEN_EJECUTIVO_FASE.txt", phase_folder_id)
                
            except Exception as e:
                print(f"[WARNING] Drive update error: {e}")
                import traceback
                traceback.print_exc()

        # Commit changes
        db.commit()
        
        return {
            "status": "success",
            "message": "Project updated successfully from document",
            "analysis": analysis
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
