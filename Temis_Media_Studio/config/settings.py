#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration and Resource Management for TEMIS Media Studio
"""

import os
import sys
import json
import logging

logger = logging.getLogger("temis_media_studio")


def get_base_dir() -> str:
    """Return runtime base directory (compatible with PyInstaller _MEIPASS)"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(rel_path: str) -> str:
    """Get absolute path to a bundled resource"""
    base = get_base_dir()
    return os.path.join(base, rel_path)


# Default Paths
BASE_DIR = get_base_dir()
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".temis_media_studio")
os.makedirs(CONFIG_DIR, exist_ok=True)

KEYS_FILE = os.path.join(CONFIG_DIR, "api_keys.json")
EXPORTS_DIR = os.path.join(os.getcwd(), "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)

FFMPEG_PATH = get_resource_path(os.path.join("resources", "ffmpeg", "ffmpeg.exe"))
MODELS_DIR = get_resource_path(os.path.join("resources", "models"))
MEL_FILTERS_PATH = get_resource_path(os.path.join("resources", "assets", "mel_filters.npz"))


def load_gemini_api_key() -> str:
    """Load Gemini API key from local config or environment variable"""
    env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if env_key:
        return env_key.strip()
    
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("api_key", "").strip()
        except Exception as e:
            logger.warning(f"Error loading API key from {KEYS_FILE}: {e}")
    return ""


def save_gemini_api_key(api_key: str) -> bool:
    """Save Gemini API key to local config file"""
    try:
        data = {"api_key": api_key.strip()}
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving API key: {e}")
        return False
