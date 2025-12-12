'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getCurrentUser } from '@/lib/supabase';
import { FileUpload } from '@/components/FileUpload';
import { Header } from '@/components/Header';
import { SidebarNav } from '@/components/SidebarNav';

export default function HomePage() {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    try {
      const user = await getCurrentUser();
      if (!user) {
        router.push('/login');
        return;
      }
      setAuthenticated(true);
    } catch (error) {
      router.push('/login');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!authenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <SidebarNav />
        <main className="flex-1 p-8">
          <div className="max-w-4xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Upload Document
              </h1>
              <p className="text-gray-600">
                Upload a PDF or image file for OCR and classification. The system will
                automatically create a draft bill after fetching details from the document.
              </p>
            </div>
            <FileUpload />
          </div>
        </main>
      </div>
    </div>
  );
}

