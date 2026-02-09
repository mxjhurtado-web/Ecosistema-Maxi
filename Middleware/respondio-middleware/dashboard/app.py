"""
Main Streamlit Dashboard Application
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="ORBIT - Integration Middleware",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    """Load custom CSS for ORBIT theme"""
    css_file = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_file):
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Additional inline styles
    st.markdown("""
    <style>
        /* ORBIT specific overrides */
        .stApp {
            background: linear-gradient(135deg, #0F1117 0%, #1A1D29 100%);
        }
        
        /* Logo container */
        .logo-container {
            text-align: center;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        /* Main title styling */
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, #00D9FF 0%, #0066FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            padding: 10px 0;
        }
        
        /* Subtitle */
        .subtitle {
            color: #00D9FF;
            font-size: 1.1rem;
            margin-top: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

    # RBAC: Hide pages from sidebar for non-admins
    if st.session_state.get("authenticated") and st.session_state.get("role") == "supervisor":
        st.markdown("""
        <style>
            /* Hide Logs, Config, Maintenance, Chat from sidebar */
            div[data-testid="stSidebarNav"] li:nth-child(3), /* Logs */
            div[data-testid="stSidebarNav"] li:nth-child(4), /* Config */
            div[data-testid="stSidebarNav"] li:nth-child(5), /* Maintenance */
            div[data-testid="stSidebarNav"] li:nth-child(6)  /* Chat */
            {
                display: none !important;
            }
        </style>
        """, unsafe_allow_html=True)

load_css()

# Import auth
from components.auth import require_auth, logout, check_authentication

# Require authentication
require_auth()

# Sidebar
with st.sidebar:
    st.title("🎛️ Middleware Dashboard")
    st.markdown("---")
    
    # User info
    if check_authentication():
        st.success(f"👤 {st.session_state.get('username', 'User')}")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    # Navigation info
    st.markdown("### 📑 Pages")
    
    role = st.session_state.get('role', 'admin')
    if role == 'admin':
        st.markdown("""
        - **📊 KPIs & Analytics** - Metrics and trends
        - **📜 History** - Request history
        - **🔍 Logs** - Live logs viewer
        - **⚙️ Configuration** - System config
        - **🔧 Maintenance** - Admin tools
        - **💬 Chat** - Test MCP
        """)
    else:
        st.markdown("""
        - **📊 KPIs & Analytics** - Basic Metrics
        - **📜 History** - Request History
        """)
    
    st.markdown("---")
    
    # Status
    from components.api_client import api_client
    health = api_client.get_health()
    
    if health:
        redis_status = health.get("redis_status", "unknown")
        if redis_status == "healthy":
            st.success("✅ Redis: Connected")
        else:
            st.warning("⚠️ Redis: Disabled")
    else:
        st.error("❌ Cannot connect to API")

# Main content
st.markdown('<div class="logo-container">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    # Display logo if available
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "orbit_logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=400)
    else:
        st.markdown('<h1 class="main-title">🪐 ORBIT</h1>', unsafe_allow_html=True)
    
    st.markdown('<p class="subtitle">Integration Middleware - Production Dashboard</p>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown("---")

st.markdown("""
## Welcome to the Middleware Dashboard

This dashboard provides comprehensive monitoring and management for the Respond.io to MCP middleware.

### 📊 Features

- **Real-time Metrics** - Monitor requests, latency, and success rates
- **Request History** - View and search past requests
- **Live Logs** - Real-time log streaming
- **Configuration** - Update MCP, cache, and security settings
- **Maintenance Tools** - Health checks, testing, and system info

### 🚀 Quick Start

1. Check the **KPIs & Analytics** page for system overview
2. Use **Configuration** to update MCP settings
3. Monitor **Logs** for real-time activity
4. Use **Maintenance** tools for testing and diagnostics

### 📝 Navigation

Use the sidebar to navigate between pages.

---

**Version:** 1.0.0  
**Status:** Running
""")

# Quick stats
st.markdown("### 📈 Quick Stats (Last 24h)")

from components.api_client import api_client

summary = api_client.get_summary()

if summary:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Requests",
            f"{summary.get('total_requests', 0):,}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Success Rate",
            f"{summary.get('success_rate', 0):.1f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            "Avg Latency",
            f"{summary.get('avg_latency_ms', 0)} ms",
            delta=None
        )
    
    with col4:
        st.metric(
            "Errors",
            f"{summary.get('error_count', 0):,}",
            delta=None
        )
else:
    st.warning("⚠️ Unable to fetch summary statistics")

st.markdown("---")
st.caption("Select a page from the sidebar to get started →")
