import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import AdminScenarios from './pages/AdminScenarios';
import Simulation from './pages/Simulation';
import Evaluation from './pages/Evaluation';
import { useAuthStore } from './context/AuthContext';

const ProtectedRoute = ({ children }) => {
    const { user } = useAuthStore();
    if (!user) {
        return <Navigate to="/login" replace />;
    }
    return children;
};

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                <Route
                    path="/dashboard"
                    element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/admin/scenarios"
                    element={
                        <ProtectedRoute>
                            <AdminScenarios />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/simulation/:id"
                    element={
                        <ProtectedRoute>
                            <Simulation />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/evaluation"
                    element={
                        <ProtectedRoute>
                            <Evaluation />
                        </ProtectedRoute>
                    }
                />

                <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Routes>
        </Router>
    );
}

export default App;
