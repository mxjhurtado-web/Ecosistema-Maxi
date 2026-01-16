#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase Wizard window for TEMIS
Guides users through 7 phases with deliverables management
"""

import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import os
from datetime import date

from desktop.core.api_client import APIClient
from desktop.core.document_templates import ALL_PHASE_DELIVERABLES


# Nombres de las fases
PHASE_NAMES = {
    1: "Priorización + Diagnóstico",
    2: "Inicio (Charter)",
    3: "Planificación",
    4: "Ejecución Iterativa",
    5: "Monitoreo y Control",
    6: "Mejora Continua",
    7: "Cierre"
}


class PhaseWizard:
    """Phase Wizard window"""

    def __init__(self, parent, auth_manager, project):
        self.parent = parent
        self.auth_manager = auth_manager
        self.project = project
        self.current_phase = project.get('current_phase', 1)
        self.api_client = APIClient(
            os.getenv("API_BASE_URL", "http://localhost:8000"),
            auth_manager.access_token
        )
        self.deliverables = []
        self.window = None
        self.create_window()
        self.load_phase_data()

    def create_window(self):
        """Create wizard window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"TEMIS - Wizard de Fases: {self.project['name']}")
        self.window.geometry("1000x700")

        # Get theme colors
        from desktop.ui.ui_helpers import get_theme_colors
        colors = get_theme_colors()
        
        bg_color = colors["bg"]
        primary_color = colors["primary"]
        secondary_color = colors["secondary"]

        self.window.configure(bg=bg_color)

        # Header
        header_frame = tk.Frame(self.window, bg=primary_color, height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text=f"🧭 Wizard de Fases - {self.project['name']}",
            font=("Arial", 18, "bold"),
            bg=primary_color,
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=20)

        # Progress indicator
        progress_frame = tk.Frame(self.window, bg=bg_color, height=60)
        progress_frame.pack(fill='x', padx=20, pady=10)

        self.create_progress_indicator(progress_frame)

        # Current phase info
        phase_info_frame = tk.Frame(self.window, bg="white", relief=tk.RAISED, borderwidth=2)
        phase_info_frame.pack(fill='x', padx=20, pady=10)

        self.phase_title_label = tk.Label(
            phase_info_frame,
            text=f"FASE {self.current_phase}: {PHASE_NAMES[self.current_phase]}",
            font=("Arial", 16, "bold"),
            bg="white",
            fg=primary_color
        )
        self.phase_title_label.pack(padx=20, pady=15)

        # Deliverables section
        deliverables_label = tk.Label(
            self.window,
            text="ENTREGABLES DE ESTA FASE:",
            font=("Arial", 12, "bold"),
            bg=bg_color,
            fg="#374151"
        )
        deliverables_label.pack(anchor='w', padx=20, pady=(10, 5))

        # Scrollable deliverables frame
        deliverables_container = tk.Frame(self.window, bg=bg_color)
        deliverables_container.pack(fill='both', expand=True, padx=20, pady=10)

        canvas = tk.Canvas(deliverables_container, bg=bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(deliverables_container, orient="vertical", command=canvas.yview)
        self.deliverables_frame = tk.Frame(canvas, bg=bg_color)

        self.deliverables_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.deliverables_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add deliverable button
        add_btn = tk.Button(
            self.window,
            text="+ Agregar Entregable",
            font=("Arial", 11, "bold"),
            bg="#10B981",
            fg="white",
            activebackground="#059669",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.add_deliverable,
            padx=20,
            pady=10
        )
        add_btn.pack(pady=10)

        # Navigation buttons
        nav_frame = tk.Frame(self.window, bg=bg_color, height=60)
        nav_frame.pack(fill='x', padx=20, pady=10)

        if self.current_phase > 1:
            prev_btn = tk.Button(
                nav_frame,
                text="← Fase Anterior",
                font=("Arial", 11),
                bg="#E5E7EB",
                fg="#374151",
                activebackground="#D1D5DB",
                relief=tk.FLAT,
                cursor="hand2",
                command=self.previous_phase,
                padx=20,
                pady=10
            )
            prev_btn.pack(side=tk.LEFT, padx=5)

        complete_btn = tk.Button(
            nav_frame,
            text="✓ Completar Fase",
            font=("Arial", 11, "bold"),
            bg=secondary_color,
            fg="white",
            activebackground=primary_color,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.complete_phase,
            padx=20,
            pady=10
        )
        complete_btn.pack(side=tk.RIGHT, padx=5)

        if self.current_phase < 7:
            next_btn = tk.Button(
                nav_frame,
                text="Fase Siguiente →",
                font=("Arial", 11),
                bg="#E5E7EB",
                fg="#374151",
                activebackground="#D1D5DB",
                relief=tk.FLAT,
                cursor="hand2",
                command=self.next_phase,
                padx=20,
                pady=10
            )
            next_btn.pack(side=tk.RIGHT, padx=5)

    def create_progress_indicator(self, parent):
        """Create visual progress indicator"""
        progress_label = tk.Label(
            parent,
            text=f"Progreso: Fase {self.current_phase}/7",
            font=("Arial", 10, "bold"),
            bg="#F9FAFB",
            fg="#374151"
        )
        progress_label.pack(anchor='w', pady=5)

        # Progress circles
        circles_frame = tk.Frame(parent, bg="#F9FAFB")
        circles_frame.pack(fill='x', pady=5)

        for i in range(1, 8):
            if i <= self.current_phase:
                color = "#10B981"  # Green for completed/current
                symbol = "●"
            else:
                color = "#D1D5DB"  # Gray for pending
                symbol = "○"

            circle = tk.Label(
                circles_frame,
                text=symbol,
                font=("Arial", 20),
                bg="#F9FAFB",
                fg=color
            )
            circle.pack(side=tk.LEFT, padx=5)

    def load_phase_data(self):
        """Load deliverables for current phase"""
        try:
            user_email = self.auth_manager.user_info.get('email')
            
            # Get deliverables from backend
            # TODO: Implement API call
            # self.deliverables = self.api_client.get_phase_deliverables(
            #     user_email,
            #     self.project['id'],
            #     self.current_phase
            # )

            # For now, show template deliverables
            self.deliverables = []
            self.display_deliverables()

        except Exception as e:
            print(f"Error loading phase data: {e}")
            self.display_deliverables()

    def display_deliverables(self):
        """Display deliverables in UI"""
        # Clear existing widgets
        for widget in self.deliverables_frame.winfo_children():
            widget.destroy()

        # Get template deliverables for this phase
        template_deliverables = ALL_PHASE_DELIVERABLES.get(self.current_phase, {})

        if not template_deliverables:
            no_deliverables = tk.Label(
                self.deliverables_frame,
                text="No hay entregables definidos para esta fase.",
                font=("Arial", 11),
                bg="#F9FAFB",
                fg="#6B7280"
            )
            no_deliverables.pack(pady=20)
            return

        # Display each template deliverable
        for name, config in template_deliverables.items():
            self.create_deliverable_card(name, config)

    def create_deliverable_card(self, name, config):
        """Create deliverable card widget"""
        card_frame = tk.Frame(
            self.deliverables_frame,
            bg="white",
            relief=tk.RAISED,
            borderwidth=1
        )
        card_frame.pack(fill='x', pady=5, padx=5)

        # Status icon
        status_icon = "⏳"  # Pending by default
        status_color = "#F59E0B"

        # Deliverable name
        name_label = tk.Label(
            card_frame,
            text=f"{status_icon} {name}",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#1E3A8A",
            anchor="w"
        )
        name_label.pack(fill='x', padx=15, pady=(10, 5))

        # Description
        description = config.get('description', '')
        if description:
            desc_label = tk.Label(
                card_frame,
                text=description,
                font=("Arial", 9),
                bg="white",
                fg="#6B7280",
                anchor="w",
                wraplength=800
            )
            desc_label.pack(fill='x', padx=15, pady=5)

        # Type and optional badge
        info_frame = tk.Frame(card_frame, bg="white")
        info_frame.pack(fill='x', padx=15, pady=5)

        type_label = tk.Label(
            info_frame,
            text=f"📄 {config.get('type', 'document')}",
            font=("Arial", 9),
            bg="white",
            fg="#6B7280"
        )
        type_label.pack(side=tk.LEFT, padx=(0, 10))

        if config.get('optional'):
            optional_label = tk.Label(
                info_frame,
                text="OPCIONAL",
                font=("Arial", 8, "bold"),
                bg="#FEF3C7",
                fg="#92400E",
                padx=5,
                pady=2
            )
            optional_label.pack(side=tk.LEFT)

        if config.get('auto_update'):
            auto_label = tk.Label(
                info_frame,
                text="AUTO-UPDATE",
                font=("Arial", 8, "bold"),
                bg="#DBEAFE",
                fg="#1E40AF",
                padx=5,
                pady=2
            )
            auto_label.pack(side=tk.LEFT, padx=(5, 0))

        # Buttons
        btn_frame = tk.Frame(card_frame, bg="white")
        btn_frame.pack(fill='x', padx=15, pady=(5, 10))

        create_btn = tk.Button(
            btn_frame,
            text="Crear desde Template",
            font=("Arial", 9),
            bg="#3B82F6",
            fg="white",
            activebackground="#1E3A8A",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.create_from_template(name, config),
            padx=10,
            pady=5
        )
        create_btn.pack(side=tk.LEFT, padx=(0, 5))

    def create_from_template(self, name, config):
        """Create deliverable from template"""
        try:
            # Get template function
            template_function = config.get('template_function')
            
            if not template_function:
                messagebox.showwarning(
                    "Template no disponible",
                    f"No hay template definido para '{name}'"
                )
                return
            
            # Import the template function
            from desktop.core import document_templates
            
            if not hasattr(document_templates, template_function):
                messagebox.showerror(
                    "Error",
                    f"Función de template '{template_function}' no encontrada"
                )
                return
            
            # Get the template function
            template_func = getattr(document_templates, template_function)
            
            # Generate the document content
            # For master document, pass the full project dict
            if template_function == "generate_master_project_document":
                content = template_func(self.project)
            else:
                # For other templates, pass project name and kwargs
                content = template_func(self.project.get('name', 'Proyecto'), **self.project)
            
            # Determine file extension based on type
            file_type = config.get('type', 'document')
            if file_type == 'spreadsheet':
                # For spreadsheets, show info message
                messagebox.showinfo(
                    "Spreadsheet",
                    f"'{name}' generado.\n\nPara spreadsheets, usa la funcionalidad de exportar a Excel."
                )
                return
            
            # Show preview dialog for documents
            from desktop.ui.document_preview_dialog import DocumentPreviewDialog
            
            def on_save(filename):
                """Callback when document is saved"""
                print(f"Document saved: {filename}")
                # TODO: Update project metadata with saved document path
            
            # Create and show preview dialog
            DocumentPreviewDialog(
                self.window,
                name,
                content,
                on_save=on_save
            )
        
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al crear '{name}':\n\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    def add_deliverable(self):
        """Add custom deliverable"""
        name = simpledialog.askstring("Nuevo Entregable", "Nombre del entregable:")
        if name:
            messagebox.showinfo("Éxito", f"Entregable '{name}' agregado\n(Funcionalidad completa en próxima versión)")

    def previous_phase(self):
        """Go to previous phase"""
        if self.current_phase > 1:
            self.current_phase -= 1
            self.refresh_ui()

    def next_phase(self):
        """Go to next phase"""
        if self.current_phase < 7:
            self.current_phase += 1
            self.refresh_ui()

    def complete_phase(self):
        """Complete current phase"""
        response = messagebox.askyesno(
            "Completar Fase",
            f"¿Estás seguro de completar la Fase {self.current_phase}?\n\n"
            "Esto marcará la fase como completada y avanzará a la siguiente."
        )

        if response:
            try:
                # TODO: Call backend to complete phase
                messagebox.showinfo("Éxito", f"Fase {self.current_phase} completada!")
                if self.current_phase < 7:
                    self.current_phase += 1
                    self.refresh_ui()
            except Exception as e:
                messagebox.showerror("Error", f"Error al completar fase:\n\n{str(e)}")

    def refresh_ui(self):
        """Refresh UI with new phase"""
        self.window.destroy()
        self.__init__(self.parent, self.auth_manager, self.project)
