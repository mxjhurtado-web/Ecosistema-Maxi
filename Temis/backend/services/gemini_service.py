#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gemini service for TEMIS
Processes daily logs and extracts structured data
"""

import requests
import json
from typing import Dict, Any, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import GEMINI_MODEL, GEMINI_API_BASE


# Prompt maestro para Gemini
GEMINI_PROMPT_TEMPLATE = """Analiza el siguiente Documento Diario de un proyecto y extrae la información estructurada.

DOCUMENTO DIARIO:
```
{daily_log_content}
```

INSTRUCCIONES:
1. Extrae TODAS las entradas con metadata (comentarios HTML <!-- ... -->)
2. Clasifica cada entrada por tipo: task, risk, decision, note
3. Para tareas: extrae entry_id, title, description, status, owner, due_date, priority
4. Para riesgos: extrae entry_id, title, description, impact, probability, mitigation
5. Para decisiones: extrae entry_id, title, description, rationale, decided_by
6. Genera un resumen ejecutivo del día (máx 3 líneas)
7. Identifica próximos pasos críticos
8. Detecta bloqueadores o alertas

OUTPUT REQUERIDO (JSON):
{{
  "summary": "Resumen ejecutivo del día",
  "tasks": [
    {{
      "entry_id": "TASK-001",
      "title": "Título de la tarea",
      "description": "Descripción detallada",
      "status": "done|in_progress|todo|blocked",
      "owner": "@username",
      "due_date": "YYYY-MM-DD",
      "priority": "low|medium|high|critical",
      "action": "create|update|close"
    }}
  ],
  "risks": [
    {{
      "entry_id": "RISK-001",
      "title": "Título del riesgo",
      "description": "Descripción",
      "impact": "low|medium|high|critical",
      "probability": "low|medium|high",
      "mitigation": "Plan de mitigación",
      "action": "create|update|close"
    }}
  ],
  "decisions": [
    {{
      "entry_id": "DEC-001",
      "title": "Título de la decisión",
      "description": "Descripción",
      "rationale": "Razón de la decisión",
      "decided_by": "@username",
      "action": "create"
    }}
  ],
  "next_steps": [
    "Próximo paso 1",
    "Próximo paso 2"
  ],
  "blockers": [
    "Bloqueador 1 (si existe)"
  ],
  "alerts": [
    "Alerta 1 (si existe)"
  ]
}}

REGLAS:
- Si no hay entradas de un tipo, devuelve array vacío []
- Respeta los entry_id originales del documento
- Si una tarea cambió de status, usa action: "update"
- Si una tarea se completó, usa action: "close"
- NO inventes información que no esté en el documento
- Responde SOLO con el JSON, sin texto adicional"""


class GeminiService:
    """Gemini AI service"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = GEMINI_MODEL
        self.base_url = GEMINI_API_BASE

    def process_daily_log(self, daily_log_content: str) -> Optional[Dict[str, Any]]:
        """
        Process daily log with Gemini
        Returns structured JSON or None if error
        """
        try:
            # Build prompt
            prompt = GEMINI_PROMPT_TEMPLATE.format(daily_log=daily_log_content)

            # Build request payload
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 8192,
                    "responseMimeType": "application/json"
                }
            }

            # Make request
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }

            url = f"{self.base_url}/models/{self.model}:generateContent"
            response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                
                # Extract JSON from response
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        text = candidate["content"]["parts"][0].get("text", "")
                        
                        # Parse JSON
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError as e:
                            print(f"Error parsing Gemini JSON: {e}")
                            print(f"Response text: {text}")
                            return None

            print(f"Gemini API error: {response.status_code} - {response.text}")
            return None

        except Exception as e:
            print(f"Error processing with Gemini: {e}")
            return None

    def test_connection(self) -> bool:
        """Test Gemini API connection"""
        try:
            payload = {
                "contents": [{
                    "parts": [{
                        "text": "Hello, respond with 'OK'"
                    }]
                }]
            }

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }

            url = f"{self.base_url}/models/{self.model}:generateContent"
            response = requests.post(url, headers=headers, json=payload, timeout=10)

            return response.status_code == 200

        except Exception as e:
            print(f"Error testing Gemini connection: {e}")
            return False


