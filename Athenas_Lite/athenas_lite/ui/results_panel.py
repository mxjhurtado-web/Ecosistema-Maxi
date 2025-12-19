

import os
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import logging

logger = logging.getLogger("athenas_lite")

# Try to import pygame for audio playback
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("pygame not available - audio playback will be disabled")


class AudioPlayer:
    """Reproductor de audio integrado usando pygame con barra de progreso"""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_audio = None
        self.current_txt_path = None  # Track TXT file for PDF export
        self.is_paused = False
        self.audio_length = 0  # Duración total en segundos
        self.is_seeking = False  # Flag para evitar loops durante seek
        self.update_job = None  # ID del job de actualización
        
        # Frame principal
        self.frame = tk.LabelFrame(parent, text=" 🎵 Reproductor de Audio ", 
                                   bg="#fceff1", fg="#0D47A1", font=("Segoe UI", 11, "bold"))
        self.frame.pack(fill="x", padx=5, pady=5)
        
        # Info del audio actual
        self.info_label = tk.Label(self.frame, text="No hay audio cargado", 
                                   bg="#fceff1", fg="#666666", font=("Segoe UI", 9))
        self.info_label.pack(pady=(10, 5))
        
        # Frame para barra de progreso y tiempo
        progress_frame = tk.Frame(self.frame, bg="#fceff1")
        progress_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        # Tiempo actual
        self.time_label = tk.Label(progress_frame, text="0:00", 
                                   bg="#fceff1", fg="#0D47A1", font=("Consolas", 9, "bold"))
        self.time_label.pack(side="left", padx=(0, 5))
        
        # Barra de progreso (Scale)
        self.progress_bar = tk.Scale(
            progress_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            showvalue=0,
            bg="#fceff1",
            fg="#0D47A1",
            troughcolor="#E3F2FD",
            activebackground="#1976D2",
            highlightthickness=0,
            sliderrelief=tk.FLAT,
            command=self.on_seek,
            state="disabled"
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        
        # Duración total
        self.duration_label = tk.Label(progress_frame, text="0:00", 
                                      bg="#fceff1", fg="#0D47A1", font=("Consolas", 9, "bold"))
        self.duration_label.pack(side="left", padx=(5, 0))
        
        # Controles
        controls_frame = tk.Frame(self.frame, bg="#fceff1")
        controls_frame.pack(pady=10)
        
        # Colores mejorados con mejor contraste (paleta ATHENAS)
        btn_style = {
            "font": ("Segoe UI", 10, "bold"),  # Bold para mejor legibilidad
            "width": 10,
            "height": 1,
            "relief": tk.RAISED,
            "bd": 2
        }
        
        # Play - Verde más oscuro para mejor contraste
        self.btn_play = tk.Button(controls_frame, text="▶️ Play", 
                                  command=self.play, bg="#2E7D32", fg="white", **btn_style)
        self.btn_play.pack(side="left", padx=5)
        
        # Pause - Naranja más oscuro
        self.btn_pause = tk.Button(controls_frame, text="⏸️ Pause", 
                                   command=self.pause, bg="#EF6C00", fg="white", 
                                   state="disabled", **btn_style)
        self.btn_pause.pack(side="left", padx=5)
        
        # Stop - Rojo más oscuro
        self.btn_stop = tk.Button(controls_frame, text="⏹️ Stop", 
                                  command=self.stop, bg="#C62828", fg="white", 
                                  state="disabled", **btn_style)
        self.btn_stop.pack(side="left", padx=5)
        
        # Separator
        tk.Frame(controls_frame, width=20, bg="#fceff1").pack(side="left")
        
        # PDF Export button - Morado más oscuro
        self.btn_export_pdf = tk.Button(controls_frame, text="📄 PDF", 
                                        command=self.export_pdf, bg="#6A1B9A", fg="white",
                                        state="disabled", **btn_style)
        self.btn_export_pdf.pack(side="left", padx=5)
        
        if not PYGAME_AVAILABLE:
            self.btn_play.config(state="disabled")
            self.info_label.config(text="⚠️ pygame no disponible - instala con: pip install pygame")
    
    def format_time(self, seconds):
        """Formatea segundos a MM:SS"""
        if seconds < 0:
            seconds = 0
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"
    
    def on_seek(self, value):
        """Callback cuando el usuario mueve la barra de progreso"""
        if not PYGAME_AVAILABLE or not self.current_audio or self.is_seeking:
            return
        
        try:
            # Calcular posición en segundos
            position = (float(value) / 100.0) * self.audio_length
            
            # Establecer posición en pygame
            pygame.mixer.music.set_pos(position)
            
            # Actualizar etiqueta de tiempo
            self.time_label.config(text=self.format_time(position))
            
            logger.info(f"Seeked to {self.format_time(position)}")
        except Exception as e:
            logger.error(f"Error seeking: {e}")
    
    def update_progress(self):
        """Actualiza la barra de progreso automáticamente"""
        if not PYGAME_AVAILABLE or not self.current_audio:
            return
        
        try:
            # Verificar si está reproduciéndose
            if pygame.mixer.music.get_busy() and not self.is_paused:
                # Obtener posición actual (en segundos)
                pos = pygame.mixer.music.get_pos() / 1000.0
                
                # Actualizar barra de progreso
                if self.audio_length > 0:
                    self.is_seeking = True  # Evitar loop con on_seek
                    progress_percent = (pos / self.audio_length) * 100
                    self.progress_bar.set(progress_percent)
                    self.is_seeking = False
                
                # Actualizar tiempo
                self.time_label.config(text=self.format_time(pos))
                
                # Programar siguiente actualización
                self.update_job = self.frame.after(100, self.update_progress)
            else:
                # Si terminó de reproducir, resetear
                if not self.is_paused and pygame.mixer.music.get_pos() == -1:
                    self.progress_bar.set(0)
                    self.time_label.config(text="0:00")
                    self.btn_play.config(state="normal")
                    self.btn_pause.config(state="disabled")
                    self.btn_stop.config(state="disabled")
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
    
    def load_audio(self, audio_path):
        """Carga un archivo de audio"""
        if not PYGAME_AVAILABLE:
            return False
        
        try:
            self.current_audio = audio_path
            pygame.mixer.music.load(audio_path)
            
            # Obtener duración del audio
            try:
                from ..services.system_tools import get_audio_duration
                self.audio_length = get_audio_duration(audio_path) or 0
            except:
                self.audio_length = 0
            
            filename = os.path.basename(audio_path)
            self.info_label.config(text=f"🎵 {filename}")
            self.duration_label.config(text=self.format_time(self.audio_length))
            self.btn_play.config(state="normal")
            self.progress_bar.config(state="normal")
            self.progress_bar.set(0)
            self.time_label.config(text="0:00")
            self.is_paused = False
            logger.info(f"Audio loaded: {filename} ({self.format_time(self.audio_length)})")
            return True
        except Exception as e:
            logger.error(f"Error loading audio: {e}")
            self.info_label.config(text=f"❌ Error cargando audio")
            return False
    
    def play(self):
        """Reproduce el audio"""
        if not PYGAME_AVAILABLE or not self.current_audio:
            return
        
        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
            else:
                pygame.mixer.music.play()
            
            self.btn_play.config(state="disabled")
            self.btn_pause.config(state="normal")
            self.btn_stop.config(state="normal")
            
            # Iniciar actualización de progreso
            self.update_progress()
            
            logger.info("Audio playing")
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def pause(self):
        """Pausa la reproducción"""
        if not PYGAME_AVAILABLE:
            return
        
        try:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.btn_play.config(state="normal")
            self.btn_pause.config(state="disabled")
            
            # Detener actualización de progreso
            if self.update_job:
                self.frame.after_cancel(self.update_job)
                self.update_job = None
            
            logger.info("Audio paused")
        except Exception as e:
            logger.error(f"Error pausing audio: {e}")
    
    def stop(self):
        """Detiene la reproducción"""
        if not PYGAME_AVAILABLE:
            return
        
        try:
            pygame.mixer.music.stop()
            self.is_paused = False
            self.btn_play.config(state="normal")
            self.btn_pause.config(state="disabled")
            self.btn_stop.config(state="disabled")
            
            # Detener actualización de progreso y resetear
            if self.update_job:
                self.frame.after_cancel(self.update_job)
                self.update_job = None
            
            self.progress_bar.set(0)
            self.time_label.config(text="0:00")
            
            logger.info("Audio stopped")
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
    
    def load_for_export(self, txt_path):
        """Carga la ruta del TXT para permitir exportación a PDF"""
        self.current_txt_path = txt_path
        if txt_path and os.path.exists(txt_path):
            self.btn_export_pdf.config(state="normal")
        else:
            self.btn_export_pdf.config(state="disabled")
    
    def export_pdf(self):
        """Exporta el contenido del análisis a PDF profesional"""
        if not self.current_txt_path or not os.path.exists(self.current_txt_path):
            messagebox.showerror("Error", "No hay archivo TXT disponible para exportar")
            return
        
        try:
            # Mostrar diálogo para comentarios del evaluador
            comments_dialog = tk.Toplevel(self.frame)
            comments_dialog.title("Comentarios del Evaluador")
            comments_dialog.geometry("500x300")
            comments_dialog.configure(bg="#fceff1")
            comments_dialog.transient(self.frame)
            comments_dialog.grab_set()
            
            # Centrar ventana
            comments_dialog.update_idletasks()
            x = (comments_dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (comments_dialog.winfo_screenheight() // 2) - (300 // 2)
            comments_dialog.geometry(f"500x300+{x}+{y}")
            
            # Variable para almacenar resultado
            result = {"comments": "", "cancelled": True}
            
            # Label
            tk.Label(comments_dialog, text="Comentarios Adicionales del Evaluador:", 
                    bg="#fceff1", fg="#0D47A1", font=("Segoe UI", 11, "bold")).pack(pady=10)
            
            # Text widget para comentarios
            comments_frame = tk.Frame(comments_dialog, bg="#fceff1")
            comments_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            comments_text = tk.Text(comments_frame, wrap=tk.WORD, font=("Segoe UI", 10),
                                   height=8, width=50)
            comments_scroll = tk.Scrollbar(comments_frame, command=comments_text.yview)
            comments_text.config(yscrollcommand=comments_scroll.set)
            
            comments_text.pack(side="left", fill="both", expand=True)
            comments_scroll.pack(side="right", fill="y")
            
            # Botones
            btn_frame = tk.Frame(comments_dialog, bg="#fceff1")
            btn_frame.pack(pady=10)
            
            def on_accept():
                result["comments"] = comments_text.get("1.0", tk.END).strip()
                result["cancelled"] = False
                comments_dialog.destroy()
            
            def on_cancel():
                result["cancelled"] = True
                comments_dialog.destroy()
            
            tk.Button(btn_frame, text="✅ Generar PDF", command=on_accept,
                     bg="#2E7D32", fg="white", font=("Segoe UI", 10, "bold"),
                     width=15, height=1).pack(side="left", padx=5)
            
            tk.Button(btn_frame, text="❌ Cancelar", command=on_cancel,
                     bg="#C62828", fg="white", font=("Segoe UI", 10, "bold"),
                     width=15, height=1).pack(side="left", padx=5)
            
            # Esperar a que se cierre el diálogo
            self.frame.wait_window(comments_dialog)
            
            # Si se canceló, salir
            if result["cancelled"]:
                return
            
            # Importar módulo de exportación PDF
            from ..services.pdf_exporter import generate_pdf_report
            
            # Obtener nombre base del archivo
            base_name = os.path.splitext(os.path.basename(self.current_txt_path))[0]
            default_name = f"{base_name}.pdf"
            
            # Diálogo para guardar PDF
            pdf_path = filedialog.asksaveasfilename(
                title="Guardar PDF",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=default_name
            )
            
            if not pdf_path:
                return  # Usuario canceló
            
            # Buscar logos
            maxi_logo_path = None
            athenas_logo_path = None
            
            # Buscar logo de Maxi
            possible_maxi_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "maxisend_logo.png"),
                os.path.join(os.path.dirname(__file__), "..", "..", "maxisend_logo.png")
            ]
            
            for path in possible_maxi_paths:
                if os.path.exists(path):
                    maxi_logo_path = path
                    break
            
            # Buscar logo de ATHENAS
            possible_athenas_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "athenas2.png"),
                os.path.join(os.path.dirname(__file__), "..", "..", "athenas2.png")
            ]
            
            for path in possible_athenas_paths:
                if os.path.exists(path):
                    athenas_logo_path = path
                    break
            
            # Generar PDF con comentarios y ambos logos
            success = generate_pdf_report(
                self.current_txt_path, 
                pdf_path, 
                maxi_logo_path=maxi_logo_path,
                athenas_logo_path=athenas_logo_path,
                evaluator_comments=result["comments"]
            )
            
            if success:
                messagebox.showinfo("Éxito", f"PDF generado exitosamente:\n{pdf_path}")
                logger.info(f"PDF exported: {pdf_path}")
            else:
                messagebox.showerror("Error", "No se pudo generar el PDF. Revisa los logs.")
                
        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            messagebox.showerror("Error", f"Error al exportar PDF:\n{e}")
    
    def is_playing(self):
        """Retorna True si el audio está reproduciéndose"""
        if not PYGAME_AVAILABLE:
            return False
        try:
            return pygame.mixer.music.get_busy()
        except:
            return False


