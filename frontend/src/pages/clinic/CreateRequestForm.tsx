/**
 * Create Donation Request Form (T-902)
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Textarea } from '../../components/common/Textarea';
import { Button } from '../../components/common/Button';
import { donationRequestService } from '../../services/donationRequestService';
import { RequestUrgency } from '../../types/donationRequest';
import { BloodType } from '../../types/dog';

const createRequestSchema = z.object({
  blood_type_needed: z.string().optional(),
  volume_ml: z.coerce
    .number()
    .int('Volume must be a whole number')
    .min(50, 'Minimum volume is 50 ml')
    .max(500, 'Maximum volume is 500 ml'),
  urgency: z.nativeEnum(RequestUrgency),
  needed_by_date: z.string().min(1, 'Needed-by date is required').refine(
    (dateStr) => new Date(dateStr) > new Date(),
    { message: 'Date must be in the future' }
  ).refine(
    (dateStr) =>
      new Date(dateStr) <=
      new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
    { message: 'Date must be within 30 days' }
  ),
  patient_info: z.string().max(2000, 'Patient info is too long').optional(),
});

type CreateRequestFormData = z.infer<typeof createRequestSchema>;

const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
const inThirtyDays = new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0];

export const CreateRequestForm: React.FC = () => {
  const navigate = useNavigate();
  const [apiError, setApiError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateRequestFormData>({
    resolver: zodResolver(createRequestSchema) as never,
    defaultValues: {
      blood_type_needed: '',
      urgency: RequestUrgency.URGENT,
      patient_info: '',
    },
  });

  const onSubmit = async (data: CreateRequestFormData) => {
    try {
      setApiError(null);
      const created = await donationRequestService.createRequest({
        blood_type_needed: (data.blood_type_needed || undefined) as never,
        urgency: data.urgency,
        volume_ml: Number(data.volume_ml),
        needed_by_date: new Date(data.needed_by_date).toISOString(),
        patient_info: data.patient_info || undefined,
      });
      setSuccessMessage('Request created!');
      setTimeout(() => navigate(`/clinic/requests/${created.id}`), 800);
    } catch (err: unknown) {
      console.error('Error creating request:', err);
      setApiError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Failed to create request. Please try again.'
      );
    }
  };

  const urgencyOptions = [
    { value: RequestUrgency.CRITICAL, label: '🚨 Critical — immediate need' },
    { value: RequestUrgency.URGENT, label: '⚠️ Urgent — within days' },
    { value: RequestUrgency.ROUTINE, label: 'ℹ️ Routine — scheduled' },
  ];

  const bloodTypeOptions = [
    { value: '', label: 'Any type accepted' },
    ...Object.values(BloodType)
      .filter((bt) => bt !== BloodType.UNKNOWN)
      .map((bt) => ({
        value: bt,
        label: bt.replace(/_/g, '. ').replace('DEA.', 'DEA ').replace('1.1', '1-1').replace(/\.(\d)/g, ' $1'),
      })),
  ];

  if (successMessage) {
    return (
      <DashboardLayout>
        <div className="p-8 max-w-2xl mx-auto text-center py-20">
          <span className="text-6xl block mb-4">✅</span>
          <h2 className="text-2xl font-bold text-text-dark mb-2">{successMessage}</h2>
          <p className="text-text-light">Redirecting to request details…</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-4 md:p-8 max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-dark mb-2">
            New Blood Donation Request
          </h1>
          <p className="text-text-light">
            Nearby dog owners will be notified of compatible requests.
          </p>
        </div>

        {apiError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-input text-red-700">
            {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4">
          <Input
            label="Volume needed (ml)"
            type="number"
            min="50"
            max="500"
            placeholder="e.g., 450"
            error={errors.volume_ml?.message}
            {...register('volume_ml')}
          />

          <Select
            label="Blood type needed"
            options={bloodTypeOptions}
            error={errors.blood_type_needed?.message}
            {...register('blood_type_needed')}
          />

          <Select
            label="Urgency"
            options={urgencyOptions}
            error={errors.urgency?.message}
            {...register('urgency')}
          />

          <Input
            label="Needed by"
            type="date"
            min={tomorrow}
            max={inThirtyDays}
            error={errors.needed_by_date?.message}
            {...register('needed_by_date')}
          />

          <Textarea
            label="Patient info (optional)"
            placeholder="Breed, size, condition requiring transfusion…"
            rows={3}
            error={errors.patient_info?.message}
            {...register('patient_info')}
          />

          <div className="flex flex-col sm:flex-row gap-4 pt-2">
            <Button type="button" variant="secondary" onClick={() => navigate('/clinic')}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting} fullWidth>
              {isSubmitting ? 'Creating…' : 'Create Request'}
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
};

export default CreateRequestForm;
