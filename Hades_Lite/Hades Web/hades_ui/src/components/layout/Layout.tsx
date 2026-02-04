/**
 * Layout principal de la aplicación
 */

import { ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { isAdmin } from '../../services/auth';

interface LayoutProps {
    children: ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        {/* Logo */}
                        <Link to="/" className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                                <span className="text-white font-bold text-xl">H</span>
                            </div>
                            <span className="text-xl font-bold text-gray-900">Hades</span>
                        </Link>

                        {/* Navigation */}
                        <nav className="flex items-center gap-6">
                            <Link
                                to="/upload"
                                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
                            >
                                Nuevo Análisis
                            </Link>
                            <Link
                                to="/history"
                                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
                            >
                                Historial
                            </Link>
                            {isAdmin() && (
                                <Link
                                    to="/admin"
                                    className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
                                >
                                    Admin
                                </Link>
                            )}
                            <Link
                                to="/settings"
                                className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
                            >
                                ⚙️ Configuración
                            </Link>
                        </nav>

                        {/* User menu */}
                        <div className="flex items-center gap-4">
                            <span className="text-sm text-gray-700">
                                {user?.name || user?.email}
                            </span>
                            <button
                                onClick={handleLogout}
                                className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
                            >
                                Cerrar sesión
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {children}
            </main>
        </div>
    );
};
