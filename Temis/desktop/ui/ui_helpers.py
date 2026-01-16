#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI Helpers for TEMIS
Common UI utilities and theme application
"""

from desktop.core.theme_manager import ThemeManager


def apply_theme_to_window(window):
    """
    Apply current theme colors to a window
    Returns a dict with commonly used colors
    """
    colors = ThemeManager.get_colors()
    
    # Configure window background
    window.configure(bg=colors["bg_primary"])
    
    # Return color palette for easy access
    return {
        "bg": colors["bg_primary"],
        "bg_secondary": colors["bg_secondary"],
        "bg_tertiary": colors["bg_tertiary"],
        "text": colors["text_primary"],
        "text_secondary": colors["text_secondary"],
        "text_tertiary": colors["text_tertiary"],
        "primary": colors["accent_secondary"],
        "secondary": colors["accent_primary"],
        "success": colors["success"],
        "warning": colors["warning"],
        "error": colors["error"],
        "info": colors["info"],
        "border": colors["border"],
        "hover": colors["hover"]
    }


def get_theme_colors():
    """Get current theme colors as a simple dict"""
    colors = ThemeManager.get_colors()
    return {
        "bg": colors["bg_primary"],
        "bg_secondary": colors["bg_secondary"],
        "bg_tertiary": colors["bg_tertiary"],
        "text": colors["text_primary"],
        "text_secondary": colors["text_secondary"],
        "text_tertiary": colors["text_tertiary"],
        "primary": colors["accent_secondary"],
        "secondary": colors["accent_primary"],
        "success": colors["success"],
        "warning": colors["warning"],
        "error": colors["error"],
        "info": colors["info"],
        "border": colors["border"],
        "hover": colors["hover"]
    }
