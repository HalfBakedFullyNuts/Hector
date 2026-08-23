/**
 * Service layer tests: verify real API wiring (no mocks of the services themselves)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./apiClient', () => {
  const calls: Array<{ method: string; url: string; data?: unknown; config?: unknown }> = [];
  const apiClient = {
    get: vi.fn(async (url: string, config?: unknown) => ({ data: { url, config }, __calls: calls })),
    post: vi.fn(async (url: string, data?: unknown) => ({ data: { url, data } })),
    patch: vi.fn(async (url: string, data?: unknown) => ({ data: { url, data } })),
    put: vi.fn(async (url: string, data?: unknown) => ({ data: { url, data } })),
    delete: vi.fn(async (url: string, config?: unknown) => ({ data: { url, config } })),
  };
  return { apiClient, default: apiClient };
});

import { apiClient } from './apiClient';
import { dogService } from './dogService';
import { donationRequestService } from './donationRequestService';
import { adminService } from './adminService';
import { clinicService } from './clinicService';
import { DogSex } from '../types/dog';
import { RequestStatus, ResponseStatus, RequestUrgency } from '../types/donationRequest';

beforeEach(() => {
  vi.clearAllMocks();
});

describe('dogService', () => {
  it('lists dogs with pagination params (T-301)', async () => {
    await dogService.getMyDogs(20, 5);
    expect(apiClient.get).toHaveBeenCalledWith('/dogs', {
      params: { limit: 20, offset: 5 },
    });
  });

  it('sends is_available for availability toggles (T-305)', async () => {
    await dogService.updateDogAvailability('d1', { is_available: false });
    expect(apiClient.patch).toHaveBeenCalledWith('/dogs/d1/availability', {
      is_available: false,
    });
  });

  it('uploads photos as multipart form data (T-1001)', async () => {
    const file = new File(['x'], 'dog.png', { type: 'image/png' });
    await dogService.uploadPhoto('d1', file);
    const [url, body, config] = (apiClient.post as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe('/dogs/d1/photo');
    expect(body).toBeInstanceOf(FormData);
    expect(config.headers['Content-Type']).toBe('multipart/form-data');
  });

  it('creates dogs with the backend payload shape', async () => {
    await dogService.createDog({
      name: 'Max',
      date_of_birth: '2022-01-01',
      weight_kg: 30,
      sex: DogSex.MALE,
    });
    const [url, data] = (apiClient.post as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe('/dogs');
    expect(data.sex).toBe(DogSex.MALE);
  });
});

describe('donationRequestService', () => {
  it('browses requests with geo filters (T-1004)', async () => {
    await donationRequestService.getRequests({
      status: RequestStatus.OPEN,
      lat: 52.52,
      lng: 13.4,
      max_distance_km: 50,
    });
    expect(apiClient.get).toHaveBeenCalledWith('/requests', {
      params: { status: RequestStatus.OPEN, lat: 52.52, lng: 13.4, max_distance_km: 50 },
    });
  });

  it('responds with dog_id/status/message (T-600)', async () => {
    await donationRequestService.respondToRequest('r1', {
      dog_id: 'd1',
      status: ResponseStatus.ACCEPTED,
      response_message: 'hi',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/requests/r1/respond', {
      dog_id: 'd1',
      status: 'ACCEPTED',
      response_message: 'hi',
    });
  });

  it('completes responses via the nested path (T-603)', async () => {
    await donationRequestService.completeResponse('resp-9');
    expect(apiClient.post).toHaveBeenCalledWith('/requests/responses/resp-9/complete');
  });

  it('creates requests with required fields only (T-500)', async () => {
    await donationRequestService.createRequest({
      urgency: RequestUrgency.CRITICAL,
      volume_ml: 450,
      needed_by_date: '2026-09-01T00:00:00Z',
    });
    const [url] = (apiClient.post as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe('/requests');
  });
});

describe('adminService', () => {
  it('toggles user active state with reason (T-701)', async () => {
    await adminService.toggleUserActive('u1', { reason: 'spam' });
    expect(apiClient.post).toHaveBeenCalledWith('/admin/users/u1/toggle-active', {
      reason: 'spam',
    });
  });

  it('deletes users with confirmation payload (T-702)', async () => {
    await adminService.deleteUser('u2', 'bad actor');
    expect(apiClient.delete).toHaveBeenCalledWith('/admin/users/u2', {
      data: { user_id: 'u2', reason: 'bad actor' },
    });
  });

  it('rejects clinics with a reason (T-704)', async () => {
    await adminService.rejectClinic('c1', 'not a clinic');
    expect(apiClient.post).toHaveBeenCalledWith('/admin/clinics/c1/reject', {
      rejection_reason: 'not a clinic',
    });
  });

  it('fetches stats with optional range (T-703)', async () => {
    await adminService.getStats({ start_date: '2026-08-01T00:00:00Z' });
    expect(apiClient.get).toHaveBeenCalledWith('/admin/stats', {
      params: { start_date: '2026-08-01T00:00:00Z' },
    });
  });
});

describe('clinicService', () => {
  it('creates a clinic profile (T-400)', async () => {
    await clinicService.createClinic({
      name: 'Vet Berlin',
      address: 'A St 1',
      city: 'Berlin',
      postal_code: '10115',
      phone: '+49',
      email: 'a@b.de',
    });
    const [url] = (apiClient.post as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe('/clinics');
  });
});
