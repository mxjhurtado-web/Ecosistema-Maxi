/**
 * Hook de autenticación
 * Modo desarrollo: usa mock auth sin Keycloak
 */

import { useState, useEffect } from 'react';
import { mockAuth } from '../services/mockAuth';

export const useAuth = () => {
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        const initAuth = async () => {
            try {
                console.log('[DEV MODE] Initializing mock authentication...');
                await mockAuth.init();

                // Check if already authenticated
                if (mockAuth.isAuthenticated()) {
                    setIsAuthenticated(true);
                    setUser(mockAuth.getUser());
                } else {
                    // Auto-login in dev mode
                    await mockAuth.login();
                    setIsAuthenticated(true);
                    setUser(mockAuth.getUser());
                }
            } catch (error) {
                console.error('[DEV MODE] Auth error:', error);
            } finally {
                setIsLoading(false);
            }
        };

        initAuth();
    }, []);

    const logout = () => {
        mockAuth.logout();
        setIsAuthenticated(false);
        setUser(null);
    };

    return {
        isLoading,
        isAuthenticated,
        user,
        logout
    };
};
