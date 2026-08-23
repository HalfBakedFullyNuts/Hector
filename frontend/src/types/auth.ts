/**
 * Authentication Types — role values match backend StrEnum serialization
 */

export enum UserRole {
  DOG_OWNER = 'dog_owner',
  CLINIC_STAFF = 'clinic_staff',
  ADMIN = 'admin',
}

export type User = {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  latitude?: number | null;
  longitude?: number | null;
  city?: string | null;
  created_at: string;
}

export type LoginRequest = {
  email: string;
  password: string;
}

/** Backend returns tokens only; fetch /auth/me afterwards */
export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type RegisterRequest = {
  email: string;
  password: string;
  role: UserRole;
}

/** Backend register response is the user object itself */
export type RegisterResponse = User & Record<string, unknown>

export type RefreshTokenRequest = {
  refresh_token: string;
}

export type RefreshTokenResponse = {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}
