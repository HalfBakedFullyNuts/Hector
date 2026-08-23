/**
 * Authentication Context
 * Manages user authentication state across the application.
 * Talks to the real backend; tokens live in localStorage (T-900 spec).
 */

import React, { useState, useEffect, type ReactNode } from 'react';
import { UserRole } from '../types/auth';
import type { User, LoginRequest, RegisterRequest } from '../types/auth';
import { authService } from '../services/authService';

import { AuthContext, type AuthContextType } from './authContextObject';

interface AuthProviderProps {
  children: ReactNode;
}

function toUserRole(role: string): UserRole {
  if (Object.values(UserRole).includes(role as UserRole)) {
    return role as UserRole;
  }
  throw new Error(`Unknown role received from server: ${role}`);
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(authService.isAuthenticated());
  const [error, setError] = useState<string | null>(null);

  // Restore session from a persisted token on first mount
  useEffect(() => {
    let cancelled = false;

    const restoreSession = async () => {
      if (!authService.isAuthenticated()) {
        setLoading(false);
        return;
      }
      try {
        const me = await authService.getCurrentUser();
        if (!cancelled) {
          setUser({ ...me, role: toUserRole(me.role as unknown as string) });
        }
      } catch {
        authService.logout();
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void restoreSession();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = async (credentials: LoginRequest) => {
    setError(null);
    await authService.login(credentials);
    const me = await authService.getCurrentUser();
    setUser({ ...me, role: toUserRole(me.role as unknown as string) });
  };

  const register = async (userData: RegisterRequest) => {
    setError(null);
    await authService.register(userData);
    // Auto-login after successful registration
    await login({ email: userData.email, password: userData.password });
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setError(null);
  };

  const clearError = () => {
    setError(null);
  };

  const value: AuthContextType = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
