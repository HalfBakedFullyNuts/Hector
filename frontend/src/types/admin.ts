/**
 * Admin Types — aligned with backend admin schemas
 */

import type { UserRole } from './auth';

export interface UserWithCounts {
  id: string;
  email: string;
  role: UserRole | string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  dog_count: number;
  clinic_count: number;
}

export interface PlatformStatistics {
  total_users: number;
  users_by_role: Record<string, number>;
  total_dogs: number;
  total_clinics: number;
  approved_clinics: number;
  pending_clinics: number;
  total_requests: number;
  requests_by_status: Record<string, number>;
  total_responses: number;
  responses_by_status: Record<string, number>;
  successful_donations_this_month: number;
}

export interface AuditLogEntry {
  id: string;
  actor_user_id: string | null;
  action: string;
  target_type: string;
  target_id: string;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface ToggleUserActiveRequest {
  reason?: string | null;
}
