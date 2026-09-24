#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Extractor Service for TEMIS Media Studio
Handles audio extraction and intelligent scene change / screenshot detection via FFmpeg.
"""

import os
import sys
import subprocess
import shutil
import logging
from typing import List, Dict, Any, Optional, Tuple
from config.settings import FFMPEG_PATH

logger = logging.getLogger("temis_media_studio")


class MediaExtractor:
    """Extracts audio and keyframe screenshots from video files using local FFmpeg"""

    @staticmethod
    def get_ffmpeg_binary() -> str:
        """Locate bundled ffmpeg.exe or system fallback"""
        if os.path.exists(FFMPEG_PATH):
            return FFMPEG_PATH
        sys_ffmpeg = shutil.which("ffmpeg")
        if sys_ffmpeg:
            return sys_ffmpeg
        raise FileNotFoundError(f"No se encontró FFmpeg en '{FFMPEG_PATH}' ni en el PATH del sistema.")

    @staticmethod
    def format_seconds(seconds: float) -> str:
        """Format seconds into HH:MM:SS string"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @classmethod
    def get_video_duration(cls, video_path: str) -> float:
        """Get video duration in seconds via FFmpeg"""
        ffmpeg_bin = cls.get_ffmpeg_binary()
        cmd = [
            ffmpeg_bin, "-i", video_path,
            "-f", "null", "-"
        ]
        try:
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
            # Parse Duration: 00:15:30.45 from stderr
            import re
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
            if match:
                hours = float(match.group(1))
                minutes = float(match.group(2))
                seconds = float(match.group(3))
                return hours * 3600 + minutes * 60 + seconds
        except Exception as e:
            logger.warning(f"Error getting duration: {e}")
        return 0.0

    @classmethod
    def extract_audio(cls, video_path: str, output_wav_path: str, progress_callback=None) -> str:
        """
        Extract 16kHz mono 16-bit PCM WAV audio from video (optimized for Whisper)
        """
        ffmpeg_bin = cls.get_ffmpeg_binary()
        os.makedirs(os.path.dirname(os.path.abspath(output_wav_path)), exist_ok=True)
        
        cmd = [
            ffmpeg_bin, "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_wav_path
        ]
        
        if progress_callback:
            progress_callback("Extrayendo pista de audio optimizada con FFmpeg...")

        # Hide window on Windows
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        return output_wav_path

    @classmethod
    def extract_keyframes(
        cls,
        video_path: str,
        output_dir: str,
        scene_threshold: float = 0.35,
        max_frames: int = 15,
        min_interval_sec: float = 5.0,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        Extract keyframe screenshots on scene/screen changes using FFmpeg scene detection filter.
        Returns list of dicts: [{"path": "...", "timestamp_sec": 45.2, "timestamp_formatted": "00:00:45", "filename": "..."}]
        """
        ffmpeg_bin = cls.get_ffmpeg_binary()
        os.makedirs(output_dir, exist_ok=True)

        if progress_callback:
            progress_callback("Analizando cambios de pantalla y extrayendo capturas clave...")

        duration = cls.get_video_duration(video_path)
        logger.info(f"Video duration: {duration}s")

        # Hide window on Windows
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        # Approach: Use FFmpeg scene filter with select='gt(scene,threshold)+gte(t-prev_selected_t,min_interval)'
        frame_pattern = os.path.join(output_dir, "frame_%03d.jpg")
        
        # FFmpeg filter to pick frames with scene change > threshold, separated by at least min_interval_sec
        filter_expr = f"select='gt(scene,{scene_threshold})',scale=1280:-1"
        
        cmd = [
            ffmpeg_bin, "-y",
            "-i", video_path,
            "-vf", filter_expr,
            "-vsync", "vfr",
            "-q:v", "2",
            frame_pattern
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        except Exception as e:
            logger.warning(f"Scene detection failed: {e}, falling back to periodic interval")

        # Check extracted frames
        import glob
        extracted_files = sorted(glob.glob(os.path.join(output_dir, "frame_*.jpg")))

        # Fallback: if fewer than 3 frames detected, extract at regular intervals across duration
        if len(extracted_files) < 3 and duration > 10:
            logger.info("Few scene changes detected, generating interval screenshots...")
            num_samples = min(max_frames, max(4, int(duration // 45)))
            interval = duration / (num_samples + 1)
            
            # Clean old frames
            for f in extracted_files:
                try: os.remove(f)
                except Exception: pass
            
            for i in range(1, num_samples + 1):
                t = i * interval
                out_file = os.path.join(output_dir, f"frame_{i:03d}.jpg")
                cmd_single = [
                    ffmpeg_bin, "-y",
                    "-ss", str(t),
                    "-i", video_path,
                    "-vframes", "1",
                    "-q:v", "2",
                    "-vf", "scale=1280:-1",
                    out_file
                ]
                subprocess.run(cmd_single, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            
            extracted_files = sorted(glob.glob(os.path.join(output_dir, "frame_*.jpg")))

        # Cap at max_frames
        if len(extracted_files) > max_frames:
            step = len(extracted_files) / max_frames
            selected_indices = [int(i * step) for i in range(max_frames)]
            keep_files = [extracted_files[i] for i in selected_indices if i < len(extracted_files)]
            # Remove unselected
            for f in extracted_files:
                if f not in keep_files:
                    try: os.remove(f)
                    except Exception: pass
            extracted_files = sorted(keep_files)

        # Build metadata with approximate timestamps
        frames_meta: List[Dict[str, Any]] = []
        total_extracted = len(extracted_files)
        
        for idx, fpath in enumerate(extracted_files):
            # Calculate estimated timestamp based on position
            if total_extracted > 1 and duration > 0:
                t_sec = (idx / (total_extracted - 1)) * (duration * 0.95) + (duration * 0.02)
            else:
                t_sec = duration * 0.5 if duration > 0 else 0.0

            frames_meta.append({
                "index": idx + 1,
                "path": fpath,
                "filename": os.path.basename(fpath),
                "timestamp_sec": round(t_sec, 1),
                "timestamp_formatted": cls.format_seconds(t_sec)
            })

        logger.info(f"Successfully extracted {len(frames_meta)} keyframe screenshots")
        return frames_meta
