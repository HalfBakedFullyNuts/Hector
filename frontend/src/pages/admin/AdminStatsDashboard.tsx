/**
 * Admin Statistics Dashboard (T-910)
 * KPI cards + simple CSS bar visuals (no chart library)
 */

import React, { useEffect, useState } from 'react';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { adminService } from '../../services/adminService';
import type { PlatformStatistics } from '../../types/admin';

function KpiCard({ label, value, hint }: { label: string; value: number; hint?: string }) {
  return (
    <div className="card">
      <h3 className="text-sm font-medium text-text-light mb-2">{label}</h3>
      <p className="text-3xl font-bold text-text-dark">{value}</p>
      {hint && <p className="text-xs text-text-light mt-1">{hint}</p>}
    </div>
  );
}

/** Pure-CSS horizontal bar list */
function BarList({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data);
  const max = Math.max(1, ...entries.map(([, v]) => v));

  if (entries.length === 0) {
    return <p className="text-sm text-text-light">No data yet.</p>;
  }

  return (
    <ul className="space-y-2">
      {entries.map(([key, value]) => (
        <li key={key} className="flex items-center gap-3">
          <span className="w-28 shrink-0 text-sm text-text-dark capitalize truncate">
            {key.replace(/_/g, ' ').toLowerCase()}
          </span>
          <div className="flex-1 h-4 bg-base-off-white rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-blue rounded-full"
              style={{ width: `${Math.round((value / max) * 100)}%` }}
              aria-label={`${key}: ${value}`}
            />
          </div>
          <span className="text-sm font-semibold text-text-dark w-8 text-right">{value}</span>
        </li>
      ))}
    </ul>
  );
}

export const AdminStatsDashboard: React.FC = () => {
  const [stats, setStats] = useState<PlatformStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    adminService
      .getStats()
      .then(setStats)
      .catch(() => setError('Failed to load platform statistics.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout>
      <div className="p-4 md:p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-dark mb-2">Platform Statistics</h1>
          <p className="text-text-light">Health of the network at a glance.</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-input text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-blue border-r-transparent"></div>
            <p className="ml-4 text-text-light">Loading statistics...</p>
          </div>
        ) : stats ? (
          <div className="space-y-8">
            {/* KPI cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
              <KpiCard label="Total Users" value={stats.total_users} />
              <KpiCard label="Donor Dogs" value={stats.total_dogs} />
              <KpiCard
                label="Clinics"
                value={stats.total_clinics}
                hint={`${stats.approved_clinics} approved · ${stats.pending_clinics} pending`}
              />
              <KpiCard
                label="Successful Donations"
                value={stats.successful_donations_this_month}
                hint="This month"
              />
            </div>

            {/* Breakdowns */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="card">
                <h3 className="font-semibold text-text-dark mb-4">Users by role</h3>
                <BarList data={stats.users_by_role} />
              </div>
              <div className="card">
                <h3 className="font-semibold text-text-dark mb-4">Requests by status</h3>
                <BarList data={stats.requests_by_status} />
              </div>
              <div className="card">
                <h3 className="font-semibold text-text-dark mb-4">Responses by status</h3>
                <BarList data={stats.responses_by_status} />
              </div>
            </div>

            <p className="text-xs text-text-light">
              Total requests: {stats.total_requests} · Total responses:{' '}
              {stats.total_responses}
            </p>
          </div>
        ) : null}
      </div>
    </DashboardLayout>
  );
};

export default AdminStatsDashboard;
