#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoke and Unit Tests for TEMIS Media Studio
"""

import os
import sys

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.media_extractor import MediaExtractor
from services.whisper_transcriber import WhisperTranscriber
from services.gemini_process_ai import GeminiProcessAI
from services.temis_package_builder import TemisPackageBuilder


def test_ffmpeg_detected():
    bin_path = MediaExtractor.get_ffmpeg_binary()
    assert os.path.exists(bin_path), f"FFmpeg binary not found at {bin_path}"
    print(f"✅ FFmpeg detected: {bin_path}")


def test_package_builder():
    sample_analysis = {
        "project_charter": {
            "project_name": "Test Proceso Liberación",
            "project_code": "PRJ-TEST-01",
            "purpose": "Validar generación de bitácora y SIPOC",
            "scope": "Desde solicitud hasta aprobación",
            "target_system": "Chronos",
            "sponsor": "Operaciones",
            "executive_summary": "Resumen de prueba técnica."
        },
        "process_steps": [
            {
                "step_number": 1,
                "title": "Búsqueda en Chronos",
                "actor": "Operador",
                "system": "Chronos",
                "timestamp": "00:01:15",
                "description": "Ingresar al módulo de liberación y validar saldo.",
                "attached_screenshot": "frame_001.jpg",
                "screenshot_caption": "Pantalla de búsqueda en Chronos"
            }
        ],
        "sipoc": [
            {
                "id": "1.0",
                "supplier": "Agencia",
                "input": "Solicitud",
                "process": "Validar estatus",
                "output": "Dictamen",
                "customer": "Comité",
                "requirement": "SLA < 15min"
            }
        ],
        "bpmn_nodes": [
            {"id": "node-1", "type": "node_start", "label": "Inicio", "swimlane": "Input", "x": 40, "y": 140, "attached_system": "", "attached_channel": ""}
        ],
        "bpmn_edges": []
    }
    sample_segments = [
        {"index": 1, "timestamp_start": "00:00:10", "timestamp_end": "00:00:40", "speaker": "Analista", "text": "Iniciando la revisión del proceso de liberación."}
    ]
    sample_keyframes = [
        {"index": 1, "filename": "frame_001.jpg", "path": "", "timestamp_formatted": "00:00:15"}
    ]

    out_docx = os.path.join(BASE_DIR, "exports", "test_bitacora.docx")
    out_json = os.path.join(BASE_DIR, "exports", "test_paquete.temis.json")

    TemisPackageBuilder.build_word_bitacora(sample_analysis, sample_segments, sample_keyframes, out_docx, "video_test.mp4")
    TemisPackageBuilder.build_temis_json_package(sample_analysis, sample_segments, sample_keyframes, out_json, "video_test.mp4")

    assert os.path.exists(out_docx), "Word bitacora not created"
    assert os.path.exists(out_json), "TEMIS json package not created"
    print(f"✅ Word and TEMIS packages generated successfully!")


if __name__ == "__main__":
    test_ffmpeg_detected()
    test_package_builder()
    print("\n🎉 All smoke tests PASSED for TEMIS Media Studio!")
