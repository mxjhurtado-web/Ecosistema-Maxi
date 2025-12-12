# ===========================
# ⚙️ CONFIGURACIÓN DE API KEYS
# ===========================
def mostrar_configuracion_api():
    """Muestra el diálogo de configuración de API Keys"""
    user_email = usuario_actual.get("correo")
    if not user_email:
        messagebox.showerror("Error", "No hay usuario autenticado")
        return
    
    api_mgr = get_api_key_manager()
    
    # Create dialog window
    dialog = tk.Toplevel(app)
    dialog.title("⚙️ Configuración de API Keys")
    dialog.geometry("650x550")
    dialog.configure(bg=COLORS["app_bg"])
    dialog.transient(app)
    dialog.grab_set()
    
    # Header
    header = tk.Frame(dialog, bg=COLORS["card_bg"], height=70)
    header.pack(fill="x", padx=20, pady=(20, 10))
    header.pack_propagate(False)
    
    tk.Label(
        header, text="🔑 Gestión de API Keys",
        font=("Segoe UI", 14, "bold"),
        bg=COLORS["card_bg"], fg=COLORS["text_primary"]
    ).pack(side="left", padx=20, pady=20)
    
    # Status display
    status = api_mgr.get_keys_status(user_email)
    
    status_frame = tk.Frame(dialog, bg=COLORS["card_bg"])
    status_frame.pack(fill="x", padx=20, pady=10)
    
    status_label = tk.Label(
        status_frame,
        text=f"📊 {status['active']} activas | {status['exhausted']} agotadas | {status['total']}/4 total",
        font=FONT["body"], bg=COLORS["card_bg"], fg=COLORS["text_secondary"]
    )
    status_label.pack(pady=10)
    
    # Keys list with scrollbar
    list_frame = tk.Frame(dialog, bg=COLORS["card_bg"])
    list_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    canvas_keys = tk.Canvas(list_frame, bg=COLORS["card_bg"], highlightthickness=0)
    scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas_keys.yview)
    scrollable_frame = tk.Frame(canvas_keys, bg=COLORS["card_bg"])
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas_keys.configure(scrollregion=canvas_keys.bbox("all"))
    )
    
    canvas_keys.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas_keys.configure(yscrollcommand=scrollbar.set)
    
    canvas_keys.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    def _refresh_keys():
        """Refresh the keys list"""
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
        
        status = api_mgr.get_keys_status(user_email)
        
        if not status["keys"]:
            tk.Label(
                scrollable_frame,
                text="No hay API Keys configuradas.\nAgrega una nueva abajo.",
                font=FONT["body"], bg=COLORS["card_bg"],
                fg=COLORS["text_secondary"], justify="center"
            ).pack(pady=40)
        else:
            for key_info in status["keys"]:
                key_card = tk.Frame(scrollable_frame, bg="#f5f5f5", relief="flat", bd=1)
                key_card.pack(fill="x", pady=5, padx=5)
                
                # Status indicator
                status_color = "#4caf50" if key_info["status"] == "active" else "#ff5252"
                status_text = "🟢 Activa" if key_info["status"] == "active" else "🔴 Agotada"
                
                tk.Label(
                    key_card, text=f"Key #{key_info['index'] + 1}",
                    font=("Segoe UI", 9, "bold"),
                    bg="#f5f5f5", fg=COLORS["text_primary"]
                ).pack(side="left", padx=10, pady=8)
                
                tk.Label(
                    key_card, text=status_text,
                    font=("Segoe UI", 9),
                    bg="#f5f5f5", fg=status_color
                ).pack(side="left", padx=5)
                
                tk.Label(
                    key_card, text=key_info["preview"],
                    font=("Courier New", 9),
                    bg="#f5f5f5", fg=COLORS["text_primary"]
                ).pack(side="left", padx=10)
                
                # Remove button
                tk.Button(
                    key_card, text="🗑️ Eliminar",
                    command=lambda idx=key_info["index"]: _remove_key(idx),
                    bg="#ffebee", fg="#c62828",
                    relief="flat", bd=0, padx=8, pady=4,
                    font=("Segoe UI", 8)
                ).pack(side="right", padx=10)
    
    def _add_key():
        new_key = key_entry.get().strip()
        if not new_key:
            messagebox.showwarning("Advertencia", "Ingresa una API Key")
            return
        
        success, message = api_mgr.add_key(user_email, new_key)
        if success:
            messagebox.showinfo("Éxito", message)
            key_entry.delete(0, tk.END)
            _refresh_keys()
            # Update status display
            status = api_mgr.get_keys_status(user_email)
            status_label.config(
                text=f"📊 {status['active']} activas | {status['exhausted']} agotadas | {status['total']}/4 total"
            )
        else:
            messagebox.showerror("Error", message)
    
    def _remove_key(idx):
        if messagebox.askyesno("Confirmar", f"¿Eliminar API Key #{idx + 1}?"):
            success, message = api_mgr.remove_key(user_email, idx)
            if success:
                _refresh_keys()
                # Update status display
                status = api_mgr.get_keys_status(user_email)
                status_label.config(
                    text=f"📊 {status['active']} activas | {status['exhausted']} agotadas | {status['total']}/4 total"
                )
            else:
                messagebox.showerror("Error", message)
    
    # Initial keys display
    _refresh_keys()
    
    # Add new key section
    add_frame = tk.Frame(dialog, bg=COLORS["card_bg"])
    add_frame.pack(fill="x", padx=20, pady=20)
    
    tk.Label(
        add_frame, text="➕ Agregar nueva API Key:",
        font=FONT["body"], bg=COLORS["card_bg"], fg=COLORS["text_primary"]
    ).pack(anchor="w", pady=(0, 5))
    
    key_entry = tk.Entry(
        add_frame, font=("Courier New", 10),
        relief="flat", bd=1, show="*"
    )
    key_entry.pack(fill="x", ipady=8, pady=5)
    key_entry.bind("<Return>", lambda e: _add_key())
    
    tk.Button(
        add_frame, text="➕ Agregar",
        command=_add_key,
        bg=COLORS["accent"], fg="#fff",
        relief="flat", bd=0, padx=20, pady=10,
        font=FONT["btn"]
    ).pack(pady=10)
    
    # Close button
    tk.Button(
        dialog, text="Cerrar",
        command=dialog.destroy,
        bg="#e0e0e0", fg=COLORS["text_primary"],
        relief="flat", bd=0, padx=20, pady=10,
        font=FONT["btn"]
    ).pack(pady=10)
