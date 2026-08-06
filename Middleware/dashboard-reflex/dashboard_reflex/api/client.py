import httpx
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class AdminAPIClient:
    """Async Client for Admin API of Orbit."""
    
    def __init__(self):
        self.base_url = os.getenv("ORBIT_API_URL", "http://localhost:8000").rstrip('/')
        self.username = os.getenv("DASHBOARD_USERNAME", "admin")
        self.password = os.getenv("DASHBOARD_PASSWORD", "")

    @property
    def auth_params(self) -> dict:
        return {"username": self.username, "password": self.password}

    async def _request(self, method: str, endpoint: str, json_data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Any]:
        url = f"{self.base_url}{endpoint}"
        
        # Merge credentials into query params
        req_params = self.auth_params.copy()
        if params:
            req_params.update(params)
            
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=req_params,
                    json=json_data
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"API Error [{method} {endpoint}]: {e}")
            return None

    # ============================================================
    # Telemetry
    # ============================================================
    async def get_summary(self) -> Optional[Dict]:
        """Get summary metrics (requests, latency, success rate)."""
        return await self._request("GET", "/admin/telemetry/summary")

    async def get_stats(self, hours: int = 24) -> List[Dict]:
        """Get hourly statistics."""
        res = await self._request("GET", "/admin/telemetry/stats", params={"hours": hours})
        return res if res else []

    async def get_recent_requests(self, limit: int = 100, status: Optional[str] = None) -> List[Dict]:
        """Get request history."""
        params = {"limit": limit}
        if status:
            params["status"] = status
        res = await self._request("GET", "/admin/telemetry/requests", params=params)
        return res if res else []

    # ============================================================
    # Configuration
    # ============================================================
    async def get_mcp_config(self) -> Optional[Dict]:
        return await self._request("GET", "/admin/config/mcp")

    async def update_mcp_config(self, data: Dict) -> bool:
        res = await self._request("PUT", "/admin/config/mcp", json_data=data)
        return res is not None

    async def get_cache_config(self) -> Optional[Dict]:
        return await self._request("GET", "/admin/config/cache")

    async def update_cache_config(self, data: Dict) -> bool:
        res = await self._request("PUT", "/admin/config/cache", json_data=data)
        return res is not None

    async def get_security_config(self) -> Optional[Dict]:
        return await self._request("GET", "/admin/config/security")

    async def update_security_config(self, data: Dict) -> bool:
        res = await self._request("PUT", "/admin/config/security", json_data=data)
        return res is not None

    # ============================================================
    # Maintenance
    # ============================================================
    async def get_health(self) -> Optional[Dict]:
        return await self._request("GET", "/admin/maintenance/health")

    async def get_system_info(self) -> Optional[Dict]:
        return await self._request("GET", "/admin/maintenance/system-info")

    async def get_circuit_breaker_status(self) -> Optional[Dict]:
        return await self._request("GET", "/admin/maintenance/circuit-breaker")

    async def clear_cache(self) -> bool:
        res = await self._request("POST", "/admin/maintenance/clear-cache")
        return res is not None

    async def reset_circuit_breaker(self) -> bool:
        res = await self._request("POST", "/admin/circuit-breaker/reset")
        return res is not None

    async def test_mcp(self, query: str) -> Optional[Dict]:
        return await self._request("POST", "/admin/maintenance/test-mcp", params={"query": query})

    # ============================================================
    # Auditoría
    # ============================================================
    async def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        res = await self._request("GET", "/admin/audit/logs", params={"limit": limit})
        return res if res else []

    async def log_audit(self, action: str, details: str) -> bool:
        res = await self._request("POST", "/admin/audit/log", params={"action": action, "details": details})
        return res is not None

    async def get_decision_logs(
        self,
        contact_id: Optional[str] = None,
        case_id: Optional[str] = None,
        rule_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Fetch decision audit logs from Orbit backend."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if contact_id:
            params["contact_id"] = contact_id
        if case_id:
            params["case_id"] = case_id
        if rule_id:
            params["rule_id"] = rule_id
        res = await self._request("GET", "/admin/decision-logs", params=params)
        return res if res else {"total": 0, "logs": [], "limit": limit, "offset": offset}

    async def get_google_sources(self) -> Dict[str, Any]:
        """Fetch Google Cloud document and sheet sources grouped by Service Account."""
        res = await self._request("GET", "/admin/google-sources")
        return res if res else {}

    async def update_google_sources(self, payload: Dict[str, Any]) -> bool:
        """Update Google Cloud source IDs in backend Redis."""
        res = await self._request("PUT", "/admin/google-sources", json=payload)
        return res is not None

    async def force_sync_sources(self) -> Dict[str, Any]:
        """Invalidates Redis cache and forces a live sync with Google Cloud."""
        res = await self._request("POST", "/admin/force-sync")
        return res if res else {"status": "error", "message": "Failed to force sync"}


    # ============================================================
    # User Management
    # ============================================================
    async def get_dashboard_users(self) -> List[Dict[str, Any]]:
        res = await self._request("GET", "/admin/users")
        return res if res else []

    async def get_users(self) -> List[Dict[str, Any]]:
        return await self.get_dashboard_users()

    async def add_user(self, user_data: Dict[str, Any]) -> bool:
        res = await self._request("POST", "/admin/users", json_data=user_data)
        return res is not None

    async def delete_user(self, username: str) -> bool:
        res = await self._request("DELETE", f"/admin/users/{username}")
        return res is not None

    # ============================================================
    # Agent Management
    # ============================================================
    async def get_agents(self) -> List[Dict[str, Any]]:
        res = await self._request("GET", "/admin/agents")
        return res if res else []

    async def add_agent(self, agent_data: Dict[str, Any]) -> bool:
        res = await self._request("POST", "/admin/agents", json_data=agent_data)
        return res is not None

    async def delete_agent(self, name: str) -> bool:
        res = await self._request("DELETE", f"/admin/agents/{name}")
        return res is not None

    # ============================================================
    # Knowledge Base
    # ============================================================
    async def get_knowledge(self) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/knowledge"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Knowledge API error: {e}")
            return None

    # ============================================================
    # QA / Quality Audits
    # ============================================================
    async def get_audits(self, start_date: Optional[str] = None, end_date: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if status:
            params["status"] = status
        res = await self._request("GET", "/admin/audits", params=params)
        return res if res else []

    async def get_audit_chat(self, conversation_id: str, date: str) -> Optional[Dict[str, Any]]:
        return await self._request("GET", f"/admin/audit/{conversation_id}/chat", params={"date": date})

    async def update_audit(self, conversation_id: str, payload: Dict[str, Any]) -> bool:
        res = await self._request("PUT", f"/admin/audit/{conversation_id}", json_data=payload)
        return res is not None

# Singleton instance
api_client = AdminAPIClient()
