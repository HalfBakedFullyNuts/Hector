/**
 * Dog Types
 */

export enum BloodType {
  DEA_1_1_POSITIVE = 'DEA_1_1_POSITIVE',
  DEA_1_1_NEGATIVE = 'DEA_1_1_NEGATIVE',
  DEA_1_2_POSITIVE = 'DEA_1_2_POSITIVE',
  DEA_3_POSITIVE = 'DEA_3_POSITIVE',
  DEA_4_POSITIVE = 'DEA_4_POSITIVE',
  DEA_5_POSITIVE = 'DEA_5_POSITIVE',
  UNKNOWN = 'UNKNOWN',
}

export interface DogProfile {
  id: string;
  owner_id: string;
  name: string;
  breed: string;
  date_of_birth: string;
  weight_kg: number;
  blood_type: BloodType | null;
  is_active: boolean;
  last_donation_date: string | null;
  health_notes: string | null;
  created_at: string;
  updated_at: string;
  // Computed fields
  age_years?: number;
  is_eligible_for_donation?: boolean;
}

export interface DogProfileCreate {
  name: string;
  breed: string;
  date_of_birth: string;
  weight_kg: number;
  blood_type?: BloodType;
  is_active: boolean;
  health_notes?: string;
}

export interface DogProfileUpdate {
  name?: string;
  breed?: string;
  date_of_birth?: string;
  weight_kg?: number;
  blood_type?: BloodType;
  health_notes?: string;
}

export interface DogAvailabilityUpdate {
  is_active: boolean;
}
