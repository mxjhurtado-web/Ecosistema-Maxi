"""
Unit tests for Pydantic models
"""

import pytest
from api.models import (
    RespondioRequest,
    RespondioResponse,
    MCPRequest,
    MCPResponse,
    ResponseStatus,
    MCPConfig,
    CacheConfig,
    SecurityConfig
)


class TestRespondioRequest:
    """Test RespondioRequest model"""
    
    def test_valid_request(self):
        """Test creating a valid request"""
        request = RespondioRequest(
            conversation_id="conv_123",
            contact_id="contact_456",
            channel="whatsapp",
            user_text="Hello world",
            metadata={"key": "value"}
        )
        
        assert request.conversation_id == "conv_123"
        assert request.contact_id == "contact_456"
        assert request.channel == "whatsapp"
        assert request.user_text == "Hello world"
        assert request.metadata == {"key": "value"}
    
    def test_minimal_request(self):
        """Test request with minimal fields"""
        request = RespondioRequest(
            conversation_id="conv_123",
            contact_id="contact_456",
            channel="whatsapp",
            user_text="Hello"
        )
        
        assert request.metadata == {}
    
    def test_empty_user_text_fails(self):
        """Test that empty user_text fails validation"""
        with pytest.raises(ValueError):
            RespondioRequest(
                conversation_id="conv_123",
                contact_id="contact_456",
                channel="whatsapp",
                user_text=""
            )


class TestRespondioResponse:
    """Test RespondioResponse model"""
    
    def test_success_response(self):
        """Test creating a success response"""
        response = RespondioResponse(
            status=ResponseStatus.OK,
            response="Test response",
            latency_ms=100,
            trace_id="trace_123"
        )
        
        assert response.status == ResponseStatus.OK
        assert response.response == "Test response"
        assert response.latency_ms == 100
        assert response.trace_id == "trace_123"
    
    def test_error_response(self):
        """Test creating an error response"""
        response = RespondioResponse(
            status=ResponseStatus.ERROR,
            response="Fallback message",
            latency_ms=0,
            trace_id="trace_456",
            error_message="MCP timeout"
        )
        
        assert response.status == ResponseStatus.ERROR
        assert response.error_message == "MCP timeout"


class TestMCPRequest:
    """Test MCPRequest model"""
    
    def test_valid_mcp_request(self):
        """Test creating a valid MCP request"""
        request = MCPRequest(
            query="Test query",
            context={"channel": "whatsapp"}
        )
        
        assert request.query == "Test query"
        assert request.context == {"channel": "whatsapp"}
    
    def test_empty_context(self):
        """Test MCP request with empty context"""
        request = MCPRequest(query="Test")
        assert request.context == {}


class TestMCPResponse:
    """Test MCPResponse model"""
    
    def test_valid_mcp_response(self):
        """Test creating a valid MCP response"""
        response = MCPResponse(
            response="MCP answer",
            confidence=0.95
        )
        
        assert response.response == "MCP answer"
        assert response.confidence == 0.95
    
    def test_default_confidence(self):
        """Test default confidence value"""
        response = MCPResponse(response="Answer")
        assert response.confidence == 0.95


class TestConfigModels:
    """Test configuration models"""
    
    def test_mcp_config(self):
        """Test MCP configuration"""
        config = MCPConfig(
            url="http://mcp:8080/query",
            timeout=10,
            max_retries=5,
            retry_delay=2
        )
        
        assert config.url == "http://mcp:8080/query"
        assert config.timeout == 10
        assert config.max_retries == 5
        assert config.retry_delay == 2
    
    def test_cache_config(self):
        """Test cache configuration"""
        config = CacheConfig(
            enabled=True,
            ttl=600,
            max_size=2000
        )
        
        assert config.enabled is True
        assert config.ttl == 600
        assert config.max_size == 2000
    
    def test_security_config(self):
        """Test security configuration"""
        config = SecurityConfig(
            webhook_secret="test-secret",
            rate_limit=200
        )
        
        assert config.webhook_secret == "test-secret"
        assert config.rate_limit == 200
