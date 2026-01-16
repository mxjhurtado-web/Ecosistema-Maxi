#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Proyecto Max Update Service
Automatically updates Proyecto Max.docx with data from daily logs (Opción A)
"""

from typing import Dict, Any, List
from datetime import datetime, date
import json


class ProyectoMaxUpdater:
    """Service to update Proyecto Max document"""

    def __init__(self, gemini_service, drive_service):
        self.gemini_service = gemini_service
        self.drive_service = drive_service

    def extract_semaforo_data(self, daily_logs: List[Dict], tasks: List[Dict], risks: List[Dict]) -> Dict:
        """Extract semáforo (traffic light) data from project state"""
        
        # Calcular estado de alcance
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t['status'] == 'done'])
        alcance_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        if alcance_percentage >= 90:
            alcance_status = "verde"
        elif alcance_percentage >= 70:
            alcance_status = "amarillo"
        else:
            alcance_status = "rojo"
        
        # Calcular estado de tiempo (basado en hitos)
        # TODO: Implementar lógica de hitos
        tiempo_status = "verde"
        
        # Calcular estado de costo
        # TODO: Implementar tracking de presupuesto
        costo_status = "verde"
        
        # Calcular estado de calidad/UX (basado en riesgos)
        high_risks = len([r for r in risks if r['impact'] == 'high' and r['status'] == 'open'])
        if high_risks == 0:
            calidad_status = "verde"
        elif high_risks <= 2:
            calidad_status = "amarillo"
        else:
            calidad_status = "rojo"
        
        return {
            "alcance": {
                "status": alcance_status,
                "percentage": alcance_percentage,
                "descripcion": f"{completed_tasks}/{total_tasks} tareas completadas"
            },
            "tiempo": {
                "status": tiempo_status,
                "descripcion": "En tiempo"
            },
            "costo": {
                "status": costo_status,
                "descripcion": "Dentro de presupuesto"
            },
            "calidad_ux": {
                "status": calidad_status,
                "descripcion": f"{high_risks} riesgos altos abiertos"
            }
        }

    def extract_hitos_data(self, project_data: Dict) -> List[Dict]:
        """Extract hitos (milestones) data"""
        # TODO: Implementar cuando tengamos modelo de Hitos
        return [
            {
                "nombre": "MVP Entregado",
                "fecha_planeada": "2026-02-15",
                "fecha_real": None,
                "status": "en_progreso"
            }
        ]

    def extract_riesgos_data(self, risks: List[Dict]) -> List[Dict]:
        """Extract and format risks data"""
        formatted_risks = []
        for risk in risks:
            formatted_risks.append({
                "id": risk.get('entry_id', 'RISK-XXX'),
                "descripcion": risk.get('title', ''),
                "probabilidad": risk.get('probability', 'medium'),
                "impacto": risk.get('impact', 'medium'),
                "mitigacion": risk.get('mitigation', ''),
                "responsable": risk.get('owner', ''),
                "status": risk.get('status', 'open')
            })
        return formatted_risks

    def extract_cambios_data(self, decisions: List[Dict]) -> List[Dict]:
        """Extract changes/decisions data"""
        formatted_changes = []
        for decision in decisions:
            formatted_changes.append({
                "id": decision.get('entry_id', 'DEC-XXX'),
                "descripcion": decision.get('title', ''),
                "impacto": decision.get('rationale', ''),
                "decision": "Aprobado",  # TODO: Add approval status
                "aprobador": decision.get('decided_by', ''),
                "fecha": decision.get('decided_at', datetime.now().strftime('%Y-%m-%d'))
            })
        return formatted_changes

    def generate_update_prompt(self, project_name: str, data: Dict) -> str:
        """Generate prompt for Gemini to update Proyecto Max"""
        
        prompt = f"""Actualiza las siguientes secciones del documento "Proyecto Max" para el proyecto "{project_name}":

## SEMÁFORO DEL PROYECTO

Actualiza la tabla del semáforo con estos datos:

| Dimensión | Estado | Descripción |
|-----------|--------|-------------|
| Alcance | {data['semaforo']['alcance']['status'].upper()} | {data['semaforo']['alcance']['descripcion']} |
| Tiempo | {data['semaforo']['tiempo']['status'].upper()} | {data['semaforo']['tiempo']['descripcion']} |
| Costo | {data['semaforo']['costo']['status'].upper()} | {data['semaforo']['costo']['descripcion']} |
| Calidad/UX | {data['semaforo']['calidad_ux']['status'].upper()} | {data['semaforo']['calidad_ux']['descripcion']} |

