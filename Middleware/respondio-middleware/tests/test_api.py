"""
Integration tests for API endpoints
"""

import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock
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


class TestStatusCheckEndpoint:
    """Test /api/v1/status/check endpoint"""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        # Mock Redis
        self.mock_redis = AsyncMock()
        self.mock_redis.get.return_value = None
        self.patcher_redis = patch("api.main.get_redis_client", AsyncMock(return_value=self.mock_redis))
        self.patcher_redis.start()
        
        # Mock httpx.AsyncClient
        self.mock_httpx = AsyncMock()
        self.patcher_httpx = patch("httpx.AsyncClient.get", self.mock_httpx)
        self.patcher_httpx.start()
        
        # Prevent actual psycopg2 connection
        self.original_uri = settings.SUPABASE_URI
        settings.SUPABASE_URI = None

        yield
        
        self.patcher_redis.stop()
        self.patcher_httpx.stop()
        settings.SUPABASE_URI = self.original_uri

    def test_unauthorized(self, client):
        """Test status check unauthorized without correct secret"""
        response = client.post(
            "/api/v1/status/check",
            json={
                "contact_id": "test_contact",
                "user_text": "ver CE12345678"
            }
        )
        assert response.status_code == 401

    def test_code_not_found_first_attempt(self, client):
        """Test status check when code is not found on first attempt"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        self.mock_httpx.return_value = mock_response
        self.mock_redis.get.return_value = None

        response = client.post(
            f"/api/v1/status/check?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact_id": "test_contact",
                "user_text": "ver CE12345678"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["derivacion"] == "NA"
        assert "No encontré resultados" in data["reply_text"]
        assert data["validation_success"] is False
        self.mock_redis.set.assert_called_with("status_attempts:test_contact", "1", ex=3600)

    def test_code_not_found_second_attempt(self, client):
        """Test status check when code is not found on second attempt (limit reached)"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        self.mock_httpx.return_value = mock_response
        self.mock_redis.get.return_value = b"1"

        response = client.post(
            f"/api/v1/status/check?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact_id": "test_contact",
                "user_text": "ver CE12345678"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["derivacion"] == "Servicio al Cliente"
        assert "No fue posible procesar su solicitud" in data["reply_text"]
        assert data["validation_success"] is False
        self.mock_redis.set.assert_any_call("status_attempts:test_contact", "0", ex=3600)

    def test_successful_remesa_paid(self, client):
        """Test successful lookup for remesa status PAGADO"""
        record = {
            "Codigo_de_envio": "CE12345678",
            "status": "PAGADO",
            "Nombre_Cliente": "JUAN",
            "Cliente_ Apellido_Paterno": "PEREZ",
            "Cliente_Apellido_Materno": "GOMEZ",
            "Beneficiario_Nombre": "MARIA",
            "Benerificario_Primer_Apellido": "RODRIGUEZ",
            "Beneficiario_Segundo_Apellido": ""
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [record]
        self.mock_httpx.return_value = mock_response

        response = client.post(
            f"/api/v1/status/check?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact_id": "test_contact",
                "user_text": "ver CE12345678",
                "nombre_remitente": "JUAN PEREZ",
                "perfil": "CLIENTE"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["derivacion"] == "NA"
        assert "pagado" in data["reply_text"].lower()
        assert data["validation_success"] is True

    def test_name_mismatch_first_attempt(self, client):
        """Test status check when names don't match on first attempt"""
        record = {
            "Codigo_de_envio": "CE12345678",
            "status": "PAYMENT READY",
            "Nombre_Cliente": "JUAN",
            "Cliente_ Apellido_Paterno": "PEREZ",
            "Cliente_Apellido_Materno": "GOMEZ",
            "Beneficiario_Nombre": "MARIA",
            "Benerificario_Primer_Apellido": "RODRIGUEZ",
            "Beneficiario_Segundo_Apellido": ""
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [record]
        self.mock_httpx.return_value = mock_response
        self.mock_redis.get.return_value = None

        response = client.post(
            f"/api/v1/status/check?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact_id": "test_contact",
                "user_text": "ver CE12345678",
                "nombre_remitente": "WRONG SENDER NAME",
                "perfil": "CLIENTE"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["derivacion"] == "NA"
        assert "no coinciden con nuestros registros" in data["reply_text"]
        assert data["validation_success"] is False
        self.mock_redis.set.assert_any_call("name_attempts:test_contact", "1", ex=3600)

    def test_name_mismatch_second_attempt(self, client):
        """Test status check when names don't match on second attempt (handoff)"""
        record = {
            "Codigo_de_envio": "CE12345678",
            "status": "PAYMENT READY",
            "Nombre_Cliente": "JUAN",
            "Cliente_ Apellido_Paterno": "PEREZ",
            "Cliente_Apellido_Materno": "GOMEZ",
            "Beneficiario_Nombre": "MARIA",
            "Benerificario_Primer_Apellido": "RODRIGUEZ",
            "Beneficiario_Segundo_Apellido": ""
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [record]
        self.mock_httpx.return_value = mock_response
        self.mock_redis.get.return_value = b"1"

        response = client.post(
            f"/api/v1/status/check?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact_id": "test_contact",
                "user_text": "ver CE12345678",
                "nombre_remitente": "WRONG SENDER NAME",
                "perfil": "CLIENTE"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["derivacion"] == "Servicio al Cliente"
        assert "No fue posible validar su identidad" in data["reply_text"]
        assert data["validation_success"] is False
        self.mock_redis.set.assert_any_call("name_attempts:test_contact", "0", ex=3600)

    def test_compliance_hours_routing_open(self, client):
        """Test compliance hold routing during business hours"""
        record = {
            "Codigo_de_envio": "CE12345678",
            "status": "VERIFY HOLD (O)",
            "Nombre_Cliente": "JUAN",
            "Cliente_ Apellido_Paterno": "PEREZ",
            "Cliente_Apellido_Materno": "GOMEZ",
            "Beneficiario_Nombre": "MARIA",
            "Benerificario_Primer_Apellido": "RODRIGUEZ",
            "Beneficiario_Segundo_Apellido": ""
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [record]
        self.mock_httpx.return_value = mock_response

        # Mock get_central_time to return a time during working hours
        mock_dt = datetime(2026, 6, 16, 12, 0, 0)
        from unittest.mock import patch
        with patch("api.main.get_central_time", return_value=mock_dt):
            response = client.post(
                f"/api/v1/status/check?secret={settings.WEBHOOK_SECRET}",
                json={
                    "contact_id": "test_contact",
                    "user_text": "ver CE12345678",
                    "nombre_remitente": "JUAN PEREZ",
                    "perfil": "CLIENTE"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["derivacion"] == "Cumplimiento"
            assert "Cumplimiento" in data["reply_text"]

    def test_compliance_hours_routing_closed(self, client):
        """Test compliance hold routing outside business hours"""
        record = {
            "Codigo_de_envio": "CE12345678",
            "status": "VERIFY HOLD (O)",
            "Nombre_Cliente": "JUAN",
            "Cliente_ Apellido_Paterno": "PEREZ",
            "Cliente_Apellido_Materno": "GOMEZ",
            "Beneficiario_Nombre": "MARIA",
            "Benerificario_Primer_Apellido": "RODRIGUEZ",
            "Beneficiario_Segundo_Apellido": ""
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [record]
        self.mock_httpx.return_value = mock_response

        # Mock get_central_time to return a time outside working hours (e.g. 1:00 AM)
        mock_dt = datetime(2026, 6, 16, 1, 0, 0)
        from unittest.mock import patch
        with patch("api.main.get_central_time", return_value=mock_dt):
            response = client.post(
                f"/api/v1/status/check?secret={settings.WEBHOOK_SECRET}",
                json={
                    "contact_id": "test_contact",
                    "user_text": "ver CE12345678",
                    "nombre_remitente": "JUAN PEREZ",
                    "perfil": "CLIENTE"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["derivacion"] == "Fuera de Horario Depto"
            assert "por el momento no se encuentra disponible" in data["reply_text"]

    def test_emergency_overflow_kyc_routing(self, client):
        """Test RNE.56 emergency routing for KYC holds when Fraud is closed but SC is open"""
        record = {
            "Codigo_de_envio": "CE12345678",
            "status": "VERIFY HOLD (KYC)",
            "Nombre_Cliente": "JUAN",
            "Cliente_ Apellido_Paterno": "PEREZ",
            "Cliente_Apellido_Materno": "GOMEZ",
            "Beneficiario_Nombre": "MARIA",
            "Benerificario_Primer_Apellido": "RODRIGUEZ",
            "Beneficiario_Segundo_Apellido": ""
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [record]
        self.mock_httpx.return_value = mock_response

        from unittest.mock import patch
        
        def mock_check_dept(depto, dt):
            if "PREVENCION" in depto or "FRAUD" in depto:
                return False
            if "SERVICIO" in depto or "SC" in depto:
                return True
            return False

        with patch("api.main.check_department_hours", side_effect=mock_check_dept):
            response = client.post(
                f"/api/v1/status/check?secret={settings.WEBHOOK_SECRET}",
                json={
                    "contact_id": "test_contact",
                    "user_text": "ver CE12345678",
                    "nombre_remitente": "JUAN PEREZ",
                    "perfil": "CLIENTE"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["derivacion"] == "Servicio al Cliente"
            assert "Desborde de Emergencia por Horario" in data["reply_text"]

    def test_status_check_stale_data_isolation(self, client):
        """Test status check ignores stale data when session active but code/names not in session text"""
        # Mock Redis get to return "hola" (session active, but code/names missing)
        async def mock_redis_get(key):
            if "session_text" in key:
                return b"hola"
            return None
            
        self.mock_redis.get.side_effect = mock_redis_get

        response = client.post(
            f"/api/v1/status/check?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact_id": "test_contact",
                "user_text": "",
                "nombre_remitente": "JUAN PEREZ",
                "codigo_envio": "CE12345678",
                "perfil": "CLIENTE"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["derivacion"] == "NA"
        assert "No encontré resultados" in data["reply_text"]
        assert data["validation_success"] is False

    def test_status_check_fresh_data_in_session(self, client):
        """Test status check accepts data when present in session text"""
        # Mock Redis get to return session text containing the code and name
        async def mock_redis_get(key):
            if "session_text" in key:
                return b"hola, mi codigo es CE12345678 y soy JUAN PEREZ"
            return None
            
        self.mock_redis.get.side_effect = mock_redis_get

        record = {
            "Codigo_de_envio": "CE12345678",
            "status": "PAGADO",
            "Nombre_Cliente": "JUAN",
            "Cliente_ Apellido_Paterno": "PEREZ",
            "Cliente_Apellido_Materno": "GOMEZ",
            "Beneficiario_Nombre": "MARIA",
            "Benerificario_Primer_Apellido": "RODRIGUEZ",
            "Beneficiario_Segundo_Apellido": ""
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.value = [record]
        mock_response.json.return_value = [record]
        self.mock_httpx.return_value = mock_response

        response = client.post(
            f"/api/v1/status/check?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact_id": "test_contact",
                "user_text": "",
                "nombre_remitente": "JUAN PEREZ",
                "codigo_envio": "CE12345678",
                "perfil": "CLIENTE"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["derivacion"] == "NA"
        assert "pagado" in data["reply_text"].lower()
        assert data["validation_success"] is True


class TestGlobalWebhookSessionTracking:
    """Test session text tracking and greeting cleanup in global webhook"""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.mock_redis = AsyncMock()
        self.mock_redis.get.return_value = None
        self.patcher_redis = patch("api.main.get_redis_client", AsyncMock(return_value=self.mock_redis))
        self.patcher_redis.start()
        yield
        self.patcher_redis.stop()

    def test_global_webhook_saves_session_text(self, client):
        """Test global webhook saves message text to Redis session text"""
        response = client.post(
            f"/webhook?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact": {"id": "test_contact_123"},
                "message": {
                    "messageId": "msg_001",
                    "message": {
                        "type": "text",
                        "text": "quiero ver mi estatus"
                    }
                }
            }
        )
        assert response.status_code == 200
        self.mock_redis.get.assert_any_call("contact:session_text:test_contact_123")
        self.mock_redis.set.assert_any_call("contact:session_text:test_contact_123", "quiero ver mi estatus", ex=7200)

    def test_global_webhook_greeting_clears_keys(self, client):
        """Test global webhook greeting clears old Redis keys"""
        response = client.post(
            f"/webhook?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact": {"id": "test_contact_123"},
                "message": {
                    "messageId": "msg_002",
                    "message": {
                        "type": "text",
                        "text": "hola"
                    }
                }
            }
        )
        assert response.status_code == 200
        self.mock_redis.delete.assert_any_call("contact:session_text:test_contact_123")
        self.mock_redis.delete.assert_any_call("contact:last_image:test_contact_123")
        self.mock_redis.delete.assert_any_call("status_attempts:test_contact_123")
        self.mock_redis.delete.assert_any_call("name_attempts:test_contact_123")


class TestBillCheckEndpoint:
    """Test /api/v1/bill/check endpoint"""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        # Mock Redis
        self.mock_redis = AsyncMock()
        self.mock_redis.get.return_value = None
        self.patcher_redis = patch("api.main.get_redis_client", AsyncMock(return_value=self.mock_redis))
        self.patcher_redis.start()
        
        # Mock httpx.AsyncClient
        self.mock_httpx = AsyncMock()
        self.patcher_httpx = patch("httpx.AsyncClient.get", self.mock_httpx)
        self.patcher_httpx.start()
        
        # Prevent actual psycopg2 connection
        self.original_uri = settings.SUPABASE_URI
        settings.SUPABASE_URI = None

        yield
        
        self.patcher_redis.stop()
        self.patcher_httpx.stop()
        settings.SUPABASE_URI = self.original_uri

    def test_unauthorized(self, client):
        """Test bill status check unauthorized without correct secret"""
        response = client.post(
            "/api/v1/bill/check",
            json={
                "contact_id": "test_contact",
                "user_text": "",
                "tracking_number": "TRK12345678"
            }
        )
        assert response.status_code == 401

    @patch("api.google_sheets_service.google_sheets_service.fetch_bill_status_rules", new_callable=AsyncMock)
    def test_bill_check_cancelled_derives_to_sc(self, mock_fetch_rules, client):
        """Test that Cancelled bill status is forced to derive to Servicio al Cliente"""
        # Mock Supabase return record
        record = {
            "tracking_number": "TRK97226012",
            "biller": "MetroGas Natural Gas Service",
            "nombre_o_nombres": "Enrique Alicia",
            "apellido_paterno": "Ruiz",
            "apellido_materno": "Cruz",
            "status": "Cancelled"
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [record]
        self.mock_httpx.return_value = mock_response

        # Mock Google Sheets rules
        mock_fetch_rules.return_value = [
            {
                "categoria": "Solicitud de status",
                "derivacion": "NA",
                "caso": "Pago de bill",
                "tipo_status": "No transitorio",
                "status": "Cancelled - Pago de Bill",
                "perfil": "Remitente o Agente",
                "code_script": "SC.027",
                "script": "Verificando el estatus de la operación, lamentablemente el pago no se procesó exitosamente."
            }
        ]

        response = client.post(
            f"/api/v1/bill/check?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact_id": "test_contact",
                "user_text": "",
                "tracking_number": "TRK97226012",
                "biller": "MetroGas",
                "nombre_completo_customer": "Enrique Alicia Ruiz Cruz",
                "perfil": "CLIENTE"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["derivacion"] == "NA"
        assert "no se procesó exitosamente" in data["reply_text"]
        assert "¿Le gustaría que lo comuniquemos con un asesor de servicio al cliente?" in data["reply_text"]
        assert data["validation_success"] is True

    @patch("api.google_sheets_service.google_sheets_service.fetch_bill_status_rules", new_callable=AsyncMock)
    def test_bill_check_origin_derives_to_sc(self, mock_fetch_rules, client):
        """Test that Origin bill status derives to Servicio al Cliente"""
        # Mock Supabase return record
        record = {
            "tracking_number": "TRK23756669",
            "biller": "MetroGas Natural Gas Service",
            "nombre_o_nombres": "Enrique Alicia",
            "apellido_paterno": "Ruiz",
            "apellido_materno": "Cruz",
            "status": "Origin"
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [record]
        self.mock_httpx.return_value = mock_response

        # Mock Google Sheets rules
        mock_fetch_rules.return_value = [
            {
                "categoria": "Solicitud de status / Consulta de status en Chronos",
                "derivacion": "Servicio al Cliente",
                "caso": "Pago de bill",
                "tipo_status": "Transitorio",
                "status": "Origin- Pago de Bill",
                "perfil": "Remitente o Agente",
                "code_script": "SC.028",
                "script": "Su pago no ha sido procesado, lo transferiré con un asesor para recibir asistencia personalizada. Por favor, espere mientras lo comunico."
            }
        ]

        response = client.post(
            f"/api/v1/bill/check?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact_id": "test_contact",
                "user_text": "",
                "tracking_number": "TRK23756669",
                "biller": "MetroGas",
                "nombre_completo_customer": "Enrique Alicia Ruiz Cruz",
                "perfil": "CLIENTE"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["derivacion"] == "Servicio al Cliente"
        assert "no ha sido procesado" in data["reply_text"]
        assert data["validation_success"] is True


