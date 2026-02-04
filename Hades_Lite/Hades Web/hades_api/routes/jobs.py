"""
Endpoints para gestión de jobs.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from ..auth.dependencies import get_current_user, require_analyst
from ..database import get_db
from ..models.job import Job, JobStatus
from ..schemas.job import JobCreate, JobResponse, JobResult, JobListItem
from ..config import settings

# Importar hades_core
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from hades_core.analyzer import analyze_image

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=JobResponse, status_code=201)
async def create_job(
    image: UploadFile = File(..., description="Imagen del documento"),
    auto_export: bool = Query(default=True, description="Exportar automáticamente a Drive"),
    current_user: dict = Depends(require_analyst),
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo job de análisis.
    
    Proceso:
    1. Valida la imagen
    2. Crea el job en DB
    3. Procesa la imagen (sync o async según ASYNC_PROCESSING)
    4. Actualiza el resultado
    
    Requiere rol: hades_analyst o hades_admin
    """
    # Validar tamaño
    contents = await image.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Imagen muy grande. Máximo: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # Validar tipo
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )
    
    # Crear job en DB
    job = Job(
        user_id=current_user["user_id"],
        user_email=current_user.get("email"),
        user_name=current_user.get("name"),
        status=JobStatus.QUEUED
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # PROCESAMIENTO: Sync vs Async (TOGGLE)
    if settings.ASYNC_PROCESSING:
        # ============================================================
        # MODO ASÍNCRONO (Celery)
        # ============================================================
        try:
            from hades_worker.tasks import process_image_task
            
            # Enviar tarea a Celery
            task = process_image_task.delay(
                job_id=str(job.id),
                image_bytes=contents,
                auto_export=auto_export,
                user_email=current_user.get("email")
            )
            
            # Guardar task_id para tracking
            job.celery_task_id = task.id
            db.commit()
            db.refresh(job)
            
            print(f"[{job.id}] Enviado a Celery. Task ID: {task.id}")
            
        except Exception as e:
            # Si falla Celery, marcar como fallido
            job.status = JobStatus.FAILED
            job.error_message = f"Error enviando a Celery: {str(e)}"
            job.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(job)
    
    else:
        # ============================================================
        # MODO SÍNCRONO (Procesamiento inmediato)
        # ============================================================
        try:
            # Actualizar a processing
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            db.commit()
            
            # Analizar imagen
            result = analyze_image(
                contents,
                gemini_api_key=settings.GEMINI_API_KEY,
                config={"auto_translate": True}
            )
            
            # Convertir a dict
            result_dict = result.to_dict()
            
            # Actualizar job
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result_dict
            
            # Extraer metadata para búsquedas
            job.country_detected = result.country_code
            job.semaforo = result.semaforo.value if result.semaforo else None
            job.score = result.score
            job.name_extracted = result.name
            job.id_number_extracted = result.id_number
            
            db.commit()
            
            # Exportar a Drive (si auto_export)
            if auto_export:
                try:
                    from ..services.drive import export_result_to_drive
                    
                    success, file_id, web_link, error = export_result_to_drive(
                        result_dict,
                        current_user.get("email", "unknown"),
                        str(job.id)
                    )
                    
                    if success:
                        job.exported_to_drive = True
                        job.drive_file_id = file_id
                        job.drive_url = web_link
                        db.commit()
                        
                except Exception as e:
                    # No fallar si Drive falla, solo loggear
                    print(f"Error exportando a Drive: {e}")
            
            db.refresh(job)
            
        except Exception as e:
            # Marcar como fallido
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(job)
    
    return job


@router.get("/{job_id}", response_model=JobResult)
async def get_job(
    job_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el resultado completo de un job.
    
    Solo puede ver sus propios jobs (excepto admins).
    """
    # Buscar job
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    # Verificar permisos
    is_admin = "hades_admin" in current_user.get("roles", [])
    if not is_admin and job.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para ver este job"
        )
    
    return job


@router.get("/", response_model=List[JobListItem])
async def list_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    country: Optional[str] = Query(default=None, description="Filtrar por país"),
    semaforo: Optional[str] = Query(default=None, description="Filtrar por semáforo"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista los jobs del usuario actual.
    
    Soporta paginación y filtros.
    """
    # Query base
    query = db.query(Job).filter(Job.user_id == current_user["user_id"])
    
    # Filtros
    if country:
        query = query.filter(Job.country_detected == country)
    if semaforo:
        query = query.filter(Job.semaforo == semaforo)
    
    # Ordenar y paginar
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    
    return jobs


@router.delete("/{job_id}")
async def delete_job(
    job_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Elimina un job.
    
    Solo puede eliminar sus propios jobs.
    """
    # Buscar job
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user["user_id"]
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    # Eliminar
    db.delete(job)
    db.commit()
    
    return {"message": "Job eliminado exitosamente"}
