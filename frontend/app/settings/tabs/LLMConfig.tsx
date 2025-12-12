'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { Save, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

interface Setting {
  id: string;
  category: string;
  key: string;
  value: string;
  description?: string;
}

interface PromptSetting extends Setting {
  type: 'prompt' | 'model';
}

const DEFAULT_PROMPTS: Record<string, string> = {
  classification_prompt: `You are a document classifier. Analyze the provided image and classify it into one of these categories:
- 'bill': If it's an invoice or bill document
- 'eway_bill': If it's an e-way bill document
- 'unknown': If it doesn't match either category

Respond with ONLY one word: 'bill', 'eway_bill', or 'unknown'. Do not include any explanation or additional text.`,
  
  ocr_prompt: `You are an OCR system. Extract all relevant data from this bill document.
Return the data as a JSON object. Include all fields like dates, invoice numbers, parties, items, amounts, taxes, etc.
Be thorough and extract all visible information. Return only valid JSON, no other text.`,
  
  fuzzy_match_prompt: `You are a fuzzy matcher with high confidence. Task: produce a ONE-TO-ONE mapping from bill items to PO items.

Rules:

1. Fuzzy Match based on item name semantics and HSN/SAC code

2. If HSN/SAC differs, you MAY still match based on strong name semantics, but only if there is high confidence and no better HSN/SAC alternative.

3. Each billId MUST map to EXACTLY ONE poId.

4. Each poId MUST be used AT MOST ONCE (no two bill items may map to the same PO item).

5. If any billId cannot be matched confidently, list it under unmatched and DO NOT guess.

Return STRICT JSON ONLY with this exact shape:

{
  "matches": [{"billId": "b0", "poId": "p2"}],
  "unmatched": ["b3"]
}`
};

const LLM_SETTINGS: PromptSetting[] = [
  { key: 'classification_prompt', type: 'prompt', description: 'Prompt for document classification (bill, e-way bill, unknown)' },
  { key: 'classification_model', type: 'model', description: 'LLM model for classification' },
  { key: 'ocr_prompt', type: 'prompt', description: 'Prompt for OCR extraction from bills' },
  { key: 'ocr_model', type: 'model', description: 'LLM model for OCR extraction' },
  { key: 'fuzzy_match_prompt', type: 'prompt', description: 'Prompt for fuzzy matching bill items with order items' },
  { key: 'fuzzy_match_model', type: 'model', description: 'LLM model for fuzzy matching' },
];

const AVAILABLE_MODELS = [
  'gpt-4o',
  'gpt-4-turbo',
  'gpt-4',
  'gpt-3.5-turbo',
];

