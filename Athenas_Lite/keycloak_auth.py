#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de autenticación con Keycloak para ATHENAS Lite
Implementa SSO con OAuth 2.0 / OpenID Connect
"""

import requests
import webbrowser
import threading
import time
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Optional, Tuple
import keycloak_config as kc_config


class KeycloakAuth:
    """Clase para manejar autenticación SSO con Keycloak"""

    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.user_info = None
        self.callback_server = None
        self.auth_code = None

    def get_auth_url(self) -> str:
        """Genera la URL de autenticación de Keycloak"""
        params = {
            'client_id': kc_config.CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': kc_config.REDIRECT_URI,
            'scope': 'openid profile email',
            'state': 'athenas_auth'
        }

        auth_url = f"{kc_config.AUTH_ENDPOINT}?{urlencode(params)}"
        return auth_url

    def start_callback_server(self) -> None:
        """Inicia servidor local para capturar el callback de SSO"""

        class CallbackHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                """Suprimir logs del servidor HTTP"""
                pass

            def do_GET(self):
                if self.path.startswith('/callback'):
                    # Parsear query parameters
                    parsed_url = urlparse(self.path)
                    query_params = parse_qs(parsed_url.query)

                    if 'code' in query_params:
                        self.server.auth_code = query_params['code'][0]
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        html_content = '''
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <title>ATHENAS - Autenticación Exitosa</title>
                            <style>
                                body {
                                    font-family: Arial, sans-serif;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    height: 100vh;
                                    margin: 0;
                                    background: linear-gradient(135deg, #e91e63 0%, #c2185b 100%);
                                }
                                .container {
                                    background: white;
                                    padding: 40px;
                                    border-radius: 10px;
                                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                    text-align: center;
                                }
                                h2 { color: #e91e63; margin-bottom: 10px; }
                                p { color: #666; }
                                .success-icon { font-size: 48px; margin-bottom: 20px; }
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="success-icon">✓</div>
                                <h2>¡Autenticación exitosa!</h2>
                                <p>Puedes cerrar esta ventana y volver a ATHENAS Lite.</p>
                            </div>
                            <script>setTimeout(() => window.close(), 3000);</script>
                        </body>
                        </html>
                        '''
                        self.wfile.write(html_content.encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        error_html = '''
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <title>ATHENAS - Error</title>
                            <style>
                                body {
                                    font-family: Arial, sans-serif;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    height: 100vh;
                                    margin: 0;
                                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                                }
                                .container {
                                    background: white;
                                    padding: 40px;
                                    border-radius: 10px;
                                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                    text-align: center;
                                }
                                h2 { color: #f5576c; }
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <h2>Error en autenticación</h2>
                                <p>Por favor, intenta nuevamente.</p>
                            </div>
                        </body>
                        </html>
                        '''
                        self.wfile.write(error_html.encode('utf-8'))
                else:
                    self.send_response(404)
                    self.end_headers()

        # Crear servidor
        self.callback_server = HTTPServer(
            (kc_config.APP_HOST, kc_config.APP_PORT), CallbackHandler)
        self.callback_server.auth_code = None

        # Ejecutar servidor en thread separado
        server_thread = threading.Thread(
            target=self.callback_server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def stop_callback_server(self) -> None:
        """Detiene el servidor de callback"""
        if self.callback_server:
            self.callback_server.shutdown()
            self.callback_server.server_close()

    def exchange_code_for_tokens(self, code: str) -> Tuple[bool, Dict]:
        """Intercambia código de autorización por tokens de acceso"""
        try:
            data = {
                'grant_type': 'authorization_code',
                'client_id': kc_config.CLIENT_ID,
                'client_secret': kc_config.CLIENT_SECRET,
                'code': code,
                'redirect_uri': kc_config.REDIRECT_URI
            }

            response = requests.post(
                kc_config.TOKEN_ENDPOINT, data=data, timeout=30)

            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens.get('access_token')
                self.refresh_token = tokens.get('refresh_token')
                return True, tokens
            else:
                return False, {
                    "error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return False, {"error": str(e)}

    def get_user_info(self) -> Tuple[bool, Dict]:
        """Obtiene información del usuario desde Keycloak"""
        if not self.access_token:
            return False, {"error": "No hay token de acceso"}

        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                kc_config.USERINFO_ENDPOINT, headers=headers, timeout=30)

            if response.status_code == 200:
                user_info = response.json()
                self.user_info = user_info
                return True, user_info
            else:
                return False, {
                    "error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return False, {"error": str(e)}

    def verify_user_roles(self) -> bool:
        """Verifica si el usuario tiene roles válidos para ATHENAS"""
        if not self.user_info:
            return False

        # Si no hay roles requeridos, permitir acceso a todos los usuarios autenticados
        if not kc_config.REQUIRED_ROLES:
            return True

        # Verificar roles en el token
        try:
            import jwt
            decoded = jwt.decode(
                self.access_token, options={"verify_signature": False})
            roles = decoded.get('realm_access', {}).get('roles', [])

            # Verificar si tiene roles requeridos
            return any(role in kc_config.REQUIRED_ROLES for role in roles)
        except Exception:
            # Fallback: permitir acceso si hay user_info válido
            return True

    def authenticate(self) -> Tuple[bool, str]:
        """
        Flujo completo de autenticación SSO
        1. Inicia servidor de callback local
        2. Redirige al navegador a Keycloak
        3. Espera el callback con el código de autorización
        4. Intercambia el código por tokens
        5. Obtiene información del usuario
        6. Verifica roles
        """
        try:
            # 1. Iniciar servidor de callback
            print("Iniciando servidor de callback...")
            self.start_callback_server()

            # 2. Abrir navegador para autenticación
            auth_url = self.get_auth_url()
            print(f"Abriendo navegador para autenticación...")
            webbrowser.open(auth_url)

            # 3. Esperar callback (máximo 5 minutos)
            timeout = 300  # 5 minutos
            start_time = time.time()

            print("Esperando autenticación en Keycloak...")
            while time.time() - start_time < timeout:
                if (hasattr(self.callback_server, 'auth_code') and
                        self.callback_server.auth_code):
                    code = self.callback_server.auth_code
                    break
                time.sleep(1)
            else:
                self.stop_callback_server()
                return False, "Timeout: No se recibió el código de autorización"

            # 4. Intercambiar código por tokens
            print("Intercambiando código por tokens...")
            success, result = self.exchange_code_for_tokens(code)
            if not success:
                self.stop_callback_server()
                return False, f"Error obteniendo tokens: {result.get('error', 'Desconocido')}"

            # 5. Obtener información del usuario
            print("Obteniendo información del usuario...")
            success, user_info = self.get_user_info()
            if not success:
                self.stop_callback_server()
                return False, f"Error obteniendo información del usuario: {user_info.get('error', 'Desconocido')}"

            # 6. Verificar roles
            print("Verificando permisos...")
            if not self.verify_user_roles():
                self.stop_callback_server()
                print("❌ Usuario no tiene permisos")
                return False, "Usuario no tiene permisos para acceder a ATHENAS"

            # 7. Limpiar servidor
            print("✅ Verificación de permisos exitosa")
            self.stop_callback_server()
            print("✅ Servidor de callback detenido")

            email = self.get_user_email()
            print(f"✅ Autenticación exitosa: {email}")
            return True, "Autenticación exitosa"

        except Exception as e:
            self.stop_callback_server()
            return False, f"Error en autenticación: {str(e)}"

    def is_authenticated(self) -> bool:
        """Verifica si el usuario está autenticado"""
        return self.access_token is not None and self.user_info is not None

    def get_user_email(self) -> Optional[str]:
        """Obtiene el email del usuario autenticado"""
        return self.user_info.get('email') if self.user_info else None

    def get_user_name(self) -> Optional[str]:
        """Obtiene el nombre del usuario autenticado"""
        if self.user_info:
            return (self.user_info.get('name') or
                    self.user_info.get('preferred_username') or
                    self.user_info.get('email', '').split('@')[0])
        return None
