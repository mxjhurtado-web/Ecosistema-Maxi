"""
Decision Logger Module for Orbit FSM & Decision Auditing.
Handles recording and retrieving structured decision logs in Redis.
"""

import json
import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import DecisionLogEntry
from shared.redis_client import get_redis_client

logger = logging.getLogger(__name__)

DECISION_LOG_PREFIX = "decision_log:"
DECISION_LOG_INDEX = "decision_logs:index"
DECISION_LOG_TTL = 30 * 24 * 3600  # 30 days TTL


async def save_decision_log(entry: DecisionLogEntry) -> bool:
    """
    Saves a DecisionLogEntry to Redis under decision_log:<contact_id_or_case_id>
    and indexes it in a Redis sorted set for fast search by timestamp.
    """
    try:
        redis = await get_redis_client()
        if not redis:
            logger.warning("Redis client not available for decision logging")
            return False
            
        key_target = entry.contact_id or entry.case_id
        if not key_target:
            logger.warning("No contact_id or case_id provided for decision logging")
            return False

        key = f"{DECISION_LOG_PREFIX}{key_target}"
        
        # Format payload dictionary
        payload_dict = entry.model_dump() if hasattr(entry, 'model_dump') else entry.dict()
        # Convert datetime objects to ISO strings
        if isinstance(payload_dict.get("timestamp"), datetime):
            payload_dict["timestamp"] = payload_dict["timestamp"].isoformat()
            
        payload_str = json.dumps(payload_dict)
        
        # Append to Redis list for this conversation/case
        await redis.rpush(key, payload_str)
        await redis.expire(key, DECISION_LOG_TTL)
        
        # Add to index (ZSET by timestamp epoch)
        ts_val = entry.timestamp.timestamp() if isinstance(entry.timestamp, datetime) else datetime.utcnow().timestamp()
        index_member = f"{key_target}:{entry.trace_id}"
        await redis.zadd(DECISION_LOG_INDEX, {index_member: int(ts_val)})
        
        logger.info(f"💾 Decision Log saved [trace_id={entry.trace_id}] for key={key}")
        return True
    except Exception as e:
        logger.error(f"Error saving decision log: {e}", exc_info=True)
        return False


async def get_decision_logs(
    contact_id: Optional[str] = None,
    case_id: Optional[str] = None,
    rule_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Retrieves decision audit logs filtered by contact_id, case_id, or rule_id.
    """
    try:
        redis = await get_redis_client()
        if not redis:
            return {"total": 0, "logs": [], "limit": limit, "offset": offset}
            
        logs: List[Dict[str, Any]] = []
        target_keys = []
        
        if contact_id or case_id:
            target_key = contact_id or case_id
            target_keys.append(f"{DECISION_LOG_PREFIX}{target_key}")
        else:
            # Scan index to get recent conversation target IDs
            index_entries = await redis.zrevrange(DECISION_LOG_INDEX, 0, 300)
            seen_keys = set()
            for item in index_entries:
                item_str = item.decode('utf-8') if isinstance(item, bytes) else str(item)
                target_id = item_str.split(':')[0]
                k = f"{DECISION_LOG_PREFIX}{target_id}"
                if k not in seen_keys:
                    seen_keys.add(k)
                    target_keys.append(k)

        for k in target_keys:
            raw_entries = await redis.lrange(k, 0, -1)
            for raw in raw_entries:
                raw_str = raw.decode('utf-8') if isinstance(raw, bytes) else str(raw)
                try:
                    entry_dict = json.loads(raw_str)
                    if rule_id and entry_dict.get("winning_rule_id") != rule_id:
                        continue
                    logs.append(entry_dict)
                except Exception:
                    continue

        # Sort logs by timestamp descending
        logs.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
        
        total = len(logs)
        paginated_logs = logs[offset : offset + limit]
        
        return {
            "total": total,
            "logs": paginated_logs,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error fetching decision logs: {e}", exc_info=True)
        return {"total": 0, "logs": [], "error": str(e), "limit": limit, "offset": offset}
