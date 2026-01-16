#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Daily Log Editor window for TEMIS
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from datetime import date
import os

from desktop.core.api_client import APIClient
from desktop.core.daily_log_template import get_daily_log_template


class DailyLogEditor:
    """Daily Log Editor window"""

    def __init__(self, parent, auth_manager, project):
        self.parent = parent
        self.auth_manager = auth_manager
        self.project = project
        self.api_client = APIClient(
            os.getenv("API_BASE_URL", "http://localhost:8000"),
            auth_manager.access_token
        )
        self.window = None
        self.text_widget = None
        self.create_window()
        self.load_daily_log()

    def create_window(self):
        """Create editor window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"TEMIS - Documento Diario: {self.project['name']}")
        self.window.geometry("900x700")

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
            text=f"📝 Documento Diario - {date.today().strftime('%Y-%m-%d')}",
            font=("Arial", 16, "bold"),
            bg=primary_color,
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)

        # Toolbar
        toolbar_frame = tk.Frame(self.window, bg=bg_color, height=50)
        toolbar_frame.pack(fill='x', padx=20, pady=10)

        # Save button
        save_btn = tk.Button(
            toolbar_frame,
            text="💾 Guardar",
            font=("Arial", 11, "bold"),
            bg=secondary_color,
            fg="white",
            activebackground=primary_color,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.save_daily_log,
            padx=15,
            pady=8
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        # Load template button
        template_btn = tk.Button(
            toolbar_frame,
            text="📋 Cargar Plantilla",
            font=("Arial", 10),
            bg="#E5E7EB",
            fg="#374151",
            activebackground="#D1D5DB",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.load_template,
            padx=15,
            pady=8
        )
        template_btn.pack(side=tk.LEFT, padx=5)

        # Insert shortcuts
        insert_task_btn = tk.Button(
            toolbar_frame,
            text="+ Tarea",
            font=("Arial", 10),
            bg="#10B981",
            fg="white",
            activebackground="#059669",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.insert_shortcut("task"),
            padx=10,
            pady=8
        )
        insert_task_btn.pack(side=tk.LEFT, padx=5)

        insert_risk_btn = tk.Button(
            toolbar_frame,
            text="+ Riesgo",
            font=("Arial", 10),
            bg="#F59E0B",
            fg="white",
            activebackground="#D97706",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.insert_shortcut("risk"),
            padx=10,
            pady=8
        )
        insert_risk_btn.pack(side=tk.LEFT, padx=5)
        
        # Add link/resource button
        insert_link_btn = tk.Button(
            toolbar_frame,
            text="🔗 + Link/Recurso",
            font=("Arial", 10),
            bg="#8B5CF6",
            fg="white",
            activebackground="#7C3AED",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.add_resource_link,
            padx=10,
            pady=8
        )
        insert_link_btn.pack(side=tk.LEFT, padx=5)

        # Editor frame
        editor_frame = tk.Frame(self.window, bg=bg_color)
        editor_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Text widget with scrollbar
        self.text_widget = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="white",
            fg="#1F2937",
            insertbackground="#3B82F6",
            relief=tk.FLAT,
            borderwidth=2
        )
        self.text_widget.pack(fill='both', expand=True)

        # Status bar
        self.status_label = tk.Label(
            self.window,
            text="Listo",
            font=("Arial", 9),
            bg=bg_color,
            fg="#6B7280",
            anchor="w"
        )
        self.status_label.pack(fill='x', padx=20, pady=5)

    def load_daily_log(self):
        """Load existing daily log or template"""
        try:
            user_email = self.auth_manager.user_info.get('email')
            today = date.today()

            # Try to get existing log
            response = self.api_client.get_daily_log(
                user_email,
                self.project['id'],
                today
            )

            if response:
                self.text_widget.delete('1.0', tk.END)
                self.text_widget.insert('1.0', response.get('content', ''))
                self.status_label.config(text="Documento cargado", fg="#10B981")
            else:
                # Load template
                self.load_template()

        except Exception as e:
            print(f"Error loading daily log: {e}")
            self.load_template()

    def load_template(self):
        """Load template"""
        user_name = self.auth_manager.user_info.get('name', 'Usuario')
        template = get_daily_log_template(self.project['name'], user_name)
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.insert('1.0', template)
        self.status_label.config(text="Plantilla cargada", fg="#3B82F6")

    def save_daily_log(self):
        """Save daily log"""
        try:
            content = self.text_widget.get('1.0', tk.END).strip()
            if not content:
                messagebox.showwarning("Advertencia", "El documento está vacío")
                return

            user_email = self.auth_manager.user_info.get('email')
            today = date.today()

            response = self.api_client.create_daily_log(
                user_email,
                self.project['id'],
                today,
                content
            )

            if response:
                self.status_label.config(text="✅ Guardado exitosamente", fg="#10B981")
                messagebox.showinfo("Éxito", "Documento Diario guardado correctamente")
            else:
                messagebox.showerror("Error", "No se pudo guardar el documento")

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar:\n\n{str(e)}")

    def insert_shortcut(self, entry_type):
        """Insert shortcut for task/risk/decision"""
        user_name = self.auth_manager.user_info.get('name', 'Usuario')
        username = user_name.split()[0].lower()
        today = date.today().strftime('%Y-%m-%d')

        shortcuts = {
            "task": f"\n<!-- entry_id: TASK-XXX | type: task | status: todo | owner: @{username} | due: {today} | priority: medium -->\n- [ ] [Descripción de la tarea]\n  - **Detalles**: [Información adicional]\n",
            "risk": f"\n<!-- entry_id: RISK-XXX | type: risk | impact: medium | probability: medium -->\n**Riesgo**: [Título del riesgo]\n- **Descripción**: [Detalles]\n- **Mitigación**: [Plan de mitigación]\n",
            "decision": f"\n<!-- entry_id: DEC-XXX | type: decision | decided_by: @{username} -->\n**Decisión**: [Título]\n- **Contexto**: [Por qué se tomó]\n- **Impacto**: [Consecuencias]\n"
        }

        shortcut = shortcuts.get(entry_type, "")
        self.text_widget.insert(tk.INSERT, shortcut)
    
    def add_resource_link(self):
        """Add a resource link with dialog"""
        # Create dialog
        dialog = tk.Toplevel(self.window)
        dialog.title("Agregar Link/Recurso")
        dialog.geometry("500x350")
        dialog.configure(bg="#F9FAFB")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Header
        header = tk.Frame(dialog, bg="#8B5CF6", height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="🔗 Agregar Link/Recurso",
            font=("Arial", 14, "bold"),
            bg="#8B5CF6",
            fg="white"
        ).pack(pady=18)
        
        # Content
        content = tk.Frame(dialog, bg="#F9FAFB")
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(
            content,
            text="Título del Recurso:",
            font=("Arial", 10, "bold"),
            bg="#F9FAFB",
            fg="#1F2937"
        ).pack(anchor='w', pady=(0, 5))
        
        title_entry = tk.Entry(
            content,
            font=("Arial", 10),
            bg="white",
            relief=tk.SOLID,
            borderwidth=1
        )
        title_entry.pack(fill='x', ipady=6, pady=(0, 15))
        title_entry.focus()
        
        # URL
        tk.Label(
            content,
            text="URL:",
            font=("Arial", 10, "bold"),
            bg="#F9FAFB",
            fg="#1F2937"
        ).pack(anchor='w', pady=(0, 5))
        
        url_entry = tk.Entry(
            content,
            font=("Arial", 10),
            bg="white",
            relief=tk.SOLID,
            borderwidth=1
        )
        url_entry.pack(fill='x', ipady=6, pady=(0, 15))
        
        # Category
        tk.Label(
            content,
            text="Categoría:",
            font=("Arial", 10, "bold"),
            bg="#F9FAFB",
            fg="#1F2937"
        ).pack(anchor='w', pady=(0, 5))
        
        from tkinter import ttk
        category_var = tk.StringVar(value="Documentación")
        category_combo = ttk.Combobox(
            content,
            textvariable=category_var,
            values=[
                "Documentación",
                "Manual de Usuario",
                "Guía Técnica",
                "API/Referencia",
                "Tutorial",
                "Recurso Externo",
                "Otro"
            ],
            state="readonly",
            font=("Arial", 10)
        )
        category_combo.pack(fill='x', ipady=4, pady=(0, 15))
        
        # Description
        tk.Label(
            content,
            text="Descripción (opcional):",
            font=("Arial", 10, "bold"),
            bg="#F9FAFB",
            fg="#1F2937"
        ).pack(anchor='w', pady=(0, 5))
        
        desc_entry = tk.Entry(
            content,
            font=("Arial", 10),
            bg="white",
            relief=tk.SOLID,
            borderwidth=1
        )
        desc_entry.pack(fill='x', ipady=6, pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(content, bg="#F9FAFB")
        button_frame.pack(fill='x')
        
        def insert_link():
            title = title_entry.get().strip()
            url = url_entry.get().strip()
            category = category_var.get()
            description = desc_entry.get().strip()
            
            if not title or not url:
                messagebox.showwarning("Campos requeridos", "Por favor ingresa título y URL")
                return
            
            # Create link entry
            username = self.auth_manager.user_info.get('name', 'Usuario').split()[0].lower()
            link_entry = f"\n<!-- entry_id: LINK-{date.today().strftime('%Y%m%d')}-XXX | type: resource_link | category: {category} | added_by: @{username} | for_manual: true -->\n"
            link_entry += f"**📚 {title}** ({category})\n"
            link_entry += f"- **URL**: [{url}]({url})\n"
            if description:
                link_entry += f"- **Descripción**: {description}\n"
            link_entry += "\n"
            
            self.text_widget.insert(tk.INSERT, link_entry)
            dialog.destroy()
            
            messagebox.showinfo(
                "Link Agregado",
                f"✅ Link agregado exitosamente!\n\nEste recurso se incluirá automáticamente en el {category}."
            )
        
        tk.Button(
            button_frame,
            text="Cancelar",
            command=dialog.destroy,
            bg="#6B7280",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side='left', padx=5)
        
        tk.Button(
            button_frame,
            text="✅ Agregar Link",
            command=insert_link,
            bg="#8B5CF6",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        ).pack(side='right', padx=5)
