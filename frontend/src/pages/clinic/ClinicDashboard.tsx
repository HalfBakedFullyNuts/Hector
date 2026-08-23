/**
 * Clinic Dashboard (T-901)
 * Lists the clinic's donation requests with status badges and response counts
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Button } from '../../components/common/Button';
import { donationRequestService } from '../../services/donationRequestService';
import type { ClinicRequest } from '../../types/donationRequest';
import { RequestStatus, RequestUrgency } from '../../types/donationRequest';

function urgencyBadge(urgency: RequestUrgency): string {
  switch (urgency) {
    case RequestUrgency.CRITICAL:
      return 'bg-red-100 text-red-800 border border-red-200';
    case RequestUrgency.URGENT:
      return 'bg-orange-100 text-orange-800 border border-orange-200';
    default:
      return 'bg-blue-100 text-blue-800 border border-blue-200';
  }
}

function statusBadge(status: RequestStatus): string {
  switch (status) {
    case RequestStatus.OPEN:
      return 'bg-green-100 text-green-800 border border-green-200';
    case RequestStatus.FULFILLED:
      return 'bg-indigo-100 text-indigo-800 border border-indigo-200';
    case RequestStatus.CANCELLED:
      return 'bg-gray-200 text-gray-600 border border-gray-300';
    default:
      return 'bg-yellow-50 text-yellow-700 border border-yellow-200';
  }
}

export const ClinicDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [requests, setRequests] = useState<ClinicRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadRequests();
  }, []);

  const loadRequests = async () => {
    try {
      setLoading(true);
      setError(null);
      setRequests(await donationRequestService.getMyClinicRequests());
    } catch (err) {
      console.error('Error loading clinic requests:', err);
      setError('Failed to load requests. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-4 md:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-text-dark mb-2">
              Clinic Dashboard
            </h1>
            <p className="text-text-light">Manage your blood donation requests.</p>
          </div>
          <Button onClick={() => navigate('/clinic/requests/new')} disabled={loading}>
            + Create New Request
          </Button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-input text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-blue border-r-transparent"></div>
            <p className="ml-4 text-text-light">Loading requests...</p>
          </div>
        ) : requests.length === 0 ? (
          <div className="card text-center py-12">
            <span className="text-6xl mb-4 block">🩸</span>
            <h3 className="text-xl font-semibold text-text-dark mb-2">
              No requests yet
            </h3>
            <p className="text-text-light mb-4">
              Post your first blood donation request to reach local donors.
            </p>
            <Button onClick={() => navigate('/clinic/requests/new')}>
              Create Your First Request
            </Button>
          </div>
        ) : (
          <div className="card overflow-x-auto">
            <table className="w-full text-left min-w-[640px]">
              <thead>
                <tr className="border-b border-gray-200 text-xs uppercase tracking-wide text-text-light">
                  <th className="py-3 px-4">Blood Type</th>
                  <th className="py-3 px-4">Urgency</th>
                  <th className="py-3 px-4">Volume</th>
                  <th className="py-3 px-4">Needed By</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Responses</th>
                  <th className="py-3 px-4" aria-label="actions" />
                </tr>
              </thead>
              <tbody>
                {requests.map((request) => (
                  <tr
                    key={request.id}
                    className="border-b border-gray-100 last:border-0 hover:bg-base-off-white cursor-pointer"
                    onClick={() => navigate(`/clinic/requests/${request.id}`)}
                  >
                    <td className="py-3 px-4 font-medium text-text-dark">
                      {request.blood_type_needed
                        ? request.blood_type_needed.replace(/_/g, ' ')
                        : 'Any'}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${urgencyBadge(request.urgency)}`}>
                        {request.urgency}
                      </span>
                    </td>
                    <td className="py-3 px-4">{request.volume_ml} ml</td>
                    <td className="py-3 px-4">
                      {new Date(request.needed_by_date).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusBadge(request.status)}`}>
                        {request.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold">{request.response_count}</td>
                    <td className="py-3 px-4 text-primary-blue font-medium">View →</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default ClinicDashboard;
