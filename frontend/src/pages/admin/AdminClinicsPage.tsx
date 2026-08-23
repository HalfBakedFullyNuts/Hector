/**
 * Admin Clinic Approval (T-909)
 * Pending queue with approve/reject actions
 */

import React, { useCallback, useEffect, useState } from 'react';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Button } from '../../components/common/Button';
import { adminService } from '../../services/adminService';
import type { Clinic } from '../../types/clinic';

export const AdminClinicsPage: React.FC = () => {
  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [rejectTarget, setRejectTarget] = useState<Clinic | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // Admin listing shows all clinics; public endpoint hides inactive ones.
      setClinics(await adminService.listAllClinics());
    } catch (err) {
      console.error(err);
      setError('Failed to load clinics.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const handleApprove = async (clinic: Clinic) => {
    setBusyId(clinic.id);
    try {
      await adminService.approveClinic(clinic.id, 'Approved via admin panel');
      await load();
    } catch (err) {
      console.error(err);
      setError('Could not approve this clinic.');
    } finally {
      setBusyId(null);
    }
  };

  const handleReject = async () => {
    if (!rejectTarget) return;
    setBusyId(rejectTarget.id);
    try {
      await adminService.rejectClinic(
        rejectTarget.id,
        rejectionReason || 'Rejected by admin'
      );
      setRejectTarget(null);
      setRejectionReason('');
      await load();
    } catch (err) {
      console.error(err);
      setError('Could not reject this clinic.');
    } finally {
      setBusyId(null);
    }
  };

  const pending = clinics.filter((c) => !c.is_approved);
  const approved = clinics.filter((c) => c.is_approved);

  const ClinicRow: React.FC<{ clinic: Clinic; isPending: boolean }> = ({
    clinic,
    isPending,
  }) => (
    <div className="py-4 first:pt-0 last:pb-0 border-b border-gray-100 last:border-0 flex flex-col md:flex-row md:items-center justify-between gap-3">
      <div className="min-w-0">
        <h4 className="font-medium text-text-dark">
          {isPending && <span className="text-orange-500 mr-1">⏳</span>}
          {clinic.name}
        </h4>
        <p className="text-sm text-text-light truncate">
          {clinic.address}, {clinic.city} · {clinic.email} ·{' '}
          {new Date(clinic.created_at).toLocaleDateString()}
        </p>
      </div>
      {isPending ? (
        <div className="flex gap-2 shrink-0">
          <Button onClick={() => void handleApprove(clinic)} disabled={busyId === clinic.id}>
            {busyId === clinic.id ? '…' : 'Approve'}
          </Button>
          <Button variant="secondary" onClick={() => setRejectTarget(clinic)}>
            Reject
          </Button>
        </div>
      ) : (
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 w-fit shrink-0">
          Approved
        </span>
      )}
    </div>
  );

  return (
    <DashboardLayout>
      <div className="p-4 md:p-8 max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-dark mb-2">Clinic Approvals</h1>
          <p className="text-text-light">Only approved clinics can post requests.</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-input text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-blue border-r-transparent"></div>
            <p className="ml-4 text-text-light">Loading clinics...</p>
          </div>
        ) : (
          <>
            <section className="mb-8">
              <h2 className="section-title mb-4">Pending ({pending.length})</h2>
              <div className="card px-6 py-4">
                {pending.length === 0 ? (
                  <p className="text-text-light">No pending applications. 🎉</p>
                ) : (
                  pending.map((clinic) => (
                    <ClinicRow key={clinic.id} clinic={clinic} isPending />
                  ))
                )}
              </div>
            </section>

            <section>
              <h2 className="section-title mb-4">Approved ({approved.length})</h2>
              <div className="card px-6 py-4">
                {approved.length === 0 ? (
                  <p className="text-text-light">No approved clinics yet.</p>
                ) : (
                  approved.map((clinic) => (
                    <ClinicRow key={clinic.id} clinic={clinic} isPending={false} />
                  ))
                )}
              </div>
            </section>
          </>
        )}

        {/* Reject confirmation modal */}
        {rejectTarget && (
          <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center p-4 z-50">
            <div className="card max-w-md w-full p-6">
              <h3 className="text-lg font-semibold text-text-dark mb-2">
                Reject “{rejectTarget.name}”?
              </h3>
              <p className="text-sm text-text-light mb-4">
                The clinic will be hidden from the platform. Please give a reason.
              </p>
              <textarea
                className="input w-full mb-4"
                rows={3}
                placeholder="e.g., Could not verify credentials"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
              />
              <div className="flex gap-3 justify-end">
                <Button variant="secondary" onClick={() => setRejectTarget(null)}>
                  Cancel
                </Button>
                <Button onClick={() => void handleReject()} disabled={busyId !== null}>
                  Confirm Reject
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default AdminClinicsPage;
