'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/Header';
import { SidebarNav } from '@/components/SidebarNav';
import { apiClient } from '@/lib/api';
import { 
  ArrowLeft, 
  Loader2,
  AlertCircle,
  Receipt,
  Download,
  CheckCircle
} from 'lucide-react';

interface DraftItem {
  id: string;
  item_name: string;
  master_item_name?: string;
  item_code?: string;
  hsn?: string;
  total_quantity?: number;
  billable_quantity?: number;
  quantity: number;
  gst_type?: 'CGST-SGST' | 'IGST';
  cgst_rate?: number;
  sgst_rate?: number;
  igst_rate?: number;
  unit?: string;
  unit_rate?: number;
  amount: number;
}

interface DraftBill {
  id: string;
  doc_id: string;
  po_number?: string;
  order_number?: string;
  order_mongo_id?: string;
  order_details?: any;
  ocr_payload?: any;  // OCR data from docs table (replaces extracted_data)
  items: DraftItem[];
  created_at: string;
}

export default function FinalDraftBillPage() {
  const router = useRouter();
  const params = useParams();
  const docId = params.docId as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draftBill, setDraftBill] = useState<DraftBill | null>(null);

  useEffect(() => {
    if (docId) {
      loadDraftBill();
    }
  }, [docId]);

  const loadDraftBill = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.getDraftBillDetail(docId);
      setDraftBill(response.data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load draft bill';
      setError(errorMessage);
      console.error('Error loading draft bill:', err);
    } finally {
      setLoading(false);
    }
  };

  // Calculate totals
  const totalAmount = draftBill?.items.reduce((sum, item) => sum + item.amount, 0) || 0;
  const totalQuantity = draftBill?.items.reduce((sum, item) => sum + item.quantity, 0) || 0;

  // Extract supplier and customer info from order_details or ocr_payload (from docs table)
  const supplierName = draftBill?.order_details?.data?.supplierName || 
                       draftBill?.ocr_payload?.supplier_name ||
                       draftBill?.ocr_payload?.supplierName ||
                       'N/A';
  
  const customerName = draftBill?.order_details?.data?.customerName ||
                       draftBill?.ocr_payload?.customer_name ||
                       draftBill?.ocr_payload?.customerName ||
                       'N/A';

  const handleBack = () => {
    router.push('/drafts');
  };

  const handleBackToDocuments = () => {
    if (draftBill) {
      // Extract job_id from the route or store it - for now, navigate to drafts list
      router.push('/drafts');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex">
          <SidebarNav />
          <main className="flex-1 p-8">
            <div className="max-w-6xl mx-auto">
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex">
          <SidebarNav />
          <main className="flex-1 p-8">
            <div className="max-w-6xl mx-auto">
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-lg font-semibold text-red-800">Error Loading Draft Bill</h3>
                  <p className="text-red-700 mt-1">{error}</p>
                  <button
                    onClick={handleBack}
                    className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                  >
                    Go Back
                  </button>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (!draftBill) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex">
          <SidebarNav />
          <main className="flex-1 p-8">
            <div className="max-w-6xl mx-auto">
              <p className="text-gray-500">Draft bill not found</p>
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
            <div className="mb-6">
              <button
                onClick={handleBack}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Draft Bills
              </button>
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <Receipt className="h-8 w-8 text-blue-600" />
                    Draft Bill
                  </h1>
                  <p className="text-gray-500 mt-1">
                    Created on {new Date(draftBill.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Draft Created
                  </span>
                  {/* Future: Download buttons */}
                  {/* <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2">
                    <Download className="h-4 w-4" />
                    Download PDF
                  </button>
                  <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2">
                    <Download className="h-4 w-4" />
                    Download JSON
                  </button> */}
                </div>
              </div>
            </div>

            {/* Draft Bill Details */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Bill Information</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                <div>
                  <label className="text-sm font-medium text-gray-500">PO Number</label>
                  <p className="mt-1 text-gray-900 font-medium">{draftBill.po_number || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Order Number</label>
                  <p className="mt-1 text-gray-900 font-medium">{draftBill.order_number || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Supplier</label>
                  <p className="mt-1 text-gray-900">{supplierName}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Customer</label>
                  <p className="mt-1 text-gray-900">{customerName}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Total Items</label>
                  <p className="mt-1 text-gray-900 font-medium">{draftBill.items.length}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Total Quantity</label>
                  <p className="mt-1 text-gray-900 font-medium">{totalQuantity.toFixed(2)}</p>
                </div>
              </div>
            </div>

            {/* Items Table */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Items</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Item Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        HSN/SAC
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Unit
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Unit Rate
                      </th>
                      {draftBill.items.some(item => item.gst_type === 'CGST-SGST') && (
                        <>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            CGST %
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            SGST %
                          </th>
                        </>
                      )}
                      {draftBill.items.some(item => item.gst_type === 'IGST') && (
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          IGST %
                        </th>
                      )}
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Amount
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {draftBill.items.map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{item.item_name}</div>
                          {item.master_item_name && item.master_item_name !== item.item_name && (
                            <div className="text-xs text-gray-500">{item.master_item_name}</div>
                          )}
                          {item.item_code && (
                            <div className="text-xs text-gray-500">Code: {item.item_code}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item.hsn || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item.unit || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item.quantity.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item.unit_rate ? `₹${item.unit_rate.toFixed(2)}` : '-'}
                        </td>
                        {draftBill.items.some(i => i.gst_type === 'CGST-SGST') && (
                          <>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {item.gst_type === 'CGST-SGST' ? `${item.cgst_rate?.toFixed(2) || 0}%` : '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {item.gst_type === 'CGST-SGST' ? `${item.sgst_rate?.toFixed(2) || 0}%` : '-'}
                            </td>
                          </>
                        )}
                        {draftBill.items.some(i => i.gst_type === 'IGST') && (
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {item.gst_type === 'IGST' ? `${item.igst_rate?.toFixed(2) || 0}%` : '-'}
                          </td>
                        )}
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 text-right">
                          ₹{item.amount.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-gray-50">
                    <tr>
                      <td colSpan={draftBill.items.some(item => item.gst_type === 'CGST-SGST') ? 7 : 6} className="px-6 py-4 text-right text-sm font-medium text-gray-900">
                        Total Amount:
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-lg font-bold text-gray-900">
                        ₹{totalAmount.toFixed(2)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                onClick={handleBackToDocuments}
                className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
              >
                Back to Documents
              </button>
              <button
                onClick={() => router.push('/')}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Upload New Document
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

