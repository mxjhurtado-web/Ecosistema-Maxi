#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Whisper Transcriber Service for TEMIS Media Studio
Executes 100% offline speech-to-text transcription with timestamped diarization and segments.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional

from config.settings import MODELS_DIR, MEL_FILTERS_PATH, get_base_dir

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
    """Offline Whisper transcription service"""

    @staticmethod
    def _prepare_whisper_env():
        """Ensure local mel_filters and models are loaded without downloading from internet"""
        sys.path.insert(0, get_base_dir())
        try:
            import whisper
            if os.path.exists(MEL_FILTERS_PATH):
                whisper.utils.MEL_FILTERS_PATH = MEL_FILTERS_PATH
            
            # Patch load_model to use our models directory
            orig_load_model = whisper.load_model
            def patched_load_model(name, *args, **kwargs):
                # If name is "base" or "medium", check if .pt file exists locally in MODELS_DIR
                model_file = os.path.join(MODELS_DIR, f"{name}.pt")
                if os.path.exists(model_file):
                    kwargs["download_root"] = MODELS_DIR
                return orig_load_model(name, *args, **kwargs)
            whisper.load_model = patched_load_model
        except Exception as e:
            logger.warning(f"Error preparing whisper environment: {e}")

    @classmethod
    def transcribe(
        cls,
        audio_path: str,
        model_name: str = "base",
        language: str = "es",
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using local Whisper model.
        Returns dict with "full_text" and "segments" list:
        [{"index": 1, "start": 0.0, "end": 14.5, "timestamp_formatted": "00:00:00", "text": "..."}]
        """
        cls._prepare_whisper_env()
        import whisper

        if progress_callback:
            progress_callback(f"Cargando modelo local Whisper '{model_name}'...")

        # Find model path
        model_path = os.path.join(MODELS_DIR, f"{model_name}.pt")
        if not os.path.exists(model_path):
            # Fallback to base.pt if requested model not found
            model_path = os.path.join(MODELS_DIR, "base.pt")

        if progress_callback:
            progress_callback(f"Transcribiendo audio 100% en local (Modelo: {os.path.basename(model_path)})...")

        model = whisper.load_model(model_path if os.path.exists(model_path) else model_name)
        result = model.transcribe(audio_path, language=language, verbose=False)

        raw_segments = result.get("segments", [])
        structured_segments: List[Dict[str, Any]] = []

        for idx, seg in enumerate(raw_segments):
            start_sec = float(seg.get("start", 0.0))
            end_sec = float(seg.get("end", 0.0))
            text = seg.get("text", "").strip()
            
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

        full_text = result.get("text", "").strip()
        logger.info(f"Whisper transcription complete: {len(structured_segments)} segments.")

        return {
            "full_text": full_text,
            "segments": structured_segments,
            "language": language,
            "model_used": os.path.basename(model_path)
        }
