import { create } from 'zustand';
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:5000/api',
});

// Add token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

const useAuthStore = create((set) => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('token') || null,
    isLoading: false,
    error: null,

    login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
            const response = await api.post('/auth/login', { email, password });
            const { token, ...user } = response.data;

            localStorage.setItem('token', token);
            localStorage.setItem('user', JSON.stringify(user));

            set({ user, token, isLoading: false });
            return true;
        } catch (error) {
            set({
                error: error.response?.data?.message || 'Login failed',
                isLoading: false
            });
            return false;
        }
    },

    register: async (name, email, password) => {
        set({ isLoading: true, error: null });
        try {
            const response = await api.post('/auth/register', { name, email, password });
            const { token, ...user } = response.data;

            localStorage.setItem('token', token);
            localStorage.setItem('user', JSON.stringify(user));

            set({ user, token, isLoading: false });
            return true;
        } catch (error) {
            set({
                error: error.response?.data?.message || 'Registration failed',
                isLoading: false
            });
            return false;
        }
    },

    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        set({ user: null, token: null });
    },
}));

export { useAuthStore, api };
