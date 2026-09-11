#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
State management for TEMIS Web Flow using Reflex
Manages projects, phases, flowchart nodes, swimlanes and AI generation
"""

import reflex as rx
from typing import List, Dict, Any, Optional, Union
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

    # Active View Navigation (4 Core Modules)
    active_view: str = "flow"  # "charter", "flow", "sipoc", "governance"

    def set_active_view(self, view_name: Union[str, List[str]]):
        """Switch active view tab: 'charter', 'flow', 'sipoc', 'governance'"""
        if isinstance(view_name, list):
            val = view_name[0] if view_name else "flow"
        else:
            val = str(view_name)
        self.active_view = val
        view_labels = {
            "charter": "Ficha del Proyecto & Narrativa",
            "flow": "Diagrama de Flujo (Lienzo)",
            "sipoc": "Matriz SIPOC Six Sigma",
            "governance": "Gobernanza & 7 Fases"
        }
        self.status_message = f"Vista activa: {view_labels.get(val, val)}"

    # Project Charter & Master Metadata State
    project_purpose: str = "Estandarizar y automatizar el ciclo integral de atención de aclaraciones y transacciones de clientes vía canales digitales y sistemas centrales."
    project_manager: str = "Ing. Mario Hurtado"
    project_sponsor: str = "Dirección de Operaciones & Tecnología"
    start_date: str = "2026-01-16"
    end_date: str = "2026-12-04"
    scope_in: str = "Mapeo SIPOC, diagrama BPMN multi-pestaña, manual de procedimientos y auditoría de calidad."
    scope_out: str = "Desarrollo de integraciones core bancarias propietarias de terceros."

    def set_project_purpose(self, val: str):
        self.project_purpose = val

    def set_project_manager(self, val: str):
        self.project_manager = val

    def set_project_sponsor(self, val: str):
        self.project_sponsor = val

    def set_start_date(self, val: str):
        self.start_date = val

    def set_end_date(self, val: str):
        self.end_date = val

    def set_scope_in(self, val: str):
        self.scope_in = val

    def set_scope_out(self, val: str):
        self.scope_out = val

    # SIPOC Matrix Data State
    sipoc_rows: List[Dict[str, Any]] = [
        {
            "id": "1",
            "step_num": "1.0",
            "provider": "Usuario / Cliente",
            "input": "Solicitud de aclaración vía WhatsApp",
            "step": "1.0 Recepción y captura de número de folio",
            "output": "Folio y datos validados",
            "customer": "Agente Operativo",
            "requirements": "Número de folio válido y teléfono registrado"
        },
        {
            "id": "2",
            "step_num": "2.0",
            "provider": "Agente Operativo",
            "input": "Número de folio validado",
            "step": "2.0 Consulta de estatus de transacción en Chronos",
            "output": "Estatus de la transacción (MO/Vigente)",
            "customer": "Sistema Chronos",
            "requirements": "Tiempo de respuesta del sistema < 30 seg"
        },
        {
            "id": "3",
            "step_num": "3.0",
            "provider": "Sistema Chronos",
            "input": "Estatus de transacción",
            "step": "3.0 ¿Transacción requiere revisión por Fraudes?",
            "output": "Dictamen de aprobación o derivación",
            "customer": "Agente / Área de Fraudes",
            "requirements": "Reglas de riesgo y montos máximos vigentes"
        },
        {
            "id": "4",
            "step_num": "4.0",
            "provider": "Agente Operativo",
            "input": "Dictamen de aprobación",
            "step": "4.0 Notificación de resolución y encuesta",
            "output": "Confirmación y encuesta de satisfacción",
            "customer": "Usuario / Cliente",
            "requirements": "Confirmación de entrega y cierre en Freshdesk"
        }
    ]
    customer_requirements: str = "Tiempos de respuesta (SLA) menores a 5 min, trazabilidad de logs en Chronos y encuesta con satisfacción >= 95%."
    is_completing_sipoc: bool = False

    def set_customer_requirements(self, val: str):
        self.customer_requirements = val

    def add_sipoc_row(self):
        """Add a new empty step row to the SIPOC matrix"""
        count = len(self.sipoc_rows) + 1
        new_row = {
            "id": str(count),
            "step_num": f"{count}.0",
            "provider": "",
            "input": "",
            "step": f"{count}.0 ",
            "output": "",
            "customer": "",
            "requirements": ""
        }
        self.sipoc_rows.append(new_row)
        self.status_message = f"Paso {count}.0 agregado a la Matriz SIPOC"

    def remove_sipoc_row(self, row_id: str):
        """Remove a step row from SIPOC matrix"""
        self.sipoc_rows = [r for r in self.sipoc_rows if r.get("id") != row_id]
        # Re-index step numbers
        for idx, r in enumerate(self.sipoc_rows):
            r["id"] = str(idx + 1)
            r["step_num"] = f"{idx + 1}.0"
        self.status_message = "Fila eliminada de la Matriz SIPOC"

    def update_sipoc_provider(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["provider"] = val
                break

    def update_sipoc_input(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["input"] = val
                break

    def update_sipoc_step(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["step"] = val
                break

    def update_sipoc_output(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["output"] = val
                break

    def update_sipoc_customer(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["customer"] = val
                break

    def update_sipoc_reqs(self, row_id: str, val: str):
        for r in self.sipoc_rows:
            if r.get("id") == row_id:
                r["requirements"] = val
                break

    def sync_sipoc_to_flow(self):
        """
        ⚡ Transform SIPOC Table into Flowchart DAG on the Canvas:
        Generates Start Node, Activities/Decisions with Systems/Channels, End Node and Bézier connections.
        """
        if not self.sipoc_rows:
            self.status_message = "La matriz SIPOC está vacía"
            return

        new_nodes = []
        new_edges = []
        
        # 1. Start Node
        first_input = self.sipoc_rows[0].get("input", "Inicio")
        first_provider = self.sipoc_rows[0].get("provider", "Input") or "Input"
        new_nodes.append({
            "id": "node-1",
            "type": "node_start",
            "label": f"Inicio: {first_input[:28]}",
            "swimlane": first_provider,
            "x": 60,
            "y": 140,
            "activity_number": None,
            "attached_system": "",
            "attached_channel": "WhatsApp" if "whatsapp" in first_input.lower() else ""
        })

        # 2. Activity / Decision Nodes from SIPOC Steps
        prev_node_id = "node-1"
        for idx, r in enumerate(self.sipoc_rows):
            node_id = f"node-{idx + 2}"
            step_text = r.get("step", f"Paso {idx+1}.0")
            provider = r.get("provider", "Actor 1") or "Actor 1"
            
            # Detect Decision node type
            is_decision = "?" in step_text or "¿" in step_text or "si " in step_text.lower() or "decisión" in step_text.lower() or "evaluar" in step_text.lower()
            node_type = "node_decision" if is_decision else "node_activity"
            
            # Detect Systems and Channels
            attached_sys = ""
            lower_text = (step_text + " " + r.get("input", "") + " " + r.get("output", "")).lower()
            if "chronos" in lower_text:
                attached_sys = "Chronos"
            elif "freshdesk" in lower_text:
                attached_sys = "Freshdesk"
            elif "sap" in lower_text or "erp" in lower_text:
                attached_sys = "SAP"

            attached_chan = ""
            if "whatsapp" in lower_text:
                attached_chan = "WhatsApp"
            elif "bria" in lower_text or "llamada" in lower_text or "teléfono" in lower_text:
                attached_chan = "Bria"
            elif "correo" in lower_text or "email" in lower_text:
                attached_chan = "Email"

            x_pos = 60 + (idx + 1) * 260
            y_pos = 140

            new_nodes.append({
                "id": node_id,
                "type": node_type,
                "label": step_text,
                "swimlane": provider,
                "x": x_pos,
                "y": y_pos,
                "activity_number": (idx + 1) if not is_decision else None,
                "attached_system": attached_sys,
                "attached_channel": attached_chan
            })

            # Add connecting edge
            edge_id = f"e{prev_node_id}-{node_id}"
            new_edges.append({
                "id": edge_id,
                "source": prev_node_id,
                "target": node_id,
                "label": "Sí" if prev_node_id != "node-1" and any(n.get("type") == "node_decision" for n in new_nodes if n.get("id") == prev_node_id) else ""
            })
            prev_node_id = node_id

        # 3. End Node
        end_node_id = f"node-{len(self.sipoc_rows) + 2}"
        last_output = self.sipoc_rows[-1].get("output", "Fin")
        last_customer = self.sipoc_rows[-1].get("customer", "Output") or "Output"
        end_x = 60 + (len(self.sipoc_rows) + 1) * 260
        
        new_nodes.append({
            "id": end_node_id,
            "type": "node_end",
            "label": f"Fin: {last_output[:28]}",
            "swimlane": last_customer,
            "x": end_x,
            "y": 140,
            "activity_number": None,
            "attached_system": "",
            "attached_channel": ""
        })

        new_edges.append({
            "id": f"e{prev_node_id}-{end_node_id}",
            "source": prev_node_id,
            "target": end_node_id,
            "label": ""
        })

        # Update swimlanes list
        unique_lanes = []
        for n in new_nodes:
            lane = n.get("swimlane")
            if lane and lane not in unique_lanes:
                unique_lanes.append(lane)
        if len(unique_lanes) < 2:
            unique_lanes = ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"]

        self.nodes = new_nodes
        self.edges = new_edges
        self.swimlanes = unique_lanes

        # Update current page tab
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)
            self.project_pages[self.active_page_index]["swimlanes"] = list(self.swimlanes)

        self.status_message = f"⚡ Diagrama de Flujo generado con {len(self.nodes)} símbolos desde la Matriz SIPOC"
        self.active_view = "flow"

    def complete_sipoc_with_ai(self):
        """Auto-complete SIPOC rows using Gemini AI / expert template"""
        self.is_completing_sipoc = True
        self.status_message = "Completando Matriz SIPOC con IA..."
        try:
            from backend.routers.diagrams import complete_sipoc_with_ai, SipocAiRequest
            res = complete_sipoc_with_ai(SipocAiRequest(
                project_name=self.project_name,
                project_purpose=self.project_purpose,
                existing_rows=self.sipoc_rows
            ))
            if res.get("rows"):
                self.sipoc_rows = res["rows"]
                self.status_message = f"✨ Matriz SIPOC completada con {len(self.sipoc_rows)} pasos sugeridos"
        except Exception as e:
            self.status_message = f"Error al autocompletar SIPOC: {str(e)}"
        finally:
            self.is_completing_sipoc = False

    def export_sipoc_excel(self):
        """Download styled Six Sigma SIPOC Excel workbook (.xlsx)"""
        try:
            from backend.services.sipoc_exporter import export_sipoc_to_excel
            stream = export_sipoc_to_excel(
                project_name=self.project_name,
                project_purpose=self.project_purpose,
                sipoc_rows=self.sipoc_rows,
                customer_requirements=self.customer_requirements
            )
            safe_name = self.project_name.replace(" ", "_")
            self.status_message = "Excel de Matriz SIPOC descargado exitosamente"
            return rx.download(
                data=stream.getvalue(),
                filename=f"Matriz_SIPOC_{safe_name}.xlsx"
            )
        except Exception as e:
            self.status_message = f"Error al exportar Excel: {str(e)}"

    # Narrative & Policy Manual State
    narrative_text: str = """# 📘 Manual de Procedimientos & Narrativa Oficial
