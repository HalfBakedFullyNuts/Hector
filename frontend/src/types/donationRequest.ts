/**
 * Donation Request Types
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
}

export enum ResponseStatus {
  PENDING = 'PENDING',
  ACCEPTED = 'ACCEPTED',
  DECLINED = 'DECLINED',
  COMPLETED = 'COMPLETED',
}

export interface BloodDonationRequest {
  id: string;
  clinic_id: string;
  blood_type_needed: BloodType | null;
  urgency: RequestUrgency;
  volume_ml: number;
  needed_by_date: string;
  patient_breed: string | null;
  reason_for_transfusion: string | null;
  contact_person: string | null;
  contact_phone: string | null;
  special_notes: string | null;
  status: RequestStatus;
  created_at: string;
  updated_at: string;
  // Relations
  clinic?: {
    id: string;
    name: string;
    address: string;
    city: string;
  };
}

export interface DonationRequestCreate {
  blood_type_needed?: BloodType;
  urgency: RequestUrgency;
  volume_ml: number;
  needed_by_date: string;
  patient_breed?: string;
  reason_for_transfusion?: string;
  contact_person?: string;
  contact_phone?: string;
  special_notes?: string;
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
  // Relations
  dog?: {
    id: string;
    name: string;
    breed: string;
    blood_type: BloodType | null;
  };
  request?: BloodDonationRequest;
}

export interface DonationResponseCreate {
  dog_id: string;
  status: ResponseStatus;
  response_message?: string;
}
