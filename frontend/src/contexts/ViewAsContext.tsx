/**
 * View As Context
 * Allows admins to view the app as different roles without logging out
 */

import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { UserRole } from '../types/auth';
import { useAuth } from './AuthContext';

const VIEW_AS_STORAGE_KEY = 'hector_view_as_role';

interface ViewAsContextType {
  viewingAs: UserRole | null;
  setViewAs: (role: UserRole | null) => void;
  clearViewAs: () => void;
  isViewingAs: boolean;
  effectiveRole: UserRole | null;
  canUseViewAs: boolean;
}

const ViewAsContext = createContext<ViewAsContextType | undefined>(undefined);

interface ViewAsProviderProps {
  children: ReactNode;
}

export const ViewAsProvider: React.FC<ViewAsProviderProps> = ({ children }) => {
  const { user } = useAuth();
  const [viewingAs, setViewingAsState] = useState<UserRole | null>(() => {
    // Load from sessionStorage on init
    const stored = sessionStorage.getItem(VIEW_AS_STORAGE_KEY);
    if (stored && Object.values(UserRole).includes(stored as UserRole)) {
      return stored as UserRole;
    }
    return null;
  });

  // Only admins can use View As
  const canUseViewAs = user?.role === UserRole.ADMIN;

  // Clear viewingAs if user is not admin
  useEffect(() => {
    if (!canUseViewAs && viewingAs) {
      setViewingAsState(null);
      sessionStorage.removeItem(VIEW_AS_STORAGE_KEY);
    }
  }, [canUseViewAs, viewingAs]);

  const setViewAs = (role: UserRole | null) => {
    if (!canUseViewAs) return;

    setViewingAsState(role);
    if (role) {
      sessionStorage.setItem(VIEW_AS_STORAGE_KEY, role);
    } else {
      sessionStorage.removeItem(VIEW_AS_STORAGE_KEY);
    }
  };

  const clearViewAs = () => {
    setViewingAsState(null);
    sessionStorage.removeItem(VIEW_AS_STORAGE_KEY);
  };

  const isViewingAs = viewingAs !== null && canUseViewAs;

  // Effective role: viewingAs if set and user is admin, otherwise actual user role
  const effectiveRole = isViewingAs ? viewingAs : (user?.role ?? null);

  const value: ViewAsContextType = {
    viewingAs,
    setViewAs,
    clearViewAs,
    isViewingAs,
    effectiveRole,
    canUseViewAs,
  };

  return (
    <ViewAsContext.Provider value={value}>
      {children}
    </ViewAsContext.Provider>
  );
};

/**
 * Custom hook to use View As context
 */
export const useViewAs = (): ViewAsContextType => {
  const context = useContext(ViewAsContext);
  if (context === undefined) {
    throw new Error('useViewAs must be used within a ViewAsProvider');
  }
  return context;
};
