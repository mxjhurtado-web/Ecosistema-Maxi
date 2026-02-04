/**
 * Página de historial
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { useJobs } from '../hooks/useJobs';
import { Spinner } from '../components/common/Spinner';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { SemaforoLevel } from '../types/job';

export const HistoryPage = () => {
    const [filters, setFilters] = useState<{
        country?: string;
        semaforo?: SemaforoLevel;
    }>({});

    const { data: jobs, isLoading } = useJobs(filters);

    return (
        <Layout>
            <div className="max-w-6xl mx-auto">
                <h1 className="text-2xl font-bold text-gray-900 mb-6">Historial de Análisis</h1>

                {/* Filters */}
                <Card className="mb-6">
                    <div className="flex gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                País
                            </label>
                            <select
                                className="border border-gray-300 rounded-lg px-3 py-2"
                                value={filters.country || ''}
                                onChange={(e) => setFilters({ ...filters, country: e.target.value || undefined })}
                            >
                                <option value="">Todos</option>
                                <option value="MX">México</option>
                                <option value="US">Estados Unidos</option>
                                <option value="CO">Colombia</option>
                                {/* Add more countries */}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Semáforo
                            </label>
                            <select
                                className="border border-gray-300 rounded-lg px-3 py-2"
                                value={filters.semaforo || ''}
                                onChange={(e) => setFilters({ ...filters, semaforo: e.target.value as SemaforoLevel || undefined })}
                            >
                                <option value="">Todos</option>
                                <option value="verde">Verde</option>
                                <option value="amarillo">Amarillo</option>
                                <option value="rojo">Rojo</option>
                            </select>
                        </div>
                    </div>
                </Card>

                {/* Jobs List */}
                {isLoading ? (
                    <div className="flex justify-center py-12">
                        <Spinner size="lg" />
                    </div>
                ) : jobs && jobs.length > 0 ? (
                    <div className="space-y-4">
                        {jobs.map((job) => (
                            <Link key={job.id} to={`/results/${job.id}`}>
                                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                                    <div className="flex items-center justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-2">
                                                <Badge
                                                    color={
                                                        job.status === 'completed' ? 'green' :
                                                            job.status === 'processing' ? 'yellow' :
                                                                job.status === 'failed' ? 'red' : 'gray'
                                                    }
                                                >
                                                    {job.status}
                                                </Badge>
                                                {job.semaforo && (
                                                    <Badge
                                                        color={
                                                            job.semaforo === 'verde' ? 'green' :
                                                                job.semaforo === 'amarillo' ? 'yellow' : 'red'
                                                        }
                                                    >
                                                        {job.semaforo.toUpperCase()}
                                                    </Badge>
                                                )}
                                                {job.country_detected && (
                                                    <span className="text-sm text-gray-600">{job.country_detected}</span>
                                                )}
                                            </div>
                                            <p className="text-sm text-gray-500">
                                                {new Date(job.created_at).toLocaleString('es-MX')}
                                            </p>
                                        </div>
                                        {job.score !== undefined && (
                                            <div className="text-right">
                                                <div className="text-2xl font-bold text-gray-900">{job.score}</div>
                                                <div className="text-xs text-gray-500">Score</div>
                                            </div>
                                        )}
                                    </div>
                                </Card>
                            </Link>
                        ))}
                    </div>
                ) : (
                    <Card>
                        <div className="text-center py-8">
                            <p className="text-gray-500">No hay análisis en el historial</p>
                        </div>
                    </Card>
                )}
            </div>
        </Layout>
    );
};
