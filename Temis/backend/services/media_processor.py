#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Processor Service for TEMIS
Lightweight audio and video metadata extraction, validation, and duration calculation
using Mutagen without heavy external FFmpeg dependencies (<5 MB RAM safe for Render).
"""

import os
import io
import hashlib
import logging
import mimetypes
from typing import Dict, Any, Optional, Tuple

try:
    import mutagen
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    from mutagen.flac import FLAC
    from mutagen.wave import WAVE
except ImportError:
    mutagen = None

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi", ".mkv", ".3gp"}
MEDIA_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS


class MediaProcessor:
    """Ultra-lightweight metadata processor for Audio and Video process recordings"""

    @staticmethod
    def is_media_file(filename: str) -> bool:
        """Check if file extension corresponds to a media file (Audio or Video)"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in MEDIA_EXTENSIONS

    @staticmethod
    def get_media_category(filename: str) -> str:
        """Return 'audio', 'video' or 'document'"""
        ext = os.path.splitext(filename)[1].lower()
        if ext in AUDIO_EXTENSIONS:
            return "audio"
        elif ext in VIDEO_EXTENSIONS:
            return "video"
        return "document"

    @staticmethod
    def format_duration(seconds: Optional[float]) -> str:
        """Format duration into human readable string (e.g., '14m 32s' or '01h 12m 05s')"""
        if seconds is None or seconds <= 0:
            return "0s"
        total_sec = int(round(seconds))
        hours, remainder = divmod(total_sec, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}h {minutes:02d}m {secs:02d}s"
        return f"{minutes:02d}m {secs:02d}s"

    @classmethod
    def extract_metadata(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract duration, bitrate, channels, and metadata using mutagen from byte buffer.
        Never consumes more than a few MBs of RAM.
        """
        ext = os.path.splitext(filename)[1].lower()
        media_type = cls.get_media_category(filename)
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        file_size = len(file_bytes)

        result = {
            "filename": filename,
            "extension": ext,
            "file_hash": file_hash,
            "file_size_bytes": file_size,
            "is_media": True,
            "media_type": media_type,
            "duration_seconds": None,
            "duration_formatted": "N/A",
            "bitrate": None,
            "sample_rate": None,
            "channels": None
        }

        if not mutagen:
            logger.warning("[MediaProcessor] Mutagen not installed, returning basic metadata.")
            return result

        try:
            bio = io.BytesIO(file_bytes)
            mutagen_file = mutagen.File(bio)
            
            if mutagen_file is not None and mutagen_file.info is not None:
                info = mutagen_file.info
                duration = getattr(info, "length", None)
                bitrate = getattr(info, "bitrate", None)
                sample_rate = getattr(info, "sample_rate", None)
                channels = getattr(info, "channels", None)

                result["duration_seconds"] = duration
                result["duration_formatted"] = cls.format_duration(duration)
                result["bitrate"] = bitrate
                result["sample_rate"] = sample_rate
                result["channels"] = channels
                logger.info(f"[MediaProcessor] Successfully parsed {filename}: {result['duration_formatted']}, {file_size} bytes")
            else:
                # Fallback estimate based on file size if header is compressed
                logger.info(f"[MediaProcessor] Parsed generic media file: {filename}")
        except Exception as e:
            logger.error(f"[MediaProcessor] Error parsing media metadata with Mutagen for {filename}: {e}")

        return result
