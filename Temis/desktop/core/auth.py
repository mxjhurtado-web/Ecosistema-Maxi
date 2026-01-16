#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Authentication manager for desktop app
Handles Keycloak PKCE flow
"""

import webbrowser
import hashlib
import base64
import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.keycloak_config import (
    AUTH_ENDPOINT,
    TOKEN_ENDPOINT,
    CLIENT_ID,
    CLIENT_SECRET,
    REDIRECT_URI,
    APP_PORT
)


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""

    def do_GET(self):
        """Handle GET request"""
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            self.server.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Autenticacion exitosa!</h1>
                    <p>Puedes cerrar esta ventana y volver a TEMIS.</p>
                    <script>window.close();</script>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress log messages"""
        pass


class AuthManager:
    """Authentication manager"""

    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.user_info = None

    def login(self) -> bool:
        """
        Perform PKCE login flow
        Returns True if successful
        """
        try:
            # Generate code verifier and challenge
            code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
            code_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode('utf-8')).digest()
            ).decode('utf-8').rstrip('=')

            # Build authorization URL
            auth_url = (
                f"{AUTH_ENDPOINT}?"
                f"client_id={CLIENT_ID}&"
                f"redirect_uri={REDIRECT_URI}&"
                f"response_type=code&"
                f"code_challenge={code_challenge}&"
                f"code_challenge_method=S256&"
                f"scope=openid email profile"
            )

            # Start local server for callback
            server = HTTPServer(('localhost', APP_PORT), CallbackHandler)
            server.auth_code = None

            # Open browser
            webbrowser.open(auth_url)

            # Wait for callback with shorter timeout
            server.timeout = 30  # Reduced from 60 to 30 seconds
            
            # Handle the request
            server.handle_request()

            # Immediately shutdown the server after receiving the code
            if server.auth_code:
                # Give browser time to render the success page
                import time
                time.sleep(1)
                # Server will close automatically after this

            if not server.auth_code:
                return False

            # Exchange code for tokens
            token_data = {
                'grant_type': 'authorization_code',
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'code': server.auth_code,
                'redirect_uri': REDIRECT_URI,
                'code_verifier': code_verifier
            }

            response = requests.post(TOKEN_ENDPOINT, data=token_data)

            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens.get('access_token')
                self.refresh_token = tokens.get('refresh_token')

                # Validate token with backend
                return self._validate_with_backend()

            return False

        except Exception as e:
            print(f"Login error: {e}")
            return False

    def _validate_with_backend(self) -> bool:
        """Validate token with backend API"""
        try:
            API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
            response = requests.post(
                f"{API_BASE}/api/auth/validate",
                json={"access_token": self.access_token}
            )

            if response.status_code == 200:
                data = response.json()
                self.user_info = data.get('user')
                return True

            return False

        except Exception as e:
            print(f"Backend validation error: {e}")
            return False

    def logout(self):
        """Logout"""
        self.access_token = None
        self.refresh_token = None
        self.user_info = None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.access_token is not None
