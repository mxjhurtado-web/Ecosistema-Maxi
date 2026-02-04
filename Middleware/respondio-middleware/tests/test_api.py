"""
Integration tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_ready_endpoint(self, client):
        """Test /ready endpoint"""
        response = client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root(self, client):
        """Test / endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data


class TestWebhookEndpoint:
    """Test webhook endpoint"""
    
    def test_webhook_missing_secret(self, client):
        """Test webhook without secret header"""
        response = client.post(
            "/webhook",
            json={
                "conversation_id": "test_conv",
                "contact_id": "test_contact",
                "channel": "whatsapp",
                "user_text": "Test message"
            }
        )
        
        assert response.status_code == 401
    
    def test_webhook_invalid_secret(self, client):
        """Test webhook with invalid secret"""
        response = client.post(
            "/webhook",
            headers={"X-Webhook-Secret": "wrong-secret"},
            json={
                "conversation_id": "test_conv",
                "contact_id": "test_contact",
                "channel": "whatsapp",
                "user_text": "Test message"
            }
        )
        
        assert response.status_code == 401
    
    def test_webhook_invalid_payload(self, client):
        """Test webhook with invalid payload"""
        response = client.post(
            "/webhook",
            headers={"X-Webhook-Secret": "change-me-in-production-use-strong-secret"},
            json={
                "conversation_id": "test_conv"
                # Missing required fields
            }
        )
        
        assert response.status_code == 422


class TestAdminEndpoints:
    """Test admin API endpoints"""
    
    def test_admin_without_auth(self, client):
        """Test admin endpoint without authentication"""
        response = client.get("/admin/config/mcp")
        
        assert response.status_code == 401
    
    def test_admin_with_auth(self, client):
        """Test admin endpoint with authentication"""
        response = client.get(
            "/admin/config/mcp",
            params={
                "username": "admin",
                "password": "change-me-in-production"
            }
        )
        
        # Should return config (even if Redis is not available)
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
    
    def test_telemetry_summary(self, client):
        """Test telemetry summary endpoint"""
        response = client.get(
            "/admin/telemetry/summary",
            params={
                "username": "admin",
                "password": "change-me-in-production"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
    
    def test_system_info(self, client):
        """Test system info endpoint"""
        response = client.get(
            "/admin/maintenance/system-info",
            params={
                "username": "admin",
                "password": "change-me-in-production"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "memory_mb" in data
        assert "cpu_percent" in data
