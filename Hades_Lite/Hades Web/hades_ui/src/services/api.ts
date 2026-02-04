/**
 * Axios client configurado para la API de Hades
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor para agregar token de autenticación y Gemini API Key
apiClient.interceptors.request.use(
    (config) => {
        // Token de autenticación
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Gemini API Key desde configuración
        const geminiKey = localStorage.getItem('gemini_api_key');
        if (geminiKey) {
            config.headers['X-Gemini-API-Key'] = geminiKey;
        }

        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Interceptor para manejar errores
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token expirado o inválido
            localStorage.removeItem('token');
            window.location.href = '/';
        }
        return Promise.reject(error);
    }
);

export default apiClient;
