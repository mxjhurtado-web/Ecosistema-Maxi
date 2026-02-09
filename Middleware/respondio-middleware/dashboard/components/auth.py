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
            from .api_client import api_client
            import os
            
            # Fetch users from API (using default credentials for the call initially)
            try:
                users = api_client.get_users()
            except Exception:
                users = []
            
            # Check if any user matches
            authenticated_user = None
            for user in users:
                if user.get("username") == username and user.get("password") == password:
                    authenticated_user = user
                    break
            
            # Fallback to default admin if no matches and no Redis users
            if not authenticated_user:
                correct_username = st.secrets.get("DASHBOARD_USERNAME") or os.getenv("DASHBOARD_USERNAME", "admin")
                correct_password = st.secrets.get("DASHBOARD_PASSWORD") or os.getenv("DASHBOARD_PASSWORD", "change-me-in-production")
                
                if username == correct_username and password == correct_password:
                    authenticated_user = {
                        "username": username,
                        "password": password,
                        "role": "admin"
                    }
            
            if authenticated_user:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.password = password  # Store temporarily for API calls
                st.session_state.role = authenticated_user.get("role", "admin")
                st.success(f"✅ Logged in as {username} ({st.session_state.role})")
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
