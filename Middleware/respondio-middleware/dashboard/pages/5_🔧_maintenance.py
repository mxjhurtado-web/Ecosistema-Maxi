"""
🔧 Maintenance Page
"""

import streamlit as st
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth import require_auth
from components.api_client import api_client
from components.page_setup import setup_page, create_status_badge

# Setup page with ORBIT theme
setup_page("Maintenance", "🔧")

# Require authentication
require_auth()

# ============================================================
# Health Checks
# ============================================================

st.subheader("🏥 Health Checks")

col1, col2 = st.columns([3, 1])

with col2:
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.rerun()

with st.spinner("Checking system health..."):
    health = api_client.get_health()

if health:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = health.get('status', 'unknown')
        if status == 'healthy':
            st.success("✅ API Status: Healthy")
        elif status == 'degraded':
            st.warning("⚠️ API Status: Degraded")
        else:
            st.error("❌ API Status: Unhealthy")
    
    with col2:
        mcp_status = health.get('mcp_status', 'unknown')
        if mcp_status == 'healthy':
            st.success("✅ MCP Status: Online")
        else:
            st.error("❌ MCP Status: Offline")
    
    with col3:
        redis_status = health.get('redis_status', 'unknown')
        if redis_status == 'healthy':
            st.success("✅ Redis Status: Connected")
        elif redis_status == 'disabled':
            st.warning("⚠️ Redis Status: Disabled")
        else:
            st.error("❌ Redis Status: Disconnected")
else:
    st.error("❌ Unable to fetch health status")

st.markdown("---")

# ============================================================
# Test Tools
# ============================================================

st.subheader("🧪 Test Tools")

with st.form("test_mcp_form"):
    st.markdown("### Test MCP Connection")
    
    test_query = st.text_area(
        "Test Query",
        value="Hola, ¿cómo estás?",
        help="Enter a test query to send to the MCP"
    )
    
    submit = st.form_submit_button("🚀 Send Test Request", use_container_width=True)
    
    if submit:
        with st.spinner("Sending test request to MCP..."):
            result = api_client.test_mcp(test_query)
        
        if result:
            if result.get('status') == 'ok':
                st.success("✅ Test successful!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Latency", f"{result.get('latency_ms', 0)} ms")
                    st.metric("Retry Count", result.get('retry_count', 0))
                
                with col2:
                    st.metric("Response Status", result.get('response_status', 'N/A'))
                    st.metric("Timestamp", result.get('timestamp', 'N/A'))
                
                st.markdown("### MCP Response")
                st.info(result.get('mcp_response', 'No response'))
            else:
                st.error(f"❌ Test failed: {result.get('error', 'Unknown error')}")
        else:
            st.error("❌ No response from API")

st.markdown("---")

# ============================================================
# Quick Actions
# ============================================================

st.subheader("⚡ Quick Actions")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Reload Configuration", use_container_width=True):
        with st.spinner("Reloading configuration..."):
            success = api_client.reload_config()
        
        if success:
            st.success("✅ Configuration reloaded!")
        else:
            st.error("❌ Failed to reload configuration")

with col2:
    if st.button("🧹 Clear Cache", use_container_width=True):
        with st.spinner("Clearing cache..."):
            success = api_client.clear_cache()
        
        if success:
            st.success("✅ Cache cleared!")
        else:
            st.error("❌ Failed to clear cache")

st.markdown("---")

# ============================================================
# Circuit Breaker
# ============================================================

st.subheader("🔌 Circuit Breaker")

circuit_status = api_client.get_circuit_breaker_status()

if circuit_status:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        enabled = circuit_status.get('enabled', False)
        if enabled:
            st.success("✅ Enabled")
        else:
            st.warning("⚠️ Disabled")
    
    with col2:
        is_open = circuit_status.get('is_open', False)
        if is_open:
            st.error("🔴 Circuit OPEN")
        else:
            st.success("🟢 Circuit CLOSED")
    
    with col3:
        failure_count = circuit_status.get('failure_count', 0)
        threshold = circuit_status.get('failure_threshold', 0)
        st.metric("Failures", f"{failure_count}/{threshold}")
    
    # Reset button
    if circuit_status.get('is_open'):
        st.warning("⚠️ Circuit breaker is open. MCP calls are being blocked.")
        
        if st.button("🔄 Reset Circuit Breaker", use_container_width=True):
            with st.spinner("Resetting circuit breaker..."):
                success = api_client.reset_circuit_breaker()
            
            if success:
                st.success("✅ Circuit breaker reset!")
                st.rerun()
            else:
                st.error("❌ Failed to reset circuit breaker")
else:
    st.warning("⚠️ Unable to fetch circuit breaker status")

st.markdown("---")

# ============================================================
# Webhook Connectivity
# ============================================================

st.subheader("🔗 Webhook Connectivity")

col1, col2 = st.columns([2, 1])

with col1:
    st.info("Utiliza esta información para configurar tu Webhook en la plataforma de Respond.io.")
    
    # Get security config for secret
    sec_config = api_client.get_security_config()
    webhook_secret = sec_config.get('webhook_secret', 'Not Set') if sec_config else 'Unknown'
    
    st.markdown("### 📡 Main Endpoint")
    st.code("http://localhost:8010/webhook", language="text")
    
    st.markdown("### 🔑 Security Header")
    st.markdown(f"**Header Name:** `X-Webhook-Secret`")
    st.markdown(f"**Value:** `{webhook_secret}`")

with col2:
    st.markdown("### 🌐 Public Access")
    st.markdown("""
    Para que Respond.io pueda enviarte mensajes, el API debe ser accesible desde internet.
    
    **Recomendación:**
    Usa `ngrok` para crear un túnel temporal:
    ```bash
    ngrok http 8010
    ```
    """)

st.markdown("---")

# ============================================================
# System Information
# ============================================================

st.subheader("📊 System Information")

system_info = api_client.get_system_info()

if system_info:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        memory_mb = system_info.get('memory_mb', 0)
        st.metric("Memory Usage", f"{memory_mb:.2f} MB")
    
    with col2:
        cpu_percent = system_info.get('cpu_percent', 0)
        st.metric("CPU Usage", f"{cpu_percent:.2f}%")
    
    with col3:
        uptime_seconds = system_info.get('uptime_seconds', 0)
        uptime_human = system_info.get('uptime_human', 'N/A')
        st.metric("Uptime", uptime_human)
    
    with col4:
        version = system_info.get('version', 'N/A')
        st.metric("Version", version)
    
    # Additional info
    with st.expander("📋 Additional Information"):
        st.text(f"Python Version: {system_info.get('python_version', 'N/A')}")
        
        if 'note' in system_info:
            st.info(system_info['note'])
else:
    st.warning("⚠️ Unable to fetch system information")

st.markdown("---")

# ============================================================
# Danger Zone
# ============================================================

with st.expander("⚠️ Danger Zone"):
    st.error("**Warning:** These actions may disrupt service")
    
    st.markdown("### Restart Service")
    st.warning("This feature requires container orchestration (e.g., Docker Compose, Kubernetes)")
    
    restart_confirm = st.checkbox("I understand the risks")
    
    if restart_confirm:
        if st.button("🔄 Restart Service", use_container_width=True):
            st.error("⚠️ Service restart not implemented. Use Docker/K8s commands directly.")
            st.code("docker-compose restart respondio_api", language="bash")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
