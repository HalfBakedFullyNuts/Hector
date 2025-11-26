/**
 * Dog Profile Card Component
 * Displays dog information in a card format
 */

import React from 'react';
import type { DogProfile } from '../../types/dog';

interface DogProfileCardProps {
  dog: DogProfile;
  onClick?: () => void;
}

export const DogProfileCard: React.FC<DogProfileCardProps> = ({ dog, onClick }) => {
  // Calculate age
  const ageYears = dog.age_years || calculateAge(dog.date_of_birth);

  // Determine eligibility status
  const eligibilityStatus = getEligibilityStatus(dog, ageYears);

  // Format blood type for display
  const bloodTypeDisplay = dog.blood_type
    ? dog.blood_type.replace('DEA_', 'DEA ').replace(/_/g, ' ')
    : 'Unknown';

  return (
    <div
      onClick={onClick}
      className={`card hover:shadow-lg transition-shadow ${onClick ? 'cursor-pointer' : ''
        }`}
    >
      {/* Header with name and availability */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-text-dark mb-1">
            {dog.name}
          </h3>
          <p className="text-sm text-text-light">{dog.breed}</p>
        </div>
        <div
          className={`px-3 py-1 rounded-full text-xs font-medium ${dog.is_active
            ? 'bg-primary-green text-green-800'
            : 'bg-gray-200 text-gray-600'
            }`}
        >
          {dog.is_active ? 'Available' : 'Unavailable'}
        </div>
      </div>

      {/* Dog Photo Placeholder */}
      <div className="w-full h-40 bg-base-off-white rounded-input mb-4 flex items-center justify-center">
        <span className="text-6xl">🐕</span>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-text-light mb-1">Age</p>
          <p className="text-sm font-medium text-text-dark">
            {ageYears} {ageYears === 1 ? 'year' : 'years'}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-light mb-1">Weight</p>
          <p className="text-sm font-medium text-text-dark">{dog.weight_kg} kg</p>
        </div>
        <div>
          <p className="text-xs text-text-light mb-1">Blood Type</p>
          <p className="text-sm font-medium text-text-dark">{bloodTypeDisplay}</p>
        </div>
        <div>
          <p className="text-xs text-text-light mb-1">Last Donation</p>
          <p className="text-sm font-medium text-text-dark">
            {dog.last_donation_date
              ? formatDate(dog.last_donation_date)
              : 'Never'}
          </p>
        </div>
      </div>

      {/* Eligibility Status */}
      <div
        className={`p-3 rounded-input text-sm ${eligibilityStatus.eligible
          ? 'bg-green-50 border border-green-200 text-green-700'
          : 'bg-yellow-50 border border-yellow-200 text-yellow-700'
          }`}
      >
        <span className="font-medium">
          {eligibilityStatus.eligible ? '✅ Eligible' : '⚠️ Not Eligible'}
        </span>
        {!eligibilityStatus.eligible && eligibilityStatus.reason && (
          <p className="text-xs mt-1">{eligibilityStatus.reason}</p>
        )}
      </div>
    </div>
  );
};

// Helper functions
function calculateAge(dateOfBirth: string): number {
  const birthDate = new Date(dateOfBirth);
  const today = new Date();
  const ageInYears = Math.floor(
    (today.getTime() - birthDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000)
  );
  return ageInYears;
}

function getEligibilityStatus(
  dog: DogProfile,
  ageYears: number
): { eligible: boolean; reason?: string } {
  if (!dog.is_active) {
    return { eligible: false, reason: 'Marked as unavailable' };
  }

  if (dog.weight_kg < 25) {
    return { eligible: false, reason: 'Must weigh at least 25kg' };
  }

  if (ageYears < 1) {
    return { eligible: false, reason: 'Must be at least 1 year old' };
  }

  if (ageYears > 8) {
    return { eligible: false, reason: 'Must be 8 years or younger' };
  }

  if (dog.last_donation_date) {
    const lastDonation = new Date(dog.last_donation_date);
    const today = new Date();
    const weeksSince = Math.floor(
      (today.getTime() - lastDonation.getTime()) / (7 * 24 * 60 * 60 * 1000)
    );
    if (weeksSince < 8) {
      return {
        eligible: false,
        reason: `Must wait ${8 - weeksSince} more weeks since last donation`,
      };
    }
  }

  return { eligible: true };
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };
  return date.toLocaleDateString('en-US', options);
}

export default DogProfileCard;
