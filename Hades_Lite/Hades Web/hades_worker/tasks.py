"""
Tareas de Celery para procesamiento de documentos.
"""

from celery import Task
from datetime import datetime
import sys
from pathlib import Path
from typing import Optional

from .celery_app import celery_app
from .config import settings

# Agregar paths para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importar después de agregar al path
from hades_core.analyzer import analyze_image
from hades_api.services.drive import export_result_to_drive
from hades_api.database import SessionLocal
from hades_api.models.job import Job, JobStatus


class DatabaseTask(Task):
    """
    Task base con manejo de sesión de base de datos.
    
    Asegura que la sesión se cierre correctamente después de cada tarea.
    """
    _db = None
    
    @property
    def db(self):
        """Obtiene o crea una sesión de DB"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        """Cierra la sesión después de retornar"""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    max_retries=settings.TASK_MAX_RETRIES,
    default_retry_delay=settings.TASK_RETRY_DELAY,
    name='hades_worker.process_image'
)
def process_image_task(
    self,
    job_id: str,
    image_bytes: bytes,
    auto_export: bool = True,
    user_email: Optional[str] = None
):
    """
    Tarea de procesamiento de imagen de documento.
    
    Args:
        self: Task instance (bind=True)
        job_id: UUID del job como string
        image_bytes: Bytes de la imagen
        auto_export: Si debe exportar a Drive automáticamente
        user_email: Email del usuario para exportación
        
    Returns:
        Dict con resultado del procesamiento
        
    Raises:
        Exception: Si falla después de todos los reintentos
    """
    try:
        # 1. Obtener job de la DB
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} no encontrado en la base de datos")
        
        # 2. Actualizar estado a PROCESSING
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        self.db.commit()
        
        print(f"[{job_id}] Iniciando análisis de imagen...")
        
        # 3. Analizar imagen con hades_core
        result = analyze_image(
            image_bytes,
            gemini_api_key=settings.GEMINI_API_KEY,
            config={"auto_translate": True}
        )
        
        print(f"[{job_id}] Análisis completado. Semáforo: {result.semaforo}")
        
        # 4. Convertir resultado a dict
        result_dict = result.to_dict()
        
        # 5. Actualizar job con resultado
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.result = result_dict
        
        # 6. Extraer metadata para búsquedas rápidas
        job.country_detected = result.country_code
        job.semaforo = result.semaforo.value if result.semaforo else None
        job.score = result.score
        job.name_extracted = result.name
        job.id_number_extracted = result.id_number
        
        self.db.commit()
        
        print(f"[{job_id}] Job actualizado en DB")
        
        # 7. Exportar a Drive (si auto_export)
        if auto_export and user_email:
            try:
                print(f"[{job_id}] Exportando a Google Drive...")
                
                success, file_id, web_link, error = export_result_to_drive(
                    result_dict,
                    user_email,
                    job_id
                )
                
                if success:
                    job.exported_to_drive = True
                    job.drive_file_id = file_id
                    job.drive_url = web_link
                    self.db.commit()
                    print(f"[{job_id}] Exportado a Drive: {file_id}")
                else:
                    print(f"[{job_id}] Error exportando a Drive: {error}")
                    
            except Exception as e:
                # No fallar la tarea si Drive falla
                print(f"[{job_id}] Excepción exportando a Drive: {e}")
        
        # 8. Retornar resultado
        return {
            "job_id": job_id,
            "status": "completed",
            "semaforo": job.semaforo,
            "score": job.score,
            "country": job.country_detected,
            "exported": job.exported_to_drive
        }
        
    except Exception as e:
        print(f"[{job_id}] Error en procesamiento: {e}")
        
        # Marcar job como fallido
        try:
            job = self.db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                self.db.commit()
        except Exception as db_error:
            print(f"[{job_id}] Error actualizando job fallido: {db_error}")
        
        # Retry si no hemos alcanzado el máximo
        if self.request.retries < self.max_retries:
            print(f"[{job_id}] Reintentando... (intento {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        # Si ya no hay más reintentos, propagar el error
        print(f"[{job_id}] Falló después de {self.max_retries} reintentos")
        raise


@celery_app.task(name='hades_worker.export_to_drive')
def export_to_drive_task(
    job_id: str,
    result_dict: dict,
    user_email: str
):
    """
    Tarea separada para exportar a Drive.
    
    Útil para exportación manual o re-exportación.
    
    Args:
        job_id: UUID del job
        result_dict: Resultado del análisis
        user_email: Email del usuario
        
    Returns:
        Dict con resultado de la exportación
    """
    try:
        print(f"[{job_id}] Iniciando exportación a Drive...")
        
        success, file_id, web_link, error = export_result_to_drive(
            result_dict,
            user_email,
            job_id
        )
        
        if success:
            # Actualizar job en DB
            db = SessionLocal()
            try:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    job.exported_to_drive = True
                    job.drive_file_id = file_id
                    job.drive_url = web_link
                    db.commit()
                    print(f"[{job_id}] Exportación exitosa: {file_id}")
            finally:
                db.close()
            
            return {
                "job_id": job_id,
                "success": True,
                "file_id": file_id,
                "web_link": web_link
            }
        else:
            print(f"[{job_id}] Error en exportación: {error}")
            return {
                "job_id": job_id,
                "success": False,
                "error": error
            }
            
    except Exception as e:
        print(f"[{job_id}] Excepción en exportación: {e}")
        return {
            "job_id": job_id,
            "success": False,
            "error": str(e)
        }
