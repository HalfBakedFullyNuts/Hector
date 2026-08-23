/**
 * Main App Component
 * Sets up routing and authentication context
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { PublicLayout } from './components/layout/PublicLayout';
import { LandingPage } from './pages/public/LandingPage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';
import { DonorDashboard } from './pages/donor/DonorDashboard';
import { DogProfileForm } from './pages/donor/DogProfileForm';
import { BrowseRequestsPage } from './pages/donor/BrowseRequestsPage';
import { RespondToRequestPage } from './pages/donor/RespondToRequestPage';
import { MyResponsesPage } from './pages/donor/MyResponsesPage';
import { ClinicDashboard } from './pages/clinic/ClinicDashboard';
import { CreateRequestForm } from './pages/clinic/CreateRequestForm';
import { ClinicRequestDetailPage } from './pages/clinic/ClinicRequestDetailPage';
import { AdminUsersPage } from './pages/admin/AdminUsersPage';
import { AdminClinicsPage } from './pages/admin/AdminClinicsPage';
import { AdminStatsDashboard } from './pages/admin/AdminStatsDashboard';
import { UserRole } from './types/auth';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
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
          <Route
            path="/forgot-password"
            element={
              <PublicLayout showHeader={false}>
                <ForgotPasswordPage />
              </PublicLayout>
            }
          />
          <Route
            path="/reset-password"
            element={
              <PublicLayout showHeader={false}>
                <ResetPasswordPage />
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
          <Route
            path="/owner/requests"
            element={
              <ProtectedRoute allowedRoles={[UserRole.DOG_OWNER]}>
                <BrowseRequestsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/owner/requests/:requestId/respond"
            element={
              <ProtectedRoute allowedRoles={[UserRole.DOG_OWNER]}>
                <RespondToRequestPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/owner/responses"
            element={
              <ProtectedRoute allowedRoles={[UserRole.DOG_OWNER]}>
                <MyResponsesPage />
              </ProtectedRoute>
            }
          />

          {/* Clinic Staff routes */}
          <Route
            path="/clinic"
            element={
              <ProtectedRoute allowedRoles={[UserRole.CLINIC_STAFF]}>
                <ClinicDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/clinic/requests/new"
            element={
              <ProtectedRoute allowedRoles={[UserRole.CLINIC_STAFF]}>
                <CreateRequestForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/clinic/requests/:requestId"
            element={
              <ProtectedRoute allowedRoles={[UserRole.CLINIC_STAFF]}>
                <ClinicRequestDetailPage />
              </ProtectedRoute>
            }
          />

          {/* Admin routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
                <AdminStatsDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
                <AdminUsersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/clinics"
            element={
              <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
                <AdminClinicsPage />
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
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
