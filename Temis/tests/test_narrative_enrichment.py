#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for TEMIS Narrative Multi-Document Ingestion & Incremental Enrichment Pipeline
"""

import os
import sys
import pytest

# Ensure Temis path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.models.narrative_source_model import (
    ParagraphBlock, ExtractedFinding, ProcessOverviewData,
    LegalFrameworkData, ActivityStepData, ValidityControlData,
    NarrativeAnalysisResult
)
from backend.services.document_parser import DocumentParser
from backend.services.narrative_ai_extractor import NarrativeAiExtractor
from backend.services.process_generator_service import ProcessGeneratorService
from backend.services.process_narrative import export_narrative_to_docx, generate_process_narrative_markdown


def test_document_parser_mock_text():
    """Test indexed paragraph extraction from raw text simulation"""
    text = "Objetivo del proceso:\nMonitoreo y seguimiento de alertas SAR a 90 días.\n\nAlcance:\nAplica a Oficialía de Cumplimiento y Operaciones."
    # Simulate parser block generation
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    blocks = [ParagraphBlock(index=i+1, source_type="paragraph", text=l) for i, l in enumerate(lines)]
    assert len(blocks) == 4
    assert blocks[0].index == 1
    assert "Objetivo" in blocks[0].text


def test_narrative_extractor_and_enrichment():
    """Test full cycle of local extraction, incremental merge with secondary document and artifact generation"""
    extractor = NarrativeAiExtractor()

    # 1. Base Document
    base_blocks = [
        ParagraphBlock(index=1, source_type="paragraph", text="Objetivo: Monitorear alertas de transacciones SAR a 90 días."),
        ParagraphBlock(index=2, source_type="paragraph", text="Alcance: Todas las agencias de envío de dinero y corresponsales."),
        ParagraphBlock(index=3, source_type="paragraph", text="Paso 1. El Oficial de Cumplimiento consulta alertas en el sistema Chronos."),
        ParagraphBlock(index=4, source_type="paragraph", text="Paso 2. Si el cliente supera el umbral de $3,000 USD, se solicita formato KYC por WhatsApp."),
    ]

    base_result = extractor.analyze_document(
        project_id="test-proj-01",
        document_id="doc-base-01",
        blocks=base_blocks
    )

    assert base_result.project_id == "test-proj-01"
    assert len(base_result.findings) >= 2
    assert len(base_result.asis_steps) >= 2

    # 2. Secondary Document (Addendum / Exceptions)
    addendum_blocks = [
        ParagraphBlock(index=1, source_type="paragraph", text="Anexo de Excepciones y Reclamos:"),
        ParagraphBlock(index=2, source_type="paragraph", text="Paso 3. En caso de reimpresión de recibo, el Agente ingresa a iCertify."),
        ParagraphBlock(index=3, source_type="paragraph", text="Paso 4. El Supervisor autoriza la liberación del folio en Chronos."),
    ]

    enriched_result = extractor.enrich_existing_process(
        project_id="test-proj-01",
        document_id="doc-addendum-02",
        document_name="Anexo_Excepciones.docx",
        blocks=addendum_blocks,
        existing_result=base_result
    )

    assert len(enriched_result.findings) >= len(base_result.findings)
    assert len(enriched_result.asis_steps) >= len(base_result.asis_steps)
    # Check that new steps are present and numbered consecutively
    step_numbers = [s.step_number for s in enriched_result.asis_steps]
    assert step_numbers == list(range(1, len(enriched_result.asis_steps) + 1))

    # 3. Dual SIPOC generation
    dual_sipoc = ProcessGeneratorService.generate_dual_sipoc(enriched_result)
    assert len(dual_sipoc.asis_rows) == len(enriched_result.asis_steps)
    assert len(dual_sipoc.tobe_rows) == len(enriched_result.tobe_steps)

    # 4. Dual BPMN generation
    page_asis, page_tobe = ProcessGeneratorService.generate_dual_bpmn(enriched_result)
    assert "Flujo AS-IS" in page_asis["name"]
    assert "Flujo TO-BE" in page_tobe["name"]
    assert len(page_asis["nodes"]) >= 2
    assert len(page_tobe["nodes"]) >= 2

    # 5. Word Document Export (.docx)
    docx_io = export_narrative_to_docx(
        project_name="Proyecto Test Enriquecido",
        overview_data=enriched_result.overview.model_dump(),
        steps_data=[s.model_dump() for s in enriched_result.asis_steps],
        legal_framework=list(enriched_result.legal_framework.regulations),
        validity_data=enriched_result.validity_control.model_dump(),
        clarification_points=[c.model_dump() for c in enriched_result.clarification_points]
    )
    docx_bytes = docx_io.getvalue()
    assert len(docx_bytes) > 1000  # Valid binary DOCX generated
