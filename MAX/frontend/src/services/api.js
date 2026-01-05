/**
 * Axios instance configured for MAX API
 */
import axios from 'axios';
import keycloak from '../lib/keycloak';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
apiClient.interceptors.request.use(
    (config) => {
        if (keycloak.token) {
            config.headers.Authorization = `Bearer ${keycloak.token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Handle token refresh on 401
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            try {
                const refreshed = await keycloak.updateToken(30);
                if (refreshed) {
                    error.config.headers.Authorization = `Bearer ${keycloak.token}`;
                    return apiClient.request(error.config);
                }
            } catch (refreshError) {
                keycloak.login();
            }
        }
        return Promise.reject(error);
    }
);

export default apiClient;
