#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gemini Document Analyzer for TEMIS
Analyzes documents and distributes content across project phases
"""

from typing import Dict, Any, Optional
import json
from backend.services.gemini_service import GeminiChatService


class GeminiDocumentAnalyzer:
    """Analyze documents and map to TEMIS phases"""
    
    def __init__(self, api_key: str):
        self.gemini = GeminiChatService(api_key)
    
    def analyze_for_phases(self, document_content: str) -> Dict[str, Any]:
        """
        Analyze document and distribute content across 7 TEMIS phases
        Returns structured analysis with tasks, deliverables, and risks per phase
        """
        
        prompt = self._build_analysis_prompt(document_content)
        
        try:
            # Use structured response for JSON output
            response = self.gemini.get_structured_response(prompt, max_tokens=4096)
            
            # Debug log
            with open("gemini_debug.log", "w", encoding="utf-8") as f:
                f.write(f"--- RAW RESPONSE FROM GEMINI ---\n{response}\n")

            # Robust JSON extraction: look for the first '{' and last '}'
            clean_response = response.strip()
            
            # Find JSON boundaries
            start_idx = clean_response.find('{')
            end_idx = clean_response.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_part = clean_response[start_idx:end_idx+1]
                try:
                    analysis = json.loads(json_part)
                    print(f"[DEBUG] Successfully parsed JSON from Gemini (chars {start_idx} to {end_idx})")
                    return analysis
                except json.JSONDecodeError as je:
                    print(f"[ERROR] Failed to parse extracted JSON part: {je}")
                    # Try one more cleanup (removing common markdown artifacts)
                    json_part = json_part.replace("```json", "").replace("```", "").strip()
                    return json.loads(json_part)
            else:
                print(f"[ERROR] Could not find JSON boundaries in Gemini response")
                return self._get_default_structure()
            
        except json.JSONDecodeError as e:
            msg = f"Error parsing Gemini response: {e}\n"
            print(msg)
            with open("gemini_debug.log", "a", encoding="utf-8") as f:
                f.write(f"\n--- PARSE ERROR ---\n{msg}\n")
            return self._get_default_structure()
        except Exception as e:
            msg = f"Error analyzing document: {e}\n"
            print(msg)
            import traceback
            traceback.print_exc()
            with open("gemini_debug.log", "a", encoding="utf-8") as f:
                f.write(f"\n--- GENERAL ERROR ---\n{msg}\n")
            return self._get_default_structure()
    
    def _build_analysis_prompt(self, content: str) -> str:
        """Build prompt for Gemini analysis based on ultra-explicit Hybrid Methodology"""
        
        return f"""Eres un experto consultor Senior en Gestión de Proyectos especializado en Metodología Híbrida (SCRUM / PMBOK / UX). 
Tu objetivo es analizar el documento adjunto y mapear el progreso contra las 7 fases oficiales de TEMIS.

---
METODOLOGÍA OFICIAL (Checklist y Evidencias):

FASE 1: Diagnóstico Estratégico
- Objetivo: Evaluar panorama, problema, usuarios y procesos.
- Checklist: Priorización estratégica, Informe diagnóstico general, Análisis AS-IS, Mapa de personas, Customer Journey Map.
- Evidencias clave: "Análisis AS-IS", "Mapa de Personas", "Stakeholders", "Problemática", "Pain points".
- Roles: Project Lead (Resp), Resp. de Procesos, PO, Developers.

FASE 2: Inicio del Proyecto
- Objetivo: Formalización, visión del producto, roles y alcance.
- Checklist: Acta de Constitución (Project Charter), Visión del Producto, Gobernanza y Roles, Modelo Operativo (Alcance In/Out).
- Evidencias clave: "Charter", "Constitución", "Product Vision", "Gobernanza", "In-Scope", "Out-Scope".
- Roles: Sponsor (Autoriza), Project Lead (Resp), PO, PM/Agile Lead.

