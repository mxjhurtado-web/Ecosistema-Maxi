"""
👥 User Management Page
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
from components.page_setup import setup_page
from api.models import UserRole, DashboardUser

# Setup page with ORBIT theme
setup_page("User Management", "👥")

# Require authentication and Admin role
require_auth()

if st.session_state.get("role") != "admin":
    st.error("🚫 Access Denied: Only Administrators can access this page.")
    st.stop()

st.title("👥 User Management")
st.markdown("Manage system administrators and supervisors. Limits: Max 3 per role.")

# ============================================================
# User List
# ============================================================

st.subheader("Current Users")

users = api_client.get_dashboard_users()

if users:
    # Convert to list of dicts for Table
    user_data = []
    for u in users:
        user_data.append({
            "Username": u.get("username"),
            "Role": u.get("role").upper(),
            "Actions": "Delete"
        })
    
    # Display table
    for i, u in enumerate(users):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{u.get('username')}**")
        with col2:
            role_color = "🔵" if u.get('role') == 'admin' else "🟢"
            st.write(f"{role_color} {u.get('role').upper()}")
        with col3:
            # Don't allow deleting yourself
            if u.get('username') == st.session_state.get('username'):
                st.caption("(You)")
            else:
                if st.button("🗑️", key=f"del_{u.get('username')}"):
                    if api_client.delete_user(u.get('username')):
                        st.success(f"User {u.get('username')} deleted")
                        st.rerun()
                    else:
                        st.error("Failed to delete user")
        st.divider()
else:
    st.info("No users found (except the default environment admin)")

# ============================================================
# Add New User
# ============================================================

st.subheader("➕ Add New User")

with st.form("add_user_form", clear_on_submit=True):
    new_username = st.text_input("Username", placeholder="e.g. jdoe")
    new_password = st.text_input("Password", type="password")
    new_role = st.selectbox("Role", ["admin", "supervisor"])
    
    submit = st.form_submit_button("🚀 Create User", use_container_width=True)
    
    if submit:
        if not new_username or not new_password:
            st.error("Please provide both username and password")
        else:
            new_user = {
                "username": new_username,
                "password": new_password,
                "role": new_role
            }
            
            with st.spinner("Creating user..."):
                success = api_client.add_user(new_user)
            
            if success:
                st.success(f"✅ User {new_username} created successfully!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Failed to create user. Check limits (Max 3 per role) or if user exists.")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
