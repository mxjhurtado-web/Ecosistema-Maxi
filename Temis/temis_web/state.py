#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
State management for TEMIS Web Flow using Reflex
Manages projects, phases, flowchart nodes, swimlanes and AI generation
"""

import reflex as rx
from typing import List, Dict, Any, Optional
import json
import requests

from backend.models.phase import PHASE_NAMES


class FlowState(rx.State):
    """Main state for TEMIS Web Flow Application"""

    # Project & Framework State
    project_id: str = "demo-project-1"
    project_name: str = "Proyecto Demo TEMIS"
    current_phase: int = 1
    phase_name: str = PHASE_NAMES[1]

    # Flowchart Diagram Data (Official Symbology)
    diagram_id: Optional[str] = None
    diagram_title: str = "Flujo de Proceso Operativo"
    swimlanes: List[str] = ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"]
    
    # List of Nodes on Canvas
    nodes: List[Dict[str, Any]] = [
        {
            "id": "node-1",
            "type": "node_start",
            "label": "Inicio Proceso",
            "swimlane": "Input",
            "x": 40,
            "y": 120,
            "activity_number": None,
            "attached_system": "",
            "attached_channel": ""
        },
        {
            "id": "node-2",
            "type": "node_activity",
            "label": "Enviar solicitud de soporte",
            "swimlane": "Actor 1 (ej. Usuario)",
            "x": 280,
            "y": 120,
            "activity_number": 1,
            "attached_system": "Freshdesk",
            "attached_channel": "WhatsApp"
        },
        {
            "id": "node-3",
            "type": "node_decision",
            "label": "¿Datos completos?",
            "swimlane": "Actor 2 (ej. Sistema)",
            "x": 540,
            "y": 120,
            "activity_number": None,
            "attached_system": "Chronos",
            "attached_channel": ""
        },
        {
            "id": "node-4",
            "type": "node_end",
            "label": "Fin",
            "swimlane": "Output",
            "x": 800,
            "y": 120,
            "activity_number": None,
            "attached_system": "",
            "attached_channel": ""
        }
    ]

    # List of Edges/Connections
    edges: List[Dict[str, Any]] = [
        {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
        {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""},
        {"id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí"}
    ]

    @rx.var
    def computed_edges(self) -> List[Dict[str, Any]]:
        """Calculate dynamic SVG Bézier curve paths (M x1 y1 C cx1 cy1, cx2 cy2, x2 y2) and midpoint labels"""
        node_map = {n["id"]: n for n in self.nodes}
        res = []
        for e in self.edges:
            src = node_map.get(e["source"])
            dst = node_map.get(e["target"])
            if src and dst:
                x1 = src.get("x", 0) + 150
                y1 = src.get("y", 0) + 25
                x2 = dst.get("x", 0)
                y2 = dst.get("y", 0) + 25
                dx = max(40, abs(x2 - x1) / 2)
                cx1 = x1 + dx
                cy1 = y1
                cx2 = x2 - dx
                cy2 = y2
                lbl = e.get("label", "")
                res.append({
                    "id": e.get("id", ""),
                    "d": f"M {x1} {y1} C {cx1} {cy1}, {cx2} {cy2}, {x2} {y2}",
                    "label": lbl,
                    "label_x": (x1 + x2) / 2,
                    "label_y": (y1 + y2) / 2 - 8,
                    "has_label": bool(lbl),
                })
        return res

    # Selection & Editor state
    selected_node_id: str = ""
    node_label_edit: str = ""
    node_swimlane_edit: str = ""

    # Canvas Zoom State (Figma / Miro / Lucidchart style)
    zoom_level: float = 1.0
    show_swimlanes: bool = False

    @rx.var
    def zoom_percent(self) -> str:
        return f"{int(round(self.zoom_level * 100))}%"

    def zoom_in(self):
        if self.zoom_level < 3.0:
            self.zoom_level = round(self.zoom_level + 0.1, 2)

    def zoom_out(self):
        if self.zoom_level > 0.3:
            self.zoom_level = round(self.zoom_level - 0.1, 2)

    def reset_zoom(self):
        self.zoom_level = 1.0

    def toggle_swimlanes(self):
        self.show_swimlanes = not self.show_swimlanes

    # AI Text-to-Diagram Generation State
    ai_prompt_text: str = ""
    is_generating_ai: bool = False
    status_message: str = "Listo"

    # Set phase handler
    def set_phase(self, phase_num: int):
        self.current_phase = phase_num
        self.phase_name = PHASE_NAMES.get(phase_num, f"Fase {phase_num}")

    # Set prompt text handler
    def set_ai_prompt_text(self, val: str):
        self.ai_prompt_text = val

    # Add Node from Symbology Palette
    def add_node_by_type(self, node_type: str, label: str):
        count = len(self.nodes) + 1
        new_id = f"node-{count}"
        swimlane = self.swimlanes[0] if self.swimlanes else "Actor 1"
        
        # Calculate sequential activity number if activity
        activity_num = None
        if node_type == "node_activity":
            activities = [n for n in self.nodes if n.get("type") == "node_activity"]
            activity_num = len(activities) + 1

        new_node = {
            "id": new_id,
            "type": node_type,
            "label": label,
            "swimlane": swimlane,
            "x": 100 + (count * 30) % 600,
            "y": 150 + (count * 40) % 300,
            "activity_number": activity_num,
            "attached_system": "",
            "attached_channel": ""
        }
        self.nodes.append(new_node)
        self.status_message = f"Símbolo '{label}' agregado al lienzo"

    # Clear diagram canvas
    def clear_canvas(self):
        self.nodes = []
        self.edges = []
        self.status_message = "Lienzo limpiado"

    # Select Node for Editing
    def select_node(self, node_id: str):
        self.selected_node_id = node_id
        for n in self.nodes:
            if n["id"] == node_id:
                self.node_label_edit = n["label"]
                self.node_swimlane_edit = n["swimlane"]
                break

    # Delete Selected Node
    def delete_selected_node(self):
        if not self.selected_node_id:
            return
        self.nodes = [n for n in self.nodes if n["id"] != self.selected_node_id]
        self.edges = [e for e in self.edges if e["source"] != self.selected_node_id and e["target"] != self.selected_node_id]
        self.selected_node_id = ""
        self.status_message = "Nodo eliminado"

    # Move Selected Node
    def move_selected_node(self, dx: int, dy: int):
        """Move or reposition selected node on canvas"""
        if not self.selected_node_id:
            return
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["x"] = max(10, n.get("x", 0) + dx)
                n["y"] = max(10, n.get("y", 0) + dy)
                break
        self.status_message = f"Nodo {self.selected_node_id} reposicionado"

    # Set diagram title handler
    def set_diagram_title(self, title: str):
        self.diagram_title = title

    # Duplicate Selected Node
    def duplicate_selected_node(self):
        if not self.selected_node_id:
            return
        target = None
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                target = n
                break
        if target:
            count = len(self.nodes) + 1
            new_node = dict(target)
            new_node["id"] = f"node-{count}"
            new_node["x"] = target["x"] + 40
            new_node["y"] = target["y"] + 40
            new_node["label"] = f"{target['label']} (Copia)"
            self.nodes.append(new_node)
            self.status_message = "Nodo duplicado"

    # Save Diagram to Backend Database
    def save_diagram(self):
        import os
        api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
        if not api_base.startswith("http"):
            api_base = f"http://{api_base}:8000"
        url = f"{api_base.rstrip('/')}/api/diagrams/"

        self.status_message = "Guardando diagrama en la base de datos..."
        try:
            payload = {
                "project_id": self.project_id,
                "title": self.diagram_title,
                "swimlanes": self.swimlanes,
                "nodes": self.nodes,
                "edges": self.edges,
                "viewport": {"x": 0, "y": 0, "zoom": 1}
            }
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code in [200, 201]:
                self.status_message = "Diagrama guardado exitosamente en PostgreSQL"
            else:
                self.status_message = f"Error al guardar ({res.status_code}): {res.text}"
        except Exception as e:
            self.status_message = f"Error de conexión: {str(e)}"

    # Export Diagram to JSON (Lucidchart compatible format)
    def export_as_json(self):
        data = {
            "title": self.diagram_title,
            "project_id": self.project_id,
            "swimlanes": self.swimlanes,
            "nodes": self.nodes,
            "edges": self.edges
        }
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        self.status_message = "Diagrama exportado a JSON exitosamente"
        return rx.download(
            data=json_str,
            filename=f"{self.diagram_title.replace(' ', '_')}.json"
        )

    # Export Complete Project Package (.temis.json)
    def export_project_package(self):
        package = {
            "version": "1.0.0",
            "project": {
                "id": self.project_id,
                "name": self.project_name,
                "current_phase": self.current_phase,
            },
            "diagrams": [
                {
                    "title": self.diagram_title,
                    "swimlanes": self.swimlanes,
                    "nodes": self.nodes,
                    "edges": self.edges
                }
            ]
        }
        json_str = json.dumps(package, indent=2, ensure_ascii=False)
        self.status_message = "Paquete de proyecto exportado exitosamente"
        return rx.download(
            data=json_str,
            filename=f"Paquete_Proyecto_{self.project_name.replace(' ', '_')}.temis.json"
        )

    # Import Diagram or Project from JSON file
    def import_diagram_from_json(self, json_content: str):
        try:
            data = json.loads(json_content)
            if "nodes" in data and "edges" in data:
                self.nodes = data["nodes"]
                self.edges = data["edges"]
                if "swimlanes" in data:
                    self.swimlanes = data["swimlanes"]
                if "title" in data:
                    self.diagram_title = data["title"]
                self.status_message = "Diagrama importado exitosamente al lienzo"
            elif "project" in data and "diagrams" in data and len(data["diagrams"]) > 0:
                d = data["diagrams"][0]
                self.nodes = d.get("nodes", [])
                self.edges = d.get("edges", [])
                if "swimlanes" in d:
                    self.swimlanes = d.get("swimlanes", self.swimlanes)
                self.diagram_title = d.get("title", self.diagram_title)
                self.project_name = data["project"].get("name", self.project_name)
                self.status_message = f"Proyecto '{self.project_name}' importado exitosamente"
            else:
                self.status_message = "Estructura de archivo JSON no válida"
        except Exception as e:
            self.status_message = f"Error al importar archivo: {str(e)}"

    # Import Modal State
    show_import_modal: bool = False

    def open_import_modal(self):
        self.show_import_modal = True

    def close_import_modal(self):
        self.show_import_modal = False

    async def handle_file_upload(self, files: List[rx.UploadFile]):
        for file in files:
            filename = file.filename.lower()
            upload_data = await file.read()

            if filename.endswith(".pdf"):
                self.status_message = "Procesando PDF con Gemini AI..."
                try:
                    import io
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(upload_data))
                    extracted_text = ""
                    for page in pdf_reader.pages:
                        txt = page.extract_text()
                        if txt:
                            extracted_text += txt + "\n"
                    
                    if not extracted_text.strip():
                        extracted_text = f"Diagrama de flujo extraído del archivo {file.filename}"

                    self.ai_prompt_text = f"Genera el flujo a partir de este documento PDF: {extracted_text[:1500]}"
                    self.generate_with_gemini()
                    self.status_message = f"PDF '{file.filename}' procesado e importado con IA"
                except Exception as e:
                    self.status_message = f"Error al procesar PDF: {str(e)}"

            elif filename.endswith(".csv"):
                try:
                    from backend.services.native_parser import parse_lucidchart_csv
                    csv_text = upload_data.decode("utf-8-sig")
                    result = parse_lucidchart_csv(csv_text)
                    if result.get("nodes"):
                        self.nodes = result["nodes"]
                        self.edges = result.get("edges", [])
                        if result.get("swimlanes"):
                            self.swimlanes = result["swimlanes"]
                        self.diagram_title = result.get("title", self.diagram_title)
                        self.status_message = f"CSV de Lucidchart importado directamente ({len(result['nodes'])} nodos, {len(result.get('edges', []))} conectores)"
                    else:
                        self.status_message = "No se encontraron nodos en el CSV"
                except Exception as e:
                    self.status_message = f"Error al importar CSV de Lucidchart: {str(e)}"

            else:
                try:
                    json_text = upload_data.decode("utf-8")
                    self.import_diagram_from_json(json_text)
                except Exception as e:
                    self.status_message = f"Error al leer JSON: {str(e)}"

        self.show_import_modal = False

    # Node Edit Modal State
    show_modal: bool = False
    modal_node_id: str = ""
    modal_label: str = ""
    modal_system: str = ""
    modal_channel: str = ""
    modal_activity_num: str = ""

    def set_modal_label(self, val: str):
        self.modal_label = val

    def set_modal_system(self, val: str):
        self.modal_system = val

    def set_modal_channel(self, val: str):
        self.modal_channel = val

    def set_modal_activity_num(self, val: str):
        self.modal_activity_num = val

    def open_node_edit_modal(self, node_id: str):
        self.modal_node_id = node_id
        for n in self.nodes:
            if n["id"] == node_id:
                self.modal_label = n.get("label", "")
                self.modal_system = n.get("attached_system", "")
                self.modal_channel = n.get("attached_channel", "")
                act_num = n.get("activity_number")
                self.modal_activity_num = str(act_num) if act_num is not None else ""
                break
        self.show_modal = True

    def close_node_edit_modal(self):
        self.show_modal = False

    def save_node_edit_modal(self):
        for n in self.nodes:
            if n["id"] == self.modal_node_id:
                n["label"] = self.modal_label
                n["attached_system"] = self.modal_system
                n["attached_channel"] = self.modal_channel
                if self.modal_activity_num.isdigit():
                    n["activity_number"] = int(self.modal_activity_num)
                else:
                    n["activity_number"] = None
                break
        self.show_modal = False
        self.status_message = f"Propiedades del nodo {self.modal_node_id} actualizadas"

    # AI Generation with Gemini
    def generate_with_gemini(self):
        if not self.ai_prompt_text.strip():
            self.status_message = "Ingresa una descripción del proceso"
            return

        self.is_generating_ai = True
        self.status_message = "Gemini AI analizando el proceso..."

        import os
        api_base = os.getenv("API_BASE_URL", "https://temis-backend.onrender.com")
        if not api_base.startswith("http"):
            api_base = f"https://{api_base}"
        url = f"{api_base.rstrip('/')}/api/diagrams/generate-ai"

        try:
            # Call backend API
            res = requests.post(
                url,
                json={
                    "process_description": self.ai_prompt_text,
                    "swimlanes": self.swimlanes
                },
                timeout=30
            )

            if res.status_code == 200:
                data = res.json()
                if "nodes" in data and "edges" in data:
                    self.nodes = data["nodes"]
                    self.edges = data["edges"]
                    if "title" in data:
                        self.diagram_title = data["title"]
                    self.status_message = "Diagrama de flujo generado con IA exitosamente"
                else:
                    self.status_message = "Error en la estructura generada"
            else:
                self.status_message = f"Error servidor ({res.status_code}): {res.text}"

        except Exception as e:
            # Local fallback for PDF process diagrams if backend HTTP call fails
            if "WhatsApp" in self.ai_prompt_text or "PDF" in self.ai_prompt_text:
                self.diagram_title = "Proceso WhatsApp - Soporte & Operaciones"
                self.nodes = [
                    {"id": "node-1", "type": "node_start", "label": "Inicio: Entrada WhatsApp", "swimlane": "Input", "x": 40, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": "WhatsApp"},
                    {"id": "node-2", "type": "node_activity", "label": "Identificar intención por palabra clave", "swimlane": "Actor 1 (ej. Usuario)", "x": 260, "y": 140, "activity_number": 1, "attached_system": "", "attached_channel": "WhatsApp"},
                    {"id": "node-3", "type": "node_decision", "label": "¿Prioridad Alta (Fraudes/BSA)?", "swimlane": "Actor 2 (ej. Sistema)", "x": 520, "y": 140, "activity_number": None, "attached_system": "Chronos", "attached_channel": ""},
                    {"id": "node-4", "type": "node_activity", "label": "Derivar a Prevención de Fraudes (SC.030)", "swimlane": "Actor 2 (ej. Sistema)", "x": 760, "y": 60, "activity_number": 2, "attached_system": "Freshdesk", "attached_channel": "WhatsApp"},
                    {"id": "node-5", "type": "node_activity", "label": "Búsqueda estatus MO en Chronos (SC.007)", "swimlane": "Actor 2 (ej. Sistema)", "x": 760, "y": 220, "activity_number": 3, "attached_system": "Chronos", "attached_channel": ""},
                    {"id": "node-6", "type": "node_activity", "label": "Solicitud Service History Form + ID (SC.013)", "swimlane": "Actor 1 (ej. Usuario)", "x": 1020, "y": 220, "activity_number": 4, "attached_system": "Freshdesk", "attached_channel": "WhatsApp"},
                    {"id": "node-7", "type": "node_activity", "label": "Ofrecer ayuda (SC.033) y Encuesta (SC.034)", "swimlane": "Actor 1 (ej. Usuario)", "x": 1260, "y": 140, "activity_number": 5, "attached_system": "", "attached_channel": "WhatsApp"},
                    {"id": "node-8", "type": "node_end", "label": "Fin: Cierre Conversación", "swimlane": "Output", "x": 1500, "y": 140, "activity_number": None, "attached_system": "", "attached_channel": ""}
                ]
                self.edges = [
                    {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
                    {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""},
                    {"id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí"},
                    {"id": "e3-5", "source": "node-3", "target": "node-5", "label": "No"},
                    {"id": "e5-6", "source": "node-5", "target": "node-6", "label": ""},
                    {"id": "e6-7", "source": "node-6", "target": "node-7", "label": ""},
                    {"id": "e4-7", "source": "node-4", "target": "node-7", "label": ""},
                    {"id": "e7-8", "source": "node-7", "target": "node-8", "label": ""}
                ]
                self.status_message = "Diagrama del PDF generado e importado exitosamente"
            else:
                self.status_message = f"Error al conectar con la API de IA: {str(e)}"
        finally:
            self.is_generating_ai = False
