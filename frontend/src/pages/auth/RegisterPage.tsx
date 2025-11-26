/**
 * Register Page
 * User registration page
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
const registerSchema = z
  .object({
    email: z.string().email('Please enter a valid email address'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Password must contain at least one number'),
    confirmPassword: z.string(),
    role: z.nativeEnum(UserRole),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register: registerUser, user } = useAuth();
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      role: UserRole.DOG_OWNER,
    },
  });

  // Redirect if already logged in
  React.useEffect(() => {
    if (user) {
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

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setApiError(null);
      await registerUser({
        email: data.email,
        password: data.password,
        role: data.role,
      });
      // Navigation happens in useEffect above after auto-login
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message);
      } else {
        setApiError('Registration failed. Please try again.');
      }
    }
  };

  return (
    <div className="min-h-screen bg-base-off-white flex items-center justify-center p-4">
      <div className="card max-w-md w-full">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-text-dark mb-2">
            Join Hector
          </h1>
          <p className="text-text-light">
            Create an account to get started
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
            placeholder="Create a strong password"
            error={errors.password?.message}
            {...register('password')}
          />

          <Input
            label="Confirm Password"
            type="password"
            placeholder="Re-enter your password"
            error={errors.confirmPassword?.message}
            {...register('confirmPassword')}
          />

          <div className="w-full">
            <label
              htmlFor="role"
              className="block text-sm font-medium text-text-dark mb-1.5"
            >
              I am a...
            </label>
            <select
              id="role"
              className="input"
              {...register('role')}
            >
              <option value={UserRole.DOG_OWNER}>Dog Owner</option>
              <option value={UserRole.CLINIC_STAFF}>Clinic Staff</option>
            </select>
            {errors.role && (
              <p className="mt-1.5 text-sm text-red-600">{errors.role.message}</p>
            )}
          </div>

          <Button type="submit" fullWidth disabled={isSubmitting}>
            {isSubmitting ? 'Creating account...' : 'Create Account'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-text-light">
            Already have an account?{' '}
            <Link
              to="/login"
              className="text-primary-blue hover:text-primary-blue-dark font-medium"
            >
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
