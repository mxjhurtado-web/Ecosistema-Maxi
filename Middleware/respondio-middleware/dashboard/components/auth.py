"""
Authentication component for Streamlit dashboard.
"""

import streamlit as st
from typing import Optional


def check_authentication() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)


def login_form():
    """Display login form"""
    st.title("🔐 Respond.io Middleware Dashboard")
    st.markdown("---")
    
    with st.form("login_form"):
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            # Get credentials from environment or use defaults
            import os
            correct_username = os.getenv("DASHBOARD_USERNAME", "admin")
            correct_password = os.getenv("DASHBOARD_PASSWORD", "change-me-in-production")
            
            if username == correct_username and password == correct_password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Invalid credentials")


def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()


def require_auth():
    """Decorator to require authentication"""
    if not check_authentication():
        login_form()
        st.stop()