FASE 3: Planificación Híbrida
- Objetivo: Plan ejecutable, roadmap, backlog y arquitectura.
- Checklist: Roadmap del Proyecto, Backlog Inicial Priorizado, Arquitectura de Experiencia (TO-BE), Declaración de beneficios (Product Goal).
- Evidencias clave: "Roadmap", "Hitos", "Backlog", "Priorización", "Arquitectura UX", "Product Goal", "Meta medible".
- Roles: Project Lead (Resp), PO, PM/Agile Lead, Developers, Procesos.

FASE 4: Ejecución Iterativa
- Objetivo: Implementación por sprint, UX y evolución de procesos.
- Checklist: Incremento del Producto, Prototipos UX/UI, Historias de Usuario refinadas, Pruebas de Usabilidad, Diseño Proceso TO-BE, Sign-off incrementos.
- Evidencias clave: "Sprint", "Incremento", "Prototipo", "User Story", "Pruebas usabilidad", "Sign-off".
- Roles: PM/Agile Lead (Resp), Developers, PO, Procesos, Calidad/Datos.

FASE 5: Monitoreo y Control
- Objetivo: Controlar hitos, indicadores, riesgos y cambios.
- Checklist: Aseguramiento de hitos, UX Metrics (CSAT/NPS), Informes de desempeño (Semáforo), Gestión de riesgos, Control de cambios.
- Evidencias clave: "Métricas UX", "Reporte ejecutivo", "Matriz de riesgos", "Bloqueos", "Control de cambios".
- Roles: Project Lead (Resp), PM/Agile Lead, PO, Calidad/Datos.

FASE 6: Mejora Continua
- Objetivo: Aprendizaje e innovación para optimizar.
- Checklist: Lecciones aprendidas, Propuestas de innovación, Iteraciones de optimización, Informe retrospectiva global.
- Evidencias clave: "Lecciones aprendidas", "Retrospectiva global", "Propuestas de mejora", "Optimización".
- Roles: PM/Agile Lead (Resp), Project Lead, Developers, Procesos, Calidad.

FASE 7: Cierre del Proyecto
- Objetivo: Finalización formal, entrega de valor y handoff.
- Checklist: Revisión final valor/UX vs Product Goal, Documentación final, Entrega formal (Transición), Retrospectiva final Scrum.
- Evidencias clave: "Transición", "Handoff", "Capacitación", "Entrega formal", "Resultados finales", "Firma de aceptación".
- Roles: Project Lead (Resp), Sponsor (Acepta), PO, PM/Agile Lead, Calidad.

---
DOCUMENTO A ANALIZAR:
{content}

---
INSTRUCCIONES CRÍTICAS:
1. **Identificación de Roles**: Usa SOLO los roles permitidos: Sponsor del Proyecto, Project Lead, Product Owner (PO), Project Manager / Agile Lead, Developers, Resp. de Procesos, Resp. Calidad y Datos, Comité Stakeholders.

