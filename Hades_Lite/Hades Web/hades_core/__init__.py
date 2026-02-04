"""
Hades Core - Motor de análisis forense de documentos

Este módulo contiene el motor principal extraído de Hades Ultimate.
"""

__version__ = "1.0.0"
__author__ = "Equipo HADES"

from .analyzer import analyze_image, AnalysisResult
from .forensics import SemaforoLevel

__all__ = ["analyze_image", "AnalysisResult", "SemaforoLevel"]
