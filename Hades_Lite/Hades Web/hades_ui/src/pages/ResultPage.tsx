/**
 * Página de resultado
 */

import { useParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { useJob } from '../hooks/useJobs';
import { Spinner } from '../components/common/Spinner';
import { Card } from '../components/common/Card';
import { SemaforoIndicator } from '../components/results/SemaforoIndicator';
import { CountryBadge } from '../components/results/CountryBadge';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { useExportToDrive } from '../hooks/useJobs';

export const ResultPage = () => {
    const { jobId } = useParams<{ jobId: string }>();
    const { data: job, isLoading } = useJob(jobId, true); // Enable polling
    const exportMutation = useExportToDrive();

    if (isLoading || !job) {
        return (
            <Layout>
                <div className="flex flex-col items-center justify-center py-12">
                    <Spinner size="lg" />
                    <p className="mt-4 text-gray-600">Cargando resultado...</p>
                </div>
            </Layout>
        );
    }

    if (job.status === 'queued' || job.status === 'processing') {
        return (
            <Layout>
                <div className="flex flex-col items-center justify-center py-12">
                    <Spinner size="lg" />
                    <p className="mt-4 text-gray-600">
                        {job.status === 'queued' ? 'En cola...' : 'Analizando documento...'}
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                        Esto puede tomar unos segundos
                    </p>
                </div>
            </Layout>
        );
    }

    if (job.status === 'failed') {
        return (
            <Layout>
                <Card>
                    <div className="text-center py-8">
                        <div className="text-red-500 text-5xl mb-4">⚠️</div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">Análisis Fallido</h2>
                        <p className="text-gray-600">{job.error_message || 'Error desconocido'}</p>
                    </div>
                </Card>
            </Layout>
        );
    }

    const result = job.result!;

    const handleExport = async () => {
        try {
            await exportMutation.mutateAsync(job.id);
            alert('Exportado exitosamente a Google Drive');
        } catch (error) {
            alert('Error al exportar a Drive');
        }
    };

    return (
        <Layout>
            <div className="max-w-5xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-gray-900">Resultado del Análisis</h1>
                    <div className="flex gap-2">
                        {!job.exported_to_drive && (
                            <Button
                                variant="secondary"
                                onClick={handleExport}
                                isLoading={exportMutation.isPending}
                            >
                                Exportar a Drive
                            </Button>
                        )}
                        {job.drive_url && (
                            <a href={job.drive_url} target="_blank" rel="noopener noreferrer">
                                <Button variant="secondary">Ver en Drive</Button>
                            </a>
                        )}
                    </div>
                </div>

                {/* Semáforo y País */}
                <Card>
                    <div className="flex items-center justify-between">
                        <SemaforoIndicator level={result.semaforo} score={result.score} size="lg" />
                        <CountryBadge country={result.country} />
                    </div>
                </Card>

                {/* Datos Extraídos */}
                <Card title="Datos Extraídos">
                    <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <dt className="text-sm font-medium text-gray-500">Nombre</dt>
                            <dd className="mt-1 text-lg font-semibold text-gray-900">
                                {result.extracted_data.name || 'No detectado'}
                            </dd>
                        </div>
                        <div>
                            <dt className="text-sm font-medium text-gray-500">Número de ID</dt>
                            <dd className="mt-1 text-lg font-semibold text-gray-900">
                                {result.extracted_data.id_number || 'No detectado'}
                            </dd>
                        </div>
                        <div className="md:col-span-2">
                            <dt className="text-sm font-medium text-gray-500">Tipo de Documento</dt>
                            <dd className="mt-1 text-lg font-semibold text-gray-900">
                                {result.extracted_data.id_type || 'No detectado'}
                            </dd>
                        </div>
                    </dl>
                </Card>

                {/* Fechas */}
                {Object.keys(result.dates).length > 0 && (
                    <Card title="Fechas">
                        <div className="space-y-3">
                            {Object.entries(result.dates).map(([type, date]) => (
                                <div key={type} className="flex items-center justify-between border-b border-gray-100 pb-2">
                                    <span className="text-sm font-medium text-gray-700 capitalize">{type}:</span>
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-semibold">{date.display}</span>
                                        {date.is_expired && <Badge color="red">Expirado</Badge>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Card>
                )}

                {/* Análisis Forense */}
                <Card title="Análisis Forense">
                    <div className="space-y-4">
                        <div>
                            <span className="text-sm font-medium text-gray-500">Elementos de Seguridad:</span>
                            <p className="mt-1 text-gray-900">{result.forensics.security_elements}</p>
                        </div>
                        <div>
                            <span className="text-sm font-medium text-gray-500">Calidad de Impresión:</span>
                            <p className="mt-1 text-gray-900">{result.forensics.print_quality}</p>
                        </div>
                        <div>
                            <span className="text-sm font-medium text-gray-500">Manipulación Detectada:</span>
                            <Badge color={result.forensics.manipulation_detected ? 'red' : 'green'}>
                                {result.forensics.manipulation_detected ? 'Sí' : 'No'}
                            </Badge>
                        </div>
                        {result.forensics.warnings.length > 0 && (
                            <div>
                                <span className="text-sm font-medium text-gray-500">Advertencias:</span>
                                <ul className="mt-1 list-disc list-inside text-sm text-gray-700">
                                    {result.forensics.warnings.map((warning, i) => (
                                        <li key={i}>{warning}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </Card>

                {/* OCR Text */}
                <Card title="Texto Extraído (OCR)">
                    <div className="space-y-4">
                        {result.was_translated && (
                            <div>
                                <span className="text-xs font-medium text-gray-500 uppercase">Traducido ({result.language_detected} → ES)</span>
                                <pre className="mt-2 text-sm text-gray-900 whitespace-pre-wrap bg-gray-50 p-4 rounded">
                                    {result.ocr_text_translated}
                                </pre>
                            </div>
                        )}
                        <div>
                            <span className="text-xs font-medium text-gray-500 uppercase">Original</span>
                            <pre className="mt-2 text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded">
                                {result.ocr_text}
                            </pre>
                        </div>
                    </div>
                </Card>
            </div>
        </Layout>
    );
};
