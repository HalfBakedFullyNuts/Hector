/**
 * Main App Component
 * Sets up routing and authentication context
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DonorDashboard } from './pages/donor/DonorDashboard';
import { UserRole } from './types/auth';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Dog Owner routes */}
          <Route
            path="/owner"
            element={
              <ProtectedRoute allowedRoles={[UserRole.DOG_OWNER]}>
                <DonorDashboard />
              </ProtectedRoute>
            }
          />

          {/* Clinic Staff routes */}
          <Route
            path="/clinic"
            element={
              <ProtectedRoute allowedRoles={[UserRole.CLINIC_STAFF]}>
                <div className="min-h-screen bg-base-off-white flex items-center justify-center">
                  <div className="card">
                    <h1 className="text-3xl font-bold text-text-dark mb-4">
                      Clinic Dashboard
                    </h1>
                    <p className="text-text-light">Coming soon...</p>
                  </div>
                </div>
              </ProtectedRoute>
            }
          />

          {/* Admin routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
                <div className="min-h-screen bg-base-off-white flex items-center justify-center">
                  <div className="card">
                    <h1 className="text-3xl font-bold text-text-dark mb-4">
                      Admin Dashboard
                    </h1>
                    <p className="text-text-light">Coming soon...</p>
                  </div>
                </div>
              </ProtectedRoute>
            }
          />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* 404 - Not found */}
          <Route
            path="*"
            element={
              <div className="min-h-screen bg-base-off-white flex items-center justify-center">
                <div className="card text-center">
                  <h1 className="text-3xl font-bold text-text-dark mb-4">
                    404 - Page Not Found
                  </h1>
                  <p className="text-text-light mb-4">
                    The page you're looking for doesn't exist.
                  </p>
                  <a
                    href="/login"
                    className="text-primary-blue hover:text-primary-blue-dark font-medium"
                  >
                    Go to Login
                  </a>
                </div>
              </div>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
