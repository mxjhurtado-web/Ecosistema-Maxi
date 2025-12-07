
import os
import sys
import pathlib
import datetime
import re
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

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ATHENAS Lite v3.2.1 (Refactored)")
        self.root.geometry("700x620")
        self.root.configure(bg=PALETTE["bg"])
        
        self.fonts = pick_font(self.root)
        
        # State
        self.ruta_audio = []
        self.carpeta_guardado = None
        self.nombre_evaluador = ""
        self.nombre_asesor = ""
        self.selected_department = None
        
        # Init sequence
        self.authenticate_user()
        self.configure_gemini_api()
        self.setup_ui()

    def authenticate_user(self):
        try:
            correo = simpledialog.askstring("Autorización", "Ingresa tu correo corporativo:", parent=self.root)
            if not correo:
                messagebox.showerror("Autorización", "Debes ingresar un correo para continuar.")
                self.root.destroy()
                sys.exit(1)
            
            ok, nombre = verificar_correo_online(correo.strip().lower())
            if not ok:
                messagebox.showerror("Autorización", "Tu correo no está autorizado. Solicita alta en el Sheet.")
                self.root.destroy()
                sys.exit(1)
            
            self.nombre_evaluador = nombre or correo
            logger.info(f"User authenticated: {self.nombre_evaluador}")
        except Exception as e:
            logger.exception("Auth failed")
            messagebox.showerror("Autorización", f"Error validando acceso:\n{e}")
            self.root.destroy()
            sys.exit(1)

    def configure_gemini_api(self):
        try:
            key = GEMINI_API_KEY or simpledialog.askstring("Gemini", "Pega tu API Key de Gemini (opcional):", show="*", parent=self.root)
            if key:
                configurar_gemini(key)
        except Exception:
            pass

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg=PALETTE["bg"])
        header_frame.pack(pady=20)
        
        if Image and ImageTk:
            try:
                logo_path = _resource_path("athenas2.png")
                if os.path.exists(logo_path):
                    logo_img = Image.open(logo_path).resize((40, 55))
                    self.logo_tk = ImageTk.PhotoImage(logo_img)
                    tk.Label(header_frame, image=self.logo_tk, bg=PALETTE["bg"]).pack(side="left", padx=(5,2))
            except Exception:
                pass

        tk.Label(header_frame,
                 text="Athenas Lite: Transforma la Voz en Calidad",
                 font=self.fonts["title"], fg="#0D47A1", bg=PALETTE["bg"]).pack(side="left", padx=5)

        # Loading Zone
        zona_carga = tk.Frame(self.root, bg="#f9d6d5", bd=2, relief="groove")
        zona_carga.pack(pady=20, padx=40, fill="x")
        tk.Label(zona_carga, text="Carga tus audios (hasta 10)", font=self.fonts["body"], fg="#333333", bg="#f9d6d5").pack(pady=10)

        btn_style = {"bg": PALETTE["brand"], "fg": "white", "font": self.fonts["body"], "width": 32}
        
        tk.Button(self.root, text="Seleccionar archivo(s)", command=self.seleccionar_archivo, **btn_style).pack(pady=5)
        tk.Button(self.root, text="Guardar en carpeta...", command=self.seleccionar_carpeta_guardado, **btn_style).pack(pady=5)
        tk.Button(self.root, text="Analizar (Resumen consolidado)", command=self.solicitar_datos_y_analizar, **btn_style).pack(pady=5)

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
