/**
 * Clinic Service — clinic profile API calls (real backend)
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import type { Clinic, ClinicCreate, ClinicUpdate } from '../types/clinic';

export const clinicService = {
  /** T-400: creates clinic linked to the current staff user (pending approval) */
  async createClinic(data: ClinicCreate): Promise<Clinic> {
    const response = await apiClient.post<Clinic>(API_ENDPOINTS.CLINICS, data);
    return response.data;
  },

  /** T-401: public */
  async getClinic(clinicId: string): Promise<Clinic> {
    const response = await apiClient.get<Clinic>(
      `${API_ENDPOINTS.CLINICS}/${clinicId}`
    );
    return response.data;
  },

  /** T-403: approved clinics only for non-admins; city filter + pagination */
  async listClinics(params?: {
    city?: string;
    limit?: number;
    offset?: number;
  }): Promise<Clinic[]> {
    const response = await apiClient.get<Clinic[]>(API_ENDPOINTS.CLINICS, {
      params,
    });
    return response.data;
  },

  /** T-402: staff of the clinic or admin */
  async updateClinic(clinicId: string, data: ClinicUpdate): Promise<Clinic> {
    const response = await apiClient.put<Clinic>(
      `${API_ENDPOINTS.CLINICS}/${clinicId}`,
      data
    );
    return response.data;
  },
};

export default clinicService;
