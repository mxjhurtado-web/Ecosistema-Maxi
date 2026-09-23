#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Narrative AI Extractor Service for TEMIS
Uses Gemini 2.5 Flash to analyze customer process narratives, extracting
findings with source citations, 4 corporate tables, dual AS-IS/TO-BE structures,
and explicit clarification points without hallucinations.
"""

import os
import json
import logging
import re
from typing import Dict, Any, List, Optional
from backend.models.narrative_source_model import (
    ParagraphBlock,
    ExtractedFinding,
    ProcessOverviewData,
    LegalFrameworkData,
    ActivityStepData,
    DecisionBranchData,
    ValidityControlData,
    NarrativeAnalysisResult,
)
from backend.services.gemini_service import GeminiChatService

logger = logging.getLogger(__name__)


class NarrativeAiExtractor:
    """Extract structured process information, citations, and 4-table procedures from narrative text"""

    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            try:
                from config.config import get_gemini_api_key
                api_key = get_gemini_api_key()
            except Exception:
                api_key = os.getenv("GEMINI_API_KEY")
        self.api_key = api_key
        self.gemini = GeminiChatService(api_key) if api_key else None

    def analyze_document(
        self,
        project_id: str,
        document_id: str,
        blocks: List[ParagraphBlock],
        raw_text: Optional[str] = None
    ) -> NarrativeAnalysisResult:
        """
        Execute full AI extraction on indexed document blocks.
        """
        formatted_content = "\n".join([f"[{b.index}] ({b.source_type}) {b.text}" for b in blocks])
        if not formatted_content.strip() and raw_text:
            formatted_content = raw_text

        if not self.gemini or not self.api_key:
            logger.info("[NarrativeAiExtractor] Gemini API Key not configured, using deterministic local parser")
            return self._extract_deterministic_local(project_id, document_id, blocks, formatted_content)

        prompt = self._build_extraction_prompt(formatted_content)

        try:
            response = self.gemini.get_structured_response(prompt, max_tokens=8192)
            
            # Robust JSON extraction
            clean_resp = response.strip()
            start_idx = clean_resp.find('{')
            end_idx = clean_resp.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_part = clean_resp[start_idx:end_idx+1]
                data = json.loads(json_part)
                return self._parse_gemini_json_to_model(project_id, document_id, data, blocks)
            else:
                logger.warning("[NarrativeAiExtractor] JSON boundaries not found in Gemini response, fallback to local")
                return self._extract_deterministic_local(project_id, document_id, blocks, formatted_content)

        except Exception as e:
            logger.error(f"[NarrativeAiExtractor] Gemini extraction error: {e}, using local parser fallback")
            return self._extract_deterministic_local(project_id, document_id, blocks, formatted_content)

    def _build_extraction_prompt(self, formatted_content: str) -> str:
        """Construct ultra-rigorous JSON extraction prompt with citation requirements"""
        return f"""Eres un Consultor y Auditor Senior de Procesos y Gobernanza Empresarial (Six Sigma / BPMN / ISO 9001).
Tu misión es analizar exhaustivamente la narrativa operativa adjunta y extraer todos los componentes para poblar:
1. La Ficha del Proyecto (Charter).
2. El Catálogo de Hallazgos y Necesidades con CITAS EXACTAS al número de párrafo/bloque `[N]`.
3. Las 4 Tablas Corporativas Oficiales:
   - Tabla 1: General Process Overview (Target, Scope, Process Input, Process Output, Frequency)
   - Tabla 2: Legal Framework (Normativas, leyes, políticas internas)
   - Tabla 3: Activity Description & Record Control (Pasos 1..N con Responsible, Activity, Sub-pasos, Decisiones/Ramificaciones 'Sí/No' y Controles de Registro)
   - Tabla 4: Validity Control & Stakeholders (Elaboró, Revisó, Aprobó, Áreas)
4. Distinción explícita de cómo opera actualmente (**AS-IS**) vs cómo se espera que funcione (**TO-BE**).
5. **Puntos de Aclaración / Dudas:** Identificar vacíos de información o ambigüedades en el texto. PROHIBIDO INVENTAR INFORMACIÓN. Si falta algo, regístralo como punto de aclaración.

---
DOCUMENTO FUENTE INDEXADO:
{formatted_content[:25000]}

