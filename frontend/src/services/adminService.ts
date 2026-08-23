/**
 * Admin Service — privileged platform management API calls
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import type {
  AuditLogEntry,
  PlatformStatistics,
  ToggleUserActiveRequest,
  UserWithCounts,
} from '../types/admin';
import type { Clinic } from '../types/clinic';

const AUDIT_LOG = '/admin/audit-log';

export const adminService = {
  /** T-700: filter by role/active/verified, email search, pagination */
  async getUsers(params?: {
    role?: string;
    is_active?: boolean;
    is_verified?: boolean;
    email?: string;
    limit?: number;
    offset?: number;
  }): Promise<UserWithCounts[]> {
    const response = await apiClient.get<UserWithCounts[]>(
      API_ENDPOINTS.ADMIN_USERS,
      { params }
    );
    return response.data;
  },

  /** T-701 */
  async toggleUserActive(
    userId: string,
    data: ToggleUserActiveRequest = {}
  ): Promise<UserWithCounts> {
    const response = await apiClient.post<UserWithCounts>(
      `${API_ENDPOINTS.ADMIN_USERS}/${userId}/toggle-active`,
      data
    );
    return response.data;
  },

  /** T-702 */
  async deleteUser(
    userId: string,
    reason?: string
  ): Promise<void> {
    await apiClient.delete(`${API_ENDPOINTS.ADMIN_USERS}/${userId}`, {
      data: { user_id: userId, reason: reason ?? null },
    });
  },

  /** T-704 */
  async approveClinic(clinicId: string, notes?: string): Promise<Clinic> {
    const response = await apiClient.post<Clinic>(
      `${API_ENDPOINTS.ADMIN_CLINICS}/${clinicId}/approve`,
      { approval_notes: notes ?? null }
    );
    return response.data;
  },

  /** T-704 */
  async rejectClinic(clinicId: string, reason: string): Promise<void> {
    await apiClient.post(
      `${API_ENDPOINTS.ADMIN_CLINICS}/${clinicId}/reject`,
      { rejection_reason: reason }
    );
  },

  /** T-703: date range optional (ISO strings) */
  async getStats(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<PlatformStatistics> {
    const response = await apiClient.get<PlatformStatistics>(
      API_ENDPOINTS.ADMIN_STATS,
      { params }
    );
    return response.data;
  },

  async getAuditLog(limit = 50, offset = 0): Promise<AuditLogEntry[]> {
    const response = await apiClient.get<AuditLogEntry[]>(AUDIT_LOG, {
      params: { limit, offset },
    });
    return response.data;
  },

  /** Convenience: pending clinics via admin-scoped listing (admins see all) */
  async listAllClinics(): Promise<Clinic[]> {
    const response = await apiClient.get<Clinic[]>(API_ENDPOINTS.CLINICS);
    return response.data;
  },
};

export default adminService;
