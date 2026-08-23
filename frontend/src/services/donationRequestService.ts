/**
 * Donation Request Service — all request/response API calls (real backend)
 */

import { apiClient } from './apiClient';
import type {
  BloodDonationRequest,
  BloodDonationRequestWithCount,
  ClinicRequest,
  CompatibleRequest,
  DonationRequestCreate,
  DonationRequestUpdate,
  DonationRequestWithDistance,
  DonationResponse,
  DonationResponseCreate,
  RequestStatus,
  ResponseStatus,
} from '../types/donationRequest';

export interface BrowseRequestFilters {
  status?: RequestStatus;
  blood_type?: string;
  urgency?: string;
  city?: string;
  lat?: number;
  lng?: number;
  max_distance_km?: number;
  limit?: number;
  offset?: number;
}

const REQUESTS_BASE = '/requests';

export const donationRequestService = {
  /** T-501/T-1004: public listing with optional filters incl. geo */
  async getRequests(
    params?: BrowseRequestFilters
  ): Promise<DonationRequestWithDistance[]> {
    const response = await apiClient.get<DonationRequestWithDistance[]>(
      REQUESTS_BASE,
      { params }
    );
    return response.data;
  },

  /** T-604: compatible requests for one of my dogs (auth + ownership enforced) */
  async getCompatibleRequests(dogId: string): Promise<CompatibleRequest[]> {
    const response = await apiClient.get<CompatibleRequest[]>(
      `${REQUESTS_BASE}/compatible`,
      { params: { dog_id: dogId, limit: 100 } }
    );
    return response.data;
  },

  /** T-502: includes real response_count */
  async getRequestById(requestId: string): Promise<BloodDonationRequest> {
    const response = await apiClient.get(
      `${REQUESTS_BASE}/${requestId}`
    );
    return response.data as BloodDonationRequest;
  },

  async createRequest(
    data: DonationRequestCreate
  ): Promise<BloodDonationRequest> {
    const response = await apiClient.post<BloodDonationRequest>(
      REQUESTS_BASE,
      data
    );
    return response.data;
  },

  /** T-503: urgency/volume/date/patient_info only; owning staff only */
  async updateRequest(
    requestId: string,
    data: DonationRequestUpdate
  ): Promise<BloodDonationRequest> {
    const response = await apiClient.put<BloodDonationRequest>(
      `${REQUESTS_BASE}/${requestId}`,
      data
    );
    return response.data;
  },

  /** T-504 */
  async cancelRequest(requestId: string): Promise<BloodDonationRequest> {
    const response = await apiClient.post<BloodDonationRequest>(
      `${REQUESTS_BASE}/${requestId}/cancel`
    );
    return response.data;
  },

  async respondToRequest(
    requestId: string,
    data: DonationResponseCreate
  ): Promise<DonationResponse> {
    const response = await apiClient.post<DonationResponse>(
      `${REQUESTS_BASE}/${requestId}/respond`,
      data
    );
    return response.data;
  },

  /** T-601: owning clinic staff only */
  async getRequestResponses(
    requestId: string,
    status?: ResponseStatus
  ): Promise<DonationResponse[]> {
    const response = await apiClient.get<DonationResponse[]>(
      `${REQUESTS_BASE}/${requestId}/responses`,
      { params: status ? { status } : undefined }
    );
    return response.data;
  },

  /** T-602 */
  async getMyResponses(status?: ResponseStatus): Promise<DonationResponse[]> {
    const response = await apiClient.get<DonationResponse[]>(
      `${REQUESTS_BASE}/my-responses`,
      { params: status ? { status } : undefined }
    );
    return response.data;
  },

  /** T-505/T-901: my clinic's requests with response counts */
  async getMyClinicRequests(status?: RequestStatus): Promise<ClinicRequest[]> {
    const response = await apiClient.get<ClinicRequest[]>(
      '/clinics/my-requests',
      { params: status ? { status } : undefined }
    );
    return response.data;
  },

  /** T-603: mark an ACCEPTED response completed; sets dog's last donation date */
  async completeResponse(responseId: string): Promise<DonationResponse> {
    const response = await apiClient.post<DonationResponse>(
      `${REQUESTS_BASE}/responses/${responseId}/complete`
    );
    return response.data;
  },
};

// Re-export for consumers that imported the count-bearing detail type.
export type { BloodDonationRequestWithCount };

export default donationRequestService;
