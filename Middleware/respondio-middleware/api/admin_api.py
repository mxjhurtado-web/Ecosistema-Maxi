"""
Admin API for dashboard management.
Provides endpoints for configuration, telemetry, and maintenance.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta

from .models import (
    MCPConfig,
    CacheConfig,
    SecurityConfig,
    RequestLog,
    ResponseStatus,
    HealthResponse
)
from .config import settings
from .config_manager import config_manager
from .telemetry import telemetry_service
from .mcp_client import mcp_client
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================
# Authentication Dependency (Basic)
# ============================================================

async def verify_admin_credentials(
    username: str = Query(...),
    password: str = Query(...)
):
    """Verify admin credentials"""
    if username != settings.DASHBOARD_USERNAME or password != settings.DASHBOARD_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return True


# ============================================================
# Configuration Endpoints
# ============================================================

@router.get("/config/mcp", response_model=MCPConfig)
async def get_mcp_config(
    _: bool = Depends(verify_admin_credentials)
):
    """Get current MCP configuration"""
    return await config_manager.get_mcp_config()


@router.put("/config/mcp")
async def update_mcp_config(
    config: MCPConfig,
    _: bool = Depends(verify_admin_credentials)
):
    """Update MCP configuration"""
    success = await config_manager.update_mcp_config(config)
    
    if success:
        # Update MCP client with new config
        mcp_client.url = config.url
        mcp_client.timeout = config.timeout
        mcp_client.max_retries = config.max_retries
        mcp_client.retry_delay = config.retry_delay
        mcp_client.gemini_api_key = config.gemini_api_key
        
        return {"status": "ok", "message": "MCP config updated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update config")


@router.get("/config/cache", response_model=CacheConfig)
async def get_cache_config(
    _: bool = Depends(verify_admin_credentials)
):
    """Get current cache configuration"""
    return await config_manager.get_cache_config()


@router.put("/config/cache")
async def update_cache_config(
    config: CacheConfig,
    _: bool = Depends(verify_admin_credentials)
):
    """Update cache configuration"""
    success = await config_manager.update_cache_config(config)
    
    if success:
        return {"status": "ok", "message": "Cache config updated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update config")


@router.get("/config/security", response_model=SecurityConfig)
async def get_security_config(
    _: bool = Depends(verify_admin_credentials)
):
    """Get current security configuration"""
    return await config_manager.get_security_config()


@router.put("/config/security")
async def update_security_config(
    config: SecurityConfig,
    _: bool = Depends(verify_admin_credentials)
):
    """Update security configuration"""
    success = await config_manager.update_security_config(config)
    
    if success:
        return {"status": "ok", "message": "Security config updated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update config")


# ============================================================
# Telemetry Endpoints
# ============================================================

@router.get("/telemetry/requests", response_model=List[RequestLog])
async def get_recent_requests(
    limit: int = Query(default=100, le=1000),
    status: Optional[ResponseStatus] = None,
    _: bool = Depends(verify_admin_credentials)
):
    """Get recent requests"""
    return await telemetry_service.get_recent_requests(limit, status)


@router.get("/telemetry/request/{trace_id}", response_model=RequestLog)
async def get_request_by_trace_id(
    trace_id: str,
    _: bool = Depends(verify_admin_credentials)
):
    """Get a specific request by trace ID"""
    request_log = await telemetry_service.get_request_by_trace_id(trace_id)
    
    if not request_log:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return request_log


@router.get("/telemetry/stats")
async def get_stats(
    hours: int = Query(default=24, le=168),  # Max 7 days
    _: bool = Depends(verify_admin_credentials)
):
    """Get hourly statistics"""
    return await telemetry_service.get_hourly_stats(hours)


@router.get("/telemetry/summary")
async def get_summary(
    _: bool = Depends(verify_admin_credentials)
):
    """Get summary statistics for today"""
    try:
        # Get today's stats
        stats = await telemetry_service.get_hourly_stats(24)
        
        if not stats:
            return {
                "total_requests": 0,
                "success_count": 0,
                "error_count": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0,
                "p95_latency_ms": 0
            }
        
        # Aggregate
        total_requests = sum(s["total_requests"] for s in stats)
        success_count = sum(s["success_count"] for s in stats)
        error_count = sum(s["error_count"] for s in stats)
        
        # Calculate averages
        total_latency = sum(s["avg_latency_ms"] * s["total_requests"] for s in stats)
        avg_latency = int(total_latency / total_requests) if total_requests > 0 else 0
        
        # Get max P95
        p95_latency = max((s["p95_latency_ms"] for s in stats), default=0)
        
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "total_requests": total_requests,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": round(success_rate, 2),
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency
        }
    
    except Exception as e:
        logger.error(f"Failed to get summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get summary")


# ============================================================
# Maintenance Endpoints
# ============================================================

@router.post("/maintenance/reload-config")
async def reload_config(
    _: bool = Depends(verify_admin_credentials)
):
    """Reload configuration from Redis"""
    success = await config_manager.reload_config()
    
    if success:
        return {"status": "ok", "message": "Configuration reloaded"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reload config")


@router.post("/maintenance/clear-cache")
async def clear_cache(
    _: bool = Depends(verify_admin_credentials)
):
    """Clear all cached data"""
    success = await config_manager.clear_cache()
    
    if success:
        return {"status": "ok", "message": "Cache cleared"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/maintenance/health", response_model=HealthResponse)
async def health_check_detailed(
    _: bool = Depends(verify_admin_credentials)
):
    """Detailed health check"""
    
    # Check MCP
    mcp_healthy = await mcp_client.health_check()
    mcp_status = "healthy" if mcp_healthy else "unhealthy"
    
    # Check Redis
    redis_status = "healthy" if telemetry_service.enabled else "disabled"
    
    # Overall status
    overall_status = "healthy" if mcp_healthy else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.API_VERSION,
        mcp_status=mcp_status,
        redis_status=redis_status
    )


@router.post("/maintenance/test-mcp")
async def test_mcp_connection(
    query: str = Query(default="Test query"),
    _: bool = Depends(verify_admin_credentials)
):
    """Test MCP connection with a query"""
    try:
        import time
        start_time = time.time()
        
        response, status, latency_ms, retry_count = await mcp_client.query(
            user_text=query,
            context={"test": True}
        )
        
        return {
            "status": "ok",
            "mcp_response": response,
            "response_status": status,
            "latency_ms": latency_ms,
            "retry_count": retry_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"MCP test failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/maintenance/system-info")
async def get_system_info(
    _: bool = Depends(verify_admin_credentials)
):
    """Get system information"""
    try:
        import psutil
        import os
        
        # Get process info
        process = psutil.Process(os.getpid())
        
        # Memory info
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # CPU info
        cpu_percent = process.cpu_percent(interval=0.1)
        
        # Uptime
        create_time = datetime.fromtimestamp(process.create_time())
        uptime = datetime.utcnow() - create_time
        
        return {
            "memory_mb": round(memory_mb, 2),
            "cpu_percent": round(cpu_percent, 2),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime).split('.')[0],
            "version": settings.API_VERSION,
            "python_version": os.sys.version.split()[0]
        }
    
    except ImportError:
        # psutil not available
        return {
            "memory_mb": 0,
            "cpu_percent": 0,
            "uptime_seconds": 0,
            "uptime_human": "N/A",
            "version": settings.API_VERSION,
            "python_version": "N/A",
            "note": "Install psutil for detailed system info"
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system info")


# ============================================================
# Circuit Breaker Info
# ============================================================

@router.get("/maintenance/circuit-breaker")
async def get_circuit_breaker_status(
    _: bool = Depends(verify_admin_credentials)
):
    """Get circuit breaker status"""
    return {
        "enabled": settings.CIRCUIT_BREAKER_ENABLED,
        "is_open": mcp_client.circuit_open,
        "failure_count": mcp_client.failure_count,
        "failure_threshold": settings.CIRCUIT_FAILURE_THRESHOLD,
        "timeout_seconds": settings.CIRCUIT_TIMEOUT
    }


@router.post("/maintenance/circuit-breaker/reset")
async def reset_circuit_breaker(
    _: bool = Depends(verify_admin_credentials)
):
    """Reset circuit breaker"""
    mcp_client.circuit_open = False
    mcp_client.failure_count = 0
    
    logger.info("Circuit breaker manually reset")
    
    return {
        "status": "ok",
        "message": "Circuit breaker reset"
    }
