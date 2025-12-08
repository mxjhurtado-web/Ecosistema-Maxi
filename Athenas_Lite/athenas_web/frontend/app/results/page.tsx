"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

interface Analysis {
    id: number;
    filename: string;
    department: string;
    evaluator: string;
    advisor: string;
    score_final: number;
    created_at: string;
}

export default function ResultsPage() {
    const [analyses, setAnalyses] = useState<Analysis[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState("");

    useEffect(() => {
        loadAnalyses();
    }, []);

    const loadAnalyses = async () => {
        try {
            const data = await apiClient.getAnalyses();
            setAnalyses(data);
        } catch (error) {
            console.error("Error loading analyses:", error);
        } finally {
            setLoading(false);
        }
    };

    const filteredAnalyses = analyses.filter(
        (a) =>
            a.filename.toLowerCase().includes(filter.toLowerCase()) ||
            a.department.toLowerCase().includes(filter.toLowerCase()) ||
            a.advisor.toLowerCase().includes(filter.toLowerCase())
    );

    const getScoreColor = (score: number) => {
        if (score >= 85) return "text-green-600 bg-green-50";
        if (score >= 70) return "text-yellow-600 bg-yellow-50";
        return "text-red-600 bg-red-50";
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white">
            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">
                                Historial de Análisis
                            </h1>
                            <p className="text-gray-600 mt-1">
                                Todos los análisis realizados
                            </p>
                        </div>
                        <div className="flex items-center gap-4">
                            <input
                                type="text"
                                placeholder="Buscar..."
                                value={filter}
                                onChange={(e) => setFilter(e.target.value)}
                                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent"
                            />
                        </div>
                    </div>
                </div>

                {/* Results Table */}
                <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                    {loading ? (
                        <div className="p-12 text-center">
                            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-brand border-t-transparent"></div>
                            <p className="mt-4 text-gray-600">Cargando análisis...</p>
                        </div>
                    ) : filteredAnalyses.length === 0 ? (
                        <div className="p-12 text-center">
                            <svg
                                className="mx-auto h-16 w-16 text-gray-400 mb-4"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                />
                            </svg>
                            <p className="text-gray-600 font-medium">
                                No hay análisis todavía
                            </p>
                            <p className="text-sm text-gray-500 mt-1">
                                Los análisis aparecerán aquí una vez que subas archivos
                            </p>
                            <a
                                href="/dashboard"
                                className="inline-block mt-4 px-6 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark transition-colors"
                            >
                                Ir al Dashboard
                            </a>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50 border-b border-gray-200">
                                    <tr>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Archivo
                                        </th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Departamento
                                        </th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Asesor
                                        </th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Score
                                        </th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Fecha
                                        </th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Acciones
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {filteredAnalyses.map((analysis) => (
                                        <tr
                                            key={analysis.id}
                                            className="hover:bg-pink-50 transition-colors"
                                        >
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center">
                                                    <svg
                                                        className="w-5 h-5 text-brand mr-2"
                                                        fill="none"
                                                        stroke="currentColor"
                                                        viewBox="0 0 24 24"
                                                    >
                                                        <path
                                                            strokeLinecap="round"
                                                            strokeLinejoin="round"
                                                            strokeWidth={2}
                                                            d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                                                        />
                                                    </svg>
                                                    <span className="text-sm font-medium text-gray-900">
                                                        {analysis.filename}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="text-sm text-gray-600">
                                                    {analysis.department}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="text-sm text-gray-600">
                                                    {analysis.advisor}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span
                                                    className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(
                                                        analysis.score_final
                                                    )}`}
                                                >
                                                    {analysis.score_final}%
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                                {new Date(
                                                    analysis.created_at
                                                ).toLocaleDateString("es-MX")}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex flex-col gap-2">
                                                    <a
                                                        href={`/results/${analysis.id}`}
                                                        className="text-brand hover:text-brand-dark font-medium text-sm"
                                                    >
                                                        Ver detalles →
                                                    </a>
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => window.open(apiClient.getDownloadUrl(analysis.id, "csv"), "_blank")}
                                                            className="text-xs text-brand hover:underline"
                                                            title="Descargar CSV local"
                                                        >
                                                            CSV
                                                        </button>
                                                        <span className="text-gray-300">|</span>
                                                        <button
                                                            onClick={() => window.open(apiClient.getDownloadUrl(analysis.id, "txt"), "_blank")}
                                                            className="text-xs text-brand hover:underline"
                                                            title="Descargar Resumen TXT"
                                                        >
                                                            TXT
                                                        </button>
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* Stats */}
                {!loading && filteredAnalyses.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <p className="text-sm text-gray-600 mb-1">
                                Total Análisis
                            </p>
                            <p className="text-3xl font-bold text-brand">
                                {filteredAnalyses.length}
                            </p>
                        </div>
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <p className="text-sm text-gray-600 mb-1">
                                Score Promedio
                            </p>
                            <p className="text-3xl font-bold text-brand">
                                {(
                                    filteredAnalyses.reduce(
                                        (acc, a) => acc + a.score_final,
                                        0
                                    ) / filteredAnalyses.length
                                ).toFixed(1)}
                                %
                            </p>
                        </div>
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <p className="text-sm text-gray-600 mb-1">
                                Departamentos
                            </p>
                            <p className="text-3xl font-bold text-brand">
                                {
                                    new Set(filteredAnalyses.map((a) => a.department))
                                        .size
                                }
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
