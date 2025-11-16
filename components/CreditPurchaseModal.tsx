/**
 * Credit Purchase Modal
 * Allows users to purchase additional credits beyond their subscription
 */

'use client';

import { useState, useEffect } from 'react';
import { useCredits, type CreditPackage } from '@/lib/hooks/useCredits';
import { api } from '@/lib/api-client';

interface CreditPurchaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function CreditPurchaseModal({
  isOpen,
  onClose,
  onSuccess,
}: CreditPurchaseModalProps) {
  const { credits, fetchPackages } = useCredits();
  const [packages, setPackages] = useState<Record<string, CreditPackage>>({});
  const [selectedPackage, setSelectedPackage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);

  // Load credit packages when modal opens
  useEffect(() => {
    if (isOpen) {
      loadPackages();
    }
  }, [isOpen]);

  const loadPackages = async () => {
    setLoading(true);
    const packagesData = await fetchPackages();
    setPackages(packagesData);
    setLoading(false);
  };

  const handlePurchase = async () => {
    if (!selectedPackage) return;

    try {
      setPurchasing(true);

      // Call backend to create Stripe checkout session
      const response = await api.post<{ checkout_url: string }>('/payment/purchase-credits', {
        package: selectedPackage,
      });

      if (response.checkout_url) {
        // Redirect to Stripe checkout
        window.location.href = response.checkout_url;
      }
    } catch (error: any) {
      console.error('[CreditPurchase] Error:', error);
      alert(error.message || 'Failed to start checkout. Please try again.');
      setPurchasing(false);
    }
  };

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: currency,
    }).format(price);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div
          className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl border border-white/10 shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 bg-gradient-to-br from-slate-800 to-slate-900 border-b border-white/10 p-6 z-10">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-bold text-white mb-2">
                  Buy More Credits
                </h2>
                {credits && (
                  <p className="text-gray-400">
                    Current balance:{' '}
                    <span className="text-blue-300 font-semibold">
                      {credits.balance.toLocaleString()} credits
                    </span>
                  </p>
                )}
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white transition"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-gray-400">Loading packages...</div>
              </div>
            ) : (
              <>
                {/* Info Banner */}
                <div className="bg-blue-500/10 border border-blue-400/30 rounded-lg p-4 mb-6">
                  <div className="flex items-start gap-3">
                    <div className="text-2xl">💡</div>
                    <div>
                      <p className="text-blue-300 font-semibold mb-1">
                        Need more credits this month?
                      </p>
                      <p className="text-gray-400 text-sm">
                        Top up your balance with a one-time credit purchase. Credits never expire and roll over to next month.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Package Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  {Object.entries(packages).map(([key, pkg]) => (
                    <button
                      key={key}
                      onClick={() => setSelectedPackage(key)}
                      className={`relative p-6 rounded-xl border-2 transition text-left ${
                        selectedPackage === key
                          ? 'border-blue-400 bg-blue-500/10'
                          : 'border-white/10 hover:border-white/20 bg-white/5 hover:bg-white/10'
                      }`}
                    >
                      {/* Badge */}
                      {pkg.badge && (
                        <div className="absolute top-4 right-4 bg-gradient-to-r from-gold to-gold-intense text-white text-xs font-bold px-3 py-1 rounded-full">
                          {pkg.badge}
                        </div>
                      )}

                      {/* Package Info */}
                      <div className="mb-4">
                        <h3 className="text-2xl font-bold text-white mb-1">
                          {pkg.credits.toLocaleString()} Credits
                        </h3>
                        <p className="text-gray-400 text-sm">{pkg.description}</p>
                      </div>

                      {/* Price */}
                      <div className="mb-4">
                        <div className="text-3xl font-bold text-blue-300">
                          {formatPrice(pkg.price, pkg.currency)}
                        </div>
                        <div className="text-gray-400 text-sm mt-1">
                          {formatPrice(pkg.price_per_credit, pkg.currency)} per credit
                        </div>
                      </div>

                      {/* Selection Indicator */}
                      {selectedPackage === key && (
                        <div className="flex items-center gap-2 text-blue-400 text-sm font-semibold">
                          <svg
                            className="w-5 h-5"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                              clipRule="evenodd"
                            />
                          </svg>
                          Selected
                        </div>
                      )}
                    </button>
                  ))}
                </div>

                {/* Monthly Allocation Info */}
                {credits && (
                  <div className="bg-royal/10 border border-royal/30 rounded-lg p-4 mb-6">
                    <div className="flex items-start gap-3">
                      <div className="text-2xl">📊</div>
                      <div className="flex-1">
                        <p className="text-royal-300 font-semibold mb-2">
                          Your Monthly Allocation
                        </p>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between text-gray-400">
                            <span>Monthly credits:</span>
                            <span className="text-white font-semibold">
                              {credits.monthly_allocation.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between text-gray-400">
                            <span>Used this month:</span>
                            <span className="text-white font-semibold">
                              {credits.percentage_used.toFixed(1)}%
                            </span>
                          </div>
                          <div className="flex justify-between text-gray-400">
                            <span>Purchased credits:</span>
                            <span className="text-white font-semibold">
                              {credits.total_purchased.toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Purchase Button */}
                <div className="flex items-center justify-end gap-4">
                  <button
                    onClick={onClose}
                    className="px-6 py-3 text-gray-400 hover:text-white transition"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handlePurchase}
                    disabled={!selectedPackage || purchasing}
                    className={`px-8 py-3 rounded-lg font-semibold transition ${
                      selectedPackage && !purchasing
                        ? 'bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-500 hover:to-royal-500 text-white'
                        : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    {purchasing ? (
                      <span className="flex items-center gap-2">
                        <svg
                          className="animate-spin h-5 w-5"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Processing...
                      </span>
                    ) : (
                      'Continue to Checkout'
                    )}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
