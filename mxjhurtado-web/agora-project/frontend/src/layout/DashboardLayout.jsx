import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../context/AuthContext';
import { LayoutDashboard, PhoneCall, Settings, LogOut, Users } from 'lucide-react';

const DashboardLayout = ({ children }) => {
    const { user, logout } = useAuthStore();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const isActive = (path) => location.pathname === path;

    return (
        <div className="flex h-screen bg-gray-100">
            {/* Sidebar */}
            <aside className="w-64 bg-white shadow-md flex flex-col">
                <div className="p-6 border-b">
                    <h1 className="text-2xl font-bold text-primary">AGORA</h1>
                    <p className="text-xs text-gray-500">Entrenamiento Inteligente</p>
                </div>

                <nav className="flex-1 p-4 space-y-2">
                    <Link
                        to="/dashboard"
                        className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${isActive('/dashboard') ? 'bg-blue-50 text-primary' : 'text-gray-600 hover:bg-gray-50'
                            }`}
                    >
                        <LayoutDashboard size={20} />
                        <span>Dashboard</span>
                    </Link>

                    {user?.role === 'admin' && (
                        <Link
                            to="/admin/scenarios"
                            className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${isActive('/admin/scenarios') ? 'bg-blue-50 text-primary' : 'text-gray-600 hover:bg-gray-50'
                                }`}
                        >
                            <Settings size={20} />
                            <span>Gestionar Escenarios</span>
                        </Link>
                    )}

                    {user?.role === 'admin' && (
                        <Link
                            to="/admin/users"
                            className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${isActive('/admin/users') ? 'bg-blue-50 text-primary' : 'text-gray-600 hover:bg-gray-50'
                                }`}
                        >
                            <Users size={20} />
                            <span>Usuarios</span>
                        </Link>
                    )}

                </nav>

                <div className="p-4 border-t">
                    <div className="flex items-center space-x-3 px-4 py-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold">
                            {user?.name?.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">{user?.name}</p>
                            <p className="text-xs text-gray-500 truncate">{user?.role}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="flex items-center space-x-3 px-4 py-2 w-full text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                        <LogOut size={20} />
                        <span>Cerrar Sesión</span>
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-8">
                {children}
            </main>
        </div>
    );
};

export default DashboardLayout;
