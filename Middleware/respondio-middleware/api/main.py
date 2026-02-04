"""
Main FastAPI application - Middleware for Respond.io to MCP.
"""

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
from datetime import datetime
from typing import Optional
import logging

from .models import (
    RespondioRequest,
    RespondioResponse,
    ResponseStatus,
    RequestLog,
    HealthResponse
)
from .config import settings
from .mcp_client import mcp_client
from .telemetry import telemetry_service
from .admin_api import router as admin_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ORBIT - Integration Middleware",
    description="Production middleware connecting Respond.io to internal MCP",
    version=settings.API_VERSION
)

# Include admin router
app.include_router(admin_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Startup/Shutdown Events
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(f"🚀 Starting Respond.io Middleware v{settings.API_VERSION}")
    logger.info(f"MCP URL: {settings.MCP_URL}")
    logger.info(f"Cache enabled: {settings.CACHE_ENABLED}")
    logger.info(f"Circuit breaker enabled: {settings.CIRCUIT_BREAKER_ENABLED}")
    
    # Initialize Redis connection
    try:
        from shared.redis_client import get_redis_client
        redis = await get_redis_client()
        telemetry_service.redis = redis
        telemetry_service.enabled = True
        
        # Initialize config manager
        from .config_manager import config_manager
        config_manager.redis = redis
        config_manager.enabled = True
        
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {str(e)}")
        logger.warning("Telemetry and config management will be disabled")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down Respond.io Middleware")


# ============================================================
# Main Webhook Endpoint
# ============================================================

@app.post("/webhook", response_model=RespondioResponse)
async def webhook(
    request: RespondioRequest,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret")
):
    """
    Main webhook endpoint for Respond.io.
    
    Validates the request, calls MCP, and returns the response.
    """
    start_time = time.time()
    trace_id = str(uuid.uuid4())
    
    logger.info(
        f"📨 Webhook received",
        extra={
            "trace_id": trace_id,
            "conversation_id": request.conversation_id,
            "channel": request.channel
        }
    )
    
    # Validate webhook secret
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        logger.warning(
            f"❌ Invalid webhook secret",
            extra={"trace_id": trace_id}
        )
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    try:
        # Call MCP
        mcp_response, status, mcp_latency_ms, retry_count = await mcp_client.query(
            user_text=request.user_text,
            context={
                "conversation_id": request.conversation_id,
                "contact_id": request.contact_id,
                "channel": request.channel,
                **request.metadata
            }
        )
        
        # Calculate total latency
        total_latency_ms = int((time.time() - start_time) * 1000)
        
        # Log telemetry
        request_log = RequestLog(
            trace_id=trace_id,
            timestamp=datetime.utcnow(),
            conversation_id=request.conversation_id,
            contact_id=request.contact_id,
            channel=request.channel,
            user_text=request.user_text,
            mcp_response=mcp_response,
            status=status,
            latency_ms=total_latency_ms,
            mcp_latency_ms=mcp_latency_ms,
            error_message=None if status != ResponseStatus.ERROR else "MCP error",
            retry_count=retry_count
        )
        
        await telemetry_service.log_request(request_log)
        
        logger.info(
            f"✅ Webhook processed",
            extra={
                "trace_id": trace_id,
                "status": status,
                "latency_ms": total_latency_ms,
                "mcp_latency_ms": mcp_latency_ms,
                "retry_count": retry_count
            }
        )
        
        # Return response
        return RespondioResponse(
            status=status,
            reply_text=mcp_response,
            trace_id=trace_id,
            latency_ms=total_latency_ms
        )
    
    except Exception as e:
        # Handle unexpected errors
        total_latency_ms = int((time.time() - start_time) * 1000)
        
        logger.error(
            f"💥 Unexpected error",
            extra={
                "trace_id": trace_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        # Log error telemetry
        request_log = RequestLog(
            trace_id=trace_id,
            timestamp=datetime.utcnow(),
            conversation_id=request.conversation_id,
            contact_id=request.contact_id,
            channel=request.channel,
            user_text=request.user_text,
            mcp_response=None,
            status=ResponseStatus.ERROR,
            latency_ms=total_latency_ms,
            mcp_latency_ms=None,
            error_message=str(e),
            retry_count=0
        )
        
        await telemetry_service.log_request(request_log)
        
        # Return error response with fallback message
        return RespondioResponse(
            status=ResponseStatus.ERROR,
            reply_text="Lo siento, ocurrió un error inesperado. Por favor intenta nuevamente.",
            trace_id=trace_id,
            latency_ms=total_latency_ms
        )


# ============================================================
# Health Check Endpoints
# ============================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    
    # Check MCP health
    mcp_healthy = await mcp_client.health_check()
    mcp_status = "healthy" if mcp_healthy else "unhealthy"
    
    # Check Redis health
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


@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes/Cloud Run"""
    return {"status": "ready"}


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Respond.io ↔ MCP Middleware",
        "version": settings.API_VERSION,
        "status": "running",
        "endpoints": {
            "webhook": "POST /webhook",
            "health": "GET /health",
            "ready": "GET /ready",
            "admin": "GET /admin/* (requires auth)"
        }
    }


# ============================================================
# Error Handlers
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