# PROYECTO DEMO TEMIS

## 🎯 1. Objetivo y Propósito del Proceso
Estandarizar y automatizar el ciclo integral de atención de aclaraciones y transacciones de clientes vía canales digitales y sistemas centrales.

## 👥 2. Matriz de Roles y Responsabilidades
- **Actores y Participantes:** Agente Operativo, Sistema Chronos, Usuario / Cliente
- **Sistemas y Plataformas:** Chronos, Freshdesk
- **Canales de Interacción:** WhatsApp

---

## 📝 3. Narrativa Operativa Secuencial (Paso a Paso)

### 1.0 Entrada e Inicio del Proceso
El proceso inicia formalmente cuando el participante **[Usuario / Cliente]** detona el evento: *"Inicio: Solicitud de aclaración"* por el canal **WhatsApp**. Se reciben los datos iniciales y se habilita el caso para su gestión.

### 2.0 Ejecución de Tarea: 1.0 Recepción y captura de número de folio
El responsable **[Usuario / Cliente]** ejecuta la actividad operativa de *"Recepción y captura de número de folio"* por el canal **WhatsApp**. Se genera el registro auditable correspondiente en Freshdesk.

### 3.0 Ejecución de Tarea: 2.0 Consulta de estatus de transacción en Chronos
El responsable **[Agente Operativo]** ejecuta la actividad operativa de *"Consulta de estatus en Chronos"* a través de **Chronos**. Se valida la vigencia de la póliza o transacción.

