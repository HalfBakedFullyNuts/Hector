/**
 * ProtectedRoute tests: auth gating behavior
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
const mockAuthState = { user: null as null | { role: string }, loading: false };

vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => mockAuthState,
}));

import { ProtectedRoute } from './ProtectedRoute';

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/clinic"
          element={
            <ProtectedRoute allowedRoles={['clinic_staff'] as never}>
              <div>CLINIC CONTENT</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>LOGIN PAGE</div>} />
      </Routes>
    </MemoryRouter>
  );

beforeEach(() => {
  mockAuthState.user = null;
  mockAuthState.loading = false;
});

describe('ProtectedRoute', () => {
  it('redirects unauthenticated visitors to login (T-900)', () => {
    renderAt('/clinic');
    expect(screen.getByText('LOGIN PAGE')).toBeInTheDocument();
  });

  it('renders content for authorized role', () => {
    mockAuthState.user = { role: 'clinic_staff' };
    renderAt('/clinic');
    expect(screen.getByText('CLINIC CONTENT')).toBeInTheDocument();
  });

  it('denies unauthorized roles', () => {
    mockAuthState.user = { role: 'dog_owner' };
    renderAt('/clinic');
    expect(screen.getByText(/access denied/i)).toBeInTheDocument();
  });

  it('shows a spinner while auth is loading', () => {
    mockAuthState.loading = true;
    renderAt('/clinic');
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
