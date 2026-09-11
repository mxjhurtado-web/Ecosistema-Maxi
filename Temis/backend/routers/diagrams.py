#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Diagrams router for TEMIS Process Flow Diagrams
CRUD and AI Flowchart Generation API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json

from backend.database import get_db
from backend.models.diagram import Diagram
from backend.models.project import Project
from backend.services.gemini_service import GeminiService
from config.config import get_gemini_api_key

router = APIRouter(prefix="/api/diagrams", tags=["diagrams"])


# Pydantic Schemas
class DiagramCreate(BaseModel):
    project_id: str
    phase_id: Optional[str] = None
    title: str = "Nuevo Diagrama de Flujo"
    description: Optional[str] = ""
    swimlanes: Optional[List[str]] = ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"]
    nodes: Optional[List[Dict[str, Any]]] = []
    edges: Optional[List[Dict[str, Any]]] = []
    viewport: Optional[Dict[str, Any]] = {"x": 0, "y": 0, "zoom": 1}


class DiagramUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    swimlanes: Optional[List[str]] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    viewport: Optional[Dict[str, Any]] = None


class AIGenerateRequest(BaseModel):
    process_description: str
    project_id: Optional[str] = None
    swimlanes: Optional[List[str]] = ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"]


@router.get("/project/{project_id}")
def get_diagrams_by_project(project_id: str, db: Session = Depends(get_db)):
    """Get all diagrams for a project"""
    diagrams = db.query(Diagram).filter(Diagram.project_id == project_id).all()
    return [d.to_dict() for d in diagrams]