class TxtViewer:
    """Visor de contenido de archivos TXT"""
    
    def __init__(self, parent):
        self.parent = parent
        
        # Frame principal
        self.frame = tk.LabelFrame(parent, text=" 📄 Contenido del Análisis ", 
                                   bg="#fceff1", fg="#333333", font=("Segoe UI", 10, "bold"))
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Text widget con scroll
        self.text_widget = scrolledtext.ScrolledText(
            self.frame, 
            wrap=tk.WORD, 
            font=("Consolas", 9),
            bg="white",
            fg="#333333",
            padx=10,
            pady=10,
            state="disabled"
        )
        self.text_widget.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurar tags para formato
        self.text_widget.tag_config("header", font=("Segoe UI", 10, "bold"), foreground="#0D47A1")
        self.text_widget.tag_config("score", font=("Consolas", 10, "bold"), foreground="#4CAF50")
        self.text_widget.tag_config("critical", font=("Consolas", 9, "bold"), foreground="#F44336")
        self.text_widget.tag_config("success", foreground="#4CAF50")
        self.text_widget.tag_config("fail", foreground="#F44336")
        self.text_widget.tag_config("na", foreground="#FF9800")
    
    def load_content(self, txt_path):
        """Carga y muestra el contenido de un archivo TXT"""
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self.text_widget.config(state="normal")
            self.text_widget.delete(1.0, tk.END)
            
            # Insertar contenido con formato básico
            lines = content.split("\n")
            for line in lines:
                # Detectar y aplicar formato
                if line.startswith("---"):
                    self.text_widget.insert(tk.END, line + "\n", "header")
                elif "Score" in line or "Puntaje" in line:
                    self.text_widget.insert(tk.END, line + "\n", "score")
                elif "CRÍTICOS" in line or "Críticos" in line:
                    self.text_widget.insert(tk.END, line + "\n", "critical")
                elif "✅" in line:
                    self.text_widget.insert(tk.END, line + "\n", "success")
                elif "❌" in line:
                    self.text_widget.insert(tk.END, line + "\n", "fail")
                elif "🟡" in line or "N/A" in line:
                    self.text_widget.insert(tk.END, line + "\n", "na")
                else:
                    self.text_widget.insert(tk.END, line + "\n")
            
            self.text_widget.config(state="disabled")
            self.text_widget.see(1.0)  # Scroll to top
            logger.info(f"TXT content loaded: {txt_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading TXT: {e}")
            self.clear()
            self.text_widget.config(state="normal")
            self.text_widget.insert(tk.END, f"❌ Error cargando archivo:\n{e}")
            self.text_widget.config(state="disabled")
            return False
    
    def clear(self):
        """Limpia el visor"""
        self.text_widget.config(state="normal")
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state="disabled")


