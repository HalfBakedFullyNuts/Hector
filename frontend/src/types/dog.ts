/**
 * Dog Types — aligned with backend models/schemas
 */

export enum BloodType {
  DEA_1_1_POSITIVE = 'DEA_1_1_POSITIVE',
  DEA_1_1_NEGATIVE = 'DEA_1_1_NEGATIVE',
  DEA_1_2_POSITIVE = 'DEA_1_2_POSITIVE',
  DEA_1_2_NEGATIVE = 'DEA_1_2_NEGATIVE',
  DEA_3_POSITIVE = 'DEA_3_POSITIVE',
  DEA_3_NEGATIVE = 'DEA_3_NEGATIVE',
  DEA_4_POSITIVE = 'DEA_4_POSITIVE',
  DEA_4_NEGATIVE = 'DEA_4_NEGATIVE',
  DEA_5_POSITIVE = 'DEA_5_POSITIVE',
  DEA_5_NEGATIVE = 'DEA_5_NEGATIVE',
  DEA_7_POSITIVE = 'DEA_7_POSITIVE',
  DEA_7_NEGATIVE = 'DEA_7_NEGATIVE',
  UNKNOWN = 'UNKNOWN',
}

export enum DogSex {
  MALE = 'MALE',
  FEMALE = 'FEMALE',
}

export interface DogProfile {
  id: string;
  owner_id: string;
  name: string;
  breed: string | null;
  date_of_birth: string;
  weight_kg: number;
  sex: DogSex;
  blood_type: BloodType | null;
  last_donation_date: string | null;
  medical_notes: string | null;
  vaccination_status: string | null;
  photo_url: string | null;
  is_active: boolean;
  is_available_for_donation: boolean;
  created_at: string;
  updated_at: string;
}

export interface DogProfileCreate {
  name: string;
  breed?: string;
  date_of_birth: string;
  weight_kg: number;
  sex: DogSex;
  blood_type?: BloodType | null;
  last_donation_date?: string | null;
  medical_notes?: string | null;
  vaccination_status?: string | null;
}

export interface DogProfileUpdate {
  name?: string;
  breed?: string | null;
  date_of_birth?: string;
  weight_kg?: number;
  sex?: DogSex;
  blood_type?: BloodType | null;
  last_donation_date?: string | null;
  medical_notes?: string | null;
  vaccination_status?: string | null;
}

/** T-305: availability is independent of the soft-delete flag */
export interface DogAvailabilityUpdate {
  is_available: boolean;
}