class GeminiChatService:
    """Gemini AI service for conversational chat"""
    
    def __init__(self, api_key: str):
        """Initialize with user's API key"""
        self.api_key = api_key
        self.model = GEMINI_MODEL
        self.base_url = GEMINI_API_BASE
    
    def get_structured_response(self, prompt: str, max_tokens: int = 4096) -> str:
        """Get a direct response from Gemini without chat wrappers (useful for JSON)"""
        try:
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,  # Lower temperature for structural tasks
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": max_tokens,
                    "responseMimeType": "application/json"
                }
            }

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }

            url = f"{self.base_url}/models/{self.model}:generateContent"
            
            print(f"[DEBUG] Calling Gemini API: {url}")
            print(f"[DEBUG] Model: {self.model}")
            print(f"[DEBUG] Prompt length: {len(prompt)} chars")
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)

            # Log full response for debugging
            with open("gemini_debug.log", "a", encoding="utf-8") as f:
                f.write(f"\n\n=== API CALL DEBUG ===\n")
                f.write(f"URL: {url}\n")
                f.write(f"Status Code: {response.status_code}\n")
                f.write(f"Response Headers: {dict(response.headers)}\n")
                f.write(f"Response Body: {response.text[:2000]}\n")  # First 2000 chars

            if response.status_code == 200:
                result = response.json()
                print(f"DEBUG API RESULT: {json.dumps(result, indent=2)[:500]}")
                
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    finish_reason = candidate.get("finishReason")
                    
                    if finish_reason != "STOP":
                        print(f"[WARNING] Gemini structured finishReason: {finish_reason}")
                        with open("gemini_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"\n[WARNING] Finish Reason: {finish_reason}\n")
                    
                    if "content" in candidate and "parts" in candidate["content"]:
                        text_response = candidate["content"]["parts"][0].get("text", "")
                        print(f"[DEBUG] Got response with {len(text_response)} chars")
                        return text_response
                    else:
                        print(f"[ERROR] No content/parts in candidate")
                        with open("gemini_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"\n[ERROR] Candidate structure: {json.dumps(candidate, indent=2)}\n")
                else:
                    print(f"[ERROR] No candidates in result")
                    with open("gemini_debug.log", "a", encoding="utf-8") as f:
                        f.write(f"\n[ERROR] Full result: {json.dumps(result, indent=2)}\n")
            
            print(f"[ERROR] Gemini Structured API Error {response.status_code}: {response.text[:500]}")
            with open("gemini_debug.log", "a", encoding="utf-8") as f:
                f.write(f"\n[ERROR] API returned status {response.status_code}\n")
            return ""
            
        except Exception as e:
            print(f"[EXCEPTION] Error in get_structured_response: {e}")
            import traceback
            traceback.print_exc()
            with open("gemini_debug.log", "a", encoding="utf-8") as f:
                f.write(f"\n[EXCEPTION] {str(e)}\n{traceback.format_exc()}\n")
            return ""

    def get_response(self, user_message: str, context: str = "", max_tokens: int = 1024) -> str:
        """Get AI response from Gemini for chat"""
        
        # ... (rest of system_prompt stays same)
        system_prompt = """
Eres TEMIS Assistant, un asistente IA especializado en gestion de proyectos.

Tu rol es ayudar a los usuarios a:
- Documentar su progreso diario de manera efectiva
- Identificar riesgos, bloqueadores y dependencias
- Sugerir mejoras y proximos pasos
- Mantener el enfoque en los objetivos del proyecto
- Generar insights valiosos del trabajo diario

Caracteristicas de tus respuestas:
- Concisas pero completas (maximo 3-4 parrafos)
- Amigables y profesionales
- Orientadas a la accion
- Basadas en mejores practicas de gestion de proyectos

Cuando el usuario comparta su progreso:
1. Reconoce sus logros
2. Identifica posibles riesgos o bloqueadores
3. Sugiere proximos pasos concretos
4. Haz preguntas relevantes para profundizar

Responde siempre en español.
"""
        
        # Build full prompt with context
        full_prompt = f"{system_prompt}\n\n"
        if context:
            full_prompt += f"Contexto:\n{context}\n\n"
        full_prompt += f"Usuario: {user_message}\n\nAsistente:"
        
        try:
            # Build request payload
            payload = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": max_tokens
                }
            }

            # Make request
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }

            url = f"{self.base_url}/models/{self.model}:generateContent"
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                
                # Debug: print full result to assist with truncation issues
                # (Will be captured by terminal logs or redirected)
                
                # Extract text from response
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    finish_reason = candidate.get("finishReason")
                    if finish_reason != "STOP":
                        print(f"[WARNING] Gemini finishReason: {finish_reason}")
                    
                    if "content" in candidate and "parts" in candidate["content"]:
                        text = candidate["content"]["parts"][0].get("text", "")
                        return text
            
            print(f"[ERROR] Gemini API Error {response.status_code}: {response.text}")
            return f"Lo siento, hubo un error al procesar tu mensaje. (Status: {response.status_code})"
            
        except Exception as e:
            return f"Lo siento, hubo un error al procesar tu mensaje: {str(e)}"

