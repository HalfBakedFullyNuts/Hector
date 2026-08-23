/**
 * Dog Profile Form Page
 * Create or edit a dog profile; includes photo upload (T-1001)
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Textarea } from '../../components/common/Textarea';
import { Button } from '../../components/common/Button';
import { dogService } from '../../services/dogService';
import { BloodType, DogSex } from '../../types/dog';

// Validation schema
const dogProfileSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name is too long'),
  breed: z.string().max(100, 'Breed is too long').optional(),
  date_of_birth: z.string().min(1, 'Date of birth is required').refine(
    (dateStr) => {
      const date = new Date(dateStr);
      const today = new Date();
      const ageInYears = (today.getTime() - date.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
      return ageInYears >= 1;
    },
    { message: 'Dog must be at least 1 year old' }
  ).refine(
    (dateStr) => {
      const date = new Date(dateStr);
      const today = new Date();
      const ageInYears = (today.getTime() - date.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
      return ageInYears <= 8;
    },
    { message: 'Dog must be 8 years or younger for donation eligibility' }
  ),
  weight_kg: z.coerce
    .number()
    .min(25, 'Dog must weigh at least 25kg for donation eligibility')
    .max(100, 'Weight seems unusually high, please verify'),
  sex: z.nativeEnum(DogSex),
  blood_type: z.string().optional(),
  medical_notes: z.string().max(2000, 'Health notes are too long').optional(),
});

type DogProfileFormData = z.infer<typeof dogProfileSchema>;

export const DogProfileForm: React.FC = () => {
  const navigate = useNavigate();
  const { dogId } = useParams<{ dogId: string }>();
  const isEditMode = !!dogId;

  const [loading, setLoading] = useState(isEditMode);
  const [apiError, setApiError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isAvailable, setIsAvailable] = useState(true);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [existingPhotoUrl, setExistingPhotoUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    watch,
  } = useForm<DogProfileFormData>({
    resolver: zodResolver(dogProfileSchema) as never,
    defaultValues: {
      name: '',
      breed: '',
      date_of_birth: '',
      weight_kg: 25,
      sex: DogSex.MALE,
      blood_type: '',
      medical_notes: '',
    },
  });

  // Watch date of birth to show eligibility info
  const dateOfBirth = watch('date_of_birth');
  const weightKg = watch('weight_kg');

  // Calculate eligibility indicators
  const eligibilityInfo = React.useMemo(() => {
    if (!dateOfBirth || !weightKg) return null;

    const birthDate = new Date(dateOfBirth);
    const today = new Date();
    const ageInYears = (today.getTime() - birthDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000);

    const issues: string[] = [];
    if (ageInYears < 1) issues.push('Too young (must be 1+ years)');
    if (ageInYears > 8) issues.push('Too old (must be 8 years or younger)');
    if (weightKg < 25) issues.push('Too light (must be 25+ kg)');

    return {
      ageInYears: Math.floor(ageInYears * 10) / 10,
      eligible: issues.length === 0,
      issues,
    };
  }, [dateOfBirth, weightKg]);

  const loadDogData = React.useCallback(async (id: string) => {
    try {
      setLoading(true);
      const dog = await dogService.getDogById(id);
      reset({
        name: dog.name,
        breed: dog.breed ?? '',
        date_of_birth: dog.date_of_birth,
        weight_kg: dog.weight_kg,
        sex: dog.sex,
        blood_type: dog.blood_type ?? '',
        medical_notes: dog.medical_notes ?? '',
      });
      setIsAvailable(dog.is_available_for_donation);
      setExistingPhotoUrl(dog.photo_url);
    } catch (err) {
      console.error('Error loading dog:', err);
      setApiError('Failed to load dog profile. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [reset]);

  useEffect(() => {
    if (isEditMode && dogId) {
      void loadDogData(dogId);
    }
  }, [isEditMode, dogId, loadDogData]);

  const handlePhotoChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  };

  const onSubmit = async (data: DogProfileFormData) => {
    try {
      setApiError(null);
      setSuccessMessage(null);

      const submitData = {
        name: data.name,
        breed: data.breed || undefined,
        date_of_birth: data.date_of_birth,
        weight_kg: Number(data.weight_kg),
        sex: data.sex,
        blood_type: (data.blood_type || undefined) as never,
        medical_notes: data.medical_notes || undefined,
      };

      let savedDogId = dogId;
      if (isEditMode && dogId) {
        await dogService.updateDog(dogId, submitData);
        setSuccessMessage('Dog profile updated successfully!');
      } else {
        const created = await dogService.createDog(submitData);
        savedDogId = created.id;
        setSuccessMessage('Dog profile created successfully!');
      }

      if (photoFile && savedDogId) {
        await dogService.uploadPhoto(savedDogId, photoFile);
      }

      // Redirect to dashboard after a short delay
      setTimeout(() => {
        navigate('/owner');
      }, 1500);
    } catch (err: unknown) {
      console.error('Error saving dog:', err);
      setApiError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Failed to save dog profile. Please try again.'
      );
    }
  };

  // Blood type options
  const bloodTypeOptions = [
    { value: '', label: 'Unknown / Not tested' },
    { value: BloodType.DEA_1_1_NEGATIVE, label: 'DEA 1.1 Negative (Universal Donor)' },
    { value: BloodType.DEA_1_1_POSITIVE, label: 'DEA 1.1 Positive' },
    { value: BloodType.DEA_1_2_POSITIVE, label: 'DEA 1.2 Positive' },
    { value: BloodType.DEA_1_2_NEGATIVE, label: 'DEA 1.2 Negative' },
    { value: BloodType.DEA_3_POSITIVE, label: 'DEA 3 Positive' },
    { value: BloodType.DEA_3_NEGATIVE, label: 'DEA 3 Negative' },
    { value: BloodType.DEA_4_POSITIVE, label: 'DEA 4 Positive' },
    { value: BloodType.DEA_4_NEGATIVE, label: 'DEA 4 Negative' },
    { value: BloodType.DEA_5_POSITIVE, label: 'DEA 5 Positive' },
    { value: BloodType.DEA_5_NEGATIVE, label: 'DEA 5 Negative' },
    { value: BloodType.DEA_7_POSITIVE, label: 'DEA 7 Positive' },
    { value: BloodType.DEA_7_NEGATIVE, label: 'DEA 7 Negative' },
  ];

  const sexOptions = [
    { value: DogSex.MALE, label: 'Male' },
    { value: DogSex.FEMALE, label: 'Female' },
  ];

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-blue border-r-transparent"></div>
            <p className="mt-4 text-text-light">Loading dog profile...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-4 md:p-8 max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-dark mb-2">
            {isEditMode ? 'Edit Dog Profile' : 'Add New Dog'}
          </h1>
          <p className="text-text-light">
            {isEditMode
              ? "Update your dog's information to keep it accurate"
              : "Add your dog's information to start helping save lives"}
          </p>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-input text-green-700">
            ✅ {successMessage}
          </div>
        )}

        {/* Error Message */}
        {apiError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-input text-red-700">
            {apiError}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Information */}
          <div className="card">
            <h2 className="text-xl font-semibold text-text-dark mb-4">
              Basic Information
            </h2>

            <div className="space-y-4">
              <Input
                label="Dog's Name"
                placeholder="e.g., Max, Bella, Charlie"
                error={errors.name?.message}
                {...register('name')}
              />

              <Input
                label="Breed"
                placeholder="e.g., Golden Retriever, Mixed Breed"
                error={errors.breed?.message}
                {...register('breed')}
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Date of Birth"
                  type="date"
                  error={errors.date_of_birth?.message}
                  {...register('date_of_birth')}
                />

                <Input
                  label="Weight (kg)"
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="25"
                  error={errors.weight_kg?.message}
                  {...register('weight_kg')}
                />
              </div>

              <Select
                label="Sex"
                options={sexOptions}
                error={errors.sex?.message}
                {...register('sex')}
              />

              {/* Eligibility Indicator */}
              {eligibilityInfo && (
                <div
                  className={`p-3 rounded-input text-sm ${eligibilityInfo.eligible
                    ? 'bg-green-50 border border-green-200 text-green-700'
                    : 'bg-yellow-50 border border-yellow-200 text-yellow-700'
                    }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium">
                      {eligibilityInfo.eligible
                        ? '✅ Eligible for Donation'
                        : '⚠️ Not Currently Eligible'}
                    </span>
                    <span className="text-xs">
                      (Age: {eligibilityInfo.ageInYears} years, Weight: {weightKg} kg)
                    </span>
                  </div>
                  {eligibilityInfo.issues.length > 0 && (
                    <ul className="text-xs mt-2 ml-4 list-disc">
                      {eligibilityInfo.issues.map((issue, idx) => (
                        <li key={idx}>{issue}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Medical Information */}
          <div className="card">
            <h2 className="text-xl font-semibold text-text-dark mb-4">
              Medical Information
            </h2>

            <div className="space-y-4">
              <Select
                label="Blood Type"
                options={bloodTypeOptions}
                error={errors.blood_type?.message}
                {...register('blood_type')}
              />

              <Textarea
                label="Health Notes (Optional)"
                placeholder="Any health conditions, medications, or special considerations..."
                rows={4}
                error={errors.medical_notes?.message}
                {...register('medical_notes')}
              />
            </div>
          </div>

          {/* Availability */}
          <div className="card">
            <h2 className="text-xl font-semibold text-text-dark mb-4">
              Donation Availability
            </h2>

            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="is_available"
                checked={isAvailable}
                onChange={(e) => setIsAvailable(e.target.checked)}
                className="mt-1 h-4 w-4 text-primary-blue focus:ring-primary-blue border-gray-300 rounded"
              />
              <div>
                <label
                  htmlFor="is_available"
                  className="font-medium text-text-dark cursor-pointer"
                >
                  Available for blood donation
                </label>
                <p className="text-sm text-text-light mt-1">
                  Check this box if your dog is currently available to donate blood.
                  You can update this anytime.
                </p>
              </div>
            </div>
          </div>

          {/* Photo Upload (T-1001) */}
          <div className="card">
            <h2 className="text-xl font-semibold text-text-dark mb-4">Photo</h2>

            <div className="flex flex-col sm:flex-row items-center gap-6">
              <div className="w-32 h-32 bg-base-off-white rounded-input flex items-center justify-center overflow-hidden shrink-0">
                {photoPreview ?? (existingPhotoUrl ? (
                  <img src={existingPhotoUrl} alt="Dog" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-5xl">📷</span>
                ))}
              </div>

              <div className="flex-1 w-full">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png"
                  className="hidden"
                  onChange={handlePhotoChange}
                />
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Choose Photo
                </Button>
                <p className="text-xs text-text-light mt-2">
                  JPEG or PNG, up to 5 MB, max 2000×2000 pixels.
                </p>
                {photoFile && (
                  <p className="text-xs text-green-700 mt-1">
                    Selected: {photoFile.name} ({Math.round(photoFile.size / 1024)} KB)
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex flex-col sm:flex-row gap-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/owner')}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting} fullWidth>
              {isSubmitting
                ? 'Saving...'
                : isEditMode
                  ? 'Update Dog Profile'
                  : 'Create Dog Profile'}
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
};

export default DogProfileForm;
