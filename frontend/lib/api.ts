import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { getAuthHeaders } from './supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // Initial delay in ms
const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504];
const RETRYABLE_ERROR_CODES = ['ECONNABORTED', 'ETIMEDOUT', 'ENOTFOUND', 'ECONNRESET'];

/**
 * Calculate exponential backoff delay with jitter
 */
function getRetryDelay(retryCount: number): number {
  const exponentialDelay = RETRY_DELAY * Math.pow(2, retryCount);
  const jitter = Math.random() * 1000; // Add random jitter (0-1000ms)
  return exponentialDelay + jitter;
}

/**
 * Check if an error is retryable
 */
function isRetryableError(error: AxiosError): boolean {
  // Don't retry if no response (network error)
  if (!error.response) {
    // Retry network errors and timeout errors
    return error.code ? RETRYABLE_ERROR_CODES.includes(error.code) : true;
  }
  
  // Retry on specific status codes
  const status = error.response.status;
  if (RETRYABLE_STATUS_CODES.includes(status)) {
    return true;
  }
  
  // Don't retry on 4xx errors except specific ones (429, 408)
  if (status >= 400 && status < 500 && !RETRYABLE_STATUS_CODES.includes(status)) {
    return false;
  }
  
  return false;
}

interface RetryConfig extends InternalAxiosRequestConfig {
  _retryCount?: number;
  _retryDelay?: number;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      timeout: 30000, // 30 second timeout
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      async (config: RetryConfig) => {
        try {
          const headers = await getAuthHeaders();
          if (config.headers) {
            Object.assign(config.headers, headers);
          } else {
            config.headers = headers as any;
          }
        } catch (error) {
          // If no auth token, request will fail (as expected for protected routes)
        }
        
        // Initialize retry count if not set
        if (config._retryCount === undefined) {
          config._retryCount = 0;
        }
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor with retry logic
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const config = error.config as RetryConfig;
        
        // Handle 401 Unauthorized
        if (error.response?.status === 401) {
          console.error('Authentication error');
          // Could redirect to login here
          return Promise.reject(error);
        }
        
        // Check if request should be retried
        if (!config || !isRetryableError(error)) {
          return Promise.reject(error);
        }
        
        // Check retry count
        const retryCount = config._retryCount || 0;
        if (retryCount >= MAX_RETRIES) {
          console.error(`Max retries (${MAX_RETRIES}) reached for ${config.url}`);
        return Promise.reject(error);
        }
        
        // Calculate delay and retry
        const delay = getRetryDelay(retryCount);
        config._retryCount = retryCount + 1;
        config._retryDelay = delay;
        
        console.warn(
          `Request failed (${error.response?.status || error.code}), ` +
          `retrying in ${delay.toFixed(0)}ms (attempt ${retryCount + 1}/${MAX_RETRIES})`
        );
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, delay));
        
        // Retry the request
        return this.client(config);
      }
    );
  }

  async uploadFile(file: File): Promise<any> {
    const formData = new FormData();
    // Field name must match the backend parameter name 'file'
    formData.append('file', file);
    
    // Get auth headers
    const authHeaders = await getAuthHeaders();
    
    // For FormData, axios will automatically:
    // 1. Set Content-Type to multipart/form-data with boundary
    // 2. Set the correct headers
    // Don't manually set Content-Type header
    // Use longer timeout for file uploads
    return this.client.post('/jobs/', formData, {
      headers: {
        'Authorization': authHeaders['Authorization'],
        // DO NOT set Content-Type - let axios handle it for FormData
      },
      // Ensure axios treats this as multipart/form-data
      transformRequest: (data) => data, // Don't transform FormData
      timeout: 60000, // 60 seconds for file uploads
    });
  }

  async getJobs(status?: string, limit = 50, offset = 0) {
    const params: any = { limit, offset };
    if (status) {
      params.status_filter = status;
    }
    return this.client.get('/jobs/', { params });
  }

  async getJob(jobId: string) {
    return this.client.get(`/jobs/${jobId}`);
  }

  async getJobUpdates(since?: string) {
    const params: any = {};
    if (since) {
      params.since = since;
    }
    return this.client.get('/jobs/updates', { params });
  }

  async getJobDocuments(jobId: string) {
    return this.client.get(`/jobs/${jobId}/documents`);
  }

  // Draft bill endpoints
  async confirmPO(docId: string, poNumber: string) {
    return this.client.post(`/drafts/${docId}/confirm-po`, { po_number: poNumber });
  }

  async matchItems(docId: string) {
    return this.client.get(`/drafts/${docId}/match-items`);
  }

  async saveDraft(docId: string, items: any[]) {
    return this.client.post(`/drafts/${docId}/save`, { items });
  }

  async getDraftBillDetail(docId: string) {
    return this.client.get(`/drafts/${docId}/final`);
  }

  async listDraftBills() {
    return this.client.get('/drafts');
  }

  // User profile endpoints
  async getUserProfile() {
    return this.client.get('/users/me');
  }

  // Admin endpoints
  async listUsers(includeDeleted = false) {
    return this.client.get('/admin/users', { params: { include_deleted: includeDeleted } });
  }

  async getUser(userId: string) {
    return this.client.get(`/admin/users/${userId}`);
  }

  async createUser(userData: any) {
    return this.client.post('/admin/users', userData);
  }

  async updateUser(userId: string, userData: any) {
    return this.client.patch(`/admin/users/${userId}`, userData);
  }

  async deleteUser(userId: string, hardDelete = false) {
    return this.client.delete(`/admin/users/${userId}`, { params: { hard_delete: hardDelete } });
  }

  async restoreUser(userId: string) {
    return this.client.post(`/admin/users/${userId}/restore`);
  }

  // Settings endpoints
  async getSettings(category?: string) {
    const params: any = {};
    if (category) {
      params.category = category;
    }
    return this.client.get('/admin/settings', { params });
  }

  async updateSetting(category: string, key: string, value: string, description?: string) {
    const data: any = { value };
    if (description !== undefined) {
      data.description = description;
    }
    return this.client.put(`/admin/settings/${category}/${key}`, data);
  }

  async testSetting(category: string, key: string) {
    return this.client.post(`/admin/settings/${category}/${key}/test`);
  }

  // Global jobs endpoints
  async listAllJobs(status?: string, userId?: string, limit = 50, offset = 0) {
    const params: any = { limit, offset };
    if (status) {
      params.status_filter = status;
    }
    if (userId) {
      params.user_id = userId;
    }
    return this.client.get('/admin/jobs', { params });
  }

  async retryJob(jobId: string) {
    return this.client.post(`/admin/jobs/${jobId}/retry`);
  }
}

export const apiClient = new ApiClient();