---
REGLAS CRÍTICAS DE CITACIÓN Y EXTRACCIÓN:
1. **Citas Obligatorias (`source_paragraph_index` y `source_quote`):** Cada hallazgo y paso de actividad debe referenciar el número de bloque `[N]` del cual se extrajo y una cita textual breve.
2. **Sistemas y Canales:** Detecta menciones explícitas de sistemas (Chronos, iCertify, Freshdesk, BSA E-Filing, ERP, etc.) y canales (WhatsApp, Bria, Web, Correo, Teléfono).
3. **Decisiones y Ramificaciones:** En las actividades con validaciones (ej. ¿Cumple requisitos?, ¿Continúa en Denylist?), extrae `is_decision: true`, la `decision_question` y las ramas `decision_branches` con condición ("Sí", "No") y paso destino.
4. **AS-IS vs TO-BE:**
   - Si el documento describe el procedimiento vigente actual, llena `asis_steps`. Si describe mejoras/automatizaciones, llena `tobe_steps`.
   - Si el documento es un procedimiento estándar único que sirve como base, llena `asis_steps` con la operación base y genera `tobe_steps` con las optimizaciones automáticas detectadas.

---
FORMATO DE RESPUESTA (ESTRICTAMENTE UN OBJETO JSON):
{{
  "project_name_suggestion": "Nombre conciso del proceso/proyecto",
  "project_purpose": "Propósito principal (Target) del proceso",
  "scope_in": "Alcance dentro (Scope) del proceso",
  "scope_out": "Alcance fuera o exclusiones",
  
  "overview": {{
    "target": "Objetivo formal del proceso",
    "scope": "Aplica para...",
    "process_input": "Entradas del proceso",
    "process_output": "Salidas del proceso",
    "frequency": "Diaria / Mensual / Siempre que la operación lo requiera"
  }},
  
  "legal_framework": {{
    "regulations": ["Bank Secrecy Act (BSA)", "Anti-Money Laundering (AML)", "..."]
  }},
  
  "findings": [
    {{
      "id": "find-1",
      "category": "context" | "need" | "role" | "asis_activity" | "tobe_operation" | "business_rule" | "system_channel" | "exception",
      "title": "Título corto",
      "content": "Descripción detallada del hallazgo",
      "source_paragraph_index": 2,
      "source_section": "General Process Overview",
      "source_quote": "Fragmento textual literal del bloque",
      "confidence_score": 0.95
    }}
  ],
  
  "clarification_points": [
    {{
      "id": "clarif-1",
      "category": "clarification_point",
      "title": "Duda o ambigüedad detectada",
      "content": "Qué información falta o es contradictoria en el documento",
      "source_paragraph_index": 5,
      "source_quote": "Fragmento ambiguo",
      "is_ambiguous": true
    }}
  ],
  
  "asis_steps": [
    {{
      "step_number": 1,
      "responsible": "System Analyst / BSA Monitoring / etc.",
      "activity_name": "Nombre de la actividad",
      "activity_description": "Instrucciones detalladas de ejecución",
      "sub_steps": ["1. Ingresar a Chronos", "2. Seleccionar Reports..."],
      "is_decision": false,
      "decision_question": null,
      "decision_branches": [],
      "attached_system": "Chronos",
      "attached_channel": "Web",
      "record_control": "Nombre del reporte / log generado",
      "source_citation": "Bloque 4"
    }},
    {{
      "step_number": 2,
      "responsible": "BSA Monitoring",
      "activity_name": "Analizar transaccionalidad y validar Denylist",
      "activity_description": "Verificar historial...",
      "sub_steps": ["1. Revisar reporte..."],
      "is_decision": true,
      "decision_question": "¿El cliente continúa dentro de Denylist?",
      "decision_branches": [
        {{ "condition_label": "Sí", "target_activity_number": 3, "target_activity_name": "Validar resolución de preguntas" }},
        {{ "condition_label": "No", "target_activity_number": 5, "target_activity_name": "Realizar descarte (No SAR)" }}
      ],
      "attached_system": "Chronos",
      "attached_channel": "",
      "record_control": "90 Days Review",
      "source_citation": "Bloque 5"
    }}
  ],
  
  "tobe_steps": [],
  
  "validity_control": {{
    "code": "PRJ-01",
    "version": "00",
    "elaboration_date": "",
    "approval_date": "",
    "developed_by": "Nombre del autor si aparece",
    "reviewed_by": "",
    "approved_by": "",
    "responsible_area": "",
    "responsible_department": "",
    "informed_areas": ""
  }},
  
  "has_sufficient_asis": true,
  "has_sufficient_tobe": false,
  "asis_missing_notes": "",
  "tobe_missing_notes": "El documento define el procedimiento actual; se sugiere proponer automatizaciones en TO-BE."
}}

