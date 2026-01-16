#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API client extensions for Sprint 2
"""

from typing import Optional, Dict, Any
from datetime import date


class APIClientExtensions:
    """Extensions to API client for daily log and EOD"""

    def get_daily_log(self, user_email: str, project_id: str, log_date: date) -> Optional[Dict[str, Any]]:
        """Get daily log for specific date"""
        try:
            response = self.session.get(
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

    def create_daily_log(self, user_email: str, project_id: str, log_date: date, content: str) -> Optional[Dict[str, Any]]:
        """Create daily log"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/projects/{project_id}/dailylog",
                headers=self.headers,
                params={"user_email": user_email},
                json={"log_date": log_date.isoformat(), "content": content}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error creating daily log: {e}")
            return None

    def process_eod(self, user_email: str, project_id: str, log_date: date, gemini_api_key: str, force: bool = False) -> Optional[Dict[str, Any]]:
        """Process End of Day"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/projects/{project_id}/eod-process",
                headers=self.headers,
                params={"user_email": user_email},
                json={
                    "log_date": log_date.isoformat(),
                    "gemini_api_key": gemini_api_key,
                    "force": force
                }
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error processing EOD: {e}")
            return None
