'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/Header';
import { SidebarNav } from '@/components/SidebarNav';
import { apiClient } from '@/lib/api';
import { 
  FileText, 
  AlertCircle, 
  Loader2, 
  ArrowLeft, 
  CheckCircle, 
  XCircle,
  Clock,
  Receipt,
  Package,
  HelpCircle
} from 'lucide-react';

interface Document {
  id: string;
  job_thread_id: string;
  user_id: string;
  page_number: number;
  doc_type: 'bill' | 'eway_bill' | 'unknown';
  status: 'draft_pending' | 'draft_created' | 'unknown';
  ocr_payload?: any;
  storage_uri?: string;
  created_at: string;
  updated_at: string;
}

const DOC_TYPE_CONFIG = {
  bill: {
    label: 'Bill',
    icon: Receipt,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
  },
  eway_bill: {
    label: 'E-Way Bill',
    icon: Package,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
  },
  unknown: {
    label: 'Unknown',
    icon: HelpCircle,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
  },
};

const STATUS_CONFIG = {
  draft_pending: {
    label: 'Draft Pending',
    icon: Clock,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
  },
  draft_created: {
    label: 'Draft Created',
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
  },
  unknown: {
    label: 'Unknown',
    icon: XCircle,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
  },
};

export default function DocumentsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;
  
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [jobStatus, setJobStatus] = useState<string>('');

  useEffect(() => {
    loadDocuments();
  }, [jobId]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError('');

      // First get job status to check if it's processed
      const jobResponse = await apiClient.getJob(jobId);
      const job = jobResponse.data;
      setJobStatus(job.status);

      if (job.status !== 'processed') {
        setError(`Job is still ${job.status}. Documents will be available once processing is complete.`);
        setLoading(false);
        return;
      }

      // Get documents
      const response = await apiClient.getJobDocuments(jobId);
      const docsData = Array.isArray(response.data) ? response.data : [];
      setDocuments(docsData);

      if (docsData.length === 0) {
        setError('No documents found for this job.');
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load documents';
      setError(errorMessage);
      console.error('Error loading documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDraft = (docId: string) => {
    router.push(`/drafts/${docId}/confirm-po`);
  };

  const handleReviewDraft = (docId: string) => {
    router.push(`/drafts/${docId}/final`);
  };

  const canConfirmDraft = (doc: Document) => {
    return doc.doc_type === 'bill' && doc.status === 'draft_pending';
  };

  const canReviewDraft = (doc: Document) => {
    return doc.status === 'draft_created';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex">
          <SidebarNav />
          <main className="flex-1 p-8">
            <div className="max-w-6xl mx-auto">
              <div className="mb-8">
                <div className="h-8 bg-gray-200 rounded w-1/4 mb-4 animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse"></div>
              </div>
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
                    <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <SidebarNav />
        <main className="flex-1 p-8">
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <button
                onClick={() => router.push('/jobs')}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Job History
              </button>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Documents</h1>
              <p className="text-gray-600">
                Job ID: <span className="font-mono text-sm">{jobId}</span>
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Documents List */}
            {documents.length === 0 && !error ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 text-lg mb-2">No documents found</p>
                <p className="text-gray-500 text-sm">
                  This job doesn't have any documents yet.
                </p>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow overflow-hidden">
                {/* Table Header - Desktop */}
                <div className="hidden md:grid md:grid-cols-12 gap-4 p-4 bg-gray-50 border-b border-gray-200 font-semibold text-sm text-gray-700">
                  <div className="col-span-1">Page #</div>
                  <div className="col-span-2">Document Type</div>
                  <div className="col-span-2">Status</div>
                  <div className="col-span-4">Details</div>
                  <div className="col-span-3 text-right">Action</div>
                </div>

                {/* Documents */}
                <div className="divide-y divide-gray-200">
                  {documents.map((doc) => {
                    const docTypeConfig = DOC_TYPE_CONFIG[doc.doc_type];
                    const statusConfig = STATUS_CONFIG[doc.status];
                    const DocTypeIcon = docTypeConfig.icon;
                    const StatusIcon = statusConfig.icon;

                    return (
                      <div
                        key={doc.id}
                        className="p-4 hover:bg-gray-50 transition-colors"
                      >
                        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                          {/* Page Number */}
                          <div className="md:col-span-1">
                            <span className="text-sm font-medium text-gray-900">
                              Page {doc.page_number}
                            </span>
                          </div>

                          {/* Document Type */}
                          <div className="md:col-span-2">
                            <span
                              className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${docTypeConfig.bgColor} ${docTypeConfig.color} border ${docTypeConfig.borderColor}`}
                            >
                              <DocTypeIcon className="h-4 w-4" />
                              {docTypeConfig.label}
                            </span>
                          </div>

                          {/* Status */}
                          <div className="md:col-span-2">
                            <span
                              className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${statusConfig.bgColor} ${statusConfig.color}`}
                            >
                              <StatusIcon className="h-4 w-4" />
                              {statusConfig.label}
                            </span>
                          </div>

                          {/* Details - Mobile */}
                          <div className="md:hidden text-sm text-gray-500">
                            {doc.storage_uri && (
                              <p className="text-xs">Storage: {doc.storage_uri.split('/').pop()}</p>
                            )}
                          </div>

                          {/* Details - Desktop */}
                          <div className="hidden md:block md:col-span-4 text-sm text-gray-600">
                            {doc.storage_uri && (
                              <p className="text-xs truncate">Storage: {doc.storage_uri.split('/').pop()}</p>
                            )}
                            {doc.ocr_payload && (
                              <p className="text-xs text-gray-500 mt-1">
                                OCR data available
                              </p>
                            )}
                          </div>

                          {/* Actions */}
                          <div className="md:col-span-3 flex justify-end gap-2">
                            {canConfirmDraft(doc) ? (
                              <button
                                onClick={() => handleConfirmDraft(doc.id)}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                              >
                                Confirm Draft
                              </button>
                            ) : canReviewDraft(doc) ? (
                              <button
                                onClick={() => handleReviewDraft(doc.id)}
                                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                              >
                                Review Draft
                              </button>
                            ) : (
                              <button
                                disabled
                                className="px-4 py-2 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed text-sm font-medium"
                                title={
                                  doc.doc_type === 'unknown'
                                    ? 'Unknown document type - no action available'
                                    : doc.status === 'draft_pending' && doc.doc_type !== 'bill'
                                    ? 'Draft confirmation is only available for bills'
                                    : 'No action available for this document'
                                }
                              >
                                {doc.doc_type === 'bill' && doc.status === 'draft_pending' 
                                  ? 'Confirm Draft'
                                  : doc.status === 'draft_created'
                                  ? 'Review Draft'
                                  : 'No Action'}
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

