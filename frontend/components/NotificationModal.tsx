'use client';

import { useState, useEffect } from 'react';
import { X, Bell, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';

interface Notification {
  id: string;
  file_name: string;
  status: string;
  updated_at: string;
  error_message?: string;
}

export function NotificationModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const { data: updates = [], refetch } = useQuery({
    queryKey: ['job-updates', lastChecked?.toISOString()],
    queryFn: async () => {
      try {
        const since = lastChecked?.toISOString();
        const response = await apiClient.getJobUpdates(since);
        return (response.data || []) as Notification[];
      } catch (error) {
        console.error('Failed to fetch job updates:', error);
        return [] as Notification[];
      }
    },
    refetchInterval: 20000, // Poll every 20 seconds
    enabled: isOpen, // Only poll when modal is open
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      default:
        return <Info className="h-5 w-5 text-blue-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processed':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  return (
    <>
      {/* Notification Bell */}
      <button
        onClick={() => {
          setIsOpen(true);
          setLastChecked(new Date());
          refetch();
        }}
        className="relative p-2 hover:bg-gray-100 rounded-full transition-colors"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5 text-gray-600" />
        {updates.length > 0 && (
          <span className="absolute top-0 right-0 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {updates.length}
          </span>
        )}
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[80vh] flex flex-col">
            {/* Header */}
            <div className="flex justify-between items-center p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Notifications</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                aria-label="Close"
              >
                <X className="h-5 w-5 text-gray-600" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {updates.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Bell className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>No new notifications</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {updates.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 rounded-lg border ${getStatusColor(notification.status)}`}
                    >
                      <div className="flex items-start gap-3">
                        {getStatusIcon(notification.status)}
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">
                            {notification.file_name}
                          </p>
                          <p className="text-sm text-gray-600 mt-1">
                            Status: {notification.status}
                          </p>
                          {notification.error_message && (
                            <p className="text-sm text-red-600 mt-1">
                              {notification.error_message}
                            </p>
                          )}
                          <p className="text-xs text-gray-500 mt-2">
                            {new Date(notification.updated_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

