"""
Metrics calculation utilities.
"""

from typing import List, Dict
import pandas as pd


def calculate_percentile(values: List[float], percentile: int) -> float:
    """Calculate percentile"""
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    index = int(len(sorted_values) * (percentile / 100))
    return sorted_values[min(index, len(sorted_values) - 1)]


def calculate_success_rate(total: int, success: int) -> float:
    """Calculate success rate percentage"""
    if total == 0:
        return 0.0
    return round((success / total) * 100, 2)


def aggregate_hourly_stats(stats: List[Dict]) -> Dict:
    """Aggregate hourly statistics"""
    if not stats:
        return {
            "total_requests": 0,
            "success_count": 0,
            "error_count": 0,
            "avg_latency_ms": 0,
            "p95_latency_ms": 0,
            "p99_latency_ms": 0
        }
    
    total_requests = sum(s["total_requests"] for s in stats)
    success_count = sum(s["success_count"] for s in stats)
    error_count = sum(s["error_count"] for s in stats)
    
    # Weighted average latency
    total_latency = sum(s["avg_latency_ms"] * s["total_requests"] for s in stats)
    avg_latency = int(total_latency / total_requests) if total_requests > 0 else 0
    
    # Max percentiles
    p95_latency = max((s["p95_latency_ms"] for s in stats), default=0)
    p99_latency = max((s["p99_latency_ms"] for s in stats), default=0)
    
    return {
        "total_requests": total_requests,
        "success_count": success_count,
        "error_count": error_count,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "p99_latency_ms": p99_latency
    }


def format_uptime(seconds: int) -> str:
    """Format uptime in human-readable format"""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def format_bytes(bytes: int) -> str:
    """Format bytes in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"


def create_stats_dataframe(stats: List[Dict]) -> pd.DataFrame:
    """Create DataFrame from stats"""
    if not stats:
        return pd.DataFrame()
    
    df = pd.DataFrame(stats)
    df['hour'] = pd.to_datetime(df['hour'])
    df = df.sort_values('hour')
    
    return df
