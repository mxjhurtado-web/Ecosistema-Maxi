/**
 * Mock authentication service for development
 */

export const mockAuth = {
    init: () => {
        console.log('[DEV MODE] Mock authentication initialized');
        return Promise.resolve();
    },

    login: () => {
        console.log('[DEV MODE] Mock login');
        // Simulate user data
        const mockUser = {
            sub: 'dev-user-123',
            email: 'developer@maxilabs.net',
            name: 'Developer User',
            preferred_username: 'developer',
            realm_access: {
                roles: ['analyst', 'admin']
            }
        };

        // Store mock token
        const mockToken = 'dev-mock-token-' + Date.now();
        localStorage.setItem('token', mockToken);
        localStorage.setItem('user', JSON.stringify(mockUser));

        return Promise.resolve();
    },

    logout: () => {
        console.log('[DEV MODE] Mock logout');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    },

    getToken: () => {
        return localStorage.getItem('token') || null;
    },

    isAuthenticated: () => {
        return !!localStorage.getItem('token');
    },

    getUser: () => {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    },

    hasRole: (role: string) => {
        const user = mockAuth.getUser();
        return user?.realm_access?.roles?.includes(role) || false;
    }
};

export const isAdmin = () => mockAuth.hasRole('admin');
export const isAnalyst = () => mockAuth.hasRole('analyst');
