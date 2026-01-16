#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings window for TEMIS
"""

import tkinter as tk
from tkinter import messagebox

from desktop.core.gemini_config import GeminiConfig


class SettingsWindow:
    """Settings window"""

    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.api_key_entry = None
        self.create_window()

    def create_window(self):
        """Create settings window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("TEMIS - Configuración")
        self.window.geometry("600x550")  # Increased height to show all content
        self.window.resizable(False, False)

        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (550 // 2)  # Updated for new height
        self.window.geometry(f"600x550+{x}+{y}")

        # Get theme colors
        from desktop.ui.ui_helpers import get_theme_colors
        colors = get_theme_colors()
        
        bg_color = colors["bg"]
        primary_color = colors["primary"]
        secondary_color = colors["secondary"]

        self.window.configure(bg=bg_color)

        # Header
        header_frame = tk.Frame(self.window, bg=primary_color, height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="⚙️ Configuración",
            font=("Arial", 16, "bold"),
            bg=primary_color,
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)

        # Main frame
        main_frame = tk.Frame(self.window, bg=bg_color)
        main_frame.pack(fill='both', expand=True, padx=40, pady=30)

        # Gemini API section
        gemini_label = tk.Label(
            main_frame,
            text="GEMINI API",
            font=("Arial", 12, "bold"),
            bg=bg_color,
            fg=primary_color
        )
        gemini_label.pack(anchor='w', pady=(0, 10))

        # API Key input
        api_key_frame = tk.Frame(main_frame, bg=bg_color)
        api_key_frame.pack(fill='x', pady=10)

        api_key_label = tk.Label(
            api_key_frame,
            text="API Key:",
            font=("Arial", 10),
            bg=bg_color,
            fg="#374151"
        )
        api_key_label.pack(side=tk.LEFT, padx=(0, 10))

        self.api_key_entry = tk.Entry(
            api_key_frame,
            font=("Arial", 10),
            bg="white",
            fg="#1F2937",
            relief=tk.FLAT,
            borderwidth=2,
            show="*",
            width=40
        )
        self.api_key_entry.pack(side=tk.LEFT, fill='x', expand=True)

        # Load existing API key
        existing_key = GeminiConfig.get_api_key()
        if existing_key:
            self.api_key_entry.insert(0, existing_key)

        # Show/Hide button
        show_btn = tk.Button(
            api_key_frame,
            text="👁️",
            font=("Arial", 10),
            bg="#E5E7EB",
            fg="#374151",
            activebackground="#D1D5DB",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_api_key_visibility,
            padx=10
        )
        show_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Model info
        model_label = tk.Label(
            main_frame,
            text="Modelo: gemini-2.5-flash",
            font=("Arial", 9),
            bg=bg_color,
            fg="#6B7280"
        )
        model_label.pack(anchor='w', pady=(5, 30))
        
        # Theme section
        theme_label = tk.Label(
            main_frame,
            text="APARIENCIA",
            font=("Arial", 12, "bold"),
            bg=bg_color,
            fg=primary_color
        )
        theme_label.pack(anchor='w', pady=(0, 10))
        
        # Theme selection
        from desktop.core.theme_manager import ThemeManager
        
        theme_frame = tk.Frame(main_frame, bg=bg_color)
        theme_frame.pack(fill='x', pady=10)
        
        theme_desc_label = tk.Label(
            theme_frame,
            text="Tema:",
            font=("Arial", 10),
            bg=bg_color,
            fg="#374151"
        )
        theme_desc_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Current theme
        current_theme = ThemeManager.get_current_theme()
        self.theme_var = tk.StringVar(value=current_theme)
        
        # Light mode button
        light_btn = tk.Radiobutton(
            theme_frame,
            text="☀️ Claro",
            variable=self.theme_var,
            value="light",
            font=("Arial", 10),
            bg=bg_color,
            fg="#374151",
            selectcolor=bg_color,
            activebackground=bg_color,
            cursor="hand2",
            command=self.preview_theme
        )
        light_btn.pack(side=tk.LEFT, padx=10)
        
        # Dark mode button
        dark_btn = tk.Radiobutton(
            theme_frame,
            text="🌙 Oscuro",
            variable=self.theme_var,
            value="dark",
            font=("Arial", 10),
            bg=bg_color,
            fg="#374151",
            selectcolor=bg_color,
            activebackground=bg_color,
            cursor="hand2",
            command=self.preview_theme
        )
        dark_btn.pack(side=tk.LEFT, padx=10)
        
        # Theme info
        theme_info_label = tk.Label(
            main_frame,
            text="💡 El tema se aplicará al reiniciar TEMIS",
            font=("Arial", 9),
            bg=bg_color,
            fg="#6B7280"
        )
        theme_info_label.pack(anchor='w', pady=(5, 20))
        
        # Separator
        separator2 = tk.Frame(main_frame, height=2, bg="#E5E7EB")
        separator2.pack(fill=tk.X, pady=20)
        
        # SHARED DATABASE MODE Section
        shared_mode_label = tk.Label(
            main_frame,
            text="MODO DE TRABAJO",
            font=("Arial", 11, "bold"),
            bg=bg_color,
            fg=text_color
        )
        shared_mode_label.pack(anchor='w', pady=(0, 10))
        
        # Mode selection
        mode_frame = tk.Frame(main_frame, bg=bg_color)
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.shared_mode_var = tk.StringVar(value="local")
        
        # Get current status
        try:
            status = self.api_client.get_shared_mode_status()
            self.shared_mode_var.set(status.get('mode', 'local'))
        except:
            pass
        
        local_radio = tk.Radiobutton(
            mode_frame,
            text="🖥️ Local (solo yo)",
            variable=self.shared_mode_var,
            value="local",
            font=("Arial", 10),
            bg=bg_color,
            fg=text_color,
            selectcolor=bg_color,
            activebackground=bg_color,
            command=self.on_mode_change
        )
        local_radio.pack(anchor='w', pady=2)
        
        shared_radio = tk.Radiobutton(
            mode_frame,
            text="☁️ Compartido (equipo en Drive)",
            variable=self.shared_mode_var,
            value="shared",
            font=("Arial", 10),
            bg=bg_color,
            fg=text_color,
            selectcolor=bg_color,
            activebackground=bg_color,
            command=self.on_mode_change
        )
        shared_radio.pack(anchor='w', pady=2)
        
        # Status indicator
        self.status_label = tk.Label(
            main_frame,
            text="Estado: Local",
            font=("Arial", 9),
            bg=bg_color,
            fg="#6B7280"
        )
        self.status_label.pack(anchor='w', pady=(10, 5))
        
        # Sync button (only visible in shared mode)
        self.sync_btn = tk.Button(
            main_frame,
            text="🔄 Sincronizar Ahora",
            font=("Arial", 9),
            bg="#10B981",
            fg="white",
            activebackground="#059669",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.manual_sync,
            padx=15,
            pady=5
        )
        if self.shared_mode_var.get() == "shared":
            self.sync_btn.pack(anchor='w', pady=5)
        
        # Backups button (only visible in shared mode)
        self.backups_btn = tk.Button(
            main_frame,
            text="📦 Ver Backups",
            font=("Arial", 9),
            bg="#6366F1",
            fg="white",
            activebackground="#4F46E5",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.view_backups,
            padx=15,
            pady=5
        )
        if self.shared_mode_var.get() == "shared":
            self.backups_btn.pack(anchor='w', pady=5)
        
        # Shared mode info
        shared_info_label = tk.Label(
            main_frame,
            text="💡 Modo compartido: Todos trabajan en la misma base de datos en Drive\n"
                 "   Sincronización automática cada 5 minutos con backups automáticos",
            font=("Arial", 8),
            bg=bg_color,
            fg="#6B7280",
            justify=tk.LEFT
        )
        shared_info_label.pack(anchor='w', pady=(5, 20))

        # Save button
        save_btn = tk.Button(
            main_frame,
            text="💾 Guardar Configuración",
            font=("Arial", 12, "bold"),
            bg=secondary_color,
            fg="white",
            activebackground=primary_color,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.save_config,
            padx=30,
            pady=12
        )
        save_btn.pack(pady=20)

        # Info label
        info_label = tk.Label(
            main_frame,
            text="💡 Obtén tu API key en: https://aistudio.google.com/app/apikey",
            font=("Arial", 9),
            bg=bg_color,
            fg="#6B7280",
            cursor="hand2"
        )
        info_label.pack(pady=10)

    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_entry.cget('show') == '*':
            self.api_key_entry.config(show='')
        else:
            self.api_key_entry.config(show='*')
    
    def preview_theme(self):
        """Preview theme selection"""
        # Just show a message for now
        theme = self.theme_var.get()
        theme_name = "Claro" if theme == "light" else "Oscuro"
        # Could add visual preview here in the future

    def save_config(self):
        """Save configuration"""
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            messagebox.showwarning("Advertencia", "Por favor ingresa una API key")
            return

        # Save API key
        api_saved = GeminiConfig.save_api_key(api_key)
        
        # Save theme
        from desktop.core.theme_manager import ThemeManager
        theme = self.theme_var.get()
        theme_saved = ThemeManager.set_theme(theme)
        
        if api_saved and theme_saved:
            messagebox.showinfo(
                "Éxito", 
                "✅ Configuración guardada correctamente\n\n💡 Reinicia TEMIS para aplicar el tema"
            )
            self.window.destroy()
        elif api_saved:
            messagebox.showinfo(
                "Parcialmente Guardado",
                "API key guardada, pero hubo un error al guardar el tema"
            )
        else:
            messagebox.showerror("Error", "No se pudo guardar la configuración")
    
    def on_mode_change(self):
        """Handle mode change"""
        mode = self.shared_mode_var.get()
        
        # Show/hide buttons based on mode
        if mode == "shared":
            self.sync_btn.pack(anchor='w', pady=5)
            self.backups_btn.pack(anchor='w', pady=5)
            self.status_label.config(text="Estado: Activando modo compartido...")
        else:
            self.sync_btn.pack_forget()
            self.backups_btn.pack_forget()
            self.status_label.config(text="Estado: Local")
        
        # Enable/disable shared mode
        try:
            user_email = self.auth_manager.user_info.get('email', 'unknown')
            result = self.api_client.toggle_shared_mode(mode == "shared", user_email)
            
            if result.get('status') == 'success':
                self.status_label.config(text=f"Estado: {result.get('mode').title()}")
                messagebox.showinfo("Éxito", result.get('message'))
            else:
                messagebox.showerror("Error", "No se pudo cambiar el modo")
                # Revert selection
                self.shared_mode_var.set("local" if mode == "shared" else "shared")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cambiar modo: {str(e)}")
            self.shared_mode_var.set("local" if mode == "shared" else "shared")
    
    def manual_sync(self):
        """Manually sync database"""
        try:
            user_email = self.auth_manager.user_info.get('email', 'unknown')
            self.status_label.config(text="Estado: Sincronizando...")
            
            result = self.api_client.sync_database(user_email)
            
            if result.get('status') == 'success':
                action = result.get('action', 'synced')
                message = result.get('message', 'Sincronizado')
                self.status_label.config(text=f"Estado: ✓ {message}")
                messagebox.showinfo("Sincronización", message)
            else:
                self.status_label.config(text="Estado: Error en sync")
                messagebox.showerror("Error", "No se pudo sincronizar")
        except Exception as e:
            self.status_label.config(text="Estado: Error")
            messagebox.showerror("Error", f"Error al sincronizar: {str(e)}")
    
    def view_backups(self):
        """View and manage backups"""
        try:
            backups = self.api_client.list_backups()
            
            if not backups.get('backups'):
                messagebox.showinfo("Backups", "No hay backups disponibles")
                return
            
            # Create backups window
            backups_window = tk.Toplevel(self.window)
            backups_window.title("Backups Disponibles")
            backups_window.geometry("600x400")
            
            # Header
            header = tk.Label(
                backups_window,
                text="📦 Backups de Base de Datos",
                font=("Arial", 14, "bold"),
                bg="#3B82F6",
                fg="white",
                pady=15
            )
            header.pack(fill=tk.X)
            
            # Listbox with scrollbar
            list_frame = tk.Frame(backups_window)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            backup_list = tk.Listbox(
                list_frame,
                font=("Arial", 10),
                yscrollcommand=scrollbar.set
            )
            backup_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=backup_list.yview)
            
            # Populate list
            backup_data = []
            for backup in backups['backups']:
                name = backup['name']
                created = backup.get('created', 'Unknown')
                backup_list.insert(tk.END, f"{name} - {created}")
                backup_data.append(backup)
            
            # Restore button
            def restore_selected():
                selection = backup_list.curselection()
                if not selection:
                    messagebox.showwarning("Selección", "Por favor selecciona un backup")
                    return
                
                backup = backup_data[selection[0]]
                
                confirm = messagebox.askyesno(
                    "Confirmar Restauración",
                    f"¿Estás seguro de restaurar este backup?\n\n{backup['name']}\n\n"
                    "Esto reemplazará la base de datos actual."
                )
                
                if confirm:
                    try:
                        result = self.api_client.restore_backup(backup['id'])
                        if result.get('status') == 'success':
                            messagebox.showinfo("Éxito", "Backup restaurado. Reinicia TEMIS para ver los cambios.")
                            backups_window.destroy()
                        else:
                            messagebox.showerror("Error", "No se pudo restaurar el backup")
                    except Exception as e:
                        messagebox.showerror("Error", f"Error al restaurar: {str(e)}")
            
            restore_btn = tk.Button(
                backups_window,
                text="🔄 Restaurar Seleccionado",
                command=restore_selected,
                bg="#10B981",
                fg="white",
                font=("Arial", 10, "bold"),
                padx=20,
                pady=10
            )
            restore_btn.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar backups: {str(e)}")
