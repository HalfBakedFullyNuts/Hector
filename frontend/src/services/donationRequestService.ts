/**
 * Donation Request Service
 * Handles all donation request-related API calls
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import type {
  BloodDonationRequest,
  DonationRequestCreate,
  DonationResponse,
  DonationResponseCreate,
} from '../types/donationRequest';
import { RequestUrgency, RequestStatus, ResponseStatus } from '../types/donationRequest';
import { BloodType } from '../types/dog';

const MOCK_REQUESTS: BloodDonationRequest[] = [
  {
    id: 'req-1',
    clinic_id: 'clinic-1',
    urgency: RequestUrgency.CRITICAL,
    status: RequestStatus.OPEN,
    blood_type_needed: BloodType.DEA_1_1_NEGATIVE,
    volume_ml: 450,
    needed_by_date: '2023-11-30',
    reason_for_transfusion: 'Urgent need for a surgery case. Universal donor preferred.',
    patient_breed: 'Labrador',
    contact_person: 'Dr. Smith',
    contact_phone: '555-0123',
    special_notes: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    clinic: {
      id: 'clinic-1',
      name: 'City Vet Clinic',
      address: '123 Main St',
      city: 'New York',
    },
  },
  {
    id: 'req-2',
    clinic_id: 'clinic-2',
    urgency: RequestUrgency.ROUTINE,
    status: RequestStatus.OPEN,
    blood_type_needed: BloodType.DEA_1_1_POSITIVE,
    volume_ml: 300,
    needed_by_date: '2023-12-05',
    reason_for_transfusion: 'Scheduled procedure requiring backup blood supply.',
    patient_breed: 'Poodle',
    contact_person: 'Nurse Joy',
    contact_phone: '555-0456',
    special_notes: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    clinic: {
      id: 'clinic-2',
      name: 'Paws & Claws Hospital',
      address: '456 Oak Ave',
      city: 'Los Angeles',
    },
  },
];

const MOCK_RESPONSES: DonationResponse[] = [
  {
    id: 'resp-1',
    request_id: 'req-3',
    dog_id: 'dog-1',
    owner_id: 'dev-owner-001',
    status: ResponseStatus.PENDING,
    response_message: 'Can donate anytime this week.',
    created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
    updated_at: new Date().toISOString(),
    dog: {
      id: 'dog-1',
      name: 'Buddy',
      breed: 'Golden Retriever',
      blood_type: BloodType.DEA_1_1_NEGATIVE,
    },
  },
];

export const donationRequestService = {
  /**
   * Get all donation requests (with optional filters)
   */
  async getRequests(_params?: {
    status?: RequestStatus;
    clinic_id?: string;
  }): Promise<BloodDonationRequest[]> {
    // Mock data for development
    return new Promise((resolve) => {
      setTimeout(() => resolve(MOCK_REQUESTS), 500);
    });
    // const response = await apiClient.get<BloodDonationRequest[]>(
    //   API_ENDPOINTS.DONATION_REQUESTS,
    //   { params }
    // );
    // return response.data;
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
    // Mock data for development
    return new Promise((resolve) => {
      setTimeout(() => resolve(MOCK_RESPONSES), 500);
    });
    // const response = await apiClient.get<DonationResponse[]>(
    //   `${API_ENDPOINTS.DONATION_REQUESTS}/my-responses`
    // );
    // return response.data;
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
