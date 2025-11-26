import React from 'react';
import type {
  BloodDonationRequest,
} from '../../types/donationRequest';
import { RequestUrgency } from '../../types/donationRequest';
import { Button } from './Button';

interface DonationRequestCardProps {
  request: BloodDonationRequest;
  onClick?: () => void;
  showOfferButton?: boolean;
  onOffer?: () => void;
}

export const DonationRequestCard: React.FC<DonationRequestCardProps> = ({
  request,
  onClick,
  showOfferButton = false,
  onOffer,
}) => {
  // Format blood type for display
  const bloodTypeDisplay = request.blood_type_needed
    ? request.blood_type_needed.replace('DEA_', 'DEA ').replace(/_/g, ' ')
    : 'Any Type';

  // Get urgency color and label
  const urgencyConfig = getUrgencyConfig(request.urgency);

  // Format date
  const neededByDate = new Date(request.needed_by_date);
  const daysUntilNeeded = Math.ceil(
    (neededByDate.getTime() - new Date().getTime()) / (24 * 60 * 60 * 1000)
  );

  return (
    <div
      className={`card hover: shadow - lg transition - shadow ${onClick ? 'cursor-pointer' : ''
        } `}
      onClick={onClick && !showOfferButton ? onClick : undefined}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-text-dark mb-1">
            {request.clinic?.name || 'Clinic'}
          </h3>
          <div className="flex items-center gap-2 text-sm text-text-light">
            <span>📍</span>
            <span>
              {request.clinic?.city || 'Location'}
            </span>
          </div>
        </div>
        <div
          className={`px - 3 py - 1 rounded - full text - xs font - medium ${urgencyConfig.className} `}
        >
          {urgencyConfig.icon} {urgencyConfig.label}
        </div>
      </div>

      {/* Blood Type and Volume */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-text-light mb-1">Blood Type Needed</p>
          <div className="flex items-center gap-2">
            <span className="text-lg">🩸</span>
            <p className="text-sm font-medium text-text-dark">{bloodTypeDisplay}</p>
          </div>
        </div>
        <div>
          <p className="text-xs text-text-light mb-1">Volume</p>
          <p className="text-sm font-medium text-text-dark">
            {request.volume_ml} ml
          </p>
        </div>
      </div>

      {/* Patient Details */}
      {request.patient_breed && (
        <div className="mb-4">
          <p className="text-xs text-text-light mb-1">Patient</p>
          <p className="text-sm font-medium text-text-dark">
            {request.patient_breed}
          </p>
        </div>
      )}

      {/* Reason for Transfusion */}
      {request.reason_for_transfusion && (
        <div className="mb-4">
          <p className="text-xs text-text-light mb-1">Reason</p>
          <p className="text-sm text-text-dark line-clamp-2">
            {request.reason_for_transfusion}
          </p>
        </div>
      )}

      {/* Needed By Date */}
      <div
        className={`p - 3 rounded - input text - sm mb - 4 ${daysUntilNeeded <= 2
          ? 'bg-red-50 border border-red-200 text-red-700'
          : daysUntilNeeded <= 7
            ? 'bg-yellow-50 border border-yellow-200 text-yellow-700'
            : 'bg-blue-50 border border-blue-200 text-blue-700'
          } `}
      >
        <span className="font-medium">
          Needed by: {formatDate(request.needed_by_date)}
        </span>
        <p className="text-xs mt-1">
          {daysUntilNeeded === 0
            ? 'Needed today'
            : daysUntilNeeded === 1
              ? 'Needed tomorrow'
              : `${daysUntilNeeded} days from now`}
        </p>
      </div>

      {/* Action Button */}
      {showOfferButton && onOffer && (
        <Button onClick={onOffer} fullWidth>
          Offer to Help
        </Button>
      )}
    </div>
  );
};

// Helper functions
function getUrgencyConfig(urgency: RequestUrgency): {
  label: string;
  icon: string;
  className: string;
} {
  switch (urgency) {
    case RequestUrgency.CRITICAL:
      return {
        label: 'Critical',
        icon: '🚨',
        className: 'bg-red-100 text-red-800 border border-red-200',
      };
    case RequestUrgency.URGENT:
      return {
        label: 'Urgent',
        icon: '⚠️',
        className: 'bg-orange-100 text-orange-800 border border-orange-200',
      };
    case RequestUrgency.ROUTINE:
      return {
        label: 'Routine',
        icon: 'ℹ️',
        className: 'bg-blue-100 text-blue-800 border border-blue-200',
      };
    default:
      return {
        label: 'Unknown',
        icon: '❓',
        className: 'bg-gray-100 text-gray-800 border border-gray-200',
      };
  }
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

export default DonationRequestCard;
