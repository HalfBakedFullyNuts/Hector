import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { UserRole } from '../../types/auth';

export const DevTools: React.FC = () => {
    const { devLogin, user } = useAuth();
    const [isOpen, setIsOpen] = useState(false);

    if (import.meta.env.PROD) return null;

    return (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2">
            {isOpen && (
                <div className="bg-white p-4 rounded-lg shadow-xl border border-gray-200 mb-2 w-64">
                    <h3 className="font-bold text-gray-800 mb-2">Dev Tools</h3>
                    <div className="text-xs text-gray-500 mb-4">
                        Current Role: <span className="font-mono font-bold">{user?.role || 'None'}</span>
                    </div>

                    <div className="space-y-2">
                        <p className="text-xs font-semibold text-gray-600 uppercase">Switch Role</p>
                        <button
                            onClick={() => devLogin(UserRole.DOG_OWNER)}
                            className="w-full px-3 py-2 text-sm bg-blue-50 text-blue-700 rounded hover:bg-blue-100 text-left flex items-center gap-2"
                        >
                            🐶 Dog Owner
                        </button>
                        <button
                            onClick={() => devLogin(UserRole.CLINIC_STAFF)}
                            className="w-full px-3 py-2 text-sm bg-green-50 text-green-700 rounded hover:bg-green-100 text-left flex items-center gap-2"
                        >
                            🏥 Clinic Staff
                        </button>
                        <button
                            onClick={() => devLogin(UserRole.ADMIN)}
                            className="w-full px-3 py-2 text-sm bg-purple-50 text-purple-700 rounded hover:bg-purple-100 text-left flex items-center gap-2"
                        >
                            🛡️ Admin
                        </button>
                    </div>
                </div>
            )}

            <button
                onClick={() => setIsOpen(!isOpen)}
                className="bg-gray-800 text-white p-3 rounded-full shadow-lg hover:bg-gray-700 transition-colors"
                title="Toggle Dev Tools"
            >
                🛠️
            </button>
        </div>
    );
};
