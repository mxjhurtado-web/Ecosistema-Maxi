"""
DevOps MCP Client - Versión Estable
Integración robusta con MaxiBot usando hilos para evitar bloqueos de interfaz.
"""
import os
import asyncio
import concurrent.futures
from typing import List, Any
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from google import genai
from dotenv import load_dotenv

load_dotenv()

class DevOpsMCP:
    """
    Cliente para el servidor MCP de DevOps.
    Usa un ThreadPoolExecutor para ejecutar consultas sin congelar la interfaz de MaxiBot.
    """
    
    def __init__(self, url: str = None, keycloak_token: str = None, gemini_api_key: str = None):
        # URL de producción por defecto
        self.url = url or os.getenv("DEVOPS_MCP_URL", "https://mcp.maxiagentes.net/mcp")
        self.keycloak_token = keycloak_token or os.getenv("KEYCLOAK_TOKEN")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")

    def available(self) -> bool:
        """Verifica configuración mínima."""
        return bool(self.url and self.keycloak_token and self.gemini_api_key)

    async def _run_query_task(self, prompt: str, model: str):
        """Tarea asíncrona interna para la consulta."""
        if not self.available():
            return "Configuración incompleta de DevOps MCP."

        # El cliente de Gemini se crea dentro del hilo para evitar conflictos
        client = genai.Client(api_key=self.gemini_api_key)
        headers = {
            "Authorization": f"Bearer {self.keycloak_token}",
            "X-Forwarded-Proto": "https"
        }

        try:
            async with streamablehttp_client(self.url, headers=headers) as (rs, ws, _):
                async with ClientSession(rs, ws) as session:
                    await session.initialize()
                    
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
            return f"Error en conexión MCP: {str(e)}"

    def query_sync(self, prompt: str, model: str = "gemini-2.5-flash") -> str:
        """
        Versión síncrona que lanza un hilo nuevo para la consulta.
        Esto evita que MaxiBot se 'congele' y recibas el KeyboardInterrupt.
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: asyncio.run(self._run_query_task(prompt, model)))
            try:
                # Tiempo de espera máximo: 60 segundos
                return future.result(timeout=60)
            except concurrent.futures.TimeoutError:
                return "Error: Tiempo de espera agotado (60s)."
            except Exception as e:
                return f"Error en query_sync: {str(e)}"

    async def _run_get_tools_task(self) -> List[str]:
        """Tarea asíncrona interna para listar herramientas."""
        headers = {
            "Authorization": f"Bearer {self.keycloak_token}",
            "X-Forwarded-Proto": "https"
        }
        try:
            async with streamablehttp_client(self.url, headers=headers) as (rs, ws, _):
                async with ClientSession(rs, ws) as session:
                    await session.initialize()
                    tools_response = await session.list_tools()
                    return [tool.name for tool in tools_response.tools]
        except:
            return []

    def get_available_tools_sync(self) -> List[str]:
        """Obtiene herramientas usando un hilo separado."""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: asyncio.run(self._run_get_tools_task()))
            try:
                return future.result(timeout=30)
            except:
                return []

    def close(self):
        """No requiere limpieza manual en esta versión síncrona/hilos."""
        pass

# Instancia global para compatibilidad con MaxiBot
devops_mcp = None

def get_devops_mcp(keycloak_token: str = None, gemini_api_key: str = None) -> DevOpsMCP:
    global devops_mcp
    if devops_mcp is None or keycloak_token or gemini_api_key:
        devops_mcp = DevOpsMCP(keycloak_token=keycloak_token, gemini_api_key=gemini_api_key)
    return devops_mcp
