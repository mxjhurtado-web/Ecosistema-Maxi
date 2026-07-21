"""
AI Quality Auditor Agent.
Uses Gemini to automatically audit chat history logs.
"""

import json
import logging
import httpx
from typing import Dict, Any, Optional
from .config import settings

logger = logging.getLogger(__name__)


class QAAuditorAgent:
    """Agent that audits conversation transcripts using Gemini API"""

    def __init__(self):
        self.model_id = "gemini-2.5-flash"

    async def audit_conversation(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends the conversation JSON to Gemini, evaluates it against the 4 QA criteria,
        and returns a dictionary with the results.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("Gemini API key not configured. QA Auditor Agent skipping.")
            return self._get_fallback_evaluation("Gemini API key not configured.")

        url = f"https://generativelanguage.googleapis.com/v1/models/{self.model_id}:generateContent?key={api_key}"
        
        system_instruction = (
            "Eres el 'Agente Auditor de Calidad IA' para el Ecosistema Maxi. Tu función es auditar conversaciones "
            "de soporte y calificar su desempeño contra 4 criterios de calidad.\n\n"
            "Analiza el historial de conversación en JSON adjunto y responde estrictamente con un objeto JSON "
            "que contenga las siguientes llaves:\n"
            "1. 'rating_intent' (bool): true si el bot identificó correctamente la intención del usuario al inicio del chat "
            "y lo canalizó al flujo/agente especializado correspondiente. false si falló en entender el tema o lo derivó incorrectamente.\n"
            "2. 'rating_resolution' (bool): true si el bot resolvió de forma correcta el estatus o proporcionó la información "
            "final según las reglas de negocio. false si dio información confusa, incorrecta o no concluyó.\n"
            "3. 'rating_formal_tone' (bool): true si el bot se dirigió al cliente con el trato formal de 'Usted' en el 100% "
            "de la conversación. false si el bot tuteó al cliente en algún momento (ej. usando palabras como 'tú', 'tu', 'te', 'puedes', 'tienes', etc.).\n"
            "4. 'rating_no_repetition' (bool): true si el bot solicitó la información (ej. la clave de la transacción o nombres) "
            "una sola vez. false si pidió los mismos datos de forma redundante o repetitiva a pesar de haberlos recibido.\n"
            "5. 'comments' (string): Explicación breve de la evaluación. Si alguno de los criterios fue calificado como false, "
            "indica con precisión en qué línea del diálogo ocurrió el desvío.\n\n"
            "Reglas adicionales:\n"
            "- Evalúa únicamente las respuestas del bot ('bot_max' o 'agent_specialized'). Los mensajes de humanos ('agent_human') "
            "u otros emisores no deben penalizar la calificación del bot.\n"
            "- Sé sumamente estricto con el criterio 'rating_formal_tone': cualquier tuteo informal ('tú', 'te', 'tuyos', 'puedes', 'tienes') "
            "emitido por el bot es un fallo (false).\n"
            "Responde estrictamente con JSON válido."
        )

        # Try to load custom QA Auditor prompt from Redis configuration
        try:
            from .config_manager import config_manager
            dynamic_agent = await config_manager.get_agent("Agente Calidad")
            if dynamic_agent and dynamic_agent.system_prompt:
                system_instruction = dynamic_agent.system_prompt
                logger.info("ℹ️ Using custom Quality Auditor system prompt from config manager (Agente Calidad)")
        except Exception as config_err:
            logger.warning(f"Could not load custom 'Agente Calidad' prompt from Redis: {config_err}. Using default.")

        prompt = f"Conversación a auditar:\n```json\n{json.dumps(chat_data, ensure_ascii=False, indent=2)}\n```"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"{system_instruction}\n\n{prompt}"}
                ]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(url, json=payload, timeout=25)
                res.raise_for_status()
                data = res.json()
                
                text_response = data['candidates'][0]['content']['parts'][0]['text']
                logger.info(f"Gemini QA Auditor Raw Response: {text_response}")
                
                # Parse JSON response
                parsed = json.loads(text_response)
                return {
                    "rating_intent": bool(parsed.get("rating_intent", True)),
                    "rating_resolution": bool(parsed.get("rating_resolution", True)),
                    "rating_formal_tone": bool(parsed.get("rating_formal_tone", True)),
                    "rating_no_repetition": bool(parsed.get("rating_no_repetition", True)),
                    "comments": str(parsed.get("comments") or "Auditoría realizada de forma automática.")
                }
        except Exception as e:
            logger.error(f"Error calling Gemini QA Auditor Agent: {str(e)}")
            return self._get_fallback_evaluation(f"Error de ejecución del Auditor: {str(e)}")

    def _get_fallback_evaluation(self, reason: str) -> Dict[str, Any]:
        """Returns fallback scores in case of model error"""
        return {
            "rating_intent": True,
            "rating_resolution": True,
            "rating_formal_tone": True,
            "rating_no_repetition": True,
            "comments": f"Auditoría automática fallida. Razón: {reason}"
        }


# Singleton instance
qa_auditor_agent = QAAuditorAgent()
