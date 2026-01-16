#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Suggestions Panel for TEMIS
Displays contextual recommendations for project continuity
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests


class SuggestionsPanel(tk.Frame):
    """Panel that shows AI-powered suggestions for project"""
    
    def __init__(self, parent, auth_manager, api_client, project_id, on_action=None):
        super().__init__(parent, bg="#F9FAFB")
        
        self.auth_manager = auth_manager
        self.api_client = api_client
        self.project_id = project_id
        self.on_action = on_action
        
        self.suggestions = []
        self.is_collapsed = True  # Start collapsed for better UX
        
        self._create_ui()
        self._load_suggestions()
    
    def _create_ui(self):
        """Create the suggestions panel UI"""
        # Header with collapse button
        header = tk.Frame(self, bg="#F9FAFB")
        header.pack(fill='x', pady=(0, 10))
        
        # Collapse/Expand button
        self.toggle_btn = tk.Button(
            header,
            text="▶",  # Start with collapsed icon
            command=self._toggle_collapse,
            bg="white",
            fg="#6B7280",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=6,
            pady=2
        )
        self.toggle_btn.pack(side='left', padx=(0, 8))
        
        tk.Label(
            header,
            text="💡 Sugerencias del Asistente",
            font=("Arial", 12, "bold"),
            bg="#F9FAFB",
            fg="#1F2937"
        ).pack(side='left')
        
        # Refresh button
        refresh_btn = tk.Button(
            header,
            text="🔄",
            command=self._load_suggestions,
            bg="white",
            fg="#6B7280",
            font=("Arial", 10),
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=4
        )
        refresh_btn.pack(side='right')
        
        # Scrollable container with limited height
        self.container_frame = tk.Frame(self, bg="#F9FAFB")
        # Don't pack initially - starts collapsed
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(
            self.container_frame,
            bg="#F9FAFB",
            highlightthickness=0,
            height=300  # Limited initial height
        )
        self.scrollbar = tk.Scrollbar(
            self.container_frame,
            orient="vertical",
            command=self.canvas.yview
        )
        
        # Suggestions container
        self.suggestions_container = tk.Frame(self.canvas, bg="#F9FAFB")
        
        # Configure scroll region when content changes
        self.suggestions_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas with proper width binding
        self.canvas_window = self.canvas.create_window((0, 0), window=self.suggestions_container, anchor="nw")
        
        # Bind canvas width to update window width
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Loading indicator
        self.loading_label = tk.Label(
            self.suggestions_container,
            text="Cargando sugerencias...",
            font=("Arial", 10),
            bg="#F9FAFB",
            fg="#6B7280"
        )
        self.loading_label.pack(pady=20)
    
    def _toggle_collapse(self):
        """Toggle collapse/expand state"""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            # Collapse
            self.toggle_btn.config(text="▶")
            self.container_frame.pack_forget()
        else:
            # Expand
            self.toggle_btn.config(text="▼")
            self.container_frame.pack(fill='both', expand=False)
    
    def _load_suggestions(self):
        """Load suggestions from API"""
        self.loading_label.pack(pady=20)
        
        for widget in self.suggestions_container.winfo_children():
            if widget != self.loading_label:
                widget.destroy()
        
        def load():
            try:
                response = requests.get(
                    f"{self.api_client.base_url}/api/wizard/projects/{self.project_id}/suggestions",
                    params={"user_email": self.auth_manager.user_info.get('email')}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.suggestions = data.get("suggestions", [])
                    self.after(0, self._display_suggestions)
                else:
                    self.after(0, lambda: self._show_error("No se pudieron cargar las sugerencias"))
            except Exception as e:
                self.after(0, lambda: self._show_error(f"Error: {str(e)}"))
        
        threading.Thread(target=load, daemon=True).start()
    
    def _display_suggestions(self):
        """Display loaded suggestions"""
        self.loading_label.pack_forget()
        
        if not self.suggestions:
            # No suggestions
            tk.Label(
                self.suggestions_container,
                text="✅ ¡Todo al día!\n\nNo hay sugerencias pendientes por ahora.",
                font=("Arial", 10),
                bg="#F9FAFB",
                fg="#6B7280",
                justify='center'
            ).pack(pady=30)
            return
        
        # Display each suggestion
        for suggestion in self.suggestions:
            self._create_suggestion_card(suggestion)
    
    def _create_suggestion_card(self, suggestion):
        """Create a suggestion card"""
        # Priority colors
        priority_colors = {
            "urgent": "#EF4444",
            "high": "#F59E0B",
            "medium": "#3B82F6",
            "low": "#6B7280"
        }
        
        priority = suggestion.get("priority", "medium")
        color = priority_colors.get(priority, "#6B7280")
        
        # Card container
        card = tk.Frame(
            self.suggestions_container,
            bg="white",
            relief=tk.SOLID,
            borderwidth=1,
            highlightbackground=color,
            highlightthickness=2
        )
        card.pack(fill='x', pady=5, padx=5)
        
        # Content
        content = tk.Frame(card, bg="white")
        content.pack(fill='both', expand=True, padx=15, pady=12)
        
        # Priority badge
        priority_frame = tk.Frame(content, bg="white")
        priority_frame.pack(fill='x', pady=(0, 8))
        
        priority_label = tk.Label(
            priority_frame,
            text=f"{suggestion.get('icon', '💡')} {priority.upper()}",
            font=("Arial", 8, "bold"),
            bg=color,
            fg="white",
            padx=8,
            pady=2
        )
        priority_label.pack(side='left')
        
        # Title
        tk.Label(
            content,
            text=suggestion.get("title", ""),
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#1F2937",
            anchor='w'
        ).pack(fill='x', pady=(0, 5))
        
        # Message
        tk.Label(
            content,
            text=suggestion.get("message", ""),
            font=("Arial", 9),
            bg="white",
            fg="#4B5563",
            anchor='w',
            wraplength=400,
            justify='left'
        ).pack(fill='x', pady=(0, 5))
        
        # Details
        if suggestion.get("details"):
            tk.Label(
                content,
                text=suggestion["details"],
                font=("Arial", 8, "italic"),
                bg="white",
                fg="#6B7280",
                anchor='w',
                wraplength=400,
                justify='left'
            ).pack(fill='x', pady=(0, 10))
        
        # Action button
        action_btn = tk.Button(
            content,
            text=suggestion.get("action_label", "Ir"),
            command=lambda s=suggestion: self._handle_action(s),
            bg=color,
            fg="white",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=6
        )
        action_btn.pack(side='left')
    
    def _handle_action(self, suggestion):
        """Handle suggestion action"""
        action = suggestion.get("action")
        phase_number = suggestion.get("phase_number")
        
        if self.on_action:
            self.on_action(action, phase_number, suggestion)
    
    def _show_error(self, message):
        """Show error message"""
        self.loading_label.pack_forget()
        tk.Label(
            self.suggestions_container,
            text=f"⚠️ {message}",
            font=("Arial", 10),
            bg="#F9FAFB",
            fg="#EF4444"
        ).pack(pady=20)
    
    def refresh(self):
        """Refresh suggestions"""
        self._load_suggestions()
