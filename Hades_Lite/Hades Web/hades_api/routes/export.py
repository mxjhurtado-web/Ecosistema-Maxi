"""
Endpoints para exportación a Google Drive.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models.job import Job
from ..services.drive import export_result_to_drive, validate_folder, DRIVE_FOLDER_ID

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/jobs/{job_id}/drive")
async def export_job_to_drive(
    job_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exporta manualmente un job a Google Drive.
    
    Útil si la exportación automática falló o se desactivó.
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
            detail="No tienes permiso para exportar este job"
        )
    
    # Verificar que esté completado
    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden exportar jobs completados"
        )
    
    # Verificar que tenga resultado
    if not job.result:
        raise HTTPException(
            status_code=400,
            detail="Job no tiene resultado para exportar"
        )
    
    # Exportar
    try:
        success, file_id, web_link, error = export_result_to_drive(
            job.result,
            job.user_email or current_user.get("email", "unknown"),
            str(job.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Error exportando a Drive: {error}"
            )
        
        # Actualizar job
        job.exported_to_drive = True
        job.drive_file_id = file_id
        job.drive_url = web_link
        db.commit()
        
        return {
            "message": "Exportado exitosamente a Google Drive",
            "file_id": file_id,
            "web_link": web_link
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@router.get("/drive/status")
async def check_drive_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Verifica el estado de la conexión con Google Drive.
    """
    try:
        success, error = validate_folder()
        
        if success:
            return {
                "status": "ok",
                "folder_id": DRIVE_FOLDER_ID,
                "message": "Conexión con Google Drive OK"
            }
        else:
            return {
                "status": "error",
                "folder_id": DRIVE_FOLDER_ID,
                "error": error
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
