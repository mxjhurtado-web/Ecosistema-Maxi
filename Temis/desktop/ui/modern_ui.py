#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modern UI Helper Functions for TEMIS
Provides consistent styling across all windows
"""

import tkinter as tk


class ModernUI:
    """Modern UI styling constants and helper functions"""
    
    # Modern Color Palette
    PRIMARY = "#4F46E5"        # Indigo
    PRIMARY_DARK = "#4338CA"   # Indigo dark
    SECONDARY = "#06B6D4"      # Cyan
    SUCCESS = "#10B981"        # Green
    WARNING = "#F59E0B"        # Amber
    DANGER = "#EF4444"         # Red
    PURPLE = "#8B5CF6"         # Purple
    
    # Backgrounds
    BG_MAIN = "#F3F4F6"        # Light gray
    BG_CARD = "#FFFFFF"        # White
    BG_HOVER = "#F9FAFB"       # Very light gray
    
    # Text
    TEXT_PRIMARY = "#111827"   # Almost black
    TEXT_SECONDARY = "#6B7280" # Gray
    TEXT_LIGHT = "#9CA3AF"     # Light gray
    
    # Borders
    BORDER = "#E5E7EB"         # Light gray
    BORDER_DARK = "#D1D5DB"    # Medium gray
    
    @staticmethod
    def create_card(parent, **kwargs):
        """Create a modern card with shadow effect"""
        # Shadow frame
        shadow = tk.Frame(
            parent,
            bg=ModernUI.BORDER,
            **kwargs
        )
        
        # Content frame
        card = tk.Frame(
            shadow,
            bg=ModernUI.BG_CARD
        )
        card.pack(padx=1, pady=1, fill='both', expand=True)
        
        return shadow, card
    
    @staticmethod
    def create_button(parent, text, command, style="primary", **kwargs):
        """Create a modern button with hover effect"""
        colors = {
            "primary": (ModernUI.PRIMARY, ModernUI.PRIMARY_DARK, "white"),
            "success": (ModernUI.SUCCESS, "#059669", "white"),
            "warning": (ModernUI.WARNING, "#D97706", "white"),
            "danger": (ModernUI.DANGER, "#DC2626", "white"),
            "secondary": ("#E5E7EB", "#D1D5DB", ModernUI.TEXT_PRIMARY),
            "purple": (ModernUI.PURPLE, "#7C3AED", "white"),
        }
        
        bg, hover_bg, fg = colors.get(style, colors["primary"])
        
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=10,
            **kwargs
        )
        
        # Hover effect
        def on_enter(e):
            btn.config(bg=hover_bg)
        
        def on_leave(e):
            btn.config(bg=bg)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    @staticmethod
    def create_input(parent, placeholder="", **kwargs):
        """Create a modern input field"""
        input_frame = tk.Frame(parent, bg=ModernUI.BORDER)
        
        entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 10),
            bg=ModernUI.BG_CARD,
            fg=ModernUI.TEXT_PRIMARY,
            relief=tk.FLAT,
            **kwargs
        )
        entry.pack(padx=1, pady=1, fill='both', expand=True, ipady=8, ipadx=10)
        
        return input_frame, entry
    
    @staticmethod
    def create_header(parent, title, subtitle="", height=100):
        """Create a modern header with gradient effect"""
        header = tk.Frame(parent, bg=ModernUI.PRIMARY, height=height)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header,
            text=title,
            font=("Segoe UI", 22, "bold"),
            bg=ModernUI.PRIMARY,
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=30, pady=(30, 5) if subtitle else 30)
        
        # Subtitle
        if subtitle:
            subtitle_label = tk.Label(
                header,
                text=subtitle,
                font=("Segoe UI", 11),
                bg=ModernUI.PRIMARY,
                fg="#E0E7FF"
            )
            subtitle_label.pack(side=tk.LEFT, padx=30, pady=(5, 30))
        
        return header
    
    @staticmethod
    def create_badge(parent, text, style="primary"):
        """Create a modern badge"""
        colors = {
            "primary": (ModernUI.PRIMARY, "white"),
            "success": (ModernUI.SUCCESS, "white"),
            "warning": (ModernUI.WARNING, "white"),
            "danger": (ModernUI.DANGER, "white"),
            "secondary": ("#E5E7EB", ModernUI.TEXT_PRIMARY),
        }
        
        bg, fg = colors.get(style, colors["primary"])
        
        badge = tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 9, "bold"),
            bg=bg,
            fg=fg,
            padx=12,
            pady=4
        )
        
        return badge
