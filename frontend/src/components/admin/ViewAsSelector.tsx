/**
 * View As Selector Component
 * Allows admins to select a role to view the app as
 */

import React from 'react';
import { useViewAs } from '../../contexts/ViewAsContext';
import { UserRole } from '../../types/auth';

const roleLabels: Record<UserRole, string> = {
  [UserRole.ADMIN]: 'Admin',
  [UserRole.CLINIC_STAFF]: 'Clinic Staff',
  [UserRole.DOG_OWNER]: 'Dog Owner',
};

export const ViewAsSelector: React.FC = () => {
  const { viewingAs, setViewAs, canUseViewAs } = useViewAs();

  if (!canUseViewAs) return null;

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="view-as-select" className="text-sm text-text-light">
        View as:
      </label>
      <select
        id="view-as-select"
        value={viewingAs || ''}
        onChange={(e) => setViewAs(e.target.value as UserRole || null)}
        className="px-3 py-1.5 text-sm border border-border rounded-input bg-white focus:outline-none focus:ring-2 focus:ring-primary-blue"
      >
        <option value="">Admin (default)</option>
        {Object.values(UserRole).map((role) => (
          <option key={role} value={role}>
            {roleLabels[role]}
          </option>
        ))}
      </select>
    </div>
  );
};
