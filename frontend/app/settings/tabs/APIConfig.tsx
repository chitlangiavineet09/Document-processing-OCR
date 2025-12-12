'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Save, Loader2, AlertCircle, CheckCircle, Eye, EyeOff, TestTube } from 'lucide-react';

interface Setting {
  id: string;
  category: string;
  key: string;
  value: string;
  description?: string;
  encrypted?: boolean;
}

export default function APIConfig() {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showToken, setShowToken] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getSettings('external_api');
      setSettings(response.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load API settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (setting: Setting, newValue: string) => {
    try {
      setSaving(setting.key);
      setError(null);
      setSuccess(null);
      
      await apiClient.updateSetting(setting.category, setting.key, newValue, setting.description);
      
      setSuccess(`Saved ${setting.key} successfully`);
      await loadSettings();
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save setting');
      setTimeout(() => setError(null), 5000);
    } finally {
      setSaving(null);
    }
  };

  const handleTest = async (key: string) => {
    try {
      setError(null);
      setSuccess(null);
      const response = await apiClient.testSetting('external_api', key);
      if (response.data.success) {
        setSuccess(response.data.message || 'Connection test successful');
      } else {
        setError(response.data.message || 'Connection test failed');
      }
      setTimeout(() => {
        setSuccess(null);
        setError(null);
      }, 5000);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Test failed');
      setTimeout(() => setError(null), 5000);
    }
  };

  const maskValue = (value: string, isToken: boolean) => {
    if (!isToken || !value) return value;
    if (showToken) return value;
    if (value.length <= 4) return '****';
    return '****' + value.slice(-4);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  const omsBaseUrl = settings.find(s => s.key === 'oms_base_url');
  const omsAuthToken = settings.find(s => s.key === 'oms_auth_token');

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">OMS API Configuration</h2>
        <p className="text-sm text-gray-500">
          Configure external OMS API connection settings. These settings are used to fetch order details.
        </p>
      </div>

      {/* Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-green-700">{success}</p>
        </div>
      )}

      {/* Settings Form */}
      <div className="space-y-6">
        {/* OMS Base URL */}
        {omsBaseUrl && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              OMS API Base URL
            </label>
            <p className="text-xs text-gray-500 mb-3">{omsBaseUrl.description}</p>
            <div className="flex gap-2">
              <input
                type="text"
                defaultValue={omsBaseUrl.value}
                onBlur={(e) => {
                  if (e.target.value !== omsBaseUrl.value) {
                    handleSave(omsBaseUrl, e.target.value);
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.currentTarget.blur();
                  }
                }}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://api.zetwerk.com/oms/v1"
              />
            </div>
          </div>
        )}

        {/* OMS Auth Token */}
        {omsAuthToken && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                OMS API Authentication Token
              </label>
              <button
                onClick={() => setShowToken(!showToken)}
                className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
              >
                {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                {showToken ? 'Hide' : 'Show'}
              </button>
            </div>
            <p className="text-xs text-gray-500 mb-3">{omsAuthToken.description}</p>
            <div className="flex gap-2">
              <input
                type={showToken ? 'text' : 'password'}
                defaultValue={omsAuthToken.value}
                onBlur={(e) => {
                  if (e.target.value !== omsAuthToken.value) {
                    handleSave(omsAuthToken, e.target.value);
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.currentTarget.blur();
                  }
                }}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                placeholder="Enter authentication token"
              />
              <button
                onClick={() => handleTest('oms_auth_token')}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
                title="Test connection"
              >
                <TestTube className="h-4 w-4" />
                Test
              </button>
            </div>
            {!showToken && omsAuthToken.value && (
              <p className="mt-2 text-xs text-gray-500">
                Current token ends with: {omsAuthToken.value.slice(-4)}
              </p>
            )}
          </div>
        )}

        {settings.length === 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-500">No API settings configured</p>
          </div>
        )}
      </div>
    </div>
  );
}
