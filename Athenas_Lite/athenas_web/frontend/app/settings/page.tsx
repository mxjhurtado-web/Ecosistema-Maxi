"use client";

import { useState, useEffect } from "react";
import ApiKeyManager from "./ApiKeyManager";

export default function SettingsPage() {
    const [name, setName] = useState("");
    const [alias, setAlias] = useState("");
    const [apiKey, setApiKey] = useState("");
    const [photo, setPhoto] = useState("");
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        // Load user data from cookie or API
        const userInfoCookie = document.cookie
            .split("; ")
            .find((row) => row.startsWith("user_info="));

        if (userInfoCookie) {
            try {
                const userInfo = JSON.parse(decodeURIComponent(userInfoCookie.split("=")[1]));
                setName(userInfo.name || "");
                setAlias(userInfo.alias || "");
            } catch (e) {
                console.error("Error parsing user info:", e);
            }
        }

        // Load API key from localStorage (more secure than showing it)
        const savedApiKey = localStorage.getItem("gemini_api_key");
        if (savedApiKey) {
            setApiKey(savedApiKey);
        }
    }, []);

    const handleSave = async () => {
        setSaving(true);

        try {
            // Save API key to localStorage
            if (apiKey) {
                localStorage.setItem("gemini_api_key", apiKey);
            } else {
                localStorage.removeItem("gemini_api_key");
            }

            // TODO: Save name, alias, photo to backend
            // await apiClient.updateProfile({ name, alias, photo });

            alert("Configuración guardada exitosamente");
        } catch (error) {
            console.error("Error saving settings:", error);
            alert("Error al guardar la configuración");
        } finally {
            setSaving(false);
        }
    };

    const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setPhoto(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white">
            <div className="max-w-4xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <h1 className="text-2xl font-bold text-gray-900">
                        Configuración de Perfil
                    </h1>
                    <p className="text-gray-600 mt-1">
                        Personaliza tu información y configuración
                    </p>
                </div>

                {/* Settings Form */}
                <div className="bg-white rounded-xl shadow-lg p-8">
                    <div className="space-y-6">
                        {/* Profile Photo */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Foto de Perfil
                            </label>
                            <div className="flex items-center gap-6">
                                <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
                                    {photo ? (
                                        <img
                                            src={photo}
                                            alt="Profile"
                                            className="w-full h-full object-cover"
                                        />
                                    ) : (
                                        <svg
                                            className="w-12 h-12 text-gray-400"
                                            fill="none"
                                            stroke="currentColor"
                                            viewBox="0 0 24 24"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                strokeWidth={2}
                                                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                                            />
                                        </svg>
                                    )}
                                </div>
                                <div>
                                    <input
                                        type="file"
                                        accept="image/*"
                                        onChange={handlePhotoUpload}
                                        className="hidden"
                                        id="photo-upload"
                                    />
                                    <label
                                        htmlFor="photo-upload"
                                        className="cursor-pointer px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors inline-block"
                                    >
                                        Cambiar foto
                                    </label>
                                    <p className="text-xs text-gray-500 mt-2">
                                        JPG, PNG o GIF. Máximo 2MB.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Name */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Nombre Completo
                            </label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent"
                                placeholder="Tu nombre completo"
                            />
                        </div>

                        {/* Alias */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Alias
                            </label>
                            <input
                                type="text"
                                value={alias}
                                onChange={(e) => setAlias(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand focus:border-transparent"
                                placeholder="Tu alias o apodo"
                            />
                        </div>

                        {/* API Key Manager - Rotating Keys */}
                        <div className="border-t pt-6">
                            <ApiKeyManager />
                        </div>

                        {/* Save Button */}
                        <div className="flex gap-4 pt-6">
                            <button
                                onClick={handleSave}
                                disabled={saving}
                                className="flex-1 bg-brand text-white py-3 px-6 rounded-lg font-medium hover:bg-brand-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {saving ? "Guardando..." : "Guardar Cambios"}
                            </button>
                            <a
                                href="/dashboard"
                                className="px-6 py-3 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors text-center"
                            >
                                Cancelar
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
