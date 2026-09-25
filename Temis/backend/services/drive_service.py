#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Drive service for TEMIS
"""

import base64
import json
import os
import tempfile
from typing import Tuple, Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import SA_JSON_B64, DRIVE_FOLDER_ID


class DriveService:
    """Google Drive service"""

    def __init__(self):
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Drive service using Service Account"""
        try:
            from config.config import get_service_account_info
            creds_dict = get_service_account_info()

            SCOPES = [
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=SCOPES
            )

            # Build service
            self.service = build('drive', 'v3', credentials=credentials)

        except Exception as e:
            print(f"Error initializing Drive service: {e}")
            self.service = None
            raise

    def create_project_folder(self, project_name: str, project_id: str) -> Tuple[bool, str]:
        """
        Create project folder structure in Drive
        Returns (success, folder_id or error_message)
        """
        try:
            # Create main project folder
            folder_metadata = {
                'name': f'[{project_id}]_{project_name}',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [DRIVE_FOLDER_ID]
            }

            folder = self.service.files().create(
                body=folder_metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()

            folder_id = folder.get('id')

            # Create subfolders for 7 phases + Diarios + Entregables + Documentos_Fuentes
            subfolders = [
                "00_Portafolio",
                "01_Diagnostico",
                "02_Inicio",
                "03_Planificacion",
                "04_Ejecucion",
                "05_Monitoreo",
                "06_Mejora_Continua",
                "07_Cierre",
                "Diarios",
                "Entregables_Finales",
                "Documentos_Fuentes"
            ]

            for subfolder_name in subfolders:
                subfolder_metadata = {
                    'name': subfolder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [folder_id]
                }
                self.service.files().create(
                    body=subfolder_metadata,
                    fields='id',
                    supportsAllDrives=True
                ).execute()

            return True, folder_id

        except Exception as e:
            return False, f"Error creating folder: {str(e)}"

    def ensure_folder_exists(self, parent_folder_id: str, folder_name: str) -> Tuple[bool, str]:
        """
        Check if a subfolder exists, if not, create it.
        Returns (success, folder_id)
        """
        try:
            query = f"name='{folder_name}' and '{parent_folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = results.get('files', [])
            if files:
                return True, files[0]['id']

            # Create it
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()
            return True, folder.get('id')
        except Exception as e:
            return False, str(e)

    def upload_file(self, file_path: str, file_name: str, parent_folder_id: str, mime_type: str = 'text/plain') -> Tuple[bool, str]:
        """
        Upload file to Drive
        Returns (success, file_id or error_message)
        """
        try:
            file_metadata = {
                'name': file_name,
                'parents': [parent_folder_id]
            }

            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id',
                supportsAllDrives=True
            ).execute()

            return True, file.get('id')

        except Exception as e:
            return False, f"Error uploading file: {str(e)}"

    def create_or_update_file(self, content: str, file_name: str, parent_folder_id: str, mime_type: str = 'text/plain') -> Tuple[bool, str]:
        """
        Create a file or update if it already exists by name in the parent folder.
        """
        try:
            import io
            from googleapiclient.http import MediaIoBaseUpload

            # Check if file exists
            query = f"name='{file_name}' and '{parent_folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = results.get('files', [])
            
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype=mime_type,
                resumable=True
            )

            if files:
                # Update
                file_id = files[0]['id']
                self.service.files().update(
                    fileId=file_id,
                    media_body=media,
                    supportsAllDrives=True
                ).execute()
                return True, file_id
            else:
                # Create
                file_metadata = {
                    'name': file_name,
                    'parents': [parent_folder_id]
                }
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id',
                    supportsAllDrives=True
                ).execute()
                return True, file.get('id')
        except Exception as e:
            return False, str(e)

    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> str:
        """Create a folder in Drive"""
        parent_id = parent_folder_id or DRIVE_FOLDER_ID
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        return folder.get('id')

    def download_file(self, file_id: str) -> Optional[bytes]:
        """Download file content from Drive"""
        try:
            from googleapiclient.http import MediaIoBaseDownload
            import io
            request = self.service.files().get_media(fileId=file_id, supportsAllDrives=True)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            fh.seek(0)
            return fh.read()
        except Exception as e:
            print(f"Error downloading file {file_id}: {e}")
            return None

    def update_file(self, file_id: str, content: bytes, mime_type: str = 'application/octet-stream') -> Tuple[bool, str]:
        """Update file content in Drive"""
        try:
            import io
            from googleapiclient.http import MediaIoBaseUpload
            media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=True)
            self.service.files().update(
                fileId=file_id,
                media_body=media,
                supportsAllDrives=True
            ).execute()
            return True, file_id
        except Exception as e:
            return False, str(e)

    def list_files(self, folder_id: Optional[str] = None) -> list:
        """
        List files in folder
        Returns files_list
        """
        try:
            parent_id = folder_id or DRIVE_FOLDER_ID
            query = f"'{parent_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, createdTime)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            return results.get('files', [])
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []
    
    def save_conversation_to_drive(self, project_folder_id: str, date_str: str, messages: list) -> Tuple[bool, str]:
        """
        Save chat conversation to Drive as JSON backup
        Args:
            project_folder_id: Project's Drive folder ID
            date_str: Date in YYYY-MM-DD format
            messages: List of message dicts
        Returns:
            (success, file_id_or_error)
        """
        try:
            import json
            import io
            from googleapiclient.http import MediaIoBaseUpload
            from datetime import datetime
            
            # Find Diarios folder
            query = f"name='Diarios' and '{project_folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            folders = results.get('files', [])
            if not folders:
                return False, "Diarios folder not found"
            
            diarios_folder_id = folders[0]['id']
            
            # Create JSON content
            conversation_data = {
                "date": date_str,
                "exported_at": datetime.utcnow().isoformat(),
                "message_count": len(messages),
                "messages": messages
            }
            
            json_content = json.dumps(conversation_data, indent=2, ensure_ascii=False)
            
            # File name
            file_name = f"conversation_{date_str}.json"
            
            # Check if file already exists
            query = f"name='{file_name}' and '{diarios_folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            existing_files = results.get('files', [])
            
            media = MediaIoBaseUpload(
                io.BytesIO(json_content.encode('utf-8')),
                mimetype='application/json',
                resumable=True
            )
            
            if existing_files:
                # Update existing file
                file_id = existing_files[0]['id']
                self.service.files().update(
                    fileId=file_id,
                    media_body=media,
                    supportsAllDrives=True
                ).execute()
                return True, file_id
            else:
                # Create new file
                file_metadata = {
                    'name': file_name,
                    'parents': [diarios_folder_id],
                    'mimeType': 'application/json'
                }
                
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id',
                    supportsAllDrives=True
                ).execute()
                
                return True, file.get('id')
                
        except Exception as e:
            print(f"Error saving conversation to Drive: {e}")
            return False, str(e)

    def trash_file_or_folder(self, file_id: str) -> Tuple[bool, str]:
        """
        Move a file or folder to trash.
        """
        try:
            self.service.files().update(
                fileId=file_id,
                body={'trashed': True},
                supportsAllDrives=True
            ).execute()
            return True, file_id
        except Exception as e:
            return False, str(e)

    def replicate_master_sheet_template(self, project_folder_id: str, project_name: str) -> Tuple[bool, str]:
        """
        Replicate the master Google Sheet template into the new project folder.
        """
        try:
            # 1. Find 00_Plantillas_Maestras folder
            ok_tpl, templates_folder_id = self.ensure_folder_exists(DRIVE_FOLDER_ID, "00_Plantillas_Maestras")
            if not ok_tpl:
                return False, f"Error finding templates folder: {templates_folder_id}"

            # 2. Find Plantilla Maestra - Plan de Trabajo
            query = f"name='Plantilla Maestra - Plan de Trabajo' and '{templates_folder_id}' in parents and trashed=false"
            res = self.service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            files = res.get('files', [])
            if not files:
                return False, "Master template 'Plantilla Maestra - Plan de Trabajo' not found in 00_Plantillas_Maestras"

            master_template_id = files[0]['id']
            sheet_title = f"Planeación - {project_name.replace('_', ' ')}"

            copy_body = {
                "name": sheet_title,
                "parents": [project_folder_id]
            }
            replicated = self.service.files().copy(
                fileId=master_template_id,
                body=copy_body,
                supportsAllDrives=True
            ).execute()

            return True, replicated.get("id")
        except Exception as e:
            return False, f"Error replicating master sheet template: {str(e)}"

    def load_users_from_drive(self) -> Optional[list]:
        """
        Load users directory JSON from Google Drive 00_Configuracion/users_directory.json
        """
        try:
            if not self.service:
                return None
            ok, cfg_folder_id = self.ensure_folder_exists(DRIVE_FOLDER_ID, "00_Configuracion")
            if not ok:
                return None

            query = f"name='users_directory.json' and '{cfg_folder_id}' in parents and trashed=false"
            res = self.service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            files = res.get('files', [])
            if not files:
                return None

            content_bytes = self.download_file(files[0]['id'])
            if not content_bytes:
                return None

            users = json.loads(content_bytes.decode('utf-8'))
            if isinstance(users, list) and len(users) > 0:
                return users
            return None
        except Exception as e:
            print(f"[DriveService] Error loading users from Drive: {e}")
            return None

    def save_users_to_drive(self, users: list) -> Tuple[bool, str]:
        """
        Save users directory JSON to Google Drive 00_Configuracion/users_directory.json
        """
        try:
            if not self.service:
                return False, "Drive service not initialized"
            ok, cfg_folder_id = self.ensure_folder_exists(DRIVE_FOLDER_ID, "00_Configuracion")
            if not ok:
                return False, f"Could not access 00_Configuracion folder: {cfg_folder_id}"

            json_str = json.dumps(users, indent=2, ensure_ascii=False)
            return self.create_or_update_file(
                json_str,
                "users_directory.json",
                cfg_folder_id,
                mime_type="application/json"
            )
        except Exception as e:
            return False, f"Error saving users to Drive: {e}"

    def scan_projects_from_drive(self) -> list:
        """
        Scan Google Drive root DRIVE_FOLDER_ID for real project folders.
        Retrieves project_state.json from 00_Portafolio or parses folder metadata.
        """
        try:
            if not self.service:
                return []

            query = f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            res = self.service.files().list(
                q=query,
                fields="files(id, name, createdTime, modifiedTime)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            folders = res.get('files', [])
            projects = []
            system_folders = {
                "00_plantillas_maestras", "00_configuracion", "00_portafolio", 
                "plantillas", "configuracion", "diarios", "entregables_finales"
            }

            for f in folders:
                folder_id = f.get('id')
                folder_name = f.get('name', '').strip()
                if folder_name.lower() in system_folders:
                    continue

                # 1. Search for project_state.json or .temis.json inside this project folder
                proj_data = None
                try:
                    q_state = f"(name='project_state.json' or name contains '.temis.json') and '{folder_id}' in parents and trashed=false"
                    res_state = self.service.files().list(
                        q=q_state,
                        fields="files(id, name)",
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True
                    ).execute()
                    state_files = res_state.get('files', [])

                    # Also check 00_Portafolio subfolder
                    if not state_files:
                        q_sub = f"name='00_Portafolio' and '{folder_id}' in parents and trashed=false"
                        res_sub = self.service.files().list(
                            q=q_sub,
                            fields="files(id)",
                            supportsAllDrives=True,
                            includeItemsFromAllDrives=True
                        ).execute()
                        sub_folders = res_sub.get('files', [])
                        if sub_folders:
                            port_id = sub_folders[0]['id']
                            q_port = f"(name='project_state.json' or name contains '.temis.json') and '{port_id}' in parents and trashed=false"
                            res_port = self.service.files().list(
                                q=q_port,
                                fields="files(id, name)",
                                supportsAllDrives=True,
                                includeItemsFromAllDrives=True
                            ).execute()
                            state_files = res_port.get('files', [])

                    if state_files:
                        content_bytes = self.download_file(state_files[0]['id'])
                        if content_bytes:
                            proj_data = json.loads(content_bytes.decode('utf-8'))
                except Exception as ex:
                    print(f"[DriveService] Warning reading state for folder '{folder_name}': {ex}")

                # 2. Search for associated Google Sheet in project folder
                sheet_id = ""
                sheet_url = ""
                try:
                    q_sheet = f"mimeType='application/vnd.google-apps.spreadsheet' and '{folder_id}' in parents and trashed=false"
                    res_sheet = self.service.files().list(
                        q=q_sheet,
                        fields="files(id, name)",
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True
                    ).execute()
                    sheet_files = res_sheet.get('files', [])
                    if sheet_files:
                        sheet_id = sheet_files[0]['id']
                        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
                except Exception:
                    pass

                # 3. If valid project state was parsed, ensure Drive URLs
                if isinstance(proj_data, dict) and proj_data.get("name"):
                    proj_data["drive_folder_id"] = folder_id
                    proj_data["drive_folder_url"] = f"https://drive.google.com/drive/folders/{folder_id}"
                    if sheet_id and not proj_data.get("sheet_id"):
                        proj_data["sheet_id"] = sheet_id
                        proj_data["sheet_url"] = sheet_url
                    projects.append(proj_data)
                else:
                    # Construct basic project record from folder name
                    code = "PRJ"
                    name = folder_name
                    if folder_name.startswith("[") and "]" in folder_name:
                        parts = folder_name.split("]", 1)
                        code = parts[0].replace("[", "").strip()
                        name = parts[1].lstrip("_ -").strip() or folder_name

                    clean_proj = {
                        "id": f"proj-{folder_id[:8]}",
                        "code": code,
                        "name": name.replace("_", " "),
                        "purpose": f"Proyecto {name} registrado en Google Drive",
                        "manager": "Ing. José Antonio Hurtado",
                        "manager_initials": "JH",
                        "sponsor": "Área de Procesos & Calidad",
                        "start_date": f.get('createdTime', '')[:10] or "2026-01-16",
                        "end_date": "2026-12-31",
                        "scope_in": "Estructura de carpetas y gobernanza activa en Google Drive.",
                        "scope_out": "",
                        "current_phase": 1,
                        "phase_name": "Fase 1: Diagnóstico Estratégico",
                        "updated_at": f.get('modifiedTime', '')[:16].replace('T', ' ') or "Reciente",
                        "drive_folder_id": folder_id,
                        "drive_folder_url": f"https://drive.google.com/drive/folders/{folder_id}",
                        "sheet_id": sheet_id,
                        "sheet_url": sheet_url,
                        "current_sprint": "Sprint 01",
                        "current_sprint_name": "Diagnóstico y Mapeo AS-IS",
                        "progress_percentage": 0.0,
                        "completed_sp": 0,
                        "total_sp": 10,
                        "completed_tasks": 0,
                        "total_tasks": 1,
                        "health_status": "green" if sheet_id else "unrated",
                        "audit_score": 0,
                        "nodes_count": 0,
                        "steps_count": 0,
                        "plan_start_date": "2026-01-16",
                        "plan_end_date": "2026-12-31",
                        "plan_daily_hours": 8,
                        "plan_work_days_mode": "mon_fri",
                        "plan_activities_description": f"Gobernanza y mapeo de procesos para {name}",
                        "plan_sprints": [
                            {"sprint_id": "Sprint 01", "period": "2026-01-16 al 2026-01-30", "objective": "Diagnóstico y levantamiento", "modules": "General", "milestone": "Charter aprobado", "status": "In Progress", "story_points": 10, "hours_estimated": 40}
                        ],
                        "plan_backlog_items": [],
                        "sipoc_rows": [],
                        "customer_requirements": "",
                        "nodes": [],
                        "edges": [],
                        "swimlanes": ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"],
                        "project_pages": [],
                        "narrative_text": ""
                    }
                    projects.append(clean_proj)

            return projects
        except Exception as e:
            print(f"[DriveService] Error scanning projects from Drive: {e}")
            return []

    def save_project_to_drive(self, project_dict: dict) -> Tuple[bool, str]:
        """
        Save complete project state JSON into 00_Portafolio/project_state.json in Drive
        """
        try:
            if not self.service:
                return False, "Drive service not initialized"

            drive_folder_id = project_dict.get("drive_folder_id")
            if not drive_folder_id:
                ok_f, folder_res = self.create_project_folder(
                    project_dict.get("name", "Nuevo_Proyecto"),
                    project_dict.get("code", "PRJ")
                )
                if not ok_f:
                    return False, folder_res
                drive_folder_id = folder_res
                project_dict["drive_folder_id"] = drive_folder_id
                project_dict["drive_folder_url"] = f"https://drive.google.com/drive/folders/{drive_folder_id}"

            ok_port, port_id = self.ensure_folder_exists(drive_folder_id, "00_Portafolio")
            target_folder = port_id if ok_port else drive_folder_id

            json_str = json.dumps(project_dict, indent=2, ensure_ascii=False)
            return self.create_or_update_file(
                json_str,
                "project_state.json",
                target_folder,
                mime_type="application/json"
            )
        except Exception as e:
            return False, f"Error saving project to Drive: {e}"

    def delete_project_from_drive(self, drive_folder_id: str) -> Tuple[bool, str]:
        """Move project folder to Trash in Google Drive"""
        if not drive_folder_id:
            return False, "No drive_folder_id provided"
        return self.trash_file_or_folder(drive_folder_id)


