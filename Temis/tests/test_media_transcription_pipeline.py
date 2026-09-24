#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for TEMIS Audio/Video Universal Ingestion, Transcript Backup Export,
and Process Generation Pipeline
"""

import os
import sys
import pytest

# Ensure Temis path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.models.narrative_source_model import ParagraphBlock, SourceDocumentMetadata
from backend.services.media_processor import MediaProcessor
from backend.services.transcript_exporter import TranscriptExporter
from backend.services.audio_transcriber import AudioTranscriber
from backend.services.document_parser import DocumentParser
from backend.services.narrative_ai_extractor import NarrativeAiExtractor
from backend.services.process_generator_service import ProcessGeneratorService
from backend.services.process_narrative import export_narrative_to_docx


def test_media_processor_format_detection():
    """Test universal format detection for audio and video"""
    assert MediaProcessor.is_media_file("entrevista.mp3") is True
    assert MediaProcessor.is_media_file("grabacion_meet.mp4") is True
    assert MediaProcessor.is_media_file("audio_nota.m4a") is True
    assert MediaProcessor.is_media_file("llamada.wav") is True
    assert MediaProcessor.is_media_file("proceso.mov") is True
    assert MediaProcessor.is_media_file("pantalla.webm") is True
    assert MediaProcessor.is_media_file("manual.docx") is False
    assert MediaProcessor.is_media_file("documento.pdf") is False

    assert MediaProcessor.get_media_category("audio.mp3") == "audio"
    assert MediaProcessor.get_media_category("video.mp4") == "video"
    assert MediaProcessor.get_media_category("doc.pdf") == "document"

    assert MediaProcessor.format_duration(92) == "01m 32s"
    assert MediaProcessor.format_duration(3665) == "01h 01m 05s"


def test_subtitle_parser_vtt_and_srt():
    """Test parsing .vtt and .srt subtitle files exported from Teams / Zoom"""
    vtt_content = """WEBVTT

1
00:00:10.000 --> 00:00:35.000
<v Juan Pérez>Iniciamos el levantamiento del proceso de seguimiento de SAR.

2
00:00:36.000 --> 00:01:15.000
<v Ana Martínez>El operador consulta el folio en Chronos y valida listas de denegación.
"""
    blocks = AudioTranscriber.parse_subtitle_file(vtt_content, "teams_transcript.vtt")
    assert len(blocks) == 2
    assert blocks[0].timestamp_start == "00:00:10"
    assert blocks[0].speaker == "Juan Pérez"
    assert "seguimiento de SAR" in blocks[0].text
    assert blocks[1].speaker == "Ana Martínez"
    assert "Chronos" in blocks[1].text


def test_transcript_exporter_txt_and_docx():
    """Test exporting audit backup files in .txt and .docx"""
    blocks = [
        {"timestamp_start": "00:00:05", "timestamp_end": "00:00:40", "speaker": "Analista", "text": "Inicio de sesión de entrevista."},
        {"timestamp_start": "00:00:41", "timestamp_end": "00:02:10", "speaker": "SME", "text": "Revisamos los folios en el sistema Chronos y si supera $3000 pedimos KYC."}
    ]

    txt_content = TranscriptExporter.export_to_txt(
        project_name="Monitoreo Transaccional SAR",
        source_filename="Entrevista_SAR.m4a",
        duration_str="14m 30s",
        uploaded_by="Ing. José Antonio Hurtado",
        blocks=blocks
    )
    assert "MINUTA & TRANSCRIPCIÓN OFICIAL" in txt_content
    assert "Entrevista_SAR.m4a" in txt_content
    assert "[00:00:41 - 00:02:10] [SME]:" in txt_content

    docx_bio = TranscriptExporter.export_to_docx(
        project_name="Monitoreo Transaccional SAR",
        source_filename="Entrevista_SAR.m4a",
        duration_str="14m 30s",
        uploaded_by="Ing. José Antonio Hurtado",
        blocks=blocks
    )
    docx_bytes = docx_bio.getvalue()
    assert len(docx_bytes) > 1000  # Valid binary DOCX


def test_end_to_end_media_to_process_pipeline():
    """Test complete flow: Media file -> Transcribe -> AI Process Extraction -> Dual SIPOC -> BPMN -> Word Manual"""
    # 1. Simulate media file blocks
    raw_media_bytes = b"MOCK_MP4_AUDIO_DATA_FOR_TESTING"
    blocks = DocumentParser.extract_blocks(raw_media_bytes, ".mp4", "Entrevista_Reimpresiones_iCertify.mp4")
    assert len(blocks) >= 3

    # 2. Extract process data with citations
    extractor = NarrativeAiExtractor()
    analysis_result = extractor.analyze_document(
        project_id="prj-media-01",
        document_id="doc-media-01",
        blocks=blocks
    )
    assert len(analysis_result.findings) >= 2
    assert len(analysis_result.asis_steps) >= 2

    # 3. Generate Dual SIPOC & BPMN
    dual_sipoc = ProcessGeneratorService.generate_dual_sipoc(analysis_result)
    assert len(dual_sipoc.asis_rows) == len(analysis_result.asis_steps)

    page_asis, page_tobe = ProcessGeneratorService.generate_dual_bpmn(analysis_result)
    assert len(page_asis["nodes"]) >= 2
    assert len(page_tobe["nodes"]) >= 2

    # 4. Generate 4-Table Corporate Word Manual (.docx)
    manual_bio = export_narrative_to_docx(
        project_name="Procedimiento iCertify",
        overview_data=analysis_result.overview.model_dump(),
        steps_data=[s.model_dump() for s in analysis_result.asis_steps],
        legal_framework=list(analysis_result.legal_framework.regulations),
        validity_data=analysis_result.validity_control.model_dump(),
        clarification_points=[c.model_dump() for c in analysis_result.clarification_points]
    )
    assert len(manual_bio.getvalue()) > 1000
