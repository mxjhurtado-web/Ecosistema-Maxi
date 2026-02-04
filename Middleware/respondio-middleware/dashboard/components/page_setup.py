"""
Common page setup for all dashboard pages
"""

import streamlit as st
import os


def setup_page(title, icon="🪐"):
    """
    Setup common page configuration and styling for all dashboard pages
    
    Args:
        title: Page title
        icon: Page icon (emoji)
    """
    # Page config
    st.set_page_config(
        page_title=f"ORBIT - {title}",
        page_icon=icon,
        layout="wide"
    )
    
    # Load custom CSS
    css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "style.css")
    if os.path.exists(css_file):
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Additional inline styles
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0F1117 0%, #1A1D29 100%);
        }
        
        .page-header {
            background: linear-gradient(90deg, #00D9FF 0%, #0066FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Page header
    st.markdown(f'<h1 class="page-header">{icon} {title}</h1>', unsafe_allow_html=True)
    st.markdown("---")


def create_metric_card(label, value, delta=None):
    """Create a styled metric card"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1A1D29 0%, #0F1117 100%);
        border: 1px solid #00D9FF;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 217, 255, 0.1);
    ">
        <p style="color: #00D9FF; margin: 0; font-size: 0.9rem; font-weight: 600;">{label}</p>
        <h2 style="color: #FFFFFF; margin: 10px 0; font-size: 2rem; font-weight: 700;">{value}</h2>
        {f'<p style="color: #00FF88; margin: 0; font-size: 0.9rem;">{delta}</p>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)


def create_status_badge(status):
    """Create a styled status badge"""
    colors = {
        "ok": "#00FF88",
        "healthy": "#00FF88",
        "success": "#00FF88",
        "degraded": "#FFB800",
        "warning": "#FFB800",
        "error": "#FF4444",
        "unhealthy": "#FF4444",
        "failed": "#FF4444"
    }
    
    color = colors.get(status.lower(), "#888")
    
    return f'<span style="color: {color}; font-weight: 600;">● {status.upper()}</span>'
