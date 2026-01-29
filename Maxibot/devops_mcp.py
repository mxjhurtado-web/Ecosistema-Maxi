"""
DevOps MCP Client - Versión Ultra-Robusta
Maneja errores de TaskGroup y asegura conexiones limpias.
"""
import os
import asyncio
import threading
from typing import List, Any
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from google import genai
from dotenv import load_dotenv

load_dotenv()

class DevOpsMCP:
    """
    Cliente para el servidor MCP de DevOps.
    Diseñado para ser invocado desde una interfaz síncrona (Tkinter).
    """
    
    def __init__(self, url: str = None, keycloak_token: str = None, gemini_api_key: str = None):
        self.url = url or os.getenv("DEVOPS_MCP_URL", "https://mcp.maxiagentes.net/mcp")
        self.keycloak_token = keycloak_token or os.getenv("KEYCLOAK_TOKEN")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")

    def available(self) -> bool:
        # El indicador de "Conectado" depende de que tengamos URL y token (y key opcionalmente)
        return bool(self.url and self.keycloak_token)

    async def _query_internal(self, prompt: str, model: str):
        """Lógica asíncrona de consulta con desempaquetado de errores."""
        if not self.available():
            return "Error: Configuración de DevOps MCP incompleta (Falta Token SSO)."

        headers = {
            "Authorization": f"Bearer {self.keycloak_token}",
            "X-Forwarded-Proto": "https"
        }

        # Debug: Mostrar longitud del token
        token_preview = f"{self.keycloak_token[:10]}...{self.keycloak_token[-10:]}" if self.keycloak_token else "None"
        print(f"DEBUG MCP: Consultando {self.url} con token {token_preview}")

        try:
            async with streamablehttp_client(self.url, headers=headers) as (rs, ws, _):
                async with ClientSession(rs, ws) as session:
                    await session.initialize()
                    
                    client = genai.Client(api_key=self.gemini_api_key)
                    response = await client.aio.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=genai.types.GenerateContentConfig(
                            temperature=0,
                            tools=[session],
                        ),
                    )
                    return response.text
        except Exception as e:
            # Desempaquetar errores de ExceptionGroup (TaskGroup) en Python 3.11+
            error_msg = str(e)
            if hasattr(e, 'exceptions') and e.exceptions:
                error_msg = f"{str(e.exceptions[0])}"
            
            if "401" in error_msg or "Unauthorized" in error_msg:
                return "Error: 401 Sesión de SSO expirada. Por favor, reinicia el Bot."
                
            print(f"DEBUG MCP Error Detalle: {error_msg}")
            return f"Error en consulta MCP: {error_msg}"

    def query_sync(self, prompt: str, model: str = "gemini-2.5-flash") -> str:
        """Invoca la consulta en un hilo nuevo para no congelar la UI."""
        result = [None]
        
        def run():
            try:
                # asyncio.run crea un loop fresco y lo cierra al terminar
                result[0] = asyncio.run(self._query_internal(prompt, model))
            except Exception as e:
                result[0] = f"Error crítico en hilo: {str(e)}"
        
        thread = threading.Thread(target=run)
        thread.start()
        thread.join(timeout=70) # Un poco más del timeout de Gemini
        return result[0] or "Error: Tiempo de espera agotado (70s)"

    def get_available_tools_sync(self) -> List[str]:
        """Obtiene herramientas de forma segura."""
        result = [[]]
        async def _get():
            if not self.available(): return []
            headers = {"Authorization": f"Bearer {self.keycloak_token}", "X-Forwarded-Proto": "https"}
            async with streamablehttp_client(self.url, headers=headers) as (rs, ws, _):
                async with ClientSession(rs, ws) as session:
                    await session.initialize()
                    tools_resp = await session.list_tools()
                    return [tool.name for tool in tools_resp.tools]
        
        def run():
            try: result[0] = asyncio.run(_get())
            except: result[0] = []
            
        thread = threading.Thread(target=run)
        thread.start()
        thread.join(timeout=30)
        return result[0]

    def close(self):
        pass

# Instancia global
_devops_instance = None

def get_devops_mcp(keycloak_token: str = None, gemini_api_key: str = None) -> DevOpsMCP:
    """
    Obtiene o crea la instancia global de DevOpsMCP (Singleton).
    Asegura que NO se pierdan los tokens al actualizar.
    """
    global _devops_instance
    if _devops_instance is None:
        _devops_instance = DevOpsMCP(keycloak_token=keycloak_token, gemini_api_key=gemini_api_key)
    else:
        # Actualizar solo si vienen valores nuevos
        if keycloak_token:
            _devops_instance.keycloak_token = keycloak_token
        if gemini_api_key:
            _devops_instance.gemini_api_key = gemini_api_key
            
    return _devops_instance
