"""
Hades Core - Dates Module

Módulo de detección y procesamiento de fechas.
"""

from .dates import (
    DateInfo,
    DateType,
    DateFormat,
    analyze_date,
    extract_dates_from_text,
    process_dates_by_type,
    detect_date_format,
    parse_date
)

__all__ = [
    "DateInfo",
    "DateType",
    "DateFormat",
    "analyze_date",
    "extract_dates_from_text",
    "process_dates_by_type",
    "detect_date_format",
    "parse_date"
]
