"""
Función para la pestaña de Operaciones en MaxiBot
Todas las consultas van directo al DevOps MCP
"""

def mostrar_operaciones():
    """
    Muestra la pestaña de Operaciones con chat dedicado para DevOps MCP.
    Todas las consultas en esta pestaña van exclusivamente al DevOps MCP.
    """
    global chat_canvas, chat_inner, chat_inner_id, entrada_pregunta
    
    # Verificar que el usuario esté autenticado con SSO
    if not usuario_actual.get("sso") or not keycloak_auth_instance:
        messagebox.showwarning(
            "Operaciones",
            "Debes iniciar sesión con SSO para acceder a Operaciones."
        )
        return
    
    # Verificar que DevOps MCP esté disponible
    if not _DEVOPS_MCP_OK:
        messagebox.showerror(
            "Operaciones",
            "DevOps MCP no está disponible. Verifica las dependencias."
        )
        return
    
    limpiar_pantalla()
    header_card(app)
    
    body = tk.Frame(app, bg=COLORS["app_bg"])
    body.pack(fill="both", expand=True, padx=24, pady=(0, 16))
    
    card_shadow = tk.Frame(body, bg="#d0d7e2")
    card_shadow.pack(fill="both", expand=True)
    chat_card = tk.Frame(
        card_shadow, bg=COLORS["card_bg"],
        highlightthickness=1, highlightbackground=COLORS["divider"]
    )
    chat_card.pack(fill="both", expand=True, padx=2, pady=2)
    
    # Título con indicador de estado
    title_bar = tk.Frame(chat_card, bg=COLORS["card_bg"])
    title_bar.pack(fill="x", padx=16, pady=(12, 0))
    
    tk.Label(
        title_bar, text="🔧 Operaciones (DevOps MCP)", 
        font=("Segoe UI", 11, "bold"),
        bg=COLORS["card_bg"], fg=COLORS["text_primary"]
    ).pack(side="left")
    
    # Indicador de estado del MCP
    try:
        devops = get_devops_mcp()
        if devops and devops.available():
            status_text = "🟢 Conectado"
            status_color = "#10b981"
        else:
            status_text = "🔴 Desconectado"
            status_color = "#ef4444"
    except:
        status_text = "🔴 Error"
        status_color = "#ef4444"
    
    tk.Label(
        title_bar, text=status_text,
        font=FONT["meta"], bg=COLORS["card_bg"], fg=status_color
    ).pack(side="right")
    
    # Área de chat
    holder = tk.Frame(chat_card, bg=COLORS["card_bg"])
    holder.pack(fill="both", expand=True, padx=12, pady=12)
    
    chat_canvas_local = tk.Canvas(
        holder, bg=COLORS["card_bg"], highlightthickness=0
    )
    vscroll = tk.Scrollbar(holder, orient="vertical", command=chat_canvas_local.yview)
    chat_canvas_local.configure(yscrollcommand=vscroll.set)
    
    vscroll.pack(side="right", fill="y")
    chat_canvas_local.pack(side="left", fill="both", expand=True)
    
    chat_canvas = chat_canvas_local
    chat_inner = tk.Frame(chat_canvas, bg=COLORS["card_bg"])
    chat_inner_id = chat_canvas.create_window((0, 0), window=chat_inner, anchor="nw")
    
    def _on_frame_config(event):
        chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
        chat_canvas.itemconfig(chat_inner_id, width=chat_canvas.winfo_width())
    
    chat_inner.bind("<Configure>", _on_frame_config)
    
    # Mensaje de bienvenida
    add_message(
        "MaxiBot", 
        "¡Bienvenido a Operaciones! 🔧\n\n"
        "Aquí puedes consultar información sobre agencias, sistemas y servicios.\n"
        "Todas tus consultas serán procesadas por el DevOps MCP.",
        kind="bot"
    )
    
    # Barra de entrada
    input_bar = tk.Frame(chat_card, bg=COLORS["card_bg"])
    input_bar.pack(fill="x", padx=12, pady=(0, 12))
    
    entrada_pregunta = tk.Entry(
        input_bar, font=FONT["body"], relief="flat",
        highlightthickness=1, highlightbackground=COLORS["divider"]
    )
    entrada_pregunta.pack(side="left", padx=(0, 8), ipady=8, fill="x", expand=True)
    entrada_pregunta.bind("<Return>", lambda e: responder_operaciones())
    
    tk.Button(
        input_bar, text="Consultar", command=responder_operaciones,
        bg=COLORS["accent"], fg="#fff",
        activebackground=COLORS["accent_dark"],
        activeforeground="#fff",
        relief="flat", bd=0, padx=16, pady=10,
        font=FONT["btn"]
    ).pack(side="left")
    
    # Botones de acción
    btn_row = tk.Frame(chat_card, bg=COLORS["card_bg"])
    btn_row.pack(fill="x", padx=12, pady=(0, 12))
    
    tk.Button(
        btn_row, text="← Volver al Chat", command=mostrar_chat,
        bg="#e6f2ff", fg=COLORS["text_primary"],
        relief="flat", bd=0, padx=12, pady=6,
        font=FONT["btn_small"]
    ).pack(side="left", padx=(0, 8))
    
    tk.Button(
        btn_row, text="Herramientas MCP", command=mostrar_herramientas_mcp,
        bg="#f0fdf4", fg=COLORS["text_primary"],
        relief="flat", bd=0, padx=12, pady=6,
        font=FONT["btn_small"]
    ).pack(side="left", padx=(0, 8))
    
    def _logout():
        if usuario_actual.get("sso"):
            cerrar_sesion_keycloak()
        else:
            usuario_actual["correo"] = None
            usuario_actual["nombre"] = None
            usuario_actual["alias"] = None
            usuario_actual["sso"] = False
        
        borrar_memoria(auto=True)
        mostrar_verificacion()
    
    tk.Button(
        btn_row, text="Cerrar sesión",
        command=_logout,
        bg="#ffe4e6", fg=COLORS["text_primary"],
        relief="flat", bd=0, padx=12, pady=6,
        font=FONT["btn_small"]
    ).pack(side="right", padx=(8, 0))


