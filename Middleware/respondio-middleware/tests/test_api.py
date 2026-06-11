"""
Integration tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.config import settings


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
            headers={"X-Webhook-Secret": settings.WEBHOOK_SECRET},
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
        response = client.get(
            "/admin/config/mcp",
            params={
                "username": "wrong_user",
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == 401
    
    def test_admin_with_auth(self, client):
        """Test admin endpoint with authentication"""
        response = client.get(
            "/admin/config/mcp",
            params={
                "username": settings.DASHBOARD_USERNAME,
                "password": settings.DASHBOARD_PASSWORD
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
                "username": settings.DASHBOARD_USERNAME,
                "password": settings.DASHBOARD_PASSWORD
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
                "username": settings.DASHBOARD_USERNAME,
                "password": settings.DASHBOARD_PASSWORD
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "memory_mb" in data
        assert "cpu_percent" in data


class TestGoogleChatNotifyEndpoint:
    """Test /google-chat/notify endpoint"""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Setup patches for google_chat_service and redis"""
        from unittest.mock import patch, AsyncMock
        
        # Mock send_alert_detailed
        self.mock_send = AsyncMock(return_value=(True, "Message sent successfully"))
        self.patcher_send = patch("api.google_chat_service.google_chat_service.send_alert_detailed", self.mock_send)
        self.patcher_send.start()
        
        # Mock redis
        self.mock_redis = AsyncMock()
        self.mock_redis.get.return_value = None
        self.patcher_redis = patch("shared.redis_client.get_redis_client", AsyncMock(return_value=self.mock_redis))
        self.patcher_redis.start()
        
        yield
        
        self.patcher_send.stop()
        self.patcher_redis.stop()

    def test_notify_with_header_secret(self, client):
        """Test notify success using header secret"""
        response = client.post(
            "/google-chat/notify",
            headers={"X-Webhook-Secret": settings.WEBHOOK_SECRET},
            json={
                "message": "Test message",
                "level": "INFO",
                "destino": "soporte"
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        self.mock_send.assert_called_once()

    def test_notify_with_query_secret(self, client):
        """Test notify success using query parameter secret"""
        response = client.post(
            f"/google-chat/notify?secret={settings.WEBHOOK_SECRET}",
            json={
                "message": "Test message",
                "level": "INFO",
                "destino": "soporte"
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_notify_unauthorized(self, client):
        """Test notify unauthorized when secret is missing or incorrect"""
        response = client.post(
            "/google-chat/notify",
            json={
                "message": "Test message",
                "level": "INFO",
                "destino": "soporte"
            }
        )
        assert response.status_code == 401

        response = client.post(
            "/google-chat/notify?secret=wrong-secret",
            json={
                "message": "Test message",
                "level": "INFO",
                "destino": "soporte"
            }
        )
        assert response.status_code == 401

    def test_notify_destino_cumplimiento(self, client):
        """Test mapping of cumplimiento destination"""
        import os
        from unittest.mock import patch
        
        # Override env variable for cumplimiento
        with patch.dict(os.environ, {"GOOGLE_CHATS_CUMPLIMIENTO_SPACE": "spaces/test-cumplimiento"}):
            response = client.post(
                f"/google-chat/notify?secret={settings.WEBHOOK_SECRET}",
                json={
                    "message": "Test message",
                    "level": "INFO",
                    "destino": "cumplimiento"
                }
            )
            assert response.status_code == 200
            
            # Verify that the target space was resolved to spaces/test-cumplimiento
            args, kwargs = self.mock_send.call_args
            assert kwargs.get("space_id") == "spaces/test-cumplimiento"

    def test_notify_with_pdf_attachment(self, client):
        """Test notify formatting with PDF attachment"""
        response = client.post(
            f"/google-chat/notify?secret={settings.WEBHOOK_SECRET}",
            json={
                "message": "Test document check",
                "level": "INFO",
                "destino": "cumplimiento",
                "media_url": "https://example.com/document.pdf"
            }
        )
        assert response.status_code == 200
        
        # Verify that the target space and formatted text are correct
        args, kwargs = self.mock_send.call_args
        assert "📄 *Adjunto:*" in kwargs.get("message")
