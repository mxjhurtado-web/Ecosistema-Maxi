"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { apiClient, AnalysisResult } from "@/lib/api";

export default function AnalysisDetailPage() {
    const router = useRouter();
    const params = useParams();
    const id = params.id as string;

    const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (id) {
            loadAnalysis();
        }
    }, [id]);

    const loadAnalysis = async () => {
        try {
            const data = await apiClient.getAnalysis(parseInt(id));
            setAnalysis(data);
        } catch (error) {
            console.error("Error loading analysis:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
            </div>
        );
    }

    if (!analysis) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <p className="text-gray-500">Análisis no encontrado</p>
                    <button
                        onClick={() => router.push("/results")}
                        className="mt-4 text-brand hover:underline"
                    >
                        Volver al historial
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-5xl mx-auto px-4 py-8">
            <div className="bg-white rounded-xl shadow-lg p-8">
                {/* Header */}
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <button
                            onClick={() => router.push("/results")}
                            className="text-brand hover:underline mb-2 flex items-center gap-2"
                        >
                            ← Volver al historial
                        </button>
                        <h1 className="text-3xl font-bold text-gray-900">
                            Reporte de Análisis
                        </h1>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => window.open(apiClient.getDownloadUrl(parseInt(id), "csv"), "_blank")}
                            className="px-4 py-2 border border-brand text-brand rounded-lg hover:bg-pink-50 transition-colors"
                        >
                            Descargar CSV
                        </button>
                        <button
                            onClick={() => window.open(apiClient.getDownloadUrl(parseInt(id), "txt"), "_blank")}
                            className="px-4 py-2 border border-brand text-brand rounded-lg hover:bg-pink-50 transition-colors"
                        >
                            Descargar TXT
                        </button>
                        <button className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark transition-colors">
                            Exportar PDF
                        </button>
                    </div>
                </div>

                {/* Metadata */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8 p-6 bg-gray-50 rounded-lg">
                    <div>
                        <p className="text-sm text-gray-600">Archivo</p>
                        <p className="font-medium text-gray-900">{analysis.filename}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-600">Departamento</p>
                        <p className="font-medium text-gray-900">{analysis.department}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-600">Evaluador</p>
                        <p className="font-medium text-gray-900">{analysis.evaluator}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-600">Asesor</p>
                        <p className="font-medium text-gray-900">{analysis.advisor}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-600">Fecha</p>
                        <p className="font-medium text-gray-900">
                            {new Date(analysis.timestamp).toLocaleString()}
                        </p>
                    </div>
                </div>

                {/* Scores */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-brand/5 rounded-lg p-6 text-center">
                        <p className="text-sm text-gray-600 mb-2">Score Bruto</p>
                        <p className="text-4xl font-bold text-brand">
                            {analysis.score_bruto.toFixed(1)}%
                        </p>
                    </div>
                    <div className="bg-brand/5 rounded-lg p-6 text-center">
                        <p className="text-sm text-gray-600 mb-2">Score Final</p>
                        <p className="text-4xl font-bold text-brand">
                            {analysis.score_final.toFixed(1)}%
                        </p>
                    </div>
                    <div className="bg-brand/5 rounded-lg p-6 text-center">
                        <p className="text-sm text-gray-600 mb-2">Sentimiento</p>
                        <p className="text-2xl font-bold text-gray-900">
                            {analysis.sentiment}
                        </p>
                    </div>
                </div>

                {/* Drive Links */}
                {(analysis.drive_txt_link ||
                    analysis.drive_csv_link ||
                    analysis.drive_pdf_link) && (
                        <div className="mb-8">
                            <h2 className="text-xl font-bold text-gray-900 mb-4">
                                Archivos en Drive
                            </h2>
                            <div className="flex gap-4">
                                {analysis.drive_txt_link && (
                                    <a
                                        href={analysis.drive_txt_link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="px-4 py-2 border-2 border-brand text-brand rounded-lg hover:bg-brand hover:text-white transition-colors"
                                    >
                                        Ver TXT
                                    </a>
                                )}
                                {analysis.drive_csv_link && (
                                    <a
                                        href={analysis.drive_csv_link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="px-4 py-2 border-2 border-brand text-brand rounded-lg hover:bg-brand hover:text-white transition-colors"
                                    >
                                        Ver CSV
                                    </a>
                                )}
                                {analysis.drive_pdf_link && (
                                    <a
                                        href={analysis.drive_pdf_link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="px-4 py-2 border-2 border-brand text-brand rounded-lg hover:bg-brand hover:text-white transition-colors"
                                    >
                                        Ver PDF
                                    </a>
                                )}
                            </div>
                        </div>
                    )}

                {/* Placeholder for detailed analysis */}
                <div className="border-t pt-8">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">
                        Análisis Detallado
                    </h2>
                    <p className="text-gray-600">
                        El análisis detallado con rúbricas, fortalezas y compromisos se
                        mostrará aquí una vez que se complete la integración con el motor
                        de análisis.
                    </p>
                </div>
            </div>
        </div>
    );
}
