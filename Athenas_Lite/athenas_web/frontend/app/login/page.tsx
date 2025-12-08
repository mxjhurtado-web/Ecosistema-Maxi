"use client";

export default function LoginPage() {
    const handleGoogleLogin = () => {
        // Redirect to Keycloak with port 8080 callback (like MaxiBot - already configured)
        const keycloakUrl = 'https://sso.maxilabs.net/auth/realms/zeusDev/protocol/openid-connect/auth';
        const params = new URLSearchParams({
            client_id: 'maxi-business-ai',
            response_type: 'code',
            redirect_uri: 'http://localhost:8080/callback',
            scope: 'openid profile email',
            state: 'athenas_auth'
        });
        window.location.href = `${keycloakUrl}?${params.toString()}`;
    };

    return (
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)] px-4">
            <div className="max-w-md w-full">
                <div className="bg-white rounded-2xl shadow-xl p-8 space-y-6">
                    {/* Logo */}
                    <div className="text-center">
                        <div className="mx-auto w-24 h-24 bg-brand/10 rounded-full flex items-center justify-center mb-4">
                            <svg
                                className="w-12 h-12 text-brand"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                            </svg>
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900">ATHENAS Lite</h1>
                        <p className="text-gray-600 mt-2">Quality Analysis Platform</p>
                    </div>

                    {/* Login Button */}
                    <div className="space-y-4">
                        <button
                            onClick={handleGoogleLogin}
                            className="w-full flex items-center justify-center gap-3 bg-white border-2 border-gray-300 rounded-lg px-6 py-3 text-gray-700 font-medium hover:bg-gray-50 hover:border-brand transition-all duration-200 shadow-sm"
                        >
                            <svg className="w-5 h-5" viewBox="0 0 24 24">
                                <path
                                    fill="#4285F4"
                                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                />
                                <path
                                    fill="#34A853"
                                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                />
                                <path
                                    fill="#FBBC05"
                                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                />
                                <path
                                    fill="#EA4335"
                                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                />
                            </svg>
                            Sign in with Google
                        </button>

                        <p className="text-sm text-gray-500 text-center">
                            Secure authentication via Keycloak SSO
                        </p>
                    </div>

                    {/* Info */}
                    <div className="border-t pt-4">
                        <p className="text-xs text-gray-500 text-center">
                            For access, contact your system administrator
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
