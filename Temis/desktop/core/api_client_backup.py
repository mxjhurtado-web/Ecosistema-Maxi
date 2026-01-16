#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Client for TEMIS Desktop
"""

import requests
from typing import Optional, Dict, Any, List
from datetime import date


class APIClient:
    """Client for TEMIS API"""

    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def get_projects(self, user_email: str) -> List[Dict[str, Any]]:
        """Get user's projects"""
        try:
            response = requests.get(
                f"{self.base_url}/api/projects/",
                headers=self.headers,
                params={"user_email": user_email}
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting projects: {e}")
            return []

    def create_project(self, user_email: str, project_data: dict) -> Optional[Dict[str, Any]]:
        """Create new project"""
        try:
            print(f"[DEBUG] Creating project with data: {project_data}")
            response = requests.post(
                f"{self.base_url}/api/projects/",
                headers=self.headers,
                params={"user_email": user_email},
                json=project_data
            )
            print(f"[DEBUG] Response status: {response.status_code}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[ERROR] Create project failed: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            print(f"[ERROR] Exception creating project: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_project(self, user_email: str, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project details"""
        try:
            response = requests.get(
                f"{self.base_url}/api/projects/{project_id}",
                headers=self.headers,
                params={"user_email": user_email}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting project: {e}")
            return None

    def delete_project(self, project_id: str, user_email: str) -> bool:
        try:
            response = requests.delete(
                f'{self.base_url}/api/projects/{project_id}',
                headers=self.headers,
                params={'user_email': user_email}
            )
            return response.status_code == 200
        except Exception as e:
            print(f'Error deleting project: {e}')
            return False

    def import_project(self, project_code: str, user_email: str) -> dict:
        try:
            response = requests.post(
                f'{self.base_url}/api/projects/import',
                headers=self.headers,
                json={'project_code': project_code, 'user_email': user_email}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(response.json().get('detail', 'Error desconocido'))
        except Exception as e:
            raise Exception(f'Error al importar proyecto: {str(e)}')

    # Daily Log methods
    def get_daily_log(self, user_email: str, project_id: str, log_date: date) -> Optional[Dict[str, Any]]:
        """Get daily log for specific date"""
        try:
            response = requests.get(
                f"{self.base_url}/api/projects/{project_id}/dailylog",
                headers=self.headers,
                params={"user_email": user_email, "log_date": log_date.isoformat()}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting daily log: {e}")
            return None

    def save_daily_log(self, user_email: str, project_id: str, log_date: date, content: str) -> bool:
        """Save daily log"""
        try:
            response = requests.post(
                f"{self.base_url}/api/projects/{project_id}/dailylog",
                headers=self.headers,
                params={"user_email": user_email},
                json={"log_date": log_date.isoformat(), "content": content}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error saving daily log: {e}")
            return False

    def process_eod(self, project_id: str, user_email: str) -> Optional[Dict[str, Any]]:
        """Process End of Day - now using chat messages"""
        try:
            from desktop.core.gemini_config import GeminiConfig
            from datetime import date
            
            # Get Gemini API key
            api_key = GeminiConfig.get_api_key()
            if not api_key:
                return {"status": "error", "message": "Gemini API key not configured"}
            
            # Get today's date
            today = date.today().isoformat()
            
            print(f"[DEBUG] Processing EOD for project {project_id}, date {today}")
            
            response = requests.post(
                f"{self.base_url}/api/eod/process-chat-daily",
                headers=self.headers,
                params={
                    "project_id": project_id,
                    "date_str": today,
                    "user_email": user_email,
                    "gemini_api_key": api_key
                }
            )
            
            print(f"[DEBUG] EOD response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"[DEBUG] EOD result: {result}")
                
                # Adapt response format to match expected structure
                if result.get("status") == "success":
                    return {
                        "status": "success",
                        "summary": {
                            "gemini_summary": result.get("summary", ""),
                            "message_count": result.get("message_count", 0),
                            "drive_backup": result.get("drive_backup", False)
                        }
                    }
                else:
                    return result
            else:
                print(f"[ERROR] EOD failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"[ERROR] Error processing EOD: {e}")
            import traceback
            traceback.print_exc()
            return None
