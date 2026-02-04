/**
 * Página de configuración
 */

import { useState, useEffect } from 'react';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

export const SettingsPage = () => {
    const [geminiKey, setGeminiKey] = useState('');
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        // Cargar API key guardada
        const savedKey = localStorage.getItem('gemini_api_key');
        if (savedKey) {
            setGeminiKey(savedKey);
        }
    }, []);

    const handleSave = () => {
        if (geminiKey.trim()) {
            localStorage.setItem('gemini_api_key', geminiKey.trim());
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        }
    };

    const handleClear = () => {
        setGeminiKey('');
        localStorage.removeItem('gemini_api_key');
    };

    return (
        <Layout>
            <div className="max-w-2xl mx-auto">
                <h1 className="text-2xl font-bold text-gray-900 mb-6">Configuración</h1>

                <Card title="Gemini API Key">
                    <div className="space-y-4">
                        <p className="text-sm text-gray-600">
                            Configura tu API key de Google Gemini para habilitar el análisis de documentos.
                        </p>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                API Key
                            </label>
                            <input
                                type="password"
                                value={geminiKey}
                                onChange={(e) => setGeminiKey(e.target.value)}
                                placeholder="Ingresa tu Gemini API Key"
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                            />
                        </div>

                        {saved && (
                            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                                <p className="text-sm text-green-800">
                                    ✓ API Key guardada exitosamente
                                </p>
                            </div>
                        )}

                        <div className="flex gap-3">
                            <Button variant="primary" onClick={handleSave}>
                                Guardar
                            </Button>
                            <Button variant="secondary" onClick={handleClear}>
                                Limpiar
                            </Button>
                        </div>

                        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <h3 className="text-sm font-semibold text-blue-900 mb-2">
                                ℹ️ Cómo obtener tu API Key
                            </h3>
                            <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                                <li>Ve a <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="underline">Google AI Studio</a></li>
                                <li>Inicia sesión con tu cuenta de Google</li>
                                <li>Haz clic en "Create API Key"</li>
                                <li>Copia la API Key y pégala aquí</li>
                            </ol>
                        </div>
                    </div>
                </Card>
            </div>
        </Layout>
    );
};
