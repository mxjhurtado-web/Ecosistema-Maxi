"""
Utility functions for dashboard styling
"""

import streamlit as st


def apply_orbit_theme():
    """Apply ORBIT custom theme styles"""
    st.markdown("""
    <style>
        /* Metric card styling */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #1A1D29 0%, #0F1117 100%);
            border: 1px solid #00D9FF;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 217, 255, 0.1);
        }
        
        /* Chart container */
        .chart-container {
            background: #1A1D29;
            border: 1px solid #00D9FF;
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)


def create_metric_card(label, value, delta=None, help_text=None):
    """Create a styled metric card"""
    st.markdown(f"""
    <div class="orbit-card">
        <h4 style="color: #00D9FF; margin: 0;">{label}</h4>
        <h2 style="color: #FFFFFF; margin: 10px 0;">{value}</h2>
        {f'<p style="color: #00FF88; margin: 0;">{delta}</p>' if delta else ''}
        {f'<p style="color: #888; font-size: 0.9rem; margin-top: 5px;">{help_text}</p>' if help_text else ''}
    </div>
    """, unsafe_allow_html=True)


def create_status_badge(status):
    """Create a styled status badge"""
    colors = {
        "ok": "#00FF88",
        "healthy": "#00FF88",
        "degraded": "#FFB800",
        "error": "#FF4444",
        "unhealthy": "#FF4444"
    }
    
    color = colors.get(status.lower(), "#888")
    
    return f'<span style="color: {color}; font-weight: 600;">● {status.upper()}</span>'


def create_section_header(title, icon=""):
    """Create a styled section header"""
    st.markdown(f"""
    <h2 class="gradient-text">{icon} {title}</h2>
    """, unsafe_allow_html=True)


def create_info_box(title, content, type="info"):
    """Create a styled info box"""
    colors = {
        "info": "#00D9FF",
        "success": "#00FF88",
        "warning": "#FFB800",
        "error": "#FF4444"
    }
    
    color = colors.get(type, "#00D9FF")
    
    st.markdown(f"""
    <div style="
        background: #1A1D29;
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    ">
        <h4 style="color: {color}; margin: 0 0 10px 0;">{title}</h4>
        <p style="color: #FFFFFF; margin: 0;">{content}</p>
    </div>
    """, unsafe_allow_html=True)
