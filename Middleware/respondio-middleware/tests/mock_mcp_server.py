"""
Mock MCP Server for Testing
Uses Google News RSS for real responses
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import requests
import xml.etree.ElementTree as ET
import re
from urllib.parse import quote
import uvicorn

app = FastAPI(
    title="Mock MCP Server",
    description="Mock MCP server for testing middleware",
    version="1.0.0"
)


class MCPRequest(BaseModel):
    """Request from middleware"""
    query: str
    context: Optional[dict] = None


class MCPResponse(BaseModel):
    """Response to middleware"""
    response: str
    confidence: float = 0.95


class NewsTool:
    """Cliente para consultas de noticias usando Google News RSS"""
    
    def __init__(self):
        self.base_url = "https://news.google.com/rss"
        self.search_url = "https://news.google.com/rss/search"
    
    def search(self, query: str, top_k: int = 3):
        """
        Busca noticias basadas en el query.
        Compatible con la interfaz MCP de MaxiBot.
        
        Args:
            query: Texto de búsqueda (ej: "noticias de tecnología")
            top_k: Número de resultados
        
        Returns:
            Lista de resultados en formato MCP
        """
        # 1. Detectar intención de noticias
        # Patrones: "noticias de X", "noticias en X", "noticias sobre X", "últimas noticias"
        match = re.search(r"noticias (?:de|en|sobre|del) (.+)", query, re.IGNORECASE)
        topic = match.group(1).strip() if match else None
        
        if not topic and "noticias" not in query.lower():
            return []

        # Si es solo "noticias" o "últimas noticias", usamos top headlines
        try:
            params = {"hl": "es-419", "gl": "MX", "ceid": "MX:es-419"}  # Configurado para México/LatAm
            
            if topic:
                # Búsqueda específica
                url = f"{self.search_url}?q={quote(topic)}"
            else:
                # Top headlines
                url = self.base_url
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return []
                
            # Parsear XML
            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            
            results = []
            count = 0
            
            for item in items:
                if count >= top_k:
                    break
                    
                title = item.find("title").text if item.find("title") is not None else "Sin título"
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                
                # Limpiar título (Google News suele poner " - Fuente" al final)
                source = "Google News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source = parts[1]
                
                snippet = f"Noticia: {title}\nFecha: {pub_date}\nFuente: {source}"
                
                results.append({
                    "title": title,
                    "content": snippet,
                    "url": link,
                    "score": 1.0
                })
                count += 1
            
            return results

        except Exception as e:
            print(f"Error en NewsTool: {e}")
            return [{
                "title": "Error al buscar noticias",
                "content": f"No se pudieron obtener noticias: {str(e)}",
                "url": "https://news.google.com",
                "score": 0.3
            }]

    def available(self) -> bool:
        return True


# Instancia global
news_tool = NewsTool()


@app.post("/query", response_model=MCPResponse)
async def query(request: MCPRequest):
    """
    Main query endpoint - compatible with middleware
    """
    query_text = request.query.lower()
    
    # Check for Gemini API Key in context
    gemini_api_key = request.context.get("gemini_api_key") if request.context else None
    
    # Check if it's a news query
    if "noticias" in query_text or "news" in query_text:
        results = news_tool.search(request.query, top_k=3)
        
        if results:
            # Format response
            response_text = "📰 **Últimas Noticias:**\n\n"
            
            for i, result in enumerate(results, 1):
                response_text += f"{i}. **{result['title']}**\n"
                response_text += f"   {result['content']}\n"
                response_text += f"   🔗 {result['url']}\n\n"
            
            return MCPResponse(
                response=response_text,
                confidence=0.95
            )
    
    # Use Gemini if API Key is provided
    if gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            Eres ORBIT, un asistente de IA inteligente integrado en un sistema de middleware.
            Un usuario te ha preguntado lo siguiente: "{request.query}"
            
            Tu objetivo es dar una respuesta concisa, profesional y útil.
            Estructura tu respuesta usando Markdown para que se vea bien en el dashboard.
            """
            
            response = model.generate_content(prompt)
            return MCPResponse(
                response=response.text,
                confidence=0.99
            )
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            # Fallback to predefined responses
    
    # Default response for specific queries
    responses = {
        "hola": "¡Hola! Soy el asistente ORBIT con integración Gemini. ¿En qué puedo ayudarte?",
        "como estas": "¡Estoy funcionando perfectamente! Listo para procesar tus consultas.",
        "ayuda": "Puedo ayudarte con:\n- Noticias actualizadas\n- Consultas generales usando Gemini\n- Configuración del sistema\n\nEjemplos:\n- 'noticias de tecnología'\n- '¿Cómo funciona un middleware?'",
    }
    
    # Find matching response
    for key, value in responses.items():
        if key in query_text:
            return MCPResponse(response=value, confidence=0.9)
    
    # Default fallback
    return MCPResponse(
        response=f"He recibido tu mensaje: '{request.query}'. Por favor, configura una Gemini API Key en la sección de Configuración para tener respuestas más completas.",
        confidence=0.7
    )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mock-mcp",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Mock MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "POST /query",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    print("🚀 Starting Mock MCP Server on http://localhost:8080")
    print("📰 News functionality enabled via Google News RSS")
    print("---")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
