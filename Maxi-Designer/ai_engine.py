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
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                print(f"Error AI Engine Config: {e}")

    def ask(self, prompt, current_json, system_override=None, include_template=True):
        if not self.model: return "⚠️ Configura API Key en Ajustes."
        
        system_instruction = system_override or "Eres el 'MAXI AI ARCHITECT'. Responde siempre en Español."
        
        template = ""
        if include_template:
            template = """
ESTRUCTURA OBLIGATORIA PARA COMANDOS (USA SOLO ESTO):
[[COMMANDS: [
  {"action": "ADD_NODE", "type": "sendMessage", "name": "Msg 1", "parentId": null, "node_data": {"payload": [{"message": {"text": "Hola"}}] } },
  {"action": "ADD_NODE", "type": "askQuestion", "name": "Q1", "parentId": "parent_item", "node_data": {"payload": [...], "options": [{"label": "Si", "value": "si"}] } }
] ]]
"""
        
        ctx_json = json.dumps(current_json)
        full_prompt = f"{system_instruction}\n{template}\nCONTEXTO ACTUAL (JSON):\n{ctx_json[:2000]}\n\nINSTRUCCIÓN: {prompt}"
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text if response and hasattr(response, 'text') else "❌ Error: Respuesta vacía."
        except Exception as e:
            return f"❌ Error API: {e}"

    def prepare_summary(self, requirements_text):
        prompt = (
            "Analiza este documento y genera un RESUMEN NARRATIVO detallado. "
            "Describe el flujo lógico PASO A PASO. NO USES JSON, NO USES [[COMMANDS]]. "
            "Habla como un humano explicando el proceso.\n\n"
            f"DOCUMENTO:\n{requirements_text[:12000]}"
        )
        return self.ask(prompt, {}, system_override="Eres un analista experto.", include_template=False)

    def generate_from_summary(self, summary_text, original_doc, current_json):
        prompt = (
            f"DOCUMENTO ORIGINAL:\n{original_doc[:8000]}\n\n"
            f"RESUMEN APROBADO:\n{summary_text}\n\n"
            "INSTRUCCIÓN: Traduce este resumen a un flujo técnico de Respond.io. "
            "Usa la estructura de comandos [[COMMANDS: [...] ]] para crear todos los nodos conectados por 'parentId'."
        )
        return self.ask(prompt, current_json)
