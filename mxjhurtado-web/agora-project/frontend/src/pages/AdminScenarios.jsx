import React, { useEffect, useState } from 'react';
import DashboardLayout from '../layout/DashboardLayout';
import { api } from '../context/AuthContext';
import { Plus, Trash2, Edit } from 'lucide-react';

const AdminScenarios = () => {
    const [scenarios, setScenarios] = useState([]);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        customerType: 'neutral',
        objective: '',
        baseScript: '',
        difficulty: 'medium'
    });

    const fetchScenarios = async () => {
        try {
            const res = await api.get('/scenarios');
            setScenarios(res.data);
        } catch (error) {
            console.error("Error fetching scenarios", error);
        }
    };

    useEffect(() => {
        fetchScenarios();
    }, []);

    const handleDelete = async (id) => {
        if (window.confirm('¿Estás seguro de eliminar este escenario?')) {
            try {
                await api.delete(`/scenarios/${id}`);
                fetchScenarios();
            } catch (error) {
                console.error("Error deleting scenario", error);
            }
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await api.post('/scenarios', formData);
            setShowForm(false);
            setFormData({
                title: '',
                description: '',
                customerType: 'neutral',
                objective: '',
                baseScript: '',
                difficulty: 'medium'
            });
            fetchScenarios();
        } catch (error) {
            console.error("Error creating scenario", error);
        }
    };

    return (
        <DashboardLayout>
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold text-gray-800">Gestión de Escenarios</h1>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="bg-primary text-white px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-blue-700"
                >
                    <Plus size={20} />
                    <span>Nuevo Escenario</span>
                </button>
            </div>

            {showForm && (
                <div className="bg-white p-6 rounded-xl shadow-md mb-8 border border-gray-200">
                    <h2 className="text-xl font-bold mb-4">Crear Nuevo Escenario</h2>
                    <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="col-span-2">
                            <label className="block text-sm font-medium text-gray-700">Título</label>
                            <input
                                type="text"
                                className="w-full border rounded-lg p-2 mt-1"
                                value={formData.title}
                                onChange={e => setFormData({ ...formData, title: e.target.value })}
                                required
                            />
                        </div>
                        <div className="col-span-2">
                            <label className="block text-sm font-medium text-gray-700">Descripción</label>
                            <textarea
                                className="w-full border rounded-lg p-2 mt-1"
                                value={formData.description}
                                onChange={e => setFormData({ ...formData, description: e.target.value })}
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Tipo de Cliente</label>
                            <select
                                className="w-full border rounded-lg p-2 mt-1"
                                value={formData.customerType}
                                onChange={e => setFormData({ ...formData, customerType: e.target.value })}
                            >
                                <option value="neutral">Neutral</option>
                                <option value="angry">Molesto</option>
                                <option value="confused">Confundido</option>
                                <option value="happy">Feliz</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Dificultad</label>
                            <select
                                className="w-full border rounded-lg p-2 mt-1"
                                value={formData.difficulty}
                                onChange={e => setFormData({ ...formData, difficulty: e.target.value })}
                            >
                                <option value="easy">Fácil</option>
                                <option value="medium">Media</option>
                                <option value="hard">Difícil</option>
                            </select>
                        </div>
                        <div className="col-span-2">
                            <label className="block text-sm font-medium text-gray-700">Objetivo</label>
                            <input
                                type="text"
                                className="w-full border rounded-lg p-2 mt-1"
                                value={formData.objective}
                                onChange={e => setFormData({ ...formData, objective: e.target.value })}
                                required
                            />
                        </div>
                        <div className="col-span-2">
                            <label className="block text-sm font-medium text-gray-700">Script Base / Reglas</label>
                            <textarea
                                className="w-full border rounded-lg p-2 mt-1"
                                rows="4"
                                value={formData.baseScript}
                                onChange={e => setFormData({ ...formData, baseScript: e.target.value })}
                                required
                            />
                        </div>
                        <div className="col-span-2 flex justify-end space-x-2">
                            <button
                                type="button"
                                onClick={() => setShowForm(false)}
                                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                            >
                                Cancelar
                            </button>
                            <button
                                type="submit"
                                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700"
                            >
                                Guardar Escenario
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 border-b">
                        <tr>
                            <th className="p-4 font-medium text-gray-600">Título</th>
                            <th className="p-4 font-medium text-gray-600">Tipo Cliente</th>
                            <th className="p-4 font-medium text-gray-600">Dificultad</th>
                            <th className="p-4 font-medium text-gray-600 text-right">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y">
                        {scenarios.map((scenario) => (
                            <tr key={scenario._id} className="hover:bg-gray-50">
                                <td className="p-4">{scenario.title}</td>
                                <td className="p-4 capitalize">{scenario.customerType}</td>
                                <td className="p-4 capitalize">{scenario.difficulty}</td>
                                <td className="p-4 text-right space-x-2">
                                    <button className="text-blue-600 hover:text-blue-800">
                                        <Edit size={18} />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(scenario._id)}
                                        className="text-red-600 hover:text-red-800"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {scenarios.length === 0 && (
                            <tr>
                                <td colSpan="4" className="p-8 text-center text-gray-500">
                                    No hay escenarios creados aún.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </DashboardLayout>
    );
};

export default AdminScenarios;
