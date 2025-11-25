/**
 * Donation Request Service
 * Handles all donation request-related API calls
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import {
  BloodDonationRequest,
  DonationRequestCreate,
  DonationResponse,
  DonationResponseCreate,
  RequestStatus,
  ResponseStatus,
} from '../types/donationRequest';

export const donationRequestService = {
  /**
   * Get all donation requests (with optional filters)
   */
  async getRequests(params?: {
    status?: RequestStatus;
    clinic_id?: string;
  }): Promise<BloodDonationRequest[]> {
    const response = await apiClient.get<BloodDonationRequest[]>(
      API_ENDPOINTS.DONATION_REQUESTS,
      { params }
    );
    return response.data;
  },

  /**
   * Get compatible requests for a specific dog
   */
  async getCompatibleRequests(dogId: string): Promise<BloodDonationRequest[]> {
    const response = await apiClient.get<BloodDonationRequest[]>(
      `${API_ENDPOINTS.DONATION_REQUESTS}/compatible`,
      { params: { dog_id: dogId } }
    );
    return response.data;
  },

  /**
   * Get request by ID
   */
  async getRequestById(requestId: string): Promise<BloodDonationRequest> {
    const response = await apiClient.get<BloodDonationRequest>(
      `${API_ENDPOINTS.DONATION_REQUESTS}/${requestId}`
    );
    return response.data;
  },

  /**
   * Create a new donation request (clinic staff only)
   */
  async createRequest(
    data: DonationRequestCreate
  ): Promise<BloodDonationRequest> {
    const response = await apiClient.post<BloodDonationRequest>(
      API_ENDPOINTS.DONATION_REQUESTS,
      data
    );
    return response.data;
  },

  /**
   * Respond to a donation request
   */
  async respondToRequest(
    requestId: string,
    data: DonationResponseCreate
  ): Promise<DonationResponse> {
    const response = await apiClient.post<DonationResponse>(
      `${API_ENDPOINTS.DONATION_REQUESTS}/${requestId}/respond`,
      data
    );
    return response.data;
  },

  /**
   * Get responses for a specific request (clinic staff only)
   */
  async getRequestResponses(
    requestId: string,
    status?: ResponseStatus
  ): Promise<DonationResponse[]> {
    const response = await apiClient.get<DonationResponse[]>(
      `${API_ENDPOINTS.DONATION_REQUESTS}/${requestId}/responses`,
      { params: { status } }
    );
    return response.data;
  },

  /**
   * Get user's own responses (dog owner)
   */
  async getMyResponses(): Promise<DonationResponse[]> {
    const response = await apiClient.get<DonationResponse[]>(
      `${API_ENDPOINTS.DONATION_REQUESTS}/my-responses`
    );
    return response.data;
  },

  /**
   * Mark response as completed (clinic staff only)
   */
  async completeResponse(responseId: string): Promise<DonationResponse> {
    const response = await apiClient.post<DonationResponse>(
      `${API_ENDPOINTS.DONATION_REQUESTS}/responses/${responseId}/complete`
    );
    return response.data;
  },
};

export default donationRequestService;
