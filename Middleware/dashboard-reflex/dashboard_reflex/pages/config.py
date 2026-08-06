import reflex as rx
from dashboard_reflex.components.layout import protected_layout
from dashboard_reflex.components.styling import (
    GLASS_EFFECT, ACCENT_BLUE, ACCENT_PURPLE, BORDER_COLOR, TEXT_MUTED,
    glass_container, status_badge
)
from dashboard_reflex.api.client import api_client
from dashboard_reflex.state.auth_state import AuthState
from dashboard_reflex.state.app_state import AppState
import json
import secrets

class ConfigState(rx.State):
    is_loading: bool = False
    
    # 🔌 MCP Settings
    mcp_url: str = ""
    mcp_timeout: int = 5
    mcp_max_retries: int = 3
    mcp_retry_delay: int = 1
    mcp_emergency_mode: bool = False
    mcp_use_keycloak: bool = False
    mcp_token: str = ""
    kc_server_url: str = ""
    kc_realm: str = ""
    kc_client_id: str = ""
    kc_client_secret: str = ""
    
    # 👥 Dynamic Agents
    agents: list[dict] = []
    edit_mode: bool = False
    agent_name: str = ""
    agent_prompt: str = ""
    agent_mcp_url: str = ""
    agent_readonly: bool = False
    agent_is_orchestrator: bool = False
    agent_rules_raw: str = '{\n  "do": ["Ser amable"],\n  "dont": ["Mencionar precios"]\n}'
    agent_knowledge_raw: str = ""
    agent_web_search: bool = False
    
    # 💾 Cache Settings
    cache_enabled: bool = True
    cache_ttl: int = 300
    cache_max_size: int = 1000
    
    # 🔐 Security
    webhook_secret: str = ""
    rate_limit: int = 100
    
    # 🤖 AI settings (Gemini Key)
    gemini_api_key: str = ""
    
    # 🚨 Email alerts
    email_enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    recipient_email: str = ""
    alert_on_mcp_error: bool = True
    alert_on_circuit_breaker: bool = True

    # 🌐 Google Cloud Sources & Service Accounts
    orbit_doc_governance_id: str = "12-fLM7wAFF3I0_ifY3Y1lahU7EfBeV5uA5GzFkkHBUw"
    orbit_sheet_rules_id: str = "1eFm3L_ALVr78wTDBB2bsg7Wq6DT9ZoGzIX9tKLN9nGw"
    orbit_sheet_scripts_id: str = "18VE3tdVt4E-eNrf0dD4zlk1aLV2nfv9_ncdUvLPaNic"
    orbit_sheet_estatus_id: str = "14BdjBuXPXPkjXMKS-955fA6bNw5qRMv5IWCNhMZGIXc"
    orbit_sheet_bill_id: str = "16fB_MGtha0NUtp5mge7UwvHcWo1NYVnOGVv6Yntv9xo"
    orbit_sheet_topup_id: str = "1E3pNthg7myh7tgjEnb_TIxCnTLFi_gzWlcxk2LOdNCs"
    maxibot_sheet_faq_id: str = "1wrtj7SZ6wB9h1yd_9h613DYNPGjI69_Zj1gLigiUHtE"

    def set_orbit_doc_governance_id(self, val: str): self.orbit_doc_governance_id = val
    def set_orbit_sheet_rules_id(self, val: str): self.orbit_sheet_rules_id = val
    def set_orbit_sheet_scripts_id(self, val: str): self.orbit_sheet_scripts_id = val
    def set_orbit_sheet_estatus_id(self, val: str): self.orbit_sheet_estatus_id = val
    def set_orbit_sheet_bill_id(self, val: str): self.orbit_sheet_bill_id = val
    def set_orbit_sheet_topup_id(self, val: str): self.orbit_sheet_topup_id = val
    def set_maxibot_sheet_faq_id(self, val: str): self.maxibot_sheet_faq_id = val

    def set_mcp_url(self, val: str):
        self.mcp_url = val
    def set_mcp_token(self, val: str):
        self.mcp_token = val
    def set_kc_server_url(self, val: str):
        self.kc_server_url = val
    def set_kc_realm(self, val: str):
        self.kc_realm = val
    def set_kc_client_id(self, val: str):
        self.kc_client_id = val
    def set_kc_client_secret(self, val: str):
        self.kc_client_secret = val
    def set_agent_name(self, val: str):
        self.agent_name = val
    def set_agent_prompt(self, val: str):
        self.agent_prompt = val
    def set_agent_mcp_url(self, val: str):
        self.agent_mcp_url = val
    def set_agent_rules_raw(self, val: str):
        self.agent_rules_raw = val
    def set_agent_knowledge_raw(self, val: str):
        self.agent_knowledge_raw = val
    def set_webhook_secret(self, val: str):
        self.webhook_secret = val
    def set_gemini_api_key(self, val: str):
        self.gemini_api_key = val
    def set_smtp_server(self, val: str):
        self.smtp_server = val
    def set_smtp_user(self, val: str):
        self.smtp_user = val
    def set_smtp_password(self, val: str):
        self.smtp_password = val
    def set_recipient_email(self, val: str):
        self.recipient_email = val
    def set_mcp_timeout(self, val: int):
        self.mcp_timeout = val
    def set_mcp_max_retries(self, val: int):
        self.mcp_max_retries = val
    def set_mcp_retry_delay(self, val: int):
        self.mcp_retry_delay = val
    def set_mcp_emergency_mode(self, val: bool):
        self.mcp_emergency_mode = val
    def set_mcp_use_keycloak(self, val: bool):
        self.mcp_use_keycloak = val
    def set_cache_enabled(self, val: bool):
        self.cache_enabled = val
    def set_cache_ttl(self, val: int):
        self.cache_ttl = val
    def set_cache_max_size(self, val: int):
        self.cache_max_size = val
    def set_rate_limit(self, val: int):
        self.rate_limit = val
    def set_email_enabled(self, val: bool):
        self.email_enabled = val
    def set_alert_on_mcp_error(self, val: bool):
        self.alert_on_mcp_error = val
    def set_alert_on_circuit_breaker(self, val: bool):
        self.alert_on_circuit_breaker = val

    def change_mcp_timeout(self, val: str):
        self.mcp_timeout = int(val) if val else 5
    def change_mcp_max_retries(self, val: str):
        self.mcp_max_retries = int(val) if val else 3
    def change_mcp_retry_delay(self, val: str):
        self.mcp_retry_delay = int(val) if val else 1
    def change_cache_ttl(self, val: str):
        self.cache_ttl = int(val) if val else 300
    def change_cache_max_size(self, val: str):
        self.cache_max_size = int(val) if val else 1000
    def change_rate_limit(self, val: str):
        self.rate_limit = int(val) if val else 100
    def change_smtp_port(self, val: str):
        self.smtp_port = int(val) if val else 587

    async def load_data(self):
        self.is_loading = True
        
        # 1. Fetch MCP Settings
        mcp_cfg = await api_client.get_mcp_config()
        if mcp_cfg:
            self.mcp_url = mcp_cfg.get("url", "")
            self.mcp_timeout = mcp_cfg.get("timeout", 5)
            self.mcp_max_retries = mcp_cfg.get("max_retries", 3)
            self.mcp_retry_delay = mcp_cfg.get("retry_delay", 1)
            self.mcp_emergency_mode = mcp_cfg.get("emergency_mode", False)
            self.mcp_use_keycloak = mcp_cfg.get("use_keycloak", False)
            self.mcp_token = mcp_cfg.get("mcp_token", "") or ""
            self.kc_server_url = mcp_cfg.get("kc_server_url", "") or ""
            self.kc_realm = mcp_cfg.get("kc_realm", "") or ""
            self.kc_client_id = mcp_cfg.get("kc_client_id", "") or ""
            self.kc_client_secret = mcp_cfg.get("kc_client_secret", "") or ""
            self.gemini_api_key = mcp_cfg.get("gemini_api_key", "") or ""
            
        # 2. Fetch Cache Settings
        cache_cfg = await api_client.get_cache_config()
        if cache_cfg:
            self.cache_enabled = cache_cfg.get("enabled", True)
            self.cache_ttl = cache_cfg.get("ttl", 300)
            self.cache_max_size = cache_cfg.get("max_size", 1000)
            
        # 3. Fetch Security Config
        sec_cfg = await api_client.get_security_config()
        if sec_cfg:
            self.webhook_secret = sec_cfg.get("webhook_secret", "")
            self.rate_limit = sec_cfg.get("rate_limit", 100)
            
        # 4. Fetch Email Settings
        try:
            email_cfg = await api_client._request("GET", "/admin/config/email")
            if email_cfg:
                self.email_enabled = email_cfg.get("enabled", False)
                self.smtp_server = email_cfg.get("smtp_server", "smtp.gmail.com")
                self.smtp_port = email_cfg.get("smtp_port", 587)
                self.smtp_user = email_cfg.get("smtp_user", "")
                self.smtp_password = email_cfg.get("smtp_password", "")
                self.recipient_email = email_cfg.get("recipient_email", "")
                self.alert_on_mcp_error = email_cfg.get("alert_on_mcp_error", True)
                self.alert_on_circuit_breaker = email_cfg.get("alert_on_circuit_breaker", True)
        except Exception:
            pass
            
        # 5. Fetch Dynamic Agents
        await self.load_agents()

        # 6. Fetch Google Sources
        await self.load_google_sources()
        self.is_loading = False

    async def load_google_sources(self):
        try:
            cfg = await api_client.get_google_sources()
            if cfg and isinstance(cfg, dict):
                orbit_srcs = cfg.get("orbit_sa", {}).get("sources", [])
                for s in orbit_srcs:
                    k = s.get("key")
                    v = s.get("id", "")
                    if k == "doc_governance": self.orbit_doc_governance_id = v
                    elif k == "sheet_rules": self.orbit_sheet_rules_id = v
                    elif k == "sheet_scripts": self.orbit_sheet_scripts_id = v
                    elif k == "sheet_estatus": self.orbit_sheet_estatus_id = v
                    elif k == "sheet_bill": self.orbit_sheet_bill_id = v
                    elif k == "sheet_topup": self.orbit_sheet_topup_id = v
                
                maxi_srcs = cfg.get("maxibot_sa", {}).get("sources", [])
                for s in maxi_srcs:
                    if s.get("key") == "sheet_faq":
                        self.maxibot_sheet_faq_id = s.get("id", "")
        except Exception:
            pass

    async def save_google_sources(self):
        payload = {
            "orbit_sa": {
                "email": "maxibot-sa@maxibot-472423.iam.gserviceaccount.com",
                "gcp_project": "maxibot-472423 (Ecosistema Orbi)",
                "sources": [
                    { "key": "doc_governance", "name": "Reglas Generales de Uso", "type": "doc", "id": self.orbit_doc_governance_id, "status": "ok" },
                    { "key": "sheet_rules", "name": "Matriz de Reglas RNE (59 Reglas)", "type": "sheet", "id": self.orbit_sheet_rules_id, "status": "ok" },
                    { "key": "sheet_scripts", "name": "Catálogo de Scripts SC (113 Scripts)", "type": "sheet", "id": self.orbit_sheet_scripts_id, "status": "ok" },
                    { "key": "sheet_estatus", "name": "Estatus Envíos Core", "type": "sheet", "id": self.orbit_sheet_estatus_id, "status": "ok" },
                    { "key": "sheet_bill", "name": "Bill Payment Estatus", "type": "sheet", "id": self.orbit_sheet_bill_id, "status": "ok" },
                    { "key": "sheet_topup", "name": "Topup Estatus", "type": "sheet", "id": self.orbit_sheet_topup_id, "status": "ok" }
                ]
            },
            "maxibot_sa": {
                "email": "athenas-driver-reader@athenas-panel.iam.gserviceaccount.com",
                "gcp_project": "athenas-panel (Maxibot Dedicada)",
                "sources": [
                    { "key": "sheet_faq", "name": "FAQ Knowledge Base", "type": "sheet", "id": self.maxibot_sheet_faq_id, "status": "ok" }
                ]
            }
        }
        res = await api_client.update_google_sources(payload)
        if res:
            return rx.toast.success("✅ Fuentes de Google Cloud guardadas exitosamente.")
        else:
            return rx.toast.error("❌ Error al guardar las fuentes de Google Cloud.")

    async def force_sync_sources(self):
        self.is_loading = True
        res = await api_client.force_sync_sources()
        self.is_loading = False
        if res and res.get("status") == "success":
            synced = res.get("synced", {})
            rules = synced.get("rules", 59)
            scripts = synced.get("scripts", 113)
            return rx.toast.success(f"⚡ ¡Sincronización en vivo completada! {rules} reglas, {scripts} scripts y directivas de gobernanza actualizadas.")
        else:
            return rx.toast.error("❌ Error al forzar la sincronización en vivo.")

    async def load_agents(self):
        res = await api_client.get_agents()
        self.agents = res if res else []

    async def test_mcp_connection(self):
        rx.toast.info("Probando conexión con el servidor MCP...")
        res = await api_client.test_mcp("Consulta de prueba")
        if res and res.get("status") == "ok":
            rx.toast.success(f"✅ ¡Conexión Exitosa! Latencia: {res.get('latency_ms')} ms")
        else:
            rx.toast.error(f"❌ Falló conexión: {res.get('error') if res else 'Sin respuesta'}")

    async def save_mcp_settings(self, form_data: dict):
        new_cfg = {
            "url": self.mcp_url,
            "timeout": int(self.mcp_timeout),
            "max_retries": int(self.mcp_max_retries),
            "retry_delay": int(self.mcp_retry_delay),
            "mcp_token": None if self.mcp_use_keycloak else self.mcp_token,
            "gemini_api_key": self.gemini_api_key if self.gemini_api_key else None,
            "emergency_mode": self.mcp_emergency_mode,
            "use_keycloak": self.mcp_use_keycloak,
            "kc_server_url": self.kc_server_url if self.mcp_use_keycloak else None,
            "kc_realm": self.kc_realm if self.mcp_use_keycloak else None,
            "kc_client_id": self.kc_client_id if self.mcp_use_keycloak else None,
            "kc_client_secret": self.kc_client_secret if self.mcp_use_keycloak else None
        }
        success = await api_client.update_mcp_config(new_cfg)
        if success:
            rx.toast.success("✅ Configuración MCP actualizada con éxito!")
            app_state = await self.get_state(AppState)
            await app_state.update_health()
        else:
            rx.toast.error("❌ Error al guardar configuración MCP.")

    async def save_cache_settings(self):
        new_cfg = {
            "enabled": self.cache_enabled,
            "ttl": int(self.cache_ttl),
            "max_size": int(self.cache_max_size)
        }
        success = await api_client.update_cache_config(new_cfg)
        if success:
            rx.toast.success("✅ Configuración de caché guardada!")
        else:
            rx.toast.error("❌ Error al guardar configuración de caché.")

    async def clear_cache_maint(self):
        success = await api_client.clear_cache()
        if success:
            rx.toast.success("🧹 Caché limpiado con éxito!")
        else:
            rx.toast.error("❌ Falló limpieza de caché.")

    async def save_security_settings(self):
        new_cfg = {
            "webhook_secret": self.webhook_secret,
            "rate_limit": int(self.rate_limit)
        }
        success = await api_client.update_security_config(new_cfg)
        if success:
            rx.toast.success("✅ Configuración de seguridad guardada!")
        else:
            rx.toast.error("❌ Error al guardar seguridad.")

    def regenerate_webhook_secret(self):
        self.webhook_secret = secrets.token_urlsafe(32)
        rx.toast.info("Nuevo webhook secret generado. Guarde los cambios para aplicar.")

    async def save_email_settings(self):
        new_cfg = {
            "enabled": self.email_enabled,
            "smtp_server": self.smtp_server,
            "smtp_port": int(self.smtp_port),
            "smtp_user": self.smtp_user,
            "smtp_password": self.smtp_password,
            "recipient_email": self.recipient_email,
            "alert_on_mcp_error": self.alert_on_mcp_error,
            "alert_on_circuit_breaker": self.alert_on_circuit_breaker
        }
        try:
            res = await api_client._request("PUT", "/admin/config/email", json_data=new_cfg)
            if res:
                rx.toast.success("✅ Alertas de correo guardadas!")
            else:
                rx.toast.error("❌ Error al guardar alertas de correo.")
        except Exception:
            rx.toast.error("❌ Error de comunicación con el servidor.")

    # Dynamic Agents Actions
    def set_agent_web_search(self, val: bool):
        self.agent_web_search = val
    def set_agent_readonly(self, val: bool):
        self.agent_readonly = val
    def set_agent_is_orchestrator(self, val: bool):
        self.agent_is_orchestrator = val

    def select_agent_edit(self, agent: dict):
        self.edit_mode = True
        self.agent_name = agent.get("name", "")
        self.agent_prompt = agent.get("system_prompt", "")
        self.agent_mcp_url = agent.get("mcp_url", "") or ""
        self.agent_readonly = agent.get("readonly", False)
        self.agent_is_orchestrator = agent.get("is_orchestrator", False)
        self.agent_rules_raw = json.dumps(agent.get("specific_rules", {}), indent=2)
        self.agent_knowledge_raw = "\n".join(agent.get("knowledge_sources", []))
        self.agent_web_search = agent.get("web_search_enabled", False)
        rx.toast.info(f"Cargando agente '{self.agent_name}' para edición.")

    def cancel_agent_edit(self):
        self.edit_mode = False
        self.agent_name = ""
        self.agent_prompt = ""
        self.agent_mcp_url = ""
        self.agent_readonly = False
        self.agent_is_orchestrator = False
        self.agent_rules_raw = '{\n  "do": ["Ser amable"],\n  "dont": ["Mencionar precios"]\n}'
        self.agent_knowledge_raw = ""
        self.agent_web_search = False

    async def delete_agent_action(self, name: str):
        success = await api_client.delete_agent(name)
        if success:
            rx.toast.success(f"Agente '{name}' eliminado.")
            await self.load_agents()
        else:
            rx.toast.error("No se pudo eliminar el agente.")

    async def save_agent_form(self):
        if not self.agent_name or not self.agent_prompt:
            rx.toast.error("Nombre y Prompt de sistema son obligatorios.")
            return

        try:
            rules = json.loads(self.agent_rules_raw)
        except Exception:
            rx.toast.error("Reglas JSON inválidas.")
            return

        knowledge = [k.strip() for k in self.agent_knowledge_raw.split("\n") if k.strip()]

        agent_data = {
            "name": self.agent_name,
            "system_prompt": self.agent_prompt,
            "readonly": self.agent_readonly,
            "mcp_url": self.agent_mcp_url if self.agent_mcp_url else None,
            "is_orchestrator": self.agent_is_orchestrator,
            "specific_rules": rules,
            "knowledge_sources": knowledge,
            "web_search_enabled": self.agent_web_search
        }

        success = await api_client.add_agent(agent_data)
        if success:
            rx.toast.success(f"Agente '{self.agent_name}' guardado correctamente!")
            self.cancel_agent_edit()
            await self.load_agents()
        else:
            rx.toast.error("Error al guardar agente.")

    async def on_load(self):
        await self.load_data()

