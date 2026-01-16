#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Daily Standup Dialog for TEMIS
Quick daily update interface
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests


class DailyStandupDialog:
    """Daily Standup dialog"""
    
    def __init__(self, parent, auth_manager, api_client, project_id, on_complete=None):
        self.parent = parent
        self.auth_manager = auth_manager
        self.api_client = api_client
        self.project_id = project_id
        self.on_complete = on_complete
        
        # Create dialog
        self.window = tk.Toplevel(parent)
        self.window.title("📅 Daily Standup")
        self.window.geometry("500x550")
        self.window.configure(bg="#F9FAFB")
        self.window.transient(parent)
        self.window.grab_set()
        
        self._create_ui()
        self._load_questions()
    
    def _create_ui(self):
        """Create the UI"""
        # Header
        header = tk.Frame(self.window, bg="#3B82F6", height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📅 Daily Standup",
            font=("Arial", 14, "bold"),
            bg="#3B82F6",
            fg="white"
        ).pack(pady=15)
        
        # Content
        content = tk.Frame(self.window, bg="#F9FAFB")
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Project name
        self.project_label = tk.Label(
            content,
            text="",
            font=("Arial", 10),
            bg="#F9FAFB",
            fg="#6B7280"
        )
        self.project_label.pack(pady=(0, 20))
        
        # Questions container
        self.questions_frame = tk.Frame(content, bg="#F9FAFB")
        self.questions_frame.pack(fill='both', expand=True)
        
        # Submit button
        self.submit_btn = tk.Button(
            content,
            text="Registrar Standup",
            command=self._submit_standup,
            bg="#10B981",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        )
        self.submit_btn.pack(pady=(20, 0))
    
    def _load_questions(self):
        """Load standup questions from API"""
        def load():
            try:
                response = requests.get(
                    f"{self.api_client.base_url}/api/wizard/projects/{self.project_id}/daily-standup",
                    params={"user_email": self.auth_manager.user_info.get('email')}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.parent.after(0, lambda: self._display_questions(data))
                else:
                    self.parent.after(0, lambda: messagebox.showerror("Error", "No se pudieron cargar las preguntas"))
                    self.window.destroy()
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
                self.window.destroy()
        
        threading.Thread(target=load, daemon=True).start()
    
    def _display_questions(self, data):
        """Display standup questions"""
        self.project_label.config(text=f"Proyecto: {data.get('project_name', '')}")
        
        self.question_widgets = {}
        
        for question in data.get("questions", []):
            # Question frame
            q_frame = tk.Frame(self.questions_frame, bg="white", relief=tk.SOLID, borderwidth=1)
            q_frame.pack(fill='x', pady=(0, 15))
            
            # Question label
            tk.Label(
                q_frame,
                text=question["question"],
                font=("Arial", 10, "bold"),
                bg="white",
                fg="#1F2937",
                anchor='w'
            ).pack(fill='x', padx=15, pady=(15, 5))
            
            # Text area
            text_widget = tk.Text(
                q_frame,
                font=("Arial", 10),
                bg="#F9FAFB",
                fg="#1F2937",
                relief=tk.FLAT,
                height=4,
                wrap=tk.WORD
            )
            text_widget.pack(fill='x', padx=15, pady=(0, 15))
            text_widget.insert("1.0", question.get("placeholder", ""))
            text_widget.bind("<FocusIn>", lambda e, w=text_widget, p=question.get("placeholder", ""): self._clear_placeholder(w, p))
            
            self.question_widgets[question["id"]] = {
                "widget": text_widget,
                "optional": question.get("optional", False)
            }
    
    def _clear_placeholder(self, widget, placeholder):
        """Clear placeholder text on focus"""
        if widget.get("1.0", "end-1c") == placeholder:
            widget.delete("1.0", "end")
    
    def _submit_standup(self):
        """Submit standup responses"""
        # Collect answers
        answers = {}
        for question_id, data in self.question_widgets.items():
            answer = data["widget"].get("1.0", "end-1c").strip()
            if not answer and not data["optional"]:
                messagebox.showwarning("Campos incompletos", "Por favor completa todas las preguntas obligatorias")
                return
            answers[question_id] = answer
        
        # Submit to API
        def submit():
            try:
                response = requests.post(
                    f"{self.api_client.base_url}/api/wizard/projects/{self.project_id}/daily-standup",
                    json={
                        "project_id": self.project_id,
                        "user_email": self.auth_manager.user_info.get('email'),
                        "yesterday": answers.get("yesterday", ""),
                        "today": answers.get("today", ""),
                        "blockers": answers.get("blockers", "")
                    }
                )
                
                if response.status_code == 200:
                    self.parent.after(0, self._on_success)
                else:
                    self.parent.after(0, lambda: messagebox.showerror("Error", "No se pudo registrar el standup"))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
        
        threading.Thread(target=submit, daemon=True).start()
    
    def _on_success(self):
        """Handle successful submission"""
        messagebox.showinfo("Éxito", "Daily Standup registrado correctamente")
        
        if self.on_complete:
            self.on_complete()
        
        self.window.destroy()
