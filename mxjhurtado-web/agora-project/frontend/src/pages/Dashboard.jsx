import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../layout/DashboardLayout';
import { api } from '../context/AuthContext';
import { Play, TrendingUp, Clock, CheckCircle } from 'lucide-react';

const Dashboard = () => {
    const [scenarios, setScenarios] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchScenarios = async () => {
            try {
                const res = await api.get('/scenarios');
                setScenarios(res.data);
            } catch (error) {
                console.error("Error fetching scenarios", error);
            } finally {
                setLoading(false);
            }
        };
        fetchScenarios();
    }, []);

    const startSimulation = (scenarioId) => {
        navigate(`/simulation/${scenarioId}`);
    };

    return (
        <DashboardLayout>
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-800">Panel de Entrenamiento</h1>
                <p className="text-gray-600">Bienvenido de nuevo. Selecciona un escenario para practicar.</p>
            </div>

            {/* Stats Cards (Mock Data) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
                    <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
                        <CheckCircle size={24} />
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Simulaciones Completadas</p>
                        <p className="text-2xl font-bold text-gray-800">12</p>
                    </div>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
                    <div className="p-3 bg-green-100 text-green-600 rounded-lg">
                        <TrendingUp size={24} />
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Puntaje Promedio</p>
                        <p className="text-2xl font-bold text-gray-800">85%</p>
                    </div>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
                    <div className="p-3 bg-purple-100 text-purple-600 rounded-lg">
                        <Clock size={24} />
                    </div>
                    <div>
                        <p className="text-sm text-gray-500">Tiempo de Práctica</p>
                        <p className="text-2xl font-bold text-gray-800">3.5 hrs</p>
                    </div>
                </div>
            </div>

            <h2 className="text-xl font-bold text-gray-800 mb-4">Escenarios Disponibles</h2>

            {loading ? (
                <p>Cargando escenarios...</p>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {scenarios.map((scenario) => (
                        <div key={scenario._id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
                            <div className="p-6">
                                <div className="flex justify-between items-start mb-4">
                                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${scenario.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
                                            scenario.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                                'bg-red-100 text-red-800'
                                        }`}>
                                        {scenario.difficulty.toUpperCase()}
                                    </span>
                                    <span className="text-xs text-gray-500">{scenario.customerType}</span>
                                </div>
                                <h3 className="text-lg font-bold text-gray-800 mb-2">{scenario.title}</h3>
                                <p className="text-gray-600 text-sm mb-4 line-clamp-2">{scenario.description}</p>

                                <button
                                    onClick={() => startSimulation(scenario._id)}
                                    className="w-full bg-primary text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center space-x-2 hover:bg-blue-700 transition-colors"
                                >
                                    <Play size={18} />
                                    <span>Iniciar Práctica</span>
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </DashboardLayout>
    );
};

export default Dashboard;