def agent_card(agent: dict) -> rx.Component:
    """Renders a single dynamic agent card."""
    name = agent.get("name", "")
    
    return glass_container(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon(rx.cond(agent.get("is_orchestrator", False), "crown", "bot"), size=16, color=ACCENT_BLUE),
                    rx.text(name, font_weight="bold", font_size="15px", color="#FFFFFF"),
                    spacing="2",
                    align="center"
                ),
                rx.text("Prompt: ", agent.get("system_prompt", ""), font_size="12px", color=TEXT_MUTED, max_width="280px", is_truncated=True),
                rx.hstack(
                    rx.badge(rx.cond(agent.get("readonly", False), "🔒 Solo lectura", "✍️ Lectura/Escritura"), variant="soft"),
                    rx.badge(rx.cond(agent.get("web_search_enabled", False), "🌐 Web search", "🚫 Sin Web Search"), color_scheme=rx.cond(agent.get("web_search_enabled", False), "sky", "gray")),
                    spacing="2",
                    style={"margin_top": "6px"}
                ),
                align_items="start",
                spacing="1"
            ),
            rx.spacer(),
            rx.hstack(
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    on_click=lambda: ConfigState.select_agent_edit(agent),
                    color_scheme="blue",
                    variant="soft",
                    style={"cursor": "pointer"}
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=14),
                    on_click=lambda: ConfigState.delete_agent_action(name),
                    color_scheme="ruby",
                    variant="soft",
                    style={"cursor": "pointer"}
                ),
                spacing="2"
            ),
            width="100%",
            align_items="center"
        ),
        style={"padding": "16px", "width": "100%", "background_color": "rgba(255,255,255,0.01)"}
    )

