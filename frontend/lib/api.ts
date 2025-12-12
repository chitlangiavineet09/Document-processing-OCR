import axios, { AxiosInstance, AxiosError } from 'axios';
import { getAuthHeaders } from './supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      timeout: 30000,
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      async (config) => {
        try {
          const headers = await getAuthHeaders();
          config.headers = {
            ...config.headers,
            ...headers,
          };
        } catch (error) {
          // If no auth token, request will fail (as expected for protected routes)
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Unauthorized - redirect to login or handle auth error
          console.error('Authentication error');
        }
        return Promise.reject(error);
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
    return this.client.post('/jobs/', formData, {
      headers: {
        'Authorization': authHeaders['Authorization'],
        // DO NOT set Content-Type - let axios handle it for FormData
      },
      // Ensure axios treats this as multipart/form-data
      transformRequest: (data) => data, // Don't transform FormData
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

