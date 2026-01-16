#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Login window for TEMIS
"""

import tkinter as tk
from tkinter import messagebox, ttk
import threading


class LoginWindow:
    """Login window"""

    def __init__(self, parent, auth_manager):
        self.parent = parent
        self.auth_manager = auth_manager
        self.window = None
        self.create_window()

    def create_window(self):
        """Create login window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("TEMIS - Login")
        self.window.geometry("500x400")
        self.window.resizable(False, False)

        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.window.winfo_screenheight() // 2) - (400 // 2)
        self.window.geometry(f"500x400+{x}+{y}")

        # Configure colors (blue theme)
        bg_color = "#F9FAFB"
        primary_color = "#1E3A8A"
        secondary_color = "#3B82F6"

        self.window.configure(bg=bg_color)

        # Main frame
        main_frame = tk.Frame(self.window, bg=bg_color)
        main_frame.pack(expand=True, fill='both', padx=40, pady=40)

        # Logo/Title
        title_label = tk.Label(
            main_frame,
            text="🏛️ TEMIS",
            font=("Arial", 32, "bold"),
            bg=bg_color,
            fg=primary_color
        )
        title_label.pack(pady=(0, 10))

        subtitle_label = tk.Label(
            main_frame,
            text="Gobierno y Documentación de Proyectos",
            font=("Arial", 12),
            bg=bg_color,
            fg="#6B7280"
        )
        subtitle_label.pack(pady=(0, 40))

        # Login button
        login_btn = tk.Button(
            main_frame,
            text="🔐 Iniciar Sesión con Keycloak",
            font=("Arial", 14, "bold"),
            bg=secondary_color,
            fg="white",
            activebackground=primary_color,
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.on_login_click,
            padx=30,
            pady=15
        )
        login_btn.pack(pady=20)

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=("Arial", 10),
            bg=bg_color,
            fg="#6B7280"
        )
        self.status_label.pack(pady=10)

        # Version label
        version_label = tk.Label(
            main_frame,
            text="Versión 1.0.0 - Sprint 1",
            font=("Arial", 9),
            bg=bg_color,
            fg="#9CA3AF"
        )
        version_label.pack(side=tk.BOTTOM, pady=10)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_login_click(self):
        """Handle login button click"""
        self.status_label.config(text="Abriendo navegador...", fg="#3B82F6")
        self.window.update()

        # Perform login in background thread
        thread = threading.Thread(target=self.perform_login)
        thread.daemon = True
        thread.start()

    def perform_login(self):
        """Perform login (in background thread)"""
        try:
            success = self.auth_manager.login()

            if success:
                # Close login window and show dashboard
                self.window.after(0, self.on_login_success)
            else:
                self.window.after(0, lambda: self.on_login_failure("Autenticación fallida"))

        except Exception as e:
            self.window.after(0, lambda: self.on_login_failure(str(e)))

    def on_login_success(self):
        """Handle successful login"""
        self.status_label.config(text="✅ Autenticación exitosa", fg="#10B981")
        self.window.update()

        # Import here to avoid circular dependency
        from desktop.ui.dashboard import DashboardWindow

        # Close login window
        self.window.destroy()

        # Show dashboard (keep root hidden)
        DashboardWindow(self.parent, self.auth_manager)

    def on_login_failure(self, error_message):
        """Handle login failure"""
        self.status_label.config(text="❌ Error de autenticación", fg="#EF4444")
        messagebox.showerror(
            "Error de Autenticación",
            f"No se pudo autenticar:\n\n{error_message}\n\nVerifica tu conexión y credenciales."
        )

    def on_close(self):
        """Handle window close"""
        self.parent.quit()
