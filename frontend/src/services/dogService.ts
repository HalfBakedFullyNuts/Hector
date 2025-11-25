/**
 * Dog Service
 * Handles all dog profile-related API calls
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import {
  DogProfile,
  DogProfileCreate,
  DogProfileUpdate,
  DogAvailabilityUpdate,
} from '../types/dog';

export const dogService = {
  /**
   * Get all dogs for current user
   */
  async getMyDogs(): Promise<DogProfile[]> {
    const response = await apiClient.get<DogProfile[]>(API_ENDPOINTS.DOGS);
    return response.data;
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