def responder_operaciones():
    """
    Maneja las respuestas en la pestaña de Operaciones.
    Todas las consultas van directo al DevOps MCP.
    """
    pregunta = entrada_pregunta.get().strip()
    if not pregunta:
        return
    
    alias = usuario_actual["alias"] or "Usuario"
    add_message(alias, pregunta, kind="user")
    entrada_pregunta.delete(0, tk.END)
    
    # Verificar que DevOps MCP esté disponible
    if not _DEVOPS_MCP_OK:
        add_message(
            "MaxiBot",
            "❌ DevOps MCP no está disponible. Verifica las dependencias.",
            kind="bot"
        )
        return
    
    try:
        devops = get_devops_mcp()
        if not devops or not devops.available():
            add_message(
                "MaxiBot",
                "❌ DevOps MCP no está conectado. Verifica tu token de Keycloak.",
                kind="bot"
            )
            return
        
        # Mostrar mensaje de carga
        temp_row, temp_meta = add_message(
            "MaxiBot", 
            "🔍 Consultando DevOps MCP...",
            kind="bot"
        )
        app.update()
        
        # Consultar DevOps MCP
        respuesta_devops = devops.query_sync(pregunta)
        
        # Remover mensaje temporal
        try:
            temp_row.destroy()
        except:
            pass
        
        # Mostrar respuesta
        if respuesta_devops and not respuesta_devops.startswith("Error"):
            registrar_consulta(usuario_actual["correo"], "operaciones", pregunta)
            row, meta = add_message("MaxiBot", respuesta_devops, kind="bot")
            
            registro_sesion.append({
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "usuario": usuario_actual["alias"],
                "correo": usuario_actual["correo"],
                "pregunta": pregunta,
                "respuesta": respuesta_devops,
                "origen": "OPERACIONES",
                "hoja": None,
                "feedback": "neutral",
            })
            _crear_botones_feedback(meta, len(registro_sesion)-1)
        else:
            add_message(
                "MaxiBot",
                f"❌ Error al consultar DevOps MCP:\n{respuesta_devops}",
                kind="bot"
            )
    
    except Exception as e:
        add_message(
            "MaxiBot",
            f"❌ Error inesperado: {str(e)}",
            kind="bot"
        )
        print(f"Error en responder_operaciones: {e}")


def mostrar_herramientas_mcp():
    """Muestra las herramientas disponibles en el DevOps MCP."""
    if not _DEVOPS_MCP_OK:
        messagebox.showerror(
            "Herramientas MCP",
            "DevOps MCP no está disponible."
        )
        return
    
    try:
        devops = get_devops_mcp()
        if not devops or not devops.available():
            messagebox.showwarning(
                "Herramientas MCP",
                "DevOps MCP no está conectado."
            )
            return
        
        # Obtener herramientas (esto es async, necesitamos manejarlo)
        tools = devops.get_available_tools_sync()
        
        if tools:
            tools_text = "\n".join(f"• {tool}" for tool in tools)
            messagebox.showinfo(
                "Herramientas MCP Disponibles",
                f"El DevOps MCP tiene las siguientes herramientas:\n\n{tools_text}"
            )
        else:
            messagebox.showinfo(
                "Herramientas MCP",
                "No se pudieron obtener las herramientas disponibles."
            )
    
    except Exception as e:
        messagebox.showerror(
            "Error",
            f"Error al obtener herramientas: {str(e)}"
        )
