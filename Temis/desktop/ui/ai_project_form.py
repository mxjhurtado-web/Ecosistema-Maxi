#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-Assisted Project Creation Form for TEMIS
Simple, reliable form with Gemini suggestions
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
from datetime import datetime


class AIAssistedProjectForm:
    """Simple form with AI assistance for project creation"""
    
    def __init__(self, parent, auth_manager, api_client, on_complete=None):
        self.parent = parent
        self.auth_manager = auth_manager
        self.api_client = api_client
        self.on_complete = on_complete
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("🤖 Crear Proyecto con Asistente IA")
        self.window.geometry("700x800")
        self.window.configure(bg="#F9FAFB")
        self.window.transient(parent)
        self.window.lift()
        self.window.focus_force()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the form UI"""
        # Header
        header = tk.Frame(self.window, bg="#1E3A8A", height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="🤖 Asistente IA para Crear Proyecto",
            font=("Arial", 16, "bold"),
            bg="#1E3A8A",
            fg="white"
        ).pack(pady=20)
        
        # Main content
        content = tk.Frame(self.window, bg="#F9FAFB")
        content.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Instructions
        instructions = tk.Label(
            content,
            text="Completa los campos para crear tu proyecto. El asistente IA te ayudará con sugerencias.",
            font=("Arial", 10),
            bg="#F9FAFB",
            fg="#6B7280",
            wraplength=600,
            justify='left'
        )
        instructions.pack(anchor='w', pady=(0, 20))
        
        # Form fields
        self.fields = {}
        
        # Project Name
        self._create_field(
            content,
            "Nombre del Proyecto *",
            "project_name",
            "Ej: Sistema de Gestión de Inventarios",
            has_ai_button=True
        )
        
        # Objective
        self._create_field(
            content,
            "Objetivo Principal *",
            "objective",
            "¿Qué problema resuelve este proyecto?",
            is_textarea=True,
            has_ai_button=True
        )
        
        # Sponsor
        self._create_field(
            content,
            "Sponsor del Proyecto *",
            "sponsor",
            "Nombre del patrocinador ejecutivo"
        )
        
        # Project Lead
        self._create_field(
            content,
            "Project Lead *",
            "project_lead",
            "Responsable de la gestión del proyecto"
        )
        
        # Target Date
        self._create_field(
            content,
            "Fecha Objetivo (opcional)",
            "target_date",
            "DD/MM/YYYY"
        )
        
        # Buttons
        button_frame = tk.Frame(content, bg="#F9FAFB")
        button_frame.pack(pady=30)
        
        tk.Button(
            button_frame,
            text="✨ Crear Proyecto",
            command=self._create_project,
            bg="#10B981",
            fg="white",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=30,
            pady=12
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="Cancelar",
            command=self.window.destroy,
            bg="#6B7280",
            fg="white",
            font=("Arial", 11),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        ).pack(side='left', padx=10)
    
    def _create_field(self, parent, label_text, field_name, placeholder, is_textarea=False, has_ai_button=False):
        """Create a form field"""
        field_frame = tk.Frame(parent, bg="#F9FAFB")
        field_frame.pack(fill='x', pady=10)
        
        # Label
        label_container = tk.Frame(field_frame, bg="#F9FAFB")
        label_container.pack(fill='x')
        
        tk.Label(
            label_container,
            text=label_text,
            font=("Arial", 10, "bold"),
            bg="#F9FAFB",
            fg="#1F2937",
            anchor='w'
        ).pack(side='left')
        
        # AI suggestion button
        if has_ai_button:
            ai_btn = tk.Button(
                label_container,
                text="💡 Sugerencia IA",
                command=lambda: self._get_ai_suggestion(field_name),
                bg="#3B82F6",
                fg="white",
                font=("Arial", 8, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                padx=10,
                pady=4
            )
            ai_btn.pack(side='right')
        
        # Input
        if is_textarea:
            text_widget = tk.Text(
                field_frame,
                font=("Arial", 10),
                bg="white",
                fg="#1F2937",
                relief=tk.SOLID,
                borderwidth=1,
                height=4,
                wrap=tk.WORD
            )
            text_widget.pack(fill='x', pady=(5, 0))
            text_widget.insert("1.0", placeholder)
            text_widget.bind("<FocusIn>", lambda e: self._clear_placeholder(text_widget, placeholder))
            text_widget.bind("<FocusOut>", lambda e: self._restore_placeholder(text_widget, placeholder))
            self.fields[field_name] = text_widget
        else:
            entry = tk.Entry(
                field_frame,
                font=("Arial", 10),
                bg="white",
                fg="#1F2937",
                relief=tk.SOLID,
                borderwidth=1
            )
            entry.pack(fill='x', ipady=8, pady=(5, 0))
            entry.insert(0, placeholder)
            entry.bind("<FocusIn>", lambda e: self._clear_placeholder(entry, placeholder))
            entry.bind("<FocusOut>", lambda e: self._restore_placeholder(entry, placeholder))
            self.fields[field_name] = entry
    
    def _clear_placeholder(self, widget, placeholder):
        """Clear placeholder text"""
        if isinstance(widget, tk.Text):
            if widget.get("1.0", "end-1c") == placeholder:
                widget.delete("1.0", "end")
                widget.config(fg="#1F2937")
        else:
            if widget.get() == placeholder:
                widget.delete(0, tk.END)
                widget.config(fg="#1F2937")
    
    def _restore_placeholder(self, widget, placeholder):
        """Restore placeholder if empty"""
        if isinstance(widget, tk.Text):
            if not widget.get("1.0", "end-1c").strip():
                widget.delete("1.0", "end")
                widget.insert("1.0", placeholder)
                widget.config(fg="#9CA3AF")
        else:
            if not widget.get().strip():
                widget.delete(0, tk.END)
                widget.insert(0, placeholder)
                widget.config(fg="#9CA3AF")
    
    def _get_ai_suggestion(self, field_name):
        """Get AI suggestion for a field"""
        # Get current values
        current_values = {}
        for name, widget in self.fields.items():
            if isinstance(widget, tk.Text):
                value = widget.get("1.0", "end-1c").strip()
            else:
                value = widget.get().strip()
            current_values[name] = value
        
        # Create loading dialog
        loading = tk.Toplevel(self.window)
        loading.title("Generando sugerencia...")
        loading.geometry("300x100")
        loading.configure(bg="white")
        loading.transient(self.window)
        
        tk.Label(
            loading,
            text="🤖 Gemini está pensando...",
            font=("Arial", 11),
            bg="white",
            fg="#1F2937"
        ).pack(expand=True)
        
        loading.lift()
        loading.focus_force()
        
        def get_suggestion():
            try:
                # Call Gemini for suggestion
                prompt = self._build_suggestion_prompt(field_name, current_values)
                
                # Use Gemini service
                from backend.services.gemini_service import GeminiChatService
                from config.gemini_config import GeminiConfig
                
                api_key = GeminiConfig.get_api_key()
                gemini = GeminiChatService(api_key)
                suggestion = gemini.get_response(prompt)
                
                self.parent.after(0, lambda: self._apply_suggestion(field_name, suggestion, loading))
            except Exception as e:
                self.parent.after(0, lambda: self._show_suggestion_error(str(e), loading))
        
        threading.Thread(target=get_suggestion, daemon=True).start()
    
    def _build_suggestion_prompt(self, field_name, current_values):
        """Build prompt for AI suggestion"""
        if field_name == "project_name":
            if current_values.get("objective"):
                return f"Sugiere un nombre profesional y descriptivo para un proyecto con este objetivo: {current_values['objective']}. Responde SOLO con el nombre, sin explicaciones."
            else:
                return "Sugiere un nombre profesional para un proyecto de gestión. Responde SOLO con el nombre, sin explicaciones."
        
        elif field_name == "objective":
            if current_values.get("project_name"):
                return f"Redacta un objetivo claro y específico para un proyecto llamado '{current_values['project_name']}'. El objetivo debe explicar qué problema resuelve. Responde en 2-3 oraciones máximo."
            else:
                return "Redacta un ejemplo de objetivo claro para un proyecto de gestión empresarial. Responde en 2-3 oraciones máximo."
        
        return "Proporciona una sugerencia útil para este campo."
    
    def _apply_suggestion(self, field_name, suggestion, loading_window):
        """Apply AI suggestion to field"""
        loading_window.destroy()
        
        widget = self.fields[field_name]
        
        if isinstance(widget, tk.Text):
            widget.delete("1.0", "end")
            widget.insert("1.0", suggestion.strip())
            widget.config(fg="#1F2937")
        else:
            widget.delete(0, tk.END)
            widget.insert(0, suggestion.strip())
            widget.config(fg="#1F2937")
    
    def _show_suggestion_error(self, error, loading_window):
        """Show error getting suggestion"""
        loading_window.destroy()
        messagebox.showerror("Error", f"No se pudo obtener sugerencia de IA:\n\n{error}")
    
    def _create_project(self):
        """Create the project"""
        # Validate required fields
        project_name = self.fields["project_name"].get().strip()
        
        if isinstance(self.fields["objective"], tk.Text):
            objective = self.fields["objective"].get("1.0", "end-1c").strip()
        else:
            objective = self.fields["objective"].get().strip()
        
        sponsor = self.fields["sponsor"].get().strip()
        project_lead = self.fields["project_lead"].get().strip()
        
        # Check placeholders
        if not project_name or project_name.startswith("Ej:"):
            messagebox.showwarning("Campo requerido", "Por favor ingresa el nombre del proyecto")
            return
        
        if not objective or objective.startswith("¿Qué"):
            messagebox.showwarning("Campo requerido", "Por favor ingresa el objetivo del proyecto")
            return
        
        if not sponsor or sponsor.startswith("Nombre"):
            messagebox.showwarning("Campo requerido", "Por favor ingresa el sponsor del proyecto")
            return
        
        if not project_lead or project_lead.startswith("Responsable"):
            messagebox.showwarning("Campo requerido", "Por favor ingresa el project lead")
            return
        
        # Create project via API
        def create():
            try:
                response = requests.post(
                    f"{self.api_client.base_url}/api/wizard/start",
                    json={"user_email": self.auth_manager.user_info.get('email')},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    session_id = data["session_id"]
                    
                    # Send project data
                    project_data = {
                        "project_name": project_name,
                        "objective": objective,
                        "sponsor_name": sponsor,
                        "project_lead": project_lead
                    }
                    
                    # Answer wizard questions automatically
                    for key, value in project_data.items():
                        requests.post(
                            f"{self.api_client.base_url}/api/wizard/answer",
                            json={"session_id": session_id, "answer": value},
                            timeout=10
                        )
                    
                    self.parent.after(0, self._on_success)
                else:
                    self.parent.after(0, lambda: messagebox.showerror("Error", "No se pudo crear el proyecto"))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
        
        threading.Thread(target=create, daemon=True).start()
    
    def _on_success(self):
        """Handle successful creation"""
        messagebox.showinfo("¡Éxito!", "Proyecto creado correctamente con las 7 fases de la metodología híbrida.")
        
        if self.on_complete:
            self.on_complete(None)
        
        self.window.destroy()
