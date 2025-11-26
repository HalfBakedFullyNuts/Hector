/**
 * Dog Owner Dashboard
 * Main dashboard for dog owners to manage dogs and view donation requests
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { DogProfileCard } from '../../components/common/DogProfileCard';
import { DonationRequestCard } from '../../components/common/DonationRequestCard';
import { Button } from '../../components/common/Button';
import { dogService } from '../../services/dogService';
import { donationRequestService } from '../../services/donationRequestService';
import type { DogProfile } from '../../types/dog';
import { type BloodDonationRequest, type DonationResponse, RequestStatus } from '../../types/donationRequest';

export const DonorDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [dogs, setDogs] = useState<DogProfile[]>([]);
  const [requests, setRequests] = useState<BloodDonationRequest[]>([]);
  const [responses, setResponses] = useState<DonationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load data on mount
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all data in parallel
      const [dogsData, requestsData, responsesData] = await Promise.all([
        dogService.getMyDogs(),
        donationRequestService.getRequests({ status: 'OPEN' as RequestStatus }),
        donationRequestService.getMyResponses(),
      ]);

      setDogs(dogsData);
      setRequests(requestsData.slice(0, 6)); // Show only first 6
      setResponses(responsesData.slice(0, 5)); // Show only first 5
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-dark mb-2">
            Welcome back!
          </h1>
          <p className="text-text-light">
            Here's a summary of your donor activity and current requests.
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-input text-red-700">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-blue border-r-transparent"></div>
              <p className="mt-4 text-text-light">Loading dashboard...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="card">
                <h3 className="text-sm font-medium text-text-light mb-2">
                  My Dogs
                </h3>
                <p className="text-3xl font-bold text-text-dark">{dogs.length}</p>
                <p className="text-xs text-text-light mt-1">
                  {dogs.filter((d) => d.is_active).length} available
                </p>
              </div>

              <div className="card">
                <h3 className="text-sm font-medium text-text-light mb-2">
                  Active Requests
                </h3>
                <p className="text-3xl font-bold text-text-dark">
                  {requests.length}
                </p>
                <p className="text-xs text-text-light mt-1">In your area</p>
              </div>

              <div className="card">
                <h3 className="text-sm font-medium text-text-light mb-2">
                  My Responses
                </h3>
                <p className="text-3xl font-bold text-text-dark">
                  {responses.length}
                </p>
                <p className="text-xs text-text-light mt-1">Total submitted</p>
              </div>
            </div>

            {/* My Dogs Section */}
            <section className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="section-title">My Dogs</h2>
                <Button onClick={() => navigate('/owner/dogs/new')}>
                  + Add New Dog
                </Button>
              </div>

              {dogs.length === 0 ? (
                <div className="card text-center py-12">
                  <span className="text-6xl mb-4 block">🐕</span>
                  <h3 className="text-xl font-semibold text-text-dark mb-2">
                    No dogs yet
                  </h3>
                  <p className="text-text-light mb-4">
                    Add your first dog profile to get started with donations
                  </p>
                  <Button onClick={() => navigate('/owner/dogs/new')}>
                    Add Your First Dog
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {dogs.map((dog) => (
                    <DogProfileCard
                      key={dog.id}
                      dog={dog}
                      onClick={() => navigate(`/owner/dogs/${dog.id}`)}
                    />
                  ))}
                </div>
              )}
            </section>

            {/* Active Blood Requests Section */}
            <section className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="section-title">Active Blood Requests</h2>
                <Button
                  variant="secondary"
                  onClick={() => navigate('/owner/requests')}
                >
                  Browse All
                </Button>
              </div>

              {requests.length === 0 ? (
                <div className="card text-center py-12">
                  <span className="text-6xl mb-4 block">🩸</span>
                  <h3 className="text-xl font-semibold text-text-dark mb-2">
                    No active requests
                  </h3>
                  <p className="text-text-light">
                    Check back later for new donation opportunities
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {requests.map((request) => (
                    <DonationRequestCard
                      key={request.id}
                      request={request}
                      onClick={() => navigate(`/owner/requests/${request.id}`)}
                      showOfferButton
                      onOffer={() => navigate(`/owner/requests/${request.id}/respond`)}
                    />
                  ))}
                </div>
              )}
            </section>

            {/* Recent Responses Section */}
            {responses.length > 0 && (
              <section>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="section-title">Recent Responses</h2>
                  <Button
                    variant="secondary"
                    onClick={() => navigate('/owner/responses')}
                  >
                    View All
                  </Button>
                </div>

                <div className="card">
                  <div className="divide-y divide-gray-200">
                    {responses.map((response) => (
                      <div key={response.id} className="py-4 first:pt-0 last:pb-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-medium text-text-dark mb-1">
                              {response.dog?.name || 'Dog'}
                            </h4>
                            <p className="text-sm text-text-light">
                              Response status:{' '}
                              <span className="font-medium capitalize">
                                {response.status.toLowerCase()}
                              </span>
                            </p>
                            <p className="text-xs text-text-light mt-1">
                              {new Date(response.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <Button
                            variant="secondary"
                            onClick={() =>
                              navigate(`/owner/responses/${response.id}`)
                            }
                          >
                            View
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
};

export default DonorDashboard;
