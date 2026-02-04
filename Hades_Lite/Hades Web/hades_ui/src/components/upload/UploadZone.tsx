/**
 * Componente de upload con drag & drop
 */

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '../common/Button';
import { useCreateJob } from '../../hooks/useJobs';
import { useNavigate } from 'react-router-dom';

export const UploadZone = () => {
    const [file, setFile] = useState<File | null>(null);
    const [preview, setPreview] = useState<string | null>(null);
    const createJobMutation = useCreateJob();
    const navigate = useNavigate();

    const onDrop = useCallback((acceptedFiles: File[]) => {
        const selectedFile = acceptedFiles[0];
        if (selectedFile) {
            setFile(selectedFile);
            setPreview(URL.createObjectURL(selectedFile));
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
        maxSize: 10 * 1024 * 1024, // 10MB
        multiple: false,
    });

    const handleUpload = async () => {
        if (!file) return;

        try {
            const job = await createJobMutation.mutateAsync({
                file,
                autoExport: true,
            });

            // Redirigir a la página de resultado
            navigate(`/results/${job.id}`);
        } catch (error) {
            console.error('Error uploading:', error);
            alert('Error al subir el archivo. Por favor intenta de nuevo.');
        }
    };

    const handleRemove = () => {
        setFile(null);
        setPreview(null);
    };

    return (
        <div className="max-w-2xl mx-auto">
            {!preview ? (
                <div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${isDragActive
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-gray-300 hover:border-primary-400'
                        }`}
                >
                    <input {...getInputProps()} />

                    <svg
                        className="mx-auto h-16 w-16 text-gray-400 mb-4"
                        stroke="currentColor"
                        fill="none"
                        viewBox="0 0 48 48"
                    >
                        <path
                            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                            strokeWidth={2}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    </svg>

                    <p className="text-lg font-medium text-gray-900 mb-2">
                        {isDragActive ? 'Suelta la imagen aquí' : 'Arrastra una imagen o haz clic para seleccionar'}
                    </p>
                    <p className="text-sm text-gray-500">
                        PNG, JPG, WEBP hasta 10MB
                    </p>
                </div>
            ) : (
                <div className="space-y-4">
                    <div className="relative rounded-lg overflow-hidden border border-gray-200">
                        <img
                            src={preview}
                            alt="Preview"
                            className="w-full h-auto max-h-96 object-contain bg-gray-50"
                        />
                    </div>

                    <div className="flex gap-3">
                        <Button
                            variant="primary"
                            onClick={handleUpload}
                            isLoading={createJobMutation.isPending}
                            className="flex-1"
                        >
                            Analizar Documento
                        </Button>
                        <Button
                            variant="secondary"
                            onClick={handleRemove}
                            disabled={createJobMutation.isPending}
                        >
                            Cambiar
                        </Button>
                    </div>

                    <p className="text-sm text-gray-500 text-center">
                        {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </p>
                </div>
            )}
        </div>
    );
};
