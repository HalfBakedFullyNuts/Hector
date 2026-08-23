/**
 * Clinic Request Detail (T-903)
 * Shows request details plus responses; complete/cancel actions
 */

import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Button } from '../../components/common/Button';
import {
  donationRequestService,
} from '../../services/donationRequestService';
import type { BloodDonationRequest, DonationResponse } from '../../types/donationRequest';
import { RequestStatus, ResponseStatus } from '../../types/donationRequest';

export const ClinicRequestDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { requestId } = useParams<{ requestId: string }>();

  const [request, setRequest] = useState<BloodDonationRequest | null>(null);
  const [responses, setResponses] = useState<DonationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  const load = useCallback(async () => {
    if (!requestId) return;
    try {
      setLoading(true);
      setError(null);
      const [req, resp] = await Promise.all([
        donationRequestService.getRequestById(requestId),
        donationRequestService
          .getRequestResponses(requestId)
          .catch(() => [] as DonationResponse[]),
      ]);
      setRequest(req as BloodDonationRequest);
      setResponses(resp);
    } catch (err) {
      console.error('Error loading request:', err);
      setError('Failed to load request details.');
    } finally {
      setLoading(false);
    }
  }, [requestId]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleComplete = async (responseId: string) => {
    setActionError(null);
    try {
      await donationRequestService.completeResponse(responseId);
      await load();
    } catch (err) {
      console.error(err);
      setActionError('Could not mark this response completed.');
    }
  };

  const handleCancel = async () => {
    if (!requestId) return;
    setActionError(null);
    try {
      await donationRequestService.cancelRequest(requestId);
      await load();
    } catch (err) {
      console.error(err);
      setActionError('Could not cancel this request.');
    } finally {
      setShowCancelConfirm(false);
    }
  };

  const ownerEmail = (response: DonationResponse): string =>
    response.owner_email ?? 'unknown';

  const dogName = (response: DonationResponse): string =>
    ((response.dog?.name as string | undefined) ?? 'Dog');

  const accepted = responses.filter(
    (r) => r.status === ResponseStatus.ACCEPTED || r.status === ResponseStatus.COMPLETED
  );
  const declined = responses.filter((r) => r.status === ResponseStatus.DECLINED);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-blue border-r-transparent"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !request) {
    return (
      <DashboardLayout>
        <div className="p-8">
          <div className="card p-6 text-red-700">{error ?? 'Request not found.'}</div>
        </div>
      </DashboardLayout>
    );
  }

  const canCancel =
    request.status === RequestStatus.OPEN || request.status === RequestStatus.EXPIRED;

  const ResponseCard: React.FC<{ response: DonationResponse }> = ({ response }) => (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 py-4 first:pt-0 last:pb-0 border-b border-gray-100 last:border-0">
      <div className="min-w-0">
        <h4 className="font-medium text-text-dark">
          🐕 {dogName(response)}{' '}
          <span className="text-xs text-text-light font-normal">
            ({(response.dog?.breed as string) || 'mixed breed'})
          </span>
        </h4>
        <p className="text-sm text-text-light truncate">
          Owner: {ownerEmail(response)}
        </p>
        {response.response_message && (
          <p className="text-sm text-text-dark mt-1 italic">
            “{response.response_message}”
          </p>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <a
          href={`mailto:${ownerEmail(response)}?subject=Blood donation for your request`}
          className="text-primary-blue hover:text-primary-blue-dark text-sm font-medium"
        >
          ✉️ Contact
        </a>
        {response.status === ResponseStatus.ACCEPTED && (
          <Button onClick={() => void handleComplete(response.id)}>Mark Completed</Button>
        )}
        {response.status === ResponseStatus.COMPLETED && (
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
            Completed ✅
          </span>
        )}
      </div>
    </div>
  );

  return (
    <DashboardLayout>
      <div className="p-4 md:p-8 max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-6">
          <div>
            <button
              onClick={() => navigate('/clinic')}
              className="text-sm text-text-light hover:text-text-dark mb-2"
            >
              ← Back to dashboard
            </button>
            <h1 className="text-2xl font-bold text-text-dark mb-1">
              {request.blood_type_needed
                ? `Request: ${request.blood_type_needed.replace(/_/g, ' ')}`
                : 'Request: Any blood type'}
            </h1>
            <p className="text-text-light">
              {request.volume_ml} ml · needed by{' '}
              {new Date(request.needed_by_date).toLocaleDateString()} ·{' '}
              <span className="font-semibold">{request.status}</span>
            </p>
          </div>

          {canCancel && !showCancelConfirm && (
            <Button variant="secondary" onClick={() => setShowCancelConfirm(true)}>
              Cancel Request
            </Button>
          )}
          {showCancelConfirm && (
            <div className="card p-4 bg-red-50 border border-red-200">
              <p className="text-sm text-red-700 mb-3">Cancel this request? Donors will no longer see it.</p>
              <div className="flex gap-2">
                <Button onClick={() => void handleCancel()}>Yes, cancel it</Button>
                <Button variant="secondary" onClick={() => setShowCancelConfirm(false)}>
                  Keep
                </Button>
              </div>
            </div>
          )}
        </div>

        {actionError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-input text-red-700">
            {actionError}
          </div>
        )}

        {request.patient_info && (
          <div className="card mb-6">
            <h2 className="font-semibold text-text-dark mb-2">Patient Info</h2>
            <p className="text-sm text-text-dark">{request.patient_info}</p>
          </div>
        )}

        {/* Accepted / Completed */}
        <section className="mb-8">
          <h2 className="section-title mb-4">
            Accepted Donors ({accepted.length})
          </h2>
          <div className="card px-6 py-4">
            {accepted.length === 0 ? (
              <p className="text-text-light">No accepted responses yet.</p>
            ) : (
              accepted.map((r) => <ResponseCard key={r.id} response={r} />)
            )}
          </div>
        </section>

        {/* Declined */}
        {declined.length > 0 && (
          <section>
            <h2 className="section-title mb-4">Declined ({declined.length})</h2>
            <div className="card px-6 py-4 opacity-75">
              {declined.map((r) => (
                <ResponseCard key={r.id} response={r} />
              ))}
            </div>
          </section>
        )}
      </div>
    </DashboardLayout>
  );
};

export default ClinicRequestDetailPage;
