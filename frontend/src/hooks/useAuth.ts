/**
 * Auth hook re-exported from a component-free module (react-refresh friendly)
 */
import { useContext } from 'react';
import { AuthContext, type AuthContextType } from '../contexts/authContextObject';

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
