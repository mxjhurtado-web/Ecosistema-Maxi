import { Loader2 } from 'lucide-react';

export default function LoadingPage() {
    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
                    <span className="text-white text-2xl font-bold">M</span>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">MAX</h2>
                <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
                <p className="text-gray-600 mt-4">Loading...</p>
            </div>
        </div>
    );
}
