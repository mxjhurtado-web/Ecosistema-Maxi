"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

export default function AdminPage() {
    const [viewMode, setViewMode] = useState<"admin" | "user">("admin");
    const [stats, setStats] = useState({
        analysis_count: 0,
        active_departments_count: 0,
        users_count: 0,
        rubrics_count: 0
    });

    useEffect(() => {
        if (viewMode === 'admin') {
            loadStats();
        }
    }, [viewMode]);

    const loadStats = async () => {
        try {
            const data = await apiClient.getAdminStats();
            if (data) {
                setStats(data);
            }
        } catch (error) {
            console.error("Error loading stats:", error);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white">
            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Header with Mode Toggle */}
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">
                                Panel de Administración
                            </h1>
                            <p className="text-gray-600 mt-1">
                                Gestión de departamentos, rúbricas y usuarios
                            </p>
                        </div>
                        <button
                            onClick={toggleMode}
                            className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark transition-colors"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            Cambiar a Modo Usuario
                        </button>
                    </div>
                </div>

                {/* Management Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    {/* Departments Card */}
                    <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
                        <div className="flex items-center justify-center w-12 h-12 bg-brand/10 rounded-lg mb-4">
                            <svg className="w-6 h-6 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 mb-2">Departamentos</h3>
                        <p className="text-sm text-gray-600 mb-4">
                            Gestionar departamentos activos
                        </p>
                        <a
                            href="/admin/departments"
                            className="text-brand hover:text-brand-dark font-medium text-sm flex items-center gap-1"
                        >
                            Administrar
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                        </a>
                    </div>

                    {/* Rubrics Card */}
                    <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
                        <div className="flex items-center justify-center w-12 h-12 bg-brand/10 rounded-lg mb-4">
                            <svg className="w-6 h-6 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 mb-2">Rúbricas</h3>
                        <p className="text-sm text-gray-600 mb-4">
                            Editar y gestionar rúbricas JSON
                        </p>
                        <a
                            href="/admin/rubrics"
                            className="text-brand hover:text-brand-dark font-medium text-sm flex items-center gap-1"
                        >
                            Administrar
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                        </a>
                    </div>

                    {/* Users Card */}
                    <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
                        <div className="flex items-center justify-center w-12 h-12 bg-brand/10 rounded-lg mb-4">
                            <svg className="w-6 h-6 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 mb-2">Usuarios</h3>
                        <p className="text-sm text-gray-600 mb-4">
                            Gestionar usuarios y roles
                        </p>
                        <a
                            href="/admin/users"
                            className="text-brand hover:text-brand-dark font-medium text-sm flex items-center gap-1"
                        >
                            Administrar
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                        </a>
                    </div>
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <p className="text-sm text-gray-600 mb-1">Total Análisis</p>
                        <p className="text-3xl font-bold text-brand">{stats.analysis_count}</p>
                    </div>
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <p className="text-sm text-gray-600 mb-1">Departamentos</p>
                        <p className="text-3xl font-bold text-brand">{stats.active_departments_count}</p>
                    </div>
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <p className="text-sm text-gray-600 mb-1">Usuarios</p>
                        <p className="text-3xl font-bold text-brand">{stats.users_count}</p>
                    </div>
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <p className="text-sm text-gray-600 mb-1">Rúbricas</p>
                        <p className="text-3xl font-bold text-brand">{stats.rubrics_count}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