class ResultsPanel:
    """Panel principal de resultados con lista de audios"""
    
    def __init__(self, parent, on_selection_callback=None):
        self.parent = parent
        self.on_selection_callback = on_selection_callback
        self.results = []
        
        # Frame principal
        self.frame = tk.Frame(parent, bg="#fceff1")
        self.frame.pack(fill="both", expand=True)
        
        # Lista de audios (Treeview)
        list_frame = tk.LabelFrame(self.frame, text=" 📋 Audios Analizados ", 
                                   bg="#fceff1", fg="#333333", font=("Segoe UI", 10, "bold"))
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Crear Treeview
        columns = ("archivo", "departamento", "score", "timestamp")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        # Configurar columnas
        self.tree.heading("archivo", text="Archivo")
        self.tree.heading("departamento", text="Departamento")
        self.tree.heading("score", text="Score")
        self.tree.heading("timestamp", text="Fecha/Hora")
        
        self.tree.column("archivo", width=200)
        self.tree.column("departamento", width=150)
        self.tree.column("score", width=80)
        self.tree.column("timestamp", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # Mensaje inicial
        self.empty_label = tk.Label(list_frame, text="No hay resultados aún. Analiza audios para verlos aquí.",
                                   bg="white", fg="#999999", font=("Segoe UI", 9, "italic"))
        
        if not self.results:
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def add_result(self, result_dict):
        """Agrega un resultado a la lista"""
        self.results.append(result_dict)
        self.update_list()
        logger.info(f"Result added: {result_dict.get('nombre_archivo', 'unknown')}")
    
    def update_list(self):
        """Actualiza la vista de lista"""
        # Limpiar
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Ocultar mensaje vacío si hay resultados
        if self.results:
            self.empty_label.place_forget()
        
        # Agregar items
        for idx, result in enumerate(self.results):
            values = (
                result.get("nombre_archivo", "Unknown"),
                result.get("departamento", "N/A"),
                f"{result.get('score', 0)}%",
                result.get("timestamp", "N/A")
            )
            self.tree.insert("", "end", iid=str(idx), values=values)
        
        # Seleccionar el último agregado
        if self.results:
            last_idx = str(len(self.results) - 1)
            self.tree.selection_set(last_idx)
            self.tree.see(last_idx)
    
    def clear_results(self):
        """Limpia todos los resultados"""
        self.results = []
        self.update_list()
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def get_selected_result(self):
        """Retorna el resultado seleccionado"""
        selection = self.tree.selection()
        if not selection:
            return None
        
        try:
            idx = int(selection[0])
            return self.results[idx]
        except (ValueError, IndexError):
            return None
    
    def _on_select(self, event):
        """Callback interno de selección"""
        if self.on_selection_callback:
            result = self.get_selected_result()
            if result:
                self.on_selection_callback(result)
