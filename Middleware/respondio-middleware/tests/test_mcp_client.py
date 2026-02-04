"""
Unit tests for MCP client
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from api.mcp_client import MCPClient
from api.models import ResponseStatus


@pytest.fixture
def mcp_client():
    """Create MCP client instance"""
    return MCPClient()


@pytest.mark.asyncio
class TestMCPClient:
    """Test MCP client functionality"""
    
    async def test_successful_query(self, mcp_client):
        """Test successful MCP query"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "Test response",
                "confidence": 0.95
            }
            mock_response.raise_for_status = MagicMock()
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            # Execute query
            response, status, latency, retries = await mcp_client.query("Test query")
            
            # Assertions
            assert response == "Test response"
            assert status in [ResponseStatus.OK, ResponseStatus.DEGRADED]
            assert latency > 0
            assert retries == 0
    
    async def test_query_with_retry(self, mcp_client):
        """Test query with retry on failure"""
        with patch('httpx.AsyncClient') as mock_client:
            # First call fails, second succeeds
            mock_response_fail = MagicMock()
            mock_response_fail.raise_for_status.side_effect = Exception("Timeout")
            
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {
                "response": "Success after retry",
                "confidence": 0.95
            }
            mock_response_success.raise_for_status = MagicMock()
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=[mock_response_fail, mock_response_success]
            )
            
            # Execute query
            response, status, latency, retries = await mcp_client.query("Test query")
            
            # Should succeed after retry
            assert response == "Success after retry"
            assert retries > 0
    
    async def test_circuit_breaker_opens(self, mcp_client):
        """Test circuit breaker opens after failures"""
        # Set low threshold for testing
        mcp_client.failure_count = 5
        mcp_client.circuit_open = True
        mcp_client.circuit_open_time = asyncio.get_event_loop().time()
        
        # Query should return fallback immediately
        response, status, latency, retries = await mcp_client.query("Test query")
        
        assert status == ResponseStatus.ERROR
        assert "temporalmente no disponible" in response.lower()
        assert retries == 0
    
    async def test_health_check_success(self, mcp_client):
        """Test successful health check"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            is_healthy = await mcp_client.health_check()
            assert is_healthy is True
    
    async def test_health_check_failure(self, mcp_client):
        """Test failed health check"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Connection failed")
            )
            
            is_healthy = await mcp_client.health_check()
            assert is_healthy is False
