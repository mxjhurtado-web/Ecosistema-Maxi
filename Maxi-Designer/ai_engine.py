import google.generativeai as genai
import config
import json
import os
from importers import DocParser

class AIEngine:
    def __init__(self):
        self.glossary_content = ""
        self.example_content = ""
        self.reconfigure()

    def reconfigure(self):
        conf = config.get_config()
        self.api_key = conf.get("gemini_api_key", "").strip()
        
        # Load Knowledge Base
        self.glossary_content = conf.get("glossary_text", "")
        g_path = conf.get("glossary_path")
        if g_path and os.path.exists(g_path):
            self.glossary_content += "\n" + DocParser.extract_text([g_path])
            
        e_path = conf.get("example_path")
        if e_path and os.path.exists(e_path):
            self.example_content = DocParser.extract_text([e_path])
        else:
            self.example_content = ""

        self.model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                print(f"Error AI Engine Config: {e}")

    def ask(self, prompt, current_json, system_override=None, include_template=True):
        if not self.model: return "⚠️ Configura API Key en Ajustes."
        
        # 💡 Inject Knowledge Base into System Instruction
        kb_context = ""
        if self.glossary_content.strip():
            kb_context += f"\n### REGLAS Y GLOSARIO DE NEGOCIO:\n{self.glossary_content}\n"
        if self.example_content.strip():
            kb_context += f"\n### MODELO DE REFERENCIA (ESTILO):\n{self.example_content}\n"
            
        base_instr = "Eres el 'MAXI AI ARCHITECT' experto en flujos de Respond.io. Responde siempre en Español."
        system_instruction = f"{system_override or base_instr}\n{kb_context}"
        
        template = ""
        if include_template:
            template = """
ESTRUCTURA OBLIGATORIA PARA COMANDOS (USA SOLO ESTO):
[[COMMANDS: [
  {"id": "1", "action": "ADD_NODE", "type": "sendMessage", "name": "Entrada", "parentId": null, "node_data": {"payload": [{"message": {"text": "Hola"}}] } },
  {"id": "2", "action": "ADD_NODE", "type": "askQuestion", "name": "Pregunta 1", "parentId": "1", "branchLabel": "Opción A", "node_data": {"payload": [...], "options": [{"label": "Si", "value": "si"}] } }
] ]]
IMPORTANTE: Usa IDs numéricos secuenciales ("1", "2", "3"...) para facilitar las conexiones. El parentId debe coincidir con el ID del padre generado anteriormente. Usa 'branchLabel' para nombrar la rama (ej: "Sí", "No", "Ventas").
"""
        
        ctx_json = json.dumps(current_json)
        full_prompt = f"{system_instruction}\n{template}\nCONTEXTO ACTUAL DEL LIENZO (JSON):\n{ctx_json[:5000]}\n\nINSTRUCCIÓN: {prompt}"
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text if response and hasattr(response, 'text') else "❌ Error: Respuesta vacía."
        except Exception as e:
            return f"❌ Error API: {e}"

    def prepare_summary(self, requirements_text):
        prompt = (
            "Analiza este documento y genera una LISTA EXHAUSTIVA Y PASO A PASO de cada interacción. "
            "Identifica individualmente: cada saludo, cada pregunta, cada opción de respuesta (botones) y cada respuesta del sistema. "
            "Formatea la respuesta como una lista de puntos clave. NO hagas un resumen narrativo, sé atómico y detallado.\n\n"
            f"DOCUMENTO:\n{requirements_text[:30000]}"
        )
        return self.ask(prompt, {}, system_override="Eres un analista técnico de flujos que desglosa procesos en pasos mínimos.", include_template=False)

    def generate_from_summary(self, summary_text, original_doc, current_json):
        prompt = (
            f"PASOS IDENTIFICADOS EN EL DOCUMENTO:\n{summary_text}\n\n"
            "INSTRUCCIÓN: Traduce CADA PUNTO de la lista anterior a un flujo técnico de Respond.io. "
            "1. Crea un nodo para CADA ELEMENTO de la lista. Si hay 20 pasos, crea 20 nodos. "
            "2. Usa parentId para hilarlos todos en un árbol lógico. "
            "3. Usa 'branchLabel' para conectar las opciones de botones a sus respectivos destinos. "
            "4. NO TE LIMITES. Queremos el flujo completo, desde el inicio hasta el fin absoluto del proceso. "
            "Usa la estructura [[COMMANDS: [...] ]]. Sé minucioso."
        )
        return self.ask(prompt, current_json)
