#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chat Daily Log - Conversational interface for TEMIS
Replaces the Markdown editor with a friendly chat interface
"""

import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import os
from datetime import datetime, date

from desktop.core.api_client import APIClient
from desktop.core.gemini_config import GeminiConfig


class ChatDailyLog:
    """Chat interface for daily log"""

    def __init__(self, parent, auth_manager, project):
        self.parent = parent
        self.auth_manager = auth_manager
        self.project = project
        self.api_client = APIClient(
            os.getenv("API_BASE_URL", "http://localhost:8000"),
            auth_manager.access_token
        )
        self.messages = []
        self.attachments = []
        self.window = None
        self.create_window()
        self.load_conversation()

    def create_window(self):
        """Create chat window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"TEMIS - Chat Diario: {self.project['name']}")
        self.window.geometry("1100x750")

        # Colors
        bg_color = "#F9FAFB"
        primary_color = "#3B82F6"
        temis_bubble = "#FFFFFF"
        user_bubble = "#DBEAFE"

        self.window.configure(bg=bg_color)

        # Header
        header_frame = tk.Frame(self.window, bg=primary_color, height=70)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        # Header left: Title
        title_label = tk.Label(
            header_frame,
            text=f"💬 Chat Diario - {self.project['name']}",
            font=("Arial", 16, "bold"),
            bg=primary_color,
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)

        # Header right: Phase info and buttons
        header_right = tk.Frame(header_frame, bg=primary_color)
        header_right.pack(side=tk.RIGHT, padx=20, pady=10)

        # Phase indicator
        phase_label = tk.Label(
            header_right,
            text=f"Fase {self.project.get('current_phase', 1)}/7",
            font=("Arial", 11, "bold"),
            bg="#1E3A8A",
            fg="white",
            padx=12,
            pady=6,
            relief=tk.RAISED
        )
        phase_label.pack(side=tk.LEFT, padx=5)

        # Wizard button
        wizard_btn = tk.Button(
            header_right,
            text="🧭 Wizard",
            font=("Arial", 10, "bold"),
            bg="#8B5CF6",
            fg="white",
            activebackground="#6D28D9",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_wizard,
            padx=12,
            pady=6
        )
        wizard_btn.pack(side=tk.LEFT, padx=5)

        # Settings button
        settings_btn = tk.Button(
            header_right,
            text="⚙️",
            font=("Arial", 14),
            bg="#6B7280",
            fg="white",
            activebackground="#4B5563",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_settings,
            padx=10,
            pady=6
        )
        settings_btn.pack(side=tk.LEFT, padx=5)

        # Main container
        main_container = tk.Frame(self.window, bg=bg_color)
        main_container.pack(fill='both', expand=True)

        # Sidebar (20%)
        self.create_sidebar(main_container)

        # Chat area (80%)
        self.create_chat_area(main_container)

        # Input area
        self.create_input_area()

    def create_sidebar(self, parent):
        """Create sidebar with conversation history"""
        sidebar = tk.Frame(parent, bg="#E5E7EB", width=220, relief=tk.RAISED, borderwidth=1)
        sidebar.pack(side=tk.LEFT, fill='y')
        sidebar.pack_propagate(False)

        # Title
        title = tk.Label(
            sidebar,
            text="Conversaciones\nAnteriores",
            font=("Arial", 11, "bold"),
            bg="#E5E7EB",
            fg="#374151",
            justify=tk.CENTER
        )
        title.pack(pady=15)

        # Separator
        separator = tk.Frame(sidebar, bg="#D1D5DB", height=1)
        separator.pack(fill='x', padx=10)

        # Assistant Actions
        actions_label = tk.Label(
            sidebar,
            text="Asistente",
            font=("Arial", 11, "bold"),
            bg="#E5E7EB",
            fg="#374151"
        )
        actions_label.pack(pady=(15, 5))

        analyze_btn = tk.Button(
            sidebar,
            text="📊 Analizar Estado",
            font=("Arial", 10),
            bg="#8B5CF6",
            fg="white",
            activebackground="#7C3AED",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.analyze_project,
            padx=10,
            pady=5
        )
        analyze_btn.pack(fill='x', padx=15, pady=5)

        # Conversation list (scrollable)
        list_frame = tk.Frame(sidebar, bg="#E5E7EB")
        list_frame.pack(fill='both', expand=True, pady=10)

        # Sample dates (TODO: Load from backend)
        dates = [
            date.today(),
            date(2026, 1, 13),
            date(2026, 1, 12),
            date(2026, 1, 9)
        ]

        for conv_date in dates:
            self.create_conversation_item(list_frame, conv_date)

        # New conversation button
        new_btn = tk.Button(
            sidebar,
            text="+ Nueva Conversación",
            font=("Arial", 10, "bold"),
            bg="#3B82F6",
            fg="white",
            activebackground="#1E3A8A",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.new_conversation,
            padx=15,
            pady=10
        )
        new_btn.pack(side=tk.BOTTOM, pady=15, padx=10, fill='x')

    def create_conversation_item(self, parent, conv_date):
        """Create conversation item in sidebar"""
        is_today = conv_date == date.today()
        
        item_frame = tk.Frame(
            parent,
            bg="#DBEAFE" if is_today else "#E5E7EB",
            relief=tk.FLAT,
            cursor="hand2"
        )
        item_frame.pack(fill='x', padx=10, pady=3)

        date_label = tk.Label(
            item_frame,
            text=f"📅 {conv_date.strftime('%Y-%m-%d')}",
            font=("Arial", 9, "bold" if is_today else "normal"),
            bg="#DBEAFE" if is_today else "#E5E7EB",
            fg="#1E3A8A" if is_today else "#6B7280",
            anchor="w"
        )
        date_label.pack(fill='x', padx=10, pady=8)

        # Click to load conversation
        item_frame.bind("<Button-1>", lambda e: self.load_conversation_date(conv_date))
        date_label.bind("<Button-1>", lambda e: self.load_conversation_date(conv_date))

    def create_chat_area(self, parent):
        """Create main chat area"""
        chat_container = tk.Frame(parent, bg="#F9FAFB")
        chat_container.pack(side=tk.LEFT, fill='both', expand=True)

        # Date header
        date_header = tk.Label(
            chat_container,
            text=date.today().strftime('%A, %d de %B de %Y'),
            font=("Arial", 10),
            bg="#F9FAFB",
            fg="#6B7280"
        )
        date_header.pack(pady=10)

        # Scrollable chat area
        canvas = tk.Canvas(chat_container, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(chat_container, orient="vertical", command=canvas.yview)
        self.chat_frame = tk.Frame(canvas, bg="white")

        self.chat_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.chat_frame, anchor="nw", width=850)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        scrollbar.pack(side="right", fill="y")

        self.canvas = canvas

    def create_input_area(self):
        """Create input area with text box and buttons"""
        input_container = tk.Frame(self.window, bg="#F9FAFB", height=100)
        input_container.pack(fill='x', side=tk.BOTTOM)
        input_container.pack_propagate(False)

        # Attachments preview area
        self.attachments_frame = tk.Frame(input_container, bg="#F9FAFB")
        self.attachments_frame.pack(fill='x', padx=20, pady=(5, 0))

        # Input frame
        input_frame = tk.Frame(input_container, bg="white", relief=tk.RAISED, borderwidth=1)
        input_frame.pack(fill='x', padx=20, pady=10)

        # Attach button
        attach_btn = tk.Button(
            input_frame,
            text="📎",
            font=("Arial", 16),
            bg="white",
            fg="#6B7280",
            activebackground="#F3F4F6",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.attach_file,
            padx=10
        )
        attach_btn.pack(side=tk.LEFT, padx=5)
        
        # Link/Resource button
        link_btn = tk.Button(
            input_frame,
            text="🔗",
            font=("Arial", 16),
            bg="white",
            fg="#8B5CF6",
            activebackground="#F3F4F6",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.add_resource_link,
            padx=10
        )
        link_btn.pack(side=tk.LEFT, padx=5)

        # Text input
        self.input_text = tk.Text(
            input_frame,
            font=("Arial", 11),
            bg="white",
            fg="#1F2937",
            relief=tk.FLAT,
            height=2,
            wrap=tk.WORD
        )
        self.input_text.pack(side=tk.LEFT, fill='both', expand=True, padx=5, pady=8)

        # Bind Enter key
        self.input_text.bind("<Return>", lambda e: self.send_message())
        self.input_text.bind("<Shift-Return>", lambda e: None)  # Allow Shift+Enter for new line

        # Send button
        send_btn = tk.Button(
            input_frame,
            text="↑",
            font=("Arial", 18, "bold"),
            bg="#3B82F6",
            fg="white",
            activebackground="#1E3A8A",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.send_message,
            width=3,
            height=1
        )
        send_btn.pack(side=tk.RIGHT, padx=5)

        # Placeholder
        self.input_text.insert("1.0", "Escribe tu mensaje...")
        self.input_text.config(fg="#9CA3AF")
        self.input_text.bind("<FocusIn>", self.clear_placeholder)
        self.input_text.bind("<FocusOut>", self.restore_placeholder)

    def clear_placeholder(self, event):
        """Clear placeholder text"""
        if self.input_text.get("1.0", "end-1c") == "Escribe tu mensaje...":
            self.input_text.delete("1.0", tk.END)
            self.input_text.config(fg="#1F2937")

    def restore_placeholder(self, event):
        """Restore placeholder if empty"""
        if not self.input_text.get("1.0", "end-1c").strip():
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", "Escribe tu mensaje...")
            self.input_text.config(fg="#9CA3AF")

    def load_conversation(self):
        """Load today's conversation from database"""
        try:
            import requests
            user_email = self.auth_manager.user_info.get('email')
            today = date.today().isoformat()
            
            # Get messages from backend
            response = requests.get(
                f"{self.api_client.base_url}/api/chat/messages",
                headers=self.api_client.headers,
                params={
                    "project_id": self.project['id'],
                    "message_date": today,
                    "user_email": user_email
                }
            )
            
            if response.status_code == 200:
                messages = response.json()
                
                if messages:
                    # Load existing messages
                    for msg in messages:
                        if msg['role'] == 'assistant':
                            self.add_temis_message(msg['content'], save_to_db=False)
                        else:
                            self.add_user_message(msg['content'], save_to_db=False)
                else:
                    # No messages today, add welcome
                    self.add_temis_message("¡Hola! ¿Qué avances tienes hoy? 😊")
            else:
                # Fallback to welcome message
                self.add_temis_message("¡Hola! ¿Qué avances tienes hoy? 😊")
                
        except Exception as e:
            print(f"Error loading conversation: {e}")
            # Fallback to welcome message
            self.add_temis_message("¡Hola! ¿Qué avances tienes hoy? 😊")

    def add_temis_message(self, message, save_to_db=True):
        """Add TEMIS message to chat"""
        # Save to history
        self.messages.append({
            'sender': 'temis',
            'content': message,
            'timestamp': datetime.now()
        })
        
        # Save to database
        if save_to_db:
            self.save_message_to_db('assistant', message)
        
        msg_frame = tk.Frame(self.chat_frame, bg="white")
        msg_frame.pack(fill='x', padx=20, pady=8, anchor='w')

        # Avatar
        avatar = tk.Label(
            msg_frame,
            text="🤖",
            font=("Arial", 20),
            bg="white"
        )
        avatar.pack(side=tk.LEFT, padx=(0, 10))

        # Message bubble
        bubble_frame = tk.Frame(msg_frame, bg="white")
        bubble_frame.pack(side=tk.LEFT, fill='x')

        name_label = tk.Label(
            bubble_frame,
            text="TEMIS Assistant",
            font=("Arial", 9, "bold"),
            bg="white",
            fg="#6B7280"
        )
        name_label.pack(anchor='w')

        bubble = tk.Label(
            bubble_frame,
            text=message,
            font=("Arial", 11),
            bg="#FFFFFF",
            fg="#1F2937",
            relief=tk.RAISED,
            borderwidth=1,
            padx=15,
            pady=10,
            wraplength=500,
            justify=tk.LEFT,
            anchor='w'
        )
        bubble.pack(anchor='w')

        time_label = tk.Label(
            bubble_frame,
            text=datetime.now().strftime('%H:%M'),
            font=("Arial", 8),
            bg="white",
            fg="#9CA3AF"
        )
        time_label.pack(anchor='w', pady=(2, 0))

        # Auto-scroll to bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def add_user_message(self, message, save_to_db=True):
        """Add user message to chat"""
        # Save to database
        if save_to_db:
            self.save_message_to_db('user', message)
        msg_frame = tk.Frame(self.chat_frame, bg="white")
        msg_frame.pack(fill='x', padx=20, pady=8, anchor='e')

        # Message bubble
        bubble = tk.Label(
            msg_frame,
            text=message,
            font=("Arial", 11),
            bg="#DBEAFE",
            fg="#1F2937",
            relief=tk.FLAT,
            padx=15,
            pady=10,
            wraplength=500,
            justify=tk.LEFT
        )
        bubble.pack(side=tk.RIGHT)

        time_label = tk.Label(
            msg_frame,
            text=datetime.now().strftime('%H:%M'),
            font=("Arial", 8),
            bg="white",
            fg="#9CA3AF"
        )
        time_label.pack(side=tk.RIGHT, padx=(0, 10))

        # Auto-scroll to bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def send_message(self):
        """Send message"""
        message = self.input_text.get("1.0", "end-1c").strip()
        
        if not message or message == "Escribe tu mensaje...":
            return "break"  # Prevent default Enter behavior

        # Save user message to history
        self.messages.append({
            'sender': 'user',
            'content': message,
            'timestamp': datetime.now()
        })

        # Add user message to chat
        self.add_user_message(message)

        # Clear input
        self.input_text.delete("1.0", tk.END)

        # Get TEMIS response with Gemini
        self.window.after(1000, lambda: self.simulate_temis_response(message))

        return "break"  # Prevent default Enter behavior

    def simulate_temis_response(self, user_message):
        """Get TEMIS response using Gemini via backend"""
        # Check if Gemini API key is configured
        api_key = GeminiConfig.get_api_key()

        if not api_key:
            # Fallback to simple responses if no API key
            self.add_temis_message("⚙️ Para respuestas inteligentes, configura tu API Key de Gemini en Configuración.")
            return

        try:
            import requests
            user_email = self.auth_manager.user_info.get('email')
            
            # Build context from recent messages
            context = self.build_conversation_context()
            
            # Call backend Gemini endpoint
            response = requests.post(
                f"{self.api_client.base_url}/api/chat/gemini",
                headers=self.api_client.headers,
                params={"user_email": user_email, "gemini_api_key": api_key},
                json={
                    "project_id": self.project['id'],
                    "message": user_message,
                    "context": context
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                temis_response = result.get('response', 'Entendido. ¿Hay algo más?')
                self.add_temis_message(temis_response)
            else:
                print(f"Error from Gemini API: {response.status_code}")
                self.add_temis_message("Entendido. ¿Hay algo más que quieras documentar?")
            
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            # Fallback to simple response
            self.add_temis_message("Entendido. ¿Hay algo más que quieras documentar?")

    def build_conversation_context(self):
        """Build conversation context for Gemini"""
        # Get last 5 messages for context
        context_lines = []
        for msg in self.messages[-5:]:
            sender = "Usuario" if msg['sender'] == 'user' else "TEMIS"
            context_lines.append(f"{sender}: {msg['content']}")
        return "\n".join(context_lines)

    def attach_file(self):
        """Attach file"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[
                ("Todos los archivos", "*.*"),
                ("PDFs", "*.pdf"),
                ("Imágenes", "*.png *.jpg *.jpeg"),
                ("Excel", "*.xlsx *.xls"),
                ("Word", "*.docx *.doc")
            ]
        )

        if file_path:
            self.attachments.append(file_path)
            self.display_attachment(file_path)

    def display_attachment(self, file_path):
        """Display attachment in preview area"""
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / 1024  # KB

        attachment_card = tk.Frame(
            self.attachments_frame,
            bg="#D1FAE5",
            relief=tk.RAISED,
            borderwidth=1
        )
        attachment_card.pack(side=tk.LEFT, padx=5, pady=5)

        icon_label = tk.Label(
            attachment_card,
            text="📄",
            font=("Arial", 16),
            bg="#D1FAE5"
        )
        icon_label.pack(side=tk.LEFT, padx=5)

        info_frame = tk.Frame(attachment_card, bg="#D1FAE5")
        info_frame.pack(side=tk.LEFT, padx=5, pady=5)

        name_label = tk.Label(
            info_frame,
            text=filename,
            font=("Arial", 9, "bold"),
            bg="#D1FAE5",
            fg="#065F46"
        )
        name_label.pack(anchor='w')

        size_label = tk.Label(
            info_frame,
            text=f"{file_size:.1f} KB",
            font=("Arial", 8),
            bg="#D1FAE5",
            fg="#059669"
        )
        size_label.pack(anchor='w')

        # Remove button
        remove_btn = tk.Button(
            attachment_card,
            text="✕",
            font=("Arial", 10),
            bg="#D1FAE5",
            fg="#065F46",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.remove_attachment(file_path, attachment_card)
        )
        remove_btn.pack(side=tk.RIGHT, padx=5)

    def remove_attachment(self, file_path, card):
        """Remove attachment"""
        self.attachments.remove(file_path)
        card.destroy()

    def new_conversation(self):
        """Start new conversation"""
        messagebox.showinfo("Nueva Conversación", "Iniciando nueva conversación...")

    def load_conversation_date(self, conv_date):
        """Load conversation for specific date"""
        messagebox.showinfo("Cargar Conversación", f"Cargando conversación del {conv_date}")

    def open_wizard(self):
        """Open phase wizard"""
        from desktop.ui.phase_wizard import PhaseWizard
        PhaseWizard(self.parent, self.auth_manager, self.project)

    def open_settings(self):
        """Open Gemini settings"""
        from desktop.ui.settings import SettingsWindow
        SettingsWindow(self.window)
    
    def save_message_to_db(self, role, content):
        """Save message to database"""
        try:
            import requests
            user_email = self.auth_manager.user_info.get('email')
            today = date.today().isoformat()
            
            response = requests.post(
                f"{self.api_client.base_url}/api/chat/message",
                headers=self.api_client.headers,
                params={"user_email": user_email},
                json={
                    "project_id": self.project['id'],
                    "message_date": today,
                    "role": role,
                    "content": content,
                    "attachments": []
                }
            )
            
            if response.status_code != 200:
                print(f"Error saving message: {response.status_code}")
                
        except Exception as e:
            print(f"Error saving message to DB: {e}")

    def analyze_project(self):
        """Analyze project status using Gemini"""
        # Check Gemini API key
        if not GeminiConfig.has_api_key():
            self.add_temis_message("⚙️ Para analizar el proyecto, configura tu API Key de Gemini en Configuración.")
            return

        self.add_temis_message("🔄 Analizando estado del proyecto y fases... un momento por favor.")
        
        def run_analysis():
            try:
                import requests
                user_email = self.auth_manager.user_info.get('email')
                api_key = GeminiConfig.get_api_key()
                
                response = requests.post(
                    f"{self.api_client.base_url}/api/chat/analyze",
                    headers=self.api_client.headers,
                    params={"user_email": user_email, "gemini_api_key": api_key},
                    json={
                        "project_id": self.project['id'],
                        "message": "analyze",  # Dummy message
                        "context": ""
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis_text = result.get('response', 'No se pudo generar el análisis.')
                    self.window.after(0, lambda: self.add_temis_message(analysis_text))
                else:
                    error_msg = f"Error en análisis: {response.status_code}"
                    self.window.after(0, lambda: self.add_temis_message(error_msg))
                    
            except Exception as e:
                error_msg = f"Error al conectar con el asistente: {str(e)}"
                self.window.after(0, lambda: self.add_temis_message(error_msg))
        
        # Run in background
        import threading
        threading.Thread(target=run_analysis, daemon=True).start()
    
    def add_resource_link(self):
        """Add a resource link - reuse the same dialog from daily_log_editor"""
        from desktop.ui.daily_log_editor import DailyLogEditor
        
        # Create a temporary dialog similar to the one in daily_log_editor
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
            
            # Create link message
            link_message = f"📚 **{title}** ({category})\n"
            link_message += f"🔗 {url}\n"
            if description:
                link_message += f"📝 {description}\n"
            
            # Add as user message
            self.add_user_message(link_message)
            dialog.destroy()
            
            messagebox.showinfo(
                "Link Agregado",
                f"✅ Link agregado al chat!\n\nEste recurso se guardará en el historial del proyecto."
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
