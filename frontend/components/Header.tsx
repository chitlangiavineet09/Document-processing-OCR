'use client';

import { useEffect, useState } from 'react';
import { supabase, getCurrentUser } from '@/lib/supabase';
import { Settings, User, LogOut } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { NotificationModal } from './NotificationModal';
import { useUserRole } from '@/hooks/useUserRole';

export function Header() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { isAdmin } = useUserRole();

  useEffect(() => {
    loadUser();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        setUser(session.user);
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  async function loadUser() {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Error loading user:', error);
    } finally {
      setLoading(false);
    }
  }

  const handleSettingsClick = () => {
    router.push('/settings');
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push('/login');
    router.refresh();
  };

  if (loading) {
    return (
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-semibold">Bill Processing System</h1>
          <div className="flex items-center gap-4">
            <div className="h-8 w-8 rounded-full bg-gray-200 animate-pulse"></div>
          </div>
        </div>
      </header>
    );
  }

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold text-gray-900">Bill Processing System</h1>
        <div className="flex items-center gap-4">
          {user && (
            <>
              <div className="flex items-center gap-2">
                <User className="h-5 w-5 text-gray-600" />
                <span className="text-sm text-gray-700">{user.email || 'User'}</span>
              </div>
              <NotificationModal />
              {isAdmin && (
                <button
                  onClick={handleSettingsClick}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                  aria-label="Settings"
                >
                  <Settings className="h-5 w-5 text-gray-600" />
                </button>
              )}
              <button
                onClick={handleLogout}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                aria-label="Logout"
                title="Logout"
              >
                <LogOut className="h-5 w-5 text-gray-600" />
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

