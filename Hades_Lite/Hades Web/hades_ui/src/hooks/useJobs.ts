/**
 * Hooks para jobs usando React Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createJob, getJob, listJobs, deleteJob, exportJobToDrive } from '../services/jobs';
import type { JobFilters } from '../types/job';

/**
 * Hook para obtener un job por ID con polling
 */
export const useJob = (jobId: string | undefined, enablePolling: boolean = false) => {
    return useQuery({
        queryKey: ['job', jobId],
        queryFn: () => getJob(jobId!),
        enabled: !!jobId,
        refetchInterval: (query) => {
            if (!enablePolling) return false;

            const data = query.state.data;
            // Polling cada 2s si está en proceso
            if (data && (data.status === 'queued' || data.status === 'processing')) {
                return 2000;
            }
            return false; // Stop polling cuando complete
        },
    });
};

/**
 * Hook para listar jobs
 */
export const useJobs = (filters?: JobFilters) => {
    return useQuery({
        queryKey: ['jobs', filters],
        queryFn: () => listJobs(filters),
    });
};

/**
 * Hook para crear un job
 */
export const useCreateJob = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ file, autoExport }: { file: File; autoExport?: boolean }) =>
            createJob(file, autoExport),
        onSuccess: () => {
            // Invalidar cache de jobs
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
        },
    });
};

/**
 * Hook para eliminar un job
 */
export const useDeleteJob = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: deleteJob,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
        },
    });
};

/**
 * Hook para exportar a Drive
 */
export const useExportToDrive = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: exportJobToDrive,
        onSuccess: (_data, jobId) => {
            // Invalidar el job específico
            queryClient.invalidateQueries({ queryKey: ['job', jobId] });
        },
    });
};
