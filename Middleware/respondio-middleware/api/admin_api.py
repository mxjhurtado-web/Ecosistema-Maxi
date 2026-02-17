"""
Admin API for dashboard management.
Provides endpoints for configuration, telemetry, and maintenance.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta

from .models import (
    SecurityConfig,
    RequestLog,
    ResponseStatus,
    HealthResponse,
    DashboardUser,
    UserRole,
    MCPConfig,
    CacheConfig,
    EmailAlertConfig,
    AuditLogEntry,
    AuditAction
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
    auth_username: str = Query(..., alias="username"),
    auth_password: str = Query(..., alias="password")
) -> DashboardUser:
    """Verify credentials against dynamic user list"""
    users = await config_manager.get_users()
    
    for user in users:
        if user.username == auth_username and user.password == auth_password:
            return user
            
    # Fallback to default if Redis is empty or no match (safety during setup)
    if auth_username == settings.DASHBOARD_USERNAME and auth_password == settings.DASHBOARD_PASSWORD:
        return DashboardUser(
            username=auth_username,
            password=auth_password,
            role=UserRole.ADMIN
        )
        
    raise HTTPException(status_code=401, detail="Invalid credentials")


async def require_admin_role(
    user: DashboardUser = Depends(verify_admin_credentials)
):
    """Ensure user has admin role"""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Permission denied: Admin role required")
    return user


# ============================================================
# Configuration Endpoints
# ============================================================

@router.get("/config/mcp", response_model=MCPConfig)
async def get_mcp_config(
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get current MCP configuration"""
    return await config_manager.get_mcp_config()


@router.put("/config/mcp")
async def update_mcp_config(
    config: MCPConfig,
    admin: DashboardUser = Depends(require_admin_role)
):
    """Update MCP configuration"""
    success = await config_manager.update_mcp_config(config)
    
    if success:
        # Audit log
        await config_manager.log_audit_action(AuditLogEntry(
            username=admin.username,
            role=admin.role,
            action=AuditAction.CONFIG_CHANGE,
            details=f"Updated MCP configuration: {config.url}"
        ))
        
        # Update MCP client with new config
        mcp_client.url = config.url
        mcp_client.timeout = config.timeout
        mcp_client.max_retries = config.max_retries
        mcp_client.mcp_token = config.mcp_token
        mcp_client.gemini_api_key = config.gemini_api_key
        
        # Update Keycloak Auth
        if config.use_keycloak and config.kc_server_url:
            from .auth import KeycloakAuthService
            mcp_client.kc_auth = KeycloakAuthService(
                server_url=config.kc_server_url,
                realm=config.kc_realm,
                client_id=config.kc_client_id,
                client_secret=config.kc_client_secret
            )
        else:
            mcp_client.kc_auth = None
        
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
    _: DashboardUser = Depends(verify_admin_credentials)
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


@router.get("/config/email", response_model=EmailAlertConfig)
async def get_email_config(_: DashboardUser = Depends(verify_admin_credentials)):
    """Get current email alert configuration"""
    return await config_manager.get_email_config()


@router.put("/config/email")
async def update_email_config(
    config: EmailAlertConfig,
    user: DashboardUser = Depends(require_admin_role)
):
    """Update email alert configuration"""
    success = await config_manager.update_email_config(config)
    
    if success:
        # Update email service instance settings if needed
        from .email_service import email_service
        email_service.enabled = config.enabled
        email_service.host = config.smtp_server
        email_service.port = config.smtp_port
        email_service.user = config.smtp_user
        email_service.password = config.smtp_password
        email_service.recipient = config.recipient_email
        
        # Audit log
        await config_manager.log_audit_action(AuditLogEntry(
            username=user.username,
            role=user.role,
            action=AuditAction.CONFIG_CHANGE,
            details="Updated email alerting configuration"
        ))
        
        return {"status": "ok", "message": "Email config updated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update config")


# ============================================================
# User Management Endpoints
# ============================================================

