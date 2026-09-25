#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Graphical Interface for TEMIS Media Studio
Professional Executive Slate Tkinter UI for Video Process & Screenshot Extraction (100% Local / 0 Tokens).
"""

import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from config.settings import (
    EXPORTS_DIR,
    get_resource_path
)
from services.media_extractor import MediaExtractor
from services.whisper_transcriber import WhisperTranscriber
from services.local_process_builder import LocalProcessBuilder
from services.temis_package_builder import TemisPackageBuilder


class TemisMediaStudioApp:
    """Desktop Application Window for TEMIS Media Studio (100% Offline)"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TEMIS Media Studio — Extractor de Procesos y Bitácoras (100% Local)")
        self.root.geometry("980x720")
        self.root.minsize(860, 640)
        self.root.configure(bg="#0f172a")

        # Set App Icon if available
        icon_path = get_resource_path(os.path.join("resources", "assets", "app_icon.ico"))
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        # State Variables
        self.selected_video_path = tk.StringVar(value="")
        self.whisper_model_var = tk.StringVar(value="base")
        self.status_var = tk.StringVar(value="Listo para seleccionar video o audio de proceso (100% Local).")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.is_processing = False

        # Output Data Store
        self.last_export_dir = ""
        self.last_docx_path = ""
        self.last_json_path = ""
        self.extracted_keyframes = []
        self.analysis_data = {}
        self.transcript_segments = []
        self.thumb_images = []  # Keep references

        self._build_ui()

    def _build_ui(self):
        """Construct modern executive UI"""
        # Style configuration
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure Notebook tabs
        style.configure("TNotebook", background="#0f172a", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1e293b", foreground="#94a3b8", padding=[16, 8], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])

        # 1. HEADER BAR
        header_frame = tk.Frame(self.root, bg="#1e293b", height=70, padx=20, pady=12)
        header_frame.pack(fill="x", side="top")

        # Title & Subtitle
        title_box = tk.Frame(header_frame, bg="#1e293b")
        title_box.pack(side="left")

        lbl_title = tk.Label(
            title_box,
            text="TEMIS Media Studio",
            font=("Segoe UI", 16, "bold"),
            fg="#38bdf8",
            bg="#1e293b"
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            title_box,
            text="Extracción de Bitácoras con Capturas de Pantalla y Transcripción Offline (0 Tokens / 100% Local)",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#1e293b"
        )
        lbl_sub.pack(anchor="w")

        # Offline Status Badge on Header Right
        badge_box = tk.Frame(header_frame, bg="#0f766e", padx=10, pady=4)
        badge_box.pack(side="right")
        
        lbl_badge = tk.Label(
            badge_box,
            text="🔒 MODO 100% LOCAL (0 TOKENS)",
            font=("Segoe UI", 9, "bold"),
            fg="#ccfbf1",
            bg="#0f766e"
        )
        lbl_badge.pack()

        # 2. MAIN CONTAINER
        main_container = tk.Frame(self.root, bg="#0f172a", padx=18, pady=14)
        main_container.pack(fill="both", expand=True)

        # 3. TOP CARD: FILE SELECTION & SETTINGS
        top_card = tk.Frame(main_container, bg="#1e293b", bd=1, relief="solid", padx=16, pady=14)
        top_card.pack(fill="x", pady=(0, 12))

        # Row 1: File selection
        row_file = tk.Frame(top_card, bg="#1e293b")
        row_file.pack(fill="x", pady=(0, 10))

        lbl_file = tk.Label(row_file, text="🎬 Archivo de Video / Audio:", font=("Segoe UI", 10, "bold"), fg="#f8fafc", bg="#1e293b")
        lbl_file.pack(side="left")

        self.lbl_selected_file = tk.Label(
            row_file,
            text="Ningún archivo seleccionado (.mp4, .mov, .mkv, .webm, .mp3, .wav)",
            font=("Segoe UI", 9, "italic"),
            fg="#94a3b8",
            bg="#1e293b",
            padx=10
        )
        self.lbl_selected_file.pack(side="left", fill="x", expand=True)

        btn_browse = tk.Button(
            row_file,
            text="Seleccionar Video",
            font=("Segoe UI", 9, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2",
            command=self._select_video
        )
        btn_browse.pack(side="right")

        # Row 2: Model and Capture Options
        row_opts = tk.Frame(top_card, bg="#1e293b")
        row_opts.pack(fill="x")

        lbl_m = tk.Label(row_opts, text="Motor Whisper Local:", font=("Segoe UI", 9), fg="#94a3b8", bg="#1e293b")
        lbl_m.pack(side="left", padx=(0, 6))

        r_base = tk.Radiobutton(
            row_opts,
            text="Base (Rápido ~30s)",
            variable=self.whisper_model_var,
            value="base",
            bg="#1e293b",
            fg="#e2e8f0",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="#38bdf8",
            font=("Segoe UI", 9)
        )
        r_base.pack(side="left", padx=4)

        r_med = tk.Radiobutton(
            row_opts,
            text="Medium (Alta Precisión)",
            variable=self.whisper_model_var,
            value="medium",
            bg="#1e293b",
            fg="#e2e8f0",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="#38bdf8",
            font=("Segoe UI", 9)
        )
        r_med.pack(side="left", padx=4)

        # Process Button
        self.btn_process = tk.Button(
            row_opts,
            text="⚡ Extraer Capturas y Generar Bitácora",
            font=("Segoe UI", 10, "bold"),
            bg="#10b981",
            fg="#ffffff",
            activebackground="#059669",
            relief="flat",
            padx=18,
            pady=6,
            cursor="hand2",
            command=self._start_processing
        )
        self.btn_process.pack(side="right")

        # 4. PROGRESS BAR & STATUS
        prog_frame = tk.Frame(main_container, bg="#0f172a")
        prog_frame.pack(fill="x", pady=(0, 10))

        self.prog_bar = ttk.Progressbar(prog_frame, variable=self.progress_var, maximum=100)
        self.prog_bar.pack(fill="x", pady=(0, 4))

        self.lbl_status = tk.Label(
            prog_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            fg="#38bdf8",
            bg="#0f172a",
            anchor="w"
        )
        self.lbl_status.pack(fill="x")

        # 5. NOTEBOOK TABS FOR PREVIEW
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Tab 1: Keyframe Screenshots Gallery
        self.tab_photos = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.tab_photos, text="📸 Capturas Extraídas")
        self._build_photos_tab()

        # Tab 2: Bitácora & Steps
        self.tab_bitacora = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.tab_bitacora, text="📄 Bitácora & Pasos")
        self._build_bitacora_tab()

        # Tab 3: SIPOC Table
        self.tab_sipoc = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.tab_sipoc, text="📊 Matriz SIPOC Preliminar")
        self._build_sipoc_tab()

        # Tab 4: Raw Transcript
        self.tab_transcript = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.tab_transcript, text="📝 Transcripción con Minutajes")
        self._build_transcript_tab()

        # 6. BOTTOM ACTION BAR
        bottom_bar = tk.Frame(main_container, bg="#1e293b", padx=14, pady=10)
        bottom_bar.pack(fill="x", side="bottom")

        self.btn_open_word = tk.Button(
            bottom_bar,
            text="📄 Abrir Bitácora Word (.docx)",
            font=("Segoe UI", 9, "bold"),
            bg="#1e5a9a",
            fg="#ffffff",
            activebackground="#174478",
            relief="flat",
            padx=12,
            pady=5,
            state="disabled",
            cursor="hand2",
            command=self._open_word_file
        )
        self.btn_open_word.pack(side="left", padx=(0, 8))

        self.btn_open_folder = tk.Button(
            bottom_bar,
            text="📁 Abrir Carpeta de Exportación",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg="#e2e8f0",
            activebackground="#475569",
            relief="flat",
            padx=12,
            pady=5,
            state="disabled",
            cursor="hand2",
            command=self._open_export_folder
        )
        self.btn_open_folder.pack(side="left")

        lbl_temis_tip = tk.Label(
            bottom_bar,
            text="🚀 Arrastra el archivo .temis.json a TEMIS Web para enriquecer con IA",
            font=("Segoe UI", 9, "italic"),
            fg="#10b981",
            bg="#1e293b"
        )
        lbl_temis_tip.pack(side="right")

    def _build_photos_tab(self):
        """Construct canvas gallery for screenshot thumbnails"""
        canvas = tk.Canvas(self.tab_photos, bg="#0f172a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_photos, orient="vertical", command=canvas.yview)
        self.photos_scroll_frame = tk.Frame(canvas, bg="#0f172a")

        self.photos_scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.photos_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.lbl_no_photos = tk.Label(
            self.photos_scroll_frame,
            text="Las capturas de pantalla detectadas por FFmpeg aparecerán aquí.",
            font=("Segoe UI", 10, "italic"),
            fg="#64748b",
            bg="#0f172a",
            padx=20,
            pady=40
        )
        self.lbl_no_photos.pack()

    def _build_bitacora_tab(self):
        """Construct text preview for structured bitácora"""
        self.txt_bitacora = tk.Text(
            self.tab_bitacora,
            bg="#1e293b",
            fg="#f8fafc",
            insertbackground="#38bdf8",
            font=("Consolas", 10),
            padx=12,
            pady=12,
            relief="flat",
            wrap="word"
        )
        sb = ttk.Scrollbar(self.tab_bitacora, orient="vertical", command=self.txt_bitacora.yview)
        self.txt_bitacora.configure(yscrollcommand=sb.set)
        self.txt_bitacora.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _build_sipoc_tab(self):
        """Construct treeview for SIPOC matrix"""
        cols = ("id", "supplier", "input", "process", "output", "customer")
        self.tree_sipoc = ttk.Treeview(self.tab_sipoc, columns=cols, show="headings", height=10)
        
        self.tree_sipoc.heading("id", text="ID")
        self.tree_sipoc.heading("supplier", text="Proveedor (S)")
        self.tree_sipoc.heading("input", text="Entrada (I)")
        self.tree_sipoc.heading("process", text="Proceso (P)")
        self.tree_sipoc.heading("output", text="Salida (O)")
        self.tree_sipoc.heading("customer", text="Cliente (C)")

        self.tree_sipoc.column("id", width=50, anchor="center")
        self.tree_sipoc.column("supplier", width=140)
        self.tree_sipoc.column("input", width=150)
        self.tree_sipoc.column("process", width=220)
        self.tree_sipoc.column("output", width=150)
        self.tree_sipoc.column("customer", width=140)

        sb = ttk.Scrollbar(self.tab_sipoc, orient="vertical", command=self.tree_sipoc.yview)
        self.tree_sipoc.configure(yscrollcommand=sb.set)
        self.tree_sipoc.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _build_transcript_tab(self):
        """Construct transcript viewer"""
        self.txt_transcript = tk.Text(
            self.tab_transcript,
            bg="#1e293b",
            fg="#f8fafc",
            insertbackground="#38bdf8",
            font=("Consolas", 10),
            padx=12,
            pady=12,
            relief="flat",
            wrap="word"
        )
        sb = ttk.Scrollbar(self.tab_transcript, orient="vertical", command=self.txt_transcript.yview)
        self.txt_transcript.configure(yscrollcommand=sb.set)
        self.txt_transcript.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _select_video(self):
        """File dialog to select video or audio file"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar Video o Audio de Proceso",
            filetypes=[
                ("Videos y Audios", "*.mp4 *.mov *.mkv *.webm *.avi *.mp3 *.m4a *.wav"),
                ("Todos los archivos", "*.*")
            ]
        )
        if file_path:
            self.selected_video_path.set(file_path)
            f_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            f_name = os.path.basename(file_path)
            self.lbl_selected_file.config(
                text=f"{f_name}  ({f_size_mb:.1f} MB)",
                fg="#38bdf8"
            )
            self.status_var.set(f"Archivo listo: {f_name}")

    def _start_processing(self):
        """Launch background worker thread"""
        video_path = self.selected_video_path.get()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("Error", "Por favor selecciona un archivo de video o audio válido.")
            return

        if self.is_processing:
            return

        self.is_processing = True
        self.btn_process.config(state="disabled", text="⏳ Procesando en Local...")
        self.progress_var.set(5.0)

        threading.Thread(target=self._run_pipeline, args=(video_path,), daemon=True).start()

    def _run_pipeline(self, video_path: str):
        """Execute 100% local extraction pipeline in background thread"""
        import datetime
        try:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            export_subfolder = os.path.join(EXPORTS_DIR, f"{base_name}_{timestamp_str}")
            os.makedirs(export_subfolder, exist_ok=True)
            self.last_export_dir = export_subfolder

            # 1. Extraer Audio con FFmpeg
            self.status_var.set("Paso 1/4: Extrayendo pista de audio con FFmpeg...")
            self.progress_var.set(15.0)
            audio_path = os.path.join(export_subfolder, "audio.wav")
            MediaExtractor.extract_audio(video_path, audio_path)

            # 2. Extraer Capturas de Pantalla con FFmpeg
            self.status_var.set("Paso 2/4: Detectando cambios de pantalla y extrayendo capturas...")
            self.progress_var.set(40.0)
            capturas_dir = os.path.join(export_subfolder, "capturas")
            keyframes = MediaExtractor.extract_keyframes(
                video_path,
                capturas_dir,
                scene_threshold=0.35,
                max_frames=12
            )
            self.extracted_keyframes = keyframes

            # 3. Transcribir 100% Offline con Faster-Whisper
            self.status_var.set("Paso 3/4: Transcribiendo audio en local con Faster-Whisper (0 Tokens)...")
            self.progress_var.set(65.0)
            model_name = self.whisper_model_var.get()
            whisper_result = WhisperTranscriber.transcribe(
                audio_path,
                model_name=model_name,
                language="es"
            )
            segments = whisper_result.get("segments", [])
            self.transcript_segments = segments

            # 4. Estructurar Proceso y Emparejar Capturas en Local (0 IA)
            self.status_var.set("Paso 4/4: Estructurando bitácora y emparejando fotos por minutaje...")
            self.progress_var.set(85.0)
            analysis_data = LocalProcessBuilder.structure_process(
                transcript_segments=segments,
                keyframes=keyframes,
                video_filename=os.path.basename(video_path)
            )
            self.analysis_data = analysis_data

            # 5. Generar Paquete Word (.docx) y Paquete TEMIS (.temis.json)
            self.status_var.set("Generando documentos oficiales...")
            self.progress_var.set(92.0)

            docx_path = os.path.join(export_subfolder, f"Bitacora_{base_name}.docx")
            json_path = os.path.join(export_subfolder, f"Proyecto_{base_name}.temis.json")
            txt_path = os.path.join(export_subfolder, f"Transcripcion_{base_name}.txt")
            vtt_path = os.path.join(export_subfolder, f"Subtitulos_{base_name}.vtt")

            TemisPackageBuilder.build_word_bitacora(
                analysis_data=analysis_data,
                transcript_segments=segments,
                keyframes=keyframes,
                output_docx_path=docx_path,
                video_filename=os.path.basename(video_path)
            )
            TemisPackageBuilder.build_temis_json_package(
                analysis_data=analysis_data,
                transcript_segments=segments,
                keyframes=keyframes,
                output_json_path=json_path,
                video_filename=os.path.basename(video_path)
            )
            TemisPackageBuilder.export_txt(segments, txt_path, analysis_data.get("project_charter", {}).get("project_name", base_name))
            TemisPackageBuilder.export_vtt(segments, vtt_path)

            self.last_docx_path = docx_path
            self.last_json_path = json_path
            self.progress_var.set(100.0)
            self.status_var.set(f"✅ ¡Proceso 100% local completado! Bitácora Word y paquete TEMIS generados.")

            # Update UI on main thread
            self.root.after(0, self._render_results)

        except Exception as e:
            self.status_var.set(f"❌ Error en el procesamiento: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}"))
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.btn_process.config(state="normal", text="⚡ Extraer Capturas y Generar Bitácora"))

    def _render_results(self):
        """Update preview tabs and activate export buttons"""
        # Enable buttons
        self.btn_open_word.config(state="normal")
        self.btn_open_folder.config(state="normal")

        # 1. Render Photos Gallery
        for widget in self.photos_scroll_frame.winfo_children():
            widget.destroy()

        self.thumb_images.clear()
        if not self.extracted_keyframes:
            tk.Label(self.photos_scroll_frame, text="No se detectaron capturas de pantalla.", fg="#94a3b8", bg="#0f172a").pack(pady=20)
        else:
            # Grid layout for images (3 per row)
            grid_frame = tk.Frame(self.photos_scroll_frame, bg="#0f172a")
            grid_frame.pack(fill="both", expand=True, padx=10, pady=10)

            for idx, kf in enumerate(self.extracted_keyframes):
                col = idx % 3
                row = idx // 3
                
                card = tk.Frame(grid_frame, bg="#1e293b", bd=1, relief="solid", padx=8, pady=8)
                card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

                img_path = kf.get("path")
                if img_path and os.path.exists(img_path):
                    try:
                        pil_img = Image.open(img_path)
                        pil_img.thumbnail((260, 160))
                        tk_img = ImageTk.PhotoImage(pil_img)
                        self.thumb_images.append(tk_img)

                        lbl_img = tk.Label(card, image=tk_img, bg="#1e293b")
                        lbl_img.pack()
                    except Exception:
                        pass

                lbl_cap = tk.Label(
                    card,
                    text=f"Captura #{kf.get('index')}  ⏱️ {kf.get('timestamp_formatted')}",
                    font=("Segoe UI", 9, "bold"),
                    fg="#38bdf8",
                    bg="#1e293b"
                )
                lbl_cap.pack(pady=(4, 0))

        # 2. Render Bitácora Text
        self.txt_bitacora.delete("1.0", tk.END)
        charter = self.analysis_data.get("project_charter", {})
        self.txt_bitacora.insert(tk.END, f"PROYECTO: {charter.get('project_name', '')}\n")
        self.txt_bitacora.insert(tk.END, f"PROPÓSITO: {charter.get('purpose', '')}\n")
        self.txt_bitacora.insert(tk.END, f"ALCANCE: {charter.get('scope', '')}\n")
        self.txt_bitacora.insert(tk.END, f"{'='*60}\n\n")

        for step in self.analysis_data.get("process_steps", []):
            self.txt_bitacora.insert(tk.END, f"PASO {step.get('step_number')}: {step.get('title')} [{step.get('timestamp')}]\n")
            self.txt_bitacora.insert(tk.END, f"  Actor: {step.get('actor')} | Sistema: {step.get('system')}\n")
            self.txt_bitacora.insert(tk.END, f"  Descripción: {step.get('description')}\n")
            if step.get('attached_screenshot'):
                self.txt_bitacora.insert(tk.END, f"  📸 Captura Vinculada: {step.get('attached_screenshot')} ({step.get('screenshot_caption')})\n")
            self.txt_bitacora.insert(tk.END, "\n")

        # 3. Render SIPOC Tree
        for item in self.tree_sipoc.get_children():
            self.tree_sipoc.delete(item)

        for row in self.analysis_data.get("sipoc", []):
            self.tree_sipoc.insert("", tk.END, values=(
                row.get("id", ""),
                row.get("supplier", ""),
                row.get("input", ""),
                row.get("process", ""),
                row.get("output", ""),
                row.get("customer", "")
            ))

        # 4. Render Transcript
        self.txt_transcript.delete("1.0", tk.END)
        for seg in self.transcript_segments:
            self.txt_transcript.insert(tk.END, f"[{seg.get('timestamp_start')}] {seg.get('speaker', 'Participante')}:\n")
            self.txt_transcript.insert(tk.END, f"  {seg.get('text')}\n\n")

        messagebox.showinfo(
            "✅ Éxito",
            f"Levantamiento 100% Local Completado.\n\n"
            f"📄 Bitácora Word con fotos: {os.path.basename(self.last_docx_path)}\n"
            f"📦 Paquete TEMIS: {os.path.basename(self.last_json_path)}\n\n"
            f"Arrastra el archivo .temis.json a TEMIS Web para sincronizar."
        )

    def _open_word_file(self):
        """Open generated Word document in default application"""
        if self.last_docx_path and os.path.exists(self.last_docx_path):
            os.startfile(self.last_docx_path)

    def _open_export_folder(self):
        """Open export directory in Windows Explorer"""
        if self.last_export_dir and os.path.exists(self.last_export_dir):
            os.startfile(self.last_export_dir)
