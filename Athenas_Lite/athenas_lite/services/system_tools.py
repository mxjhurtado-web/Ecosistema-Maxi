
import os
import sys
import subprocess
import mimetypes
import logging
from typing import Optional

try:
    import mutagen
except ImportError:
    mutagen = None

try:
    import soundfile as sf
    import numpy as np
except ImportError:
    sf = None
    np = None

logger = logging.getLogger("athenas_lite")

# Lista de extensiones que Gemini suele soportar nativamente para audio/video
# (Excluimos .gsm porque suele requerir conversión)
GEMINI_SUPPORTED_EXTENSIONS = {
    ".wav", ".mp3", ".aiff", ".aac", ".ogg", ".flac",
    ".mp4", ".mpeg", ".mov", ".avi", ".flv", ".mpg", ".webm", ".wmv", ".3gp"
}

def guess_mime(path: str) -> str:
    m, _ = mimetypes.guess_type(path)
    return m or "audio/wav"

def convert_to_wav(input_path: str, output_path: str) -> Optional[str]:
    """
    Convierte audio a WAV usando soundfile (requiere numpy).
    Útil para archivos .gsm o formatos raw soportados por libsndfile.
    """
    if not sf or not np:
        logger.error("soundfile/numpy no instalados. No se puede convertir.")
        return None
        
    try:
        data, samplerate = sf.read(input_path)
        sf.write(output_path, data, samplerate)
        logger.info(f"Convertido: {input_path} -> {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error convirtiendo {input_path} con soundfile: {e}")
        return None

def get_audio_duration(path: str) -> Optional[float]:
    """
    Obtiene la duración del archivo de audio/video usando mutagen.
    No requiere ffmpeg.exe ni ffprobe.exe.
    """
    if not mutagen:
        logger.warning("Mutagen no está instalado. No se puede calcular duración.")
        return None
        
    try:
        f = mutagen.File(path)
        if f is not None and f.info is not None:
            return f.info.length
    except Exception as e:
        logger.error(f"Error obteniendo duración con mutagen para {path}: {e}")
    
    return None

def human_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "N/A"
    seconds = int(round(seconds))
    mm, ss = divmod(seconds, 60)
    hh, mm = divmod(mm, 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d}" if hh else f"{mm:02d}:{ss:02d}"

def is_gemini_supported(path: str) -> bool:
    """Devuelve True si la extensión está en la lista de soportados por Gemini."""
    ext = os.path.splitext(path)[1].lower()
    return ext in GEMINI_SUPPORTED_EXTENSIONS

