"""
API client for communicating with Admin API.
"""

import requests
import os
import streamlit as st
from typing import Optional, List, Dict, Any


class AdminAPIClient:
    """Client for Admin API"""
    
    def __init__(self):
        # Prioritize Streamlit Secrets (for Cloud) over environment variables
        self.default_base_url = st.secrets.get("API_URL") or os.getenv("API_URL", "http://localhost:8000")
        self.default_username = st.secrets.get("DASHBOARD_USERNAME") or os.getenv("DASHBOARD_USERNAME", "admin")
        self.default_password = st.secrets.get("DASHBOARD_PASSWORD") or os.getenv("DASHBOARD_PASSWORD", "change-me-in-production")

    @property
    def base_url(self):
        return self.default_base_url

    @property
    def params(self):
        # Use session credentials if available, otherwise use defaults
        username = st.session_state.get("username", self.default_username)
        password = st.session_state.get("password", self.default_password)
        return {"username": username, "password": password}
    
    def _get(self, endpoint: str) -> Optional[Dict]:
        """GET request"""
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                params=self.params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"GET error: {str(e)}")
            return None
    
    def _post(self, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """POST request"""
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                params=self.params,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"POST error: {str(e)}")
            return None
    
    def _put(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """PUT request"""
        try:
            response = requests.put(
                f"{self.base_url}{endpoint}",
                params=self.params,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"PUT error: {str(e)}")
            return None
    
    # ============================================================
    # Configuration
    # ============================================================
    
    def get_mcp_config(self) -> Optional[Dict]:
        """Get MCP configuration"""
        return self._get("/admin/config/mcp")
    
    def update_mcp_config(self, config: Dict) -> bool:
        """Update MCP configuration"""
        result = self._put("/admin/config/mcp", config)
        return result is not None
    
    def get_cache_config(self) -> Optional[Dict]:
        """Get cache configuration"""
        return self._get("/admin/config/cache")
    
    def update_cache_config(self, config: Dict) -> bool:
        """Update cache configuration"""
        result = self._put("/admin/config/cache", config)
        return result is not None
    
    def get_security_config(self) -> Optional[Dict]:
        """Get security configuration"""
        return self._get("/admin/config/security")
    
    def update_security_config(self, config: Dict) -> bool:
        """Update security configuration"""
        result = self._put("/admin/config/security", config)
        return result is not None
    
    # ============================================================
    # Telemetry
    # ============================================================
    
    def get_recent_requests(self, limit: int = 100, status: Optional[str] = None) -> List[Dict]:
        """Get recent requests"""
        endpoint = f"/admin/telemetry/requests?limit={limit}"
        if status:
            endpoint += f"&status={status}"
        
        result = self._get(endpoint)
        return result if result else []
    
    def get_request_by_trace_id(self, trace_id: str) -> Optional[Dict]:
        """Get request by trace ID"""
        return self._get(f"/admin/telemetry/request/{trace_id}")
    
    def get_stats(self, hours: int = 24) -> List[Dict]:
        """Get hourly statistics"""
        result = self._get(f"/admin/telemetry/stats?hours={hours}")
        return result if result else []
    
    def get_summary(self) -> Optional[Dict]:
        """Get summary statistics"""
        return self._get("/admin/telemetry/summary")
    
    # ============================================================
    # Maintenance
    # ============================================================
    
    def reload_config(self) -> bool:
        """Reload configuration"""
        result = self._post("/admin/maintenance/reload-config")
        return result is not None
    
    def clear_cache(self) -> bool:
        """Clear cache"""
        result = self._post("/admin/maintenance/clear-cache")
        return result is not None
    
    def get_health(self) -> Optional[Dict]:
        """Get health status"""
        return self._get("/admin/maintenance/health")
    
    def test_mcp(self, query: str = "Test query") -> Optional[Dict]:
        """Test MCP connection"""
        return self._post(f"/admin/maintenance/test-mcp?query={query}")
    
    def get_system_info(self) -> Optional[Dict]:
        """Get system information"""
        return self._get("/admin/maintenance/system-info")
    
    def get_circuit_breaker_status(self) -> Optional[Dict]:
        """Get circuit breaker status"""
        return self._get("/admin/maintenance/circuit-breaker")
    
    def reset_circuit_breaker(self) -> bool:
        """Reset circuit breaker"""
        result = self._post("/admin/circuit-breaker/reset")
        return result is not None

    # ============================================================
    # User Management
    # ============================================================

    def get_users(self) -> List[Dict]:
        """Get all dashboard users"""
        result = self._get("/admin/users")
        return result if result else []

    def add_user(self, user_data: Dict) -> bool:
        """Add or update a dashboard user"""
        result = self._post("/admin/users", user_data)
        return result is not None

    def delete_user(self, username: str) -> bool:
        """Delete a dashboard user"""
        result = requests.delete(
            f"{self.base_url}/admin/users/{username}",
            params=self.params,
            timeout=10
        )
        return result.status_code == 200


# Singleton instance
api_client = AdminAPIClient()
