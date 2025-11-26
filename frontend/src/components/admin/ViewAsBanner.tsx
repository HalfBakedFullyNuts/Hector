/**
 * View As Banner Component
 * Shows a warning banner when viewing as another role
 */

import React from 'react';
import { useViewAs } from '../../contexts/ViewAsContext';
import { UserRole } from '../../types/auth';

const roleLabels: Record<UserRole, string> = {
  [UserRole.ADMIN]: 'Admin',
  [UserRole.CLINIC_STAFF]: 'Clinic Staff',
  [UserRole.DOG_OWNER]: 'Dog Owner',
};

export const ViewAsBanner: React.FC = () => {
  const { isViewingAs, viewingAs, clearViewAs } = useViewAs();

  if (!isViewingAs || !viewingAs) return null;

  return (
    <div className="bg-amber-500 text-amber-950 px-4 py-2 text-sm flex items-center justify-between">
      <div className="flex items-center gap-2">
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
          />
        </svg>
        <span>
          <strong>View As Mode:</strong> You are viewing the app as{' '}
          <strong>{roleLabels[viewingAs]}</strong>
        </span>
      </div>
      <button
        onClick={clearViewAs}
        className="px-3 py-1 bg-amber-700 hover:bg-amber-800 text-white rounded-button text-xs font-medium transition-colors"
      >
        Exit View As
      </button>
    </div>
  );
};
