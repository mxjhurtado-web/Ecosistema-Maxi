#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project Suggestions Service for TEMIS
Provides contextual recommendations based on project state
"""

from typing import Dict, Any, List
from backend.models.phase import Phase, PhaseStatus
import json


class ProjectSuggestionsService:
    """Generate contextual suggestions for project continuity"""
    
    # Deliverables expected per phase
    PHASE_DELIVERABLES = {
        1: ["Análisis AS-IS", "Mapa de Personas", "Customer Journey Map", "Informe diagnóstico"],
        2: ["Acta de Constitución", "Product Vision", "Gobernanza y Roles", "Modelo Operativo"],
        3: ["Roadmap", "Backlog Priorizado", "Arquitectura UX", "Product Goal"],
        4: ["Incremento del Producto", "Prototipos UX/UI", "Historias de Usuario", "Pruebas de Usabilidad"],
        5: ["Métricas UX", "Informes de Desempeño", "Matriz de Riesgos", "Control de Cambios"],
        6: ["Lecciones Aprendidas", "Propuestas de Innovación", "Retrospectiva Global"],
        7: ["Documentación Final", "Entrega Formal", "Retrospectiva Final", "Firma de Aceptación"]
    }
    
    def get_suggestions(self, project: Any, phases: List[Phase]) -> List[Dict[str, Any]]:
        """Generate suggestions based on project state"""
        suggestions = []
        
        # Sort phases by number
        sorted_phases = sorted(phases, key=lambda p: p.phase_number)
        
        for phase in sorted_phases:
            # Check for not started phases
            if phase.progress == 0:
                suggestions.append(self._suggest_start_phase(phase))
            
            # Check for in-progress phases
            elif 0 < phase.progress < 100:
                suggestions.append(self._suggest_complete_phase(phase))
            
            # Check for completed phases without next phase started
            elif phase.progress == 100:
                next_phase = self._get_next_phase(phase.phase_number, sorted_phases)
                if next_phase and next_phase.progress == 0:
                    suggestions.append(self._suggest_next_phase(phase, next_phase))
        
        # Check for stale projects (no updates in 7 days)
        suggestions.extend(self._check_stale_project(project, sorted_phases))
        
        # Prioritize suggestions
        return self._prioritize_suggestions(suggestions)
    
    def _suggest_start_phase(self, phase: Phase) -> Dict[str, Any]:
        """Suggest starting a not-started phase"""
        deliverables = self.PHASE_DELIVERABLES.get(phase.phase_number, [])
        
        return {
            "type": "start_phase",
            "priority": "high" if phase.phase_number <= 2 else "medium",
            "phase_number": phase.phase_number,
            "phase_name": phase.name,
            "title": f"Iniciar {phase.name}",
            "message": f"Aún no has comenzado la {phase.name}. Esta fase es clave para el éxito del proyecto.",
            "action": "start_phase",
            "action_label": "Comenzar Fase",
            "details": f"Necesitarás preparar: {', '.join(deliverables[:3])}",
            "icon": "🚀"
        }
    
    def _suggest_complete_phase(self, phase: Phase) -> Dict[str, Any]:
        """Suggest completing an in-progress phase"""
        # Parse deliverables
        try:
            current_deliverables = json.loads(phase.deliverables) if phase.deliverables else []
        except:
            current_deliverables = []
        
        expected_deliverables = self.PHASE_DELIVERABLES.get(phase.phase_number, [])
        missing = [d for d in expected_deliverables if d not in current_deliverables]
        
        return {
            "type": "complete_phase",
            "priority": "high",
            "phase_number": phase.phase_number,
            "phase_name": phase.name,
            "title": f"¡Casi terminas {phase.name}!",
            "message": f"Llevas {phase.progress}% de avance. Te falta poco para completar esta fase.",
            "action": "upload_document",
            "action_label": "Subir Documento",
            "details": f"Pendientes: {', '.join(missing[:3]) if missing else 'Actualiza el progreso'}",
            "icon": "⚡"
        }
    
    def _suggest_next_phase(self, completed_phase: Phase, next_phase: Phase) -> Dict[str, Any]:
        """Suggest moving to next phase after completion"""
        return {
            "type": "next_phase",
            "priority": "high",
            "phase_number": next_phase.phase_number,
            "phase_name": next_phase.name,
            "title": f"¡Completaste {completed_phase.name}!",
            "message": f"Excelente trabajo. Es momento de avanzar a {next_phase.name}.",
            "action": "start_phase",
            "action_label": f"Ir a {next_phase.name}",
            "details": f"Siguiente paso: {self.PHASE_DELIVERABLES.get(next_phase.phase_number, ['Revisar checklist'])[0]}",
            "icon": "🎉"
        }
    
    def _check_stale_project(self, project: Any, phases: List[Phase]) -> List[Dict[str, Any]]:
        """Check if project has been inactive"""
        from datetime import datetime, timedelta
        
        suggestions = []
        
        # Check if any phase was updated recently
        if project.updated_at:
            days_since_update = (datetime.utcnow() - project.updated_at).days
            
            if days_since_update >= 7:
                # Find current phase
                current_phase = next((p for p in phases if 0 < p.progress < 100), None)
                
                suggestions.append({
                    "type": "stale_project",
                    "priority": "urgent",
                    "phase_number": current_phase.phase_number if current_phase else 1,
                    "phase_name": current_phase.name if current_phase else "Diagnóstico",
                    "title": "⚠️ Proyecto sin actividad",
                    "message": f"Han pasado {days_since_update} días sin actualizaciones. ¿Necesitas ayuda para retomar el momentum?",
                    "action": "daily_standup",
                    "action_label": "Hacer Daily Standup",
                    "details": "Un Daily Standup te ayudará a identificar bloqueos y próximos pasos",
                    "icon": "⏰"
                })
        
        return suggestions
    
    def _get_next_phase(self, current_phase_number: int, phases: List[Phase]) -> Phase:
        """Get the next phase"""
        return next((p for p in phases if p.phase_number == current_phase_number + 1), None)
    
    def _prioritize_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        """Sort suggestions by priority"""
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(suggestions, key=lambda s: priority_order.get(s["priority"], 3))
    
    def get_daily_standup_questions(self, project: Any, current_phase: Phase) -> Dict[str, Any]:
        """Generate Daily Standup questions"""
        return {
            "project_name": project.name,
            "current_phase": current_phase.name,
            "questions": [
                {
                    "id": "yesterday",
                    "question": f"¿Qué avanzaste ayer en {project.name}?",
                    "placeholder": "Ej: Terminé el prototipo de la pantalla de login",
                    "type": "textarea"
                },
                {
                    "id": "today",
                    "question": "¿Qué planeas hacer hoy?",
                    "placeholder": "Ej: Voy a hacer pruebas de usabilidad con 5 usuarios",
                    "type": "textarea"
                },
                {
                    "id": "blockers",
                    "question": "¿Hay algún bloqueo o impedimento?",
                    "placeholder": "Ej: Necesito acceso a la base de datos de producción",
                    "type": "textarea",
                    "optional": True
                }
            ],
            "next_action": "Registraré todo en el chat del proyecto para que quede documentado."
        }
