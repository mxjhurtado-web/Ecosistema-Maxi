/**
 * API client for ATHENAS Lite backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export interface UserInfo {
    id: number;
    email: string;
    name: string;
    role: 'admin' | 'user';
    keycloak_id?: string;
    last_login?: string;
    created_at?: string;
}

export interface CallSummary {
    id: number;
    filename: string;
    department: string;
    score_final: number;
    sentiment: string;
    timestamp: string;
}

export interface AnalysisResult {
    id: number;
    filename: string;
    department: string;
    evaluator: string;
    advisor: string;
    timestamp: string;
    score_bruto: number;
    score_final: number;
    sentiment: string;
    drive_txt_link?: string;
    drive_csv_link?: string;
    drive_pdf_link?: string;
}

class APIClient {
    private baseURL: string;

    constructor() {
        this.baseURL = API_BASE_URL;
    }

    private async fetch(endpoint: string, options: RequestInit = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            credentials: 'include', // Include cookies
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return response.json();
    }

    // Auth endpoints
    async getCurrentUser(): Promise<UserInfo> {
        return this.fetch('/api/auth/me');
    }

    async logout(): Promise<void> {
        await this.fetch('/api/auth/logout', { method: 'POST' });
    }

    // Analysis endpoints
    async analyzeAudio(
        file: File,
        department: string,
        evaluator: string,
        advisor: string,
        geminiApiKey?: string
    ): Promise<any> {
        const formData = new FormData();
        formData.append('audio_file', file);
        formData.append('department', department);
        formData.append('evaluator', evaluator);
        formData.append('advisor', advisor);
        if (geminiApiKey) {
            formData.append('gemini_api_key', geminiApiKey);
        }

        const response = await fetch(`${this.baseURL}/api/analysis/analyze`, {
            method: 'POST',
            credentials: 'include',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return response.json();
    }

    async getAnalysisHistory(department?: string, limit = 100): Promise<CallSummary[]> {
        const params = new URLSearchParams();
        if (department) params.append('department', department);
        params.append('limit', limit.toString());

        return this.fetch(`/api/analysis/history?${params.toString()}`);
    }

    async getAnalysis(id: number): Promise<AnalysisResult> {
        return this.fetch(`/api/analysis/${id}`);
    }

    // Admin endpoints
    async getDepartments(activeOnly = false): Promise<any[]> {
        const params = new URLSearchParams();
        if (activeOnly) params.append('active_only', 'true');
        return this.fetch(`/api/admin/departments?${params.toString()}`);
    }

    async createDepartment(name: string, active = true): Promise<any> {
        return this.fetch('/api/admin/departments', {
            method: 'POST',
            body: JSON.stringify({ name, active }),
        });
    }

    async updateDepartment(id: number, name: string, active: boolean): Promise<any> {
        return this.fetch(`/api/admin/departments/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ name, active }),
        });
    }

    async deleteDepartment(id: number): Promise<any> {
        return this.fetch(`/api/admin/departments/${id}`, {
            method: 'DELETE',
        });
    }

    async getRubrics(): Promise<any[]> {
        return this.fetch('/api/admin/rubrics');
    }

    // User management endpoints
    async getUsers(): Promise<UserInfo[]> {
        return this.fetch('/api/users/users');
    }

    async updateUserRole(userId: number, role: string): Promise<any> {
        return this.fetch(`/api/users/users/${userId}/role?new_role=${role}`, {
            method: 'PUT',
        });
    }

    async deleteUser(userId: number): Promise<any> {
        return this.fetch(`/api/users/users/${userId}`, {
            method: 'DELETE',
        });
    }
    async createUser(email: string, name: string, role: string): Promise<any> {
        return this.fetch('/api/users/users', {
            method: 'POST',
            body: JSON.stringify({ email, name, role }),
        });
    }

    async getAdminStats(): Promise<any> {
        return this.fetch('/api/admin/stats');
    }

    getDownloadUrl(analysisId: number, format: 'csv' | 'txt'): string {
        return `${this.baseURL}/api/analysis/${analysisId}/download?format=${format}`;
    }
}

export const apiClient = new APIClient();
