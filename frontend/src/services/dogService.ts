/**
 * Dog Service
 * Handles all dog profile-related API calls
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import type {
  DogProfile,
  DogProfileCreate,
  DogProfileUpdate,
  DogAvailabilityUpdate,
} from '../types/dog';
import { BloodType } from '../types/dog';

const MOCK_DOGS: DogProfile[] = [
  {
    id: 'dog-1',
    owner_id: 'dev-owner-001',
    name: 'Buddy',
    breed: 'Golden Retriever',
    date_of_birth: '2020-01-01',
    weight_kg: 32,
    blood_type: BloodType.DEA_1_1_NEGATIVE,
    is_active: true,
    last_donation_date: '2023-10-15',
    health_notes: 'Healthy and happy',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    age_years: 3,
    is_eligible_for_donation: true,
  },
  {
    id: 'dog-2',
    owner_id: 'dev-owner-001',
    name: 'Luna',
    breed: 'German Shepherd',
    date_of_birth: '2021-05-20',
    weight_kg: 28,
    blood_type: BloodType.DEA_1_1_POSITIVE,
    is_active: true,
    last_donation_date: null,
    health_notes: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    age_years: 2,
    is_eligible_for_donation: true,
  },
];
export const dogService = {
  /**
   * Get all dogs for current user
   */
  async getMyDogs(): Promise<DogProfile[]> {
    // Mock data for development
    return new Promise((resolve) => {
      setTimeout(() => resolve(MOCK_DOGS), 500);
    });
    // const response = await apiClient.get<DogProfile[]>(API_ENDPOINTS.DOGS);
    // return response.data;
  },

  /**
   * Get a specific dog by ID
   */
  async getDogById(dogId: string): Promise<DogProfile> {
    const response = await apiClient.get<DogProfile>(
      `${API_ENDPOINTS.DOGS}/${dogId}`
    );
    return response.data;
  },

  /**
   * Create a new dog profile
   */
  async createDog(data: DogProfileCreate): Promise<DogProfile> {
    const response = await apiClient.post<DogProfile>(
      API_ENDPOINTS.DOGS,
      data
    );
    return response.data;
  },

  /**
   * Update dog profile
   */
  async updateDog(
    dogId: string,
    data: DogProfileUpdate
  ): Promise<DogProfile> {
    const response = await apiClient.patch<DogProfile>(
      `${API_ENDPOINTS.DOGS}/${dogId}`,
      data
    );
    return response.data;
  },

  /**
   * Update dog availability status
   */
  async updateDogAvailability(
    dogId: string,
    data: DogAvailabilityUpdate
  ): Promise<DogProfile> {
    const response = await apiClient.patch<DogProfile>(
      `${API_ENDPOINTS.DOGS}/${dogId}/availability`,
      data
    );
    return response.data;
  },

  /**
   * Delete dog profile
   */
  async deleteDog(dogId: string): Promise<void> {
    await apiClient.delete(`${API_ENDPOINTS.DOGS}/${dogId}`);
  },
};

export default dogService;
