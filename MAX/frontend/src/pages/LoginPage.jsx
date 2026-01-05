import keycloak from '../lib/keycloak';
import { LogIn } from 'lucide-react';

export default function LoginPage() {
    const handleLogin = () => {
        keycloak.login();
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
                        <span className="text-white text-2xl font-bold">M</span>
                    </div>
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">MAX</h1>
                    <p className="text-gray-600">Omnichannel Inbox Platform</p>
                </div>

                <button
                    onClick={handleLogin}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
                >
                    <LogIn className="w-5 h-5" />
                    Sign in with SSO
                </button>

                <p className="text-center text-sm text-gray-500 mt-6">
                    Powered by Keycloak
                </p>
            </div>
        </div>
    );
}
