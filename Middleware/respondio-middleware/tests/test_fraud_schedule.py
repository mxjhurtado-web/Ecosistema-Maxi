import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
from zoneinfo import ZoneInfo
from api.main import app, check_department_hours
from api.config import settings

@pytest.fixture
def client():
    return TestClient(app)

class TestFraudBSAScheduleCDMX:
    """Test suite for Fraud and BSA in-hours vs out-of-hours behavior under CDMX timezone"""

    def test_department_hours_cdmx(self):
        """Test department operating hours logic in CDMX timezone"""
        # Tuesday 11:00 AM CDMX (Within working hours)
        dt_in_hours = datetime(2026, 9, 29, 11, 0, tzinfo=ZoneInfo("America/Mexico_City"))
        assert check_department_hours("PREVENCION DE FRAUDES", dt_in_hours) is True
        assert check_department_hours("BSA MONITORING", dt_in_hours) is True
        assert check_department_hours("SERVICIO AL CLIENTE", dt_in_hours) is True

        # Tuesday 7:30 PM CDMX (Fraudes/BSA closed, CS open)
        dt_guardia = datetime(2026, 9, 29, 19, 30, tzinfo=ZoneInfo("America/Mexico_City"))
        assert check_department_hours("PREVENCION DE FRAUDES", dt_guardia) is False
        assert check_department_hours("BSA MONITORING", dt_guardia) is False
        assert check_department_hours("SERVICIO AL CLIENTE", dt_guardia) is True

        # Tuesday 11:00 PM CDMX (All closed)
        dt_closed = datetime(2026, 9, 29, 23, 0, tzinfo=ZoneInfo("America/Mexico_City"))
        assert check_department_hours("PREVENCION DE FRAUDES", dt_closed) is False
        assert check_department_hours("BSA MONITORING", dt_closed) is False
        assert check_department_hours("SERVICIO AL CLIENTE", dt_closed) is False

        # Sunday 11:00 AM CDMX (Fraudes/BSA closed, CS open)
        dt_sunday = datetime(2026, 10, 4, 11, 0, tzinfo=ZoneInfo("America/Mexico_City"))
        assert check_department_hours("PREVENCION DE FRAUDES", dt_sunday) is False
        assert check_department_hours("BSA MONITORING", dt_sunday) is False
        assert check_department_hours("SERVICIO AL CLIENTE", dt_sunday) is True

    @pytest.mark.asyncio
    async def test_fraud_turn1_in_hours(self, client):
        """Turn 1 Fraud in working hours delivers SC.030.1 and fires notification"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True

        mock_gchat = AsyncMock(return_value=True)

        with patch("api.main.get_redis_client", AsyncMock(return_value=mock_redis)), \
             patch("api.main.check_department_hours", return_value=True), \
             patch("api.google_chat_service.google_chat_service.send_unified_notification", mock_gchat):

            response = client.post(
                f"/api/v1/agent/interact?secret={settings.WEBHOOK_SECRET}",
                json={
                    "agent_name": "DerivacionFraudes",
                    "contact_id": "test_cdmx_contact",
                    "user_text": "Me llamo Juan Perez, fui victima de estafa y quiero cancelar el envio"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["derivacion"] == "NA"
            assert "alta prioridad" in data["reply_text"] or "Lamento lo sucedido" in data["reply_text"]
            mock_gchat.assert_called_once()
            call_kwargs = mock_gchat.call_args[1]
            assert call_kwargs["is_out_of_hours"] is False
            assert call_kwargs["dept_key"] == "FRAUDES"

    @pytest.mark.asyncio
    async def test_fraud_turn1_out_of_hours_guardia(self, client):
        """Turn 1 Fraud outside dept hours but CS open delivers SC.030.2 with is_out_of_hours=True"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True

        mock_gchat = AsyncMock(return_value=True)

        def mock_check_dept(depto, dt):
            if "SERVICIO AL CLIENTE" in depto:
                return True
            return False

        with patch("api.main.get_redis_client", AsyncMock(return_value=mock_redis)), \
             patch("api.main.check_department_hours", side_effect=mock_check_dept), \
             patch("api.google_chat_service.google_chat_service.send_unified_notification", mock_gchat):

            response = client.post(
                f"/api/v1/agent/interact?secret={settings.WEBHOOK_SECRET}",
                json={
                    "agent_name": "DerivacionFraudes",
                    "contact_id": "test_cdmx_out_hours",
                    "user_text": "Me acaban de estafar con una llamada falsa pidiendome dinero"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["derivacion"] == "NA"
            assert "canalizaré su solicitud" in data["reply_text"] or "Lamento lo sucedido" in data["reply_text"]
            mock_gchat.assert_called_once()
            call_kwargs = mock_gchat.call_args[1]
            assert call_kwargs["is_out_of_hours"] is True

    @pytest.mark.asyncio
    async def test_fraud_turn2_out_of_hours_derives_to_cs(self, client):
        """Turn 2 Fraud outside working hours delivers SC.037 and routes to 'Servicio al Cliente'"""
        mock_redis = AsyncMock()
        async def mock_redis_get(key):
            if "fraud_collecting" in key:
                return b"1"
            if "fraud_turn1_text" in key:
                return b"mensaje inicial"
            return None
        mock_redis.get.side_effect = mock_redis_get
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = True

        mock_gchat = AsyncMock(return_value=True)

        with patch("api.main.get_redis_client", AsyncMock(return_value=mock_redis)), \
             patch("api.main.check_department_hours", return_value=False), \
             patch("api.google_chat_service.google_chat_service.send_unified_notification", mock_gchat):

            response = client.post(
                f"/api/v1/agent/interact?secret={settings.WEBHOOK_SECRET}",
                json={
                    "agent_name": "DerivacionFraudes",
                    "contact_id": "test_cdmx_turn2",
                    "user_text": "Mi nombre es Carlos Gomez, clave de envio CE98765432 agencia 1234"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["derivacion"] == "Servicio al Cliente"
            assert "área especializada" in data["reply_text"] or "canalizado" in data["reply_text"]
            mock_gchat.assert_called_once()
            call_kwargs = mock_gchat.call_args[1]
            assert call_kwargs["turn_tag"] == "turn2"
            assert call_kwargs["is_out_of_hours"] is True

    @pytest.mark.asyncio
    async def test_bsa_turn1_out_of_hours_guardia(self, client):
        """Turn 1 BSA outside dept hours but CS open delivers SC.030.2 with is_out_of_hours=True"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True

        mock_gchat = AsyncMock(return_value=True)

        def mock_check_dept(depto, dt):
            if "SERVICIO AL CLIENTE" in depto:
                return True
            return False

        with patch("api.main.get_redis_client", AsyncMock(return_value=mock_redis)), \
             patch("api.main.check_department_hours", side_effect=mock_check_dept), \
             patch("api.google_chat_service.google_chat_service.send_unified_notification", mock_gchat):

            response = client.post(
                f"/api/v1/agent/interact?secret={settings.WEBHOOK_SECRET}",
                json={
                    "agent_name": "DerivacionBSA",
                    "contact_id": "test_bsa_out_hours",
                    "user_text": "Un cliente envió más de 10 mil dólares y se negó a proporcionar identificación para CTR"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["derivacion"] == "NA"
            assert "canalizaré su solicitud" in data["reply_text"] or "Lamento lo sucedido" in data["reply_text"]
            mock_gchat.assert_called_once()
            call_kwargs = mock_gchat.call_args[1]
            assert call_kwargs["is_out_of_hours"] is True
            assert call_kwargs["dept_key"] == "BSA"

