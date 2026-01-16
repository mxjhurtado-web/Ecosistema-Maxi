#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings window for TEMIS
"""

import tkinter as tk
from tkinter import messagebox

from desktop.core.gemini_config import GeminiConfig


class SettingsWindow:
    """Settings window"""

    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.api_key_entry = None
        self.create_window()

    def create_window(self):
        """Create settings window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("TEMIS - Configuración")
        self.window.geometry("600x400")
        self.window.resizable(False, False)

        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (400 // 2)
        self.window.geometry(f"600x400+{x}+{y}")

        # Colors
        bg_color = "#F9FAFB"
        primary_color = "#1E3A8A"
        secondary_color = "#3B82F6"

        self.window.configure(bg=bg_color)

        # Header
        header_frame = tk.Frame(self.window, bg=primary_color, height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="⚙️ Configuración",
            font=("Arial", 16, "bold"),
            bg=primary_color,
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)

        # Main frame
        main_frame = tk.Frame(self.window, bg=bg_color)
        main_frame.pack(fill='both', expand=True, padx=40, pady=30)

        # Gemini API section
        gemini_label = tk.Label(
            main_frame,
            text="GEMINI API",
            font=("Arial", 12, "bold"),
            bg=bg_color,
            fg=primary_color
        )
        gemini_label.pack(anchor='w', pady=(0, 10))

        # API Key input
        api_key_frame = tk.Frame(main_frame, bg=bg_color)
        api_key_frame.pack(fill='x', pady=10)

        api_key_label = tk.Label(
            api_key_frame,
            text="API Key:",
            font=("Arial", 10),
            bg=bg_color,
            fg="#374151"
        )
        api_key_label.pack(side=tk.LEFT, padx=(0, 10))

        self.api_key_entry = tk.Entry(
            api_key_frame,
            font=("Arial", 10),
            bg="white",
            fg="#1F2937",
            relief=tk.FLAT,
            borderwidth=2,
            show="*",
            width=40
        )
        self.api_key_entry.pack(side=tk.LEFT, fill='x', expand=True)

        # Load existing API key
        existing_key = GeminiConfig.get_api_key()
        if existing_key:
            self.api_key_entry.insert(0, existing_key)

        # Show/Hide button
        show_btn = tk.Button(
            api_key_frame,
            text="👁️",
            font=("Arial", 10),
            bg="#E5E7EB",
            fg="#374151",
            activebackground="#D1D5DB",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_api_key_visibility,
            padx=10
        )
        show_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Model info
        model_label = tk.Label(
            main_frame,
            text="Modelo: gemini-2.5-flash",
            font=("Arial", 9),
            bg=bg_color,
            fg="#6B7280"
        )
        model_label.pack(anchor='w', pady=(5, 20))

        # Save button
        save_btn = tk.Button(
            main_frame,
            text="💾 Guardar Configuración",
            font=("Arial", 12, "bold"),
            bg=secondary_color,
            fg="white",
            activebackground=primary_color,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.save_config,
            padx=30,
            pady=12
        )
        save_btn.pack(pady=20)

        # Info label
        info_label = tk.Label(
            main_frame,
            text="💡 Obtén tu API key en: https://aistudio.google.com/app/apikey",
            font=("Arial", 9),
            bg=bg_color,
            fg="#6B7280",
            cursor="hand2"
        )
        info_label.pack(pady=10)

    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_entry.cget('show') == '*':
            self.api_key_entry.config(show='')
        else:
            self.api_key_entry.config(show='*')

    def save_config(self):
        """Save configuration"""
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            messagebox.showwarning("Advertencia", "Por favor ingresa una API key")
            return

        if GeminiConfig.save_api_key(api_key):
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
            self.window.destroy()
        else:
            messagebox.showerror("Error", "No se pudo guardar la configuración")
