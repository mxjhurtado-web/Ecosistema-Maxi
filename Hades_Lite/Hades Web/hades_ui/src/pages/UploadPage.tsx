/**
 * Página de upload
 */

import { Layout } from '../components/layout/Layout';
import { UploadZone } from '../components/upload/UploadZone';

export const UploadPage = () => {
    return (
        <Layout>
            <div className="max-w-4xl mx-auto">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        Análisis Forense de Documentos
                    </h1>
                    <p className="text-gray-600">
                        Sube una imagen de un documento de identidad para analizarlo
                    </p>
                </div>

                <UploadZone />
            </div>
        </Layout>
    );
};
