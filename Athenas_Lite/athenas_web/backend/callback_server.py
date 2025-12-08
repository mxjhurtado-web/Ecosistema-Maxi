"""
OAuth callback server on port 8080 (like MaxiBot)
Captures the authorization code and redirects to frontend with session
"""
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.keycloak import keycloak_service
from services.storage import storage_service

# Create separate FastAPI app for callback server
callback_app = FastAPI()

@callback_app.get("/callback")
async def oauth_callback(code: str, state: str = None):
    """
    Handle OAuth callback from Keycloak (like MaxiBot)
    This runs on port 8080 to match the redirect URI already configured in Keycloak
    """
    try:
        # Exchange code for tokens
        success, result = keycloak_service.exchange_code_for_tokens(code)
        
        if not success:
            return HTMLResponse(content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>ATHENAS Lite - Error</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }}
                        .container {{
                            background: white;
                            padding: 40px;
                            border-radius: 10px;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            text-align: center;
                        }}
                        h2 {{ color: #e91e63; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Error en autenticación</h2>
                        <p>{result.get('error', 'Error desconocido')}</p>
                        <p><a href="http://localhost:3000">Volver a intentar</a></p>
                    </div>
                </body>
                </html>
            """, status_code=400)
        
        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token")
        
        # Get user info
        success, user_data = keycloak_service.get_user_info(access_token)
        
        if not success:
            return HTMLResponse(content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>ATHENAS Lite - Error</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }
                        .container {
                            background: white;
                            padding: 40px;
                            border-radius: 10px;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            text-align: center;
                        }
                        h2 { color: #e91e63; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Error obteniendo información del usuario</h2>
                        <p><a href="http://localhost:3000">Volver a intentar</a></p>
                    </div>
                </body>
                </html>
            """, status_code=400)
        
        email = user_data.get("email")
        keycloak_id = user_data.get("sub")
        name = user_data.get("name", user_data.get("preferred_username", ""))
        
        # Sync user and get role from internal DB
        user_id, role = await storage_service.sync_user(email, keycloak_id, name)
        
        # Create redirect response to frontend
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # Redirect based on role
        if role == 'admin':
            redirect_url = f"{frontend_url}/admin"
        else:
            redirect_url = f"{frontend_url}/dashboard"
        
        # Create response with cookies
        response = RedirectResponse(url=redirect_url)
        
        # Set httpOnly cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=3600,  # 1 hour
            domain="localhost"  # Important for cross-port cookies
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=86400,  # 24 hours
            domain="localhost"
        )
        
        # Also set user info cookie for frontend
        import json
        user_info_json = json.dumps({"email": email, "name": name, "role": role})
        response.set_cookie(
            key="user_info",
            value=user_info_json,
            httponly=False,  # Frontend needs to read this
            secure=False,
            samesite="lax",
            max_age=3600,
            domain="localhost"
        )
        
        return response
        
    except Exception as e:
        return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>ATHENAS Lite - Error</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        text-align: center;
                    }}
                    h2 {{ color: #e91e63; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Error inesperado</h2>
                    <p>{str(e)}</p>
                    <p><a href="http://localhost:3000">Volver a intentar</a></p>
                </div>
            </body>
            </html>
        """, status_code=500)

if __name__ == "__main__":
    import uvicorn
    print("🔐 Starting OAuth callback server on port 8080...")
    print("📍 Callback URL: http://localhost:8080/callback")
    uvicorn.run(callback_app, host="0.0.0.0", port=8080)
