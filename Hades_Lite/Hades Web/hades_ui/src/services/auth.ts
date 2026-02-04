/**
 * Servicios de autenticación
 * Modo desarrollo: usa mock auth
 */

import { mockAuth } from './mockAuth';

// Export mock auth functions
export const initAuth = mockAuth.init;
export const login = mockAuth.login;
export const logout = mockAuth.logout;
export const getToken = mockAuth.getToken;
export const isAuthenticated = mockAuth.isAuthenticated;
export const getUser = mockAuth.getUser;
export const hasRole = mockAuth.hasRole;
export const isAdmin = () => mockAuth.hasRole('admin');
export const isAnalyst = () => mockAuth.hasRole('analyst');