export default function LLMConfig() {
  const [settings, setSettings] = useState<Record<string, Setting>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editingValues, setEditingValues] = useState<Record<string, string>>({});
  const [useDefaultPrompt, setUseDefaultPrompt] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getSettings('llm');
      const settingsMap: Record<string, Setting> = {};
      const defaultFlags: Record<string, boolean> = {};
      
      (response.data || []).forEach((s: Setting) => {
        settingsMap[s.key] = s;
        
        // Check if prompt is empty or matches default (means using default)
        if (DEFAULT_PROMPTS[s.key]) {
          // If value is empty or whitespace, user is using default
          const isUsingDefault = !s.value || !s.value.trim();
          defaultFlags[s.key] = isUsingDefault;
          
          // Set editing value to default prompt text if using default, otherwise use saved value
          setEditingValues(prev => ({ 
            ...prev, 
            [s.key]: isUsingDefault ? DEFAULT_PROMPTS[s.key] : (s.value || '') 
          }));
        } else {
          // For non-prompt fields (models), just use the saved value
          setEditingValues(prev => ({ ...prev, [s.key]: s.value || '' }));
        }
      });
      
      setSettings(settingsMap);
      setUseDefaultPrompt(defaultFlags);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load LLM settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (key: string, newValue: string, isDefault: boolean) => {
    try {
      setSaving(key);
      setError(null);
      setSuccess(null);
      
      // If using default, save empty string to indicate using default
      const valueToSave = isDefault ? '' : newValue;
      
      await apiClient.updateSetting('llm', key, valueToSave);
      
      setSuccess(`Saved ${key} successfully`);
      await loadSettings();
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save setting');
      setTimeout(() => setError(null), 5000);
    } finally {
      setSaving(null);
    }
  };

  const handleValueChange = (key: string, value: string) => {
    setEditingValues(prev => ({ ...prev, [key]: value }));
  };

  const handleToggleDefault = (key: string) => {
    const newUseDefault = !useDefaultPrompt[key];
    setUseDefaultPrompt(prev => ({ ...prev, [key]: newUseDefault }));
    
    // When switching to default, update editing value to show default prompt
    if (newUseDefault) {
      setEditingValues(prev => ({ ...prev, [key]: DEFAULT_PROMPTS[key] || '' }));
    } else {
      // When switching to custom, restore the saved value if it exists (non-empty), or keep empty for new custom
      const savedValue = settings[key]?.value || '';
      // If saved value exists and is not empty, use it; otherwise start with empty string for new custom prompt
      setEditingValues(prev => ({ ...prev, [key]: savedValue.trim() || '' }));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">LLM Prompt & Model Configuration</h2>
        <p className="text-sm text-gray-500">
          Configure LLM prompts and models used for document classification, OCR extraction, and fuzzy matching.
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
        {LLM_SETTINGS.map((settingDef) => {
          const setting = settings[settingDef.key];
          const isUsingDefault = useDefaultPrompt[settingDef.key] || false;
          const isPromptField = settingDef.type === 'prompt' && DEFAULT_PROMPTS[settingDef.key];
          
          // Determine current value to display
          let currentValue: string;
          if (isPromptField && isUsingDefault) {
            currentValue = DEFAULT_PROMPTS[settingDef.key];
          } else {
            currentValue = editingValues[settingDef.key] || setting?.value || '';
          }
          
          // Check if has unsaved changes
          // If using default and setting value is not empty, there are changes
          // If not using default and current value differs from saved value, there are changes
          const savedValue = setting?.value || '';
          const hasChanges = isUsingDefault 
            ? savedValue && savedValue.trim() !== '' 
            : currentValue !== savedValue;

          return (
            <div key={settingDef.key} className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  {settingDef.key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </label>
                <div className="flex items-center gap-3">
                  {isPromptField && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-600">Use Default</span>
                      <button
                        type="button"
                        onClick={() => handleToggleDefault(settingDef.key)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          isUsingDefault ? 'bg-blue-600' : 'bg-gray-300'
                        }`}
                        role="switch"
                        aria-checked={isUsingDefault}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            isUsingDefault ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  )}
                  {hasChanges && (
                    <button
                      onClick={() => handleSave(settingDef.key, currentValue, isUsingDefault)}
                      disabled={saving === settingDef.key}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
                    >
                      {saving === settingDef.key ? (
                        <>
                          <Loader2 className="h-3 w-3 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="h-3 w-3" />
                          Save
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
              {settingDef.description && (
                <p className="text-xs text-gray-500 mb-3">{settingDef.description}</p>
              )}

              {settingDef.type === 'prompt' ? (
                <div>
                  {isPromptField && isUsingDefault && (
                    <p className="text-xs text-amber-600 mb-2">
                      Showing default prompt (read-only). Toggle off to customize.
                    </p>
                  )}
                  <textarea
                    value={currentValue}
                    onChange={(e) => handleValueChange(settingDef.key, e.target.value)}
                    disabled={isPromptField && isUsingDefault}
                    rows={10}
                    className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm ${
                      isPromptField && isUsingDefault 
                        ? 'bg-gray-100 text-gray-600 cursor-not-allowed' 
                        : 'bg-white'
                    }`}
                    placeholder={`Enter ${settingDef.key.replace(/_/g, ' ')} prompt...`}
                  />
                </div>
              ) : (
                <select
                  value={currentValue}
                  onChange={(e) => handleValueChange(settingDef.key, e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {AVAILABLE_MODELS.map(model => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
              )}

              {hasChanges && (
                <p className="mt-2 text-xs text-amber-600">
                  You have unsaved changes
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
