/**
 * Forgot Password Page (T-1008)
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Input } from '../../components/common/Input';
import { Button } from '../../components/common/Button';
import { authService } from '../../services/authService';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!email) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await authService.forgotPassword(email);
      setSent(true);
      // Log mode surfaces the token so the flow is testable without SMTP
      if (result.dev_token) setDevToken(result.dev_token);
    } catch (err) {
      console.error(err);
      setError('Something went wrong. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-base-off-white">
      <div className="card w-full max-w-md p-8">
        <h1 className="text-2xl font-bold text-text-dark mb-2">Forgot your password?</h1>
        <p className="text-text-light mb-6">
          Enter your account email and we'll send you a reset link.
        </p>

        {sent ? (
          <div className="space-y-4">
            <div className="p-4 bg-green-50 border border-green-200 rounded-input text-green-700">
              If that email exists, a reset link has been sent. It expires in one hour.
            </div>
            {devToken && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-input text-xs text-yellow-800 break-all">
                Dev mode token (no SMTP configured): <strong>{devToken}</strong>
              </div>
            )}
            <Link to="/login" className="block text-center text-primary-blue font-medium hover:underline">
              ← Back to login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-input text-red-700 text-sm">
                {error}
              </div>
            )}
            <Button type="submit" disabled={submitting} fullWidth>
              {submitting ? 'Sending…' : 'Send Reset Link'}
            </Button>
            <Link
              to="/login"
              className="block text-center text-primary-blue text-sm font-medium hover:underline"
            >
              ← Back to login
            </Link>
          </form>
        )}
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
