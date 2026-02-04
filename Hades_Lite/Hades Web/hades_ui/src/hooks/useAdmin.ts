/**
 * Hook para admin usando React Query
 */

import { useQuery } from '@tanstack/react-query';
import { getAdminStats, getAdminJobs } from '../services/jobs';
import type { JobFilters } from '../types/job';

/**
 * Hook para estadísticas de admin
 */
export const useAdminStats = () => {
    return useQuery({
        queryKey: ['admin', 'stats'],
        queryFn: getAdminStats,
    });
};

/**
 * Hook para listar todos los jobs (admin)
 */
export const useAdminJobs = (filters?: JobFilters) => {
    return useQuery({
        queryKey: ['admin', 'jobs', filters],
        queryFn: () => getAdminJobs(filters),
    });
};
