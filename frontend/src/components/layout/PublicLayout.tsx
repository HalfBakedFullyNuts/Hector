/**
 * Public Layout Component
 * Layout for public pages (landing, login, register) with header
 */

import { Link } from 'react-router-dom';
import type { ReactNode } from 'react';

interface PublicLayoutProps {
  children: ReactNode;
  showHeader?: boolean;
}

export const PublicLayout: React.FC<PublicLayoutProps> = ({
  children,
  showHeader = true,
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-base-white">
      {showHeader && (
        <header className="bg-white border-b border-border px-4 py-4">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            {/* Logo / Brand */}
            <Link to="/" className="flex items-center gap-2">
              {/* Placeholder logo */}
              <div className="w-10 h-10 bg-primary-blue rounded-lg flex items-center justify-center">
                <span className="text-xl font-bold text-text-dark">H</span>
              </div>
              <span className="text-xl font-bold text-text-dark">Hector</span>
            </Link>

            {/* Navigation */}
            <nav className="flex items-center gap-4">
              <Link
                to="/login"
                className="text-text-light hover:text-text-dark transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 bg-primary-blue hover:bg-primary-blue-dark text-text-dark font-medium rounded-button transition-colors"
              >
                Register
              </Link>
            </nav>
          </div>
        </header>
      )}

      <main className="flex-1">{children}</main>
    </div>
  );
};
