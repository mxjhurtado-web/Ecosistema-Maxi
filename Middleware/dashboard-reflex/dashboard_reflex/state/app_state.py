import reflex as rx
from dashboard_reflex.api.client import api_client
from datetime import datetime

class AppState(rx.State):
    """Global state for managing health check data and API data caching."""
    api_status: str = "checking"      # healthy, issues, offline, checking
    mcp_status: str = "checking"      # healthy, disconnected, checking
    redis_status: str = "checking"    # healthy, disabled, error, checking
    cb_is_open: bool = False
    
    # Summary Metrics (KPIs)
    total_requests: int = 0
    success_rate: float = 0.0
    avg_latency_ms: int = 0
    error_count: int = 0
    
    is_loading: bool = False
    last_checked: str = ""

    async def update_health(self):
        """Query the API health endpoints and update status variables."""
        self.is_loading = True
        
        # 1. Fetch Health
        health_data = await api_client.get_health()
        if health_data:
            self.api_status = health_data.get("status", "issues")
            self.mcp_status = health_data.get("mcp_status", "disconnected")
            self.redis_status = health_data.get("redis_status", "error")
        else:
            self.api_status = "offline"
            self.mcp_status = "disconnected"
            self.redis_status = "error"
            
        # 2. Fetch Circuit Breaker
        cb_data = await api_client.get_circuit_breaker_status()
        if cb_data:
            self.cb_is_open = cb_data.get("is_open", False)
        else:
            self.cb_is_open = False
            
        self.last_checked = datetime.now().strftime("%H:%M:%S")
        self.is_loading = False

    async def load_dashboard_summary(self):
        """Fetch summary data for KPIs page."""
        self.is_loading = True
        summary = await api_client.get_summary()
        if summary:
            self.total_requests = summary.get("total_requests", 0)
            self.success_rate = summary.get("success_rate", 0.0)
            self.avg_latency_ms = summary.get("avg_latency_ms", 0)
            self.error_count = summary.get("error_count", 0)
        else:
            self.total_requests = 0
            self.success_rate = 0.0
            self.avg_latency_ms = 0
            self.error_count = 0
        self.is_loading = False

    async def on_load(self):
        """Event run when the dashboard pages are opened."""
        await self.update_health()
