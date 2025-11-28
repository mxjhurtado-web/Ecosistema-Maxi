import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import DashboardLayout from '../layout/DashboardLayout';
import { api } from '../context/AuthContext';
import { CheckCircle, XCircle, AlertTriangle, ArrowRight } from 'lucide-react';

const Evaluation = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [evaluation, setEvaluation] = useState(null);
    const [loading, setLoading] = useState(true);

    // The simulation result passed from the socket event 'simulation_ended'
    // contains { history, duration, scenario }
    const simulationResult = location.state?.result;

    useEffect(() => {
        if (!simulationResult) {
            navigate('/dashboard');
            return;
        }

        const fetchEvaluation = async () => {
            try {
                const res = await api.post('/evaluation', {
                    history: simulationResult.history,
                    scenarioId: simulationResult.scenario._id
                });
                setEvaluation(res.data);
            } catch (error) {
                console.error("Error fetching evaluation", error);
            } finally {
                setLoading(false);
            }
        };

        fetchEvaluation();
    }, [simulationResult, navigate]);

    if (loading) {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                        <p className="text-xl text-gray-600">Analizando tu desempeño...</p>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <div className="max-w-4xl mx-auto">
                <div className="bg-white rounded-xl shadow-lg overflow-hidden mb-8">
                    <div className="bg-primary p-8 text-white text-center">
                        <h1 className="text-3xl font-bold mb-2">Resultados de la Simulación</h1>
                        <p className="opacity-90">{simulationResult?.scenario?.title}</p>

                        <div className="mt-6 inline-block bg-white/20 rounded-full px-6 py-2 backdrop-blur-sm">
                            <span className="text-4xl font-bold">{evaluation?.score}</span>
                            <span className="text-xl opacity-80">/100</span>
                        </div>
                    </div>

                    <div className="p-8">
                        <div className="mb-8">
                            <h2 className="text-xl font-bold text-gray-800 mb-4">Resumen</h2>
                            <p className="text-gray-600 bg-gray-50 p-4 rounded-lg border border-gray-100">
                                {evaluation?.summary}
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                            <div>
                                <h3 className="font-bold text-green-600 mb-3 flex items-center">
                                    <CheckCircle size={20} className="mr-2" /> Fortalezas
                                </h3>
                                <ul className="space-y-2">
                                    {evaluation?.strengths.map((item, i) => (
                                        <li key={i} className="flex items-start text-sm text-gray-700">
                                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full mt-1.5 mr-2"></span>
                                            {item}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            <div>
                                <h3 className="font-bold text-orange-600 mb-3 flex items-center">
                                    <AlertTriangle size={20} className="mr-2" /> Áreas de Mejora
                                </h3>
                                <ul className="space-y-2">
                                    {evaluation?.improvements.map((item, i) => (
                                        <li key={i} className="flex items-start text-sm text-gray-700">
                                            <span className="w-1.5 h-1.5 bg-orange-500 rounded-full mt-1.5 mr-2"></span>
                                            {item}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>

                        <div>
                            <h2 className="text-xl font-bold text-gray-800 mb-4">Detalle por Criterio</h2>
                            <div className="space-y-4">
                                {evaluation?.criteria.map((criterion, index) => (
                                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-100">
                                        <div className="flex items-center space-x-3">
                                            {criterion.passed ? (
                                                <CheckCircle className="text-green-500" size={24} />
                                            ) : (
                                                <XCircle className="text-red-500" size={24} />
                                            )}
                                            <div>
                                                <p className="font-medium text-gray-900">{criterion.name}</p>
                                                <p className="text-sm text-gray-500">{criterion.comment}</p>
                                            </div>
                                        </div>
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${criterion.passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                            }`}>
                                            {criterion.passed ? 'APROBADO' : 'FALLIDO'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="mt-8 flex justify-center space-x-4">
                            <button
                                onClick={() => navigate('/dashboard')}
                                className="px-6 py-3 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors"
                            >
                                Volver al Dashboard
                            </button>
                            <button
                                onClick={() => navigate(`/simulation/${simulationResult.scenario._id}`)}
                                className="px-6 py-3 bg-primary text-white font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                            >
                                <span>Intentar de Nuevo</span>
                                <ArrowRight size={18} className="ml-2" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
};

export default Evaluation;
