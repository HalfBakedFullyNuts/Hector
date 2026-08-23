/**
 * My Responses (T-602)
 * Lists all of the owner's responses with request and clinic context
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import {
  donationRequestService,
} from '../../services/donationRequestService';
import type { DonationResponse } from '../../types/donationRequest';
import { ResponseStatus } from '../../types/donationRequest';

function statusBadge(status: ResponseStatus): string {
  switch (status) {
    case ResponseStatus.ACCEPTED:
      return 'bg-green-100 text-green-800 border border-green-200';
    case ResponseStatus.DECLINED:
      return 'bg-gray-200 text-gray-600 border border-gray-300';
    default:
      return 'bg-indigo-100 text-indigo-800 border border-indigo-200';
  }
}

export const MyResponsesPage: React.FC = () => {
  const navigate = useNavigate();
  const [responses, setResponses] = useState<DonationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    donationRequestService
      .getMyResponses()
      .then(setResponses)
      .catch(() => setError('Failed to load your responses.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout>
      <div className="p-4 md:p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-dark mb-2">My Responses</h1>
          <p className="text-text-light">Your donation history across all requests.</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-input text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-blue border-r-transparent"></div>
            <p className="ml-4 text-text-light">Loading...</p>
          </div>
        ) : responses.length === 0 ? (
          <div className="card text-center py-12">
            <span className="text-6xl mb-4 block">📋</span>
            <h3 className="text-xl font-semibold text-text-dark mb-2">No responses yet</h3>
            <p className="text-text-light mb-4">
              Browse open requests to make your first offer.
            </p>
            <button
              onClick={() => navigate('/owner/requests')}
              className="text-primary-blue font-medium hover:underline"
            >
              Browse requests →
            </button>
          </div>
        ) : (
          <div className="card divide-y divide-gray-100">
            {responses.map((response) => {
              const clinic =
                (response.request?.clinic as { name?: string } | null | undefined)?.name ??
                'Clinic';
              return (
                <div
                  key={response.id}
                  className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="min-w-0">
                    <h4 className="font-medium text-text-dark">
                      {(response.dog?.name as string) ?? 'Dog'} →{' '}
                      {(response.request?.blood_type_needed as string | null)
                        ?.replace(/_/g, ' ') ?? 'Any type'}{' '}
                      @ {clinic}
                    </h4>
                    <p className="text-xs text-text-light mt-1">
                      {new Date(response.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium w-fit ${statusBadge(
                      response.status
                    )}`}
                  >
                    {response.status}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default MyResponsesPage;
