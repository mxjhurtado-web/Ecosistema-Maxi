import google.generativeai as genai
import config
import json

class AIEngine:
    def __init__(self):
        self.reconfigure()

    def reconfigure(self):
        self.api_key = config.get_config().get("gemini_api_key", "").strip()
        self.model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Using 1.5-flash as the standard robust model
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                print(f"Error AI Engine Config: {e}")

    def ask(self, prompt, current_json, system_override=None):
        if not self.model: return "⚠️ Configura API Key en Ajustes."
        
        system_instruction = system_override or (
            "Eres el 'MAXI AI ARCHITECT'. Tu misión es diseñar flujos de Respond.io basados UNICAMENTE en el documento del usuario. "
            "Responde siempre en Español. NUNCA inventes aplicaciones externas."
        )
        
        ctx_json = json.dumps(current_json)
        full_prompt = f"""{system_instruction}

ESTRUCTURA OBLIGATORIA PARA COMANDOS:
[[COMMANDS: [
  {{"action": "ADD_NODE", "type": "sendMessage", "name": "Msg 1", "parentId": null, "node_data": {{"payload": [{{"message": {{"text": "Hola"}}}}] }} }},
  {{"action": "ADD_NODE", "type": "askQuestion", "name": "Q1", "parentId": "parent_id", "node_data": {{"payload": [...], "options": [{{"label": "Si", "value": "si"}}] }} }}
] ]]

CONTEXTO ACTUAL (JSON):
{ctx_json[:4000]}

INSTRUCCIÓN: {prompt}"""
        
        try:
            response = self.model.generate_content(full_prompt)
            if not response or not hasattr(response, 'text'):
                return "❌ Error: Respuesta vacía de la IA."
            return response.text
        except Exception as e:
            err_msg = str(e)
            if "403" in err_msg:
                return f"❌ Error API (403): La llave es inválida o está bloqueada. Por favor usa una nueva llave en 'Config Gemini'."
            return f"❌ Error: {err_msg}"

    def prepare_summary(self, requirements_text):
        prompt = (
            "Analiza este documento y genera un RESUMEN NARRATIVO detallado. "
            "Explica los pasos del diálogo y las ramas lógicas. NO USES JSON EN ESTA ETAPA.\n\n"
            f"DOCUMENTO:\n{requirements_text[:12000]}"
        )
        return self.ask(prompt, {}, system_override="Eres un analista experto en scripts de ventas.")

    def generate_from_summary(self, summary_text, feedback, current_json):
        prompt = (
            f"Basado en el análisis previo: {summary_text}\n"
            "Crea el flujo completo siguiendo la ESTRUCTURA OBLIGATORIA de [[COMMANDS: [...] ]].\n"
            "Es VITAL usar 'parentId' para conectar los nodos en un árbol ramificado."
        )
        return self.ask(prompt, current_json)
