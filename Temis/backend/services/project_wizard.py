#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project Wizard Service for TEMIS
Guides users through project creation with conversational AI
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class ProjectWizardService:
    """Conversational wizard for project creation"""
    
    # Wizard flow definition
    WIZARD_STEPS = {
        "welcome": {
            "message": "¡Hola! 👋 Soy tu asistente de TEMIS. Voy a ayudarte a crear tu proyecto paso a paso siguiendo nuestra metodología híbrida.\n\n¿Estás listo para empezar?",
            "type": "confirmation",
            "options": ["Sí, empecemos", "Necesito más información"],
            "next_yes": "step_1_name",
            "next_no": "explain_methodology"
        },
        "explain_methodology": {
            "message": "TEMIS usa una metodología híbrida que combina SCRUM, PMBOK y UX en 7 fases:\n\n1️⃣ Diagnóstico Estratégico\n2️⃣ Inicio del Proyecto\n3️⃣ Planificación Híbrida\n4️⃣ Ejecución Iterativa\n5️⃣ Monitoreo y Control\n6️⃣ Mejora Continua\n7️⃣ Cierre del Proyecto\n\nTe guiaré para que no te pierdas ningún paso importante. ¿Listo ahora?",
            "type": "confirmation",
            "options": ["Sí, empecemos", "Volver al inicio"],
            "next_yes": "step_1_name",
            "next_no": "welcome"
        },
        "step_1_name": {
            "message": "Perfecto. Empecemos con lo básico:\n\n📝 **¿Cuál es el nombre de tu proyecto?**\n\nEj: 'Sistema de Gestión de Inventarios', 'App Móvil de Ventas'",
            "type": "text",
            "field": "project_name",
            "validation": {"required": True, "min_length": 3},
            "next": "step_2_objective"
        },
        "step_2_objective": {
            "message": "Excelente nombre: **{project_name}**\n\n🎯 **¿Cuál es el objetivo principal o problema que resuelve este proyecto?**\n\nSé específico. Esto será tu norte durante todo el proyecto.",
            "type": "textarea",
            "field": "objective",
            "validation": {"required": True, "min_length": 20},
            "next": "step_3_sponsor"
        },
        "step_3_sponsor": {
            "message": "Perfecto. Ahora hablemos del equipo:\n\n👔 **¿Quién es el Sponsor o patrocinador ejecutivo del proyecto?**\n\n(La persona que autoriza y respalda el proyecto a nivel directivo)",
            "type": "text",
            "field": "sponsor_name",
            "validation": {"required": True},
            "next": "step_4_lead"
        },
        "step_4_lead": {
            "message": "👨‍💼 **¿Quién será el Project Lead?**\n\n(Responsable de la gestión integral del proyecto)",
            "type": "text",
            "field": "project_lead",
            "validation": {"required": True},
            "next": "step_5_deadline"
        },
        "step_5_deadline": {
            "message": "📅 **¿Cuál es la fecha objetivo de entrega?**\n\n(Formato: DD/MM/YYYY)",
            "type": "date",
            "field": "target_date",
            "validation": {"required": False},
            "next": "step_6_document"
        },
        "step_6_document": {
            "message": "📄 **¿Tienes algún documento inicial?**\n\n(Charter, propuesta, diagnóstico, etc.)\n\nPuedes subirlo ahora o hacerlo después.",
            "type": "file_optional",
            "field": "initial_document",
            "validation": {"required": False},
            "next": "step_7_confirm"
        },
        "step_7_confirm": {
            "message": "✅ **Resumen de tu proyecto:**\n\n📌 **Nombre:** {project_name}\n🎯 **Objetivo:** {objective}\n👔 **Sponsor:** {sponsor_name}\n👨‍💼 **Project Lead:** {project_lead}\n📅 **Fecha objetivo:** {target_date}\n\n¿Todo correcto?",
            "type": "confirmation",
            "options": ["Sí, crear proyecto", "Necesito corregir algo"],
            "next_yes": "create_project",
            "next_no": "step_1_name"
        },
        "create_project": {
            "message": "🎉 **¡Proyecto creado exitosamente!**\n\nHe configurado las 7 fases de la metodología híbrida.\n\n📋 **Siguiente paso recomendado:**\nComienza con el Diagnóstico Estratégico (Fase 1). Necesitarás:\n- Análisis AS-IS de procesos actuales\n- Mapa de Personas (arquetipos de usuario)\n- Customer Journey Map\n\n¿Quieres que te ayude con alguno de estos entregables?",
            "type": "final",
            "action": "create_project"
        }
    }
    
    def __init__(self):
        self.sessions = {}  # Store wizard sessions
    
    def start_wizard(self, user_id: str) -> Dict[str, Any]:
        """Start a new wizard session"""
        session_id = f"{user_id}_{datetime.now().timestamp()}"
        
        self.sessions[session_id] = {
            "user_id": user_id,
            "current_step": "welcome",
            "data": {},
            "started_at": datetime.now().isoformat()
        }
        
        return {
            "session_id": session_id,
            "step": self._get_step_data("welcome", {})
        }
    
    def process_answer(self, session_id: str, answer: Any) -> Dict[str, Any]:
        """Process user's answer and return next step"""
        if session_id not in self.sessions:
            return {"error": "Invalid session"}
        
        session = self.sessions[session_id]
        current_step_id = session["current_step"]
        current_step = self.WIZARD_STEPS[current_step_id]
        
        # Validate answer
        if "validation" in current_step:
            validation_result = self._validate_answer(answer, current_step["validation"])
            if not validation_result["valid"]:
                return {
                    "error": validation_result["message"],
                    "step": self._get_step_data(current_step_id, session["data"])
                }
        
        # Store answer
        if "field" in current_step:
            session["data"][current_step["field"]] = answer
        
        # Determine next step
        next_step_id = self._get_next_step(current_step, answer)
        
        if next_step_id == "create_project":
            # Wizard complete - return project data
            return {
                "completed": True,
                "project_data": session["data"],
                "step": self._get_step_data(next_step_id, session["data"])
            }
        
        session["current_step"] = next_step_id
        
        return {
            "session_id": session_id,
            "step": self._get_step_data(next_step_id, session["data"])
        }
    
    def _get_step_data(self, step_id: str, data: Dict) -> Dict[str, Any]:
        """Get step data with interpolated variables"""
        step = self.WIZARD_STEPS[step_id].copy()
        
        # Interpolate variables in message
        if "message" in step:
            step["message"] = step["message"].format(**data) if data else step["message"]
        
        return {
            "step_id": step_id,
            "message": step.get("message", ""),
            "type": step.get("type", "text"),
            "options": step.get("options", []),
            "field": step.get("field")
        }
    
    def _validate_answer(self, answer: Any, validation: Dict) -> Dict[str, Any]:
        """Validate user's answer"""
        if validation.get("required") and not answer:
            return {"valid": False, "message": "Este campo es obligatorio"}
        
        if "min_length" in validation and len(str(answer)) < validation["min_length"]:
            return {
                "valid": False,
                "message": f"Debe tener al menos {validation['min_length']} caracteres"
            }
        
        return {"valid": True}
    
    def _get_next_step(self, current_step: Dict, answer: Any) -> str:
        """Determine next step based on current step and answer"""
        if current_step["type"] == "confirmation":
            if answer in ["Sí, empecemos", "Sí, crear proyecto"]:
                return current_step["next_yes"]
            else:
                return current_step["next_no"]
        
        return current_step.get("next", "create_project")
