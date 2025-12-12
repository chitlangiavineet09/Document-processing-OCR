'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface UserProfile {
  id: string;
  email?: string;
  full_name?: string;
  role: string;
  is_admin: boolean;
  deleted_at?: string | null;
}

export function useUserRole() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getUserProfile();
      setProfile(response.data);
    } catch (err: any) {
      console.error('Error loading user profile:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load user profile');
    } finally {
      setLoading(false);
    }
  };

  return {
    profile,
    isAdmin: profile?.is_admin || false,
    role: profile?.role || 'user',
    loading,
    error,
    refetch: loadProfile,
  };
}

