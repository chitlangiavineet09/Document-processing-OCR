'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { 
  Loader2, 
  AlertCircle, 
  Clock, 
  CheckCircle, 
  XCircle,
  RefreshCw,
  Search,
  Filter,
  Eye
} from 'lucide-react';

interface Job {
  id: string;
  user_id: string;
  user_email?: string;
  user_name?: string;
  file_name: string;
  original_size: number;
  status: string;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  failed_at?: string;
}

const STATUS_CONFIG = {
  in_queue: {
    label: 'In Queue',
    icon: Clock,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    animate: false,
  },
  processing: {
    label: 'Processing',
    icon: Loader2,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    animate: true,
  },
  processed: {
    label: 'Processed',
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    animate: false,
  },
  error: {
    label: 'Error',
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    animate: false,
  },
} as const;

export default function GlobalJobs() {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [retrying, setRetrying] = useState<string | null>(null);

  useEffect(() => {
    loadJobs();
  }, [statusFilter]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.listAllJobs(statusFilter || undefined);
      setJobs(response.data || []);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load jobs';
      setError(errorMessage);
      console.error('Error loading jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async (jobId: string) => {
    if (!confirm('Are you sure you want to retry this job?')) {
      return;
    }

    try {
      setRetrying(jobId);
      await apiClient.retryJob(jobId);
      await loadJobs();
      alert('Job queued for retry successfully');
    } catch (err: any) {
      alert(`Failed to retry job: ${err.response?.data?.detail || err.message}`);
    } finally {
      setRetrying(null);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const filteredJobs = jobs.filter(job => {
    const searchLower = searchTerm.toLowerCase();
    return (
      job.file_name.toLowerCase().includes(searchLower) ||
      job.id.toLowerCase().includes(searchLower) ||
      (job.user_email?.toLowerCase().includes(searchLower) || false) ||
      (job.user_name?.toLowerCase().includes(searchLower) || false)
    );
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Global Job List</h2>
        <p className="text-sm text-gray-500">
          View all jobs across all users. You can retry failed jobs or view job details.
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by file name, job ID, or user..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="in_queue">In Queue</option>
            <option value="processing">Processing</option>
            <option value="processed">Processed</option>
            <option value="error">Error</option>
          </select>
        </div>
        <button
          onClick={loadJobs}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">Error Loading Jobs</p>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Jobs Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Job ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  File Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Completed/Failed
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredJobs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    {searchTerm || statusFilter ? 'No jobs found matching your filters' : 'No jobs found'}
                  </td>
                </tr>
              ) : (
                filteredJobs.map((job) => {
                  const statusConfig = STATUS_CONFIG[job.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.in_queue;
                  const StatusIcon = statusConfig.icon;

                  return (
                    <tr key={job.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-mono text-gray-900">{job.id.slice(0, 8)}...</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{job.user_email || job.user_name || '-'}</div>
                        {job.user_name && job.user_email && (
                          <div className="text-xs text-gray-500">{job.user_email}</div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">{job.file_name}</div>
                        <div className="text-xs text-gray-500">{formatFileSize(job.original_size)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}>
                          <StatusIcon className={`h-4 w-4 ${statusConfig.animate ? 'animate-spin' : ''}`} />
                          {statusConfig.label}
                        </span>
                        {job.error_message && (
                          <div className="mt-1 text-xs text-red-600 max-w-xs truncate" title={job.error_message}>
                            {job.error_message}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(job.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {job.completed_at ? (
                          <span className="text-green-600">{formatDate(job.completed_at)}</span>
                        ) : job.failed_at ? (
                          <span className="text-red-600">{formatDate(job.failed_at)}</span>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => router.push(`/jobs/${job.id}/documents`)}
                            className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                            title="View job details"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          {job.status === 'error' && (
                            <button
                              onClick={() => handleRetry(job.id)}
                              disabled={retrying === job.id}
                              className="text-green-600 hover:text-green-900 flex items-center gap-1 disabled:opacity-50"
                              title="Retry job"
                            >
                              {retrying === job.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <RefreshCw className="h-4 w-4" />
                              )}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="text-sm text-gray-500 text-center">
        Showing {filteredJobs.length} of {jobs.length} jobs
      </div>
    </div>
  );
}
