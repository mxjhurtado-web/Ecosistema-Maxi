"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import Link from "next/link";

interface Rubric {
    filename: string;
    department: string;
}

export default function RubricsPage() {
    const [rubrics, setRubrics] = useState<Rubric[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const fetchRubrics = async () => {
        try {
            const data = await apiClient.getRubrics();
            setRubrics(data);
        } catch (err) {
            console.error("Error loading rubrics:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRubrics();
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            if (file.type !== "application/json" && !file.name.endsWith('.json')) {
                alert("Por favor selecciona un archivo JSON válido");
                return;
            }
            setSelectedFile(file);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedFile) return;

        setUploading(true);
        try {
            // Read file content first since backend expects JSON body currently
            // (ideally should be multipart upload, but adapting to existing api/admin.py)
            const text = await selectedFile.text();
            let jsonContent;
            try {
                jsonContent = JSON.parse(text);
            } catch (err) {
                throw new Error("El archivo no contiene JSON válido");
            }

            const deptName = selectedFile.name.replace('.json', '');

            // We need to use fetch directly or add upload method to apiClient
            // For now, extending usage pattern
            await fetch('/api/admin/rubrics/upload?department=' + encodeURIComponent(deptName), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(jsonContent)
            });

            alert("Rúbrica subida exitosamente");
            setSelectedFile(null);
            fetchRubrics();
        } catch (err: any) {
            alert(err.message || "Error al subir rúbrica");
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (dept: string) => {
        if (!confirm(`¿Estás seguro de eliminar la rúbrica de ${dept}?`)) return;
        try {
            await fetch(`/api/admin/rubrics/${encodeURIComponent(dept)}`, {
                method: 'DELETE'
            });
            fetchRubrics();
        } catch (err: any) {
            alert(err.message || "Error al eliminar rúbrica");
        }
    };

    if (loading) return <div className="p-8 text-center">Cargando rúbricas...</div>;

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
                        <h1 className="text-2xl font-bold text-gray-900">Gestión de Rúbricas</h1>
                        <p className="text-gray-600">Sube y actualiza las rúbricas de evaluación (JSON)</p>
                    </div>
                </div>

                {/* Upload Section */}
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Nueva Rúbrica</h3>
                    <form onSubmit={handleUpload} className="flex gap-4 items-end">
                        <div className="flex-1">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Archivo JSON
                            </label>
                            <input
                                type="file"
                                accept=".json"
                                onChange={handleFileChange}
                                className="block w-full text-sm text-gray-500
                                    file:mr-4 file:py-2 file:px-4
                                    file:rounded-full file:border-0
                                    file:text-sm file:font-semibold
                                    file:bg-pink-50 file:text-brand
                                    hover:file:bg-pink-100"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={uploading || !selectedFile}
                            className="px-6 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark transition-colors disabled:opacity-50"
                        >
                            {uploading ? "Subiendo..." : "Subir Rúbrica"}
                        </button>
                    </form>
                    <p className="text-xs text-gray-500 mt-2">
                        El nombre del archivo determinará el departamento (ej. <code>Ventas.json</code>)
                    </p>
                </div>

                {/* List */}
                <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                    <div className="divide-y divide-gray-100">
                        {rubrics.map((rubric) => (
                            <div key={rubric.filename} className="p-4 flex items-center justify-between hover:bg-gray-50">
                                <div className="flex items-center gap-3">
                                    <div className="bg-gray-100 p-2 rounded text-gray-500 font-mono text-xs">
                                        JSON
                                    </div>
                                    <div>
                                        <span className="font-medium text-gray-900 block">{rubric.department}</span>
                                        <span className="text-xs text-gray-500">{rubric.filename}</span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => handleDelete(rubric.department)}
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
                        {rubrics.length === 0 && (
                            <div className="p-8 text-center text-gray-500">
                                No hay rúbricas cargadas
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
