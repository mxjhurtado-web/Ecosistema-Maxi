#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Document Preview Dialog for TEMIS
Shows live preview of generated documents
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import subprocess


class DocumentPreviewDialog:
    """Dialog to preview and edit generated documents"""
    
    def __init__(self, parent, document_name, content, on_save=None):
        self.parent = parent
        self.document_name = document_name
        self.content = content
        self.on_save = on_save
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Vista Previa: {document_name}")
        self.window.geometry("900x700")
        self.window.configure(bg="#F9FAFB")
        
        self._create_ui()
        
    def _create_ui(self):
        """Create the preview UI"""
        # Header
        header = tk.Frame(self.window, bg="#1E3A8A", height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"📄 Vista Previa: {self.document_name}",
            font=("Arial", 14, "bold"),
            bg="#1E3A8A",
            fg="white"
        ).pack(side='left', padx=20, pady=20)
        
        # Info label
        info_frame = tk.Frame(self.window, bg="#EFF6FF", height=50)
        info_frame.pack(fill='x', padx=20, pady=10)
        info_frame.pack_propagate(False)
        
        tk.Label(
            info_frame,
            text="💡 Puedes editar el contenido antes de guardar. Los cambios se reflejarán en el archivo final.",
            font=("Arial", 9),
            bg="#EFF6FF",
            fg="#1E40AF",
            wraplength=800,
            justify='left'
        ).pack(padx=15, pady=12)
        
        # Content area
        content_frame = tk.Frame(self.window, bg="#F9FAFB")
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Scrolled text widget for content
        self.text_widget = scrolledtext.ScrolledText(
            content_frame,
            font=("Consolas", 10),
            bg="white",
            fg="#1F2937",
            wrap=tk.WORD,
            relief=tk.SOLID,
            borderwidth=1,
            padx=15,
            pady=15
        )
        self.text_widget.pack(fill='both', expand=True)
        
        # Insert content
        self.text_widget.insert("1.0", self.content)
        
        # Highlight markdown headers
        self._highlight_markdown()
        
        # Buttons
        button_frame = tk.Frame(self.window, bg="#F9FAFB", height=70)
        button_frame.pack(fill='x', padx=20, pady=10)
        button_frame.pack_propagate(False)
        
        # Left side buttons
        left_buttons = tk.Frame(button_frame, bg="#F9FAFB")
        left_buttons.pack(side='left')
        
        tk.Button(
            left_buttons,
            text="📋 Copiar Todo",
            command=self._copy_to_clipboard,
            bg="#6B7280",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side='left', padx=5)
        
        # Right side buttons
        right_buttons = tk.Frame(button_frame, bg="#F9FAFB")
        right_buttons.pack(side='right')
        
        tk.Button(
            right_buttons,
            text="Cancelar",
            command=self.window.destroy,
            bg="#EF4444",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        ).pack(side='left', padx=5)
        
        tk.Button(
            right_buttons,
            text="💾 Guardar Documento",
            command=self._save_document,
            bg="#10B981",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=25,
            pady=12
        ).pack(side='left', padx=5)
    
    def _highlight_markdown(self):
        """Highlight markdown syntax"""
        # Configure tags for different markdown elements
        self.text_widget.tag_config("h1", font=("Arial", 16, "bold"), foreground="#1E3A8A")
        self.text_widget.tag_config("h2", font=("Arial", 14, "bold"), foreground="#3B82F6")
        self.text_widget.tag_config("h3", font=("Arial", 12, "bold"), foreground="#60A5FA")
        self.text_widget.tag_config("bold", font=("Consolas", 10, "bold"))
        self.text_widget.tag_config("checkbox", foreground="#10B981")
        
        # Get all text
        content = self.text_widget.get("1.0", "end")
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Highlight headers
            if line.startswith('# '):
                self.text_widget.tag_add("h1", f"{line_num}.0", f"{line_num}.end")
            elif line.startswith('## '):
                self.text_widget.tag_add("h2", f"{line_num}.0", f"{line_num}.end")
            elif line.startswith('### '):
                self.text_widget.tag_add("h3", f"{line_num}.0", f"{line_num}.end")
            
            # Highlight checkboxes
            if '[ ]' in line or '[x]' in line or '[✓]' in line:
                self.text_widget.tag_add("checkbox", f"{line_num}.0", f"{line_num}.end")
    
    def _copy_to_clipboard(self):
        """Copy content to clipboard"""
        content = self.text_widget.get("1.0", "end-1c")
        self.window.clipboard_clear()
        self.window.clipboard_append(content)
        messagebox.showinfo("Copiado", "Contenido copiado al portapapeles")
    
    def _save_document(self):
        """Save the document"""
        # Get current content (may have been edited)
        content = self.text_widget.get("1.0", "end-1c")
        
        # Ask where to save
        filename = filedialog.asksaveasfilename(
            title=f"Guardar {self.document_name}",
            defaultextension=".md",
            initialfile=f"{self.document_name.replace(' ', '_')}.md",
            filetypes=[
                ("Markdown", "*.md"),
                ("Texto", "*.txt"),
                ("Todos", "*.*")
            ]
        )
        
        if filename:
            try:
                # Save file
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                messagebox.showinfo(
                    "Éxito",
                    f"✅ Documento guardado exitosamente!\n\nArchivo: {filename}"
                )
                
                # Call callback if provided
                if self.on_save:
                    self.on_save(filename)
                
                # Ask if user wants to open it
                if messagebox.askyesno("Abrir archivo", "¿Deseas abrir el archivo?"):
                    subprocess.Popen(['notepad.exe', filename])
                
                # Close preview window
                self.window.destroy()
                
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al guardar el archivo:\n\n{str(e)}"
                )
