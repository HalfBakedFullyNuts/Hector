/**
 * Admin User Management (T-908)
 */

import React, { useCallback, useEffect, useState } from 'react';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { adminService } from '../../services/adminService';
import type { UserWithCounts } from '../../types/admin';

export const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<UserWithCounts[]>([]);
  const [emailSearch, setEmailSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setUsers(
        await adminService.getUsers({
          email: emailSearch || undefined,
          role: roleFilter || undefined,
          is_active:
            activeFilter === '' ? undefined : activeFilter === 'true',
        })
      );
    } catch (err) {
      console.error(err);
      setError('Failed to load users.');
    } finally {
      setLoading(false);
    }
  }, [emailSearch, roleFilter, activeFilter]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  const handleToggle = async (user: UserWithCounts) => {
    setBusyId(user.id);
    try {
      await adminService.toggleUserActive(user.id, {
        reason: user.is_active ? 'Disabled by admin' : 'Re-enabled by admin',
      });
      await loadUsers();
    } catch (err) {
      console.error(err);
      setError('Could not toggle this account.');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-4 md:p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-text-dark mb-2">User Management</h1>
          <p className="text-text-light">Oversee platform accounts.</p>
        </div>

        {/* Filters */}
        <div className="card mb-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          <div className="lg:col-span-2">
            <Input
              label="Search by email"
              placeholder="e.g., @example.com"
              value={emailSearch}
              onChange={(e) => setEmailSearch(e.target.value)}
            />
          </div>
          <Select
            label="Role"
            options={[
              { value: '', label: 'All roles' },
              { value: 'dog_owner', label: 'Dog owner' },
              { value: 'clinic_staff', label: 'Clinic staff' },
              { value: 'admin', label: 'Admin' },
            ]}
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
          />
          <Select
            label="Status"
            options={[
              { value: '', label: 'All' },
              { value: 'true', label: 'Active' },
              { value: 'false', label: 'Disabled' },
            ]}
            value={activeFilter}
            onChange={(e) => setActiveFilter(e.target.value)}
          />
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-input text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-blue border-r-transparent"></div>
            <p className="ml-4 text-text-light">Loading users...</p>
          </div>
        ) : (
          <div className="card overflow-x-auto">
            <table className="w-full text-left min-w-[720px]">
              <thead>
                <tr className="border-b border-gray-200 text-xs uppercase tracking-wide text-text-light">
                  <th className="py-3 px-4">Email</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Dogs</th>
                  <th className="py-3 px-4">Clinics</th>
                  <th className="py-3 px-4">Joined</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4" aria-label="actions" />
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b border-gray-100 last:border-0">
                    <td className="py-3 px-4 font-medium text-text-dark">{user.email}</td>
                    <td className="py-3 px-4 capitalize">{String(user.role).replace('_', ' ')}</td>
                    <td className="py-3 px-4">{user.dog_count}</td>
                    <td className="py-3 px-4">{user.clinic_count}</td>
                    <td className="py-3 px-4">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          user.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {user.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => void handleToggle(user)}
                        disabled={busyId === user.id}
                        className="text-primary-blue hover:text-primary-blue-dark text-sm font-medium disabled:opacity-50"
                      >
                        {busyId === user.id
                          ? '…'
                          : user.is_active
                            ? 'Disable'
                            : 'Enable'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {users.length === 0 && (
              <p className="p-6 text-text-light text-center">No users match your filters.</p>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default AdminUsersPage;
