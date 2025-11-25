/**
 * Dog Owner Dashboard
 * Main dashboard for dog owners
 */

import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/common/Button';

export const DonorDashboard: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-base-off-white">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-text-dark">
            Dog Owner Dashboard
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-text-light">{user?.email}</span>
            <Button variant="secondary" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="card">
            <h2 className="section-title">My Dogs</h2>
            <p className="text-text-light mb-4">
              Manage your dog profiles and donation history
            </p>
            <Button>View Dogs</Button>
          </div>

          <div className="card">
            <h2 className="section-title">Active Requests</h2>
            <p className="text-text-light mb-4">
              Browse donation requests that match your dogs
            </p>
            <Button>Browse Requests</Button>
          </div>

          <div className="card">
            <h2 className="section-title">My Responses</h2>
            <p className="text-text-light mb-4">
              Track your donation responses and appointments
            </p>
            <Button>View Responses</Button>
          </div>
        </div>

        <div className="mt-8 card">
          <h2 className="section-title">Welcome to Hector!</h2>
          <p className="text-text-light">
            This is your dog owner dashboard. Here you can manage your dogs' profiles,
            browse blood donation requests from clinics, and respond to requests when
            your dogs are eligible.
          </p>
        </div>
      </main>
    </div>
  );
};

export default DonorDashboard;
