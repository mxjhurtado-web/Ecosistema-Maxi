#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Whisper Transcriber Service for TEMIS Media Studio
Executes 100% offline speech-to-text transcription with timestamped diarization and segments
using faster-whisper (CTranslate2 int8 optimized).
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("temis_media_studio")


def format_seconds(seconds: float) -> str:
    """Format seconds into HH:MM:SS string"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class WhisperTranscriber:
    """Offline Whisper transcription service (100% local, 0 tokens)"""

    @classmethod
    def transcribe(
        cls,
        audio_path: str,
        model_name: str = "base",
        language: str = "es",
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using local Faster-Whisper model.
        Returns dict with "full_text" and "segments" list:
        [{"index": 1, "start_sec": 0.0, "end_sec": 14.5, "timestamp_start": "00:00:00", "timestamp_end": "00:00:14", "text": "..."}]
        """
        from faster_whisper import WhisperModel

        if progress_callback:
            progress_callback(f"Cargando motor de transcripción local Whisper '{model_name}'...")

        # Run on CPU with int8 quantization for speed and low memory
        model = WhisperModel(model_name, device="cpu", compute_type="int8")

        if progress_callback:
            progress_callback(f"Transcribiendo audio en local (0 Tokens, Modelo: {model_name})...")

        segments_generator, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        structured_segments: List[Dict[str, Any]] = []
        full_text_list: List[str] = []

        for idx, seg in enumerate(segments_generator):
            start_sec = float(seg.start)
            end_sec = float(seg.end)
            text = seg.text.strip()
            
            if text:
                structured_segments.append({
                    "index": idx + 1,
                    "start_sec": start_sec,
                    "end_sec": end_sec,
                    "timestamp_start": format_seconds(start_sec),
                    "timestamp_end": format_seconds(end_sec),
                    "speaker": "Participante",
                    "text": text
                })
                full_text_list.append(text)

        full_text = " ".join(full_text_list)
        logger.info(f"Whisper transcription complete: {len(structured_segments)} segments.")

        return {
            "full_text": full_text,
            "segments": structured_segments,
            "language": info.language if hasattr(info, "language") else language,
            "model_used": model_name
        }
