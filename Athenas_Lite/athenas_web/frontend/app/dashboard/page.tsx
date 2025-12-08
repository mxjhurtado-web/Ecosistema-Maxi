"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api";

export default function DashboardPage() {
    const [selectedDept, setSelectedDept] = useState("");
    const [evaluator, setEvaluator] = useState("");
    const [advisor, setAdvisor] = useState("");
    const [files, setFiles] = useState<File[]>([]);
    const [uploading, setUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);

    const departments = [
        "Servicio al cliente",
        "Ventas telefónicas",
        "Cobranza",
        "Soporte técnico",
        "Cumplimiento",
    ];

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFiles(Array.from(e.target.files));
        }
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFiles(Array.from(e.dataTransfer.files));
        }
    };

    const handleAnalyze = async () => {
        if (!selectedDept || !evaluator || !advisor || files.length === 0) {
            alert("Por favor completa todos los campos y selecciona al menos un archivo");
            return;
        }

        setUploading(true);

        try {
            // Get API key from localStorage
            const storedApiKey = localStorage.getItem("gemini_api_key");

            // Analyze first file (for now, single file analysis)
            const result = await apiClient.analyzeAudio(
                files[0],
                selectedDept,
                evaluator,
                advisor,
                storedApiKey || undefined
            );

            setUploading(false);
            // Instead of auto-redirect, show success state or prompt
            if (confirm(`Análisis completado! Score: ${result.score_final}%\n\n¿Deseas ir a resultados? (Cancelar para descargar aquí)`)) {
                window.location.href = `/results/${result.id}`;
            } else {
                // Open downloads in new tabs
                window.open(apiClient.getDownloadUrl(result.id, 'csv'), '_blank');
                // window.open(apiClient.getDownloadUrl(result.id, 'txt'), '_blank'); // Optional
            }
        } catch (error: any) {
            setUploading(false);
            alert(`Error: ${error.message}`);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white">
            <div className="max-w-4xl mx-auto px-4 py-8">
                {/* Welcome Header */}
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <h1 className="text-2xl font-bold text-gray-900">
                        Bienvenido, Usuario
                    </h1>
                    <p className="text-gray-600 mt-1">Análisis de Calidad de Llamadas</p>
                </div>

                {/* Analysis Form */}
                <div className="bg-white rounded-xl shadow-lg p-8">
                    <h2 className="text-xl font-bold text-gray-900 mb-6">
                        Detalles del Análisis
                    </h2>

                    <div className="space-y-6">
                        {/* Department Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Departamento
                            </label>
                            <select
                                value={selectedDept}
                                onChange={(e) => setSelectedDept(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent bg-white"
                            >
                                <option value="">Selecciona un departamento</option>
                                {departments.map((dept) => (
                                    <option key={dept} value={dept}>
                                        {dept}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Evaluator and Advisor */}
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Evaluador
                                </label>
                                <input
                                    type="text"
                                    value={evaluator}
                                    onChange={(e) => setEvaluator(e.target.value)}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent"
                                    placeholder="Nombre del evaluador"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Asesor
                                </label>
                                <input
                                    type="text"
                                    value={advisor}
                                    onChange={(e) => setAdvisor(e.target.value)}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent"
                                    placeholder="Nombre del asesor"
                                />
                            </div>
                        </div>

                        {/* File Upload */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Archivos de Audio
                            </label>
                            <div
                                className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${dragActive
                                    ? "border-brand bg-pink-50"
                                    : "border-gray-300 hover:border-brand"
                                    }`}
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                            >
                                <input
                                    type="file"
                                    multiple
                                    accept=".wav,.mp3,.mp4,.m4a,.gsm"
                                    onChange={handleFileChange}
                                    className="hidden"
                                    id="file-upload"
                                />
                                <label
                                    htmlFor="file-upload"
                                    className="cursor-pointer flex flex-col items-center"
                                >
                                    <svg
                                        className="w-16 h-16 text-brand mb-4"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                                        />
                                    </svg>
                                    <p className="text-lg font-medium text-brand mb-2">
                                        Drop audio files here or click to browse
                                    </p>
                                    <p className="text-sm text-gray-500">
                                        Supported formats: WAV, MP3, MP4, M4A, GSM
                                    </p>
                                </label>
                            </div>
                            {files.length > 0 && (
                                <div className="mt-4 space-y-2">
                                    {files.map((file, index) => (
                                        <div
                                            key={index}
                                            className="flex items-center justify-between bg-pink-50 px-4 py-3 rounded-lg border border-brand/20"
                                        >
                                            <span className="text-sm font-medium text-gray-700">
                                                {file.name}
                                            </span>
                                            <span className="text-xs text-gray-500">
                                                {(file.size / 1024 / 1024).toFixed(2)} MB
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Analyze Button */}
                        <button
                            onClick={handleAnalyze}
                            disabled={uploading}
                            className="w-full bg-brand text-white py-4 px-6 rounded-lg font-medium text-lg hover:bg-brand-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                        >
                            {uploading ? "Analizando..." : "Analyze"}
                        </button>
                    </div>
                </div>

                {/* Recent Analyses Preview */}
                <div className="bg-white rounded-xl shadow-lg p-6 mt-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-bold text-gray-900">
                            Recent Analyses Preview
                        </h3>
                        <a
                            href="/results"
                            className="text-brand hover:text-brand-dark font-medium text-sm"
                        >
                            Ver todos →
                        </a>
                    </div>
                    <div className="text-sm text-gray-500">
                        No hay análisis recientes
                    </div>
                </div>
            </div>
        </div>
    );
}
