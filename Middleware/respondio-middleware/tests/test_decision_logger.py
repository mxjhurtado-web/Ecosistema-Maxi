import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from api.decision_logger import save_decision_log, get_decision_logs
from api.models import DecisionLogEntry

@pytest.mark.asyncio
async def test_save_and_get_decision_logs():
    fake_redis = AsyncMock()
    fake_redis.rpush = AsyncMock()
    fake_redis.expire = AsyncMock()
    fake_redis.zadd = AsyncMock()
    fake_redis.lrange = AsyncMock(return_value=[
        b'{"trace_id": "test-123", "timestamp": "2026-08-03T20:00:00", "case_id": "test_case", "contact_id": "12345", "winning_rule_id": "RULE-1", "action_taken": "ALLOW"}'
    ])

    with patch("shared.redis_client.get_redis_client", return_value=fake_redis):
        entry = DecisionLogEntry(
            trace_id="test-123",
            contact_id="12345",
            case_id="test_case",
            winning_rule_id="RULE-1",
            action_taken="ALLOW",
            timestamp=datetime.utcnow()
        )
        # Test logging
        saved = await save_decision_log(entry)
        assert saved is True
        assert fake_redis.rpush.called

        # Test querying
        logs = await get_decision_logs(contact_id="12345")
        assert logs["total"] == 1
        assert logs["logs"][0]["case_id"] == "test_case"
