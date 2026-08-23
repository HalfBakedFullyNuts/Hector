/**
 * Auth context object (kept separate so providers stay react-refresh friendly)
 */
import { createContext } from 'react';
import type { User, LoginRequest, RegisterRequest } from '../types/auth';

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
