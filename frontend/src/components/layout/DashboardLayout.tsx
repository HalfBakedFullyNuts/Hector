/**
 * Dashboard Layout Component
 * Reusable layout with sidebar navigation
 * Supports View As functionality for admins
 */

import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useViewAs } from '../../contexts/ViewAsContext';
import { UserRole } from '../../types/auth';
import { ViewAsBanner } from '../admin/ViewAsBanner';
import { ViewAsSelector } from '../admin/ViewAsSelector';

interface NavItem {
  path: string;
  label: string;
  icon: string;
  roles?: UserRole[];
}

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const { effectiveRole, isViewingAs, canUseViewAs } = useViewAs();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Navigation items based on effective role (supports View As)
  const navItems: NavItem[] = React.useMemo(() => {
    if (effectiveRole === UserRole.DOG_OWNER) {
      return [
        { path: '/owner', label: 'Dashboard', icon: '📊' },
        { path: '/owner/dogs', label: 'My Dogs', icon: '🐕' },
        { path: '/owner/requests', label: 'Browse Requests', icon: '🔍' },
        { path: '/owner/responses', label: 'My Responses', icon: '📋' },
        { path: '/owner/settings', label: 'Settings', icon: '⚙️' },
      ];
    } else if (effectiveRole === UserRole.CLINIC_STAFF) {
      return [
        { path: '/clinic', label: 'Dashboard', icon: '📊' },
        { path: '/clinic/requests', label: 'Blood Requests', icon: '🩸' },
        { path: '/clinic/donors', label: 'Find Donors', icon: '🔍' },
        { path: '/clinic/profile', label: 'Clinic Profile', icon: '🏥' },
        { path: '/clinic/settings', label: 'Settings', icon: '⚙️' },
      ];
    } else if (effectiveRole === UserRole.ADMIN) {
      return [
        { path: '/admin', label: 'Dashboard', icon: '📊' },
        { path: '/admin/users', label: 'Users', icon: '👥' },
        { path: '/admin/clinics', label: 'Clinics', icon: '🏥' },
        { path: '/admin/stats', label: 'Statistics', icon: '📈' },
        { path: '/admin/settings', label: 'Settings', icon: '⚙️' },
      ];
    }
    return [];
  }, [effectiveRole]);

  return (
    <div className="min-h-screen bg-base-off-white flex flex-col">
      {/* View As Banner - shown when admin is viewing as another role */}
      <ViewAsBanner />

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-64 bg-white shadow-sm flex flex-col">
          {/* Logo/Brand */}
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-2xl font-bold text-primary-blue">Hector</h1>
            <p className="text-sm text-text-light mt-1">Blood Donation</p>
          </div>

          {/* User Info */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold ${isViewingAs ? 'bg-amber-500' : 'bg-primary-blue'}`}>
                {user?.email?.[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-dark truncate">
                  {user?.email}
                </p>
                <p className="text-xs text-text-light capitalize">
                  {isViewingAs ? (
                    <span className="text-amber-600">
                      Viewing as: {effectiveRole?.replace('_', ' ').toLowerCase()}
                    </span>
                  ) : (
                    effectiveRole?.replace('_', ' ').toLowerCase()
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* View As Selector for Admins */}
          {canUseViewAs && (
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <ViewAsSelector />
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 p-4">
            <ul className="space-y-2">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      className={`flex items-center gap-3 px-4 py-2.5 rounded-button transition-colors ${
                        isActive
                          ? 'bg-primary-blue text-white'
                          : 'text-text-dark hover:bg-base-off-white'
                      }`}
                    >
                      <span className="text-lg">{item.icon}</span>
                      <span className="font-medium">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Logout */}
          <div className="p-4 border-t border-gray-200">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-4 py-2.5 rounded-button text-text-dark hover:bg-base-off-white transition-colors w-full"
            >
              <span className="text-lg">🚪</span>
              <span className="font-medium">Logout</span>
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
