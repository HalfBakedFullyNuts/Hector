/**
 * Authentication Types
 */

export enum UserRole {
  DOG_OWNER = 'DOG_OWNER',
  CLINIC_STAFF = 'CLINIC_STAFF',
  ADMIN = 'ADMIN',
}

export type User = {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export type LoginRequest = {
  email: string;
  password: string;
}

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export type RegisterRequest = {
  email: string;
  password: string;
  role: UserRole;
}

export type RegisterResponse = {
  user: User;
  message: string;
}

export type RefreshTokenRequest = {
  refresh_token: string;
}

export type RefreshTokenResponse = {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}
