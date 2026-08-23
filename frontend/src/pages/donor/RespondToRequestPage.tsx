/**
 * Respond to Donation Request (T-907)
 * Dog picker with eligibility display, accept/decline, optional message
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Select } from '../../components/common/Select';
import { Textarea } from '../../components/common/Textarea';
import { Button } from '../../components/common/Button';
import { dogService } from '../../services/dogService';
import { donationRequestService } from '../../services/donationRequestService';
import type { BloodDonationRequest } from '../../types/donationRequest';
import { ResponseStatus } from '../../types/donationRequest';
import type { DogProfile } from '../../types/dog';

function weeksSinceLastDonation(dog: DogProfile): number | null {
  if (!dog.last_donation_date) return null;
  const last = new Date(dog.last_donation_date);
  return Math.floor((Date.now() - last.getTime()) / (7 * 24 * 60 * 60 * 1000));
}

export const RespondToRequestPage: React.FC = () => {
  const navigate = useNavigate();
  const { requestId } = useParams<{ requestId: string }>();

  const [request, setRequest] = useState<BloodDonationRequest | null>(null);
  const [dogs, setDogs] = useState<DogProfile[]>([]);
  const [selectedDogId, setSelectedDogId] = useState('');
  const [decision, setDecision] = useState<ResponseStatus>(ResponseStatus.ACCEPTED);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [req, myDogs] = await Promise.all([
          donationRequestService.getRequestById(requestId ?? ''),
          dogService.getMyDogs(50),
        ]);
        setRequest(req);
        setDogs(myDogs.filter((d) => d.is_active && d.is_available_for_donation));
      } catch (err) {
        console.error('Error loading respond page:', err);
        setApiError('Failed to load this request.');
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [requestId]);

  const selectedDog = dogs.find((d) => d.id === selectedDogId) ?? null;
  const weeksSince = selectedDog ? weeksSinceLastDonation(selectedDog) : null;
  const recentlyDonated =
    decision === ResponseStatus.ACCEPTED &&
    selectedDog !== null &&
    weeksSince !== null &&
    weeksSince < 8;

  const handleSubmit = async () => {
    if (!requestId || !selectedDogId) return;
    setSubmitting(true);
    setApiError(null);
    try {
      await donationRequestService.respondToRequest(requestId, {
        dog_id: selectedDogId,
        status: decision,
        response_message: message || undefined,
      });
      navigate('/owner/responses');
    } catch (err: unknown) {
      console.error(err);
      setApiError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Could not submit your response.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-blue border-r-transparent"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-4 md:p-8 max-w-2xl mx-auto">
        <button
          onClick={() => navigate('/owner/requests')}
          className="text-sm text-text-light hover:text-text-dark mb-4"
        >
          ← Back to requests
        </button>

        <h1 className="text-3xl font-bold text-text-dark mb-6">
          Respond to Request
        </h1>

        {request && (
          <div className="card mb-8">
            <h2 className="text-lg font-semibold text-text-dark mb-2">
              {request.clinic?.name ?? 'Clinic'} ·{' '}
              {request.blood_type_needed
                ? request.blood_type_needed.replace(/_/g, ' ')
                : 'Any blood type'}
            </h2>
            <p className="text-text-light">
              {request.volume_ml} ml · needed by{' '}
              {new Date(request.needed_by_date).toLocaleDateString()} · urgency{' '}
              {request.urgency}
            </p>
            {request.patient_info && (
              <p className="text-sm text-text-dark mt-3">{request.patient_info}</p>
            )}
          </div>
        )}

        {dogs.length === 0 ? (
          <div className="card text-center py-10">
            <span className="text-5xl block mb-3">🐕</span>
            <h3 className="text-lg font-semibold text-text-dark mb-2">
              No available dogs
            </h3>
            <p className="text-text-light mb-4">
              You need an active, available dog profile to respond.
            </p>
            <Button onClick={() => navigate('/owner/dogs/new')}>Add a Dog</Button>
          </div>
        ) : (
          <div className="card space-y-4">
            <Select
              label="Choose your dog"
              options={[
                ...dogs.map((dog) => ({
                  value: dog.id,
                  label: `${dog.name}${dog.blood_type ? ` (${dog.blood_type.replace(/_/g, ' ')})` : ''}`,
                })),
              ]}
              value={selectedDogId}
              onChange={(e) => setSelectedDogId(e.target.value)}
            />

            {selectedDog && (
              <div
                className={`p-3 rounded-input text-sm ${
                  recentlyDonated
                    ? 'bg-red-50 border border-red-200 text-red-700'
                    : 'bg-green-50 border border-green-200 text-green-700'
                }`}
              >
                {recentlyDonated
                  ? `⚠️ ${selectedDog.name} donated only ${weeksSince} weeks ago — clinics require 8+ weeks between donations.`
                  : `✅ ${selectedDog.name} looks eligible to donate.`}
              </div>
            )}

            <div>
              <p className="block text-sm font-medium text-text-dark mb-2">Your answer</p>
              <div className="flex flex-col sm:flex-row gap-4">
                {([ResponseStatus.ACCEPTED, ResponseStatus.DECLINED] as const).map(
                  (status) => (
                    <label
                      key={status}
                      className={`flex-1 cursor-pointer rounded-input border p-4 transition-colors ${
                        decision === status
                          ? status === ResponseStatus.ACCEPTED
                            ? 'border-primary-blue bg-blue-50'
                            : 'border-gray-400 bg-gray-100'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="decision"
                        value={status}
                        checked={decision === status}
                        onChange={() => setDecision(status)}
                        className="mr-2"
                      />
                      {status === ResponseStatus.ACCEPTED ? 'I can help! ✅' : 'Not this time'}
                    </label>
                  )
                )}
              </div>
            </div>

            <Textarea
              label="Message to the clinic (optional)"
              placeholder="Availability questions, timing…"
              rows={3}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />

            {apiError && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-input text-red-700">
                {apiError}
              </div>
            )}

            <Button
              onClick={() => void handleSubmit()}
              disabled={submitting || !selectedDogId || recentlyDonated}
              fullWidth
            >
              {submitting ? 'Sending…' : 'Submit Response'}
            </Button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default RespondToRequestPage;
