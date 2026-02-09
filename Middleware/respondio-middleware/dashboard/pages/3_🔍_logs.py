"""
🔍 Logs Viewer Page
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
setup_page("Logs Viewer", "🔍")

# Require authentication
require_auth()

if st.session_state.get("role") == "supervisor":
    st.warning("⚠️ Access Denied: Supervisors cannot view live logs.")
    st.switch_page("pages/1_📊_kpis.py")
    st.stop()

# Controls
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    log_level = st.selectbox(
        "Log Level",
        ["All", "ERROR", "WARNING", "INFO", "DEBUG"],
        index=0
    )

with col2:
    auto_refresh = st.checkbox("Auto-refresh", value=False)
    if auto_refresh:
        refresh_interval = st.slider("Interval (seconds)", 1, 30, 5)

with col3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.markdown("---")

# Note about logs
st.info("""
📝 **Note:** This page shows recent requests as log entries. 
For detailed application logs, check the container logs directly using:
```bash
docker logs respondio_api
```
""")

# Fetch recent requests as logs
with st.spinner("Loading logs..."):
    requests = api_client.get_recent_requests(limit=100)

if requests:
    # Display log statistics
    st.subheader("📊 Log Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        errors = len([r for r in requests if r.get('status') == 'error'])
        st.metric("Errors", errors, delta=None if errors == 0 else f"+{errors}")
    
    with col2:
        warnings = len([r for r in requests if r.get('status') == 'degraded'])
        st.metric("Warnings", warnings, delta=None if warnings == 0 else f"+{warnings}")
    
    with col3:
        info = len([r for r in requests if r.get('status') == 'ok'])
        st.metric("Info", info)
    
    st.markdown("---")
    
    # Display logs
    st.subheader("📋 Log Entries")
    
    # Create log container
    log_container = st.container()
    
    with log_container:
        for req in requests:
            status = req.get('status', 'unknown')
            timestamp = req.get('timestamp', 'N/A')
            trace_id = req.get('trace_id', 'N/A')
            
            # Determine log level and color
            if status == 'error':
                level = "ERROR"
                color = "🔴"
            elif status == 'degraded':
                level = "WARNING"
                color = "🟡"
            else:
                level = "INFO"
                color = "🟢"
            
            # Filter by log level
            if log_level != "All" and level != log_level:
                continue
            
            # Format log entry
            user_text = req.get('user_text', 'N/A')
            latency = req.get('latency_ms', 0)
            channel = req.get('channel', 'unknown')
            
            # Display log entry
            if level == "ERROR":
                st.error(
                    f"{color} **[{timestamp}] {level}** - "
                    f"Trace: {trace_id[:8]}... | "
                    f"Channel: {channel} | "
                    f"Latency: {latency}ms | "
                    f"Error: {req.get('error_message', 'Unknown error')}"
                )
            elif level == "WARNING":
                st.warning(
                    f"{color} **[{timestamp}] {level}** - "
                    f"Trace: {trace_id[:8]}... | "
                    f"Channel: {channel} | "
                    f"Latency: {latency}ms (degraded) | "
                    f"Text: {user_text[:50]}..."
                )
            else:
                st.success(
                    f"{color} **[{timestamp}] {level}** - "
                    f"Trace: {trace_id[:8]}... | "
                    f"Channel: {channel} | "
                    f"Latency: {latency}ms | "
                    f"Text: {user_text[:50]}..."
                )
    
    # Download logs
    st.markdown("---")
    
    if st.button("📥 Download Logs", use_container_width=True):
        # Format logs as text
        log_text = ""
        for req in requests:
            status = req.get('status', 'unknown')
            timestamp = req.get('timestamp', 'N/A')
            trace_id = req.get('trace_id', 'N/A')
            
            if status == 'error':
                level = "ERROR"
            elif status == 'degraded':
                level = "WARNING"
            else:
                level = "INFO"
            
            log_text += f"[{timestamp}] {level} - Trace: {trace_id} - {req.get('user_text', 'N/A')}\n"
        
        st.download_button(
            label="📄 Download as TXT",
            data=log_text,
            file_name=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

else:
    st.warning("⚠️ No logs available")

# Auto-refresh
if auto_refresh:
    import time
    time.sleep(refresh_interval)
    st.rerun()

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
