"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import Link from "next/link";

interface Department {
    id: number;
    name: string;
    active: boolean;
}

export default function DepartmentsPage() {
    const [departments, setDepartments] = useState<Department[]>([]);
    const [loading, setLoading] = useState(true);
    const [newName, setNewName] = useState("");
    const [creating, setCreating] = useState(false);

    const fetchDepartments = async () => {
        try {
            const data = await apiClient.getDepartments(false);
            setDepartments(data);
        } catch (err) {
            console.error("Error loading departments:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDepartments();
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newName.trim()) return;

        setCreating(true);
        try {
            await apiClient.createDepartment(newName);
            setNewName("");
            fetchDepartments();
        } catch (err: any) {
            alert(err.message || "Error al crear departamento");
        } finally {
            setCreating(false);
        }
    };

    const handleToggleActive = async (dept: Department) => {
        try {
            await apiClient.updateDepartment(dept.id, dept.name, !dept.active);
            fetchDepartments();
        } catch (err: any) {
            alert(err.message || "Error al actualizar departamento");
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm("¿Estás seguro de eliminar este departamento?")) return;
        try {
            await apiClient.deleteDepartment(id);
            fetchDepartments();
        } catch (err: any) {
            alert(err.message || "Error al eliminar departamento");
        }
    };

    if (loading) return <div className="p-8 text-center">Cargando departamentos...</div>;

    return (
        <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white p-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <Link
                            href="/admin"
                            className="text-gray-500 hover:text-brand flex items-center gap-2 mb-2"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                            Volver al Panel
                        </Link>
                        <h1 className="text-2xl font-bold text-gray-900">Gestión de Departamentos</h1>
                        <p className="text-gray-600">Crea y gestiona los departamentos disponibles</p>
                    </div>
                </div>

                {/* Create Form */}
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <form onSubmit={handleCreate} className="flex gap-4">
                        <input
                            type="text"
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            placeholder="Nombre del nuevo departamento"
                            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent"
                        />
                        <button
                            type="submit"
                            disabled={creating || !newName.trim()}
                            className="px-6 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark transition-colors disabled:opacity-50"
                        >
                            {creating ? "Creando..." : "Crear Departamento"}
                        </button>
                    </form>
                </div>

                {/* List */}
                <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                    <div className="divide-y divide-gray-100">
                        {departments.map((dept) => (
                            <div key={dept.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                                <div className="flex items-center gap-3">
                                    <div className={`w-3 h-3 rounded-full ${dept.active ? 'bg-green-500' : 'bg-gray-300'}`} />
                                    <span className="font-medium text-gray-900">{dept.name}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => handleToggleActive(dept)}
                                        className={`px-3 py-1 rounded-full text-xs font-medium ${dept.active
                                                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                            }`}
                                    >
                                        {dept.active ? 'Activo' : 'Inactivo'}
                                    </button>
                                    <button
                                        onClick={() => handleDelete(dept.id)}
                                        className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                                        title="Eliminar"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        ))}
                        {departments.length === 0 && (
                            <div className="p-8 text-center text-gray-500">
                                No hay departamentos creados
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
