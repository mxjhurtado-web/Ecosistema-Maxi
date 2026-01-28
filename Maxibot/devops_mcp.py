"""
DevOps MCP Client
Integrates with MaxiLabs DevOps MCP server using streamable HTTP and Keycloak authentication
"""
import os
import asyncio
from typing import Optional, Dict, List, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client
from google import genai
from dotenv import load_dotenv

load_dotenv()

class DevOpsMCP:
    """
    Cliente para el servidor MCP de DevOps.
    Usa streamable HTTP con autenticación Keycloak.
    """
    
    def __init__(self, url: str = None, keycloak_token: str = None, gemini_api_key: str = None):
        """
        Inicializa el cliente DevOps MCP.
        
        Args:
            url: URL del servidor MCP (default: https://mcp.maxiagentes.net/mcp)
            keycloak_token: Token de Keycloak para autenticación
            gemini_api_key: API Key de Gemini para consultas
        """
        self.url = url or os.getenv("DEVOPS_MCP_URL", "https://mcp.maxiagentes.net/mcp")
        self.keycloak_token = keycloak_token or os.getenv("KEYCLOAK_TOKEN")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        # Inicializar cliente de Gemini con API key
        if self.gemini_api_key:
            self.gemini_client = genai.Client(api_key=self.gemini_api_key)
        else:
            self.gemini_client = None
        
        self._session = None
        self._tools = []
    
    def available(self) -> bool:
        """Verifica si el MCP está disponible (tiene token, URL y API key de Gemini)."""
        return bool(self.url and self.keycloak_token and self.gemini_client)
    
    async def _initialize_session(self):
        """Inicializa la sesión MCP si no está activa."""
        if self._session is not None:
            return
        
        if not self.gemini_client:
            raise RuntimeError("Gemini API key no configurada")
        
        headers = {
            "Authorization": f"Bearer {self.keycloak_token}",
            "X-Forwarded-Proto": "https"
        }
        
        # Crear contexto de cliente streamable
        self._client_context = streamablehttp_client(self.url, headers=headers)
        self._rs, self._ws, _ = await self._client_context.__aenter__()
        
        # Crear sesión
        self._session_context = ClientSession(self._rs, self._ws)
        self._session = await self._session_context.__aenter__()
        
        # Inicializar conexión
        await self._session.initialize()
        
        # Obtener herramientas disponibles
        tools_response = await self._session.list_tools()
        self._tools = tools_response.tools
    
    async def _cleanup_session(self):
        """Limpia la sesión MCP."""
        if self._session is not None:
            try:
                await self._session_context.__aexit__(None, None, None)
                await self._client_context.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error al cerrar sesión MCP: {e}")
            finally:
                self._session = None
                self._tools = []
    
    async def query(self, prompt: str, model: str = "gemini-2.5-flash") -> str:
        """
        Realiza una consulta al MCP usando Gemini.
        
        Args:
            prompt: Pregunta o comando para el MCP
            model: Modelo de Gemini a usar (default: gemini-2.5-flash)
            
        Returns:
            Respuesta del modelo con los resultados del MCP
        """
        if not self.available():
            return "DevOps MCP no está disponible. Verifica el token de Keycloak y la API key de Gemini."
        
        try:
            # Inicializar sesión
            await self._initialize_session()
            
            # Enviar request a Gemini con las herramientas MCP
            response = await self.gemini_client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0,
                    tools=[self._session],  # Usa la sesión MCP como herramienta
                ),
            )
            
            return response.text
            
        except Exception as e:
            return f"Error al consultar DevOps MCP: {str(e)}"
        finally:
            # Limpiar sesión
            await self._cleanup_session()
    
    def query_sync(self, prompt: str, model: str = "gemini-2.5-flash") -> str:
        """
        Versión síncrona de query() para usar en código no-async.
        
        Args:
            prompt: Pregunta o comando para el MCP
            model: Modelo de Gemini a usar (default: gemini-2.5-flash)
            
        Returns:
            Respuesta del modelo con los resultados del MCP
        """
        try:
            # Crear nuevo event loop si no existe
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Ejecutar query async
            return loop.run_until_complete(self.query(prompt, model))
        except Exception as e:
            return f"Error en query_sync: {str(e)}"
    
    async def get_available_tools(self) -> List[str]:
        """
        Obtiene la lista de herramientas disponibles en el MCP.
        
        Returns:
            Lista de nombres de herramientas
        """
        if not self.available():
            return []
        
        try:
            await self._initialize_session()
            return [tool.name for tool in self._tools]
        except Exception as e:
            print(f"Error al obtener herramientas: {e}")
            return []
        finally:
            await self._cleanup_session()
    
    def get_available_tools_sync(self) -> List[str]:
        """Versión síncrona de get_available_tools()."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.get_available_tools())


# Instancia global
devops_mcp = None

def get_devops_mcp(keycloak_token: str = None, gemini_api_key: str = None) -> DevOpsMCP:
    """
    Obtiene o crea la instancia global de DevOpsMCP.
    
    Args:
        keycloak_token: Token de Keycloak (opcional si está en .env)
        gemini_api_key: API Key de Gemini (opcional si está en .env)
        
    Returns:
        Instancia de DevOpsMCP
    """
    global devops_mcp
    if devops_mcp is None or keycloak_token or gemini_api_key:
        devops_mcp = DevOpsMCP(keycloak_token=keycloak_token, gemini_api_key=gemini_api_key)
    return devops_mcp


# Ejemplo de uso
if __name__ == "__main__":
    async def test():
        mcp = DevOpsMCP()
        
        if not mcp.available():
            print("⚠️ DevOps MCP no disponible. Configura KEYCLOAK_TOKEN en .env")
            return
        
        # Obtener herramientas disponibles
        tools = await mcp.get_available_tools()
        print(f"Herramientas disponibles: {tools}")
        
        # Hacer una consulta
        prompt = "Dame el status de la agencia NM-238, y si está deshabilitada, explicar el motivo"
        response = await mcp.query(prompt)
        print(f"\nRespuesta:\n{response}")
    
    asyncio.run(test())

