/**
 * Authentication Context
 * Manages user authentication state across the application
 *
 * NOTE: DEV_MODE is enabled - auto-logged in as admin for testing
 */

import React, { createContext, useContext, useState, type ReactNode } from 'react';
import { UserRole } from '../types/auth';
import type { User, LoginRequest, RegisterRequest } from '../types/auth';

// DEV MODE: Set to true to bypass authentication
const DEV_MODE = true;

// Mock admin user for development
export const MOCK_ADMIN_USER: User = {
  id: 'dev-admin-001',
  email: 'admin@hector.dev',
  role: UserRole.ADMIN,
  is_active: true,
  is_verified: true,
  created_at: new Date().toISOString(),
};

// Mock clinic user for development
export const MOCK_CLINIC_USER: User = {
  id: 'dev-clinic-001',
  email: 'clinic@hector.dev',
  role: UserRole.CLINIC_STAFF,
  is_active: true,
  is_verified: true,
  created_at: new Date().toISOString(),
};

// Mock dog owner user for development
export const MOCK_DOG_OWNER_USER: User = {
  id: 'dev-owner-001',
  email: 'owner@hector.dev',
  role: UserRole.DOG_OWNER,
  is_active: true,
  is_verified: true,
  created_at: new Date().toISOString(),
};

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  devLogin: (role: UserRole) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // In DEV_MODE, start with mock admin user
  const [user, setUser] = useState<User | null>(DEV_MODE ? MOCK_DOG_OWNER_USER : null);
  const [loading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (_credentials: LoginRequest) => {
    if (DEV_MODE) {
      setUser(MOCK_DOG_OWNER_USER);
      return;
    }
    // Real login logic would go here
  };

  const register = async (_userData: RegisterRequest) => {
    if (DEV_MODE) {
      setUser(MOCK_DOG_OWNER_USER);
      return;
    }
    // Real register logic would go here
  };

  const logout = () => {
    if (!DEV_MODE) {
      setUser(null);
    }
    setError(null);
  };

  const clearError = () => {
    setError(null);
  };

  const devLogin = (role: UserRole) => {
    switch (role) {
      case UserRole.ADMIN:
        setUser(MOCK_ADMIN_USER);
        break;
      case UserRole.CLINIC_STAFF:
        setUser(MOCK_CLINIC_USER);
        break;
      case UserRole.DOG_OWNER:
        setUser(MOCK_DOG_OWNER_USER);
        break;
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    clearError,
    devLogin,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Custom hook to use auth context
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
