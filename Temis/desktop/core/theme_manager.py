#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Theme Manager for TEMIS
Handles light/dark theme configuration
"""

import json
import os


class ThemeManager:
    """Manage application theme (light/dark)"""
    
    CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".temis_theme.json")
    
    # Light Theme Colors
    LIGHT_THEME = {
        "bg_primary": "#F9FAFB",
        "bg_secondary": "#FFFFFF",
        "bg_tertiary": "#E5E7EB",
        "text_primary": "#1F2937",
        "text_secondary": "#6B7280",
        "text_tertiary": "#9CA3AF",
        "accent_primary": "#3B82F6",
        "accent_secondary": "#1E3A8A",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "info": "#8B5CF6",
        "border": "#D1D5DB",
        "hover": "#F3F4F6"
    }
    
    # Dark Theme Colors
    DARK_THEME = {
        "bg_primary": "#111827",
        "bg_secondary": "#1F2937",
        "bg_tertiary": "#374151",
        "text_primary": "#F9FAFB",
        "text_secondary": "#D1D5DB",
        "text_tertiary": "#9CA3AF",
        "accent_primary": "#60A5FA",
        "accent_secondary": "#3B82F6",
        "success": "#34D399",
        "warning": "#FBBF24",
        "error": "#F87171",
        "info": "#A78BFA",
        "border": "#4B5563",
        "hover": "#4B5563"
    }
    
    @classmethod
    def get_current_theme(cls) -> str:
        """Get current theme name (light or dark)"""
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get('theme', 'light')
        except Exception as e:
            print(f"Error loading theme config: {e}")
        return 'light'  # Default to light theme
    
    @classmethod
    def set_theme(cls, theme: str):
        """Set theme (light or dark)"""
        try:
            config = {'theme': theme}
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            return True
        except Exception as e:
            print(f"Error saving theme config: {e}")
            return False
    
    @classmethod
    def get_colors(cls) -> dict:
        """Get colors for current theme"""
        theme = cls.get_current_theme()
        if theme == 'dark':
            return cls.DARK_THEME
        return cls.LIGHT_THEME
    
    @classmethod
    def is_dark_mode(cls) -> bool:
        """Check if dark mode is enabled"""
        return cls.get_current_theme() == 'dark'
