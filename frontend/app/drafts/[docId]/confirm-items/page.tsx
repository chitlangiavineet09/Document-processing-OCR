'use client';

import { useState, useEffect, useMemo } from 'react';
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
  CheckSquare,
  Square,
  DollarSign
} from 'lucide-react';

interface MatchedItem {
  bill_index: number;
  order_index: number;
  bill_item: any;
  order_item: any;
  item_name: string;
  master_item_name?: string;
  item_code?: string;
  hsn?: string;
  total_quantity?: number;
  billable_quantity?: number;
  unit?: string;
  unit_rate?: number;
  gst_type?: 'CGST-SGST' | 'IGST';
  available_tax_rates?: number[];
}

interface ItemInput {
  bill_index: number;
  order_index: number;
  selected: boolean;
  quantity: number;
  gst_rate?: number;
  cgst_rate?: number;
  sgst_rate?: number;
}

export default function ConfirmItemsPage() {
  const router = useRouter();
  const params = useParams();
  const docId = params.docId as string;

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matchedItems, setMatchedItems] = useState<MatchedItem[]>([]);
  const [unmatchedItems, setUnmatchedItems] = useState<any[]>([]);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [itemInputs, setItemInputs] = useState<Record<string, ItemInput>>({});
  const [matchResponse, setMatchResponse] = useState<any>(null);

  useEffect(() => {
    if (docId) {
      loadMatchedItems();
    }
  }, [docId]);

  // Calculate amount for an item
  const calculateAmount = (item: MatchedItem, input: ItemInput): number => {
    if (!input.selected || !item.unit_rate) return 0;

    let totalGstRate = 0;
    if (item.gst_type === 'CGST-SGST') {
      totalGstRate = (input.cgst_rate || 0) + (input.sgst_rate || 0);
    } else if (item.gst_type === 'IGST') {
      totalGstRate = input.gst_rate || 0;
    }

    // Amount = (quantity * unit_rate) * (1 + GST_rate/100)
    return (input.quantity * item.unit_rate) * (1 + totalGstRate / 100);
  };

  // Calculate total amount
  const totalAmount = useMemo(() => {
    return matchedItems.reduce((sum, item) => {
      const key = `${item.bill_index}_${item.order_index}`;
      const input = itemInputs[key];
      if (input) {
        return sum + calculateAmount(item, input);
      }
      return sum;
    }, 0);
  }, [matchedItems, itemInputs]);

  const loadMatchedItems = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.matchItems(docId);
      
      if (response.data) {
        setMatchResponse(response.data);
        const items = response.data.matches || [];
        setMatchedItems(items);
        setUnmatchedItems(response.data.unmatched_bill_items || []);
        setValidationErrors(response.data.validation_errors || []);

        // Initialize item inputs
        const inputs: Record<string, ItemInput> = {};
        items.forEach((item: MatchedItem) => {
          const key = `${item.bill_index}_${item.order_index}`;
          inputs[key] = {
            bill_index: item.bill_index,
            order_index: item.order_index,
            selected: true,
            quantity: item.billable_quantity || item.total_quantity || 1,
            ...(item.gst_type === 'IGST' 
              ? { gst_rate: item.available_tax_rates?.[0] || 0 }
              : { cgst_rate: 0, sgst_rate: 0 }
            )
          };
        });
        setItemInputs(inputs);
      }
    } catch (err: any) {
      console.error('Failed to load matched items:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load matched items');
    } finally {
      setLoading(false);
    }
  };

  const handleItemChange = (item: MatchedItem, field: string, value: any) => {
    const key = `${item.bill_index}_${item.order_index}`;
    const currentInput = itemInputs[key] || {
      bill_index: item.bill_index,
      order_index: item.order_index,
      selected: true,
      quantity: item.billable_quantity || item.total_quantity || 1,
    };

    setItemInputs({
      ...itemInputs,
      [key]: {
        ...currentInput,
        [field]: value,
      },
    });
  };

  const toggleItemSelection = (item: MatchedItem) => {
    const key = `${item.bill_index}_${item.order_index}`;
    const currentInput = itemInputs[key];
    handleItemChange(item, 'selected', !currentInput?.selected);
  };

  const validateInputs = (): string[] => {
    const errors: string[] = [];
    
    matchedItems.forEach((item) => {
      const key = `${item.bill_index}_${item.order_index}`;
      const input = itemInputs[key];
      
      if (!input || !input.selected) return;

      // Validate quantity
      if (input.quantity <= 0) {
        errors.push(`Quantity must be greater than 0 for item: ${item.item_name}`);
      }

      if (item.billable_quantity && input.quantity > item.billable_quantity) {
        errors.push(`Quantity ${input.quantity} exceeds billable quantity ${item.billable_quantity} for item: ${item.item_name}`);
      }

      // Validate GST rates
      if (item.gst_type === 'CGST-SGST') {
        if (!input.cgst_rate && input.cgst_rate !== 0) {
          errors.push(`CGST rate is required for item: ${item.item_name}`);
        }
        if (!input.sgst_rate && input.sgst_rate !== 0) {
          errors.push(`SGST rate is required for item: ${item.item_name}`);
        }
      } else if (item.gst_type === 'IGST') {
        if (!input.gst_rate && input.gst_rate !== 0) {
          errors.push(`IGST rate is required for item: ${item.item_name}`);
        }
      }
    });

    // Check if at least one item is selected
    const selectedCount = Object.values(itemInputs).filter(input => input?.selected).length;
    if (selectedCount === 0) {
      errors.push('At least one item must be selected');
    }

    return errors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate inputs
    const errors = validateInputs();
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      setValidationErrors([]);

      // Prepare items for submission
      const itemsToSave = Object.values(itemInputs)
        .filter(input => input?.selected)
        .map(input => ({
          bill_index: input.bill_index,
          order_index: input.order_index,
          selected: true,
          quantity: input.quantity,
          ...(itemInputs[`${input.bill_index}_${input.order_index}`]?.gst_rate !== undefined
            ? { gst_rate: input.gst_rate }
            : { cgst_rate: input.cgst_rate || 0, sgst_rate: input.sgst_rate || 0 }
          )
        }));

      const response = await apiClient.saveDraft(docId, itemsToSave);
      
      if (response.data) {
        // Navigate to final draft bill page (Page 7)
        router.push(`/drafts/${docId}/final`);
      }
    } catch (err: any) {
      console.error('Failed to save draft:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to save draft bill');
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
          <div className="max-w-7xl mx-auto">
            <div className="mb-6">
              <button
                onClick={() => router.back()}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
              <h1 className="text-3xl font-bold text-gray-900">Confirm Items & Quantities</h1>
              <p className="text-gray-600 mt-2">Step 2 of 2: Review matched items, edit quantities, and configure GST rates</p>
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

            {unmatchedItems.length > 0 && (
              <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800">Unmatched Items</p>
                    <p className="text-sm text-yellow-700 mt-1">
                      {unmatchedItems.length} bill item(s) could not be automatically matched with order items.
                      Please review the matched items below.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {validationErrors.length > 0 && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm font-medium text-red-800 mb-2">Validation Errors:</p>
                <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
                  {validationErrors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          <span className="sr-only">Select</span>
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Item Name
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          HSN
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Unit Rate
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Total Qty
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Billable Qty
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Quantity
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          GST Type
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          CGST %
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          SGST %
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          IGST %
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Amount
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {matchedItems.map((item) => {
                        const key = `${item.bill_index}_${item.order_index}`;
                        const input = itemInputs[key];
                        const amount = input ? calculateAmount(item, input) : 0;
                        const hasCGSTSGST = item.gst_type === 'CGST-SGST';
                        const hasIGST = item.gst_type === 'IGST';

                        return (
                          <tr key={key} className={input?.selected ? '' : 'opacity-50'}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <button
                                type="button"
                                onClick={() => toggleItemSelection(item)}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                {input?.selected ? (
                                  <CheckSquare className="h-5 w-5" />
                                ) : (
                                  <Square className="h-5 w-5" />
                                )}
                              </button>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-sm font-medium text-gray-900">{item.item_name}</div>
                              {item.item_code && (
                                <div className="text-sm text-gray-500">Code: {item.item_code}</div>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {item.hsn || '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              ₹{item.unit_rate?.toFixed(2) || '0.00'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {item.total_quantity?.toFixed(2) || '-'} {item.unit || ''}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {item.billable_quantity?.toFixed(2) || '-'} {item.unit || ''}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={input?.quantity || 0}
                                onChange={(e) => handleItemChange(item, 'quantity', parseFloat(e.target.value) || 0)}
                                disabled={!input?.selected || submitting}
                                className="w-24 px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                              />
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {item.gst_type || '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {hasCGSTSGST ? (
                                <input
                                  type="number"
                                  min="0"
                                  max="100"
                                  step="0.01"
                                  value={input?.cgst_rate || 0}
                                  onChange={(e) => handleItemChange(item, 'cgst_rate', parseFloat(e.target.value) || 0)}
                                  disabled={!input?.selected || submitting}
                                  className="w-20 px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                                />
                              ) : (
                                <span className="text-gray-400">-</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {hasCGSTSGST ? (
                                <input
                                  type="number"
                                  min="0"
                                  max="100"
                                  step="0.01"
                                  value={input?.sgst_rate || 0}
                                  onChange={(e) => handleItemChange(item, 'sgst_rate', parseFloat(e.target.value) || 0)}
                                  disabled={!input?.selected || submitting}
                                  className="w-20 px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                                />
                              ) : (
                                <span className="text-gray-400">-</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {hasIGST ? (
                                <input
                                  type="number"
                                  min="0"
                                  max="100"
                                  step="0.01"
                                  value={input?.gst_rate || 0}
                                  onChange={(e) => handleItemChange(item, 'gst_rate', parseFloat(e.target.value) || 0)}
                                  disabled={!input?.selected || submitting}
                                  className="w-20 px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                                />
                              ) : (
                                <span className="text-gray-400">-</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              ₹{amount.toFixed(2)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot className="bg-gray-50">
                      <tr>
                        <td colSpan={11} className="px-6 py-4 text-right text-sm font-medium text-gray-700">
                          Total Amount:
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                          ₹{totalAmount.toFixed(2)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              <div className="mt-6 flex items-center justify-end gap-4">
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={submitting}
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      Confirm & Save Draft
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}

