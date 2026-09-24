#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Narrative Source & Process Generation Data Models for TEMIS
Models for Document Metadata, Citations, Extracted Findings, Dual SIPOC, 
and Corporate 4-Table Process Procedures.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import datetime


class ParagraphBlock(BaseModel):
    """Indexed paragraph, table row, or audio/video transcript block for exact citation matching"""
    index: int
    source_type: str = "paragraph"  # "paragraph", "table_row", "audio_transcript"
    heading_level: Optional[int] = None
    text: str
    page_number: Optional[int] = None
    table_index: Optional[int] = None
    row_index: Optional[int] = None
    timestamp_start: Optional[str] = None  # e.g., "00:03:15"
    timestamp_end: Optional[str] = None    # e.g., "00:03:48"
    speaker: Optional[str] = None          # e.g., "Analista", "SME", "Cliente"


class SourceDocumentMetadata(BaseModel):
    """Metadata for uploaded source narrative document, audio interview or video session"""
    id: str
    filename: str
    extension: str
    file_hash: str
    file_size_bytes: int
    uploaded_at: str = Field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    uploaded_by_email: str
    uploaded_by_name: str
    total_paragraphs: int = 0
    total_tables: int = 0
    version_label: str = "v1.0"
    is_active_version: bool = True
    
    # Multimedia Metadata
    is_media: bool = False
    media_type: str = "document"  # "document", "audio", "video"
    duration_seconds: Optional[float] = None
    duration_formatted: str = ""   # e.g., "14m 32s"
    bitrate: Optional[int] = None
    has_transcript_backup: bool = False
    transcript_txt_content: str = ""
    transcript_docx_filename: str = ""


class ExtractedFinding(BaseModel):
    """Single extracted data point with source citation and human curation status"""
    id: str
    category: str  # "context", "need", "role", "asis_activity", "tobe_operation", "business_rule", "system_channel", "exception", "clarification_point"
    title: str
    content: str
    source_paragraph_index: Optional[int] = None
    source_section: Optional[str] = None
    source_quote: str = ""
    confidence_score: float = 1.0  # 0.0 to 1.0
    is_ambiguous: bool = False
    
    # Human Curation Status
    curation_status: str = "approved"  # "approved", "modified", "discarded", "pending_clarification"
    curated_by: Optional[str] = None
    curated_at: Optional[str] = None
    curation_notes: Optional[str] = None
    modified_content: Optional[str] = None


class ProcessOverviewData(BaseModel):
    """Corporate Table 1: General Process Overview"""
    target: str = ""
    scope: str = ""
    process_input: str = ""
    process_output: str = ""
    frequency: str = "Siempre que la operación lo requiera"


class LegalFrameworkData(BaseModel):
    """Corporate Table 2: Legal & Regulatory Framework"""
    regulations: List[str] = Field(default_factory=list)


class DecisionBranchData(BaseModel):
    """Conditional decision branch within an activity"""
    condition_label: str  # e.g., "Sí", "No", "Rechazado"
    target_activity_number: Optional[int] = None
    target_activity_name: Optional[str] = None
    target_description: Optional[str] = None


class ActivityStepData(BaseModel):
    """Corporate Table 3: Activity Description & Record Control Step"""
    step_number: int
    responsible: str  # Swimlane / Actor
    activity_name: str
    activity_description: str
    sub_steps: List[str] = Field(default_factory=list)
    is_decision: bool = False
    decision_question: Optional[str] = None
    decision_branches: List[DecisionBranchData] = Field(default_factory=list)
    attached_system: str = ""  # e.g., Chronos, iCertify, Freshdesk
    attached_channel: str = ""  # e.g., WhatsApp, Bria, Web
    record_control: str = ""  # Evidencias / Reportes / Formatos
    source_citation: Optional[str] = None


class ValidityControlData(BaseModel):
    """Corporate Table 4: Validity Control & Stakeholders"""
    code: str = "PRJ-01"
    version: str = "00"
    elaboration_date: str = ""
    approval_date: str = ""
    developed_by: str = ""
    reviewed_by: str = ""
    approved_by: str = ""
    responsible_area: str = ""
    responsible_department: str = ""
    informed_areas: str = ""


class NarrativeAnalysisResult(BaseModel):
    """Full Analysis Result from Gemini 2.5 on a Source Narrative Document"""
    project_id: str
    document_id: str
    analyzed_at: str = Field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    analyzer_model: str = "gemini-2.5-flash"
    
    # Overview & Charter Fields
    project_name_suggestion: str = ""
    project_purpose: str = ""
    scope_in: str = ""
    scope_out: str = ""
    
    # Extracted Findings with Citations
    findings: List[ExtractedFinding] = Field(default_factory=list)
    clarification_points: List[ExtractedFinding] = Field(default_factory=list)
    
    # 4 Corporate Tables Data (AS-IS and TO-BE structures)
    overview: ProcessOverviewData = Field(default_factory=ProcessOverviewData)
    legal_framework: LegalFrameworkData = Field(default_factory=LegalFrameworkData)
    asis_steps: List[ActivityStepData] = Field(default_factory=list)
    tobe_steps: List[ActivityStepData] = Field(default_factory=list)
    validity_control: ValidityControlData = Field(default_factory=ValidityControlData)
    
    # Information Completeness Flags
    has_sufficient_asis: bool = True
    has_sufficient_tobe: bool = True
    asis_missing_notes: str = ""
    tobe_missing_notes: str = ""


class SipocRowModel(BaseModel):
    """Single SIPOC Matrix Row"""
    id: str
    step: str
    provider: str
    input: str
    output: str
    customer: str
    requirements: str = ""
    source_ref: str = ""


class DualSipocProposal(BaseModel):
    """Dual AS-IS and TO-BE SIPOC Matrix Proposal"""
    asis_rows: List[SipocRowModel] = Field(default_factory=list)
    tobe_rows: List[SipocRowModel] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    is_approved_asis: bool = False
    is_approved_tobe: bool = False


class BpmnNodeModel(BaseModel):
    """BPMN Node Representation for Flowchart Canvas"""
    id: str
    type: str  # "node_start", "node_activity", "node_decision", "node_end", "node_document", "node_system"
    label: str
    swimlane: str
    x: float
    y: float
    activity_number: Optional[int] = None
    attached_system: str = ""
    attached_channel: str = ""


class BpmnEdgeModel(BaseModel):
    """BPMN Edge Representation"""
    id: str
    source: str
    target: str
    label: str = ""


class BpmnDiagramPageModel(BaseModel):
    """Multi-Tab BPMN Diagram Page"""
    page_id: str
    name: str
    diagram_type: str = "general"  # "asis", "tobe", "general"
    swimlanes: List[str] = Field(default_factory=list)
    nodes: List[BpmnNodeModel] = Field(default_factory=list)
    edges: List[BpmnEdgeModel] = Field(default_factory=list)
    provenance_tag: str = ""
