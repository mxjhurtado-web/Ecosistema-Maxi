    def open_settings(self):
        """Open settings window"""
        from desktop.ui.settings import SettingsWindow
        SettingsWindow(self.parent)

    def open_daily_log(self, project):
        """Open daily log editor"""
        from desktop.ui.daily_log_editor import DailyLogEditor
        DailyLogEditor(self.parent, self.auth_manager, project)

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

        # Confirm processing
        response = messagebox.askyesno(
            "Procesar Día",
            f"¿Deseas procesar el Documento Diario de hoy para el proyecto '{project['name']}'?\\n\\n"
            "Gemini extraerá automáticamente:\\n"
            "• Tareas\\n"
            "• Riesgos\\n"
            "• Decisiones\\n\\n"
            "Este proceso puede tardar unos segundos."
        )

        if not response:
            return

        try:
            # Show processing message
            processing_window = tk.Toplevel(self.parent)
            processing_window.title("Procesando...")
            processing_window.geometry("400x150")
            processing_window.resizable(False, False)

            # Center window
            processing_window.update_idletasks()
            x = (processing_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (processing_window.winfo_screenheight() // 2) - (150 // 2)
            processing_window.geometry(f"400x150+{x}+{y}")

            label = tk.Label(
                processing_window,
                text="🤖 Procesando con Gemini...\\n\\nEsto puede tardar unos segundos.",
                font=("Arial", 12),
                pady=30
            )
            label.pack()

            processing_window.update()

            # Process EOD
            user_email = self.auth_manager.user_info.get('email')
            today = date.today()
            api_key = GeminiConfig.get_api_key()

            result = self.api_client.process_eod(
                user_email,
                project['id'],
                today,
                api_key
            )

            processing_window.destroy()

            if result and result.get('status') == 'success':
                summary = result.get('summary', {})
                message = (
                    f"✅ Procesamiento completado exitosamente!\\n\\n"
                    f"Tareas creadas: {summary.get('tasks_created', 0)}\\n"
                    f"Tareas actualizadas: {summary.get('tasks_updated', 0)}\\n"
                    f"Riesgos creados: {summary.get('risks_created', 0)}\\n"
                    f"Decisiones creadas: {summary.get('decisions_created', 0)}\\n\\n"
                    f"Resumen: {summary.get('gemini_summary', 'N/A')}"
                )
                messagebox.showinfo("Éxito", message)
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo procesar el documento diario.\\n\\n"
                    "Verifica que:\\n"
                    "• Hayas creado un documento diario para hoy\\n"
                    "• Tu API key de Gemini sea válida\\n"
                    "• Tengas conexión a internet"
                )

        except Exception as e:
            if 'processing_window' in locals():
                processing_window.destroy()
            messagebox.showerror("Error", f"Error al procesar:\\n\\n{str(e)}")
