/**
 * Reset Password Page (T-1008)
 */

import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Input } from '../../components/common/Input';
import { Button } from '../../components/common/Button';
import { authService } from '../../services/authService';

export const ResetPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [token, setToken] = useState(searchParams.get('token') ?? '');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const passwordValid =
    password.length >= 8 &&
    /[A-Z]/.test(password) &&
    /[a-z]/.test(password) &&
    /\d/.test(password);

  const mismatch = confirm.length > 0 && confirm !== password;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!token || !passwordValid || mismatch) return;
    setSubmitting(true);
    setError(null);
    try {
      await authService.resetPassword(token, password);
      navigate('/login', { state: { resetSuccess: true } });
    } catch (err: unknown) {
      console.error(err);
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Could not reset your password. The link may have expired.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-base-off-white">
      <div className="card w-full max-w-md p-8">
        <h1 className="text-2xl font-bold text-text-dark mb-2">Set a new password</h1>
        <p className="text-text-light mb-6">Paste your reset token and choose a new password.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Reset token"
            placeholder="From your email"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            required
          />
          <Input
            label="New password"
            type="password"
            placeholder="8+ chars, upper & lowercase, digit"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={
              password.length > 0 && !passwordValid
                ? '8+ characters with uppercase, lowercase and a digit'
                : undefined
            }
            required
          />
          <Input
            label="Confirm new password"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            error={mismatch ? 'Passwords do not match' : undefined}
            required
          />

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-input text-red-700 text-sm">
              {error}
            </div>
          )}

          <Button
            type="submit"
            disabled={submitting || !token || !passwordValid || Boolean(mismatch)}
            fullWidth
          >
            {submitting ? 'Updating…' : 'Update Password'}
          </Button>

          <Link
            to="/login"
            className="block text-center text-primary-blue text-sm font-medium hover:underline"
          >
            ← Back to login
          </Link>
        </form>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
