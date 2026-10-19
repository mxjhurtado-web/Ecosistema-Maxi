import asyncio
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Add middleware directory to path
sys.path.insert(0, r"c:\Users\User\Ecosistema-Maxi\Middleware\respondio-middleware")

from api.models import (
    BillCheckRequest,
    BillCheckResponse,
    TopupCheckRequest,
    TopupCheckResponse,
    CSATLogRequest,
    CSATLogResponse,
    AgentInteractRequest,
    AgentInteractResponse
)
from api.main import (
    check_bill_status_inner,
    check_topup_status_inner,
    log_csat_feedback_inner,
    agent_interact_inner
)
from api.config import settings

async def run_tests():
    print("==================================================")
    print("🚀 RUNNING ECOSYSTEM ALIGNMENT VERIFICATION TESTS")
    print("==================================================")
    
    # 1. Test BillCheckRequest with codigo_envio and nombre_remitente alias
    print("\n--- 1. Testing BillCheckRequest Aliases ---")
    bill_req_alias = BillCheckRequest(
        contact_id="test_user_1",
        user_text="Consultar pago",
        codigo_envio="TRK987654321",
        nombre_remitente="Juan Perez",
        biller="CFE"
    )
    assert bill_req_alias.codigo_envio == "TRK987654321"
    print("✅ BillCheckRequest parsed alias fields successfully.")

    # 2. Test TopupCheckRequest with codigo_envio alias
    print("\n--- 2. Testing TopupCheckRequest Aliases ---")
    topup_req_alias = TopupCheckRequest(
        contact_id="test_user_2",
        user_text="Consultar recarga",
        codigo_envio="TOP11223344",
        customer_number="5512345678",
        cellular_number="5587654321"
    )
    assert topup_req_alias.codigo_envio == "TOP11223344"
    print("✅ TopupCheckRequest parsed alias fields successfully.")

    # 3. Test CSATLogRequest with optional contact_name and conversation_id
    print("\n--- 3. Testing CSATLogRequest & Response ---")
    csat_req = CSATLogRequest(
        contact_id="test_user_3",
        conversation_id="conv_12345",
        rating=5,
        comment="Excelente servicio de Max"
    )
    assert csat_req.contact_name == "Cliente"
    assert csat_req.conversation_id == "conv_12345"
    print(f"✅ CSATLogRequest validated with default name: '{csat_req.contact_name}'")

    csat_resp = CSATLogResponse(
        status="success",
        message="CSAT logged",
        reply_text="Gracias por comunicarse a Maxitransfers. Le atendió Max. Que tenga un buen día."
    )
    assert csat_resp.reply_text is not None
    print(f"✅ CSATLogResponse validated with reply_text: '{csat_resp.reply_text[:40]}...'")

    # 4. Test AgenteComunicador via agent_interact_inner
    print("\n--- 4. Testing AgenteComunicador Canonical Closure ---")
    interact_req = AgentInteractRequest(
        agent_name="AgenteComunicador",
        contact_id="test_agency_contact",
        user_text="Soy Laura de la agencia 789, requiero asistencia sobre un balance pendiente"
    )
    resp = await agent_interact_inner(interact_req, secret="maxi-secret-2025")
    print(f"Status: {resp.status}")
    print(f"Derivacion: {resp.derivacion}")
    print(f"Reply Text: {resp.reply_text[:60]}...")
    assert resp.status == "success"
    assert resp.derivacion == "cerrar"
    assert "SC." not in resp.reply_text
    print("✅ AgenteComunicador closed properly with derivacion='cerrar' and clean text.")

    # 5. Test CancelacionEnvio Channel Exclusion
    print("\n--- 5. Testing CancelacionEnvio Channel Exclusion ---")
    cancel_req = AgentInteractRequest(
        agent_name="CancelacionEnvio",
        contact_id="test_user_cancel",
        user_text="Quiero cancelar mi envio de dinero"
    )
    resp_cancel = await agent_interact_inner(cancel_req, secret="maxi-secret-2025")
    print(f"Status: {resp_cancel.status}")
    print(f"Derivacion: {resp_cancel.derivacion}")
    print(f"Reply Text: {resp_cancel.reply_text[:60]}...")
    assert resp_cancel.status == "success"
    assert resp_cancel.derivacion == "cerrar"
    assert "SC." not in resp_cancel.reply_text
    print("✅ CancelacionEnvio closed properly with derivacion='cerrar'.")

    # 6. Test DerivacionFraudes Turn 1 & Turn 2
    print("\n--- 6. Testing DerivacionFraudes Turn 1 & Turn 2 ---")
    t1_req = AgentInteractRequest(
        agent_name="DerivacionFraudes",
        contact_id="test_user_fraud",
        user_text="Me llamaron pidiendo mi clave para depositarme"
    )
    resp_t1 = await agent_interact_inner(t1_req, secret="maxi-secret-2025")
    print(f"Turn 1 Derivacion: {resp_t1.derivacion}")
    print(f"Turn 1 Reply: {resp_t1.reply_text[:60]}...")
    assert resp_t1.derivacion == "NA"

    t2_req = AgentInteractRequest(
        agent_name="DerivacionFraudes",
        contact_id="test_user_fraud",
        user_text="Soy Carlos Gomez, agencia 100, no di la clave"
    )
    resp_t2 = await agent_interact_inner(t2_req, secret="maxi-secret-2025")
    print(f"Turn 2 Derivacion: {resp_t2.derivacion}")
    print(f"Turn 2 Reply: {resp_t2.reply_text[:60]}...")
    assert resp_t2.derivacion in ["cerrar", "Servicio al Cliente"]
    assert "SC." not in resp_t2.reply_text
    print("✅ DerivacionFraudes executed Turn 1 and Turn 2 flawlessly.")

    print("\n==================================================")
    print("🎉 ALL 6 VERIFICATION SUITES PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
