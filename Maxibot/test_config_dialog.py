"""
Test simple para verificar el diálogo de configuración
"""
import tkinter as tk
from tkinter import messagebox

# Simular COLORS y FONT
COLORS = {
    "app_bg": "#f5f7fa",
    "card_bg": "#ffffff",
    "text_primary": "#1a202c",
    "text_secondary": "#718096",
    "accent": "#4299e1"
}

FONT = {
    "body": ("Segoe UI", 10),
    "btn": ("Segoe UI", 10, "bold")
}

def test_dialog():
    app = tk.Tk()
    app.title("Test Dialog")
    app.geometry("400x300")
    
    def show_config():
        dialog = tk.Toplevel(app)
        dialog.title("⚙️ Test Configuración")
        dialog.geometry("650x550")
        dialog.configure(bg=COLORS["app_bg"])
        
        # Header
        header = tk.Frame(dialog, bg=COLORS["card_bg"], height=70)
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(
            header, text="🔑 Test Gestión de API Keys",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["card_bg"], fg=COLORS["text_primary"]
        ).pack(side="left", padx=20, pady=20)
        
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
        
        def _add_key():
            key = key_entry.get().strip()
            if not key:
                messagebox.showwarning("Test", "Ingresa una key")
                return
            messagebox.showinfo("Test", f"Key ingresada: {key[:4]}...")
            key_entry.delete(0, tk.END)
        
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
    
    tk.Button(
        app, text="Abrir Configuración",
        command=show_config,
        bg=COLORS["accent"], fg="#fff",
        relief="flat", bd=0, padx=20, pady=10,
        font=FONT["btn"]
    ).pack(pady=50)
    
    app.mainloop()

if __name__ == "__main__":
    test_dialog()