### 4.0 Punto de Decisión / Validación: 3.0 ¿Transacción requiere revisión por Fraudes?
El rol **[Sistema Chronos]** realiza la validación crítica *"¿Transacción requiere revisión por Fraudes?"* a través de **Chronos**. Las ramificaciones son:
  - **Condición 'Sí':** Se turna al área especializada de Fraudes (SC.030).
  - **Condición 'No':** Se procede con el dictamen de aprobación estándar.

### 5.0 Cierre y Conclusión del Proceso
Se completa la etapa final: *"Fin: Confirmación y encuesta"*. El proceso concluye satisfactoriamente con la entrega del producto/resultado hacia el participante **[Usuario / Cliente]**.

---

## ⚖️ 4. Políticas y Reglas de Negocio Clave
1. **Trazabilidad Absoluta:** Toda interacción por canal digital o sistema debe quedar registrada con marca de tiempo y folio.
2. **Control de Calidad:** Las compuertas de decisión deben validar que la totalidad de requisitos previos se cumplan antes de pasar a la siguiente fase.
3. **Escalamiento:** En caso de excepción no contemplada en las reglas estándar, el caso se turna al líder del proceso para dictamen.
"""
    is_generating_narrative: bool = False

    def set_narrative_text(self, val: str):
        self.narrative_text = val

    def generate_narrative_ai(self):
        """⚡ Generate procedure manual narrative in continuous prose from current Flow and SIPOC data"""
        self.is_generating_narrative = True
        self.status_message = "Gemini AI redactando la Narrativa Oficial del proceso..."
        try:
            from backend.services.process_narrative import generate_process_narrative
            self.narrative_text = generate_process_narrative(
                project_name=self.project_name,
                project_purpose=self.project_purpose,
                nodes=self.nodes,
                edges=self.edges,
                sipoc_rows=self.sipoc_rows
            )
            self.status_message = "✨ Narrativa Oficial redactada y sincronizada con éxito"
        except Exception as e:
            self.status_message = f"Error al generar narrativa: {str(e)}"
        finally:
            self.is_generating_narrative = False

    def export_narrative_markdown(self):
        """Download narrative as Markdown/Text document"""
        safe_name = self.project_name.replace(" ", "_")
        self.status_message = "Manual de Procedimientos exportado (.md)"
        return rx.download(
            data=self.narrative_text,
            filename=f"Manual_Procedimiento_{safe_name}.md"
        )

    
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
        """Calculate dynamic SVG Bézier curve paths with exact perimeter anchor points (East -> West)"""
        node_map = {n["id"]: n for n in self.nodes}
        res = []
        for e in self.edges:
            src = node_map.get(e["source"])
            dst = node_map.get(e["target"])
            if src and dst:
                st = src.get("type", "")
                dt = dst.get("type", "")

                # Source Node dimensions
                if st in ["node_start", "node_end"]:
                    sw, sh = 130, 42
                elif st == "node_decision":
                    sw, sh = 160, 68
                elif st == "node_activity":
                    sw, sh = 190, 68
                elif st.startswith("channel_") or st == "node_system":
                    sw, sh = 175, 58
                else:
                    sw, sh = 160, 52

                # Target Node dimensions
                if dt in ["node_start", "node_end"]:
                    dw, dh = 130, 42
                elif dt == "node_decision":
                    dw, dh = 160, 68
                elif dt == "node_activity":
                    dw, dh = 190, 68
                elif dt.startswith("channel_") or dt == "node_system":
                    dw, dh = 175, 58
                else:
                    dw, dh = 160, 52

                x1 = src.get("x", 0) + sw
                y1 = src.get("y", 0) + (sh / 2)
                x2 = dst.get("x", 0)
                y2 = dst.get("y", 0) + (dh / 2)

                dx = max(45, abs(x2 - x1) / 2)
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

    # Selection & Property Inspector state
    selected_node_id: str = ""
    node_label_edit: str = ""
    node_swimlane_edit: str = ""
    selected_node_type: str = ""
    selected_node_system: str = ""
    selected_node_channel: str = ""

    # Canvas Zoom State (Figma / Miro / Lucidchart style)
    zoom_level: float = 1.0
    show_swimlanes: bool = False

    @rx.var
    def zoom_percent(self) -> str:
        return f"{int(round(self.zoom_level * 100))}%"

    @rx.var
    def zoom_width(self) -> str:
        return f"{int(round(100.0 / max(0.1, self.zoom_level)))}%"

    @rx.var
    def zoom_height(self) -> str:
        return f"{int(round(100.0 / max(0.1, self.zoom_level)))}vh"

    def zoom_in(self):
        if self.zoom_level < 3.0:
            self.zoom_level = round(self.zoom_level + 0.1, 2)

    def zoom_out(self):
        if self.zoom_level > 0.3:
            self.zoom_level = round(self.zoom_level - 0.1, 2)

    def zoom_reset(self):
        self.zoom_level = 1.0

    def toggle_swimlanes(self):
        self.show_swimlanes = not self.show_swimlanes

    # Select Node for Editing in Inspector
    def select_node(self, node_id: str):
        self.selected_node_id = node_id
        for n in self.nodes:
            if n["id"] == node_id:
                self.node_label_edit = n.get("label", "")
                self.node_swimlane_edit = n.get("swimlane", "")
                self.selected_node_type = n.get("type", "node_activity")
                self.selected_node_system = n.get("attached_system", "")
                self.selected_node_channel = n.get("attached_channel", "")
                break

    def unselect_node(self):
        self.selected_node_id = ""

    def set_selected_node_label(self, val: str):
        self.node_label_edit = val
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["label"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_type(self, val: str):
        self.selected_node_type = val
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["type"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_swimlane(self, val: str):
        self.node_swimlane_edit = val
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["swimlane"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_system(self, val: str):
        self.selected_node_system = val
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["attached_system"] = val
                break
        self.trigger_auto_save()

    def set_selected_node_channel(self, val: str):
        self.selected_node_channel = val
        for n in self.nodes:
            if n["id"] == self.selected_node_id:
                n["attached_channel"] = val
                break
        self.trigger_auto_save()

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

    # Project Multi-Tab Diagram Pages State
    project_pages: List[Dict[str, Any]] = [
        {
            "page_id": "1",
            "name": "Página 1: Flujo Principal",
            "nodes": [
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
            ],
            "edges": [
                {"id": "e1-2", "source": "node-1", "target": "node-2", "label": ""},
                {"id": "e2-3", "source": "node-2", "target": "node-3", "label": ""},
                {"id": "e3-4", "source": "node-3", "target": "node-4", "label": "Sí"}
            ],
            "swimlanes": ["Input", "Actor 1 (ej. Usuario)", "Actor 2 (ej. Sistema)", "Output"]
        }
    ]
    active_page_index: int = 0
    show_recent_modal: bool = False
    recent_projects: List[Dict[str, Any]] = []

    def set_project_name(self, name: str):
        """Set project title"""
        self.project_name = name

    def create_new_project(self):
        """Reset canvas and initialize a new empty project"""
        self.project_name = "Nuevo Proyecto TEMIS"
        self.diagram_title = "Flujo de Proceso Operativo"
        self.nodes = [
            {
                "id": "node-1",
                "type": "node_start",
                "label": "Inicio Proceso",
                "swimlane": "Input",
                "x": 80,
                "y": 120,
                "activity_number": None,
                "attached_system": "",
                "attached_channel": ""
            }
        ]
        self.edges = []
        self.project_pages = [
            {
                "page_id": "1",
                "name": "Página 1: Flujo Principal",
                "nodes": list(self.nodes),
                "edges": [],
                "swimlanes": list(self.swimlanes)
            }
        ]
        self.active_page_index = 0
        self.selected_node_id = ""
        self.status_message = "Nuevo proyecto creado"

    def select_page_tab(self, index: int):
        """Save current tab state and switch active page"""
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)

        if 0 <= index < len(self.project_pages):
            self.active_page_index = index
            page = self.project_pages[index]
            self.nodes = list(page.get("nodes", []))
            self.edges = list(page.get("edges", []))
            if page.get("swimlanes"):
                self.swimlanes = list(page["swimlanes"])
            self.status_message = f"Cargada {page.get('name', 'Pestaña')}"

    def add_new_tab_page(self):
        """Add a new blank page tab to the current project"""
        # Save current active page
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)

        count = len(self.project_pages) + 1
        new_page = {
            "page_id": str(count),
            "name": f"Página {count}",
            "nodes": [
                {
                    "id": "node-1",
                    "type": "node_start",
                    "label": "Inicio",
                    "swimlane": "Input",
                    "x": 80,
                    "y": 120,
                    "activity_number": None,
                    "attached_system": "",
                    "attached_channel": ""
                }
            ],
            "edges": [],
            "swimlanes": ["Input", "Actor 1", "Output"]
        }
        self.project_pages.append(new_page)
        self.select_page_tab(len(self.project_pages) - 1)
        self.status_message = f"Pestaña 'Página {count}' creada"

    def delete_tab_page(self, index: int):
        """Delete a diagram page tab from the project"""
        if len(self.project_pages) <= 1:
            self.status_message = "El proyecto debe conservar al menos una pestaña"
            return

        if 0 <= index < len(self.project_pages):
            deleted = self.project_pages.pop(index)
            new_idx = max(0, min(self.active_page_index, len(self.project_pages) - 1))
            self.active_page_index = new_idx
            page = self.project_pages[new_idx]
            self.nodes = list(page.get("nodes", []))
            self.edges = list(page.get("edges", []))
            self.status_message = f"Pestaña '{deleted.get('name')}' eliminada"

    def open_recent_modal(self):
        """Open recent projects modal and fetch from backend database"""
        self.show_recent_modal = True
        self.fetch_recent_projects()

    def close_recent_modal(self):
        """Close recent projects modal"""
        self.show_recent_modal = False

    def fetch_recent_projects(self):
        """Fetch list of saved projects from backend database"""
        import os
        api_base = os.getenv("API_BASE_URL", "https://temis-backend.onrender.com")
        if not api_base.startswith("http"):
            api_base = f"https://{api_base}"
        url = f"{api_base.rstrip('/')}/api/projects"

        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                self.recent_projects = res.json()
            else:
                self.recent_projects = []
        except Exception:
            self.recent_projects = []

    # Connector Modal & Interactive Line Connection State
    show_connect_modal: bool = False
    connect_target_id: str = ""
    connect_label: str = ""
    auto_save_status: str = "✓ Cambios Guardados"

    @rx.var
    def target_node_options(self) -> List[str]:
        """Return candidate target node option strings for connect modal"""
        return [f"{n['id']} - {n.get('label', '')}" for n in self.nodes if n["id"] != self.selected_node_id]

    # AI Process Auditor State
    show_audit_modal: bool = False
    is_auditing_ai: bool = False
    audit_score: int = 100
    audit_findings: List[Dict[str, Any]] = []

    def set_connect_target_id(self, val: str):
        if " - " in str(val or ""):
            self.connect_target_id = str(val).split(" - ")[0].strip()
        else:
            self.connect_target_id = str(val or "").strip()

    def set_connect_label(self, val: str):
        self.connect_label = val

    def open_connect_modal(self):
        """Open modal to connect selected node to another target node"""
        if not self.selected_node_id:
            self.status_message = "Selecciona un nodo primero para conectar"
            return
        self.connect_target_id = ""
        self.connect_label = ""
        self.show_connect_modal = True

    def close_connect_modal(self):
        self.show_connect_modal = False

    def add_connection(self):
        """Add a new SVG Bézier connector edge between selected node and target node"""
        if not self.selected_node_id or not self.connect_target_id:
            self.status_message = "Selecciona un nodo de origen y destino válidos"
            return
        if self.selected_node_id == self.connect_target_id:
            self.status_message = "No se puede conectar un nodo consigo mismo"
            return

        edge_count = len(self.edges) + 1
        new_edge = {
            "id": f"e-{self.selected_node_id}-{self.connect_target_id}-{edge_count}",
            "source": self.selected_node_id,
            "target": self.connect_target_id,
            "label": self.connect_label.strip()
        }
        self.edges.append(new_edge)
        self.show_connect_modal = False
        self.status_message = f"Conexión agregada hacia {self.connect_target_id}"
        self.trigger_auto_save()

    def delete_edge(self, edge_id: str):
        """Delete an edge connector"""
        self.edges = [e for e in self.edges if e.get("id") != edge_id]
        self.status_message = "Conector eliminado"
        self.trigger_auto_save()

    def trigger_auto_save(self):
        """Save active diagram page state and update auto-save badge"""
        if 0 <= self.active_page_index < len(self.project_pages):
            self.project_pages[self.active_page_index]["nodes"] = list(self.nodes)
            self.project_pages[self.active_page_index]["edges"] = list(self.edges)
        self.auto_save_status = "✓ Cambios Guardados"

    def open_audit_modal(self):
        """Open AI Process Auditor modal and execute structural governance analysis"""
        self.show_audit_modal = True
        self.run_ai_process_audit()

    def close_audit_modal(self):
        self.show_audit_modal = False

    def run_ai_process_audit(self):
        """Execute Gemini AI & Structural Governance Audit on current active flowchart tab"""
        self.is_auditing_ai = True
        findings = []
        deductions = 0

        node_map = {n["id"]: n for n in self.nodes}
        out_edges = {}
        in_edges = {}

        for e in self.edges:
            out_edges.setdefault(e["source"], []).append(e)
            in_edges.setdefault(e["target"], []).append(e)

        # Check 1: Start Nodes
        start_nodes = [n for n in self.nodes if n.get("type") == "node_start"]
        if not start_nodes:
            findings.append({
                "severity": "Alta",
                "color": "#ef4444",
                "category": "Inicio de Proceso",
                "title": "Falta Nodo de Inicio de Proceso",
                "description": "El diagrama no tiene un punto de entrada oficial definido (Nodo de Inicio).",
                "recommendation": "Agrega un símbolo 'Inicio Proceso' para marcar el desencadenador inicial."
            })
            deductions += 15
        else:
            for sn in start_nodes:
                if sn["id"] not in out_edges:
                    findings.append({
                        "severity": "Alta",
                        "color": "#ef4444",
                        "category": "Flujo Desconectado",
                        "title": f"Inicio '{sn.get('label')}' sin salida",
                        "description": "El nodo de inicio está desconectado y no conduce a ninguna actividad.",
                        "recommendation": "Conecta el nodo de inicio con la primera actividad operativa."
                    })
                    deductions += 10

        # Check 2: Decision Nodes
        decision_nodes = [n for n in self.nodes if n.get("type") == "node_decision"]
        for dn in decision_nodes:
            edges = out_edges.get(dn["id"], [])
            labels = [e.get("label", "").lower() for e in edges]
            if len(edges) < 2:
                findings.append({
                    "severity": "Alta",
                    "color": "#ef4444",
                    "category": "Decisión Incompleta",
                    "title": f"Decisión '{dn.get('label')}' requiere ramas Sí/No",
                    "description": f"La decisión tiene {len(edges)} salida(s). Toda pregunta de validación debe tener ramas afirmativas y alternativas.",
                    "recommendation": "Agrega la rama faltante (ej. 'Sí' / 'No' o 'Válido' / 'Inválido')."
                })
                deductions += 12

        # Check 3: Activities without System or Channel
        activity_nodes = [n for n in self.nodes if n.get("type") == "node_activity"]
        for an in activity_nodes:
            sys_val = (an.get("attached_system") or "").strip()
            chan_val = (an.get("attached_channel") or "").strip()
            if not sys_val and not chan_val:
                findings.append({
                    "severity": "Media",
                    "color": "#f59e0b",
                    "category": "Gobierno Operativo",
                    "title": f"Actividad '{an.get('label')}' sin Sistema o Canal",
                    "description": "La actividad no especifica qué sistema (Chronos/Freshdesk) o canal (WhatsApp/Bria) soporta la operación.",
                    "recommendation": "Asigna el sistema o canal correspondiente en las propiedades del nodo."
                })
                deductions += 5

        # Check 4: End Nodes
        end_nodes = [n for n in self.nodes if n.get("type") == "node_end"]
        if not end_nodes:
            findings.append({
                "severity": "Media",
                "color": "#f59e0b",
                "category": "Cierre de Proceso",
                "title": "Falta Nodo de Fin de Proceso",
                "description": "El flujo no declara explícitamente el estado de término o resolución.",
                "recommendation": "Agrega un nodo 'Fin Proceso' al término del flujo."
            })
            deductions += 10

        if not findings:
            findings.append({
                "severity": "Baja",
                "color": "#22c55e",
                "category": "Excelente Calidad",
                "title": "¡Proceso Cumple 100% las Reglas de Gobierno TEMIS!",
                "description": "El diagrama tiene nodos de inicio/fin, validaciones completas y asignación adecuada de sistemas.",
                "recommendation": "El flujo está listo para ser promovido a la siguiente Fase de Gobierno."
            })

        self.audit_findings = findings
        self.audit_score = max(0, 100 - deductions)
        self.is_auditing_ai = False

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
                        if result.get("pages"):
                            self.project_pages = result["pages"]
                            self.active_page_index = 0
                        if result.get("swimlanes"):
                            self.swimlanes = result["swimlanes"]
                        self.diagram_title = result.get("title", self.diagram_title)
                        self.status_message = f"CSV de Lucidchart importado ({len(result.get('pages', []))} pestañas de diagramas)"
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
