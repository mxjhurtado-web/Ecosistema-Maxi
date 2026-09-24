#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gemini Process AI Service for TEMIS Media Studio
Synthesizes transcript text and screenshot keyframes into structured process artifacts:
- Bitácora Narrativa con Capturas
- Matriz SIPOC Tabular
- Diagrama BPMN con Swimlanes
- Ficha de Proyecto para TEMIS Web
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from config.settings import load_gemini_api_key

logger = logging.getLogger("temis_media_studio")


class GeminiProcessAI:
    """Uses Gemini 2.5 Flash to synthesize transcripts and screenshots into TEMIS artifacts"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or load_gemini_api_key()
        self.is_configured = False
        if self.api_key and genai:
            try:
                genai.configure(api_key=self.api_key)
                self.is_configured = True
            except Exception as e:
                logger.warning(f"Error configuring Gemini API: {e}")

    def analyze_process(
        self,
        transcript_segments: List[Dict[str, Any]],
        keyframes: List[Dict[str, Any]],
        video_filename: str,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Analyze process recording and correlate screenshots with process steps
        """
        if not self.is_configured:
            return self._generate_fallback_analysis(transcript_segments, keyframes, video_filename)

        if progress_callback:
            progress_callback("Gemini 2.5 Flash estructurando bitácora, SIPOC y flujo con capturas...")

        # Build prompt content
        transcript_text = "\n".join([
            f"[{s.get('timestamp_start', '00:00:00')}] {s.get('speaker', 'Participante')}: {s.get('text', '')}"
            for s in transcript_segments
        ])

        keyframes_text = "\n".join([
            f"- Captura #{k.get('index')}: '{k.get('filename')}' (Timestamp: {k.get('timestamp_formatted')})"
            for k in keyframes
        ])

        prompt = f"""Eres el Auditor y Arquitecto Líder de Procesos del sistema corporativo TEMIS.
Analiza la siguiente transcripción de una entrevista/levantamiento de proceso y la lista de capturas de pantalla extraídas del video '{video_filename}'.

Tu objetivo es estructurar un paquete integral de proceso con bitácora cronológica, matriz SIPOC y diagrama BPMN, asociando cada captura de pantalla al paso correspondiente donde el usuario interactúa con el sistema.

### TRANSCRIPCIÓN CON MINUTAJES:
{transcript_text}

### CAPTURAS DE PANTALLA EXTRAÍDAS DEL VIDEO:
{keyframes_text}

### INSTRUCCIONES ESTRICTAS:
Devuelve EXCLUSIVAMENTE un objeto JSON válido (sin markdown ni texto antes o después) con la siguiente estructura exacta:

{{
  "project_charter": {{
    "project_name": "Nombre formal y profesional del proceso (ej. Liberación de Agencias y Control Operativo)",
    "project_code": "PRJ-001",
    "purpose": "Propósito claro del proceso ('Para qué sirve')",
    "scope": "Alcance del proceso (desde qué evento inicia hasta qué entregable concluye)",
    "target_system": "Sistemas informáticos mencionados (ej. Chronos, Freshdesk, SAP, etc.)",
    "sponsor": "Área dueña del proceso (ej. Operaciones / Soporte)",
    "executive_summary": "Resumen ejecutivo formal de 2-3 párrafos explicando la operativa observada."
  }},
  "process_steps": [
    {{
      "step_number": 1,
      "title": "Nombre corto de la actividad (ej. Búsqueda y Validación en Chronos)",
      "actor": "Rol que ejecuta (ej. Operador de Soporte / Analista)",
      "system": "Sistema utilizado (ej. Chronos / Correo)",
      "timestamp": "00:04:12",
      "description": "Descripción detallada paso a paso de lo que se hace y qué reglas aplican.",
      "attached_screenshot": "frame_001.jpg",
      "screenshot_caption": "Pantalla de consulta de agencia en el sistema Chronos"
    }}
  ],
  "sipoc": [
    {{
      "id": "1.0",
      "supplier": "Proveedor o disparador (ej. Agencia solicitante)",
      "input": "Entrada requerida (ej. Solicitud de liberación)",
      "process": "Actividad del proceso (ej. Validar estatus de cuenta en Chronos)",
      "output": "Salida generada (ej. Reporte de historial crediticio)",
      "customer": "Cliente receptor (ej. Comité de Liberaciones)",
      "requirement": "Requisito de calidad o SLA (ej. < 15 minutos, sin adeudo)"
    }}
  ],
  "bpmn_nodes": [
    {{
      "id": "node-1",
      "type": "node_start",
      "label": "Inicio: Recepción de Solicitud",
      "swimlane": "Input",
      "x": 40,
      "y": 140,
      "attached_system": "",
      "attached_channel": "Email"
    }},
    {{
      "id": "node-2",
      "type": "node_activity",
      "label": "Validar estatus en Chronos",
      "swimlane": "Operador",
      "x": 260,
      "y": 140,
      "attached_system": "Chronos",
      "attached_channel": ""
    }},
    {{
      "id": "node-3",
      "type": "node_decision",
      "label": "¿Cumple requisitos de liberación?",
      "swimlane": "Operador",
      "x": 520,
      "y": 140,
      "attached_system": "Chronos",
      "attached_channel": ""
    }},
    {{
      "id": "node-4",
      "type": "node_activity",
      "label": "Liberar agencia y notificar",
      "swimlane": "Operador",
      "x": 780,
      "y": 60,
      "attached_system": "Chronos",
      "attached_channel": "Email"
    }},
    {{
      "id": "node-5",
      "type": "node_activity",
      "label": "Solicitar aclaración o rechazar",
      "swimlane": "Operador",
      "x": 780,
      "y": 220,
      "attached_system": "Freshdesk",
      "attached_channel": ""
    }},
    {{
      "id": "node-6",
      "type": "node_end",
      "label": "Fin: Proceso Concluido",
      "swimlane": "Output",
      "x": 1040,
      "y": 140,
      "attached_system": "",
      "attached_channel": ""
    }}
  ],
  "bpmn_edges": [
    {{"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""}},
    {{"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""}},
    {{"id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí"}},
    {{"id": "e3-5", "source": "node-3", "target": "node-5", "label": "No"}},
    {{"id": "e4-6", "source": "node-4", "target": "node-6", "label": ""}},
    {{"id": "e5-6", "source": "node-5", "target": "node-6", "label": ""}}
  ],
  "audit_findings": [
    {{
      "type": "Mejora",
      "timestamp": "00:08:30",
      "description": "Se detecta doble validación manual que podría automatizarse mediante API."
    }}
  ]
}}
"""

        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            raw = getattr(response, "text", "") or ""
            clean = raw.strip()
            s_idx = clean.find("{")
            e_idx = clean.rfind("}")
            if s_idx != -1 and e_idx != -1:
                return json.loads(clean[s_idx:e_idx+1])
        except Exception as e:
            logger.error(f"Gemini process analysis failed: {e}")

        return self._generate_fallback_analysis(transcript_segments, keyframes, video_filename)

    def _generate_fallback_analysis(
        self,
        transcript_segments: List[Dict[str, Any]],
        keyframes: List[Dict[str, Any]],
        video_filename: str
    ) -> Dict[str, Any]:
        """Generate structured baseline analysis when offline"""
        clean_name = os.path.splitext(video_filename)[0].replace("_", " ").replace("-", " ").title()
        
        # Build steps
        steps = []
        num_kf = len(keyframes)
        for idx, seg in enumerate(transcript_segments[:10]):
            attached_kf = ""
            caption = ""
            if num_kf > 0:
                kf_idx = min(idx % num_kf, num_kf - 1)
                attached_kf = keyframes[kf_idx]["filename"]
                caption = f"Evidencia visual del paso en {keyframes[kf_idx]['timestamp_formatted']}"

            steps.append({
                "step_number": idx + 1,
                "title": f"Paso {idx + 1}: Ejecución de Actividad",
                "actor": "Operador / Analista",
                "system": "Sistema Principal",
                "timestamp": seg.get("timestamp_start", "00:00:00"),
                "description": seg.get("text", "Descripción del paso observada en la grabación."),
                "attached_screenshot": attached_kf,
                "screenshot_caption": caption
            })

        return {
            "project_charter": {
                "project_name": f"Proceso: {clean_name}",
                "project_code": "PRJ-MEDIA-01",
                "purpose": f"Estandarización y levantamiento de bitácora para el proceso {clean_name}.",
                "scope": "Desde la recepción de la solicitud hasta la conclusión de la actividad.",
                "target_system": "Sistemas Corporativos",
                "sponsor": "Operaciones",
                "executive_summary": f"Levantamiento automático generado a partir de la grabación '{video_filename}'. Contiene transcripción cronológica y evidencia gráfica de pantallas."
            },
            "process_steps": steps,
            "sipoc": [
                {
                    "id": f"{i+1}.0",
                    "supplier": "Solicitante",
                    "input": "Datos de entrada",
                    "process": s.get("title", f"Paso {i+1}"),
                    "output": "Resultado de la actividad",
                    "customer": "Área receptora",
                    "requirement": "Completar conforme a política"
                }
                for i, s in enumerate(steps[:5])
            ],
            "bpmn_nodes": [
                {"id": "node-1", "type": "node_start", "label": "Inicio", "swimlane": "Input", "x": 40, "y": 140, "attached_system": "", "attached_channel": ""},
                {"id": "node-2", "type": "node_activity", "label": "Ejecutar actividad principal", "swimlane": "Operador", "x": 260, "y": 140, "attached_system": "Sistema", "attached_channel": ""},
                {"id": "node-3", "type": "node_end", "label": "Fin", "swimlane": "Output", "x": 520, "y": 140, "attached_system": "", "attached_channel": ""}
            ],
            "bpmn_edges": [
                {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
                {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""}
            ],
            "audit_findings": []
        }
