"""
Telemetry and logging system using Redis.
"""

import json
import time
from datetime import datetime
from typing import List, Optional
from .models import RequestLog, ResponseStatus
from .config import settings
import logging

logger = logging.getLogger(__name__)


class TelemetryService:
    """Service for storing and querying telemetry data"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.enabled = redis_client is not None
    
    async def log_request(self, request_log: RequestLog):
        """Log a processed request"""
        if not self.enabled:
            logger.warning("Telemetry disabled (no Redis connection)")
            return
        
        try:
            # Store in Redis with TTL (7 days)
            key = f"request:{request_log.trace_id}"
            value = request_log.model_dump_json()
            
            await self.redis.setex(key, 7 * 24 * 60 * 60, value)
            
            # Add to sorted set for time-based queries
            timestamp = int(request_log.timestamp.timestamp())
            await self.redis.zadd("requests:timeline", {request_log.trace_id: timestamp})
            
            # Update hourly aggregations
            await self._update_hourly_stats(request_log)
            
            logger.debug(f"Request logged: {request_log.trace_id}")
            
        except Exception as e:
            logger.error(f"Failed to log request: {str(e)}")
    
    async def _update_hourly_stats(self, request_log: RequestLog):
        """Update hourly aggregated statistics"""
        try:
            # Get hour key
            hour = request_log.timestamp.replace(minute=0, second=0, microsecond=0)
            hour_key = f"stats:hour:{hour.isoformat()}"
            
            # Increment counters
            await self.redis.hincrby(hour_key, "total_requests", 1)
            
            if request_log.status == ResponseStatus.OK:
                await self.redis.hincrby(hour_key, "success_count", 1)
            else:
                await self.redis.hincrby(hour_key, "error_count", 1)
            
            # Update latency sum (for average calculation)
            await self.redis.hincrby(hour_key, "latency_sum", request_log.latency_ms)
            
            # Store latencies for percentile calculation
            await self.redis.rpush(f"{hour_key}:latencies", request_log.latency_ms)
            
            # Set TTL (30 days)
            await self.redis.expire(hour_key, 30 * 24 * 60 * 60)
            await self.redis.expire(f"{hour_key}:latencies", 30 * 24 * 60 * 60)
            
        except Exception as e:
            logger.error(f"Failed to update hourly stats: {str(e)}")
    
    async def get_recent_requests(
        self, 
        limit: int = 100,
        status_filter: Optional[ResponseStatus] = None
    ) -> List[RequestLog]:
        """Get recent requests"""
        if not self.enabled:
            return []
        
        try:
            # Get recent trace IDs from sorted set
            trace_ids = await self.redis.zrevrange("requests:timeline", 0, limit - 1)
            
            # Fetch request details
            requests = []
            for trace_id in trace_ids:
                key = f"request:{trace_id.decode()}"
                data = await self.redis.get(key)
                
                if data:
                    request_log = RequestLog(**json.loads(data))
                    
                    # Apply filter
                    if status_filter is None or request_log.status == status_filter:
                        requests.append(request_log)
            
            return requests
            
        except Exception as e:
            logger.error(f"Failed to get recent requests: {str(e)}")
            return []
    
    async def get_request_by_trace_id(self, trace_id: str) -> Optional[RequestLog]:
        """Get a specific request by trace ID"""
        if not self.enabled:
            return None
        
        try:
            key = f"request:{trace_id}"
            data = await self.redis.get(key)
            
            if data:
                return RequestLog(**json.loads(data))
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get request: {str(e)}")
            return None
    
    async def get_hourly_stats(self, hours: int = 24) -> List[dict]:
        """Get hourly statistics for the last N hours"""
        if not self.enabled:
            return []
        
        try:
            stats = []
            now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            
            for i in range(hours):
                hour = now - timedelta(hours=i)
                hour_key = f"stats:hour:{hour.isoformat()}"
                
                data = await self.redis.hgetall(hour_key)
                
                if data:
                    total = int(data.get(b"total_requests", 0))
                    success = int(data.get(b"success_count", 0))
                    errors = int(data.get(b"error_count", 0))
                    latency_sum = int(data.get(b"latency_sum", 0))
                    
                    avg_latency = latency_sum // total if total > 0 else 0
                    
                    # Get latencies for percentiles
                    latencies_key = f"{hour_key}:latencies"
                    latencies = await self.redis.lrange(latencies_key, 0, -1)
                    latencies = sorted([int(l) for l in latencies])
                    
                    p50 = latencies[len(latencies) // 2] if latencies else 0
                    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
                    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
                    
                    stats.append({
                        "hour": hour.isoformat(),
                        "total_requests": total,
                        "success_count": success,
                        "error_count": errors,
                        "avg_latency_ms": avg_latency,
                        "p50_latency_ms": p50,
                        "p95_latency_ms": p95,
                        "p99_latency_ms": p99
                    })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get hourly stats: {str(e)}")
            return []


from datetime import timedelta

# Singleton instance (will be initialized with Redis client)
telemetry_service = TelemetryService()
