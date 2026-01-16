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
        """Initialize Google Drive service"""
        try:
            # Decode service account JSON
            creds_json = base64.b64decode(SA_JSON_B64).decode('utf-8')
            creds_dict = json.loads(creds_json)

            # Create credentials
            temp_creds_file = os.path.join(tempfile.gettempdir(), "temis_sa_creds.json")
            with open(temp_creds_file, 'w') as f:
                f.write(creds_json)

            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            credentials = service_account.Credentials.from_service_account_file(
                temp_creds_file,
                scopes=SCOPES
            )

            # Build service
            self.service = build('drive', 'v3', credentials=credentials)

            # Clean up temp file
            os.remove(temp_creds_file)

        except Exception as e:
            print(f"Error initializing Drive service: {e}")
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

    def list_files(self, folder_id: str) -> Tuple[bool, list]:
        """
        List files in folder
        Returns (success, files_list or error_message)
        """
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, createdTime)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = results.get('files', [])
            return True, files

        except Exception as e:
            return False, f"Error listing files: {str(e)}"
    
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

