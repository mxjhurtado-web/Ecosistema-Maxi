#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared Database Manager for TEMIS
Manages shared database in Google Drive for team collaboration
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import threading
import time

from backend.services.drive_service import DriveService


class SharedDBManager:
    """Manages shared database synchronization with Google Drive"""
    
    # Singleton instance
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.mode = "local"  # "local" or "shared"
            self.drive_service = None
            self.local_db_path = Path("temis.db")
            self.shared_folder_name = "TEMIS_Shared_DB"
            self.shared_folder_id = None
            self.db_file_id = None
            self.status_file_id = None
            self.last_sync = None
            self.sync_interval = 300  # 5 minutes
            self.sync_thread = None
            self.sync_running = False
            self.initialized = True
    
    def enable_shared_mode(self) -> bool:
        """Enable shared database mode"""
        try:
            # Initialize Drive service
            self.drive_service = DriveService()
            
            # Create or get shared folder
            self.shared_folder_id = self._get_or_create_shared_folder()
            
            # Get or create status file
            self.status_file_id = self._get_or_create_status_file()
            
            # Initial sync from Drive
            self.sync_from_drive()
            
            # Start auto-sync thread
            self.mode = "shared"
            self.start_auto_sync()
            
            return True
        except Exception as e:
            print(f"[SharedDB] Error enabling shared mode: {e}")
            return False
    
    def disable_shared_mode(self) -> bool:
        """Disable shared database mode"""
        try:
            # Stop auto-sync
            self.stop_auto_sync()
            
            # Final sync to Drive
            if self.mode == "shared":
                self.sync_to_drive()
            
            self.mode = "local"
            return True
        except Exception as e:
            print(f"[SharedDB] Error disabling shared mode: {e}")
            return False
    
    def sync_from_drive(self) -> bool:
        """Download database from Drive"""
        try:
            print("[SharedDB] Syncing from Drive...")
            
            # Get DB file from Drive
            db_file_id = self._get_db_file_id()
            
            if not db_file_id:
                print("[SharedDB] No shared DB found, uploading local DB")
                return self.sync_to_drive()
            
            # Create backup of local DB before downloading
            self._create_local_backup("before_download")
            
            # Download DB from Drive
            content = self.drive_service.download_file(db_file_id)
            
            if content:
                # Write to local DB
                with open(self.local_db_path, 'wb') as f:
                    f.write(content)
                
                self.last_sync = datetime.now()
                print("[SharedDB] ✓ Synced from Drive successfully")
                return True
            
            return False
        except Exception as e:
            print(f"[SharedDB] Error syncing from Drive: {e}")
            return False
    
    def sync_to_drive(self, user_email: str = "system") -> bool:
        """Upload database to Drive"""
        try:
            print("[SharedDB] Syncing to Drive...")
            
            # Create backup before upload
            backup_id = self.create_backup(f"auto_backup_{user_email}")
            
            # Check if DB file exists in Drive
            db_file_id = self._get_db_file_id()
            
            if db_file_id:
                # Update existing file
                with open(self.local_db_path, 'rb') as f:
                    self.drive_service.update_file(db_file_id, f.read())
            else:
                # Create new file
                with open(self.local_db_path, 'rb') as f:
                    db_file_id = self.drive_service.upload_file(
                        "temis_shared.db",
                        f.read(),
                        self.shared_folder_id,
                        "application/x-sqlite3"
                    )
                self.db_file_id = db_file_id
            
            # Update status file
            self._update_status({
                "last_modified_by": user_email,
                "last_modified_at": datetime.now().isoformat(),
                "last_backup_id": backup_id
            })
            
            self.last_sync = datetime.now()
            print("[SharedDB] ✓ Synced to Drive successfully")
            return True
        except Exception as e:
            print(f"[SharedDB] Error syncing to Drive: {e}")
            return False
    
    def create_backup(self, reason: str = "manual") -> Optional[str]:
        """Create backup of current database in Drive"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"temis_backup_{timestamp}_{reason}.db"
            
            # Get or create backups folder
            backups_folder_id = self._get_or_create_backups_folder()
            
            # Upload backup
            with open(self.local_db_path, 'rb') as f:
                backup_id = self.drive_service.upload_file(
                    backup_name,
                    f.read(),
                    backups_folder_id,
                    "application/x-sqlite3"
                )
            
            print(f"[SharedDB] ✓ Backup created: {backup_name}")
            return backup_id
        except Exception as e:
            print(f"[SharedDB] Error creating backup: {e}")
            return None
    
    def list_backups(self) -> list:
        """List available backups"""
        try:
            backups_folder_id = self._get_or_create_backups_folder()
            files = self.drive_service.list_files(backups_folder_id)
            
            backups = []
            for file in files:
                if file['name'].startswith('temis_backup_'):
                    backups.append({
                        'id': file['id'],
                        'name': file['name'],
                        'created': file.get('createdTime', 'Unknown')
                    })
            
            return sorted(backups, key=lambda x: x['created'], reverse=True)
        except Exception as e:
            print(f"[SharedDB] Error listing backups: {e}")
            return []
    
    def restore_backup(self, backup_id: str) -> bool:
        """Restore database from backup"""
        try:
            print(f"[SharedDB] Restoring from backup: {backup_id}")
            
            # Create backup of current state
            self._create_local_backup("before_restore")
            
            # Download backup
            content = self.drive_service.download_file(backup_id)
            
            if content:
                # Write to local DB
                with open(self.local_db_path, 'wb') as f:
                    f.write(content)
                
                # Sync to Drive
                self.sync_to_drive("restore_operation")
                
                print("[SharedDB] ✓ Backup restored successfully")
                return True
            
            return False
        except Exception as e:
            print(f"[SharedDB] Error restoring backup: {e}")
            return False
    
    def check_for_updates(self) -> Dict[str, Any]:
        """Check if there are updates in Drive"""
        try:
            status = self._get_status()
            
            if not status:
                return {"has_updates": False}
            
            remote_modified = status.get("last_modified_at")
            
            if not remote_modified or not self.last_sync:
                return {"has_updates": True, "status": status}
            
            remote_time = datetime.fromisoformat(remote_modified)
            
            if remote_time > self.last_sync:
                return {
                    "has_updates": True,
                    "modified_by": status.get("last_modified_by"),
                    "modified_at": remote_modified,
                    "status": status
                }
            
            return {"has_updates": False}
        except Exception as e:
            print(f"[SharedDB] Error checking for updates: {e}")
            return {"has_updates": False, "error": str(e)}
    
    def start_auto_sync(self):
        """Start automatic synchronization thread"""
        if self.sync_running:
            return
        
        self.sync_running = True
        self.sync_thread = threading.Thread(target=self._auto_sync_loop, daemon=True)
        self.sync_thread.start()
        print("[SharedDB] Auto-sync started")
    
    def stop_auto_sync(self):
        """Stop automatic synchronization"""
        self.sync_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("[SharedDB] Auto-sync stopped")
    
    def _auto_sync_loop(self):
        """Auto-sync loop running in background"""
        while self.sync_running:
            try:
                time.sleep(self.sync_interval)
                
                if not self.sync_running:
                    break
                
                # Check for updates
                updates = self.check_for_updates()
                
                if updates.get("has_updates"):
                    print(f"[SharedDB] Updates detected from {updates.get('modified_by', 'unknown')}")
                    # Note: In production, this should notify the UI
                
                # Sync to Drive
                self.sync_to_drive("auto_sync")
                
            except Exception as e:
                print(f"[SharedDB] Error in auto-sync: {e}")
    
    # Private helper methods
    
    def _get_or_create_shared_folder(self) -> str:
        """Get or create shared database folder in Drive"""
        folders = self.drive_service.list_files()
        
        for folder in folders:
            if folder['name'] == self.shared_folder_name and folder.get('mimeType') == 'application/vnd.google-apps.folder':
                return folder['id']
        
        # Create folder
        return self.drive_service.create_folder(self.shared_folder_name)
    
    def _get_or_create_backups_folder(self) -> str:
        """Get or create backups folder"""
        if not self.shared_folder_id:
            self.shared_folder_id = self._get_or_create_shared_folder()
        
        files = self.drive_service.list_files(self.shared_folder_id)
        
        for file in files:
            if file['name'] == 'backups' and file.get('mimeType') == 'application/vnd.google-apps.folder':
                return file['id']
        
        # Create backups folder
        return self.drive_service.create_folder('backups', self.shared_folder_id)
    
    def _get_db_file_id(self) -> Optional[str]:
        """Get database file ID from Drive"""
        if self.db_file_id:
            return self.db_file_id
        
        if not self.shared_folder_id:
            return None
        
        files = self.drive_service.list_files(self.shared_folder_id)
        
        for file in files:
            if file['name'] == 'temis_shared.db':
                self.db_file_id = file['id']
                return file['id']
        
        return None
    
    def _get_or_create_status_file(self) -> str:
        """Get or create status file"""
        if not self.shared_folder_id:
            self.shared_folder_id = self._get_or_create_shared_folder()
        
        files = self.drive_service.list_files(self.shared_folder_id)
        
        for file in files:
            if file['name'] == '_db_status.json':
                self.status_file_id = file['id']
                return file['id']
        
        # Create status file
        initial_status = {
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "last_modified_at": datetime.now().isoformat()
        }
        
        status_id = self.drive_service.upload_file(
            "_db_status.json",
            json.dumps(initial_status, indent=2).encode('utf-8'),
            self.shared_folder_id,
            "application/json"
        )
        
        self.status_file_id = status_id
        return status_id
    
    def _get_status(self) -> Optional[Dict]:
        """Get current status from Drive"""
        try:
            if not self.status_file_id:
                self.status_file_id = self._get_or_create_status_file()
            
            content = self.drive_service.download_file(self.status_file_id)
            
            if content:
                return json.loads(content.decode('utf-8'))
            
            return None
        except Exception as e:
            print(f"[SharedDB] Error getting status: {e}")
            return None
    
    def _update_status(self, updates: Dict):
        """Update status file in Drive"""
        try:
            current_status = self._get_status() or {}
            current_status.update(updates)
            current_status["version"] = current_status.get("version", 0) + 1
            
            self.drive_service.update_file(
                self.status_file_id,
                json.dumps(current_status, indent=2).encode('utf-8')
            )
        except Exception as e:
            print(f"[SharedDB] Error updating status: {e}")
    
    def _create_local_backup(self, reason: str):
        """Create local backup of database"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = Path(f"temis_local_backup_{timestamp}_{reason}.db")
            shutil.copy2(self.local_db_path, backup_path)
            print(f"[SharedDB] Local backup created: {backup_path}")
        except Exception as e:
            print(f"[SharedDB] Error creating local backup: {e}")
