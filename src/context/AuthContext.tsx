/**
 * Auth Context — Manages login state across the app.
 */
import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import { tokenManager, authService, userService } from '../services/api';

interface User {
    id: number;
    email: string;
    name: string;
    first_name?: string;
    last_name?: string;
    phone?: string;
    age?: string;
    blood_group?: string;
    address?: string;
    emergency_contact?: string;
    parent_link_code?: string;
}

interface AuthState {
    isLoading: boolean;
    isLoggedIn: boolean;
    user: User | null;
    login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
    register: (email: string, password: string, name?: string, family_name?: string) => Promise<{ success: boolean; error?: string }>;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState>({} as AuthState);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [isLoading, setIsLoading] = useState(true);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [user, setUser] = useState<User | null>(null);

    // Check stored token on mount
    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const loggedIn = await tokenManager.isLoggedIn();
            if (loggedIn) {
                const { data } = await userService.getProfile();
                setUser(data);
                setIsLoggedIn(true);
            }
        } catch {
            await tokenManager.clear();
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (email: string, password: string) => {
        const result = await authService.login(email, password);
        if (result.error) return { success: false, error: result.error };
        try {
            const { data } = await userService.getProfile();
            setUser(data);
            setIsLoggedIn(true);
            return { success: true };
        } catch {
            return { success: false, error: 'Failed to load profile' };
        }
    };

    const register = async (email: string, password: string, name?: string, family_name?: string) => {
        const result = await authService.register(email, password, name, family_name);
        if (result.error) return { success: false, error: result.error };
        try {
            const { data } = await userService.getProfile();
            setUser(data);
            setIsLoggedIn(true);
            return { success: true };
        } catch {
            return { success: false, error: 'Failed to load profile' };
        }
    };

    const logout = async () => {
        await authService.logout();
        setUser(null);
        setIsLoggedIn(false);
    };

    const refreshUser = async () => {
        try {
            const { data } = await userService.getProfile();
            setUser(data);
        } catch { }
    };

    return (
        <AuthContext.Provider value={{ isLoading, isLoggedIn, user, login, register, logout, refreshUser }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
export default AuthContext;
