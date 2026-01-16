#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared Database API endpoints for TEMIS
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.core.shared_db_manager import SharedDBManager


router = APIRouter()


class SharedModeRequest(BaseModel):
    """Request to enable/disable shared mode"""
    enable: bool
    user_email: str


class SyncRequest(BaseModel):
    """Request to sync database"""
    user_email: str


class BackupRequest(BaseModel):
    """Request to create backup"""
    reason: str = "manual"


class RestoreRequest(BaseModel):
    """Request to restore from backup"""
    backup_id: str


@router.post("/shared-mode")
def toggle_shared_mode(request: SharedModeRequest):
    """Enable or disable shared database mode"""
    try:
        db_manager = SharedDBManager()
        
        if request.enable:
            success = db_manager.enable_shared_mode()
            if success:
                return {
                    "status": "success",
                    "mode": "shared",
                    "message": "Modo compartido activado. La base de datos se sincronizará automáticamente cada 5 minutos."
                }
            else:
                raise HTTPException(status_code=500, detail="No se pudo activar el modo compartido")
        else:
            success = db_manager.disable_shared_mode()
            if success:
                return {
                    "status": "success",
                    "mode": "local",
                    "message": "Modo local activado. Los cambios solo se guardarán localmente."
                }
            else:
                raise HTTPException(status_code=500, detail="No se pudo desactivar el modo compartido")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/shared-mode/status")
def get_shared_mode_status():
    """Get current shared mode status"""
    try:
        db_manager = SharedDBManager()
        
        updates = db_manager.check_for_updates() if db_manager.mode == "shared" else {}
        
        return {
            "mode": db_manager.mode,
            "last_sync": db_manager.last_sync.isoformat() if db_manager.last_sync else None,
            "sync_interval": db_manager.sync_interval,
            "has_updates": updates.get("has_updates", False),
            "modified_by": updates.get("modified_by"),
            "modified_at": updates.get("modified_at")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/shared-mode/sync")
def sync_database(request: SyncRequest):
    """Manually sync database"""
    try:
        db_manager = SharedDBManager()
        
        if db_manager.mode != "shared":
            raise HTTPException(status_code=400, detail="Modo compartido no está activado")
        
        # Check for updates first
        updates = db_manager.check_for_updates()
        
        if updates.get("has_updates"):
            # Download updates from Drive
            success = db_manager.sync_from_drive()
            if not success:
                raise HTTPException(status_code=500, detail="Error al descargar actualizaciones")
            
            return {
                "status": "success",
                "action": "downloaded",
                "message": f"Actualizaciones descargadas (modificado por {updates.get('modified_by', 'unknown')})"
            }
        else:
            # Upload local changes
            success = db_manager.sync_to_drive(request.user_email)
            if not success:
                raise HTTPException(status_code=500, detail="Error al subir cambios")
            
            return {
                "status": "success",
                "action": "uploaded",
                "message": "Cambios subidos a Drive"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/shared-mode/backup")
def create_backup(request: BackupRequest):
    """Create manual backup"""
    try:
        db_manager = SharedDBManager()
        
        if db_manager.mode != "shared":
            raise HTTPException(status_code=400, detail="Modo compartido no está activado")
        
        backup_id = db_manager.create_backup(request.reason)
        
        if backup_id:
            return {
                "status": "success",
                "backup_id": backup_id,
                "message": "Backup creado exitosamente"
            }
        else:
            raise HTTPException(status_code=500, detail="Error al crear backup")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/shared-mode/backups")
def list_backups():
    """List available backups"""
    try:
        db_manager = SharedDBManager()
        
        if db_manager.mode != "shared":
            raise HTTPException(status_code=400, detail="Modo compartido no está activado")
        
        backups = db_manager.list_backups()
        
        return {
            "status": "success",
            "backups": backups,
            "count": len(backups)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/shared-mode/restore")
def restore_backup(request: RestoreRequest):
    """Restore from backup"""
    try:
        db_manager = SharedDBManager()
        
        if db_manager.mode != "shared":
            raise HTTPException(status_code=400, detail="Modo compartido no está activado")
        
        success = db_manager.restore_backup(request.backup_id)
        
        if success:
            return {
                "status": "success",
                "message": "Base de datos restaurada exitosamente"
            }
        else:
            raise HTTPException(status_code=500, detail="Error al restaurar backup")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
