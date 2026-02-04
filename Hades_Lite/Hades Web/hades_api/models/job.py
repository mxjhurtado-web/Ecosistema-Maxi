"""
Modelo de Job para análisis de documentos.
"""

from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from ..database import Base


class JobStatus(str, enum.Enum):
    """Estados posibles de un job"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """
    Modelo de Job de análisis.
    
    Representa un análisis de documento en el sistema.
    """
    __tablename__ = "jobs"
    
    # ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Usuario (de Keycloak)
    user_id = Column(String, nullable=False, index=True)
    user_email = Column(String, nullable=True)
    user_name = Column(String, nullable=True)
    
    # Estado
    status = Column(
        SQLEnum(JobStatus),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True
    )
    
    # Resultado del análisis (JSON completo)
    result = Column(JSON, nullable=True)
    
    # Exportación a Drive
    exported_to_drive = Column(Boolean, default=False)
    drive_file_id = Column(String, nullable=True)
    drive_url = Column(String, nullable=True)
    
    # Metadata extraída (para búsquedas rápidas)
    country_detected = Column(String, nullable=True, index=True)
    semaforo = Column(String, nullable=True, index=True)  # verde/amarillo/rojo
    score = Column(Integer, nullable=True)
    name_extracted = Column(String, nullable=True)
    id_number_extracted = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error (si falla)
    error_message = Column(String, nullable=True)
    
    # Celery task ID (para tracking asíncrono)
    celery_task_id = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Job {self.id} - {self.status}>"
