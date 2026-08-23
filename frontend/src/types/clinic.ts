/**
 * Clinic Types — aligned with backend schemas
 */

export interface Clinic {
  id: string;
  name: string;
  address: string;
  city: string;
  postal_code: string;
  phone: string;
  email: string;
  latitude: number | null;
  longitude: number | null;
  is_approved: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClinicCreate {
  name: string;
  address: string;
  city: string;
  postal_code: string;
  phone: string;
  email: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface ClinicUpdate extends Partial<Omit<ClinicCreate, 'latitude' | 'longitude'>> {
  latitude?: number | null;
  longitude?: number | null;
}
