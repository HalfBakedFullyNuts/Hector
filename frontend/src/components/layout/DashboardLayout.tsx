/**
 * Dashboard Layout Component
 * Sidebar navigation (collapses to a top bar with hamburger on mobile, T-1007)
 */

import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { UserRole } from '../../types/auth';

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Only ticketed destinations; dead links removed
  const navItems: NavItem[] = (() => {
    if (user?.role === UserRole.DOG_OWNER) {
      return [
        { path: '/owner', label: 'Dashboard', icon: '📊' },
        { path: '/owner/requests', label: 'Browse Requests', icon: '🔍' },
        { path: '/owner/responses', label: 'My Responses', icon: '📋' },
      ];
    }
    if (user?.role === UserRole.CLINIC_STAFF) {
      return [
        { path: '/clinic', label: 'Dashboard', icon: '📊' },
        { path: '/clinic/requests/new', label: 'New Request', icon: '🩸' },
      ];
    }
    if (user?.role === UserRole.ADMIN) {
      return [
        { path: '/admin', label: 'Statistics', icon: '📊' },
        { path: '/admin/users', label: 'Users', icon: '👥' },
        { path: '/admin/clinics', label: 'Clinics', icon: '🏥' },
      ];
    }
    return [];
  })();

  const roleLabel = user?.role.replace('_', ' ') ?? '';

  const navList = (
    <ul className="space-y-2">
      {navItems.map((item) => {
        const isActive = location.pathname === item.path;
        return (
          <li key={item.path}>
            <Link
              to={item.path}
              onClick={() => setMenuOpen(false)}
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
  );

  return (
    <div className="min-h-screen bg-base-off-white flex flex-col">
      {/* Mobile top bar */}
      <div className="md:hidden bg-white shadow-sm px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold text-primary-blue">Hector</Link>
        <button
          aria-label="Toggle navigation"
          className="p-2 rounded-button text-text-dark hover:bg-base-off-white"
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? '✕' : '☰'}
        </button>
      </div>

      {menuOpen && (
        <div className="md:hidden bg-white shadow-sm px-4 pb-4">
          {navList}
          <button
            onClick={handleLogout}
            className="mt-4 flex items-center gap-3 px-4 py-2.5 rounded-button text-text-dark hover:bg-base-off-white w-full"
          >
            <span className="text-lg">🚪</span>
            <span className="font-medium">Logout</span>
          </button>
        </div>
      )}

      <div className="flex flex-1">
        {/* Desktop sidebar */}
        <aside className="hidden md:flex w-64 bg-white shadow-sm flex-col">
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-2xl font-bold text-primary-blue">Hector</h1>
            <p className="text-sm text-text-light mt-1">Blood Donation</p>
          </div>

          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold bg-primary-blue">
                {user?.email?.[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-dark truncate">
                  {user?.email}
                </p>
                <p className="text-xs text-text-light capitalize">{roleLabel}</p>
              </div>
            </div>
          </div>

          <nav className="flex-1 p-4">{navList}</nav>

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
        <main className="flex-1 overflow-auto min-w-0">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
