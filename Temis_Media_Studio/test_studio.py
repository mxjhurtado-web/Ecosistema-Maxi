#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smoke and Unit Tests for TEMIS Media Studio (100% Local)
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
from services.local_process_builder import LocalProcessBuilder
from services.temis_package_builder import TemisPackageBuilder


def test_ffmpeg_detected():
    bin_path = MediaExtractor.get_ffmpeg_binary()
    assert os.path.exists(bin_path), f"FFmpeg binary not found at {bin_path}"
    print(f"✅ FFmpeg detected: {bin_path}")


def test_local_process_builder_and_package():
    sample_segments = [
        {"index": 1, "start_sec": 5.0, "end_sec": 25.0, "timestamp_start": "00:00:05", "timestamp_end": "00:00:25", "speaker": "Operador", "text": "Ingresando a Chronos para validar estatus de la agencia."},
        {"index": 2, "start_sec": 26.0, "end_sec": 48.0, "timestamp_start": "00:00:26", "timestamp_end": "00:00:48", "speaker": "Operador", "text": "Revisamos que no existan alertas de fraude o adeudos pendientes."}
    ]
    sample_keyframes = [
        {"index": 1, "filename": "frame_001.jpg", "path": "", "timestamp_sec": 10.0, "timestamp_formatted": "00:00:10"},
        {"index": 2, "filename": "frame_002.jpg", "path": "", "timestamp_sec": 30.0, "timestamp_formatted": "00:00:30"}
    ]

    # Test Local Process Builder
    analysis_data = LocalProcessBuilder.structure_process(sample_segments, sample_keyframes, "liberacion_agencias.mp4")
    assert "project_charter" in analysis_data
    assert len(analysis_data["process_steps"]) > 0
    print(f"✅ LocalProcessBuilder structured {len(analysis_data['process_steps'])} steps successfully (0 IA)!")

    # Test Package Builder
    out_docx = os.path.join(BASE_DIR, "exports", "test_bitacora_local.docx")
    out_json = os.path.join(BASE_DIR, "exports", "test_paquete_local.temis.json")

    TemisPackageBuilder.build_word_bitacora(analysis_data, sample_segments, sample_keyframes, out_docx, "liberacion_agencias.mp4")
    TemisPackageBuilder.build_temis_json_package(analysis_data, sample_segments, sample_keyframes, out_json, "liberacion_agencias.mp4")

    assert os.path.exists(out_docx), "Word bitacora not created"
    assert os.path.exists(out_json), "TEMIS json package not created"
    print(f"✅ Word Document and TEMIS Web Package (.temis.json) generated successfully!")


if __name__ == "__main__":
    test_ffmpeg_detected()
    test_local_process_builder_and_package()
    print("\n🎉 All 100% local tests PASSED for TEMIS Media Studio!")
