'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/Header';
import { SidebarNav } from '@/components/SidebarNav';
import { apiClient } from '@/lib/api';
import { 
  ArrowLeft, 
  CheckCircle, 
  XCircle, 
  Loader2,
  AlertCircle,
  ShoppingCart
} from 'lucide-react';

export default function ConfirmPOPage() {
  const router = useRouter();
  const params = useParams();
  const docId = params.docId as string;

  const [poNumber, setPONumber] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [docInfo, setDocInfo] = useState<any>(null);
  const [poNotFound, setPONotFound] = useState(false);

  useEffect(() => {
    if (docId) {
      loadDocument();
    }
  }, [docId]);

  const loadDocument = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch document details to get OCR payload
      const jobsResponse = await apiClient.getJobs();
      const jobs = jobsResponse.data || [];

      // Find the document
      let document: any = null;
      for (const job of jobs) {
        try {
          const docsResponse = await apiClient.getJobDocuments(job.id);
          const docs = docsResponse.data || [];
          const foundDoc = docs.find((d: any) => d.id === docId);
          if (foundDoc) {
            document = foundDoc;
            break;
          }
        } catch (e) {
          // Continue searching
        }
      }

      if (!document) {
        setError('Document not found');
        return;
      }

      setDocInfo(document);

      // Use PO number from doc table (already extracted during OCR)
      // Fall back to OCR payload if not yet set
      const extractedPONumber = document.po_number || 
                                document.ocr_payload?.po_number || 
                                document.ocr_payload?.poNumber || 
                                document.ocr_payload?.purchase_order_number ||
                                document.ocr_payload?.purchaseOrderNumber ||
                                '';

      if (extractedPONumber) {
        setPONumber(extractedPONumber);
        setPONotFound(false);
      } else {
        // PO number was not found during OCR extraction
        setPONotFound(true);
      }
    } catch (err: any) {
      console.error('Failed to load document:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!poNumber.trim()) {
      setError('PO number is required');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const response = await apiClient.confirmPO(docId, poNumber.trim());
      
      if (response.data) {
        // Navigate to items confirmation page
        router.push(`/drafts/${docId}/confirm-items`);
      }
    } catch (err: any) {
      console.error('Failed to confirm PO:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to confirm PO number');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <SidebarNav />
        <main className="flex-1 p-8">
          <div className="max-w-4xl mx-auto">
            <div className="mb-6">
              <button
                onClick={() => router.back()}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
              <h1 className="text-3xl font-bold text-gray-900">Confirm PO Number</h1>
              <p className="text-gray-600 mt-2">Step 1 of 2: Confirm or edit the PO number extracted from the bill</p>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                <XCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-800">Error</p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            )}

            {poNotFound && (
              <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-yellow-800">PO Number Not Found</p>
                  <p className="text-sm text-yellow-700 mt-1">
                    The system could not automatically extract the PO number from the document. Please enter it manually below.
                  </p>
                </div>
              </div>
            )}

            <div className="bg-white rounded-lg shadow p-6">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label htmlFor="po-number" className="block text-sm font-medium text-gray-700 mb-2">
                    Purchase Order (PO) Number
                  </label>
                  <div className="relative">
                    <ShoppingCart className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <input
                      id="po-number"
                      type="text"
                      value={poNumber}
                      onChange={(e) => setPONumber(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter PO number"
                      disabled={submitting}
                      required
                    />
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    {poNumber ? (
                      <span className="flex items-center gap-2 text-green-600">
                        <CheckCircle className="h-4 w-4" />
                        PO number ready to confirm
                      </span>
                    ) : (
                      'Please enter a valid PO number'
                    )}
                  </p>
                </div>

                <div className="flex items-center justify-end gap-4 pt-4 border-t">
                  <button
                    type="button"
                    onClick={() => router.back()}
                    className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={submitting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting || !poNumber.trim()}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Confirming...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="h-4 w-4" />
                        Confirm PO
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {docInfo && (
              <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-blue-800">Next Steps</p>
                    <p className="text-sm text-blue-700 mt-1">
                      After confirming the PO number, we'll fetch order details and match bill items with order items.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