@router.get("/{diagram_id}")
def get_diagram(diagram_id: str, db: Session = Depends(get_db)):
    """Get a specific diagram by ID"""
    diagram = db.query(Diagram).filter(Diagram.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")
    return diagram.to_dict()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_diagram(diagram_data: DiagramCreate, db: Session = Depends(get_db)):
    """Create a new diagram"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == diagram_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    diagram = Diagram(
        project_id=diagram_data.project_id,
        phase_id=diagram_data.phase_id,
        title=diagram_data.title,
        description=diagram_data.description,
        swimlanes=json.dumps(diagram_data.swimlanes),
        nodes=json.dumps(diagram_data.nodes),
        edges=json.dumps(diagram_data.edges),
        viewport=json.dumps(diagram_data.viewport)
    )
    db.add(diagram)
    db.commit()
    db.refresh(diagram)
    return diagram.to_dict()


@router.put("/{diagram_id}")
def update_diagram(diagram_id: str, diagram_data: DiagramUpdate, db: Session = Depends(get_db)):
    """Update a diagram"""
    diagram = db.query(Diagram).filter(Diagram.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if diagram_data.title is not None:
        diagram.title = diagram_data.title
    if diagram_data.description is not None:
        diagram.description = diagram_data.description
    if diagram_data.swimlanes is not None:
        diagram.swimlanes = json.dumps(diagram_data.swimlanes)
    if diagram_data.nodes is not None:
        diagram.nodes = json.dumps(diagram_data.nodes)
    if diagram_data.edges is not None:
        diagram.edges = json.dumps(diagram_data.edges)
    if diagram_data.viewport is not None:
        diagram.viewport = json.dumps(diagram_data.viewport)

    db.commit()
    db.refresh(diagram)
    return diagram.to_dict()


@router.delete("/{diagram_id}")
def delete_diagram(diagram_id: str, db: Session = Depends(get_db)):
    """Delete a diagram"""
    diagram = db.query(Diagram).filter(Diagram.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")
    db.delete(diagram)
    db.commit()
    return {"message": "Diagrama eliminado exitosamente"}


@router.post("/generate-ai")
def generate_diagram_with_ai(request: AIGenerateRequest, db: Session = Depends(get_db)):
    """Generate process diagram JSON using Gemini AI based on official symbology"""
    api_key = get_gemini_api_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key no configurada")

    try:
        gemini = GeminiService(api_key=api_key)
        
        prompt = f"""Analiza la siguiente descripción de un proceso operativo y genera la estructura completa del diagrama de flujo en JSON siguiendo la SIMBOLOGÍA OFICIAL.

PROCESO OPERATIVO:
```
{request.process_description}
```

SWIMLANES DISPONIBLES:
{json.dumps(request.swimlanes, ensure_ascii=False)}

REGLAS DE SIMBOLOGÍA OFICIAL:
1. 'node_start': Cápsula de Inicio (1 por diagrama en la columna Input o Actor 1).
2. 'node_end': Cápsula de Fin (en la columna Output o Actor 1).
3. 'node_activity': Tarea principal en la columna correspondiente. Debe incluir:
   - 'activity_number': Número de paso secuencial (1, 2, 3...)
   - 'label': Verbo en infinitivo (ej: Enviar solicitud, Verificar datos)
4. 'node_decision': Pregunta de decisión ('¿Es válido?', '¿Aprobado?'). Salidas con etiquetas 'Sí' o 'No'.
5. 'node_system': Sistema involucrado (Chronos, Freshdesk, SAP, etc.).
6. 'node_delay': Demora/Tiempo de espera (ej. '5 min', '24 horas').
7. 'node_split_and': Símbolo Y (Paralelo - Actividades simultáneas ⊗).
8. 'node_split_or': Símbolo O (Exclusivo - Opciones alternativas ⊕).
9. 'node_document': Documento (ej. Solicitud SAR, Factura).
10. 'channel_whatsapp', 'channel_freshdesk', 'channel_bria': Canales de comunicación.
11. 'node_automation': Actividad automatizada.

FORMATO DE SALIDA (SOLO JSON VÁLIDO):
{{
  "title": "Nombre corto del Proceso",
  "description": "Resumen ejecutivo del flujo",
  "swimlanes": {json.dumps(request.swimlanes, ensure_ascii=False)},
  "nodes": [
    {{
      "id": "node-1",
      "type": "node_start",
      "label": "Inicio",
      "swimlane": "Input",
      "x": 50,
      "y": 100
    }},
    {{
      "id": "node-2",
      "type": "node_activity",
      "activity_number": 1,
      "label": "Verificar solicitud de reembolso",
      "swimlane": "Actor 1 (ej. Usuario)",
      "attached_system": "Freshdesk",
      "attached_channel": "WhatsApp",
      "x": 250,
      "y": 100
    }},
    {{
      "id": "node-3",
      "type": "node_decision",
      "label": "¿Es monto válido?",
      "swimlane": "Actor 2 (ej. Sistema)",
      "x": 450,
      "y": 100
    }},
    {{
      "id": "node-4",
      "type": "node_end",
      "label": "Fin",
      "swimlane": "Output",
      "x": 650,
      "y": 100
    }}
  ],
  "edges": [
    {{ "id": "e1-2", "source": "node-1", "target": "node-2", "label": "" }},
    {{ "id": "e2-3", "source": "node-2", "target": "node-3", "label": "" }},
    {{ "id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí" }}
  ]
}}
"""
        response_text = gemini.generate_content(prompt)
        
        # Clean JSON codeblock delimiters if present
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        cleaned_text = cleaned_text.strip()

        diagram_data = json.loads(cleaned_text)
        return diagram_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar diagrama con IA: {str(e)}")


class ExportRequest(BaseModel):
    title: str = "Diagrama_TEMIS"
    swimlanes: List[str] = []
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []


@router.post("/export/csv")
def export_diagram_csv(data: ExportRequest):
    """Export shape data and process activities as CSV (Lucidchart format)"""
    import io
    import csv
    from fastapi.responses import StreamingResponse

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID Nodo", "Tipo de Símbolo", "Etiqueta / Verbo Infinitivo", "Swimlane / Rol", "Número Actividad", "Sistema Adjunto", "Canal Adjunto", "Posición X", "Posición Y"])

    for n in data.nodes:
        writer.writerow([
            n.get("id", ""),
            n.get("type", ""),
            n.get("label", ""),
            n.get("swimlane", ""),
            n.get("activity_number", ""),
            n.get("attached_system", ""),
            n.get("attached_channel", ""),
            n.get("x", 0),
            n.get("y", 0)
        ])

    output.seek(0)
    filename = f"{data.title.replace(' ', '_')}_shape_data.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


class NarrativeRequest(BaseModel):
    project_name: str = "Proyecto TEMIS"
    project_purpose: str = ""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    sipoc_rows: Optional[List[Dict[str, Any]]] = None


@router.post("/generate-narrative")
def generate_narrative_endpoint(req: NarrativeRequest):
    """Generate formal process procedure manual and narrative in continuous prose"""
    from backend.services.process_narrative import generate_process_narrative
    try:
        narrative = generate_process_narrative(
            project_name=req.project_name,
            project_purpose=req.project_purpose,
            nodes=req.nodes,
            edges=req.edges,
            sipoc_rows=req.sipoc_rows
        )
        return {"narrative": narrative}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al redactar narrativa: {str(e)}")


class SipocAiRequest(BaseModel):
    project_name: str = "Proceso Operativo"
    project_purpose: str = ""
    existing_rows: Optional[List[Dict[str, Any]]] = []


@router.post("/sipoc/ai-complete")
def complete_sipoc_with_ai(req: SipocAiRequest):
    """Suggest complete SIPOC table rows based on project purpose"""
    api_key = get_gemini_api_key()
    if api_key:
        try:
            from backend.services.gemini_service import GeminiChatService
            gemini = GeminiChatService(api_key=api_key)
            prompt = f"""Eres un experto en Lean Six Sigma y BPMN. Genera las filas de una MATRIZ SIPOC estructurada (Suppliers, Inputs, Process, Outputs, Customers, Requirements) para el siguiente proceso:
NOMBRE: {req.project_name}
PROPÓSITO: {req.project_purpose}

Devuelve un array JSON con 5 a 8 filas estructuradas con estas llaves exactas:
[
  {{
    "id": "1",
    "step_num": "1.0",
    "provider": "Nombre del Proveedor (ej. Cliente, Agente)",
    "input": "Entrada / Recurso (ej. Folio, Llamada, Documento)",
    "step": "1.0 [Verbo] Acción a ejecutar",
    "output": "Salida resultante (ej. Registro creado, Ticket)",
    "customer": "Cliente receptor (ej. Operador, Chronos)",
    "requirements": "Requisito / SLA (ej. < 2 min, Datos completos)"
  }}
]

Devuelve ÚNICAMENTE el array JSON válido."""
            res = gemini.get_structured_response(prompt, max_tokens=3000)
            cleaned = res.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            rows = json.loads(cleaned.strip())
            return {"rows": rows}
        except Exception:
            pass

    # Fallback template
    rows = [
        {"id": "1", "step_num": "1.0", "provider": "Usuario Final", "input": "Solicitud vía WhatsApp", "step": "1.0 Recepción y captura de solicitud", "output": "Ticket en Freshdesk", "customer": "Agente Operativo", "requirements": "Folio y teléfono válidos"},
        {"id": "2", "step_num": "2.0", "provider": "Agente Operativo", "input": "Ticket en Freshdesk", "step": "2.0 Validación de datos y estatus en Chronos", "output": "Estatus confirmado", "customer": "Sistema Chronos", "requirements": "Respuesta < 30 seg"},
        {"id": "3", "step_num": "3.0", "provider": "Sistema Chronos", "input": "Estatus confirmado", "step": "3.0 Dictamen y resolución del caso", "output": "Resolución / Reembolso", "customer": "Usuario Final", "requirements": "Aprobación conforme a política"},
        {"id": "4", "step_num": "4.0", "provider": "Agente Operativo", "input": "Resolución emitida", "step": "4.0 Notificación y encuesta de satisfacción", "output": "Cierre de conversación", "customer": "Usuario Final", "requirements": "Confirmación de recibido"}
    ]
    return {"rows": rows}


class SipocExportRequest(BaseModel):
    project_name: str = "Proyecto_TEMIS"
    project_purpose: str = ""
    customer_requirements: str = ""
    sipoc_rows: List[Dict[str, Any]] = []


@router.post("/sipoc/export-excel")
def export_sipoc_excel_endpoint(req: SipocExportRequest):
    """Download styled professional Six Sigma SIPOC Excel workbook"""
    from backend.services.sipoc_exporter import export_sipoc_to_excel
    from fastapi.responses import StreamingResponse
    try:
        excel_stream = export_sipoc_to_excel(
            project_name=req.project_name,
            project_purpose=req.project_purpose,
            sipoc_rows=req.sipoc_rows,
            customer_requirements=req.customer_requirements
        )
        safe_name = req.project_name.replace(' ', '_')
        return StreamingResponse(
            excel_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=Matriz_SIPOC_{safe_name}.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar Excel SIPOC: {str(e)}")


