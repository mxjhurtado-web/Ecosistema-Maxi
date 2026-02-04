"""
Endpoints del panel de administración.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from ..auth.dependencies import require_admin
from ..database import get_db
from ..models.job import Job, JobStatus
from ..schemas.job import JobListItem

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_stats(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Estadísticas generales del sistema.
    
    Solo para admins.
    
    Retorna:
    - Total de jobs
    - Jobs por estado
    - Jobs por país
    - Jobs por semáforo
    - Jobs por usuario
    """
    # Total de jobs
    total_jobs = db.query(func.count(Job.id)).scalar()
    
    # Por estado
    jobs_by_status = db.query(
        Job.status,
        func.count(Job.id)
    ).group_by(Job.status).all()
    
    # Por país
    jobs_by_country = db.query(
        Job.country_detected,
        func.count(Job.id)
    ).filter(Job.country_detected.isnot(None)).group_by(Job.country_detected).all()
    
    # Por semáforo
    jobs_by_semaforo = db.query(
        Job.semaforo,
        func.count(Job.id)
    ).filter(Job.semaforo.isnot(None)).group_by(Job.semaforo).all()
    
    # Por usuario (top 10)
    jobs_by_user = db.query(
        Job.user_email,
        func.count(Job.id).label("count")
    ).filter(Job.user_email.isnot(None)).group_by(Job.user_email).order_by(
        func.count(Job.id).desc()
    ).limit(10).all()
    
    # Score promedio
    avg_score = db.query(func.avg(Job.score)).filter(Job.score.isnot(None)).scalar()
    
    return {
        "total_jobs": total_jobs,
        "by_status": {str(status): count for status, count in jobs_by_status},
        "by_country": {country: count for country, count in jobs_by_country},
        "by_semaforo": {semaforo: count for semaforo, count in jobs_by_semaforo},
        "by_user": [{"email": email, "count": count} for email, count in jobs_by_user],
        "avg_score": round(avg_score, 2) if avg_score else 0
    }


@router.get("/jobs", response_model=List[JobListItem])
async def get_all_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    country: Optional[str] = Query(default=None),
    semaforo: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    user_email: Optional[str] = Query(default=None),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Ver todos los jobs del sistema con filtros.
    
    Solo para admins.
    """
    # Query base
    query = db.query(Job)
    
    # Filtros
    if country:
        query = query.filter(Job.country_detected == country)
    if semaforo:
        query = query.filter(Job.semaforo == semaforo)
    if status:
        query = query.filter(Job.status == status)
    if user_email:
        query = query.filter(Job.user_email.ilike(f"%{user_email}%"))
    
    # Ordenar y paginar
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    
    return jobs


@router.get("/users")
async def get_users_stats(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Estadísticas de usuarios.
    
    Solo para admins.
    """
    users = db.query(
        Job.user_email,
        Job.user_name,
        func.count(Job.id).label("total_jobs"),
        func.count(func.nullif(Job.status == JobStatus.COMPLETED, False)).label("completed"),
        func.count(func.nullif(Job.status == JobStatus.FAILED, False)).label("failed")
    ).filter(Job.user_email.isnot(None)).group_by(
        Job.user_email, Job.user_name
    ).order_by(func.count(Job.id).desc()).all()
    
    return [
        {
            "email": email,
            "name": name,
            "total_jobs": total,
            "completed": completed,
            "failed": failed
        }
        for email, name, total, completed, failed in users
    ]
