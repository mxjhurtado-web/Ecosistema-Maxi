/**
 * API response types
 */

export interface ApiError {
    detail: string;
    status?: number;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    skip: number;
    limit: number;
}

export interface HealthResponse {
    status: string;
    version: string;
    database: string;
    redis: string;
}

export interface StatsResponse {
    total_jobs: number;
    by_status: Record<string, number>;
    by_country: Record<string, number>;
    by_semaforo: Record<string, number>;
    by_user: Record<string, number>;
}