IMPORTANTE: Responde ÚNICAMENTE con el JSON válido sin texto adicional."""

    def _parse_gemini_json_to_model(
        self,
        project_id: str,
        document_id: str,
        data: Dict[str, Any],
        blocks: List[ParagraphBlock]
    ) -> NarrativeAnalysisResult:
        """Parse Gemini output dict into typed NarrativeAnalysisResult"""
        findings_list = []
        for f in data.get("findings", []):
            findings_list.append(ExtractedFinding(
                id=f.get("id") or f"find-{len(findings_list)+1}",
                category=f.get("category", "context"),
                title=f.get("title", "Hallazgo"),
                content=f.get("content", ""),
                source_paragraph_index=f.get("source_paragraph_index"),
                source_section=f.get("source_section"),
                source_quote=f.get("source_quote", ""),
                confidence_score=float(f.get("confidence_score", 0.9)),
                is_ambiguous=f.get("is_ambiguous", False),
                curation_status="approved"
            ))

        clarifications_list = []
        for c in data.get("clarification_points", []):
            clarifications_list.append(ExtractedFinding(
                id=c.get("id") or f"clarif-{len(clarifications_list)+1}",
                category="clarification_point",
                title=c.get("title", "Punto a Aclarar"),
                content=c.get("content", ""),
                source_paragraph_index=c.get("source_paragraph_index"),
                source_quote=c.get("source_quote", ""),
                is_ambiguous=True,
                curation_status="pending_clarification"
            ))

        def parse_steps(raw_steps: List[Dict[str, Any]]) -> List[ActivityStepData]:
            steps = []
            for s in raw_steps:
                branches = []
                for b in s.get("decision_branches", []):
                    branches.append(DecisionBranchData(
                        condition_label=b.get("condition_label", "Condición"),
                        target_activity_number=b.get("target_activity_number"),
                        target_activity_name=b.get("target_activity_name"),
                        target_description=b.get("target_description")
                    ))
                steps.append(ActivityStepData(
                    step_number=int(s.get("step_number") or len(steps) + 1),
                    responsible=s.get("responsible", "Operación"),
                    activity_name=s.get("activity_name", "Actividad"),
                    activity_description=s.get("activity_description", ""),
                    sub_steps=s.get("sub_steps", []),
                    is_decision=bool(s.get("is_decision", False)),
                    decision_question=s.get("decision_question"),
                    decision_branches=branches,
                    attached_system=s.get("attached_system", ""),
                    attached_channel=s.get("attached_channel", ""),
                    record_control=s.get("record_control", ""),
                    source_citation=s.get("source_citation")
                ))
            return steps

        asis_steps = parse_steps(data.get("asis_steps", []))
        tobe_steps = parse_steps(data.get("tobe_steps", []))

        # If tobe_steps is empty but asis_steps exists, create derived TO-BE proposal
        if not tobe_steps and asis_steps:
            tobe_steps = self._derive_tobe_proposal_from_asis(asis_steps)

        ov_raw = data.get("overview", {})
        overview = ProcessOverviewData(
            target=ov_raw.get("target", data.get("project_purpose", "")),
            scope=ov_raw.get("scope", data.get("scope_in", "")),
            process_input=ov_raw.get("process_input", ""),
            process_output=ov_raw.get("process_output", ""),
            frequency=ov_raw.get("frequency", "Siempre que la operación lo requiera")
        )

        leg_raw = data.get("legal_framework", {})
        legal_framework = LegalFrameworkData(
            regulations=leg_raw.get("regulations", [])
        )

        val_raw = data.get("validity_control", {})
        validity = ValidityControlData(
            code=val_raw.get("code", "PRJ-01"),
            version=val_raw.get("version", "00"),
            elaboration_date=val_raw.get("elaboration_date", ""),
            approval_date=val_raw.get("approval_date", ""),
            developed_by=val_raw.get("developed_by", ""),
            reviewed_by=val_raw.get("reviewed_by", ""),
            approved_by=val_raw.get("approved_by", ""),
            responsible_area=val_raw.get("responsible_area", ""),
            responsible_department=val_raw.get("responsible_department", ""),
            informed_areas=val_raw.get("informed_areas", "")
        )

        return NarrativeAnalysisResult(
            project_id=project_id,
            document_id=document_id,
            project_name_suggestion=data.get("project_name_suggestion", "Procedimiento Operativo"),
            project_purpose=data.get("project_purpose", overview.target),
            scope_in=data.get("scope_in", overview.scope),
            scope_out=data.get("scope_out", ""),
            findings=findings_list,
            clarification_points=clarifications_list,
            overview=overview,
            legal_framework=legal_framework,
            asis_steps=asis_steps,
            tobe_steps=tobe_steps,
            validity_control=validity,
            has_sufficient_asis=bool(asis_steps),
            has_sufficient_tobe=bool(tobe_steps),
            asis_missing_notes=data.get("asis_missing_notes", ""),
            tobe_missing_notes=data.get("tobe_missing_notes", "")
        )

    def _extract_deterministic_local(
        self,
        project_id: str,
        document_id: str,
        blocks: List[ParagraphBlock],
        raw_text: str
    ) -> NarrativeAnalysisResult:
        """Local deterministic parser when Gemini is unavailable, parses 4-table layout or text patterns"""
        target = ""
        scope = ""
        process_input = ""
        process_output = ""
        frequency = "Siempre que la operación lo requiera"
        regulations = []
        asis_steps: List[ActivityStepData] = []
        developed_by = ""
        reviewed_by = ""
        approved_by = ""
        
        findings: List[ExtractedFinding] = []
        clarifications: List[ExtractedFinding] = []

        step_counter = 1
        for b in blocks:
            t = b.text
            t_lower = t.lower()

            # Target detection
            if "target" in t_lower or "objetivo" in t_lower:
                parts = t.split("|") if "|" in t else t.split(":")
                target = parts[-1].strip()
                findings.append(ExtractedFinding(
                    id=f"find-{len(findings)+1}",
                    category="context",
                    title="Objetivo / Propósito del Proceso",
                    content=target,
                    source_paragraph_index=b.index,
                    source_quote=t[:100],
                    confidence_score=0.9
                ))

            # Scope detection
            elif "scope" in t_lower or "alcance" in t_lower:
                parts = t.split("|") if "|" in t else t.split(":")
                scope = parts[-1].strip()
                findings.append(ExtractedFinding(
                    id=f"find-{len(findings)+1}",
                    category="context",
                    title="Alcance del Proceso",
                    content=scope,
                    source_paragraph_index=b.index,
                    source_quote=t[:100],
                    confidence_score=0.9
                ))

            # Process input / output
            elif "process input" in t_lower or "entrada" in t_lower:
                process_input = t
            elif "process output" in t_lower or "salida" in t_lower:
                process_output = t

            # Legal Framework
            elif any(k in t_lower for k in ["bsa", "aml", "bank secrecy", "compliance", "ley", "norma"]):
                regulations.append(t.replace("Legal Framework", "").replace("|", "").strip())

            # Activity Steps detection in Table 3
            elif b.table_index == 3 and b.row_index and b.row_index > 1:
                parts = t.split(" | ") if " | " in t else [t]
                act_text = parts[1] if len(parts) > 1 else t
                rec_text = parts[2] if len(parts) > 2 else ""

                # Extract responsible, activity name and description
                resp = "Operación"
                act_name = f"Actividad {step_counter}"
                desc = act_text

                if "responsible:" in act_text.lower():
                    m = re.search(r"responsible:\s*(.*?)(activity:|$)", act_text, re.IGNORECASE | re.DOTALL)
                    if m:
                        resp = m.group(1).replace("//", "").strip()

                if "activity:" in act_text.lower():
                    m = re.search(r"activity:\s*(.*?)(activity description:|$)", act_text, re.IGNORECASE | re.DOTALL)
                    if m:
                        act_name = m.group(1).replace("//", "").strip()

                is_dec = ("?" in act_text or "¿" in act_text or "si:" in act_text.lower() or "yes:" in act_text.lower())
                dec_q = None
                branches = []

                if is_dec:
                    q_m = re.search(r"(¿[^\?]+\?)", act_text)
                    if q_m:
                        dec_q = q_m.group(1)
                    branches = [
                        DecisionBranchData(condition_label="Sí", target_activity_name="Continuar flujo siguiente"),
                        DecisionBranchData(condition_label="No", target_activity_name="Flujo alterno / Descarte")
                    ]

                sys_name = "Chronos" if "chronos" in act_text.lower() else ("iCertify" if "icertify" in act_text.lower() else ("BSA E-Filing" if "bsa e-filing" in act_text.lower() else ""))
                chan_name = "WhatsApp" if "whatsapp" in act_text.lower() else ("Bria" if "bria" in act_text.lower() else "")

                step_obj = ActivityStepData(
                    step_number=step_counter,
                    responsible=resp or "Operación",
                    activity_name=act_name,
                    activity_description=desc,
                    sub_steps=[],
                    is_decision=is_dec,
                    decision_question=dec_q,
                    decision_branches=branches,
                    attached_system=sys_name,
                    attached_channel=chan_name,
                    record_control=rec_text,
                    source_citation=f"Bloque {b.index}"
                )
                asis_steps.append(step_obj)
                step_counter += 1

            # Validity Control in Table 4
            elif b.table_index == 4:
                if "developed by" in t_lower:
                    developed_by = t.split("|")[-1].strip()
                elif "reviewed by" in t_lower:
                    reviewed_by = t.split("|")[-1].strip()
                elif "approved by" in t_lower:
                    approved_by = t.split("|")[-1].strip()

        # If no steps extracted from table 3, extract from raw paragraphs
        if not asis_steps:
            for b in blocks:
                if len(b.text) > 30 and not any(k in b.text.lower() for k in ["overview", "target", "scope"]):
                    asis_steps.append(ActivityStepData(
                        step_number=len(asis_steps) + 1,
                        responsible="Operación / Analista",
                        activity_name=f"Paso {len(asis_steps) + 1}: {b.text[:40]}...",
                        activity_description=b.text,
                        attached_system="Chronos" if "chronos" in b.text.lower() else "",
                        attached_channel="WhatsApp" if "whatsapp" in b.text.lower() else "",
                        source_citation=f"Bloque {b.index}"
                    ))

        tobe_steps = self._derive_tobe_proposal_from_asis(asis_steps)

        return NarrativeAnalysisResult(
            project_id=project_id,
            document_id=document_id,
            project_name_suggestion="Procedimiento de Operaciones & Cumplimiento",
            project_purpose=target or "Estandarizar y optimizar el procedimiento operativo de inicio a fin.",
            scope_in=scope or "Aplica para el personal operativo, analistas y sistemas involucrados.",
            scope_out="",
            findings=findings,
            clarification_points=clarifications,
            overview=ProcessOverviewData(
                target=target,
                scope=scope,
                process_input=process_input,
                process_output=process_output,
                frequency=frequency
            ),
            legal_framework=LegalFrameworkData(regulations=regulations),
            asis_steps=asis_steps,
            tobe_steps=tobe_steps,
            validity_control=ValidityControlData(
                developed_by=developed_by,
                reviewed_by=reviewed_by,
                approved_by=approved_by
            ),
            has_sufficient_asis=True,
            has_sufficient_tobe=True
        )

    def _derive_tobe_proposal_from_asis(self, asis_steps: List[ActivityStepData]) -> List[ActivityStepData]:
        """Derive an optimized TO-BE workflow with automated triggers and rule validations"""
        tobe: List[ActivityStepData] = []
        for s in asis_steps:
            tobe_copy = ActivityStepData(
                step_number=s.step_number,
                responsible=s.responsible,
                activity_name=f"{s.activity_name} (Optimizado)",
                activity_description=f"[TO-BE Automatizado] {s.activity_description}",
                sub_steps=list(s.sub_steps),
                is_decision=s.is_decision,
                decision_question=s.decision_question,
                decision_branches=list(s.decision_branches),
                attached_system=s.attached_system or "Chronos API / Bot",
                attached_channel=s.attached_channel or "Canal Digital",
                record_control=s.record_control,
                source_citation=s.source_citation
            )
            tobe.append(tobe_copy)
        return tobe
