#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Test Wizard - Para diagnosticar el problema
"""

import tkinter as tk
from tkinter import messagebox

def test_wizard():
    """Test simple del wizard"""
    root = tk.Tk()
    root.withdraw()
    
    # Crear ventana
    dialog = tk.Toplevel(root)
    dialog.title("🧙‍♂️ Test Wizard")
    dialog.geometry("400x300")
    dialog.configure(bg="#F9FAFB")
    
    # Forzar que aparezca al frente
    dialog.lift()
    dialog.attributes('-topmost', True)
    dialog.after(100, lambda: dialog.attributes('-topmost', False))
    dialog.focus_force()
    
    # Contenido
    label = tk.Label(
        dialog,
        text="¡Hola! Soy el asistente de TEMIS.\n\n¿Estás listo para empezar?",
        font=("Arial", 12),
        bg="#F9FAFB",
        fg="#1F2937",
        wraplength=350,
        justify='center',
        pady=30
    )
    label.pack(expand=True)
    
    # Botones
    btn_frame = tk.Frame(dialog, bg="#F9FAFB")
    btn_frame.pack(pady=20)
    
    def on_yes():
        messagebox.showinfo("Éxito", "¡Perfecto! El wizard funciona correctamente.")
        dialog.destroy()
        root.quit()
    
    def on_no():
        messagebox.showinfo("Info", "Puedes cerrar esta ventana.")
        dialog.destroy()
        root.quit()
    
    btn_yes = tk.Button(
        btn_frame,
        text="Sí, empecemos",
        command=on_yes,
        bg="#3B82F6",
        fg="white",
        font=("Arial", 10, "bold"),
        padx=20,
        pady=10,
        cursor="hand2"
    )
    btn_yes.pack(side='left', padx=10)
    
    btn_no = tk.Button(
        btn_frame,
        text="Necesito más información",
        command=on_no,
        bg="#6B7280",
        fg="white",
        font=("Arial", 10),
        padx=20,
        pady=10,
        cursor="hand2"
    )
    btn_no.pack(side='left', padx=10)
    
    print("Test wizard window created")
    print(f"Dialog: {dialog}")
    print(f"Dialog winfo_exists: {dialog.winfo_exists()}")
    print(f"Dialog winfo_viewable: {dialog.winfo_viewable()}")
    
    root.mainloop()

if __name__ == "__main__":
    test_wizard()