@router.get("/users", response_model=List[DashboardUser])
async def get_dashboard_users(
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get all dashboard users"""
    return await config_manager.get_users()


@router.post("/users")
async def add_dashboard_user(
    new_user: DashboardUser,
    admin: DashboardUser = Depends(require_admin_role)
):
    """Add or update a dashboard user with limit checks"""
    existing_users = await config_manager.get_users()
    
    # Check if we are updating or creating
    is_update = any(u.username == new_user.username for u in existing_users)
    
    if not is_update:
        # Enforce limits: Max 3 of each role
        admins = [u for u in existing_users if u.role == UserRole.ADMIN]
        supervisors = [u for u in existing_users if u.role == UserRole.SUPERVISOR]
        
        if new_user.role == UserRole.ADMIN and len(admins) >= 3:
            raise HTTPException(status_code=400, detail="Limit reached: Maximum 3 administrators allowed")
        
        if new_user.role == UserRole.SUPERVISOR and len(supervisors) >= 3:
            raise HTTPException(status_code=400, detail="Limit reached: Maximum 3 supervisors allowed")
            
    success = await config_manager.add_user(new_user)
    
    if success:
        # Audit log
        await config_manager.log_audit_action(AuditLogEntry(
            username=admin.username,
            role=admin.role,
            action=AuditAction.USER_MANAGEMENT,
            details=f"{'Updated' if is_update else 'Created'} user: {new_user.username} as {new_user.role}"
        ))
        return {"status": "ok", "message": f"User {new_user.username} {'updated' if is_update else 'created'}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save user")


@router.delete("/users/{username}")
async def delete_dashboard_user(
    username: str,
    admin: DashboardUser = Depends(require_admin_role)
):
    """Delete a dashboard user"""
    success = await config_manager.delete_user(username)
    
    if success:
        # Audit log
        await config_manager.log_audit_action(AuditLogEntry(
            username=admin.username,
            role=admin.role,
            action=AuditAction.USER_MANAGEMENT,
            details=f"Deleted user: {username}"
        ))
        return {"status": "ok", "message": f"User {username} deleted"}
    else:
        raise HTTPException(status_code=400, detail=f"Cannot delete user {username}")


# ============================================================
# Audit Log Endpoints
# ============================================================

@router.get("/audit/logs", response_model=List[AuditLogEntry])
async def get_audit_logs(
    limit: int = 100,
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get recent audit logs"""
    return await config_manager.get_audit_logs(limit)


@router.post("/audit/log")
async def log_audit_generic(
    action: AuditAction,
    details: str,
    user: DashboardUser = Depends(verify_admin_credentials)
):
    """Log a generic audit action from the frontend"""
    entry = AuditLogEntry(
        username=user.username,
        role=user.role,
        action=action,
        details=details
    )
    await config_manager.log_audit_action(entry)
    return {"status": "ok"}


# ============================================================
# Telemetry Endpoints
# ============================================================

@router.get("/telemetry/requests", response_model=List[RequestLog])
async def get_recent_requests(
    limit: int = Query(default=100, le=1000),
    status: Optional[ResponseStatus] = None,
    _: DashboardUser = Depends(verify_admin_credentials)
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
    _: DashboardUser = Depends(verify_admin_credentials)
):
    """Get hourly statistics"""
    return await telemetry_service.get_hourly_stats(hours)


@router.get("/telemetry/summary")
async def get_summary(
    _: DashboardUser = Depends(verify_admin_credentials)
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
    user: DashboardUser = Depends(require_admin_role)
):
    """Reload configuration from Redis"""
    success = await config_manager.reload_config()
    
    if success:
        await config_manager.log_audit_action(AuditLogEntry(
            username=user.username,
            role=user.role,
            action=AuditAction.SYSTEM_MAINTENANCE,
            details="Reloaded system configuration from Redis"
        ))
        return {"status": "ok", "message": "Configuration reloaded"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reload config")


@router.post("/maintenance/clear-cache")
async def clear_cache(
    user: DashboardUser = Depends(require_admin_role)
):
    """Clear all cached data"""
    success = await config_manager.clear_cache()
    
    if success:
        await config_manager.log_audit_action(AuditLogEntry(
            username=user.username,
            role=user.role,
            action=AuditAction.CACHE_CLEAR,
            details="Cleared all system cache"
        ))
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
    user: DashboardUser = Depends(require_admin_role)
):
    """Reset circuit breaker"""
    mcp_client.circuit_open = False
    mcp_client.failure_count = 0
    
    # Audit log
    await config_manager.log_audit_action(AuditLogEntry(
        username=user.username,
        role=user.role,
        action=AuditAction.CIRCUIT_RESET,
        details="Manually reset system circuit breaker"
    ))
    
    logger.info(f"Circuit breaker manually reset by {user.username}")
    
    return {
        "status": "ok",
        "message": "Circuit breaker reset"
    }
