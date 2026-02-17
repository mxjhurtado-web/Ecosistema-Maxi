"""
🔧 Maintenance Page with User Management
"""

import streamlit as st
from datetime import datetime
import sys
import os

# Add project root to path with high priority
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from components.auth import require_auth
from components.api_client import api_client
from components.page_setup import setup_page, create_status_badge

# Setup page with ORBIT theme
setup_page("Maintenance", "🔧")

# Require authentication
require_auth()

# RBAC Check: Only Admins can access maintenance
if st.session_state.get("role") != "admin":
    st.warning("⚠️ Access Denied: This page is only for Administrators.")
    st.info("You will be redirected to the KPIs page...")
    import time
    time.sleep(2)
    st.switch_page("pages/1_📊_kpis.py")
    st.stop()

st.title("🔧 System Maintenance")
st.markdown("---")

# Navigation Tabs
tabs = st.tabs(["🚀 Diagnostics", "👥 User Management", "⚙️ System Controls", "📚 Knowledge Base"])

# ============================================================
# TAB 1: Diagnostics
# ============================================================
with tabs[0]:
    st.subheader("🏥 Health Checks")
    
    if st.button("🔄 Refresh Status", key="refresh_health"):
        st.rerun()

    with st.spinner("Checking system health..."):
        health = api_client.get_health()

    if health:
        col1, col2, col3 = st.columns(3)
        with col1:
            status = health.get('status', 'unknown')
            if status == 'healthy': st.success("✅ API Status: Healthy")
            elif status == 'degraded': st.warning("⚠️ API Status: Degraded")
            else: st.error("❌ API Status: Unhealthy")
        with col2:
            mcp_status = health.get('mcp_status', 'unknown')
            if mcp_status == 'healthy': st.success("✅ MCP Status: Online")
            else: st.error("❌ MCP Status: Offline")
        with col3:
            redis_status = health.get('redis_status', 'unknown')
            if redis_status == 'healthy': st.success("✅ Redis Status: Connected")
            elif redis_status == 'disabled': st.warning("⚠️ Redis Status: Disabled")
            else: st.error("❌ Redis Status: Disconnected")
    else:
        st.error("❌ Unable to fetch health status")

    st.markdown("---")
    st.subheader("🧪 Test Tools")
    
    with st.form("test_mcp_form"):
        st.markdown("### Test MCP Connection")
        test_query = st.text_area("Test Query", value="Hola, ¿cómo estás?")
        submit = st.form_submit_button("🚀 Send Test Request", use_container_width=True)
        
        if submit:
            with st.spinner("Sending test request to MCP..."):
                result = api_client.test_mcp(test_query)
            if result and result.get('status') == 'ok':
                st.success("✅ Test successful!")
                st.info(f"Response: {result.get('mcp_response')}")
            else:
                st.error(f"❌ Test failed: {result.get('error', 'Unknown error')}")

# ============================================================
# TAB 2: User Management
# ============================================================
with tabs[1]:
    st.subheader("👥 Dashboard Users")
    st.info("Administra quién puede acceder al panel. Máximo 3 por rol.")
    
    users = api_client.get_users()
    
    if users:
        # Display User List
        admins = [u for u in users if u.get('role') == 'admin']
        supervisors = [u for u in users if u.get('role') == 'supervisor']
        
        col_list, col_add = st.columns([2, 1])
        
        with col_list:
            st.markdown(f"#### Active Users ({len(users)})")
            for u in users:
                role_icon = "🔑" if u.get('role') == 'admin' else "👁️"
                with st.expander(f"{role_icon} **{u.get('username')}** ({u.get('role')})"):
                    st.write(f"Created: {u.get('created_at', 'N/A')}")
                    # Don't allow deleting the current user or the last admin
                    is_current = u.get('username') == st.session_state.get('username')
                    if not is_current:
                        if st.button(f"🗑️ Delete {u.get('username')}", key=f"del_{u.get('username')}"):
                            if api_client.delete_user(u.get('username')):
                                st.success(f"User {u.get('username')} deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete user.")
                    else:
                        st.info("This is your current session.")

        with col_add:
            st.markdown("#### ✨ Create New User")
            with st.form("add_user_form"):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["admin", "supervisor"])
                
                # Show limits info
                count = len(admins) if new_role == "admin" else len(supervisors)
                st.caption(f"Current {new_role}s: {count}/3")
                
                add_submit = st.form_submit_button("➕ Create User", use_container_width=True)
                
                if add_submit:
                    if not new_username or not new_password:
                        st.error("Please fill all fields.")
                    else:
                        new_user = {
                            "username": new_username,
                            "password": new_password,
                            "role": new_role
                        }
                        if api_client.add_user(new_user):
                            st.success("User created successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to create user. Check limits.")
    else:
        st.warning("No users found or Redis unavailable.")

# ============================================================
# TAB 3: System Controls
# ============================================================
with tabs[2]:
    st.subheader("⚡ Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reload Configuration", use_container_width=True):
            if api_client.reload_config(): st.success("✅ Configuration reloaded!")
            else: st.error("❌ Failed to reload configuration")
    with col2:
        if st.button("🧹 Clear Cache", use_container_width=True):
            if api_client.clear_cache(): st.success("✅ Cache cleared!")
            else: st.error("❌ Failed to clear cache")

    st.markdown("---")
    st.subheader("🔌 Circuit Breaker")
    cb = api_client.get_circuit_breaker_status()
    if cb:
        c1, c2, c3 = st.columns(3)
        c1.metric("Enabled", "Yes" if cb.get('enabled') else "No")
        c2.metric("Status", "OPEN 🔴" if cb.get('is_open') else "CLOSED 🟢")
        c3.metric("Failures", f"{cb.get('failure_count')}/{cb.get('failure_threshold')}")
        if cb.get('is_open'):
            if st.button("🔄 Reset Circuit Breaker"):
                api_client.reset_circuit_breaker()
                st.rerun()

# ============================================================
# TAB 4: Knowledge Base
# ============================================================
with tabs[3]:
    st.subheader("📚 Knowledge Base & FAQ")
    st.markdown("Acceso rápido a guías y resolución de dudas comunes.")
    
    knowledge = api_client.get_knowledge()
    
    # Show the direct link for easy copying
    knowledge_url = f"{api_client.base_url}/knowledge"
    st.info("🔗 **Public Knowledge URL (JSON)**")
    st.code(knowledge_url, language="text")
    st.caption("Esta es la liga que puedes compartir o usar en integraciones externas.")
    
    st.markdown("---")
    
    if knowledge:
        faq = knowledge.get('faq', [])
        for item in faq:
            with st.expander(f"❓ {item.get('question')}"):
                st.write(item.get('answer'))
        
        st.markdown("---")
        st.subheader("🔗 Enlaces Útiles")
        links = knowledge.get('links', [])
        cols = st.columns(len(links) if links else 1)
        for i, link in enumerate(links):
            with cols[i]:
                # Build absolute URL if it's a relative path
                url = link.get('url')
                if url.startswith('/'):
                    url = f"{api_client.base_url}{url}"
                st.link_button(link.get('name'), url, use_container_width=True)
    else:
        st.info("💡 La base de conocimientos no está disponible en este momento.")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
