/**
 * Authentication Service
 * Handles all authentication-related API calls
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  User,
} from '../types/auth';

export const authService = {
  /**
   * Login with email and password
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    // FastAPI OAuth2 expects form data
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const response = await apiClient.post<LoginResponse>(
      API_ENDPOINTS.LOGIN,
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    // Store tokens
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);

    return response.data;
  },

  /**
   * Register new user
   */
  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    const response = await apiClient.post<RegisterResponse>(
      API_ENDPOINTS.REGISTER,
      userData
    );
    return response.data;
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>(API_ENDPOINTS.ME);
    return response.data;
  },

  /**
   * Logout - clear tokens
   */
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  },

  /** T-1008: always-200 request for a reset email */
  async forgotPassword(email: string): Promise<{ message: string; dev_token?: string }> {
    const response = await apiClient.post('/auth/forgot-password', { email });
    return response.data;
  },

  /** T-1008: consume token and set new password */
  async resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
    const response = await apiClient.post('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
    return response.data;
  },

  /** T-1004: store optional owner coordinates */
  async updateMyLocation(latitude: number, longitude: number): Promise<User> {
    const response = await apiClient.patch<User>(API_ENDPOINTS.ME, {
      latitude,
      longitude,
    });
    return response.data;
  },
};

export default authService;