2. **Detección de Progreso (ANÁLISIS PROFUNDO - NO SOLO PALABRAS CLAVE)**:
   - **REGLA FUNDAMENTAL**: NO asignes progreso solo por encontrar palabras clave. Debes analizar si el CONTENIDO REAL cumple con los requisitos de la fase.
   
   - **Criterios de Evaluación por Fase**:
     * **Fase 1 (Diagnóstico)**: 
       - ¿Hay un análisis detallado del problema actual con datos concretos?
       - ¿Se identifican stakeholders con sus necesidades específicas?
       - ¿Existe mapeo de procesos actuales (AS-IS) con flujos documentados?
       - Progreso = (Items completados con contenido sustancial / 5) * 100
     
     * **Fase 2 (Inicio)**:
       - ¿Hay autorización formal del proyecto con sponsor identificado?
       - ¿Se define claramente qué está IN-SCOPE y OUT-SCOPE?
       - ¿Existe una visión del producto con objetivos medibles?
       - Progreso = (Items completados con contenido sustancial / 4) * 100
     
     * **Fase 3 (Planificación)**:
       - ¿Hay un roadmap con fechas y milestones específicos?
       - ¿Existe un backlog priorizado con historias de usuario o requerimientos?
       - ¿Se define arquitectura técnica o de experiencia (TO-BE)?
       - ¿Hay un Product Goal medible y claro?
       - Progreso = (Items completados con contenido sustancial / 4) * 100
     
     * **Fase 4 (Ejecución)**:
       - ¿Se mencionan sprints específicos con entregables concretos?
       - ¿Hay evidencia de incrementos de producto funcionando?
       - ¿Se documentan pruebas de usabilidad o validaciones con usuarios?
       - Progreso = (Sprints completados / Total sprints planeados) * 100
     
     * **Fase 5 (Monitoreo)**:
       - ¿Existen métricas cuantitativas de progreso (KPIs, métricas UX)?
       - ¿Hay matriz de riesgos con mitigaciones específicas?
       - ¿Se reportan bloqueos o cambios formalmente?
       - Progreso = (Items de control implementados / 5) * 100
     
     * **Fase 6 (Mejora)**:
       - ¿Hay retrospectivas documentadas con acciones concretas?
       - ¿Se proponen mejoras basadas en aprendizajes?
       - Progreso = (Retrospectivas + Mejoras implementadas / Items esperados) * 100
     
     * **Fase 7 (Cierre)**:
       - ¿Hay entrega formal documentada?
       - ¿Se comparan resultados vs objetivos iniciales?
       - ¿Existe plan de transición a operaciones?
       - Progreso = (Items de cierre completados / 4) * 100

3. **Validación de Contenido**:
   - Si encuentras una palabra clave pero NO hay contenido sustancial detrás, NO cuentes ese item.
   - Ejemplo INCORRECTO: Ver "Mapa de Personas" en un título sin contenido → 0% de progreso
   - Ejemplo CORRECTO: Ver "Mapa de Personas" con tabla de stakeholders, roles, intereses → 20% de progreso
   
4. **Descripción de Evidencia**: 
   - NO digas solo "Se encontró X". 
   - DI: "Se encontró X con [detalle específico del contenido]"
   - Ejemplo: "Se encontró Mapa de Personas con 5 stakeholders identificados y matriz de poder-interés"

5. **Progreso Conservador**:
   - Si tienes duda sobre si el contenido es suficiente, asigna el progreso MÁS BAJO.
   - Es mejor subestimar que sobreestimar el progreso.

FORMATO DE RESPUESTA (JSON):
{{
  "project_summary": "Resumen ejecutivo",
  "roles": [{{ "name": "...", "position": "[Rol de la lista permitida]", "responsibilities": "..." }}],
  "phases": [
    {{
      "phase_number": 1,
      "phase_name": "Nombre oficial",
      "status": "completed" | "in_progress" | "not_started",
      "progress": 0-100,
      "description": "RESUMEN DE EVIDENCIA: Qué items del checklist encontraste.",
      "tasks": ["Item del checklist 1", "Item del checklist 2"],
      "deliverables": ["Evidencia detectada (ej: El documento menciona AS-IS)"]
    }},
    ... (fases 1 a 7)
  ],
  "missing_from_methodology": ["Entregable obligatorio faltante"]
}}

IMPORTANTE: Responde ÚNICAMENTE con el objeto JSON."""
    
    def _get_default_structure(self) -> Dict[str, Any]:
        """Return default structure if analysis fails"""
        return {
            "project_summary": "Proyecto creado desde documento",
            "roles": [],
            "phases": [
                {
                    "phase_number": i,
                    "phase_name": name,
                    "status": "not_started",
                    "progress": 0,
                    "description": f"Fase {i}: {name}",
                    "tasks": [],
                    "deliverables": [],
                    "risks": []
                }
                for i, name in enumerate([
                    "Diagnostico Estrategico", "Inicio del Proyecto", "Planificacion Hibrida", 
                    "Ejecucion Iterativa", "Monitoreo y Control", "Mejora Continua", "Cierre del Proyecto"
                ], 1)
            ],
            "missing_from_methodology": []
        }
