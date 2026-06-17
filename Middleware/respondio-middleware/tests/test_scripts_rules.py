import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from api.main import app
from api.config import settings

@pytest.fixture
def client():
    return TestClient(app)

class TestScriptsAndRules:
    """Test suite for dynamic scripts and rules endpoints"""

    @patch("api.main.get_redis_client", new_callable=AsyncMock)
    @patch("api.google_sheets_service.google_sheets_service.fetch_official_scripts", new_callable=AsyncMock)
    def test_get_scripts_uncached(self, mock_fetch_sheets, mock_get_redis, client):
        """Test getting scripts when not cached in Redis"""
        # Setup mocks
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Redis miss
        mock_get_redis.return_value = mock_redis
        
        mock_fetch_sheets.return_value = {
            "SC.001": "Hello, how can I help you?",
            "CU.A1": "Privacy policy text..."
        }

        # Request
        response = client.get("/api/v1/scripts?codes=SC.001,CU.A1")
        assert response.status_code == 200
        data = response.json()
        assert data["SC.001"] == "Hello, how can I help you?"
        assert data["CU.A1"] == "Privacy policy text..."

        # Verify Google Sheet was fetched
        mock_fetch_sheets.assert_called_once_with(settings.GOOGLE_SHEET_ID_SCRIPTS)
        mock_redis.setex.assert_called_once()

    @patch("api.main.get_redis_client", new_callable=AsyncMock)
    @patch("api.google_sheets_service.google_sheets_service.fetch_official_scripts", new_callable=AsyncMock)
    def test_get_scripts_cached(self, mock_fetch_sheets, mock_get_redis, client):
        """Test getting scripts from Redis cache directly"""
        # Setup mocks
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b'{"SC.001": "Cached Greeting", "CU.A1": "Cached Privacy"}'
        mock_get_redis.return_value = mock_redis

        # Request
        response = client.get("/api/v1/scripts?codes=SC.001,CU.A1")
        assert response.status_code == 200
        data = response.json()
        assert data["SC.001"] == "Cached Greeting"
        assert data["CU.A1"] == "Cached Privacy"

        # Verify Google Sheet was NOT fetched
        mock_fetch_sheets.assert_not_called()

    @patch("api.main.get_redis_client", new_callable=AsyncMock)
    @patch("api.google_sheets_service.google_sheets_service.fetch_business_rules", new_callable=AsyncMock)
    def test_get_rules(self, mock_fetch_rules, mock_get_redis, client):
        """Test getting business rules"""
        # Setup mocks
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Redis miss
        mock_get_redis.return_value = mock_redis
        
        mock_fetch_rules.return_value = {
            "RNE.01": "Routing rule description..."
        }

        # Request
        response = client.get("/api/v1/rules?codes=RNE.01")
        assert response.status_code == 200
        data = response.json()
        assert data["RNE.01"] == "Routing rule description..."

        mock_fetch_rules.assert_called_once_with(settings.GOOGLE_SHEET_ID_REGLAS)

    @patch("api.main.get_redis_client", new_callable=AsyncMock)
    def test_sync_clears_cache(self, mock_get_redis, client):
        """Test that POST /api/v1/scripts/sync deletes cache keys"""
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis

        response = client.post("/api/v1/scripts/sync")
        assert response.status_code == 200
        assert "success" in response.json()["status"]
        
        # Verify keys were deleted
        mock_redis.delete.assert_any_call("google_sheets:scripts_cache")
        mock_redis.delete.assert_any_call("google_sheets:rules_cache")
