/**
 * Servicio de Jobs - API calls
 */

import apiClient from './api';
import type { Job, JobListItem, JobFilters } from '../types/job';
import type { StatsResponse } from '../types/api';

/**
 * Crear un nuevo job de análisis
 */
export const createJob = async (
    imageFile: File,
    autoExport: boolean = true
): Promise<Job> => {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('auto_export', String(autoExport));

    const response = await apiClient.post<Job>('/jobs', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });

    return response.data;
};

/**
 * Obtener un job por ID
 */
export const getJob = async (jobId: string): Promise<Job> => {
    const response = await apiClient.get<Job>(`/jobs/${jobId}`);
    return response.data;
};

/**
 * Listar jobs del usuario
 */
export const listJobs = async (filters?: JobFilters): Promise<JobListItem[]> => {
    const params = new URLSearchParams();

    if (filters?.country) params.append('country', filters.country);
    if (filters?.semaforo) params.append('semaforo', filters.semaforo);
    if (filters?.skip !== undefined) params.append('skip', String(filters.skip));
    if (filters?.limit !== undefined) params.append('limit', String(filters.limit));

    const response = await apiClient.get<JobListItem[]>('/jobs', { params });
    return response.data;
};

/**
 * Eliminar un job
 */
export const deleteJob = async (jobId: string): Promise<void> => {
    await apiClient.delete(`/jobs/${jobId}`);
};

/**
 * Exportar job a Drive manualmente
 */
export const exportJobToDrive = async (jobId: string): Promise<{
    message: string;
    file_id: string;
    web_link: string;
}> => {
    const response = await apiClient.post(`/export/jobs/${jobId}/drive`);
    return response.data;
};

/**
 * Verificar estado de Drive
 */
export const checkDriveStatus = async (): Promise<{
    status: string;
    folder_id: string;
    message?: string;
    error?: string;
}> => {
    const response = await apiClient.get('/export/drive/status');
    return response.data;
};

/**
 * Obtener estadísticas (admin)
 */
export const getAdminStats = async (): Promise<StatsResponse> => {
    const response = await apiClient.get<StatsResponse>('/admin/stats');
    return response.data;
};

/**
 * Listar todos los jobs (admin)
 */
export const getAdminJobs = async (filters?: JobFilters): Promise<JobListItem[]> => {
    const params = new URLSearchParams();

    if (filters?.country) params.append('country', filters.country);
    if (filters?.semaforo) params.append('semaforo', filters.semaforo);
    if (filters?.skip !== undefined) params.append('skip', String(filters.skip));
    if (filters?.limit !== undefined) params.append('limit', String(filters.limit));

    const response = await apiClient.get<JobListItem[]>('/admin/jobs', { params });
    return response.data;
};
