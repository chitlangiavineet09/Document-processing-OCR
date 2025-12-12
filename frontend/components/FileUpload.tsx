'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle, CheckCircle } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface UploadError {
  message: string;
  type: 'extension' | 'size' | 'multiple' | 'api';
}

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.pdf'];

export function FileUpload() {
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [error, setError] = useState<UploadError | null>(null);
  const [success, setSuccess] = useState(false);
  const router = useRouter();

  const onDrop = useCallback(async (acceptedFiles: File[], rejectedFiles: any[]) => {
    // Reset state
    setError(null);
    setSuccess(false);
    setUploadedFile(null);

    // Check for rejections
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors[0].code === 'file-too-large') {
        setError({
          message: `File size exceeds maximum allowed size of ${MAX_FILE_SIZE / (1024 * 1024)} MB`,
          type: 'size',
        });
        return;
      }
      if (rejection.errors[0].code === 'file-invalid-type') {
        setError({
          message: `Invalid file type. Allowed formats: ${ALLOWED_EXTENSIONS.join(', ')}`,
          type: 'extension',
        });
        return;
      }
    }

    // Check for multiple files
    if (acceptedFiles.length > 1) {
      setError({
        message: 'Please upload only one file at a time',
        type: 'multiple',
      });
      return;
    }

    if (acceptedFiles.length === 0) {
      return;
    }

    const file = acceptedFiles[0];
    setUploadedFile(file);
    setUploading(true);

    try {
      const response = await apiClient.uploadFile(file);
      console.log('Upload response:', response);
      
      // Extract job_id from response (FastAPI returns Pydantic model directly in response.data)
      const responseData = response.data || response;
      
      // Handle case where response might be an error object
      if (responseData && typeof responseData === 'object' && !responseData.job_id && !responseData.jobId && !responseData.id) {
        // Check if this is an error response
        if (responseData.detail || responseData.error || responseData.message) {
          throw new Error(JSON.stringify(responseData));
        }
      }
      
      const jobId = responseData?.job_id || responseData?.jobId || responseData?.id;
      
      // Ensure jobId is a string, not an object
      const jobIdString = typeof jobId === 'string' ? jobId : String(jobId || '');
      
      if (!jobIdString || jobIdString === '') {
        console.error('No job_id in response. Full response:', response);
        setError({
          message: 'Invalid response from server: missing job_id. Please try again.',
          type: 'api',
        });
        setUploadedFile(null);
        setUploading(false);
        return;
      }
      
      setSuccess(true);
      
      // Redirect to job confirmation page (Page 2) after 2 seconds
      setTimeout(() => {
        router.push(`/jobs/${jobIdString}/confirmation`);
      }, 2000);
    } catch (err: any) {
      console.error('Upload error:', err);
      console.error('Error response:', err.response?.data);
      let errorMessage = 'Failed to upload file';
      
      if (err.response?.data) {
        const responseData = err.response.data;
        console.log('Response data type:', typeof responseData);
        console.log('Response data:', JSON.stringify(responseData, null, 2));
        
        // Check if response.data itself is an error object
        if (responseData.detail) {
          const detail = responseData.detail;
          console.log('Detail type:', typeof detail);
          console.log('Detail value:', detail);
          
          // Handle Pydantic validation errors (array of error objects)
          if (Array.isArray(detail)) {
            errorMessage = detail
              .map((e: any) => {
                if (typeof e === 'string') return e;
                if (e && typeof e === 'object' && e.msg) return `${e.loc?.join('.') || 'Field'}: ${e.msg}`;
                if (e && typeof e === 'object') {
                  // Extract meaningful message from error object
                  return e.type || e.msg || 'Validation error';
                }
                return 'Unknown error';
              })
              .join(', ');
          } else if (typeof detail === 'string') {
            errorMessage = detail;
          } else if (detail && typeof detail === 'object') {
            // Handle single error object - extract message safely
            if (detail.msg) {
              errorMessage = detail.msg;
            } else if (detail.message) {
              errorMessage = detail.message;
            } else {
              errorMessage = `Validation error: ${detail.type || 'Unknown error'}`;
            }
          }
        } else if (typeof responseData === 'string') {
          errorMessage = responseData;
        } else if (responseData.message) {
          errorMessage = responseData.message;
        } else {
          // If response.data is an object, try to extract message
          errorMessage = `Server error (${err.response?.status || 'unknown'}): ${JSON.stringify(responseData)}`;
          console.error('Unexpected error format:', responseData);
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      // Ensure errorMessage is always a string
      if (typeof errorMessage !== 'string') {
        errorMessage = String(errorMessage);
      }
      
      setError({
        message: errorMessage,
        type: 'api',
      });
      setUploadedFile(null);
    } finally {
      setUploading(false);
    }
  }, [router]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'application/pdf': ['.pdf'],
    },
    maxSize: MAX_FILE_SIZE,
    multiple: false,
    disabled: uploading || success,
  });

  const handleClear = () => {
    setUploadedFile(null);
    setError(null);
    setSuccess(false);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Error Alert */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800">
              {typeof error.message === 'string' ? error.message : 'An error occurred'}
            </p>
          </div>
          <button
            onClick={handleClear}
            className="text-red-600 hover:text-red-800"
            aria-label="Dismiss error"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      )}

      {/* Success Alert */}
      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-green-800">
              File uploaded successfully! Processing started. Redirecting...
            </p>
          </div>
        </div>
      )}

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : uploading || success
              ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
              : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50'
          }
        `}
      >
        <input {...getInputProps()} />
        
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="text-gray-600">Uploading and processing...</p>
          </div>
        ) : success ? (
          <div className="flex flex-col items-center gap-3">
            <CheckCircle className="h-12 w-12 text-green-600" />
            <p className="text-gray-600">Upload successful!</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="h-12 w-12 text-gray-400" />
            <div>
              <p className="text-lg font-medium text-gray-900">
                {isDragActive ? 'Drop file here' : 'Drag & drop file here'}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                or click to select a file
              </p>
            </div>
            <div className="text-xs text-gray-400 mt-2">
              <p>Allowed formats: {ALLOWED_EXTENSIONS.join(', ')}</p>
              <p>Max file size: {MAX_FILE_SIZE / (1024 * 1024)} MB</p>
            </div>
          </div>
        )}
      </div>

      {/* Uploaded File Info */}
      {uploadedFile && !success && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg flex items-center gap-3">
          <File className="h-5 w-5 text-gray-600" />
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-900">{uploadedFile.name}</p>
            <p className="text-xs text-gray-500">
              {(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB
            </p>
          </div>
          {!uploading && (
            <button
              onClick={handleClear}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
              aria-label="Remove file"
            >
              <X className="h-4 w-4 text-gray-600" />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

