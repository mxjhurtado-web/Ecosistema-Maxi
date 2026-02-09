import streamlit as st
import requests
import jwt
from urllib.parse import urlencode
import os

class AuthManager:
    def __init__(self, settings):
        self.settings = settings
        self.auth_endpoint = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/auth"
        self.token_endpoint = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
        self.userinfo_endpoint = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
        self.logout_endpoint = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout"

    def get_auth_url(self, redirect_uri):
        params = {
            "client_id": self.settings.KEYCLOAK_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
        }
        return f"{self.auth_endpoint}?{urlencode(params)}"

    def exchange_code_for_token(self, code, redirect_uri):
        data = {
            "grant_type": "authorization_code",
            "client_id": self.settings.KEYCLOAK_CLIENT_ID,
            "client_secret": self.settings.KEYCLOAK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
        }
        response = requests.post(self.token_endpoint, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error exchange code: {response.text}")
            return None

    def get_user_info(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.userinfo_endpoint, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None

    def check_auth(self):
        # 1. Check session state
        if st.session_state.get("authenticated"):
            return True

        # 2. Check query params for code (callback)
        query_params = st.query_params
        if "code" in query_params:
            # We are in the callback
            code = query_params["code"]
            # Important: the redirect_uri must match EXACTLY what was sent in get_auth_url
            # In Streamlit Cloud, we can use the current URL without query params
            redirect_uri = st.session_state.get("redirect_uri")
            
            tokens = self.exchange_code_for_token(code, redirect_uri)
            if tokens:
                st.session_state.authenticated = True
                st.session_state.access_token = tokens["access_token"]
                st.session_state.refresh_token = tokens.get("refresh_token")
                st.session_state.user_info = self.get_user_info(tokens["access_token"])
                
                # Clear query params to clean URL
                st.query_params.clear()
                st.rerun()
            return False

        # 3. Show login button if not authenticated
        self.show_login_page()
        return False

    def show_login_page(self):
        st.markdown("""
            <div style="text-align: center; padding: 50px;">
                <h1>🦅 Hades Web</h1>
                <p>Análisis Forense de Identidad - Trusted by Ecosistema Maxi</p>
            </div>
        """, unsafe_allow_html=True)
        
        # En Streamlit Cloud, la URL base puede variar. 
        # Es mejor guardarla en session state antes de redirigir.
        redirect_uri = st.secrets.get("REDIRECT_URI") or "http://localhost:8501"
        st.session_state.redirect_uri = redirect_uri
        
        auth_url = self.get_auth_url(redirect_uri)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.link_button("🔑 Iniciar Sesión con Keycloak", auth_url, use_container_width=True)
            st.info("Serás redirigido al servidor de autenticación corporativo.")

    def logout(self):
        for key in ["authenticated", "access_token", "refresh_token", "user_info"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
