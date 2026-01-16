#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project Management window for TEMIS
Allows owners to manage members and assign roles
"""

import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import os

from desktop.core.api_client import APIClient


# Framework roles
FRAMEWORK_ROLES = [
    "SPONSOR",
    "PROJECT_LEAD",
    "PRODUCT_OWNER",
    "AGILE_LEAD",
    "UX_DESIGNER",
    "DEVELOPER",
    "QA_ENGINEER",
    "PROCESS_OWNER",
    "DATA_QUALITY",
    "STAKEHOLDER"
]


class ProjectManagement:
    """Project Management window"""

    def __init__(self, parent, auth_manager, project):
        self.parent = parent
        self.auth_manager = auth_manager
        self.project = project
        self.api_client = APIClient(
            os.getenv("API_BASE_URL", "http://localhost:8000"),
            auth_manager.access_token
        )
        self.members = []
        self.window = None
        self.is_owner = False
        self.create_window()
        self.load_members()

    def create_window(self):
        """Create management window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"TEMIS - Gestión: {self.project['name']}")
        self.window.geometry("900x600")

        # Colors
        bg_color = "#F9FAFB"
        primary_color = "#1E3A8A"

        self.window.configure(bg=bg_color)

        # Header
        header_frame = tk.Frame(self.window, bg=primary_color, height=70)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text=f"👥 Gestión de Proyecto - {self.project['name']}",
            font=("Arial", 16, "bold"),
            bg=primary_color,
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=20)

        # Main content
        content_frame = tk.Frame(self.window, bg=bg_color)
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Members section
        members_label = tk.Label(
            content_frame,
            text="MIEMBROS DEL PROYECTO:",
            font=("Arial", 12, "bold"),
            bg=bg_color,
            fg="#374151"
        )
        members_label.pack(anchor='w', pady=(0, 10))

        # Members list with scrollbar
        list_frame = tk.Frame(content_frame, bg="white", relief=tk.RAISED, borderwidth=1)
        list_frame.pack(fill='both', expand=True)

        # Create Treeview
        columns = ("Email", "Rol Sistema", "Roles Proyecto")
        self.members_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        self.members_tree.heading("Email", text="Email")
        self.members_tree.heading("Rol Sistema", text="Rol Sistema")
        self.members_tree.heading("Roles Proyecto", text="Roles Proyecto")

        self.members_tree.column("Email", width=250)
        self.members_tree.column("Rol Sistema", width=120)
        self.members_tree.column("Roles Proyecto", width=400)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.members_tree.yview)
        self.members_tree.configure(yscrollcommand=scrollbar.set)

        self.members_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons frame
        buttons_frame = tk.Frame(self.window, bg=bg_color)
        buttons_frame.pack(fill='x', padx=20, pady=10)

        # Add member button
        add_btn = tk.Button(
            buttons_frame,
            text="+ Agregar Miembro",
            font=("Arial", 10, "bold"),
            bg="#10B981",
            fg="white",
            activebackground="#059669",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.add_member,
            padx=15,
            pady=8
        )
        add_btn.pack(side=tk.LEFT, padx=5)

        # Assign role button
        assign_btn = tk.Button(
            buttons_frame,
            text="🎯 Asignar Rol",
            font=("Arial", 10, "bold"),
            bg="#3B82F6",
            fg="white",
            activebackground="#1E3A8A",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.assign_role,
            padx=15,
            pady=8
        )
        assign_btn.pack(side=tk.LEFT, padx=5)

        # Remove member button
        remove_btn = tk.Button(
            buttons_frame,
            text="❌ Remover Miembro",
            font=("Arial", 10, "bold"),
            bg="#EF4444",
            fg="white",
            activebackground="#DC2626",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.remove_member,
            padx=15,
            pady=8
        )
        remove_btn.pack(side=tk.LEFT, padx=5)

        # Refresh button
        refresh_btn = tk.Button(
            buttons_frame,
            text="🔄 Actualizar",
            font=("Arial", 10),
            bg="#E5E7EB",
            fg="#374151",
            activebackground="#D1D5DB",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.load_members,
            padx=15,
            pady=8
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5)

    def load_members(self):
        """Load project members"""
        try:
            user_email = self.auth_manager.user_info.get('email')
            
            # Get members from API
            import requests
            response = requests.get(
                f"{self.api_client.base_url}/api/projects/{self.project['id']}/members",
                headers=self.api_client.headers,
                params={"user_email": user_email}
            )
            
            if response.status_code == 200:
                self.members = response.json()
                self.display_members()
                
                # Check if current user is owner
                for member in self.members:
                    if member['email'] == user_email and member['role'] == 'OWNER':
                        self.is_owner = True
                        break
            else:
                messagebox.showerror("Error", "No se pudieron cargar los miembros")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar miembros:\n\n{str(e)}")

    def display_members(self):
        """Display members in tree"""
        # Clear existing items
        for item in self.members_tree.get_children():
            self.members_tree.delete(item)

        # Add members
        for member in self.members:
            roles_str = ", ".join(member.get('project_roles', [])) if member.get('project_roles') else "Sin asignar"
            
            self.members_tree.insert(
                "",
                "end",
                values=(
                    member['email'],
                    member['role'],
                    roles_str
                ),
                tags=(member['user_id'],)
            )

    def add_member(self):
        """Add new member to project"""
        if not self.is_owner:
            messagebox.showwarning("Acceso Denegado", "Solo los owners pueden agregar miembros")
            return

        email = simpledialog.askstring("Agregar Miembro", "Email del nuevo miembro:")
        if not email:
            return

        try:
            user_email = self.auth_manager.user_info.get('email')
            
            import requests
            response = requests.post(
                f"{self.api_client.base_url}/api/projects/{self.project['id']}/members",
                headers=self.api_client.headers,
                params={"user_email": user_email},
                json={"email": email, "role": "MEMBER"}
            )
            
            if response.status_code == 200:
                messagebox.showinfo("Éxito", f"Miembro {email} agregado correctamente")
                self.load_members()
            else:
                error_msg = response.json().get('detail', 'Error desconocido')
                messagebox.showerror("Error", f"No se pudo agregar el miembro:\n\n{error_msg}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar miembro:\n\n{str(e)}")

    def assign_role(self):
        """Assign framework role to member"""
        if not self.is_owner:
            messagebox.showwarning("Acceso Denegado", "Solo los owners pueden asignar roles")
            return

        # Get selected member
        selection = self.members_tree.selection()
        if not selection:
            messagebox.showwarning("Selección", "Por favor selecciona un miembro")
            return

        item = self.members_tree.item(selection[0])
        user_id = item['tags'][0]
        email = item['values'][0]

        # Create role selection dialog
        role_window = tk.Toplevel(self.window)
        role_window.title("Asignar Rol")
        role_window.geometry("400x500")

        tk.Label(
            role_window,
            text=f"Asignar rol a: {email}",
            font=("Arial", 12, "bold")
        ).pack(pady=10)

        tk.Label(
            role_window,
            text="Selecciona un rol del framework:",
            font=("Arial", 10)
        ).pack(pady=5)

        # Listbox with roles
        listbox = tk.Listbox(role_window, height=10)
        for role in FRAMEWORK_ROLES:
            listbox.insert(tk.END, role.replace("_", " ").title())
        listbox.pack(fill='both', expand=True, padx=20, pady=10)

        def assign():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Selección", "Por favor selecciona un rol")
                return

            role = FRAMEWORK_ROLES[selection[0]]
            
            try:
                user_email = self.auth_manager.user_info.get('email')
                
                import requests
                response = requests.post(
                    f"{self.api_client.base_url}/api/projects/{self.project['id']}/members/assign-role",
                    headers=self.api_client.headers,
                    params={"user_email": user_email},
                    json={"user_id": user_id, "project_role": role}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Éxito", f"Rol {role.replace('_', ' ').title()} asignado correctamente")
                    role_window.destroy()
                    self.load_members()
                else:
                    error_msg = response.json().get('detail', 'Error desconocido')
                    messagebox.showerror("Error", f"No se pudo asignar el rol:\n\n{error_msg}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error al asignar rol:\n\n{str(e)}")

        tk.Button(
            role_window,
            text="Asignar",
            command=assign,
            bg="#3B82F6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=8
        ).pack(pady=10)

    def remove_member(self):
        """Remove member from project"""
        if not self.is_owner:
            messagebox.showwarning("Acceso Denegado", "Solo los owners pueden remover miembros")
            return

        # Get selected member
        selection = self.members_tree.selection()
        if not selection:
            messagebox.showwarning("Selección", "Por favor selecciona un miembro")
            return

        item = self.members_tree.item(selection[0])
        user_id = item['tags'][0]
        email = item['values'][0]

        response = messagebox.askyesno(
            "Confirmar",
            f"¿Estás seguro de remover a {email} del proyecto?"
        )

        if not response:
            return

        try:
            user_email = self.auth_manager.user_info.get('email')
            
            import requests
            response = requests.delete(
                f"{self.api_client.base_url}/api/projects/{self.project['id']}/members/{user_id}",
                headers=self.api_client.headers,
                params={"user_email": user_email}
            )
            
            if response.status_code == 200:
                messagebox.showinfo("Éxito", f"Miembro {email} removido correctamente")
                self.load_members()
            else:
                error_msg = response.json().get('detail', 'Error desconocido')
                messagebox.showerror("Error", f"No se pudo remover el miembro:\n\n{error_msg}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al remover miembro:\n\n{str(e)}")
