'use client';

import { Header } from '@/components/Header';
import { SidebarNav } from '@/components/SidebarNav';
import { useParams, useRouter } from 'next/navigation';
import { CheckCircle } from 'lucide-react';

export default function JobConfirmationPage() {
  const params = useParams();
  const router = useRouter();
  // Ensure jobId is always a string (not an object or array)
  const jobId = typeof params.jobId === 'string' 
    ? params.jobId 
    : Array.isArray(params.jobId) 
      ? params.jobId[0] 
      : String(params.jobId || 'unknown');

  const handleOk = () => {
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <SidebarNav />
        <main className="flex-1 p-8">
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8 text-center">
              <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
              <h1 className="text-2xl font-bold text-gray-900 mb-4">
                File Upload Successful
              </h1>
              <p className="text-gray-600 mb-6">
                Your document has been uploaded and the OCR and classification job has
                been triggered. You can continue to use the application while the job
                runs in the background.
              </p>
              <p className="text-sm text-gray-500 mb-8">
                Job ID: <span className="font-mono">{jobId}</span>
              </p>
              <button
                onClick={handleOk}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                OK
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

