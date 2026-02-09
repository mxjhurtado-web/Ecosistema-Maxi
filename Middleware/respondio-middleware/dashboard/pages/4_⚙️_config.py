"""
⚙️ Configuration Page
"""

import streamlit as st
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth import require_auth
from components.api_client import api_client
from components.page_setup import setup_page

# Setup page with ORBIT theme
setup_page("Configuration", "⚙️")

# Require authentication
require_auth()

# Tabs for different config sections
tab1, tab2, tab3, tab4 = st.tabs(["🔌 MCP Settings", "💾 Cache Settings", "🔐 Security", "🤖 AI Integration"])

# ============================================================
# MCP Configuration
# ============================================================

with tab1:
    st.subheader("🔌 MCP Configuration")
    
    # Fetch current config
    mcp_config = api_client.get_mcp_config()
    
    if mcp_config:
        with st.form("mcp_config_form"):
            st.markdown("### Connection Settings")
            
            url = st.text_input(
                "MCP URL",
                value=mcp_config.get('url', ''),
                help="Full URL to the MCP query endpoint"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                timeout = st.number_input(
                    "Timeout (seconds)",
                    min_value=1,
                    max_value=30,
                    value=mcp_config.get('timeout', 5),
                    help="Maximum time to wait for MCP response"
                )
            
            with col2:
                max_retries = st.number_input(
                    "Max Retries",
                    min_value=0,
                    max_value=10,
                    value=mcp_config.get('max_retries', 3),
                    help="Number of retry attempts on failure"
                )
            
            retry_delay = st.number_input(
                "Retry Delay (seconds)",
                min_value=0,
                max_value=10,
                value=mcp_config.get('retry_delay', 1),
                help="Delay entre retry attempts"
            )
            
            st.markdown("---")
            st.markdown("### 🔐 MCP Security Settings")
            
            mcp_token = st.text_input(
                "MCP Authentication Token",
                value=mcp_config.get('mcp_token', '') or '',
                type="password",
                help="Token de seguridad para autenticarse con el servidor MCP (Bearer Token)"
            )
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit = st.form_submit_button("💾 Save Configuration", use_container_width=True)
            
            with col2:
                test = st.form_submit_button("🧪 Test Connection", use_container_width=True)
            
            if submit:
                # Update config
                new_config = {
                    "url": url,
                    "timeout": timeout,
                    "max_retries": max_retries,
                    "retry_delay": retry_delay,
                    "mcp_token": mcp_token,
                    "gemini_api_key": mcp_config.get('gemini_api_key')
                }
                
                with st.spinner("Updating configuration..."):
                    success = api_client.update_mcp_config(new_config)
                
                if success:
                    st.success("✅ Configuration updated successfully!")
                    st.balloons()
                else:
                    st.error("❌ Failed to update configuration")
            
            if test:
                with st.spinner("Testing MCP connection..."):
                    result = api_client.test_mcp("Test query from dashboard")
                
                if result and result.get('status') == 'ok':
                    st.success(f"✅ MCP is responding! Latency: {result.get('latency_ms')} ms")
                    st.info(f"Response: {result.get('mcp_response', 'N/A')}")
                else:
                    st.error(f"❌ MCP test failed: {result.get('error', 'Unknown error') if result else 'No response'}")
    else:
        st.error("❌ Unable to fetch MCP configuration")

# ============================================================
# Cache Configuration
# ============================================================

with tab2:
    st.subheader("💾 Cache Configuration")
    
    # Fetch current config
    cache_config = api_client.get_cache_config()
    
    if cache_config:
        with st.form("cache_config_form"):
            st.markdown("### Cache Settings")
            
            enabled = st.checkbox(
                "Enable Cache",
                value=cache_config.get('enabled', True),
                help="Enable response caching"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                ttl = st.number_input(
                    "TTL (seconds)",
                    min_value=0,
                    max_value=3600,
                    value=cache_config.get('ttl', 300),
                    help="Time to live for cached entries"
                )
            
            with col2:
                max_size = st.number_input(
                    "Max Size (entries)",
                    min_value=0,
                    max_value=10000,
                    value=cache_config.get('max_size', 1000),
                    help="Maximum number of cached entries"
                )
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit = st.form_submit_button("💾 Save Configuration", use_container_width=True)
            
            with col2:
                clear = st.form_submit_button("🧹 Clear Cache", use_container_width=True)
            
            if submit:
                # Update config
                new_config = {
                    "enabled": enabled,
                    "ttl": ttl,
                    "max_size": max_size
                }
                
                with st.spinner("Updating configuration..."):
                    success = api_client.update_cache_config(new_config)
                
                if success:
                    st.success("✅ Cache configuration updated successfully!")
                else:
                    st.error("❌ Failed to update configuration")
            
            if clear:
                with st.spinner("Clearing cache..."):
                    success = api_client.clear_cache()
                
                if success:
                    st.success("✅ Cache cleared successfully!")
                else:
                    st.error("❌ Failed to clear cache")
    else:
        st.error("❌ Unable to fetch cache configuration")

# ============================================================
# Security Configuration
# ============================================================

with tab3:
    st.subheader("🔐 Security Configuration")
    
    st.warning("⚠️ **Warning:** Changing security settings may affect active connections")
    
    # Fetch current config
    security_config = api_client.get_security_config()
    
    if security_config:
        with st.form("security_config_form"):
            st.markdown("### Security Settings")
            
            webhook_secret = st.text_input(
                "Webhook Secret",
                value=security_config.get('webhook_secret', ''),
                type="password",
                help="Secret key for webhook validation"
            )
            
            rate_limit = st.number_input(
                "Rate Limit (requests/minute)",
                min_value=1,
                max_value=1000,
                value=security_config.get('rate_limit', 100),
                help="Maximum requests per minute per IP"
            )
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit = st.form_submit_button("💾 Save Configuration", use_container_width=True)
            
            with col2:
                regenerate = st.form_submit_button("🔄 Regenerate Secret", use_container_width=True)
            
            if submit:
                # Update config
                new_config = {
                    "webhook_secret": webhook_secret,
                    "rate_limit": rate_limit
                }
                
                with st.spinner("Updating configuration..."):
                    success = api_client.update_security_config(new_config)
                
                if success:
                    st.success("✅ Security configuration updated successfully!")
                    st.warning("⚠️ Make sure to update Respond.io with the new webhook secret")
                else:
                    st.error("❌ Failed to update configuration")
            
            if regenerate:
                import secrets
                new_secret = secrets.token_urlsafe(32)
                
                st.info(f"New secret generated: `{new_secret}`")
                st.warning("⚠️ Copy this secret and update the form above, then save")
    else:
        st.error("❌ Unable to fetch security configuration")

# ============================================================
# AI Integration
# ============================================================

with tab4:
    st.subheader("🤖 AI Integration Settings")
    
    st.info("Configura la integración con LLMs externos para potenciar el servidor Mock MCP.")
    
    # Fetch current config again to ensure we have latest
    mcp_config = api_client.get_mcp_config()
    
    if mcp_config:
        with st.form("gemini_config_form"):
            st.markdown("### Google Gemini")
            
            gemini_api_key = st.text_input(
                "Gemini API Key",
                value=mcp_config.get('gemini_api_key', '') or '',
                type="password",
                help="Clave de API de Google Gemini para habilitar respuestas inteligentes en el Mock MCP"
            )
            
            st.caption("Si se proporciona, el servidor Mock MCP usará Gemini para responder consultas generales.")
            
            submit_gemini = st.form_submit_button("💾 Save AI Configuration", use_container_width=True)
            
            if submit_gemini:
                # Update only the gemini key, keeping other settings
                new_config = mcp_config.copy()
                new_config["gemini_api_key"] = gemini_api_key
                
                with st.spinner("Updating AI configuration..."):
                    success = api_client.update_mcp_config(new_config)
                
                if success:
                    st.success("✅ Gemini API Key updated successfully!")
                    st.balloons()
                else:
                    st.error("❌ Failed to update configuration")
    else:
        st.error("❌ Unable to fetch configuration")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
