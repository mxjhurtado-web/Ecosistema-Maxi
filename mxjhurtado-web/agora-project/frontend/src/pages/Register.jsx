import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../context/AuthContext';
import { Lock, Mail, User } from 'lucide-react';

const Register = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const { register, isLoading, error } = useAuthStore();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        const success = await register(name, email, password);
        if (success) {
            navigate('/dashboard');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
            <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
                <h2 className="text-2xl font-bold text-center text-primary mb-6">Crear Cuenta AGORA</h2>

                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-gray-700 text-sm font-bold mb-2">Nombre Completo</label>
                        <div className="relative">
                            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500">
                                <User size={20} />
                            </span>
                            <input
                                type="text"
                                className="w-full pl-10 pr-3 py-2 border rounded-lg focus:outline-none focus:border-primary"
                                placeholder="Juan Pérez"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-gray-700 text-sm font-bold mb-2">Email</label>
                        <div className="relative">
                            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500">
                                <Mail size={20} />
                            </span>
                            <input
                                type="email"
                                className="w-full pl-10 pr-3 py-2 border rounded-lg focus:outline-none focus:border-primary"
                                placeholder="tu@email.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-gray-700 text-sm font-bold mb-2">Contraseña</label>
                        <div className="relative">
                            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500">
                                <Lock size={20} />
                            </span>
                            <input
                                type="password"
                                className="w-full pl-10 pr-3 py-2 border rounded-lg focus:outline-none focus:border-primary"
                                placeholder="********"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-primary text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-300 disabled:opacity-50"
                    >
                        {isLoading ? 'Creando cuenta...' : 'Registrarse'}
                    </button>
                </form>

                <div className="mt-4 text-center">
                    <p className="text-sm text-gray-600">
                        ¿Ya tienes cuenta?{' '}
                        <Link to="/login" className="text-primary hover:underline">
                            Inicia sesión aquí
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Register;
