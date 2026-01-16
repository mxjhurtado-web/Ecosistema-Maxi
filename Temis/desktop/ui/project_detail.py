#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project Detail View for TEMIS
Shows comprehensive project information
"""

import tkinter as tk
from tkinter import ttk
import os


class ProjectDetailView:
    """Detailed project view window"""
    
    def __init__(self, parent, auth_manager, api_client, project):
        self.parent = parent
        self.auth_manager = auth_manager
        self.api_client = api_client
        self.project = project
        self.window = None
        self.create_window()
        self.load_project_data()
    
    def create_window(self):
        """Create detail view window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"TEMIS - {self.project['name']}")
        self.window.geometry("1200x800")
        
        # Colors
        bg_color = "#F9FAFB"
        primary_color = "#1E3A8A"
        
        self.window.configure(bg=bg_color)
        
        # Header
        header_frame = tk.Frame(self.window, bg=primary_color, height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Project name
        title_label = tk.Label(
            header_frame,
            text=f"📁 {self.project['name']}",
            font=("Arial", 18, "bold"),
            bg=primary_color,
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=30, pady=20)
        
        # Status badge
        status = self.project.get('status', 'ACTIVE')
        status_color = "#10B981" if status == "ACTIVE" else "#6B7280"
        status_label = tk.Label(
            header_frame,
            text=status,
            font=("Arial", 10, "bold"),
            bg=status_color,
            fg="white",
            padx=15,
            pady=5
        )
        status_label.pack(side=tk.LEFT, padx=10)
        
        # Main content area with scrollbar
        main_container = tk.Frame(self.window, bg=bg_color)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left column (70%)
        left_column = tk.Frame(main_container, bg=bg_color)
        left_column.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 10))
        
        # Right column (30%)
        right_column = tk.Frame(main_container, bg=bg_color, width=300)
        right_column.pack(side=tk.RIGHT, fill='y')
        right_column.pack_propagate(False)
        
        # Create sections
        self.create_description_section(left_column)
        self.create_phases_section(left_column)
        self.create_suggestions_section(right_column)  # NEW: AI Suggestions
        self.create_info_section(right_column)
        self.create_team_section(right_column)
        self.create_actions_section(right_column)
    
    def create_description_section(self, parent):
        """Create description section"""
        section = tk.Frame(parent, bg="white", relief=tk.RAISED, borderwidth=1)
        section.pack(fill='x', pady=(0, 15))
        
        title = tk.Label(
            section,
            text="📝 Descripción",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#1F2937"
        )
        title.pack(anchor='w', padx=20, pady=(15, 10))
        
        desc_text = self.project.get('description', 'Sin descripción')
        desc_label = tk.Label(
            section,
            text=desc_text,
            font=("Arial", 10),
            bg="white",
            fg="#6B7280",
            wraplength=700,
            justify=tk.LEFT
        )
        desc_label.pack(anchor='w', padx=20, pady=(0, 15))
    
    def create_phases_section(self, parent):
        """Create phases progress section"""
        section = tk.Frame(parent, bg="white", relief=tk.RAISED, borderwidth=1)
        section.pack(fill='both', expand=True)
        
        title = tk.Label(
            section,
            text="📊 Fases del Proyecto",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#1F2937"
        )
        title.pack(anchor='w', padx=20, pady=(15, 10))
        
        # Phases list
        self.phases_frame = tk.Frame(section, bg="white")
        self.phases_frame.pack(fill='both', expand=True, padx=20, pady=(0, 15))
    
    def create_info_section(self, parent):
        """Create project info section"""
        section = tk.Frame(parent, bg="white", relief=tk.RAISED, borderwidth=1)
        section.pack(fill='x', pady=(0, 15))
        
        title = tk.Label(
            section,
            text="ℹ️ Información",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#1F2937"
        )
        title.pack(anchor='w', padx=15, pady=(15, 10))
        
        # Project ID
        self.add_info_row(section, "ID:", self.project['id'][:8] + "...")
        
        # Created date
        created = self.project.get('created_at', 'N/A')
        if created and created != 'N/A':
            created = created.split('T')[0]
        self.add_info_row(section, "Creado:", created)
        
        # Current phase
        current_phase = self.project.get('current_phase', 1)
        self.add_info_row(section, "Fase Actual:", f"{current_phase}/7")
        
        tk.Label(section, bg="white", height=1).pack()
    
    def add_info_row(self, parent, label, value):
        """Add info row"""
        row = tk.Frame(parent, bg="white")
        row.pack(fill='x', padx=15, pady=3)
        
        tk.Label(
            row,
            text=label,
            font=("Arial", 9, "bold"),
            bg="white",
            fg="#6B7280"
        ).pack(side=tk.LEFT)
        
        tk.Label(
            row,
            text=value,
            font=("Arial", 9),
            bg="white",
            fg="#1F2937"
        ).pack(side=tk.LEFT, padx=(5, 0))
    
    def create_suggestions_section(self, parent):
        """Create AI suggestions section"""
        from desktop.ui.suggestions_panel import SuggestionsPanel
        
        section = tk.Frame(parent, bg="white", relief=tk.RAISED, borderwidth=1)
        section.pack(fill='both', expand=True, pady=(0, 15))
        
        # Suggestions panel
        self.suggestions_panel = SuggestionsPanel(
            section,
            self.auth_manager,
            self.api_client,
            self.project['id'],
            on_action=self._handle_suggestion_action
        )
        self.suggestions_panel.pack(fill='both', expand=True, padx=15, pady=15)
    
    def _handle_suggestion_action(self, action, phase_number, suggestion):
        """Handle suggestion action click"""
        if action == "start_phase":
            # Scroll to phase
            self._scroll_to_phase(phase_number)
        elif action == "upload_document":
            # Open update from document dialog
            self.update_from_document()
        elif action == "daily_standup":
            # Open daily standup dialog
            self._open_daily_standup()
    
    def _scroll_to_phase(self, phase_number):
        """Scroll to specific phase"""
        # This would scroll to the phase in the phases section
        pass
    
    def _open_daily_standup(self):
        """Open daily standup dialog"""
        from desktop.ui.daily_standup_dialog import DailyStandupDialog
        DailyStandupDialog(
            self.window,
            self.auth_manager,
            self.api_client,
            self.project['id'],
            on_complete=lambda: self.suggestions_panel.refresh()
        )
    
    def create_team_section(self, parent):
        """Create team members section"""
        section = tk.Frame(parent, bg="white", relief=tk.RAISED, borderwidth=1)
        section.pack(fill='x', pady=(0, 15))
        
        title = tk.Label(
            section,
            text="👥 Equipo",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#1F2937"
        )
        title.pack(anchor='w', padx=15, pady=(15, 10))
        
        self.team_frame = tk.Frame(section, bg="white")
        self.team_frame.pack(fill='x', padx=15, pady=(0, 15))
    
    def create_actions_section(self, parent):
        """Create quick actions section"""
        section = tk.Frame(parent, bg="white", relief=tk.RAISED, borderwidth=1)
        section.pack(fill='x')
        
        title = tk.Label(
            section,
            text="⚡ Acciones Rápidas",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#1F2937"
        )
        title.pack(anchor='w', padx=15, pady=(15, 10))
        
        # Chat button
        chat_btn = tk.Button(
            section,
            text="💬 Abrir Chat Diario",
            font=("Arial", 10),
            bg="#10B981",
            fg="white",
            activebackground="#059669",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_chat,
            padx=15,
            pady=8
        )
        chat_btn.pack(fill='x', padx=15, pady=5)
        
        # Management button
        mgmt_btn = tk.Button(
            section,
            text="⚙️ Gestión de Equipo",
            font=("Arial", 10),
            bg="#3B82F6",
            fg="white",
            activebackground="#1E3A8A",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_management,
            padx=15,
            pady=8
        )
        mgmt_btn.pack(fill='x', padx=15, pady=5)
        
        # EOD button
        eod_btn = tk.Button(
            section,
            text="🤖 Procesar Día",
            font=("Arial", 10),
            bg="#F59E0B",
            fg="white",
            activebackground="#D97706",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.process_eod,
            padx=15,
            pady=8
        )
        eod_btn.pack(fill='x', padx=15, pady=5)
        
        # Update from Document button
        update_doc_btn = tk.Button(
            section,
            text="🔄 Actualizar desde Doc",
            font=("Arial", 10),
            bg="#8B5CF6",
            fg="white",
            activebackground="#6D28D9",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.update_from_document,
            padx=15,
            pady=8
        )
        update_doc_btn.pack(fill='x', padx=15, pady=(5, 15))
    
    def update_from_document(self):
        """Update project by selecting a new document"""
        from tkinter import filedialog, messagebox
        import base64
        import threading
        from desktop.core.gemini_config import GeminiConfig
        
        file_path = filedialog.askopenfilename(
            title="Seleccionar Documento Actualizado",
            filetypes=[("Documentos", "*.docx *.pdf *.txt *.md")]
        )
        
        if not file_path:
            return
            
        if not GeminiConfig.has_api_key():
            messagebox.showwarning("API Key Requerida", "Configura tu API Key de Gemini en Configuración")
            return
            
        # Loading indicator
        loading_window = tk.Toplevel(self.window)
        loading_window.title("Procesando...")
        loading_window.geometry("300x150")
        loading_window.transient(self.window)
        loading_window.grab_set()
        
        tk.Label(loading_window, text="🔄 Analizando documento y\nactualizando proyecto...", font=("Arial", 10), pady=20).pack()
        
        def run_update():
            try:
                with open(file_path, 'rb') as f:
                    file_content = base64.b64encode(f.read()).decode('utf-8')
                
                file_extension = os.path.splitext(file_path)[1]
                gemini_api_key = GeminiConfig().get_api_key()
                user_email = self.auth_manager.user_info.get('email')
                
                # Use api_client or direct requests if method not in client
                import requests
                
                response = requests.post(
                    f"{self.api_client.base_url}/api/projects/{self.project['id']}/update-from-document",
                    json={
                        "file_content": file_content,
                        "file_extension": file_extension,
                        "gemini_api_key": gemini_api_key,
                        "user_email": user_email
                    }
                )
                
                loading_window.destroy()
                
                if response.status_code == 200:
                    data = response.json()
                    messagebox.showinfo("Éxito", "¡Proyecto actualizado correctamente!")
                    
                    # Refresh project data
                    self.parent.after(0, self.refresh_view)
                else:
                    messagebox.showerror("Error", f"Error al actualizar: {response.text}")
                    
            except Exception as e:
                loading_window.destroy()
                messagebox.showerror("Error", f"Error crítico: {str(e)}")
        
        threading.Thread(target=run_update, daemon=True).start()

    def refresh_view(self):
        """Refresh the entire project view with updated data"""
        try:
            user_email = self.auth_manager.user_info.get('email')
            # Fetch updated project from API
            updated_project = self.api_client.get_project(self.project['id'], user_email)
            if updated_project:
                self.project = updated_project
                self.load_project_data()
                # Update description label if it exists (need to handle widget update)
                # For simplicity, we can close and reopen or just update the key widgets
                self.window.destroy()
                ProjectDetailView(self.parent, self.auth_manager, self.api_client, self.project)
        except Exception as e:
            print(f"Error refreshing view: {e}")
    
    def load_project_data(self):
        """Load project data from API"""
        # Load phases
        self.load_phases()
        # Load team
        self.load_team()
    
    def load_phases(self):
        """Load project phases from project data"""
        # Clear existing
        for widget in self.phases_frame.winfo_children():
            widget.destroy()
        
        phases = self.project.get('phases', [])
        
        # Fallback if no phases in data (old projects)
        if not phases:
            phase_names = [
                "Portafolio", "Diagnóstico", "Inicio",
                "Planificación", "Ejecución", "Monitoreo", "Cierre"
            ]
            current_phase = self.project.get('current_phase', 1)
            for i, name in enumerate(phase_names, 1):
                self._create_phase_item(i, name, "not_started", 0, "Sin detalles")
            return

        # Sort phases by number
        phases.sort(key=lambda x: x.get('phase_number', 0))
        
        for phase in phases:
            self._create_phase_item(
                phase.get('phase_number', 0),
                phase.get('name', 'Fase'),
                phase.get('status', 'not_started'),
                phase.get('progress', 0),
                phase
            )

    def _create_phase_item(self, num, name, status, progress, phase_data):
        """Create a single phase item in the list"""
        # Status styling
        status_icons = {
            "completed": "✅",
            "in_progress": "🔄",
            "not_started": "⏳"
        }
        status_colors = {
            "completed": "#10B981",
            "in_progress": "#3B82F6",
            "not_started": "#9CA3AF"
        }
        
        icon = status_icons.get(status, "❓")
        color = status_colors.get(status, "#000000")
        
        # Main item frame
        item_frame = tk.Frame(self.phases_frame, bg="white", cursor="hand2")
        item_frame.pack(fill='x', pady=5)
        
        # Label
        label = tk.Label(
            item_frame,
            text=f"{icon} Fase {num}: {name}",
            font=("Arial", 10, "bold" if status == "in_progress" else "normal"),
            bg="white",
            fg=color
        )
        label.pack(side=tk.LEFT, padx=(5, 10))
        
        # Progress container
        progress_container = tk.Frame(item_frame, bg="white")
        progress_container.pack(side=tk.RIGHT, padx=10)
        
        # Percentage label
        tk.Label(
            progress_container,
            text=f"{progress}%",
            font=("Arial", 9),
            bg="white",
            fg="#6B7280",
            width=5
        ).pack(side=tk.RIGHT)
        
        # We'll use a simple canvas for custom progress bar
        canvas = tk.Canvas(progress_container, width=100, height=12, bg="#E5E7EB", highlightthickness=0)
        canvas.pack(side=tk.RIGHT, padx=5)
        
        # Fill
        if progress > 0:
            fill_width = max(2, int(progress))
            fill_color = "#10B981" if status == "completed" else "#3B82F6"
            canvas.create_rectangle(0, 0, fill_width, 12, fill=fill_color, outline="")
            
        # Click binding
        for widget in [item_frame, label, progress_container, canvas]:
             widget.bind("<Button-1>", lambda e, p=phase_data: self.show_phase_detail(p))

    def show_phase_detail(self, phase_data):
        """Show phase details in a pop-up"""
        if isinstance(phase_data, str):
            from tkinter import messagebox
            messagebox.showinfo("Fase", f"Fase: {phase_data}\nNo hay detalles disponibles para este proyecto antiguo.")
            return
            
        detail_window = tk.Toplevel(self.window)
        detail_window.title(f"Detalle: {phase_data.get('name')}")
        detail_window.geometry("500x600")
        detail_window.configure(bg="#F9FAFB")
        detail_window.transient(self.window)
        detail_window.grab_set()
        
        # Container
        main_frame = tk.Frame(detail_window, bg="#F9FAFB")
        main_frame.pack(fill='both', expand=True)
        
        # Scrollable content
        canvas = tk.Canvas(main_frame, bg="#F9FAFB", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#F9FAFB")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=480)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Header
        header = tk.Frame(scrollable_frame, bg="#1E3A8A")
        header.pack(fill='x')
        tk.Label(
            header, 
            text=phase_data.get('name'), 
            font=("Arial", 14, "bold"), 
            bg="#1E3A8A", 
            fg="white"
        ).pack(pady=15)
        
        # Description
        desc_frame = tk.Frame(scrollable_frame, bg="white", padx=20, pady=15)
        desc_frame.pack(fill='x', pady=10, padx=10)
        tk.Label(desc_frame, text="📝 Resumen de la Fase", font=("Arial", 11, "bold"), bg="white", fg="#1E3A8A").pack(anchor='w')
        tk.Label(
            desc_frame, 
            text=phase_data.get('description', 'Sin descripción'), 
            font=("Arial", 10), 
            bg="white", 
            wraplength=440, 
            justify=tk.LEFT,
            fg="#4B5563"
        ).pack(anchor='w', pady=(8, 0))
        
        # Progress
        prog_info_frame = tk.Frame(scrollable_frame, bg="white", padx=20, pady=15)
        prog_info_frame.pack(fill='x', pady=5, padx=10)
        tk.Label(prog_info_frame, text=f"📊 Progreso: {phase_data.get('progress', 0)}%", font=("Arial", 11, "bold"), bg="white", fg="#1E3A8A").pack(anchor='w')
        
        # Tasks
        import json
        tasks_raw = phase_data.get('tasks', '[]')
        try:
            tasks = json.loads(tasks_raw) if isinstance(tasks_raw, str) else tasks_raw
        except:
            tasks = []
            
        tasks_frame = tk.Frame(scrollable_frame, bg="white", padx=20, pady=15)
        tasks_frame.pack(fill='x', pady=5, padx=10)
        tk.Label(tasks_frame, text="✅ Tareas / Actividades", font=("Arial", 11, "bold"), bg="white", fg="#1E3A8A").pack(anchor='w')
        
        if not tasks:
            tk.Label(tasks_frame, text="No hay tareas registradas.", font=("Arial", 10, "italic"), bg="white", fg="#9CA3AF").pack(anchor='w', pady=5)
        else:
            for task in tasks:
                tk.Label(tasks_frame, text=f"• {task}", font=("Arial", 10), bg="white", wraplength=420, justify=tk.LEFT, fg="#4B5563").pack(anchor='w', pady=3)
                
        # Deliverables
        deli_raw = phase_data.get('deliverables', '[]')
        try:
            deliverables = json.loads(deli_raw) if isinstance(deli_raw, str) else deli_raw
        except:
            deliverables = []
            
        deli_frame = tk.Frame(scrollable_frame, bg="white", padx=20, pady=15)
        deli_frame.pack(fill='x', pady=5, padx=10)
        tk.Label(deli_frame, text="📦 Entregables Esperados", font=("Arial", 11, "bold"), bg="white", fg="#1E3A8A").pack(anchor='w')
        
        if not deliverables:
            tk.Label(deli_frame, text="No hay entregables registrados.", font=("Arial", 10, "italic"), bg="white", fg="#9CA3AF").pack(anchor='w', pady=5)
        else:
            for d in deliverables:
                tk.Label(deli_frame, text=f"▫️ {d}", font=("Arial", 10), bg="white", wraplength=420, justify=tk.LEFT, fg="#4B5563").pack(anchor='w', pady=3)
                
        # Close button
        tk.Button(
            scrollable_frame, 
            text="Cerrar", 
            command=detail_window.destroy,
            bg="#3B82F6",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8
        ).pack(pady=20)
    
    def load_team(self):
        """Load team members"""
        # Clear existing
        for widget in self.team_frame.winfo_children():
            widget.destroy()
        
        # Show owner
        user_email = self.auth_manager.user_info.get('email', 'N/A')
        member_label = tk.Label(
            self.team_frame,
            text=f"👤 {user_email} (Owner)",
            font=("Arial", 9),
            bg="white",
            fg="#1F2937"
        )
        member_label.pack(anchor='w', pady=2)
    
    def open_chat(self):
        """Open chat window"""
        from desktop.ui.chat_daily_log import ChatDailyLog
        ChatDailyLog(self.window, self.auth_manager, self.project)
    
    def open_management(self):
        """Open management window"""
        from desktop.ui.project_management import ProjectManagement
        ProjectManagement(self.window, self.auth_manager, self.project)
    
    def process_eod(self):
        """Process end of day"""
        from tkinter import messagebox
        from desktop.core.gemini_config import GeminiConfig
        
        if not GeminiConfig.has_api_key():
            messagebox.showwarning(
                "API Key Requerida",
                "Configura tu API Key de Gemini en Configuración"
            )
            return
        
        try:
            user_email = self.auth_manager.user_info.get('email')
            result = self.api_client.process_eod(self.project['id'], user_email)
            
            if result and result.get('status') == 'success':
                summary = result.get('summary', {})
                messagebox.showinfo(
                    "Procesamiento Completado",
                    f"✅ Día procesado exitosamente!\n\n{summary.get('gemini_summary', '')}"
                )
            else:
                messagebox.showerror("Error", "No se pudo procesar el día")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
