import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from api.main import app
from api.config import settings

@pytest.fixture
def client():
    return TestClient(app)

class TestCascadeSafetyGuards:
    """Tests ensuring AgenteComunicador cannot be mistakenly used to hijack remittance tracking or spam Google Chat."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        self.mock_redis = AsyncMock()
        self.mock_redis.get.return_value = None
        self.patcher_redis = patch("api.main.get_redis_client", AsyncMock(return_value=self.mock_redis))
        self.patcher_redis.start()

        self.mock_gchat = AsyncMock(return_value=True)
        self.patcher_gchat = patch("api.google_chat_service.google_chat_service.send_unified_notification", self.mock_gchat)
        self.patcher_gchat.start()

        yield

        self.patcher_redis.stop()
        self.patcher_gchat.stop()

    def test_agente_comunicador_intercepts_remittance_code(self, client):
        """When AgenteComunicador receives a message containing a remittance code (CE11563936568) with only a name,
        it must NOT notify Google Chat and must redirect immediately to VerificadorEstatus requesting both names."""
        response = client.post(
            f"/api/v1/agent/interact?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact_id": "contact_remittance_test",
                "agent_name": "AgenteComunicador",
                "user_text": "roberto cruz gomez CE11563936568"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["derivacion"] == "VerificadorEstatus"
        # Must ask for sender and receiver names (SC.010)
        assert "nombre completo de quien envió" in data["reply_text"] or "validar algunos datos" in data["reply_text"]
        # Google Chat notification must have been SUPPRESSED
        self.mock_gchat.assert_not_called()

    def test_agente_comunicador_processes_valid_agency_request(self, client):
        """When AgenteComunicador receives a genuine agency request with agency number,
        it should notify Google Chat and close or follow standard agency protocol."""
        response = client.post(
            f"/api/v1/agent/interact?secret={settings.WEBHOOK_SECRET}",
            json={
                "contact_id": "contact_agency_test",
                "agent_name": "AgenteComunicador",
                "user_text": "Soy de la agencia 5421, Juan Perez, tenemos problemas con el POS"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Should notify Google Chat for Soporte Tecnico
        self.mock_gchat.assert_called_once()
        assert data["derivacion"] == "cerrar"
