/**
 * Main App Component
 * Sets up routing and authentication context
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ViewAsProvider } from './contexts/ViewAsContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { PublicLayout } from './components/layout/PublicLayout';
import { LandingPage } from './pages/public/LandingPage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DonorDashboard } from './pages/donor/DonorDashboard';
import { DogProfileForm } from './pages/donor/DogProfileForm';
import { UserRole } from './types/auth';

import { DevTools } from './components/dev/DevTools';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ViewAsProvider>
          <DevTools />
          <Routes>
          {/* Public routes */}
          <Route
            path="/"
            element={
              <PublicLayout>
                <LandingPage />
              </PublicLayout>
            }
          />
          <Route
            path="/login"
            element={
              <PublicLayout showHeader={false}>
                <LoginPage />
              </PublicLayout>
            }
          />
          <Route
            path="/register"
            element={
              <PublicLayout showHeader={false}>
                <RegisterPage />
              </PublicLayout>
            }
          />

          {/* Dog Owner routes */}
          <Route
            path="/owner"
            element={
              <ProtectedRoute allowedRoles={[UserRole.DOG_OWNER]}>
                <DonorDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/owner/dogs/new"
            element={
              <ProtectedRoute allowedRoles={[UserRole.DOG_OWNER]}>
                <DogProfileForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/owner/dogs/:dogId"
            element={
              <ProtectedRoute allowedRoles={[UserRole.DOG_OWNER]}>
                <DogProfileForm />
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
                    href="/"
                    className="text-primary-blue hover:text-primary-blue-dark font-medium"
                  >
                    Go to Home
                  </a>
                </div>
              </div>
            }
          />
          </Routes>
        </ViewAsProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
