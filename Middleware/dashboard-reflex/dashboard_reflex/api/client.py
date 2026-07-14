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
        self.password = os.getenv("DASHBOARD_PASSWORD", "your-super-secret-dashboard-password")

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

# Singleton instance
api_client = AdminAPIClient()
