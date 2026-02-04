/**
 * User types
 */

export interface User {
    sub: string;
    email?: string;
    name?: string;
    preferred_username?: string;
    roles: string[];
}

export interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
}
