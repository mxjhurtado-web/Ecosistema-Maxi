
import os
import sys
import subprocess
import re
import mimetypes
import logging

logger = logging.getLogger("athenas_lite")

def _bin_path(name: str) -> str:
    exe = f"{name}.exe" if os.name == "nt" else name
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.join(base, exe)
    return exe

def verificar_ffmpeg():
    try:
        subprocess.run([_bin_path("ffmpeg"), "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        return False

def verificar_ffprobe():
    try:
        subprocess.run([_bin_path("ffprobe"), "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        return False

def guess_mime(path: str) -> str:
    m, _ = mimetypes.guess_type(path)
    return m or "audio/wav"

def ffprobe_duration(path: str):
    try:
        resultado = subprocess.run(
            [_bin_path("ffprobe"), "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        out = (resultado.stdout or "").strip()
        if out:
            return float(out)
    except Exception:
        pass
    try:
        proc = subprocess.run([_bin_path("ffmpeg"), "-i", path],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, check=False)
        m = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)", proc.stderr or "")
        if m:
            h, m_, s = m.groups()
            return int(h) * 3600 + int(m_) * 60 + float(s)
    except Exception:
        pass
    return None

def human_duration(seconds):
    if seconds is None:
        return "N/A"
    seconds = int(round(seconds))
    mm, ss = divmod(seconds, 60)
    hh, mm = divmod(mm, 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}" if hh else f"{mm:02d}:{ss:02d}"

def extraer_audio(video_path, output_path):
    """Extrae a WAV mono 16k desde cualquier contenedor (incluye .gsm)."""
    try:
        logger.info(f"Extracting audio from {video_path} to {output_path}")
        subprocess.run([
            _bin_path("ffmpeg"), "-y", "-i", video_path, "-vn",
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", output_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return output_path
    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        return None
