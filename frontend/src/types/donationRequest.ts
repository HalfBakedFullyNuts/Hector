/**
 * Donation Request Types — aligned with backend schemas
 */

import { BloodType } from './dog';

export enum RequestUrgency {
  ROUTINE = 'ROUTINE',
  URGENT = 'URGENT',
  CRITICAL = 'CRITICAL',
}

export enum RequestStatus {
  OPEN = 'OPEN',
  FULFILLED = 'FULFILLED',
  CANCELLED = 'CANCELLED',
  EXPIRED = 'EXPIRED',
}

export enum ResponseStatus {
  ACCEPTED = 'ACCEPTED',
  DECLINED = 'DECLINED',
  COMPLETED = 'COMPLETED',
}

export interface ClinicSummary {
  id: string;
  name: string;
  address: string;
  city: string;
}

export interface BloodDonationRequest {
  id: string;
  clinic_id: string;
  created_by_user_id?: string | null;
  blood_type_needed: BloodType | null;
  urgency: RequestUrgency;
  volume_ml: number;
  patient_info: string | null;
  needed_by_date: string;
  status: RequestStatus;
  created_at: string;
  updated_at: string;
  clinic?: ClinicSummary | null;
}

/** GET /requests/{id} */
export interface BloodDonationRequestWithCount extends BloodDonationRequest {
  response_count: number;
}

/** Listings with distance when geo params are used (T-1004) */
export interface DonationRequestWithDistance extends BloodDonationRequest {
  distance_km?: number | null;
}

/** Compatible listing entries (T-604) */
export interface CompatibleRequest extends BloodDonationRequest {
  compatibility_score: number;
}

/** Staff clinic listings (T-505/T-901) */
export interface ClinicRequest extends BloodDonationRequest {
  response_count: number;
}

export interface DonationRequestCreate {
  blood_type_needed?: BloodType | null;
  urgency: RequestUrgency;
  volume_ml: number;
  needed_by_date: string;
  patient_info?: string | null;
}

export interface DonationRequestUpdate {
  urgency?: RequestUrgency;
  volume_ml?: number;
  needed_by_date?: string;
  patient_info?: string | null;
}

export interface DogSummary {
  id: string;
  name: string;
  breed: string | null;
  blood_type: BloodType | null;
}

export interface DonationResponse {
  id: string;
  request_id: string;
  dog_id: string;
  owner_id: string;
  status: ResponseStatus;
  response_message: string | null;
  created_at: string;
  updated_at: string;
  dog?: Partial<DogSummary> & Record<string, unknown> | null;
  owner_email?: string;
  request?: BloodDonationRequest;
  clinic?: ClinicSummary | null;
}

export interface DonationResponseCreate {
  dog_id: string;
  status: ResponseStatus;
  response_message?: string | null;
}
