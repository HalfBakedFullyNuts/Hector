/**
 * Login Page
 * User authentication page
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { UserRole } from '../../types/auth';

// Validation schema
const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, user } = useAuth();
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  // Redirect if already logged in
  React.useEffect(() => {
    if (user) {
      // Redirect based on role
      switch (user.role) {
        case UserRole.ADMIN:
          navigate('/admin');
          break;
        case UserRole.CLINIC_STAFF:
          navigate('/clinic');
          break;
        case UserRole.DOG_OWNER:
          navigate('/owner');
          break;
        default:
          navigate('/');
      }
    }
  }, [user, navigate]);

  const onSubmit = async (data: LoginFormData) => {
    try {
      setApiError(null);
      await login(data);
      // Navigation happens in useEffect above
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message);
      } else {
        setApiError('Login failed. Please check your credentials and try again.');
      }
    }
  };

  return (
    <div className="min-h-screen bg-base-off-white flex items-center justify-center p-4">
      <div className="card max-w-md w-full">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-text-dark mb-2">
            Welcome to Hector
          </h1>
          <p className="text-text-light">
            Sign in to access your dashboard
          </p>
        </div>

        {apiError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-input text-red-700 text-sm">
            {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Email"
            type="email"
            placeholder="your.email@example.com"
            error={errors.email?.message}
            {...register('email')}
          />

          <Input
            label="Password"
            type="password"
            placeholder="Enter your password"
            error={errors.password?.message}
            {...register('password')}
          />

          <div className="text-right">
            <a
              href="#"
              className="text-sm text-primary-blue hover:text-primary-blue-dark"
            >
              Forgot password?
            </a>
          </div>

          <Button type="submit" fullWidth disabled={isSubmitting}>
            {isSubmitting ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        <div className="mt-6 text-center space-y-2">
          <p className="text-text-light">
            Don't have an account?{' '}
            <Link
              to="/register"
              className="text-primary-blue hover:text-primary-blue-dark font-medium"
            >
              Register here
            </Link>
          </p>
          <p>
            <Link
              to="/"
              className="text-sm text-text-placeholder hover:text-text-light"
            >
              &larr; Back to home
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
