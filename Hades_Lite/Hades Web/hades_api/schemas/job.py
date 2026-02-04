"""
Schemas Pydantic para Jobs.
"""

from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional, Dict, Any


class JobCreate(BaseModel):
    """Schema para crear un job"""
    auto_export: bool = Field(default=True, description="Exportar automáticamente a Drive")


class JobResponse(BaseModel):
    """Schema de respuesta básica de job"""
    id: UUID4
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class JobResult(BaseModel):
    """Schema del resultado completo de un job"""
    id: UUID4
    status: str
    
    # Resultado del análisis
    result: Optional[Dict[str, Any]] = None
    
    # Exportación
    exported_to_drive: bool
    drive_file_id: Optional[str] = None
    drive_url: Optional[str] = None
    
    # Metadata
    country_detected: Optional[str] = None
    semaforo: Optional[str] = None
    score: Optional[int] = None
    name_extracted: Optional[str] = None
    id_number_extracted: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class JobListItem(BaseModel):
    """Schema para lista de jobs (sin resultado completo)"""
    id: UUID4
    status: str
    country_detected: Optional[str] = None
    semaforo: Optional[str] = None
    name_extracted: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