def config_page() -> rx.Component:
    """The system settings configuration page."""
    
    # 🔌 MCP Settings Tab
    mcp_form = rx.vstack(
        rx.heading("🔌 Configuración MCP", size="4", style={"margin_bottom": "16px", "color": "#FFFFFF"}),
        rx.vstack(
            rx.text("URL del Servidor MCP", font_size="12px", font_weight="bold", color=TEXT_MUTED),
            rx.input(
                value=ConfigState.mcp_url,
                on_change=ConfigState.set_mcp_url,
                width="100%",
                style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "8px"}
            ),
            align_items="start",
            width="100%"
        ),
        rx.grid(
            rx.vstack(
                rx.text("Timeout (segundos)", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(
                    type="number",
                    value=ConfigState.mcp_timeout.to(str),
                    on_change=ConfigState.change_mcp_timeout,
                    width="100%",
                    style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "8px"}
                ),
                align_items="start"
            ),
            rx.vstack(
                rx.text("Intentos Máximos", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(
                    type="number",
                    value=ConfigState.mcp_max_retries.to(str),
                    on_change=ConfigState.change_mcp_max_retries,
                    width="100%",
                    style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "8px"}
                ),
                align_items="start"
            ),
            rx.vstack(
                rx.text("Demora de Reintento (seg)", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(
                    type="number",
                    value=ConfigState.mcp_retry_delay.to(str),
                    on_change=ConfigState.change_mcp_retry_delay,
                    width="100%",
                    style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "8px"}
                ),
                align_items="start"
            ),
            columns="3",
            spacing="4",
            width="100%"
        ),
        
        rx.hstack(
            rx.switch(
                checked=ConfigState.mcp_emergency_mode,
                on_change=ConfigState.set_mcp_emergency_mode
            ),
            rx.text("Modo de Emergencia (Uso Directo de Gemini)", font_size="13px", font_weight="bold"),
            spacing="3",
            align="center",
            style={"margin_top": "12px"}
        ),
        
        rx.divider(style={"border_color": BORDER_COLOR, "margin": "16px 0"}),
        
        rx.heading("Keycloak OAuth & Seguridad", size="3", color="#FFFFFF"),
        rx.hstack(
            rx.switch(
                checked=ConfigState.mcp_use_keycloak,
                on_change=ConfigState.set_mcp_use_keycloak
            ),
            rx.text("Utilizar Autenticación Keycloak", font_size="13px", font_weight="bold"),
            spacing="3",
            align="center"
        ),
        
        rx.cond(
            ConfigState.mcp_use_keycloak,
            rx.vstack(
                rx.text("Servidor Keycloak URL", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(
                    value=ConfigState.kc_server_url,
                    on_change=ConfigState.set_kc_server_url,
                    width="100%",
                    style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "8px"}
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Realm", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                        rx.input(value=ConfigState.kc_realm, on_change=ConfigState.set_kc_realm, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"})
                    ),
                    rx.vstack(
                        rx.text("Client ID", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                        rx.input(value=ConfigState.kc_client_id, on_change=ConfigState.set_kc_client_id, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"})
                    ),
                    columns="2",
                    spacing="4",
                    width="100%"
                ),
                rx.text("Client Secret", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(
                    type="password",
                    value=ConfigState.kc_client_secret,
                    on_change=ConfigState.set_kc_client_secret,
                    width="100%",
                    style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"}
                ),
                width="100%",
                spacing="3"
            ),
            rx.vstack(
                rx.text("Manual Bearer Token", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(
                    type="password",
                    value=ConfigState.mcp_token,
                    on_change=ConfigState.set_mcp_token,
                    width="100%",
                    style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"}
                ),
                width="100%"
            )
        ),
        
        rx.hstack(
            rx.button("💾 Guardar Configuración", on_click=ConfigState.save_mcp_settings, style={"background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)", "color": "#FFFFFF", "cursor": "pointer"}),
            rx.button("🧪 Probar Conexión MCP", on_click=ConfigState.test_mcp_connection, variant="outline", style={"cursor": "pointer", "border_color": BORDER_COLOR, "color": "#FFFFFF"}),
            spacing="3",
            style={"margin_top": "20px"}
        ),
        width="100%",
        spacing="3"
    )

    # 👥 Dynamic Agents Tab
    agent_creation_form = rx.vstack(
        rx.heading(rx.cond(ConfigState.edit_mode, "📝 Editar Agente", "➕ Agregar Nuevo Agente"), size="3", color="#FFFFFF"),
        rx.grid(
            rx.vstack(
                rx.text("Nombre del Agente", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(value=ConfigState.agent_name, on_change=ConfigState.set_agent_name, disabled=ConfigState.edit_mode, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"})
            ),
            rx.vstack(
                rx.text("MCP URL Personalizado (Opcional)", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(value=ConfigState.agent_mcp_url, on_change=ConfigState.set_agent_mcp_url, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"})
            ),
            columns="2",
            spacing="4",
            width="100%"
        ),
        rx.hstack(
            rx.hstack(
                rx.switch(checked=ConfigState.agent_is_orchestrator, on_change=ConfigState.set_agent_is_orchestrator),
                rx.text("¿Es Orquestador?", font_size="12px", font_weight="bold")
            ),
            rx.hstack(
                rx.switch(checked=ConfigState.agent_readonly, on_change=ConfigState.set_agent_readonly),
                rx.text("Modo Solo Lectura", font_size="12px", font_weight="bold")
            ),
            rx.hstack(
                rx.switch(checked=ConfigState.agent_web_search, on_change=ConfigState.set_agent_web_search),
                rx.text("Web Search Habilitado", font_size="12px", font_weight="bold")
            ),
            spacing="5",
            style={"margin": "8px 0"}
        ),
        rx.text("Prompt de Sistema", font_size="12px", font_weight="bold", color=TEXT_MUTED),
        rx.text_area(
            value=ConfigState.agent_prompt,
            on_change=ConfigState.set_agent_prompt,
            width="100%",
            style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "8px", "height": "100px"}
        ),
        rx.grid(
            rx.vstack(
                rx.text("Reglas Específicas (JSON)", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.text_area(value=ConfigState.agent_rules_raw, on_change=ConfigState.set_agent_rules_raw, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "8px", "height": "120px"})
            ),
            rx.vstack(
                rx.text("Fuentes de Conocimiento (1 ID por línea)", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.text_area(value=ConfigState.agent_knowledge_raw, on_change=ConfigState.set_agent_knowledge_raw, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "color": "#FFFFFF", "border_radius": "8px", "height": "120px"})
            ),
            columns="2",
            spacing="4",
            width="100%"
        ),
        rx.hstack(
            rx.button("💾 Guardar Agente", on_click=ConfigState.save_agent_form, style={"background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)", "color": "#FFFFFF", "cursor": "pointer"}),
            rx.cond(
                ConfigState.edit_mode,
                rx.button("Cancelar Edición", on_click=ConfigState.cancel_agent_edit, variant="outline", style={"cursor": "pointer", "border_color": BORDER_COLOR, "color": "#FFFFFF"})
            ),
            spacing="3",
            style={"margin_top": "12px"}
        ),
        width="100%",
        style={"padding": "20px", "border": f"1px solid {BORDER_COLOR}", "border_radius": "12px", "background_color": "rgba(255,255,255,0.01)"}
    )

    agents_list = rx.vstack(
        rx.heading("Lista de Agentes Activos", size="3", color="#FFFFFF", style={"margin_top": "20px"}),
        rx.cond(
            ConfigState.agents.length() > 0,
            rx.vstack(
                rx.foreach(
                    ConfigState.agents,
                    agent_card
                ),
                width="100%"
            ),
            rx.text("No hay agentes configurados actualmente.")
        ),
        width="100%"
    )

    # 💾 Cache Settings Tab
    cache_form = rx.vstack(
        rx.heading("💾 Cache del Sistema", size="4", color="#FFFFFF", style={"margin_bottom": "16px"}),
        rx.hstack(
            rx.switch(checked=ConfigState.cache_enabled, on_change=ConfigState.set_cache_enabled),
            rx.text("Habilitar Caché de Respuestas", font_size="13px", font_weight="bold"),
            spacing="3",
            align="center"
        ),
        rx.grid(
            rx.vstack(
                rx.text("TTL de Caché (segundos)", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(type="number", value=ConfigState.cache_ttl.to(str), on_change=ConfigState.change_cache_ttl, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"})
            ),
            rx.vstack(
                rx.text("Capacidad Máxima (entradas)", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(type="number", value=ConfigState.cache_max_size.to(str), on_change=ConfigState.change_cache_max_size, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"})
            ),
            columns="2",
            spacing="4",
            width="100%"
        ),
        rx.hstack(
            rx.button("💾 Guardar Caché", on_click=ConfigState.save_cache_settings, style={"background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)", "color": "#FFFFFF", "cursor": "pointer"}),
            rx.button("🧹 Vaciar Caché", on_click=ConfigState.clear_cache_maint, variant="outline", style={"cursor": "pointer", "border_color": BORDER_COLOR, "color": "#FFFFFF"}),
            spacing="3",
            style={"margin_top": "16px"}
        ),
        width="100%",
        spacing="3"
    )

    # 🔐 Security Tab
    security_form = rx.vstack(
        rx.heading("🔐 Seguridad y Webhooks", size="4", color="#FFFFFF", style={"margin_bottom": "16px"}),
        rx.text("Webhook Secret Key (Respond.io validation)", font_size="12px", font_weight="bold", color=TEXT_MUTED),
        rx.hstack(
            rx.input(type="password", value=ConfigState.webhook_secret, on_change=ConfigState.set_webhook_secret, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"}),
            rx.button("🔄 Regenerar", on_click=ConfigState.regenerate_webhook_secret, variant="outline", style={"cursor": "pointer", "border_color": BORDER_COLOR, "color": "#FFFFFF"}),
            width="100%",
            spacing="3"
        ),
        rx.vstack(
            rx.text("Límite de Peticiones (requests/min por IP)", font_size="12px", font_weight="bold", color=TEXT_MUTED),
            rx.input(type="number", value=ConfigState.rate_limit.to(str), on_change=ConfigState.change_rate_limit, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"}),
            align_items="start",
            width="100%"
        ),
        rx.button("💾 Guardar Seguridad", on_click=ConfigState.save_security_settings, style={"background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)", "color": "#FFFFFF", "cursor": "pointer", "margin_top": "16px"}),
        width="100%",
        spacing="3"
    )

    # 🤖 AI settings Tab
    ai_form = rx.vstack(
        rx.heading("🤖 Integración Inteligencia Artificial", size="4", color="#FFFFFF", style={"margin_bottom": "16px"}),
        rx.text("Google Gemini API Key", font_size="12px", font_weight="bold", color=TEXT_MUTED),
        rx.input(
            type="password",
            value=ConfigState.gemini_api_key,
            on_change=ConfigState.set_gemini_api_key,
            width="100%",
            style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"}
        ),
        rx.text("Esta llave se utiliza para consultas conversacionales directas cuando el DevOps MCP está apagado o en modo emergencia.", font_size="11px", color=TEXT_MUTED),
        rx.button("💾 Guardar Configuración IA", on_click=ConfigState.save_mcp_settings, style={"background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)", "color": "#FFFFFF", "cursor": "pointer", "margin_top": "16px"}),
        width="100%",
        spacing="3"
    )

    # 🚨 Email Alerts Tab
    email_form = rx.vstack(
        rx.heading("🚨 Alertas Críticas por Correo", size="4", color="#FFFFFF", style={"margin_bottom": "16px"}),
        rx.hstack(
            rx.switch(checked=ConfigState.email_enabled, on_change=ConfigState.set_email_enabled),
            rx.text("Habilitar Alertas por Email", font_size="13px", font_weight="bold"),
            spacing="3",
            align="center"
        ),
        rx.grid(
            rx.vstack(
                rx.text("Servidor SMTP", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(value=ConfigState.smtp_server, on_change=ConfigState.set_smtp_server, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"})
            ),
            rx.vstack(
                rx.text("Puerto SMTP", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(type="number", value=ConfigState.smtp_port.to(str), on_change=ConfigState.change_smtp_port, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"})
            ),
            columns="2",
            spacing="4",
            width="100%"
        ),
        rx.grid(
            rx.vstack(
                rx.text("SMTP Username (Email)", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(value=ConfigState.smtp_user, on_change=ConfigState.set_smtp_user, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"})
            ),
            rx.vstack(
                rx.text("SMTP App Password", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                rx.input(type="password", value=ConfigState.smtp_password, on_change=ConfigState.set_smtp_password, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"})
            ),
            columns="2",
            spacing="4",
            width="100%"
        ),
        rx.vstack(
            rx.text("Email Destinatario de Alertas", font_size="12px", font_weight="bold", color=TEXT_MUTED),
            rx.input(value=ConfigState.recipient_email, on_change=ConfigState.set_recipient_email, width="100%", style={"background_color": "#0C0F1D", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px"}),
            align_items="start",
            width="100%"
        ),
        rx.hstack(
            rx.switch(checked=ConfigState.alert_on_mcp_error, on_change=ConfigState.set_alert_on_mcp_error),
            rx.text("Alertar si falla conexión al MCP", font_size="12px"),
            spacing="3",
            align="center"
        ),
        rx.hstack(
            rx.switch(checked=ConfigState.alert_on_circuit_breaker, on_change=ConfigState.set_alert_on_circuit_breaker),
            rx.text("Alertar si se abre el Circuit Breaker", font_size="12px"),
            spacing="3",
            align="center"
        ),
        rx.button("💾 Guardar Configuración de Correo", on_click=ConfigState.save_email_settings, style={"background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)", "color": "#FFFFFF", "cursor": "pointer", "margin_top": "16px"}),
        width="100%",
        spacing="3"
    )

    # 🌐 Google Cloud Sources & Service Accounts Form
    google_sources_form = rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.heading("🌐 Fuentes de Conocimiento Google Cloud & Service Accounts", size="4", font_weight="bold"),
                rx.text("Administre dinámicamente los IDs de documentos/hojas y ejecute sincronizaciones en vivo.", color=TEXT_MUTED, font_size="13px"),
                spacing="1"
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon("zap", size=16),
                    rx.text("⚡ Forzar Sincronización Inmediata"),
                    spacing="2",
                    align="center"
                ),
                on_click=ConfigState.force_sync_sources,
                color_scheme="cyan",
                variant="solid",
                is_loading=ConfigState.is_loading
            ),
            width="100%",
            align="center",
            margin_bottom="12px"
        ),

        # Block 1: MAXIBOT Service Account (Aislada)
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("bot", size=18, color=ACCENT_PURPLE),
                    rx.text("🤖 MAXIBOT Service Account (Agente Aislado)", font_size="14px", font_weight="bold"),
                    rx.badge("athenas-panel", color_scheme="purple", variant="soft"),
                    spacing="2",
                    align="center"
                ),
                rx.text("SA: athenas-driver-reader@athenas-panel.iam.gserviceaccount.com", font_size="11px", color=TEXT_MUTED),
                rx.vstack(
                    rx.text("FAQ Knowledge Base (Google Sheet ID)", font_size="12px", font_weight="bold", color=TEXT_MUTED),
                    rx.input(
                        value=ConfigState.maxibot_sheet_faq_id,
                        on_change=ConfigState.set_maxibot_sheet_faq_id,
                        width="100%",
                        style={"color": "#38BDF8", "background_color": "#0F1322", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px", "font_family": "monospace", "font_size": "13px"}
                    ),
                    align_items="start",
                    width="100%"
                ),
                spacing="3",
                align_items="stretch"
            ),
            style={
                "background": "rgba(255, 255, 255, 0.02)",
                "padding": "16px",
                "border_radius": "10px",
                "border": f"1px solid {BORDER_COLOR}",
                "margin_bottom": "16px"
            }
        ),

        # Block 2: ORBIT Service Account
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("activity", size=18, color=ACCENT_BLUE),
                    rx.text("📱 ORBIT Middleware Service Account (Cerebro Core)", font_size="14px", font_weight="bold"),
                    rx.badge("maxibot-472423", color_scheme="blue", variant="soft"),
                    spacing="2",
                    align="center"
                ),
                rx.text("SA: maxibot-sa@maxibot-472423.iam.gserviceaccount.com", font_size="11px", color=TEXT_MUTED),
                rx.grid(
                    rx.vstack(
                        rx.hstack(rx.icon("file-text", size=14, color=ACCENT_BLUE), rx.text("Reglas Generales de Uso (Google Doc ID)", font_size="12px", font_weight="bold", color=TEXT_MUTED), spacing="1"),
                        rx.input(value=ConfigState.orbit_doc_governance_id, on_change=ConfigState.set_orbit_doc_governance_id, width="100%", style={"color": "#38BDF8", "background_color": "#0F1322", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px", "font_family": "monospace", "font_size": "13px"}),
                        align_items="start"
                    ),
                    rx.vstack(
                        rx.hstack(rx.icon("table", size=14, color=ACCENT_BLUE), rx.text("Matriz de Reglas RNE (59 Reglas Sheet ID)", font_size="12px", font_weight="bold", color=TEXT_MUTED), spacing="1"),
                        rx.input(value=ConfigState.orbit_sheet_rules_id, on_change=ConfigState.set_orbit_sheet_rules_id, width="100%", style={"color": "#38BDF8", "background_color": "#0F1322", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px", "font_family": "monospace", "font_size": "13px"}),
                        align_items="start"
                    ),
                    rx.vstack(
                        rx.hstack(rx.icon("table", size=14, color=ACCENT_BLUE), rx.text("Catálogo de Scripts SC (113 Scripts Sheet ID)", font_size="12px", font_weight="bold", color=TEXT_MUTED), spacing="1"),
                        rx.input(value=ConfigState.orbit_sheet_scripts_id, on_change=ConfigState.set_orbit_sheet_scripts_id, width="100%", style={"color": "#38BDF8", "background_color": "#0F1322", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px", "font_family": "monospace", "font_size": "13px"}),
                        align_items="start"
                    ),
                    rx.vstack(
                        rx.hstack(rx.icon("table", size=14, color=ACCENT_BLUE), rx.text("Estatus Envíos Core (Sheet ID)", font_size="12px", font_weight="bold", color=TEXT_MUTED), spacing="1"),
                        rx.input(value=ConfigState.orbit_sheet_estatus_id, on_change=ConfigState.set_orbit_sheet_estatus_id, width="100%", style={"color": "#38BDF8", "background_color": "#0F1322", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px", "font_family": "monospace", "font_size": "13px"}),
                        align_items="start"
                    ),
                    rx.vstack(
                        rx.hstack(rx.icon("table", size=14, color=ACCENT_BLUE), rx.text("Bill Payment Estatus (Sheet ID)", font_size="12px", font_weight="bold", color=TEXT_MUTED), spacing="1"),
                        rx.input(value=ConfigState.orbit_sheet_bill_id, on_change=ConfigState.set_orbit_sheet_bill_id, width="100%", style={"color": "#38BDF8", "background_color": "#0F1322", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px", "font_family": "monospace", "font_size": "13px"}),
                        align_items="start"
                    ),
                    rx.vstack(
                        rx.hstack(rx.icon("table", size=14, color=ACCENT_BLUE), rx.text("Topup Estatus (Sheet ID)", font_size="12px", font_weight="bold", color=TEXT_MUTED), spacing="1"),
                        rx.input(value=ConfigState.orbit_sheet_topup_id, on_change=ConfigState.set_orbit_sheet_topup_id, width="100%", style={"color": "#38BDF8", "background_color": "#0F1322", "border": f"1px solid {BORDER_COLOR}", "border_radius": "8px", "font_family": "monospace", "font_size": "13px"}),
                        align_items="start"
                    ),
                    columns="2",
                    spacing="4",
                    width="100%"
                ),
                spacing="3",
                align_items="stretch"
            ),
            style={
                "background": "rgba(255, 255, 255, 0.02)",
                "padding": "16px",
                "border_radius": "10px",
                "border": f"1px solid {BORDER_COLOR}",
                "margin_bottom": "16px"
            }
        ),

        rx.button(
            "💾 Guardar Configuración de Fuentes Google",
            on_click=ConfigState.save_google_sources,
            style={"background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)", "color": "#FFFFFF", "cursor": "pointer", "margin_top": "8px"}
        ),
        width="100%",
        spacing="3"
    )

    # Compile tabs layout using Radix
    tabs_section = rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger("🔌 MCP Server", value="mcp", style={"cursor": "pointer"}),
            rx.tabs.trigger("👥 Agentes IA", value="agents", style={"cursor": "pointer"}),
            rx.tabs.trigger("🌐 Fuentes Google", value="google_sources", style={"cursor": "pointer"}),
            rx.tabs.trigger("💾 Caché", value="cache", style={"cursor": "pointer"}),
            rx.tabs.trigger("🔐 Seguridad", value="security", style={"cursor": "pointer"}),
            rx.tabs.trigger("🤖 Gemini IA", value="ai", style={"cursor": "pointer"}),
            rx.tabs.trigger("🚨 Alertas", value="alerts", style={"cursor": "pointer"}),
        ),
        rx.tabs.content(
            glass_container(mcp_form, style={"padding": "24px", "margin_top": "16px"}),
            value="mcp"
        ),
        rx.tabs.content(
            rx.vstack(
                agent_creation_form,
                agents_list,
                spacing="4",
                style={"margin_top": "16px"}
            ),
            value="agents"
        ),
        rx.tabs.content(
            glass_container(google_sources_form, style={"padding": "24px", "margin_top": "16px"}),
            value="google_sources"
        ),
        rx.tabs.content(
            glass_container(cache_form, style={"padding": "24px", "margin_top": "16px"}),
            value="cache"
        ),
        rx.tabs.content(
            glass_container(security_form, style={"padding": "24px", "margin_top": "16px"}),
            value="security"
        ),
        rx.tabs.content(
            glass_container(ai_form, style={"padding": "24px", "margin_top": "16px"}),
            value="ai"
        ),
        rx.tabs.content(
            glass_container(email_form, style={"padding": "24px", "margin_top": "16px"}),
            value="alerts"
        ),
        default_value="mcp",
        width="100%"
    )

    # Main content assembly
    content = rx.vstack(
        rx.cond(
            ConfigState.is_loading,
            rx.center(rx.spinner(size="3", color=ACCENT_BLUE), width="100%", height="250px"),
            tabs_section
        ),
        width="100%"
    )

    return protected_layout(content, "Configuración del Sistema", "/config")
