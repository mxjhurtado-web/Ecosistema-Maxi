#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wizard Dialog for TEMIS
Conversational project creation interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
from datetime import datetime


class WizardDialog:
    """Conversational wizard for project creation"""
    
    def __init__(self, parent, auth_manager, api_client, on_complete=None):
        self.parent = parent
        self.auth_manager = auth_manager
        self.api_client = api_client
        self.on_complete = on_complete
        
        self.session_id = None
        self.conversation_history = []
        
        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("🧙‍♂️ Asistente de Creación de Proyecto")
        self.window.geometry("600x700")
        self.window.configure(bg="#F9FAFB")
        self.window.transient(parent)
        
        # Make sure window appears on top
        self.window.lift()
        self.window.attributes('-topmost', True)
        self.window.after(100, lambda: self.window.attributes('-topmost', False))
        self.window.focus_force()
        
        # DON'T grab_set yet - wait until content is loaded
        
        self._create_ui()
        self._start_wizard()
    
    def _create_ui(self):
        """Create the wizard UI"""
        # Header
        header = tk.Frame(self.window, bg="#1E3A8A", height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="🤖 Asistente TEMIS",
            font=("Arial", 14, "bold"),
            bg="#1E3A8A",
            fg="white"
        ).pack(pady=15)
        
        # Chat area
        chat_frame = tk.Frame(self.window, bg="white")
        chat_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Scrollable chat
        self.chat_canvas = tk.Canvas(chat_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_canvas.yview)
        self.chat_content = tk.Frame(self.chat_canvas, bg="white")
        
        self.chat_content.bind(
            "<Configure>",
            lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        )
        
        self.chat_canvas.create_window((0, 0), window=self.chat_content, anchor="nw", width=540)
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.chat_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Input area
        input_frame = tk.Frame(self.window, bg="#F9FAFB")
        input_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            font=("Arial", 11),
            relief=tk.FLAT,
            bg="white",
            fg="#1F2937"
        )
        self.input_entry.pack(side='left', fill='x', expand=True, ipady=8, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self._send_answer())
        
        self.send_button = tk.Button(
            input_frame,
            text="Enviar",
            command=self._send_answer,
            bg="#3B82F6",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        self.send_button.pack(side='right')
        
        # Options frame (for buttons)
        self.options_frame = tk.Frame(input_frame, bg="#F9FAFB")
        self.options_frame.pack(side='bottom', fill='x', pady=(10, 0))
    
    def _start_wizard(self):
        """Start the wizard session"""
        def start():
            try:
                print(f"[DEBUG] Connecting to {self.api_client.base_url}/api/wizard/start")
                response = requests.post(
                    f"{self.api_client.base_url}/api/wizard/start",
                    json={"user_email": self.auth_manager.user_info.get('email')},
                    timeout=10  # 10 seconds timeout
                )
                
                print(f"[DEBUG] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.session_id = data["session_id"]
                    print(f"[DEBUG] Session ID: {self.session_id}")
                    self.parent.after(0, lambda: self._show_step(data["step"]))
                else:
                    error_msg = f"Error {response.status_code}: {response.text[:200]}"
                    print(f"[ERROR] {error_msg}")
                    self.parent.after(0, lambda: self._show_error_and_close(f"No se pudo iniciar el asistente\n\n{error_msg}"))
            except requests.exceptions.Timeout:
                print("[ERROR] Timeout connecting to backend")
                self.parent.after(0, lambda: self._show_error_and_close("El servidor tardó demasiado en responder.\n\nVerifica que el backend esté corriendo."))
            except requests.exceptions.ConnectionError:
                print("[ERROR] Connection error")
                self.parent.after(0, lambda: self._show_error_and_close("No se pudo conectar al servidor.\n\nVerifica que el backend esté corriendo en http://localhost:8000"))
            except Exception as e:
                print(f"[ERROR] Exception: {e}")
                import traceback
                traceback.print_exc()
                self.parent.after(0, lambda: self._show_error_and_close(f"Error inesperado: {str(e)}"))
        
        threading.Thread(target=start, daemon=True).start()
    
    def _show_error_and_close(self, message):
        """Show error and close window"""
        messagebox.showerror("Error", message)
        try:
            self.window.destroy()
        except:
            pass
    
    def _show_step(self, step):
        """Display a wizard step"""
        try:
            print(f"[DEBUG] _show_step called with step: {step.get('step_id', 'unknown')}")
            print(f"[DEBUG] Step type: {step.get('type', 'text')}")
            print(f"[DEBUG] Message length: {len(step.get('message', ''))}")
            
            # Add assistant message
            self._add_message(step["message"], is_user=False)
            print("[DEBUG] Message added to chat")
            
            # NOW grab the input focus after content is loaded
            try:
                self.window.grab_set()
                print("[DEBUG] Window grab_set applied")
            except:
                pass
            
            # Configure input based on step type
            step_type = step.get("type", "text")
            
            if step_type == "confirmation":
                # Show option buttons
                print("[DEBUG] Showing confirmation options")
                self._show_options(step.get("options", []))
                self.input_entry.config(state='disabled')
            elif step_type == "file_optional":
                # Show file upload button
                print("[DEBUG] Showing file upload")
                self._show_file_upload()
                self.input_entry.config(state='normal')
            elif step_type == "final":
                # Wizard complete
                print("[DEBUG] Wizard final step")
                self.input_entry.config(state='disabled')
                self.send_button.config(state='disabled')
            else:
                # Normal text input
                print("[DEBUG] Showing normal text input")
                self._clear_options()
                self.input_entry.config(state='normal')
                self.input_entry.focus()
            
            print("[DEBUG] _show_step completed successfully")
        except Exception as e:
            print(f"[ERROR] Exception in _show_step: {e}")
            import traceback
            traceback.print_exc()
    
    def _add_message(self, text, is_user=False):
        """Add a message bubble to the chat"""
        bubble_frame = tk.Frame(self.chat_content, bg="white")
        bubble_frame.pack(fill='x', pady=5, padx=10)
        
        # Message bubble
        bubble = tk.Frame(
            bubble_frame,
            bg="#3B82F6" if is_user else "#E5E7EB",
            relief=tk.FLAT
        )
        
        if is_user:
            bubble.pack(side='right', padx=(100, 0))
        else:
            bubble.pack(side='left', padx=(0, 100))
        
        message_label = tk.Label(
            bubble,
            text=text,
            font=("Arial", 10),
            bg="#3B82F6" if is_user else "#E5E7EB",
            fg="white" if is_user else "#1F2937",
            wraplength=400,
            justify='left',
            padx=15,
            pady=10
        )
        message_label.pack()
        
        # Auto-scroll to bottom
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
    
    def _show_options(self, options):
        """Show option buttons"""
        self._clear_options()
        
        for option in options:
            btn = tk.Button(
                self.options_frame,
                text=option,
                command=lambda o=option: self._select_option(o),
                bg="white",
                fg="#1F2937",
                font=("Arial", 10),
                relief=tk.SOLID,
                borderwidth=1,
                padx=15,
                pady=8,
                cursor="hand2"
            )
            btn.pack(side='left', padx=5)
    
    def _show_file_upload(self):
        """Show file upload button"""
        self._clear_options()
        
        btn = tk.Button(
            self.options_frame,
            text="📎 Subir Documento",
            command=self._upload_file,
            bg="#10B981",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        btn.pack(side='left', padx=5)
        
        skip_btn = tk.Button(
            self.options_frame,
            text="Omitir por ahora",
            command=lambda: self._send_answer_value(""),
            bg="white",
            fg="#6B7280",
            font=("Arial", 10),
            relief=tk.SOLID,
            borderwidth=1,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        skip_btn.pack(side='left', padx=5)
    
    def _clear_options(self):
        """Clear option buttons"""
        for widget in self.options_frame.winfo_children():
            widget.destroy()
    
    def _select_option(self, option):
        """Handle option selection"""
        self._add_message(option, is_user=True)
        self._send_answer_value(option)
    
    def _upload_file(self):
        """Handle file upload"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar Documento",
            filetypes=[("Documentos", "*.docx *.pdf *.txt *.md")]
        )
        
        if file_path:
            import os
            filename = os.path.basename(file_path)
            self._add_message(f"📎 {filename}", is_user=True)
            self._send_answer_value(file_path)
    
    def _send_answer(self):
        """Send text answer"""
        answer = self.input_var.get().strip()
        if not answer:
            return
        
        self._add_message(answer, is_user=True)
        self.input_var.set("")
        self._send_answer_value(answer)
    
    def _send_answer_value(self, answer):
        """Send answer to backend"""
        def send():
            try:
                response = requests.post(
                    f"{self.api_client.base_url}/api/wizard/answer",
                    json={
                        "session_id": self.session_id,
                        "answer": answer
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("completed"):
                        # Wizard complete
                        self.parent.after(0, lambda: self._on_wizard_complete(data))
                    elif data.get("error"):
                        # Validation error
                        self.parent.after(0, lambda: self._add_message(f"⚠️ {data['error']}", is_user=False))
                    else:
                        # Next step
                        self.parent.after(0, lambda: self._show_step(data["step"]))
                else:
                    self.parent.after(0, lambda: messagebox.showerror("Error", "Error al procesar respuesta"))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
        
        threading.Thread(target=send, daemon=True).start()
    
    def _on_wizard_complete(self, data):
        """Handle wizard completion"""
        messagebox.showinfo(
            "¡Proyecto Creado!",
            f"Tu proyecto '{data['project_name']}' ha sido creado exitosamente.\n\nYa puedes empezar a trabajar en él."
        )
        
        if self.on_complete:
            self.on_complete(data["project_id"])
        
        self.window.destroy()
