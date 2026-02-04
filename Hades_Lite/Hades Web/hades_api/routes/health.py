"""
Endpoints de health check.
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Retorna el estado del servicio.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "hades-api"
    }


@router.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "service": "Hades API",
        "version": "1.0.0",
        "description": "API para análisis forense de documentos"
    }
