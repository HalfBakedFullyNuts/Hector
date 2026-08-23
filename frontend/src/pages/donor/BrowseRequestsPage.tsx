/**
 * Browse Donation Requests (T-906, T-1006, T-1004)
 * Filters persist in URL; compatibility badges for my dogs
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { DonationRequestCard } from '../../components/common/DonationRequestCard';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Button } from '../../components/common/Button';
import { dogService } from '../../services/dogService';
import { donationRequestService } from '../../services/donationRequestService';
import type { CompatibleRequest, DonationRequestWithDistance } from '../../types/donationRequest';
import type { DogProfile } from '../../types/dog';
import { RequestStatus, RequestUrgency } from '../../types/donationRequest';

export const BrowseRequestsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [requests, setRequests] = useState<DonationRequestWithDistance[]>([]);
  const [compatibleIds, setCompatibleIds] = useState<Set<string>>(new Set());
  const [, setDogs] = useState<DogProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters persisted in URL query params (T-1006)
  const urgency = searchParams.get('urgency') ?? '';
  const city = searchParams.get('city') ?? '';
  const latParam = searchParams.get('lat');
  const lngParam = searchParams.get('lng');
  const maxKm = searchParams.get('max_distance_km') ?? '';

  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next, { replace: true });
  };

  const fetchCompatibleIds = useCallback(async (myDogs: DogProfile[]) => {
    // Mark requests compatible with any of my available dogs (bounded)
    const ids = new Set<string>();
    for (const dog of myDogs.slice(0, 5)) {
      if (!dog.is_available_for_donation || !dog.is_active) continue;
      try {
        const compatible: CompatibleRequest[] =
          await donationRequestService.getCompatibleRequests(dog.id);
        compatible.forEach((req) => ids.add(req.id));
      } catch {
        // Eligibility errors (e.g., recently donated) simply skip this dog
      }
    }
    setCompatibleIds(ids);
  }, []);

  const loadRequests = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setRequests(
        await donationRequestService.getRequests({
          status: RequestStatus.OPEN,
          urgency: urgency || undefined,
          city: city || undefined,
          lat: latParam ? Number(latParam) : undefined,
          lng: lngParam ? Number(lngParam) : undefined,
          max_distance_km: maxKm ? Number(maxKm) : undefined,
          limit: 50,
        })
      );
    } catch (err) {
      console.error('Error loading requests:', err);
      setError('Failed to load donation requests.');
    } finally {
      setLoading(false);
    }
  }, [urgency, city, latParam, lngParam, maxKm]);

  useEffect(() => {
    void loadRequests();
  }, [loadRequests]);

  useEffect(() => {
    dogService
      .getMyDogs(20)
      .then((myDogs) => {
        void fetchCompatibleIds(myDogs);
      })
      .catch(() => setDogs([]));
  }, [fetchCompatibleIds]);

  const hasFilters = Boolean(urgency || city || maxKm || latParam);

  const clearFilters = () => {
    setSearchParams(new URLSearchParams(), { replace: true });
  };

  const locationHint = useMemo(
    () =>
      'Set your location once on this page to sort by distance.',
    []
  );

  return (
    <DashboardLayout>
      <div className="p-4 md:p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-dark mb-2">
            Browse Blood Requests
          </h1>
          <p className="text-text-light">{locationHint}</p>
        </div>

        {/* Filters */}
        <div className="card mb-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          <Select
            label="Urgency"
            options={[
              { value: '', label: 'All' },
              { value: RequestUrgency.CRITICAL, label: 'Critical' },
              { value: RequestUrgency.URGENT, label: 'Urgent' },
              { value: RequestUrgency.ROUTINE, label: 'Routine' },
            ]}
            value={urgency}
            onChange={(e) => setFilter('urgency', e.target.value)}
          />
          <Input
            label="Clinic city"
            placeholder="e.g., Berlin"
            value={city}
            onChange={(e) => setFilter('city', e.target.value)}
          />
          <>
            <label className="block text-sm font-medium text-text-dark mb-1">
              Within (km){' '}
              {latParam && lngParam ? '' : '(requires coordinates below)'}
            </label>
            <input
              type="number"
              min={1}
              max={2000}
              className="input w-full"
              value={maxKm}
              onChange={(e) => setFilter('max_distance_km', e.target.value)}
              disabled={!latParam || !lngParam}
            />
          </>
          <div>
            <p className="block text-sm font-medium text-text-dark mb-1">My location</p>
            <Button
              variant="secondary"
              onClick={() => {
                navigator.geolocation?.getCurrentPosition((pos) => {
                  const next = new URLSearchParams(searchParams);
                  next.set('lat', String(pos.coords.latitude));
                  next.set('lng', String(pos.coords.longitude));
                  setSearchParams(next, { replace: true });
                });
              }}
              fullWidth
            >
              📍 {latParam && lngParam ? 'Location set ✓' : 'Use my location'}
            </Button>
          </div>
        </div>

        {/* Clear filters */}
        {hasFilters && (
          <button
            onClick={clearFilters}
            className="text-primary-blue text-sm font-medium mb-6 hover:underline"
          >
            ✕ Clear all filters
          </button>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-input text-red-700">
            {error}
          </div>
        )}

        {/* Results */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-blue border-r-transparent"></div>
            <p className="ml-4 text-text-light">Loading requests...</p>
          </div>
        ) : requests.length === 0 ? (
          <div className="card text-center py-12">
            <span className="text-6xl mb-4 block">🔍</span>
            <h3 className="text-xl font-semibold text-text-dark mb-2">
              No matching requests
            </h3>
            <p className="text-text-light">Try adjusting or clearing your filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {requests.map((request) => (
              <div key={request.id} className="relative">
                {compatibleIds.has(request.id) && (
                  <span className="absolute -top-2 -right-2 z-10 px-3 py-1 rounded-full text-xs font-bold bg-green-600 text-white shadow">
                    ✓ Compatible with my dog
                  </span>
                )}
                <DonationRequestCard
                  request={request}
                  showOfferButton
                  onOffer={() => navigate(`/owner/requests/${request.id}/respond`)}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default BrowseRequestsPage;
