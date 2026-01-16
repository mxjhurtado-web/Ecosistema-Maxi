#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dashboard window for TEMIS
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import threading
import os
from datetime import date

from desktop.core.auth import AuthManager
from desktop.core.api_client import APIClient
from desktop.ui.chat_daily_log import ChatDailyLog
from desktop.core.gemini_config import GeminiConfig


class DashboardWindow:
    """Dashboard window"""

    def __init__(self, parent, auth_manager):
        self.parent = parent
        self.auth_manager = auth_manager
        self.api_client = APIClient(
            os.getenv("API_BASE_URL", "http://localhost:8000"),
            auth_manager.access_token
        )
        self.projects = []
        self.window = None
        self.create_window()
        self.load_projects()

    def create_window(self):
        """Create dashboard window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("TEMIS - Portafolio de Proyectos")
        self.window.geometry("1000x700")

        # Colors
        bg_color = "#F9FAFB"
        primary_color = "#1E3A8A"

        self.window.configure(bg=bg_color)

        # Header
        header_frame = tk.Frame(self.window, bg=primary_color, height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        # Logo and title
        title_label = tk.Label(
            header_frame,
            text="🏛️ TEMIS | Portfolio",
            font=("Arial", 20, "bold"),
            bg=primary_color,
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=20)

        # User info
        user_name = self.auth_manager.user_info.get('name', 'Usuario')
        user_label = tk.Label(
            header_frame,
            text=f"👤 {user_name}",
            font=("Arial", 12),
            bg=primary_color,
            fg="white"
        )
        user_label.pack(side=tk.RIGHT, padx=20, pady=20)

        # Toolbar
        toolbar_frame = tk.Frame(self.window, bg=bg_color)
        toolbar_frame.pack(fill='x', padx=20, pady=10)

        # New project button
        new_project_btn = tk.Button(
            toolbar_frame,
            text="+ Nuevo Proyecto",
            font=("Arial", 12, "bold"),
            bg="#3B82F6",
            fg="white",
            activebackground="#1E3A8A",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.create_project,
            padx=20,
            pady=10
        )
        new_project_btn.pack(side=tk.LEFT, padx=5)

        # Create from document button
        doc_btn = tk.Button(
            toolbar_frame,
            text="📄 Crear desde Documento",
            font=("Arial", 11, "bold"),
            bg="#8B5CF6",
            fg="white",
            activebackground="#7C3AED",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.create_from_document,
            padx=20,
            pady=10
        )
        doc_btn.pack(side=tk.LEFT, padx=5)

        # Wizard button (NEW)
        wizard_btn = tk.Button(
            toolbar_frame,
            text="🧙‍♂️ Crear con Asistente",
            font=("Arial", 10, "bold"),
            bg="#10B981",
            fg="white",
            activebackground="#059669",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.create_with_wizard,
            padx=20,
            pady=10
        )
        wizard_btn.pack(side=tk.LEFT, padx=5)

        # Refresh button
        refresh_btn = tk.Button(
            toolbar_frame,
            text="🔄 Actualizar",
            font=("Arial", 10),
            bg="#E5E7EB",
            fg="#374151",
            activebackground="#D1D5DB",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.load_projects,
            padx=15,
            pady=8
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Settings button
        settings_btn = tk.Button(
            toolbar_frame,
            text="⚙️ Configuración",
            font=("Arial", 10),
            bg="#E5E7EB",
            fg="#374151",
            activebackground="#D1D5DB",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_settings,
            padx=15,
            pady=8
        )
        settings_btn.pack(side=tk.LEFT, padx=5)

        # Import button
        import_btn = tk.Button(
            toolbar_frame,
            text="📥 Importar Proyecto",
            font=("Arial", 10),
            bg="#10B981",
            fg="white",
            activebackground="#059669",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.import_project,
            padx=15,
            pady=8
        )
        import_btn.pack(side=tk.LEFT, padx=5)

        # Projects area with scrollbar
        projects_frame = tk.Frame(self.window, bg=bg_color)
        projects_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Create canvas and scrollbar
        canvas = tk.Canvas(projects_frame, bg=bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(projects_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=bg_color)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_projects(self):
        """Load user's projects"""
        try:
            user_email = self.auth_manager.user_info.get('email')
            self.projects = self.api_client.get_projects(user_email)

            # Clear existing widgets
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            if not self.projects:
                # No projects message
                no_projects_label = tk.Label(
                    self.scrollable_frame,
                    text="No tienes proyectos aún.\nCrea tu primer proyecto usando el botón '+ Nuevo Proyecto'",
                    font=("Arial", 12),
                    bg="#F9FAFB",
                    fg="#6B7280",
                    justify=tk.CENTER
                )
                no_projects_label.pack(pady=50)
                return

            # Display each project
            for project in self.projects:
                self.create_project_card(project)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar proyectos:\n\n{str(e)}")

    def create_project_card(self, project):
        """Create project card widget"""
        card_frame = tk.Frame(
            self.scrollable_frame,
            bg="white",
            relief=tk.RAISED,
            borderwidth=1
        )
        card_frame.pack(fill='x', pady=10, padx=5)

        # Project name
        name_label = tk.Label(
            card_frame,
            text=f"📁 {project['name']}",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#1E3A8A",
            anchor="w"
        )
        name_label.pack(fill='x', padx=15, pady=(15, 5))

        # Project description
        if project.get('description'):
            desc_label = tk.Label(
                card_frame,
                text=project['description'],
                font=("Arial", 10),
                bg="white",
                fg="#6B7280",
                anchor="w",
                wraplength=800
            )
            desc_label.pack(fill='x', padx=15, pady=(0, 10))

        # Status and phase info
        info_frame = tk.Frame(card_frame, bg="white")
        info_frame.pack(fill='x', padx=15, pady=(0, 10))

        status_label = tk.Label(
            info_frame,
            text=f"● {project.get('status', 'active').title()}",
            font=("Arial", 9),
            bg="white",
            fg="#10B981"
        )
        status_label.pack(side=tk.LEFT, padx=(0, 20))

        phase_label = tk.Label(
            info_frame,
            text=f"[Fase {project.get('current_phase', 1)}/7]",
            font=("Arial", 9),
            bg="white",
            fg="#6B7280"
        )
        phase_label.pack(side=tk.LEFT, padx=(0, 20))

        # Buttons
        btn_frame = tk.Frame(card_frame, bg="white")
        btn_frame.pack(fill='x', padx=15, pady=(5, 15))

        open_btn = tk.Button(
            btn_frame,
            text="Abrir",
            font=("Arial", 10),
            bg="#3B82F6",
            fg="white",
            activebackground="#1E3A8A",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda p=project: self.open_project(p),
            padx=15,
            pady=5
        )
        open_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Management button
        mgmt_btn = tk.Button(
            btn_frame,
            text="👥 Gestión",
            font=("Arial", 10),
            bg="#8B5CF6",
            fg="white",
            activebackground="#6D28D9",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda p=project: self.open_management(p),
            padx=15,
            pady=5
        )
        mgmt_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Daily Log button
        daily_log_btn = tk.Button(
            btn_frame,
            text="📝 Diario",
            font=("Arial", 10),
            bg="#10B981",
            fg="white",
            activebackground="#059669",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda p=project: self.open_daily_log(p),
            padx=15,
            pady=5
        )
        daily_log_btn.pack(side=tk.LEFT, padx=(0, 10))

        # EOD button
        eod_btn = tk.Button(
            btn_frame,
            text="🤖 Procesar Día",
            font=("Arial", 10),
            bg="#F59E0B",
            fg="white",
            activebackground="#D97706",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda p=project: self.process_eod(p),
            padx=15,
            pady=5
        )
        eod_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Export button
        export_btn = tk.Button(
            btn_frame,
            text="📤 Exportar",
            font=("Arial", 10),
            bg="#8B5CF6",
            fg="white",
            activebackground="#6D28D9",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda p=project: self.export_project(p),
            padx=15,
            pady=5
        )
        export_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Delete button
        delete_btn = tk.Button(
            btn_frame,
            text="🗑️ Eliminar",
            font=("Arial", 10),
            bg="#EF4444",
            fg="white",
            activebackground="#DC2626",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda p=project: self.delete_project(p),
            padx=15,
            pady=5
        )
        delete_btn.pack(side=tk.RIGHT, padx=(0, 0))

    def create_project(self):
        """Create new project"""
        # Project name
        name = simpledialog.askstring("Nuevo Proyecto", "Nombre del proyecto:")
        if not name:
            return

        # Project description
        description = simpledialog.askstring("Nuevo Proyecto", "Descripción (opcional):")

        try:
            user_email = self.auth_manager.user_info.get('email')
            project_data = {
                "name": name,
                "description": description
            }
            
            project = self.api_client.create_project(user_email, project_data)
            
            messagebox.showinfo("Éxito", f"Proyecto '{name}' creado exitosamente!")
            self.load_projects()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el proyecto:\n\n{str(e)}")

    def delete_project(self, project):
        """Delete project"""
        # Confirm deletion
        response = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar el proyecto '{project['name']}'?\n\n"
            "Esta acción no se puede deshacer."
        )
        
        if not response:
            return

        try:
            user_email = self.auth_manager.user_info.get('email')
            self.api_client.delete_project(project['id'], user_email)
            
            messagebox.showinfo("Éxito", f"Proyecto '{project['name']}' eliminado correctamente")
            self.load_projects()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el proyecto:\n\n{str(e)}")

    def open_project(self, project):
        """Open project detail view"""
        from desktop.ui.project_detail import ProjectDetailView
        ProjectDetailView(self.window, self.auth_manager, self.api_client, project)

    def create_from_document(self):
        """Create project from document with Gemini analysis"""
        from tkinter import filedialog
        import base64
        import os
        
        # Check Gemini API key
        if not GeminiConfig.has_api_key():
            response = messagebox.askyesno(
                "Configuración Requerida",
                "Necesitas configurar tu API Key de Gemini para usar esta funcionalidad.\n\n¿Deseas configurarla ahora?"
            )
            if response:
                self.open_settings()
            return
        
        # File dialog
        file_path = filedialog.askopenfilename(
            title="Seleccionar documento del proyecto",
            filetypes=[
                ("Word", "*.docx"),
                ("PDF", "*.pdf"),
                ("Texto", "*.txt"),
                ("Markdown", "*.md"),
                ("Todos", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Get project name
        project_name = simpledialog.askstring(
            "Nombre del Proyecto",
            "Ingresa el nombre del proyecto:",
            parent=self.window
        )
        
        if not project_name or not project_name.strip():
            return
        
        # Show processing window
        processing_window = tk.Toplevel(self.window)
        processing_window.title("Procesando documento...")
        processing_window.geometry("400x150")
        processing_window.transient(self.window)
        processing_window.grab_set()
        
        label = tk.Label(
            processing_window,
            text="🤖 Gemini está analizando el documento...\n\nEsto puede tomar unos segundos.",
            font=("Arial", 11),
            pady=30,
            padx=20
        )
        label.pack()
        
        progress_label = tk.Label(
            processing_window,
            text="Extrayendo texto del documento...",
            font=("Arial", 9),
            fg="#6B7280"
        )
        progress_label.pack()
        
        # Process in background thread
        def process():
            try:
                # Read file
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Encode to base64
                file_b64 = base64.b64encode(file_content).decode('utf-8')
                
                # Get file extension
                _, file_ext = os.path.splitext(file_path)
                
                # Update progress
                self.window.after(0, lambda: progress_label.config(text="Analizando con Gemini AI..."))
                
                # Call API
                user_email = self.auth_manager.user_info.get('email')
                api_key = GeminiConfig.get_api_key()
                
                # Call API
                user_email = self.auth_manager.user_info.get('email')
                api_key = GeminiConfig.get_api_key()
                
                import requests
                response = requests.post(
                    f"{self.api_client.base_url}/api/projects/create-from-document",
                    headers=self.api_client.headers,
                    json={
                        "project_name": project_name,
                        "file_content": file_b64,
                        "file_extension": file_ext,
                        "gemini_api_key": api_key,
                        "user_email": user_email
                    }
                )
                
                processing_window.destroy()
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result.get('analysis', {})
                    
                    # Show success message with summary
                    summary = analysis.get('project_summary', 'Proyecto creado exitosamente')
                    message = (
                        f"✅ Proyecto creado desde documento!\n\n"
                        f"📋 Resumen:\n{summary}\n\n"
                        f"🎯 Fases creadas: 7\n"
                        f"📁 Carpeta en Drive: Sí"
                    )
                    messagebox.showinfo("Proyecto Creado", message)
                    
                    # Reload projects
                    self.load_projects()
                else:
                    error_msg = response.json().get('detail', 'Error desconocido')
                    messagebox.showerror("Error", f"No se pudo crear el proyecto:\n\n{error_msg}")
                    
            except Exception as e:
                processing_window.destroy()
                messagebox.showerror("Error", f"Error al procesar el documento:\n\n{str(e)}")
        
        # Start processing thread
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def create_with_wizard(self):
        """Create project using AI-assisted form"""
        from desktop.ui.ai_project_form import AIAssistedProjectForm
        
        def on_complete(project_id):
            # Refresh projects list
            self.load_projects()
        
        # Create form (keeps reference to prevent garbage collection)
        AIAssistedProjectForm(
            self.parent,
            self.auth_manager,
            self.api_client,
            on_complete=on_complete
        )

    def open_settings(self):
        """Open settings"""
        from desktop.ui.settings import SettingsWindow
        SettingsWindow(self.parent)

    def open_daily_log(self, project):
        """Open daily log chat interface"""
        ChatDailyLog(self.parent, self.auth_manager, project)

    def open_management(self, project):
        """Open project management"""
        from desktop.ui.project_management import ProjectManagement
        ProjectManagement(self.parent, self.auth_manager, project)

    def process_eod(self, project):
        """Process End of Day"""
        # Check if Gemini API key is configured
        if not GeminiConfig.has_api_key():
            response = messagebox.askyesno(
                "Configuración Requerida",
                "No has configurado tu API key de Gemini.\\n\\n¿Deseas configurarla ahora?"
            )
            if response:
                self.open_settings()
            return

        try:
            # Show processing window
            processing_window = tk.Toplevel(self.window)
            processing_window.title("Procesando...")
            processing_window.geometry("300x100")
            processing_window.transient(self.window)
            processing_window.grab_set()

            label = tk.Label(
                processing_window,
                text="Procesando documento diario con Gemini...\\nEsto puede tomar unos segundos.",
                font=("Arial", 10),
                pady=20
            )
            label.pack()

            # Process in background thread
            def process():
                try:
                    user_email = self.auth_manager.user_info.get('email')
                    result = self.api_client.process_eod(project['id'], user_email)
                    
                    processing_window.destroy()

                    if result and result.get('status') == 'success':
                        summary = result.get('summary', {})
                        message_count = summary.get('message_count', 0)
                        drive_backup = summary.get('drive_backup', False)
                        gemini_summary = summary.get('gemini_summary', 'N/A')
                        
                        message = (
                            f"Procesamiento completado exitosamente!\n\n"
                            f"Mensajes procesados: {message_count}\n"
                            f"Backup en Drive: {'Si' if drive_backup else 'No'}\n\n"
                            f"Resumen del dia:\n{gemini_summary}"
                        )
                        messagebox.showinfo("Procesamiento Completado", message)
                    else:
                        error_msg = result.get('message', 'No se pudo procesar el documento') if result else 'No se pudo procesar el documento'
                        messagebox.showerror("Error", error_msg)

                except Exception as e:
                    processing_window.destroy()
                    messagebox.showerror("Error", f"Error al procesar:\\n\\n{str(e)}")

            thread = threading.Thread(target=process)
            thread.daemon = True
            thread.start()

        except Exception as e:
            if 'processing_window' in locals():
                processing_window.destroy()
            messagebox.showerror(
                "Error de Configuración",
                f"No se pudo procesar el documento:\\n\\n{str(e)}\\n\\n"
                "Verifica que:\\n"
                "• Tu API key de Gemini sea válida\\n"
                "• Tengas conexión a internet"
            )

    def export_project(self, project):
        """Show project export code"""
        export_window = tk.Toplevel(self.window)
        export_window.title("Exportar Proyecto")
        export_window.geometry("500x300")
        export_window.transient(self.window)
        export_window.grab_set()
        
        tk.Label(
            export_window,
            text=f"Código del Proyecto: {project['name']}",
            font=("Arial", 12, "bold"),
            pady=10
        ).pack()
        
        code_frame = tk.Frame(export_window, bg="#F3F4F6", relief=tk.RAISED, borderwidth=2)
        code_frame.pack(fill='x', padx=20, pady=10)
        
        code_label = tk.Label(
            code_frame,
            text=project['id'],
            font=("Courier", 11),
            bg="#F3F4F6",
            fg="#1E3A8A",
            pady=15
        )
        code_label.pack()
        
        def copy_code():
            self.window.clipboard_clear()
            self.window.clipboard_append(project['id'])
            messagebox.showinfo("Copiado", "Código copiado al portapapeles")
        
        tk.Button(
            export_window,
            text="📋 Copiar Código",
            command=copy_code,
            bg="#3B82F6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=8
        ).pack(pady=10)
        
        tk.Label(
            export_window,
            text="Comparte este código con otros usuarios para que puedan importar el proyecto.",
            font=("Arial", 9),
            fg="#6B7280",
            wraplength=400
        ).pack(pady=10)

    def import_project(self):
        """Import project by code"""
        code = simpledialog.askstring("Importar Proyecto", "Ingresa el código del proyecto:")
        if not code:
            return
        
        try:
            user_email = self.auth_manager.user_info.get('email')
            project = self.api_client.import_project(code, user_email)
            messagebox.showinfo("Éxito", f"Proyecto '{project['name']}' importado exitosamente!")
            self.load_projects()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar el proyecto:\n\n{str(e)}")

    def on_close(self):
        """Handle window close"""
        self.parent.quit()
