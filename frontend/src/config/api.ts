/**
 * API Configuration
 * Centralized API base URL and settings
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  // Authentication
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  REFRESH: '/auth/refresh',
  LOGOUT: '/auth/logout',
  ME: '/auth/me',

  // Users
  USERS: '/users',

  // Dogs
  DOGS: '/dogs',

  // Clinics
  CLINICS: '/clinics',

  // Donation Requests
  DONATION_REQUESTS: '/donation-requests',

  // Admin
  ADMIN_USERS: '/admin/users',
  ADMIN_STATS: '/admin/stats',
  ADMIN_CLINICS: '/admin/clinics',
} as const;