## MATRIZ DE RIESGOS

Actualiza la matriz de riesgos con estos datos:

{json.dumps(data['riesgos'], indent=2, ensure_ascii=False)}

## REGISTRO DE CAMBIOS

Actualiza el registro de cambios con:

{json.dumps(data['cambios'], indent=2, ensure_ascii=False)}

## PRÓXIMOS PASOS

Basado en los datos del proyecto, genera una lista de próximos pasos prioritarios.

Devuelve el contenido actualizado en formato Markdown, manteniendo la estructura del documento original.
"""
        return prompt

    async def update_proyecto_max(
        self,
        project_id: str,
        project_name: str,
        daily_logs: List[Dict],
        tasks: List[Dict],
        risks: List[Dict],
        decisions: List[Dict],
        gemini_api_key: str
    ) -> Dict[str, Any]:
        """
        Main function to update Proyecto Max
        Called after EOD processing
        """
        
        try:
            # 1. Extract data from project state
            semaforo_data = self.extract_semaforo_data(daily_logs, tasks, risks)
            hitos_data = self.extract_hitos_data({})
            riesgos_data = self.extract_riesgos_data(risks)
            cambios_data = self.extract_cambios_data(decisions)
            
            update_data = {
                "semaforo": semaforo_data,
                "hitos": hitos_data,
                "riesgos": riesgos_data,
                "cambios": cambios_data
            }
            
            # 2. Generate update prompt
            prompt = self.generate_update_prompt(project_name, update_data)
            
            # 3. Use Gemini to generate updated content
            # TODO: Implement actual Gemini call
            # updated_content = self.gemini_service.update_document(prompt, gemini_api_key)
            
            # 4. Update document in Drive
            # TODO: Implement Drive update
            # self.drive_service.update_document(project_master_doc_id, updated_content)
            
            return {
                "status": "success",
                "updated_sections": ["semaforo", "riesgos", "cambios"],
                "timestamp": datetime.now().isoformat(),
                "data": update_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def generate_proyecto_max_complete(
        self,
        project_data: Dict,
        gemini_api_key: str
    ) -> str:
        """
        Generate complete Proyecto Max document (Opción B)
        Called when user clicks "Generar Avance" or at project closure
        """
        
        prompt = f"""Genera un documento completo "Proyecto Max" siguiendo esta estructura:

# PROYECTO MAX - {project_data['name']}

## 1. DEFINICIÓN DE ROLES Y GOBERNANZA
{json.dumps(project_data.get('roles', {}), indent=2, ensure_ascii=False)}

## 2. FASE 1: DIAGNÓSTICO
{json.dumps(project_data.get('fase1_deliverables', {}), indent=2, ensure_ascii=False)}

## 3. FASE 2: INICIO
{json.dumps(project_data.get('fase2_deliverables', {}), indent=2, ensure_ascii=False)}

## 4. FASE 3: PLANIFICACIÓN
{json.dumps(project_data.get('fase3_deliverables', {}), indent=2, ensure_ascii=False)}

## 5. FASE 4: EJECUCIÓN ITERATIVA
{json.dumps(project_data.get('sprints', []), indent=2, ensure_ascii=False)}

## 6. FASE 5: MONITOREO Y CONTROL
- Semáforo: {json.dumps(project_data.get('semaforo', {}), indent=2, ensure_ascii=False)}
- Hitos: {json.dumps(project_data.get('hitos', []), indent=2, ensure_ascii=False)}
- Riesgos: {json.dumps(project_data.get('riesgos', []), indent=2, ensure_ascii=False)}

## 7. FASE 6: MEJORA CONTINUA
{json.dumps(project_data.get('fase6_deliverables', {}), indent=2, ensure_ascii=False)}

## 8. FASE 7: CIERRE
{json.dumps(project_data.get('fase7_deliverables', {}), indent=2, ensure_ascii=False)}

Genera el documento completo en formato Markdown profesional, con tablas bien formateadas.
"""
        
        # TODO: Implement Gemini call
        # return self.gemini_service.generate_document(prompt, gemini_api_key)
        
        return "Documento generado (placeholder)"
