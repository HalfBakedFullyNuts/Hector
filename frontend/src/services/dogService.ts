/**
 * Dog Service — all dog profile API calls (real backend)
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import type {
  DogProfile,
  DogProfileCreate,
  DogProfileUpdate,
  DogAvailabilityUpdate,
} from '../types/dog';

export const dogService = {
  /** T-301: paginated, newest-first listing of my active dogs */
  async getMyDogs(limit = 50, offset = 0): Promise<DogProfile[]> {
    const response = await apiClient.get<DogProfile[]>(API_ENDPOINTS.DOGS, {
      params: { limit, offset },
    });
    return response.data;
  },

  async getDogById(dogId: string): Promise<DogProfile> {
    const response = await apiClient.get<DogProfile>(
      `${API_ENDPOINTS.DOGS}/${dogId}`
    );
    return response.data;
  },

  async createDog(data: DogProfileCreate): Promise<DogProfile> {
    const response = await apiClient.post<DogProfile>(
      API_ENDPOINTS.DOGS,
      data
    );
    return response.data;
  },

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

  /** T-305: toggles donation availability only */
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

  /** Soft delete (T-304) */
  async deleteDog(dogId: string): Promise<void> {
    await apiClient.delete(`${API_ENDPOINTS.DOGS}/${dogId}`);
  },

  /** T-1001: multipart photo upload; returns updated profile with photo_url */
  async uploadPhoto(dogId: string, file: File): Promise<DogProfile> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<DogProfile>(
      `${API_ENDPOINTS.DOGS}/${dogId}/photo`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },
};

export default dogService;
