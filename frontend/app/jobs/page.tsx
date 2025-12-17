'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/Header';
import { SidebarNav } from '@/components/SidebarNav';
import { apiClient } from '@/lib/api';
import { Clock, CheckCircle, XCircle, Loader2, AlertCircle, FileText } from 'lucide-react';

interface Job {
  id: string;
  file_name: string;
  status: 'in_queue' | 'processing' | 'processed' | 'error';
  created_at: string;
  completed_at?: string;
  error_message?: string;
  document_count?: number;
  can_review_docs: boolean;
}

const STATUS_CONFIG = {
  in_queue: {
    label: 'In Queue',
    icon: Clock,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    animate: false,
  },
  processing: {
    label: 'Processing',
    icon: Loader2,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    animate: true,
  },
  processed: {
    label: 'Processed',
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    animate: false,
  },
  error: {
    label: 'Error',
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    animate: false,
  },
} as const;

export default function JobsPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadJobs();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadJobs(true);
    }, 30000);
    
    return () => clearInterval(interval);
  }, [statusFilter]);

  const loadJobs = async (silent = false) => {
    try {
      if (!silent) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setError('');

      const response = await apiClient.getJobs(
        statusFilter || undefined,
        50,
        0
      );

      // Backend returns array directly or wrapped in data property
      const jobsData = Array.isArray(response.data) ? response.data : response.data?.data || [];
      setJobs(jobsData);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load jobs';
      setError(errorMessage);
      console.error('Error loading jobs:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleCheckDocuments = (jobId: string) => {
    router.push(`/jobs/${jobId}/documents`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const filteredJobs = statusFilter
    ? jobs.filter((job) => job.status === statusFilter)
    : jobs;

  // Calculate counts for each status
  const jobCounts = {
    all: jobs.length,
    in_queue: jobs.filter((job) => job.status === 'in_queue').length,
    processing: jobs.filter((job) => job.status === 'processing').length,
    processed: jobs.filter((job) => job.status === 'processed').length,
    error: jobs.filter((job) => job.status === 'error').length,
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex">
          <SidebarNav />
          <main className="flex-1 p-8">
            <div className="max-w-6xl mx-auto">
              <h1 className="text-3xl font-bold text-gray-900 mb-8">Job History</h1>
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="bg-white rounded-lg shadow p-6 animate-pulse"
                  >
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
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-3xl font-bold text-gray-900">Job History</h1>
              <button
                onClick={() => loadJobs()}
                disabled={refreshing}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {refreshing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Refreshing...
                  </>
                ) : (
                  'Refresh'
                )}
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Status Filter */}
            <div className="mb-6 flex gap-2">
              <button
                onClick={() => setStatusFilter('')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  !statusFilter
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                All ({jobCounts.all})
              </button>
              {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
                    statusFilter === status
                      ? `${config.bgColor} ${config.color} border ${config.borderColor}`
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <config.icon className={`h-4 w-4 ${config.animate ? 'animate-spin' : ''}`} />
                  {config.label} ({jobCounts[status as keyof typeof jobCounts]})
                </button>
              ))}
            </div>

            {/* Jobs List */}
            {filteredJobs.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 text-lg mb-2">No jobs found</p>
                <p className="text-gray-500 text-sm">
                  {statusFilter
                    ? `No jobs with status "${STATUS_CONFIG[statusFilter as keyof typeof STATUS_CONFIG].label}"`
                    : 'Upload a document to get started'}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredJobs.map((job) => {
                  const statusConfig = STATUS_CONFIG[job.status];
                  const StatusIcon = statusConfig.icon;

                  return (
                    <div
                      key={job.id}
                      className={`bg-white rounded-lg shadow border ${statusConfig.borderColor} hover:shadow-md transition-shadow`}
                    >
                      {/* Job Card Header */}
                      <div className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="text-lg font-semibold text-gray-900">
                                {job.file_name}
                              </h3>
                              <span
                                className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-2 ${statusConfig.bgColor} ${statusConfig.color} border ${statusConfig.borderColor}`}
                              >
                                <StatusIcon
                                  className={`h-4 w-4 ${statusConfig.animate ? 'animate-spin' : ''}`}
                                />
                                {statusConfig.label}
                              </span>
                            </div>
                            <p className="text-sm text-gray-500">
                              Job ID: <span className="font-mono">{job.id}</span>
                            </p>
                            <p className="text-sm text-gray-500">
                              Created: {formatDate(job.created_at)}
                            </p>
                            {job.completed_at && (
                              <p className="text-sm text-gray-500">
                                Completed: {formatDate(job.completed_at)}
                              </p>
                            )}
                            {job.document_count !== undefined && job.document_count > 0 && (
                              <p className="text-sm text-gray-500">
                                Documents: {job.document_count} page(s)
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Error/Warning Message */}
                        {job.error_message && (
                          <div className={`mb-4 p-3 border rounded-lg ${
                            job.status === 'error' 
                              ? 'bg-red-50 border-red-200' 
                              : 'bg-yellow-50 border-yellow-200'
                          }`}>
                            <p className={`text-sm font-medium mb-1 ${
                              job.status === 'error' ? 'text-red-800' : 'text-yellow-800'
                            }`}>
                              {job.status === 'error' ? 'Error Details:' : 'Warning:'}
                            </p>
                            <p className={`text-sm ${
                              job.status === 'error' ? 'text-red-700' : 'text-yellow-700'
                            }`}>
                              {job.error_message}
                            </p>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="flex items-center justify-end gap-3">
                          {job.can_review_docs ? (
                            <button
                              onClick={() => handleCheckDocuments(job.id)}
                              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                            >
                              Check Documents
                            </button>
                          ) : (
                            <button
                              disabled
                              className="px-4 py-2 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed font-medium"
                              title={
                                job.status === 'processed'
                                  ? 'No documents found'
                                  : `Job must be processed to check documents. Current status: ${statusConfig.label}`
                              }
                            >
                              Check Documents
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
