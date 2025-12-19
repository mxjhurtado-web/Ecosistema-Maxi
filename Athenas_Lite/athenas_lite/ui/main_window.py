
import os
import sys
import pathlib
import datetime
import re
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from collections import Counter, defaultdict
from datetime import datetime

# Optional dependencies
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

try:
    import pandas as pd
except ImportError:
    pd = None

# Internal modules
from ..config.constants import PALETTE, DEPT_OPTIONS_FIXED, EXPORT_FOLDER
from ..config.settings import GEMINI_API_KEY
from ..config.logging_config import logger
from ..auth.google_auth import verificar_correo_online
from ..services.gemini_api import (configurar_gemini, llm_json_or_mock, 
                                   analizar_sentimiento, analizar_sentimiento_por_roles)
from ..services.system_tools import get_audio_duration, human_duration, is_gemini_supported, convert_to_wav
from ..services.drive_exports import subir_csv_a_drive
from ..core.rubric_loader import load_dept_rubric_json_local, rubric_json_to_prompt, LOCAL_RUBRICS_DIR
from ..core.scoring import aplicar_defaults_items, compute_scores_with_na, _atributos_a_columnas_valor
from .helpers import pick_font, _resource_path
from .results_panel import ResultsPanel, AudioPlayer, TxtViewer

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ATHENAS Lite v3.2.1 (Refactored)")
        self.root.geometry("1200x700")
        self.root.configure(bg=PALETTE["bg"])
        
        self.fonts = pick_font(self.root)
        
        # State
        self.ruta_audio = []
        self.carpeta_guardado = None
        self.nombre_evaluador = ""
        self.nombre_asesor = ""
        self.selected_department = None
        self.analysis_results = []  # Store analysis results
        
        # UI Components (will be initialized in setup_ui)
        self.results_panel = None
        self.txt_viewer = None
        self.audio_player = None
        
        # Configure safe window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Init sequence
        self.authenticate_user()
        self.configure_gemini_api()
        self.setup_ui()

    def on_closing(self):
        """Manejo seguro del cierre de ventana"""
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass  # Ignorar errores al cerrar

    def authenticate_user(self):
        """Autenticación con Keycloak SSO con splash screen"""
        # Crear ventana de splash
        splash = tk.Toplevel(self.root)
        splash.title("ATHENAS Lite")
        splash.geometry("400x300")
        splash.configure(bg="#fceff1")
        splash.resizable(False, False)
        
        # Centrar ventana
        splash.update_idletasks()
        x = (splash.winfo_screenwidth() // 2) - 200
        y = (splash.winfo_screenheight() // 2) - 150
        splash.geometry(f"+{x}+{y}")
        
        # Quitar bordes de ventana
        splash.overrideredirect(True)
        
        # Frame principal
        main_frame = tk.Frame(splash, bg="#fceff1", bd=2, relief="solid")
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Logo (intentar cargar imagen, si no, usar texto)
        try:
            logo_path = _resource_path("athenas2.png")
            if os.path.exists(logo_path) and Image and ImageTk:
                logo_img = Image.open(logo_path).resize((80, 110))
                logo_tk = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(main_frame, image=logo_tk, bg="#fceff1")
                logo_label.image = logo_tk  # Mantener referencia
                logo_label.pack(pady=(20, 10))
            else:
                raise Exception("No logo")
        except:
            tk.Label(main_frame, text="ATHENAS", font=("Segoe UI", 24, "bold"), 
                    fg="#e91e63", bg="#fceff1").pack(pady=(20, 5))
            tk.Label(main_frame, text="Lite", font=("Segoe UI", 16), 
                    fg="#c2185b", bg="#fceff1").pack(pady=(0, 10))
        
        # Título
        tk.Label(main_frame, text="Autenticación SSO", font=("Segoe UI", 12, "bold"),
                fg="#333333", bg="#fceff1").pack(pady=(10, 5))
        
        # Mensaje de estado
        status_label = tk.Label(main_frame, text="Iniciando autenticación...", 
                               font=("Segoe UI", 9), fg="#666666", bg="#fceff1")
        status_label.pack(pady=10)
        
        # Barra de progreso (indeterminada)
        try:
            progress = ttk.Progressbar(main_frame, mode='indeterminate', length=300)
            progress.pack(pady=10)
            progress.start(10)
        except:
            pass
        
        splash.update()
        
        # Función para actualizar estado
        def update_status(message):
            status_label.config(text=message)
            splash.update()
        
        try:
            # Importar módulo de Keycloak
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            from keycloak_auth import KeycloakAuth
            
            update_status("Conectando con servidor SSO...")
            splash.update()
            
            # Autenticar con Keycloak
            keycloak = KeycloakAuth()
            
            update_status("Abriendo navegador...")
            splash.update()
            
            # Ejecutar autenticación en thread para no bloquear UI
            import threading
            auth_result = {"success": False, "message": ""}
            
            def do_auth():
                success, message = keycloak.authenticate()
                auth_result["success"] = success
                auth_result["message"] = message
            
            auth_thread = threading.Thread(target=do_auth)
            auth_thread.daemon = True
            auth_thread.start()
            
            # Esperar autenticación con actualizaciones de UI
            update_status("Esperando autenticación en navegador...")
            while auth_thread.is_alive():
                splash.update()
                time.sleep(0.1)
            
            if not auth_result["success"]:
                splash.destroy()
                messagebox.showerror("Autorización", f"Error de autenticación:\n{auth_result['message']}")
                self.root.destroy()
                sys.exit(1)
            
            # Obtener información del usuario
            update_status("Obteniendo información del usuario...")
            splash.update()
            
            user_email = keycloak.get_user_email() or "unknown"
            self.nombre_evaluador = keycloak.get_user_name() or user_email
            logger.info(f"User authenticated: {self.nombre_evaluador} ({user_email})")
            
            # Cargar API Keys específicas del usuario
            try:
                from athenas_lite.services import gemini_api
                gemini_api.load_api_keys(user_email)
                logger.info(f"API Keys cargadas para {user_email}")
                
                # IMPORTANTE: Configurar Gemini con las keys cargadas
                if gemini_api.configurar_gemini():
                    logger.info(f"✅ Gemini configurado correctamente con keys de {user_email}")
                else:
                    logger.warning(f"⚠️ No se pudo configurar Gemini - posiblemente sin keys guardadas")
            except Exception as e:
                logger.error(f"Error cargando/configurando keys de usuario: {e}")
            
            update_status("✅ Autenticación exitosa")
            splash.update()
            time.sleep(0.5)
            
            # Cerrar splash
            splash.destroy()
            
        except Exception as e:
            splash.destroy()
            logger.exception("Auth failed")
            messagebox.showerror("Autorización", f"Error validando acceso:\n{e}")
            self.root.destroy()
            sys.exit(1)

    def configure_gemini_api(self):
        """Configuración inicial de Gemini (opcional desde .env)"""
        try:
            if GEMINI_API_KEY:
                configurar_gemini(GEMINI_API_KEY)
                logger.info("Gemini API Key cargada desde .env")
        except Exception:
            pass

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg=PALETTE["bg"])
        header_frame.pack(pady=10, fill="x")
        
        if Image and ImageTk:
            try:
                logo_path = _resource_path("athenas2.png")
                if os.path.exists(logo_path):
                    logo_img = Image.open(logo_path).resize((30, 42))
                    self.logo_tk = ImageTk.PhotoImage(logo_img)
                    tk.Label(header_frame, image=self.logo_tk, bg=PALETTE["bg"]).pack(side="left", padx=(10,2))
            except Exception:
                pass

        tk.Label(header_frame,
                 text="Athenas Lite: Transforma la Voz en Calidad",
                 font=("Segoe UI", 14, "bold"), fg="#0D47A1", bg=PALETTE["bg"]).pack(side="left", padx=5)

        # Main PanedWindow (horizontal split)
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5, bg="#cccccc")
        main_paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # LEFT PANEL - Controls
        left_panel = tk.Frame(main_paned, bg=PALETTE["bg"], width=350)
        main_paned.add(left_panel, minsize=300)
        
        # Loading Zone
        zona_carga = tk.Frame(left_panel, bg="#f9d6d5", bd=2, relief="groove")
        zona_carga.pack(pady=10, padx=10, fill="x")
        tk.Label(zona_carga, text="Carga tus audios (hasta 10)", 
                font=("Segoe UI", 9, "bold"), fg="#333333", bg="#f9d6d5").pack(pady=8)

        btn_style = {"bg": PALETTE["brand"], "fg": "white", "font": ("Segoe UI", 9), "width": 30}
        
        tk.Button(left_panel, text="⚙️ Configurar API Key y Modelo", 
                 command=self.configurar_api_key_y_modelo, **btn_style).pack(pady=5, padx=10)
        tk.Button(left_panel, text="📁 Seleccionar archivo(s)", 
                 command=self.seleccionar_archivo, **btn_style).pack(pady=5, padx=10)
        tk.Button(left_panel, text="💾 Guardar en carpeta...", 
                 command=self.seleccionar_carpeta_guardado, **btn_style).pack(pady=5, padx=10)
        tk.Button(left_panel, text="🚀 Analizar (Resumen consolidado)", 
                 command=self.solicitar_datos_y_analizar, **btn_style).pack(pady=5, padx=10)
        
        # RIGHT PANEL - Results
        right_panel = tk.Frame(main_paned, bg="#fceff1")
        main_paned.add(right_panel, minsize=600)
        
        # Setup results panel with vertical split
        self.setup_results_panel(right_panel)

    def configurar_api_key_y_modelo(self):
        """Ventana avanzada para gestión de API Keys y Modelo"""
        # Importar dinámicamente para asegurar estado actualizado
        from athenas_lite.services import gemini_api
        from athenas_lite.services.gemini_api import GEMINI_MODEL_SELECTED, GEMINI_API_KEYS
        
        ventana = tk.Toplevel(self.root)
        ventana.title("Gestión de API Keys Gemini")
        ventana.configure(bg="#fceff1")
        ventana.geometry("700x550")
        ventana.transient(self.root)
        ventana.grab_set()
        
        # Estilos
        COLOR_BG = "#fceff1"
        COLOR_CARD = "white"
        COLOR_ACTIVE = "#4CAF50" # Verde
        COLOR_EXHAUSTED = "#F44336" # Rojo
        
        # --- HEADER ---
        header_frame = tk.Frame(ventana, bg=COLOR_BG)
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        
        tk.Label(header_frame, text="⚙️ Gestión de Llaves y Modelo", 
                bg=COLOR_BG, fg="#0D47A1", font=("Segoe UI", 16, "bold")).pack(side="left")
                
        # --- PANEL PRINCIPAL (Scrollable) ---
        container = tk.Frame(ventana, bg=COLOR_BG)
        container.pack(fill="both", expand=True, padx=20, pady=5)
        
        canvas = tk.Canvas(container, bg=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLOR_BG)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- SECCIÓN DE KEYS ---
        keys_label_frame = tk.LabelFrame(scrollable_frame, text=" Mis API Keys ", 
                                       bg=COLOR_BG, fg="#333333", font=("Segoe UI", 11, "bold"))
        keys_label_frame.pack(fill="x", padx=5, pady=10, ipady=5)
        
        # Area donde se pintan las keys
        keys_container = tk.Frame(keys_label_frame, bg=COLOR_BG)
        keys_container.pack(fill="x", padx=10, pady=5)
        
        def refresh_keys_list():
            # Limpiar
            for widget in keys_container.winfo_children():
                widget.destroy()
            
            # Repintar
            if not gemini_api.GEMINI_API_KEYS:
                tk.Label(keys_container, text="No hay API Keys registradas.", 
                        bg=COLOR_BG, fg="#666666", font=("Segoe UI", 10, "italic")).pack(pady=10)
            
            for i, key_data in enumerate(gemini_api.GEMINI_API_KEYS):
                k = key_data["key"]
                status = key_data["status"]
                
                # Card para la key
                card = tk.Frame(keys_container, bg="white", bd=1, relief="solid")
                card.pack(fill="x", pady=2)
                
                # Indicador de estado (Semáforo)
                color = COLOR_ACTIVE if status == "active" else COLOR_EXHAUSTED
                status_text = "ACTIVA" if status == "active" else "AGOTADA"
                
                indicator = tk.Label(card, text="●", fg=color, bg="white", font=("Arial", 16))
                indicator.pack(side="left", padx=(10, 5))
                
                # Info Key
                masked_key = f"{k[:4]}...{k[-4:]}" if len(k) > 8 else k
                info_frame = tk.Frame(card, bg="white")
                info_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)
                
                tk.Label(info_frame, text=f"API KEY {i+1}", bg="white", fg="#333333", 
                        font=("Segoe UI", 9, "bold")).pack(anchor="w")
                tk.Label(info_frame, text=f"{masked_key} • {status_text}", 
                        bg="white", fg="#666666", font=("Segoe UI", 8)).pack(anchor="w")
                
                # Botón Eliminar
                btn_del = tk.Button(card, text="🗑️", bg="white", relief="flat", cursor="hand2",
                                   command=lambda idx=i: delete_key(idx))
                btn_del.pack(side="right", padx=10)

        def add_new_key():
            new_k = entry_new_key.get().strip()
            if not new_k: return
            
            # Usar email actual almacenado en el módulo
            current_email = gemini_api.CURRENT_USER_EMAIL
            
            if gemini_api.add_api_key(new_k, current_email):
                entry_new_key.delete(0, tk.END)
                refresh_keys_list()
                messagebox.showinfo("Éxito", "API Key agregada correctamente", parent=ventana)
            else:
                messagebox.showerror("Error", "Key inválida o duplicada", parent=ventana)
        
        def delete_key(index):
            if messagebox.askyesno("Confirmar", "¿Eliminar esta API Key?", parent=ventana):
                current_email = gemini_api.CURRENT_USER_EMAIL
                if gemini_api.remove_api_key(index, current_email):
                    refresh_keys_list()

        def reset_status():
            current_email = gemini_api.CURRENT_USER_EMAIL
            gemini_api.reset_keys_status(current_email)
            refresh_keys_list()
            # Forzar reconfiguración para que tome una activa
            gemini_api.configurar_gemini() 
            messagebox.showinfo("Restablecido", "Estatus de todas las keys restablecido a ACTIVO", parent=ventana)

        # Input para nueva key
        add_frame = tk.Frame(keys_label_frame, bg=COLOR_BG)
        add_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        entry_new_key = tk.Entry(add_frame, bg="white", width=40, relief="solid", bd=1)
        entry_new_key.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        tk.Button(add_frame, text="➕ Agregar Key", bg=PALETTE["brand"], fg="white", 
                 command=add_new_key).pack(side="left")
        
        # Link obtener key
        link = tk.Label(keys_label_frame, text="🔗 Obtener Key en Google AI Studio", 
                       bg=COLOR_BG, fg="#1976D2", cursor="hand2", font=("Segoe UI", 9, "underline"))
        link.pack(anchor="w", padx=10, pady=(0, 10))
        link.bind("<Button-1>", lambda e: self._open_url("https://aistudio.google.com/app/apikey"))

        # Botón Reset Status
        tk.Button(keys_label_frame, text="🔄 Restablecer Estatus (Todas a Verde)", 
                 bg="#607D8B", fg="white", command=reset_status).pack(anchor="e", padx=10, pady=5)
        
        # --- SECCIÓN DE MODELO ---
        model_frame = tk.LabelFrame(scrollable_frame, text=" Modelo Gemini ", 
                                  bg=COLOR_BG, fg="#333333", font=("Segoe UI", 11, "bold"))
        model_frame.pack(fill="x", padx=5, pady=10, ipady=5)
        
        modelo_var = tk.StringVar(value=GEMINI_MODEL_SELECTED)
        
        tk.Label(model_frame, 
                text=f"Modelo actual: {GEMINI_MODEL_SELECTED}",
                bg=COLOR_BG, fg="#1976D2", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=8)
        
        tk.Label(model_frame, 
                text="💡 Límite: 15 RPM (requests por minuto)",
                bg=COLOR_BG, fg="#666666", justify="left", font=("Segoe UI", 8)).pack(anchor="w", padx=25, pady=2)

        # Cargar lista inicial
        refresh_keys_list()

        # --- BOTONES FINALES ---
        btn_action_frame = tk.Frame(ventana, bg=COLOR_BG)
        btn_action_frame.pack(fill="x", padx=20, pady=15)
        
        def save_and_close():
            # Guardamos modelo seleccionado
            gemini_api.GEMINI_MODEL_SELECTED = modelo_var.get()
            # Las keys ya se guardaron al agregarlas
            # Reconfigurar con la primera disponible
            gemini_api.configurar_gemini()
            ventana.destroy()
            messagebox.showinfo("Configuración", "Cambios guardados correctamente", parent=self.root)
            
        tk.Button(btn_action_frame, text="Guardar y Cerrar", bg=PALETTE["brand"], fg="white",
                 width=20, font=("Segoe UI", 10, "bold"), command=save_and_close).pack(side="right")
        
        tk.Button(btn_action_frame, text="Cancelar", bg="#999999", fg="white",
                 width=15, font=("Segoe UI", 10), command=ventana.destroy).pack(side="right", padx=10)
        
        # Centrar ventana
        self.root.update_idletasks()
        y = self.root.winfo_rooty() + (self.root.winfo_height()//2 - 190)
        try:
            ventana.geometry(f"+{x}+{y}")
        except:
            pass
    
    def _open_url(self, url):
        """Abre URL en el navegador"""
        import webbrowser
        webbrowser.open(url)
    
    def setup_results_panel(self, parent):
        """Configura el panel de resultados con sub-paneles verticales"""
        # Vertical PanedWindow for results area
        results_paned = tk.PanedWindow(parent, orient=tk.VERTICAL, sashwidth=5, bg="#cccccc")
        results_paned.pack(fill="both", expand=True)
        
        # Top section: Results list + TXT viewer (side by side)
        top_frame = tk.Frame(results_paned, bg="#fceff1")
        results_paned.add(top_frame, minsize=300)
        
        # Horizontal split for list and viewer
        top_paned = tk.PanedWindow(top_frame, orient=tk.HORIZONTAL, sashwidth=5, bg="#cccccc")
        top_paned.pack(fill="both", expand=True)
        
        # Results list (left)
        list_container = tk.Frame(top_paned, bg="#fceff1")
        top_paned.add(list_container, minsize=250)
        self.results_panel = ResultsPanel(list_container, on_selection_callback=self.on_audio_selected)
        
        # TXT viewer (right)
        viewer_container = tk.Frame(top_paned, bg="#fceff1")
        top_paned.add(viewer_container, minsize=350)
        self.txt_viewer = TxtViewer(viewer_container)
        
        # Bottom section: Audio player
        bottom_frame = tk.Frame(results_paned, bg="#fceff1")
        results_paned.add(bottom_frame, minsize=150)
        self.audio_player = AudioPlayer(bottom_frame)
    
    def update_results_panel(self):
        """Actualiza el panel de resultados con el último análisis"""
        if self.results_panel and self.analysis_results:
            # El último resultado ya fue agregado a self.analysis_results
            # Actualizamos el panel
            last_result = self.analysis_results[-1]
            self.results_panel.add_result(last_result)
            logger.info(f"Results panel updated with: {last_result.get('nombre_archivo')}")
    
    def on_audio_selected(self, result):
        """Callback cuando se selecciona un audio de la lista"""
        logger.info(f"Audio selected: {result.get('nombre_archivo')}")
        
        # Cargar contenido TXT
        txt_path = result.get("txt_path")
        if txt_path and os.path.exists(txt_path):
            self.txt_viewer.load_content(txt_path)
            # Cargar TXT para exportación PDF
            self.audio_player.load_for_export(txt_path)
        else:
            logger.warning(f"TXT file not found: {txt_path}")
        
        # Cargar audio en el reproductor
        audio_path = result.get("audio_path")
        if audio_path and os.path.exists(audio_path):
            self.audio_player.load_audio(audio_path)
        else:
            logger.warning(f"Audio file not found: {audio_path}")

    def seleccionar_archivo(self):
        archivos = filedialog.askopenfilenames(
            filetypes=[("Multimedia", "*.mp3 *.wav *.mp4 *.mov *.mkv *.m4a *.aac *.wma *.ogg *.flac *.gsm *.3gp *.avi")])
        if len(archivos) > 10:
            messagebox.showerror("Límite excedido", "Solo puedes seleccionar hasta 10 archivos.")
        elif archivos:
            self.ruta_audio = archivos
            messagebox.showinfo("🎧 Archivos seleccionados", f"{len(archivos)} archivos listos para analizar.")

    def seleccionar_carpeta_guardado(self):
        carpeta = filedialog.askdirectory(title="Selecciona carpeta de guardado")
        if carpeta:
            try:
                os.makedirs(carpeta, exist_ok=True)
                self.carpeta_guardado = carpeta
                messagebox.showinfo("📂 Carpeta seleccionada", f"Los archivos se guardarán en:\n{carpeta}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear/usar la carpeta:\n{e}")

    def solicitar_datos_y_analizar(self):
        if not self.ruta_audio:
            messagebox.showerror("Error", "Primero debes seleccionar al menos un archivo.")
            return
        if not self.carpeta_guardado:
            messagebox.showerror("Error", "Debes seleccionar la carpeta donde se guardarán los resultados.")
            return
        
        # Modal
        ventana = tk.Toplevel(self.root)
        ventana.title("Datos del análisis")
        ventana.configure(bg="#fceff1")
        
        frm = tk.Frame(ventana, bg="#fceff1")
        frm.pack(padx=10, pady=10)

        tk.Label(frm, text="Nombre del Evaluador:", bg="#fceff1", font=self.fonts["body"]).grid(row=0, column=0, sticky="w", pady=4)
        entry_evaluador = tk.Entry(frm, width=40)
        entry_evaluador.grid(row=0, column=1, padx=8, pady=4)
        if self.nombre_evaluador:
            entry_evaluador.insert(0, self.nombre_evaluador)
            entry_evaluador.config(state="readonly")

        tk.Label(frm, text="Nombre del asesor:", bg="#fceff1", font=self.fonts["body"]).grid(row=1, column=0, sticky="w", pady=4)
        entry_asesor = tk.Entry(frm, width=40)
        entry_asesor.grid(row=1, column=1, padx=8, pady=4)

        tk.Label(frm, text="Departamento:", bg="#fceff1", font=self.fonts["body"]).grid(row=2, column=0, sticky="w", pady=4)
        cb_dept = ttk.Combobox(frm, values=DEPT_OPTIONS_FIXED, state="readonly", width=37)
        cb_dept.grid(row=2, column=1, padx=8, pady=4)
        cb_dept.current(0)

        def continuar():
            eval_name = entry_evaluador.get().strip()
            self.nombre_evaluador = eval_name or self.nombre_evaluador
            self.nombre_asesor = entry_asesor.get().strip()
            self.selected_department = cb_dept.get().strip()
            
            if not self.nombre_evaluador or not self.nombre_asesor or not self.selected_department:
                messagebox.showerror("Error", "Completa Evaluador, Asesor y Departamento.")
                return
            
            ventana.destroy()
            self.run_analysis_loop()

        tk.Button(ventana, text="Iniciar análisis", command=continuar, bg=PALETTE["brand"], fg="white").pack(pady=10)

    def _call_department_eval(self, dept: str, audio_path: str) -> dict:
        rubric = load_dept_rubric_json_local(dept)
        if not rubric:
            # Fallback message
            listing = []
            if os.path.isdir(LOCAL_RUBRICS_DIR):
                try:
                    listing = [fn for fn in os.listdir(LOCAL_RUBRICS_DIR) if fn.lower().endswith(".json")]
                except Exception:
                    pass
            messagebox.showerror(
                "Rúbrica no encontrada",
                "No se encontró el archivo local de rúbrica:\n"
                f"  {os.path.join(LOCAL_RUBRICS_DIR, dept + '.json')}\n\n"
                + ("Archivos encontrados:\n- " + "\n- ".join(listing) if listing else "No hay JSON en 'rubricas/'")
            )
            return {
                "department": dept,
                "sections": [{"name": "Sin datos", "items": [{"key": "n/a", "peso": 10, "ok": False, "aplicable": True, "evidencia": ""}]}],
                "section_VI": {"criticos": []},
                "fortalezas": [],
                "compromisos": [],
                "contenido_evaluador": "No se pudo cargar la rúbrica del departamento."
            }
        
        prompt = rubric_json_to_prompt(dept, rubric)
        fallback = {
            "department": dept,
            "sections": rubric.get("sections", []) or [{"name": "Sin datos", "items": [{"key": "n/a", "peso": 10, "ok": False, "aplicable": True, "evidencia": ""}]}],
            "section_VI": rubric.get("section_VI", {"criticos": []}),
            "fortalezas": rubric.get("fortalezas", []),
            "compromisos": rubric.get("compromisos", []),
            "contenido_evaluador": ""
        }
        return llm_json_or_mock(prompt, audio_path, fallback)

    def run_analysis_loop(self):
        if pd is None:
            messagebox.showerror("Dependencia", "Pandas no está instalado. Instala con: pip install pandas")
            return

        save_dir = self.carpeta_guardado
        dept = self.selected_department

        resultados, scores_finales, sentiments_glob = [], [], []
        strengths_counter, failed_items = Counter(), Counter()
        dept_counts, dept_score_sum = Counter(), defaultdict(int)
        critical_fail_count = 0
        all_cumplido_cols = set()

        for path in self.ruta_audio:
            try:
                nombre_archivo = os.path.basename(path)
                ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                
                audio_final = path
                
                # Check extension
                ext = os.path.splitext(path)[1].lower()
                
                # Special handling for GSM (convert to WAV using soundfile)
                if ext == ".gsm":
                     wav_path = os.path.join(save_dir, f"{pathlib.Path(nombre_archivo).stem}_converted.wav")
                     converted = convert_to_wav(path, wav_path)
                     if converted:
                         audio_final = converted
                     else:
                         messagebox.showwarning("Error conversión", f"No se pudo convertir {nombre_archivo}. Revisa logs.")
                         continue
                
                # For everything else, verify Gemini support
                elif not is_gemini_supported(path):
                    logger.warning(f"Formato no soportado nativamente: {path}")
                    messagebox.showwarning("Formato no soportado", 
                        f"El archivo {nombre_archivo} tiene una extensión no soportada nativamente.\n"
                        "Athenas Lite: Usa WAV, MP3, MP4, M4A, o GSM.")
                    continue

                # Audio duration with mutagen
                dur_secs = get_audio_duration(audio_final)
                dur_str = human_duration(dur_secs)

                # Sentiment
                val, clasif, comentario, resumen_calido = analizar_sentimiento(audio_final)
                sent_cli, sent_ase = analizar_sentimiento_por_roles(audio_final)

                # Evaluation
                eval_data = self._call_department_eval(dept, audio_final)
                eval_data = aplicar_defaults_items(eval_data)
                
                sections = eval_data.get("sections", [])
                criticos = eval_data.get("section_VI", {}).get("criticos", [])
                fortalezas = eval_data.get("fortalezas", [])
                contenido_evaluador = eval_data.get("contenido_evaluador", "")

                # Scoring
                score_bruto, fallo_critico, score_final, det_atrib = compute_scores_with_na(sections, criticos)
                resumen = " • ".join(fortalezas[:2]) if fortalezas else resumen_calido

                # Write TXT
                txt_path = os.path.join(save_dir, f"{pathlib.Path(nombre_archivo).stem}_ATHENAS_Lite.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    # (Replicating the TXT output format exactly)
                    f.write(f"Asesor: {self.nombre_asesor}\n")
                    f.write(f"Evaluador: {self.nombre_evaluador}\n")
                    f.write(f"Archivo: {nombre_archivo}\n")
                    f.write(f"Departamento seleccionado: {dept}\n")
                    f.write(f"Timestamp: {ts}\n")
                    f.write(f"Duración: {dur_str}\n\n")
                    f.write("Resumen:\n")
                    f.write(resumen or "N/A")
                    f.write("\n\nContenido para el evaluador:\n")
                    f.write(contenido_evaluador or "N/A")
                    f.write("\n--- CALIFICACIÓN FINAL ---\n")
                    f.write(f"Score de Atributos (Puntaje Bruto, N/A incluido): {score_bruto}%\n")
                    f.write(f"Score Final (Aplicando Críticos): {score_final}%\n")
                    f.write("\n--- PUNTOS CRÍTICOS ---\n")
                    if not criticos:
                        f.write("(Sin críticos configurados)\n")
                    else:
                        for c in criticos:
                            keyc = c.get("key","(sin_key)")
                            okc = c.get("ok", False)
                            f.write(f"{keyc}: {'✅ Cumplido' if okc else '❌ No cumplido'}\n")
                    f.write("\n--- Detalle por atributo ---\n")
                    for d in det_atrib:
                        est = d["estado"]
                        marca = "✅ Cumplido" if est == "OK" else ("❌ No cumplido" if est == "NO" else "🟡 N/A")
                        f.write(f"{marca} {d['key']} → {d['otorgado']} / {d['peso']}\n")
                    f.write("\n--- Sentimiento ---\n")
                    f.write(f"Valoración (1-10): {val}\n")
                    f.write(f"Clasificación: {clasif}\n")
                    f.write(f"Comentario emocional: {comentario}\n")
                    f.write("\n--- Sentimiento por roles ---\n")
                    f.write(f"Cliente -> {sent_cli['clasificacion']} ({sent_cli['valor']}/10). {sent_cli['comentario']}\n")
                    f.write(f"Asesor  -> {sent_ase['clasificacion']} ({sent_ase['valor']}/10). {sent_ase['comentario']}\n")

                # Add result to tracking
                self.analysis_results.append({
                    "audio_path": audio_final,
                    "txt_path": txt_path,
                    "nombre_archivo": nombre_archivo,
                    "departamento": dept,
                    "score": score_final,
                    "timestamp": ts
                })
                
                # Update results panel
                self.update_results_panel()

                # Data collection for CSV
                fila_atrib, _keys = _atributos_a_columnas_valor(det_atrib)
                all_cumplido_cols.update(fila_atrib.keys())

                r = {
                    "archivo": nombre_archivo,
                    "asesor": self.nombre_asesor,
                    "timestamp": ts,
                    "resumen": resumen,
                    "sentimiento": val,
                    "clasificación": clasif,
                    "comentario": comentario,
                    "evaluador": self.nombre_evaluador,
                    "duración": dur_str,
                    "duracion_seg": (round(dur_secs, 3) if dur_secs is not None else None),
                    "contenido_evaluador": contenido_evaluador,
                    "porcentaje_evaluacion": score_final,
                    "score_bruto": score_bruto,
                    "departamento": dept,
                    "sentimiento_cliente": sent_cli["valor"],
                    "clasificación_cliente": sent_cli["clasificacion"],
                    "comentario_cliente": sent_cli["comentario"],
                    "sentimiento_asesor": sent_ase["valor"],
                    "clasificación_asesor": sent_ase["clasificacion"],
                    "comentario_asesor": sent_ase["comentario"]
                }
                r.update(fila_atrib)
                resultados.append(r)
                scores_finales.append(score_final)
                sentiments_glob.append(val)

                # Stats accumulation
                dept_counts[dept] += 1
                dept_score_sum[dept] += score_final
                if any(not c.get("ok", False) for c in (criticos or [])):
                    critical_fail_count += 1
                for sec in (sections or []):
                    for it in sec.get("items", []):
                        if it.get("aplicable", True) and not it.get("ok", False):
                            failed_items[it.get("key","(sin_key)")] += 1
                for s in (fortalezas or []):
                    strengths_counter[s.strip()] += 1

            except Exception as e:
                logger.exception(f"Error processing file {path}")
                messagebox.showerror("Error", f"Fallo al analizar {path}:\n{e}")

        # Post-processing CSV and Summary
        if resultados:
            for row in resultados:
                for col in all_cumplido_cols:
                    row.setdefault(col, "")
            
            df = pd.DataFrame(resultados)
            asesor_slug = re.sub(r'[^A-Za-z0-9_-]+', '_', (self.nombre_asesor or 'asesor').strip()) or 'asesor'
            ts_all = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_path = os.path.join(save_dir, f"ATHENAS_Lite_{asesor_slug}_{ts_all}.csv")
            
            try:
                df.to_csv(export_path, index=False, encoding="utf-8-sig")
            except Exception as e:
                messagebox.showerror("CSV", f"No se pudo escribir el CSV:\n{e}")
                export_path = None

            # Summary TXT
            resumen_path = None
            if len(resultados) >= 2:
                total = len(resultados)
                avg_score = round(sum(scores_finales)/total, 2) if scores_finales else 0.0
                avg_sent = round(sum(sentiments_glob)/total, 2) if sentiments_glob else 0.0

                lines = []
                lines.append("=== Resumen Consolidado ATHENAS Lite ===")
                lines.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append(f"Evaluador: {self.nombre_evaluador}")
                lines.append(f"Asesor: {self.nombre_asesor}")
                lines.append("")
                lines.append(f"Total de llamadas: {total}")
                lines.append(f"Promedio Score Final (%): {avg_score}")
                lines.append(f"Promedio Sentimiento (1-10): {avg_sent}")
                lines.append(f"Fallos críticos detectados: {critical_fail_count}")
                lines.append("")
                lines.append("— Distribución por departamento —")
                for d, c in dept_counts.items():
                    prom = round(dept_score_sum[d]/c, 2) if c else 0.0
                    lines.append(f"  {d}: {c} llamadas | Score prom: {prom}")
                lines.append("")
                lines.append("— Top 5 fallas —")
                for key, cnt in failed_items.most_common(5):
                    lines.append(f"  {key}: {cnt} veces")
                lines.append("")
                lines.append("— Top 5 fortalezas —")
                for s, cnt in strengths_counter.most_common(5):
                    lines.append(f"  {s}: {cnt} veces")

                resumen_path = os.path.join(save_dir, f"ATHENAS_Lite_Resumen_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt")
                try:
                    with open(resumen_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines))
                except Exception as e:
                    messagebox.showerror("TXT", f"No se pudo escribir el resumen:\n{e}")

                messagebox.showinfo("🎉 Resumen consolidado",
                                    f"CSV: {export_path or 'N/A'}\nResumen: {resumen_path or 'N/A'}")
            else:
                r = resultados[0]
                messagebox.showinfo(
                    "✅ Análisis completado",
                    f"{r['archivo']}\nDepto: {r['departamento']} | Score: {r['porcentaje_evaluacion']}%\n"
                    f"Sentimiento: {r['clasificación']} ({r['sentimiento']}/10)\nCSV: {export_path or 'N/A'}"
                )

            # Drive Upload
            try:
                # Need to import DRIVE_EXPORT_FOLDER_ID to check if configured? 
                # Actually subir_csv_a_drive handles the check nicely.
                if export_path and pd is not None:
                     # Check if we should even try (is simple config check exposed?) -> Rely on the function handling None returns
                     df_up = pd.DataFrame(resultados)
                     fn = f"ATLite_compilado_{(self.nombre_asesor or 'asesor').strip().replace(' ','_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                     link = subir_csv_a_drive(df_up, fn)
                     if link:
                         messagebox.showinfo("📤 Drive", f"Compilado subido a Drive:\n{link}")
            except Exception as e:
                logger.error(f"Drive upload failed: {e}")

def start_app():
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
