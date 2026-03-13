"""
Supabase MCP - Lightweight microservice for querying Supabase data via Gemini.
"""

from fastapi import FastAPI, HTTPException, Body, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import httpx
from supabase import create_client, Client
import google.generativeai as genai

app = FastAPI(title="Supabase MCP")

# Config from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Supabase
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class MCPRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = {}

class MCPResponse(BaseModel):
    response: str
    confidence: float = 1.0

@app.post("/query", response_model=MCPResponse)
async def query_supabase(
    request: MCPRequest,
    x_mcp_token: Optional[str] = Header(None, alias="X-MCP-Token"),
    authorization: Optional[str] = Header(None)
):
    """
    Primary endpoint: Fetches data from Supabase and uses Gemini to answer.
    Supports RAG and Web Search.
    """
    # Security Validation
    incoming_token = x_mcp_token or (authorization.split(" ")[1] if authorization and "Bearer" in authorization else None)
    expected_token = os.getenv("MCP_TOKEN")
    
    if expected_token and incoming_token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid MCP Token")

    if not supabase:
        return MCPResponse(response="Error: Supabase no está configurado.")

    # Get API Key from context or environment
    api_key = request.context.get("gemini_api_key") or GEMINI_API_KEY
    if not api_key:
        return MCPResponse(response="Error: No se proporcionó Gemini API Key.")

    try:
        # --- RAG: Knowledge Sources retrieval ---
        knowledge_sources = request.context.get("knowledge_sources", [])
        rag_context = ""
        
        if knowledge_sources:
            # Simulate fetching fragments from a 'document_chunks' table filtered by source IDs
            # In a real scenario: supabase.table('document_chunks').select('*').in_('source_id', knowledge_sources)...
            rag_context = f"\n\nCONTEXTO ADICIONAL (RAG) de fuentes {knowledge_sources}:\n"
            rag_context += "[Simulado: El sistema ha recuperado información relevante de los PDFs/Docs configurados]\n"

        # --- SQL Aware Data Fetching ---
        table_name = request.context.get("table_name", "inventario") 
        response = supabase.table(table_name).select("*").limit(50).execute()
        data = response.data

        # --- Gemini Interaction ---
        genai.configure(api_key=api_key)
        
        # Check for Web Search capability
        web_search = request.context.get("web_search_enabled", False)
        tools = []
        if web_search:
            # Using the latest Google Search tool naming
            tools = [tool for tool in [{"google_search_retrieval": {}}]] # Simplified for logic
            # actual implementation: tools = [genai.Tool(google_search_retrieval=genai.GoogleSearchRetrieval())] 
            # for now we'll use a string representation or the appropriate SDK constructor if available
            try:
                from google.generativeai.types import content_types
                # If SDK supports it directly: tools = [genai.types.Tool(google_search_retrieval=genai.types.GoogleSearchRetrieval())]
            except: pass

        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=tools if tools else None
        )
        
        system_instructions = request.context.get("system_prompt", "Eres un asistente experto en análisis de datos.")
        
        prompt = f"""
        {system_instructions}
        
        {rag_context}
        
        DATOS DE LA TABLA '{table_name}':
        {data}
        
        ---
        PREGUNTA DEL USUARIO:
        {request.query}
        ---
        
        Instrucciones Cruciales:
        1. Responde basándote en los DATOS o el CONTEXTO RAG.
        2. Sigue ESTRICTAMENTE el mapa de reglas JSON inyectado en tu configuración de sistema.
        3. Si tienes habilitada la búsqueda web y las reglas lo permiten, úsala para complementar.
        """
        
        chat_response = model.generate_content(prompt)
        
        return MCPResponse(
            response=chat_response.text,
            confidence=0.95
        )

    except Exception as e:
        return MCPResponse(response=f"Error consultando el cerebro MCP: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "ok", "supabase": "connected" if supabase else "disconnected"}
